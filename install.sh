#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    CLASSIFIED - INSTALLATION SCRIPT                          ║
# ║                        Border Surveillance System                             ║
# ║                                                                              ║
# ║  Purpose: Automated installation for Linux/macOS                             ║
# ║  Security Level: CONFIDENTIAL                                                 ║
# ║  Version: 1.0.0                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# SECURITY NOTICE:
# - This script should only be run on air-gapped systems
# - All dependencies must be pre-downloaded for offline installation
# - Review all operations before executing
#
# USAGE:
#   chmod +x install.sh
#   ./install.sh
#
# REQUIREMENTS:
#   - Python 3.9 or higher
#   - pip package manager
#   - 50GB available disk space
#   - 8GB RAM minimum (16GB recommended)

set -e  # Exit on any error

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
PYTHON_MIN_VERSION="3.9"
LOG_FILE="${SCRIPT_DIR}/install.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNCTIONS
# =============================================================================

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[${timestamp}]${NC} $1"
    echo "[${timestamp}] $1" >> "${LOG_FILE}"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}] ✓${NC} $1"
    echo "[${timestamp}] SUCCESS: $1" >> "${LOG_FILE}"
}

log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}] ⚠${NC} $1"
    echo "[${timestamp}] WARNING: $1" >> "${LOG_FILE}"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[${timestamp}] ✗${NC} $1"
    echo "[${timestamp}] ERROR: $1" >> "${LOG_FILE}"
}

print_banner() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                    ${RED}CLASSIFIED${NC} - BORDER SURVEILLANCE SYSTEM                    ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                           Installation Script                               ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_python_version() {
    log "Checking Python version..."
    
    # Find Python 3
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python ${PYTHON_MIN_VERSION} or higher."
        exit 1
    fi
    
    # Check version
    PYTHON_VERSION=$(${PYTHON_CMD} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    
    if [[ "$(printf '%s\n' "${PYTHON_MIN_VERSION}" "${PYTHON_VERSION}" | sort -V | head -n1)" != "${PYTHON_MIN_VERSION}" ]]; then
        log_error "Python ${PYTHON_MIN_VERSION} or higher required. Found: ${PYTHON_VERSION}"
        exit 1
    fi
    
    log_success "Python ${PYTHON_VERSION} found"
}

create_virtual_environment() {
    log "Creating virtual environment..."
    
    if [[ -d "${VENV_DIR}" ]]; then
        log_warning "Virtual environment already exists. Skipping creation."
        return
    fi
    
    ${PYTHON_CMD} -m venv "${VENV_DIR}"
    log_success "Virtual environment created at ${VENV_DIR}"
}

activate_virtual_environment() {
    log "Activating virtual environment..."
    
    source "${VENV_DIR}/bin/activate"
    
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    log_success "Virtual environment activated"
}

upgrade_pip() {
    log "Upgrading pip..."
    
    pip install --upgrade pip --quiet
    
    log_success "pip upgraded"
}

install_dependencies() {
    log "Installing dependencies..."
    
    # Check if requirements.txt exists
    if [[ ! -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    # Install dependencies
    pip install -r "${SCRIPT_DIR}/requirements.txt" --quiet
    
    log_success "Dependencies installed"
}

create_directories() {
    log "Creating required directories..."
    
    directories=(
        "data"
        "data/map_tiles"
        "data/video_cache"
        "logs"
        "logs/audit"
        "logs/system"
        "logs/detections"
        "models"
        "exports"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "${SCRIPT_DIR}/${dir}"
    done
    
    log_success "Directories created"
}

set_permissions() {
    log "Setting secure file permissions..."
    
    # Set restrictive permissions on sensitive directories
    chmod 700 "${SCRIPT_DIR}/data" 2>/dev/null || true
    chmod 700 "${SCRIPT_DIR}/logs" 2>/dev/null || true
    chmod 700 "${SCRIPT_DIR}/config" 2>/dev/null || true
    
    log_success "Permissions set"
}

download_yolo_model() {
    log "Checking for YOLOv8 model..."
    
    MODEL_PATH="${SCRIPT_DIR}/models/yolov8n.pt"
    
    if [[ -f "${MODEL_PATH}" ]]; then
        log_success "YOLOv8 model already exists"
        return
    fi
    
    log_warning "YOLOv8 model not found at ${MODEL_PATH}"
    echo ""
    echo "For OFFLINE installation, you need to:"
    echo "1. Download yolov8n.pt from https://github.com/ultralytics/assets/releases"
    echo "2. Copy it to: ${MODEL_PATH}"
    echo ""
    
    read -p "Would you like to download the model now? (requires internet) [y/N]: " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Downloading YOLOv8n model..."
        
        # Download using Python/urllib (more portable than curl/wget)
        python3 -c "
import urllib.request
import sys

url = 'https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt'
dest = '${MODEL_PATH}'

print(f'Downloading from {url}...')

try:
    urllib.request.urlretrieve(url, dest)
    print('Download complete!')
except Exception as e:
    print(f'Download failed: {e}')
    sys.exit(1)
"
        
        if [[ $? -eq 0 ]]; then
            log_success "YOLOv8 model downloaded"
        else
            log_error "Failed to download model"
        fi
    else
        log_warning "Skipping model download. Remember to add it manually."
    fi
}

initialize_database() {
    log "Initializing database..."
    
    # Run database initialization
    python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')

from database.db_manager import DatabaseManager

db = DatabaseManager()
db.initialize_database()
print('Database initialized successfully')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "Database initialized"
    else
        log_warning "Database initialization may have issues"
    fi
}

verify_installation() {
    log "Verifying installation..."
    
    # Run verification script
    python3 -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}')

errors = []

# Check imports
try:
    import streamlit
    print('✓ Streamlit installed')
except ImportError as e:
    errors.append(f'Streamlit: {e}')

try:
    import cv2
    print('✓ OpenCV installed')
except ImportError as e:
    errors.append(f'OpenCV: {e}')

try:
    import torch
    print(f'✓ PyTorch installed (CUDA: {torch.cuda.is_available()})')
except ImportError as e:
    errors.append(f'PyTorch: {e}')

try:
    from ultralytics import YOLO
    print('✓ Ultralytics YOLO installed')
except ImportError as e:
    errors.append(f'Ultralytics: {e}')

try:
    import folium
    print('✓ Folium installed')
except ImportError as e:
    errors.append(f'Folium: {e}')

try:
    from cryptography.fernet import Fernet
    print('✓ Cryptography installed')
except ImportError as e:
    errors.append(f'Cryptography: {e}')

# Check local modules
try:
    from config.settings import BASE_DIR
    print('✓ Config module loaded')
except ImportError as e:
    errors.append(f'Config: {e}')

try:
    from core.detection import BorderDetector
    print('✓ Detection module loaded')
except ImportError as e:
    errors.append(f'Detection: {e}')

try:
    from database.db_manager import DatabaseManager
    print('✓ Database module loaded')
except ImportError as e:
    errors.append(f'Database: {e}')

if errors:
    print()
    print('ERRORS:')
    for err in errors:
        print(f'  ✗ {err}')
    sys.exit(1)
else:
    print()
    print('All checks passed!')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "Installation verified"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

print_completion_message() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                        INSTALLATION COMPLETE                                ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "To start the Border Surveillance System:"
    echo ""
    echo "  1. Activate the virtual environment:"
    echo "     source ${VENV_DIR}/bin/activate"
    echo ""
    echo "  2. Run the application:"
    echo "     streamlit run ui/app.py"
    echo ""
    echo "  Or use the run script:"
    echo "     ./run.sh"
    echo ""
    echo -e "${YELLOW}SECURITY REMINDER:${NC}"
    echo "  - Change the default admin password immediately"
    echo "  - Ensure system is air-gapped for production use"
    echo "  - Review audit logs regularly"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_banner
    
    # Initialize log file
    echo "Installation started at $(date)" > "${LOG_FILE}"
    
    log "Starting installation..."
    log "Installation directory: ${SCRIPT_DIR}"
    
    # Run installation steps
    check_python_version
    create_virtual_environment
    activate_virtual_environment
    upgrade_pip
    install_dependencies
    create_directories
    set_permissions
    download_yolo_model
    initialize_database
    verify_installation
    
    print_completion_message
    
    log "Installation completed successfully"
}

# Run main function
main "$@"
