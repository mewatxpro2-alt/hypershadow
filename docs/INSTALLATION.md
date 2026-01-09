# CLASSIFIED - Installation Guide

## Border Surveillance System Installation Manual

**Classification Level: CONFIDENTIAL**
**Document Version: 1.0.0**
**Last Updated: January 2026**

---

## ⚠️ SECURITY NOTICE

This system is designed for AIR-GAPPED deployment. After initial setup, disconnect ALL network connections. Unauthorized network connectivity is a security violation.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Installation Steps](#installation-steps)
4. [Post-Installation Configuration](#post-installation-configuration)
5. [Offline Installation](#offline-installation)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i5 / AMD Ryzen 5 | Intel i7 / AMD Ryzen 7 |
| RAM | 8 GB | 16 GB |
| Storage | 50 GB SSD | 100 GB NVMe SSD |
| GPU | None (CPU inference) | NVIDIA RTX 3060+ (CUDA) |
| Display | 1920x1080 | 2560x1440 or dual monitor |

### Software Requirements

| Software | Version | Notes |
|----------|---------|-------|
| Operating System | Windows 10/11, Ubuntu 20.04+, macOS 12+ | 64-bit required |
| Python | 3.9 - 3.11 | 3.10 recommended |
| pip | 21.0+ | Latest recommended |
| Git | 2.30+ | Optional, for version control |

### GPU Support (Optional)

For NVIDIA GPU acceleration:
- CUDA Toolkit 11.8+
- cuDNN 8.6+
- NVIDIA Driver 525+

---

## Pre-Installation Checklist

Before beginning installation, verify:

- [ ] System meets minimum hardware requirements
- [ ] Python 3.9+ is installed
- [ ] pip is installed and updated
- [ ] 50GB+ free disk space available
- [ ] Administrator/root access available
- [ ] Network access available (for initial setup only)
- [ ] Security clearance obtained for installation

---

## Installation Steps

### Step 1: Obtain Installation Package

```bash
# Option A: Clone repository (requires network)
git clone [INTERNAL_REPO_URL] border_surveillance

# Option B: Extract from approved media
unzip border_surveillance_v1.0.0.zip -d border_surveillance
```

### Step 2: Navigate to Project Directory

```bash
cd border_surveillance
```

### Step 3: Run Installation Script

#### Linux / macOS:

```bash
# Make script executable
chmod +x install.sh

# Run installation
./install.sh
```

#### Windows:

```batch
# Run installation
install.bat
```

### Step 4: Download YOLOv8 Model

The YOLOv8 model must be downloaded separately:

```bash
# During installation, you'll be prompted
# Or download manually:
# URL: https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt
# Place in: models/yolov8n.pt
```

**For offline environments**: Pre-download the model and copy to the `models/` directory.

### Step 5: Verify Installation

```bash
# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Run verification
python -c "from core.detection import BorderDetector; print('Installation OK')"
```

---

## Post-Installation Configuration

### 1. Change Default Credentials

**CRITICAL**: Change the default admin password immediately!

Default credentials:
- Username: `admin`
- Password: `admin123`

1. Start the application: `./run.sh` or `run.bat`
2. Login with default credentials
3. System will prompt for password change
4. Set a strong password (8+ characters)

### 2. Configure System Settings

Edit `config/settings.py` for your deployment:

```python
# Key settings to review:

# Border area configuration
BORDER_CONFIG = {
    "sector_name": "YOUR_SECTOR_NAME",
    "bounds": [[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]],
    "timezone": "YOUR_TIMEZONE",
}

# Detection thresholds
MODEL_CONFIG = {
    "confidence_threshold": 0.70,  # Adjust as needed
    "device": "auto",  # 'cuda', 'cpu', or 'auto'
}

# Session timeout (minutes)
SECURITY_CONFIG = {
    "session_timeout_minutes": 480,  # 8 hours
}
```

### 3. Download Offline Map Tiles (Optional)

For map functionality, download tiles before going offline:

```bash
# Activate virtual environment first
source venv/bin/activate

# Download tiles for your area
python maps/tile_downloader.py \
    --lat YOUR_LATITUDE \
    --lon YOUR_LONGITUDE \
    --radius 50 \
    --zoom 10-15
```

### 4. Configure Border Zones

Edit `config/zones.json` to define your border zones:

```json
{
    "A": {
        "name": "Zone Alpha",
        "terrain": "riverbank",
        "threat_modifier": 2,
        "patrol_coverage": true
    }
}
```

---

## Offline Installation

For air-gapped environments with no network access:

### Pre-Download Dependencies

On a networked machine:

```bash
# Create a directory for packages
mkdir offline_packages
cd offline_packages

# Download all dependencies
pip download -r requirements.txt -d .

# Also download pip and setuptools
pip download pip setuptools wheel -d .
```

### Transfer to Air-Gapped System

1. Copy `offline_packages/` to approved removable media
2. Scan media for malware
3. Copy to target system

### Install from Local Packages

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install from local packages
pip install --no-index --find-links=offline_packages -r requirements.txt
```

---

## Verification

### Run System Checks

```bash
# Activate virtual environment
source venv/bin/activate

# Run comprehensive check
python -c "
import sys
print('Python:', sys.version)

# Check core dependencies
import streamlit; print('Streamlit:', streamlit.__version__)
import cv2; print('OpenCV:', cv2.__version__)
import torch; print('PyTorch:', torch.__version__)
print('CUDA Available:', torch.cuda.is_available())
from ultralytics import YOLO; print('Ultralytics: OK')
import folium; print('Folium:', folium.__version__)

# Check local modules
from config.settings import BASE_DIR; print('Config: OK')
from core.detection import BorderDetector; print('Detection: OK')
from database.db_manager import DatabaseManager; print('Database: OK')

print()
print('All checks passed!')
"
```

### Test Application Launch

```bash
# Start the application
./run.sh  # or run.bat on Windows

# Open browser to: http://localhost:8501
# Login with admin/admin123
# Verify dashboard loads correctly
```

### Expected Output

```
[INFO] Activating virtual environment...
[OK] Virtual environment activated
[OK] Dependencies OK
[INFO] Starting Border Surveillance System...
[INFO] Port: 8501
[INFO] URL: http://localhost:8501
```

---

## Troubleshooting

### Common Issues

#### Issue: "Python not found"

**Solution**:
```bash
# Check Python installation
python3 --version

# Install Python if needed (Ubuntu)
sudo apt install python3.10 python3.10-venv

# Windows: Download from python.org
```

#### Issue: "Module not found" errors

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: "CUDA not available" (GPU support)

**Solution**:
```bash
# Check NVIDIA driver
nvidia-smi

# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### Issue: "Permission denied" on Linux/macOS

**Solution**:
```bash
# Make scripts executable
chmod +x install.sh run.sh

# Check directory permissions
ls -la
```

#### Issue: Database initialization fails

**Solution**:
```bash
# Delete existing database and reinitialize
rm -rf data/surveillance.db

# Run database initialization
python -c "from database.db_manager import DatabaseManager; DatabaseManager().initialize_database()"
```

#### Issue: YOLOv8 model not loading

**Solution**:
1. Verify model file exists: `ls models/yolov8n.pt`
2. Check file size (should be ~6.3 MB)
3. Re-download if corrupted

### Getting Help

For authorized support:
1. Check logs in `logs/system/`
2. Contact system administrator
3. Reference this documentation

---

## Directory Structure After Installation

```
border_surveillance/
├── config/
│   ├── settings.py
│   ├── security.py
│   └── zones.json
├── core/
│   ├── detection.py
│   ├── grid_system.py
│   ├── threat_scoring.py
│   └── video_processor.py
├── database/
│   ├── db_manager.py
│   ├── encryption.py
│   └── schema.sql
├── data/                    # Created during install
│   ├── map_tiles/
│   └── video_cache/
├── docs/
│   ├── INSTALLATION.md
│   ├── SECURITY.md
│   └── USER_MANUAL.md
├── logs/                    # Created during install
│   ├── audit/
│   ├── detections/
│   └── system/
├── maps/
│   ├── grid_overlay.py
│   ├── map_generator.py
│   └── tile_downloader.py
├── models/
│   ├── model_loader.py
│   └── yolov8n.pt          # Downloaded separately
├── ui/
│   ├── app.py
│   ├── auth.py
│   ├── components.py
│   └── styles.py
├── utils/
│   └── logger.py
├── venv/                    # Created during install
├── install.sh
├── install.bat
├── run.sh
├── run.bat
├── requirements.txt
└── README.md
```

---

## Security Reminder

After completing installation and verification:

1. **DISCONNECT** all network connections
2. **DISABLE** network adapters in system settings
3. **VERIFY** air-gap status
4. **DOCUMENT** installation in security log

---

**END OF INSTALLATION GUIDE**

*This document is CLASSIFIED. Handle according to applicable security protocols.*
