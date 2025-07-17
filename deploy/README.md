# EC2 Deployment Guide

This directory contains all the necessary files and scripts for deploying the Insurance Underwriting System on AWS EC2.

## 🚀 Quick Start

### 1. Launch EC2 Instance

**Recommended Configuration:**
- **AMI**: Ubuntu 22.04 LTS
- **Instance Type**: t3.large (2 vCPU, 8GB RAM)
- **Storage**: 20GB GP3
- **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8501 (Streamlit)

### 2. Connect to Your Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Run the Setup Script

```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/jconnelly/insurance-underwriting-system/main/deploy/setup_ec2.sh | sudo bash
```

**Or manually:**

```bash
# Clone the repository
git clone https://github.com/jconnelly/insurance-underwriting-system.git
cd insurance-underwriting-system

# Run setup script
sudo bash deploy/setup_ec2.sh
```

### 4. Configure Environment Variables

```bash
# Copy and edit environment file
cp .env.production .env
nano .env

# Update these key values:
# OPENAI_API_KEY=your_actual_api_key_here
# LANGSMITH_API_KEY=your_langsmith_key_here
# SECRET_KEY=your_random_secret_key
```

### 5. Start the Application

```bash
# Start the service
sudo systemctl start insurance-underwriting

# Enable auto-start on boot
sudo systemctl enable insurance-underwriting

# Check status
sudo systemctl status insurance-underwriting
```

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `setup_ec2.sh` | Complete EC2 setup script |
| `start_app.sh` | Application management script |
| `install_dependencies.sh` | Install Python dependencies |
| `streamlit.service` | Systemd service configuration |
| `nginx.conf` | Nginx reverse proxy configuration |
| `.env.production` | Production environment template |

## 🛠️ Management Commands

### Using the Management Script

```bash
# Start application
./deploy/start_app.sh start

# Stop application
./deploy/start_app.sh stop

# Restart application
./deploy/start_app.sh restart

# Check status and logs
./deploy/start_app.sh status

# Start manually for testing
./deploy/start_app.sh manual
```

### Using Systemd Directly

```bash
# Service management
sudo systemctl start insurance-underwriting
sudo systemctl stop insurance-underwriting
sudo systemctl restart insurance-underwriting
sudo systemctl status insurance-underwriting

# View logs
sudo journalctl -u insurance-underwriting -f
sudo journalctl -u insurance-underwriting -n 50
```

## 🌐 Access Your Application

After successful deployment:

- **Direct Access**: `http://your-ec2-ip:8501`
- **Via Nginx**: `http://your-ec2-ip`
- **Health Check**: `http://your-ec2-ip/health`

## 🔧 Configuration

### Environment Variables

Edit `/opt/insurance-underwriting-system/.env`:

```bash
# Required for AI features
OPENAI_API_KEY=your_openai_api_key

# Optional for AI tracing
LANGSMITH_API_KEY=your_langsmith_api_key

# Security
SECRET_KEY=your_secure_random_key
ALLOWED_HOSTS=your-domain.com,your-ec2-ip
```

### Nginx Configuration

The setup script configures Nginx as a reverse proxy. To customize:

```bash
sudo nano /etc/nginx/sites-available/insurance-underwriting
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Monitoring

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u insurance-underwriting -f

# Recent logs
sudo journalctl -u insurance-underwriting -n 100

# Error logs only
sudo journalctl -u insurance-underwriting -p err
```

### Check System Resources

```bash
# Memory usage
free -h

# Disk usage
df -h

# Process status
ps aux | grep streamlit

# Network connections
sudo netstat -tlnp | grep :8501
```

### Health Checks

```bash
# Check if application is responding
curl -f http://localhost:8501/healthz || echo "Service not responding"

# Check service status
sudo systemctl is-active insurance-underwriting
```

## 🔒 Security Considerations

### Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow necessary ports
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 8501/tcp

# Check status
sudo ufw status
```

### SSL Certificate (Optional)

To enable HTTPS with Let's Encrypt:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo journalctl -u insurance-underwriting -n 50
   # Check for missing dependencies or configuration errors
   ```

2. **Port already in use**:
   ```bash
   sudo netstat -tlnp | grep :8501
   sudo kill -9 <pid>
   ```

3. **Permission errors**:
   ```bash
   sudo chown -R ubuntu:ubuntu /opt/insurance-underwriting-system
   ```

4. **Memory issues**:
   ```bash
   # Check memory usage
   free -h
   # Consider upgrading to larger instance
   ```

### Dependency Issues

```bash
# Reinstall dependencies
cd /opt/insurance-underwriting-system
source venv/bin/activate
pip install -r requirements.txt

# Or try minimal installation
pip install -r requirements-minimal.txt
```

## 📈 Performance Optimization

### Instance Sizing

| Instance Type | vCPU | RAM | Recommended For |
|---------------|------|-----|-----------------|
| t3.medium | 2 | 4GB | Basic deployment |
| t3.large | 2 | 8GB | Recommended |
| t3.xlarge | 4 | 16GB | Heavy AI usage |

### Application Optimization

1. **Disable unused features** in `.env`:
   ```bash
   AI_ENABLED=false  # If no OpenAI key
   LANGCHAIN_TRACING_V2=false  # If no LangSmith key
   ```

2. **Use minimal requirements**:
   ```bash
   pip install -r requirements-minimal.txt
   ```

3. **Enable caching**:
   ```bash
   CACHE_ENABLED=true
   CACHE_TTL=3600
   ```

## 🔄 Updates and Maintenance

### Update Application

```bash
cd /opt/insurance-underwriting-system
git pull origin main
sudo systemctl restart insurance-underwriting
```

### Update Dependencies

```bash
cd /opt/insurance-underwriting-system
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart insurance-underwriting
```

### Backup Important Data

```bash
# Backup configuration
cp .env backups/env-$(date +%Y%m%d)

# Backup rate limiting data
tar -czf backups/rate_limit_data-$(date +%Y%m%d).tar.gz rate_limit_data/

# Backup logs
tar -czf backups/logs-$(date +%Y%m%d).tar.gz logs/
```

## 📞 Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/jconnelly/insurance-underwriting-system/issues)
- Review the main [README.md](../README.md)
- Check the [CLAUDE.md](../CLAUDE.md) for development notes

## 🎯 Cost Optimization

### Estimated Monthly Costs

- **t3.medium**: ~$30/month
- **t3.large**: ~$60/month (recommended)
- **Storage**: ~$2/month (20GB)
- **Data Transfer**: Usually minimal

### Cost-Saving Tips

1. **Stop instance when not needed**
2. **Use spot instances** for development
3. **Enable detailed monitoring** only if needed
4. **Use reserved instances** for production