#!/bin/bash

# =============================================================================
# Health Check Script for Insurance Underwriting System
# =============================================================================
# This script performs comprehensive health checks on the deployed application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="insurance-underwriting"
APP_PORT=8501
HEALTH_URL="http://localhost:${APP_PORT}/healthz"
TIMEOUT=10

echo -e "${GREEN}=== Insurance Underwriting System Health Check ===${NC}"
echo "Timestamp: $(date)"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓ $message${NC}"
    elif [ "$status" = "WARNING" ]; then
        echo -e "${YELLOW}⚠ $message${NC}"
    else
        echo -e "${RED}✗ $message${NC}"
    fi
}

# Function to check service status
check_service_status() {
    echo -e "${YELLOW}=== Service Status ===${NC}"
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_status "OK" "Service is running"
        
        # Get service uptime
        local uptime=$(systemctl show $SERVICE_NAME --property=ActiveEnterTimestamp | cut -d= -f2)
        echo "  Service started: $uptime"
        
        # Check if service is enabled
        if systemctl is-enabled --quiet $SERVICE_NAME; then
            print_status "OK" "Service is enabled (auto-start)"
        else
            print_status "WARNING" "Service is not enabled for auto-start"
        fi
        
        return 0
    else
        print_status "ERROR" "Service is not running"
        return 1
    fi
}

# Function to check network connectivity
check_network() {
    echo -e "\n${YELLOW}=== Network Status ===${NC}"
    
    # Check if port is listening
    if netstat -tln | grep -q ":${APP_PORT}"; then
        print_status "OK" "Port ${APP_PORT} is listening"
    else
        print_status "ERROR" "Port ${APP_PORT} is not listening"
        return 1
    fi
    
    # Check local HTTP response
    if curl -f -s -m $TIMEOUT $HEALTH_URL > /dev/null; then
        print_status "OK" "Health endpoint responding"
    else
        print_status "ERROR" "Health endpoint not responding"
        return 1
    fi
    
    return 0
}

# Function to check system resources
check_resources() {
    echo -e "\n${YELLOW}=== System Resources ===${NC}"
    
    # Check memory usage
    local memory_info=$(free -m)
    local memory_usage=$(echo "$memory_info" | awk 'NR==2{printf "%.1f", $3/$2*100}')
    local memory_available=$(echo "$memory_info" | awk 'NR==2{printf "%.0f", $7}')
    
    echo "Memory usage: ${memory_usage}% (${memory_available}MB available)"
    
    if (( $(echo "$memory_usage < 80" | bc -l) )); then
        print_status "OK" "Memory usage is normal"
    elif (( $(echo "$memory_usage < 90" | bc -l) )); then
        print_status "WARNING" "Memory usage is high"
    else
        print_status "ERROR" "Memory usage is critical"
    fi
    
    # Check disk usage
    local disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    echo "Disk usage: ${disk_usage}%"
    
    if [ $disk_usage -lt 80 ]; then
        print_status "OK" "Disk usage is normal"
    elif [ $disk_usage -lt 90 ]; then
        print_status "WARNING" "Disk usage is high"
    else
        print_status "ERROR" "Disk usage is critical"
    fi
    
    # Check CPU load
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    echo "CPU load (1min): $cpu_load"
    
    # Check process status
    local process_count=$(ps aux | grep -c streamlit || echo "0")
    echo "Streamlit processes: $process_count"
    
    if [ $process_count -gt 0 ]; then
        print_status "OK" "Application processes are running"
    else
        print_status "ERROR" "No application processes found"
    fi
}

# Function to check application health
check_application() {
    echo -e "\n${YELLOW}=== Application Health ===${NC}"
    
    # Check if application directory exists
    if [ -d "/opt/insurance-underwriting-system" ]; then
        print_status "OK" "Application directory exists"
    else
        print_status "ERROR" "Application directory not found"
        return 1
    fi
    
    # Check if virtual environment exists
    if [ -d "/opt/insurance-underwriting-system/venv" ]; then
        print_status "OK" "Python virtual environment exists"
    else
        print_status "ERROR" "Python virtual environment not found"
        return 1
    fi
    
    # Check if main application file exists
    if [ -f "/opt/insurance-underwriting-system/streamlit_main.py" ]; then
        print_status "OK" "Main application file exists"
    else
        print_status "ERROR" "Main application file not found"
        return 1
    fi
    
    # Check if environment file exists
    if [ -f "/opt/insurance-underwriting-system/.env" ]; then
        print_status "OK" "Environment configuration file exists"
    else
        print_status "WARNING" "Environment configuration file not found"
    fi
    
    # Check log directory
    if [ -d "/opt/insurance-underwriting-system/logs" ]; then
        print_status "OK" "Log directory exists"
        
        # Check for recent log entries
        local log_files=$(find /opt/insurance-underwriting-system/logs -name "*.log" -mtime -1 | wc -l)
        if [ $log_files -gt 0 ]; then
            print_status "OK" "Recent log files found"
        else
            print_status "WARNING" "No recent log files found"
        fi
    else
        print_status "WARNING" "Log directory not found"
    fi
}

# Function to check dependencies
check_dependencies() {
    echo -e "\n${YELLOW}=== Dependencies Check ===${NC}"
    
    # Switch to application directory and activate virtual environment
    cd /opt/insurance-underwriting-system
    source venv/bin/activate
    
    # Check core dependencies
    if python -c "import streamlit" 2>/dev/null; then
        local streamlit_version=$(python -c "import streamlit; print(streamlit.__version__)")
        print_status "OK" "Streamlit installed (v$streamlit_version)"
    else
        print_status "ERROR" "Streamlit not installed"
    fi
    
    if python -c "import pandas" 2>/dev/null; then
        print_status "OK" "Pandas installed"
    else
        print_status "ERROR" "Pandas not installed"
    fi
    
    if python -c "import numpy" 2>/dev/null; then
        print_status "OK" "NumPy installed"
    else
        print_status "ERROR" "NumPy not installed"
    fi
    
    # Check optional dependencies
    if python -c "import openai" 2>/dev/null; then
        print_status "OK" "OpenAI package installed"
    else
        print_status "WARNING" "OpenAI package not installed (AI features disabled)"
    fi
    
    if python -c "import langchain" 2>/dev/null; then
        print_status "OK" "LangChain package installed"
    else
        print_status "WARNING" "LangChain package not installed (AI features limited)"
    fi
    
    # Test application import
    if python -c "import sys; sys.path.insert(0, 'src'); from underwriting.streamlit_app.app import main" 2>/dev/null; then
        print_status "OK" "Application modules can be imported"
    else
        print_status "ERROR" "Application modules cannot be imported"
    fi
}

# Function to check nginx (if installed)
check_nginx() {
    echo -e "\n${YELLOW}=== Nginx Status ===${NC}"
    
    if command -v nginx &> /dev/null; then
        if systemctl is-active --quiet nginx; then
            print_status "OK" "Nginx is running"
            
            # Check nginx configuration
            if nginx -t 2>/dev/null; then
                print_status "OK" "Nginx configuration is valid"
            else
                print_status "ERROR" "Nginx configuration has errors"
            fi
        else
            print_status "WARNING" "Nginx is installed but not running"
        fi
    else
        print_status "WARNING" "Nginx is not installed"
    fi
}

# Function to generate summary
generate_summary() {
    echo -e "\n${YELLOW}=== Health Check Summary ===${NC}"
    
    local overall_status="OK"
    
    # Check service status
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        overall_status="ERROR"
    fi
    
    # Check network connectivity
    if ! curl -f -s -m $TIMEOUT $HEALTH_URL > /dev/null; then
        overall_status="ERROR"
    fi
    
    # Check memory usage
    local memory_usage=$(free -m | awk 'NR==2{printf "%.1f", $3/$2*100}')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        overall_status="ERROR"
    fi
    
    # Print overall status
    if [ "$overall_status" = "OK" ]; then
        print_status "OK" "Overall system health is good"
        echo -e "\n${GREEN}✓ System is healthy and ready to serve requests${NC}"
    else
        print_status "ERROR" "System has issues that need attention"
        echo -e "\n${RED}✗ System requires immediate attention${NC}"
    fi
    
    echo ""
    echo "Access URLs:"
    echo "  Local: http://localhost:${APP_PORT}"
    echo "  External: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-server-ip'):${APP_PORT}"
    
    if command -v nginx &> /dev/null && systemctl is-active --quiet nginx; then
        echo "  Via Nginx: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'your-server-ip')"
    fi
}

# Main execution
main() {
    check_service_status
    check_network
    check_resources
    check_application
    check_dependencies
    check_nginx
    generate_summary
}

# Run main function
main

# Exit with error code if any critical issues found
if ! systemctl is-active --quiet $SERVICE_NAME || ! curl -f -s -m $TIMEOUT $HEALTH_URL > /dev/null; then
    exit 1
fi

exit 0