#!/bin/bash

# =============================================================================
# Start Application Script
# =============================================================================
# This script starts the Insurance Underwriting System application

set -e

# Configuration
APP_DIR="/opt/insurance-underwriting-system"
SERVICE_NAME="insurance-underwriting"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting Insurance Underwriting System ===${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   echo "Please run as the application user (ubuntu)"
   exit 1
fi

# Change to application directory
cd $APP_DIR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Please run setup_ec2.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating default .env file..."
    cp .env.production .env
    echo "Please update .env with your actual API keys"
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if service is running
check_service() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}Service is running${NC}"
        return 0
    else
        echo -e "${RED}Service is not running${NC}"
        return 1
    fi
}

# Function to start service
start_service() {
    echo -e "${YELLOW}Starting systemd service...${NC}"
    sudo systemctl start $SERVICE_NAME
    sleep 3
    
    if check_service; then
        echo -e "${GREEN}Service started successfully!${NC}"
    else
        echo -e "${RED}Failed to start service${NC}"
        echo "Check logs with: sudo journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

# Function to start manually (for testing)
start_manual() {
    echo -e "${YELLOW}Starting application manually...${NC}"
    echo "Press Ctrl+C to stop"
    
    # Start Streamlit
    streamlit run streamlit_main.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false
}

# Function to show status
show_status() {
    echo -e "${YELLOW}=== Service Status ===${NC}"
    sudo systemctl status $SERVICE_NAME --no-pager
    
    echo -e "\n${YELLOW}=== Recent Logs ===${NC}"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
    
    echo -e "\n${YELLOW}=== System Resources ===${NC}"
    echo "Memory usage:"
    ps aux | grep streamlit | grep -v grep | awk '{print $6/1024 " MB"}'
    
    echo -e "\n${YELLOW}=== Network Status ===${NC}"
    echo "Listening on:"
    sudo netstat -tlnp | grep :8501 || echo "Port 8501 not listening"
}

# Function to stop service
stop_service() {
    echo -e "${YELLOW}Stopping service...${NC}"
    sudo systemctl stop $SERVICE_NAME
    echo -e "${GREEN}Service stopped${NC}"
}

# Function to restart service
restart_service() {
    echo -e "${YELLOW}Restarting service...${NC}"
    sudo systemctl restart $SERVICE_NAME
    sleep 3
    
    if check_service; then
        echo -e "${GREEN}Service restarted successfully!${NC}"
    else
        echo -e "${RED}Failed to restart service${NC}"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  start       Start the service (default)"
    echo "  stop        Stop the service"
    echo "  restart     Restart the service"
    echo "  status      Show service status and logs"
    echo "  manual      Start manually (for testing)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 restart"
}

# Main logic
case "${1:-start}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    manual)
        start_manual
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}Invalid option: $1${NC}"
        show_help
        exit 1
        ;;
esac

echo -e "\n${GREEN}=== Access Information ===${NC}"
echo "Local access: http://localhost:8501"
echo "Network access: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo "Via Nginx: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"