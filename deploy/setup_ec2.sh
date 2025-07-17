#!/bin/bash

# =============================================================================
# EC2 Setup Script for Insurance Underwriting System
# =============================================================================
# This script sets up a complete production environment on Ubuntu 22.04 LTS
# Run this script as root or with sudo privileges

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="insurance-underwriting"
APP_USER="ubuntu"
APP_DIR="/opt/insurance-underwriting-system"
SERVICE_NAME="insurance-underwriting"
PYTHON_VERSION="3.11"

echo -e "${GREEN}=== Insurance Underwriting System EC2 Setup ===${NC}"
echo "Starting setup process..."

# Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update && apt-get upgrade -y

# Install required system packages
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-pip \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    nginx \
    supervisor \
    htop \
    nano \
    vim

# Create application directory
echo -e "${YELLOW}Creating application directory...${NC}"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# Switch to application user
echo -e "${YELLOW}Setting up application as user: $APP_USER${NC}"
sudo -u $APP_USER bash << 'EOF'
cd /opt/insurance-underwriting-system

# Clone repository if not already present
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/jconnelly/insurance-underwriting-system.git .
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p backups

# Set up environment file
if [ ! -f ".env" ]; then
    echo "Creating environment file..."
    cat > .env << 'ENVEOF'
# Production Environment Variables
# Copy this file and update with your actual values

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# API Keys (update with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Insurance-Underwriting-System

# Database Settings (if needed)
DATABASE_URL=sqlite:///data/underwriting.db

# Security Settings
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENVEOF
fi

echo "Python environment setup complete!"
EOF

# Create Streamlit configuration
echo -e "${YELLOW}Creating Streamlit configuration...${NC}"
mkdir -p $APP_DIR/.streamlit
cat > $APP_DIR/.streamlit/config.toml << 'STREAMLITEOF'
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f8ff"
textColor = "#262730"

[logger]
level = "info"
STREAMLITEOF

# Create systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/${SERVICE_NAME}.service << 'SERVICEEOF'
[Unit]
Description=Insurance Underwriting System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/insurance-underwriting-system
Environment=PATH=/opt/insurance-underwriting-system/venv/bin
ExecStart=/opt/insurance-underwriting-system/venv/bin/streamlit run streamlit_main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

# Output to syslog
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=insurance-underwriting

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Create nginx configuration
echo -e "${YELLOW}Creating Nginx configuration...${NC}"
cat > /etc/nginx/sites-available/${SERVICE_NAME} << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Increase timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXEOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Create log rotation configuration
echo -e "${YELLOW}Setting up log rotation...${NC}"
cat > /etc/logrotate.d/${SERVICE_NAME} << 'LOGROTATEEOF'
/opt/insurance-underwriting-system/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload insurance-underwriting
    endscript
}
LOGROTATEEOF

# Set proper permissions
chown -R $APP_USER:$APP_USER $APP_DIR
chmod +x $APP_DIR/deploy/*.sh

# Reload systemd and start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl enable nginx
systemctl start nginx

# Configure firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo -e "${YELLOW}Configuring firewall...${NC}"
    ufw --force enable
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw allow 8501/tcp
fi

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Update /opt/insurance-underwriting-system/.env with your API keys"
echo "2. Start the application: sudo systemctl start ${SERVICE_NAME}"
echo "3. Check status: sudo systemctl status ${SERVICE_NAME}"
echo "4. View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "Access your application at:"
echo "- Direct: http://your-server-ip:8501"
echo "- Via Nginx: http://your-server-ip"
echo ""
echo "To get your server's public IP:"
echo "curl -s http://169.254.169.254/latest/meta-data/public-ipv4"