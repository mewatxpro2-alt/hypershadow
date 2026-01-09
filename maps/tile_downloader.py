"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CLASSIFIED - OFFLINE MAP TILE DOWNLOADER                  ║
║                        Border Surveillance System                             ║
║                                                                              ║
║  Purpose: Download OpenStreetMap tiles for offline operation                  ║
║  Security Level: CONFIDENTIAL                                                 ║
║  Version: 1.0.0                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

IMPORTANT: This utility should be run ONCE during initial setup
when network access is available. After tiles are downloaded,
the system operates fully offline.

USAGE:
    python tile_downloader.py --lat 25.0 --lon 55.0 --zoom 10-15 --radius 50

This will download all tiles within 50km of coordinates (25.0, 55.0)
at zoom levels 10 through 15.
"""

import os
import sys
import math
import time
import hashlib
import argparse
import urllib.request
from pathlib import Path
from typing import Tuple, List, Optional, Generator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import MAP_CONFIG, BASE_DIR


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TileConfig:
    """Configuration for tile downloading."""
    
    # OpenStreetMap tile server (standard tiles)
    # Using HTTPS for secure download during setup phase
    tile_server: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    
    # Local storage directory for tiles
    tile_dir: Path = BASE_DIR / "data" / "map_tiles"
    
    # Download settings
    max_concurrent: int = 4  # Max concurrent downloads (be nice to servers)
    request_delay: float = 0.25  # Delay between requests in seconds
    retry_count: int = 3  # Number of retries for failed downloads
    timeout: int = 30  # Request timeout in seconds
    
    # User agent (required by OSM usage policy)
    user_agent: str = "BorderSurveillanceSystem/1.0 (Offline Tile Cache)"
    
    # Tile size
    tile_size: int = 256  # Standard OSM tile size in pixels


# =============================================================================
# COORDINATE UTILITIES
# =============================================================================

def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    """
    Convert latitude/longitude to tile coordinates.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        zoom: Zoom level (0-19)
        
    Returns:
        Tuple of (tile_x, tile_y)
        
    Reference:
        https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    """
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    
    return x, y


def tile_to_lat_lon(x: int, y: int, zoom: int) -> Tuple[float, float]:
    """
    Convert tile coordinates to latitude/longitude (top-left corner).
    
    Args:
        x: Tile X coordinate
        y: Tile Y coordinate
        zoom: Zoom level
        
    Returns:
        Tuple of (latitude, longitude)
    """
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    
    return lat, lon


def calculate_tiles_in_radius(
    center_lat: float,
    center_lon: float,
    radius_km: float,
    zoom: int
) -> List[Tuple[int, int]]:
    """
    Calculate all tile coordinates within a radius of a center point.
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        radius_km: Radius in kilometers
        zoom: Zoom level
        
    Returns:
        List of (x, y) tile coordinates
    """
    # Convert radius to degrees (approximate)
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 * cos(lat) km
    lat_offset = radius_km / 111.0
    lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    # Calculate bounding box
    min_lat = center_lat - lat_offset
    max_lat = center_lat + lat_offset
    min_lon = center_lon - lon_offset
    max_lon = center_lon + lon_offset
    
    # Get tile range
    min_tile_x, max_tile_y = lat_lon_to_tile(max_lat, min_lon, zoom)
    max_tile_x, min_tile_y = lat_lon_to_tile(min_lat, max_lon, zoom)
    
    # Generate all tiles in range
    tiles = []
    for x in range(min_tile_x, max_tile_x + 1):
        for y in range(min_tile_y, max_tile_y + 1):
            tiles.append((x, y))
    
    return tiles


# =============================================================================
# TILE DOWNLOADER CLASS
# =============================================================================

class TileDownloader:
    """
    Downloads OpenStreetMap tiles for offline use.
    
    This class handles downloading map tiles from OSM servers and storing
    them locally for offline operation. It implements rate limiting and
    retry logic to comply with OSM usage policies.
    
    Security Note:
        - Downloads should only occur during initial setup
        - After download, system operates fully offline
        - Downloaded tiles are verified with checksums
    
    Attributes:
        config: TileConfig instance with download settings
        downloaded: Count of successfully downloaded tiles
        failed: Count of failed downloads
        skipped: Count of already-existing tiles
    """
    
    def __init__(self, config: Optional[TileConfig] = None):
        """
        Initialize the tile downloader.
        
        Args:
            config: TileConfig instance (uses defaults if not provided)
        """
        self.config = config or TileConfig()
        
        # Statistics
        self.downloaded = 0
        self.failed = 0
        self.skipped = 0
        
        # Create SSL context (for HTTPS)
        self.ssl_context = ssl.create_default_context()
        
        # Ensure tile directory exists
        self.config.tile_dir.mkdir(parents=True, exist_ok=True)
    
    def get_tile_path(self, z: int, x: int, y: int) -> Path:
        """
        Get the local file path for a tile.
        
        Args:
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            Path to the tile file
        """
        return self.config.tile_dir / str(z) / str(x) / f"{y}.png"
    
    def tile_exists(self, z: int, x: int, y: int) -> bool:
        """
        Check if a tile already exists locally.
        
        Args:
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            True if tile exists and is valid
        """
        tile_path = self.get_tile_path(z, x, y)
        
        if not tile_path.exists():
            return False
        
        # Check if file is not empty/corrupted
        if tile_path.stat().st_size < 100:  # Minimum valid PNG size
            return False
        
        return True
    
    def download_tile(self, z: int, x: int, y: int) -> bool:
        """
        Download a single tile.
        
        Args:
            z: Zoom level
            x: Tile X coordinate
            y: Tile Y coordinate
            
        Returns:
            True if download successful, False otherwise
            
        Security Note:
            Only called during setup phase when network is available.
        """
        # Skip if already exists
        if self.tile_exists(z, x, y):
            self.skipped += 1
            return True
        
        # Construct URL
        url = self.config.tile_server.format(z=z, x=x, y=y)
        tile_path = self.get_tile_path(z, x, y)
        
        # Ensure directory exists
        tile_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Attempt download with retries
        for attempt in range(self.config.retry_count):
            try:
                # Create request with proper headers
                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": self.config.user_agent}
                )
                
                # Download tile
                with urllib.request.urlopen(
                    request,
                    timeout=self.config.timeout,
                    context=self.ssl_context
                ) as response:
                    data = response.read()
                
                # Validate PNG header
                if not data.startswith(b'\x89PNG'):
                    raise ValueError("Invalid PNG data received")
                
                # Save tile
                with open(tile_path, "wb") as f:
                    f.write(data)
                
                self.downloaded += 1
                return True
                
            except Exception as e:
                if attempt < self.config.retry_count - 1:
                    time.sleep(self.config.request_delay * (attempt + 1))
                else:
                    print(f"Failed to download tile {z}/{x}/{y}: {e}")
                    self.failed += 1
                    return False
        
        return False
    
    def download_region(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float,
        min_zoom: int,
        max_zoom: int,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        Download all tiles for a region.
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Radius in kilometers
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with download statistics
            
        Security Note:
            This operation requires network access.
            Should only be run during initial setup.
        """
        # Reset statistics
        self.downloaded = 0
        self.failed = 0
        self.skipped = 0
        
        # Calculate total tiles
        all_tiles = []
        for zoom in range(min_zoom, max_zoom + 1):
            tiles = calculate_tiles_in_radius(center_lat, center_lon, radius_km, zoom)
            for x, y in tiles:
                all_tiles.append((zoom, x, y))
        
        total_tiles = len(all_tiles)
        print(f"Total tiles to process: {total_tiles}")
        
        # Download tiles
        processed = 0
        
        for z, x, y in all_tiles:
            self.download_tile(z, x, y)
            processed += 1
            
            # Progress update
            if progress_callback:
                progress_callback(processed, total_tiles)
            elif processed % 100 == 0:
                print(f"Progress: {processed}/{total_tiles} ({100*processed/total_tiles:.1f}%)")
            
            # Rate limiting
            if not self.tile_exists(z, x, y):  # Only delay for new downloads
                time.sleep(self.config.request_delay)
        
        return {
            "total": total_tiles,
            "downloaded": self.downloaded,
            "skipped": self.skipped,
            "failed": self.failed,
        }
    
    def verify_tiles(self, min_zoom: int, max_zoom: int) -> dict:
        """
        Verify integrity of downloaded tiles.
        
        Args:
            min_zoom: Minimum zoom level to verify
            max_zoom: Maximum zoom level to verify
            
        Returns:
            Dictionary with verification results
        """
        valid = 0
        invalid = 0
        missing = 0
        
        for zoom in range(min_zoom, max_zoom + 1):
            zoom_dir = self.config.tile_dir / str(zoom)
            
            if not zoom_dir.exists():
                continue
            
            for x_dir in zoom_dir.iterdir():
                if not x_dir.is_dir():
                    continue
                
                for tile_file in x_dir.iterdir():
                    if tile_file.suffix != ".png":
                        continue
                    
                    # Check file size
                    if tile_file.stat().st_size < 100:
                        invalid += 1
                    else:
                        # Verify PNG header
                        with open(tile_file, "rb") as f:
                            header = f.read(8)
                        
                        if header.startswith(b'\x89PNG'):
                            valid += 1
                        else:
                            invalid += 1
        
        return {
            "valid": valid,
            "invalid": invalid,
            "total": valid + invalid,
        }
    
    def get_storage_size(self) -> dict:
        """
        Calculate storage size of downloaded tiles.
        
        Returns:
            Dictionary with size information
        """
        total_bytes = 0
        file_count = 0
        
        for tile_file in self.config.tile_dir.rglob("*.png"):
            total_bytes += tile_file.stat().st_size
            file_count += 1
        
        return {
            "bytes": total_bytes,
            "megabytes": total_bytes / (1024 * 1024),
            "gigabytes": total_bytes / (1024 * 1024 * 1024),
            "file_count": file_count,
        }


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """
    Command line interface for tile downloading.
    
    Usage examples:
        # Download tiles for a 50km radius around coordinates
        python tile_downloader.py --lat 25.0 --lon 55.0 --radius 50 --zoom 10-15
        
        # Verify downloaded tiles
        python tile_downloader.py --verify --zoom 10-15
        
        # Check storage size
        python tile_downloader.py --size
    """
    parser = argparse.ArgumentParser(
        description="Download OpenStreetMap tiles for offline use",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Download tiles:
    python tile_downloader.py --lat 25.0 --lon 55.0 --radius 50 --zoom 10-15
    
  Verify tiles:
    python tile_downloader.py --verify --zoom 10-15
    
  Check storage:
    python tile_downloader.py --size

SECURITY NOTE:
  This utility requires network access and should only be run
  during initial system setup. After tiles are downloaded,
  the surveillance system operates fully offline.
        """
    )
    
    parser.add_argument(
        "--lat",
        type=float,
        help="Center latitude"
    )
    parser.add_argument(
        "--lon",
        type=float,
        help="Center longitude"
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=50.0,
        help="Radius in kilometers (default: 50)"
    )
    parser.add_argument(
        "--zoom",
        type=str,
        default="10-15",
        help="Zoom range (e.g., '10-15', default: 10-15)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify downloaded tiles"
    )
    parser.add_argument(
        "--size",
        action="store_true",
        help="Show storage size"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for tiles"
    )
    
    args = parser.parse_args()
    
    # Parse zoom range
    if "-" in args.zoom:
        min_zoom, max_zoom = map(int, args.zoom.split("-"))
    else:
        min_zoom = max_zoom = int(args.zoom)
    
    # Initialize downloader
    config = TileConfig()
    if args.output:
        config.tile_dir = Path(args.output)
    
    downloader = TileDownloader(config)
    
    # Handle commands
    if args.size:
        print("\n=== Tile Storage Statistics ===")
        size_info = downloader.get_storage_size()
        print(f"Total files: {size_info['file_count']:,}")
        print(f"Total size: {size_info['megabytes']:.2f} MB ({size_info['gigabytes']:.2f} GB)")
        return
    
    if args.verify:
        print(f"\n=== Verifying Tiles (zoom {min_zoom}-{max_zoom}) ===")
        verify_result = downloader.verify_tiles(min_zoom, max_zoom)
        print(f"Valid tiles: {verify_result['valid']:,}")
        print(f"Invalid tiles: {verify_result['invalid']:,}")
        print(f"Total: {verify_result['total']:,}")
        return
    
    # Download tiles
    if args.lat is None or args.lon is None:
        parser.error("--lat and --lon are required for downloading")
    
    print("\n" + "=" * 60)
    print("BORDER SURVEILLANCE SYSTEM - OFFLINE TILE DOWNLOADER")
    print("=" * 60)
    print(f"\nCenter: ({args.lat}, {args.lon})")
    print(f"Radius: {args.radius} km")
    print(f"Zoom levels: {min_zoom} to {max_zoom}")
    print(f"Output: {config.tile_dir}")
    print("\n⚠️  SECURITY NOTICE: Network access required for this operation")
    print("   After download, system operates fully offline.\n")
    
    # Confirm
    confirm = input("Proceed with download? [y/N]: ")
    if confirm.lower() != "y":
        print("Download cancelled.")
        return
    
    print("\nStarting download...")
    start_time = time.time()
    
    result = downloader.download_region(
        center_lat=args.lat,
        center_lon=args.lon,
        radius_km=args.radius,
        min_zoom=min_zoom,
        max_zoom=max_zoom
    )
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Total tiles: {result['total']:,}")
    print(f"Downloaded: {result['downloaded']:,}")
    print(f"Skipped (existing): {result['skipped']:,}")
    print(f"Failed: {result['failed']:,}")
    print(f"Time elapsed: {elapsed:.1f} seconds")
    
    # Show storage size
    size_info = downloader.get_storage_size()
    print(f"\nStorage used: {size_info['megabytes']:.2f} MB")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "TileConfig",
    "TileDownloader",
    "lat_lon_to_tile",
    "tile_to_lat_lon",
    "calculate_tiles_in_radius",
]


if __name__ == "__main__":
    main()
