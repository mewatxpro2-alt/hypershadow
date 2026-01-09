#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                    CLASSIFIED - RUN SCRIPT                                   ║
# ║                        Border Surveillance System                             ║
# ║                                                                              ║
# ║  Purpose: Launch the surveillance dashboard                                   ║
# ║  Security Level: CONFIDENTIAL                                                 ║
# ║  Version: 1.0.0                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
# USAGE:
#   ./run.sh [--port PORT] [--no-browser]
#
# OPTIONS:
#   --port PORT      Specify port number (default: 8501)
#   --no-browser     Don't open browser automatically
#   --debug          Enable debug mode

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
APP_FILE="${SCRIPT_DIR}/ui/app.py"
DEFAULT_PORT=8501
OPEN_BROWSER=true
DEBUG_MODE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

PORT=$DEFAULT_PORT

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# FUNCTIONS
# =============================================================================

print_banner() {
    clear
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                    ${RED}CLASSIFIED${NC} - BORDER SURVEILLANCE SYSTEM                    ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                              Launching...                                    ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_venv() {
    if [[ ! -d "${VENV_DIR}" ]]; then
        echo -e "${RED}Error:${NC} Virtual environment not found."
        echo "Please run ./install.sh first."
        exit 1
    fi
}

activate_venv() {
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "${VENV_DIR}/bin/activate"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    python3 -c "import streamlit" 2>/dev/null || {
        echo -e "${RED}Error:${NC} Streamlit not installed."
        exit 1
    }
    
    echo -e "${GREEN}✓${NC} Dependencies OK"
}

start_application() {
    echo ""
    echo -e "${GREEN}Starting Border Surveillance System...${NC}"
    echo -e "Port: ${PORT}"
    echo -e "URL: http://localhost:${PORT}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Build streamlit command
    STREAMLIT_OPTS=""
    
    # Server options
    STREAMLIT_OPTS+=" --server.port=${PORT}"
    STREAMLIT_OPTS+=" --server.address=localhost"  # Only listen on localhost for security
    
    # Browser options
    if [[ "$OPEN_BROWSER" == "false" ]]; then
        STREAMLIT_OPTS+=" --server.headless=true"
    fi
    
    # Security options
    STREAMLIT_OPTS+=" --server.enableCORS=false"
    STREAMLIT_OPTS+=" --server.enableXsrfProtection=true"
    
    # Theme (dark mode for military aesthetic)
    STREAMLIT_OPTS+=" --theme.base=dark"
    STREAMLIT_OPTS+=" --theme.primaryColor=#4ade80"
    STREAMLIT_OPTS+=" --theme.backgroundColor=#0a0a0a"
    STREAMLIT_OPTS+=" --theme.secondaryBackgroundColor=#1a1a1a"
    STREAMLIT_OPTS+=" --theme.textColor=#e6e6e6"
    
    # Debug options
    if [[ "$DEBUG_MODE" == "true" ]]; then
        STREAMLIT_OPTS+=" --logger.level=debug"
    fi
    
    # Run streamlit
    streamlit run "${APP_FILE}" ${STREAMLIT_OPTS}
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    
    # Log shutdown
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] System shutdown" >> "${SCRIPT_DIR}/logs/system/startup.log"
    
    exit 0
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    # Set up signal handlers
    trap cleanup SIGINT SIGTERM
    
    print_banner
    check_venv
    activate_venv
    check_dependencies
    
    # Log startup
    mkdir -p "${SCRIPT_DIR}/logs/system"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] System startup on port ${PORT}" >> "${SCRIPT_DIR}/logs/system/startup.log"
    
    start_application
}

main "$@"
