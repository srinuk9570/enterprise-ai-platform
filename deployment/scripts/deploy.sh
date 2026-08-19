#!/bin/bash
# Deployment script for Enterprise AI Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Enterprise AI Platform Deployment Script${NC}"
echo "================================================"

# Configuration
APP_DIR="/opt/enterprise-ai-platform"
VENV_DIR="$APP_DIR/.venv"
USER="aiplatform"
GROUP="aiplatform"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Create user if not exists
if ! id "$USER" &>/dev/null; then
    echo -e "${YELLOW}Creating user $USER...${NC}"
    useradd -m -s /bin/bash "$USER"
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/data"/{database,vector_store,uploads,generated,logs,cache,sessions,exports,backups}
chown -R "$USER:$GROUP" "$APP_DIR"

# Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}Updating repository...${NC}"
    cd "$APP_DIR"
    sudo -u "$USER" git pull origin main
else
    echo -e "${YELLOW}Cloning repository...${NC}"
    sudo -u "$USER" git clone https://github.com/yourusername/enterprise-ai-platform.git "$APP_DIR"
fi

# Set up Python virtual environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
cd "$APP_DIR"
sudo -u "$USER" python3 -m venv "$VENV_DIR"
sudo -u "$USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$USER" "$VENV_DIR/bin/pip" install -r requirements/prod.txt

# Copy environment file if not exists
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo -e "${RED}Please edit $APP_DIR/.env with your configuration!${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
cd "$APP_DIR"
sudo -u "$USER" "$VENV_DIR/bin/python" scripts/init_data_directories.py

# Install systemd services
echo -e "${YELLOW}Installing systemd services...${NC}"
cp "$APP_DIR/deployment/systemd/backend.service" /etc/systemd/system/
cp "$APP_DIR/deployment/systemd/frontend.service" /etc/systemd/system/

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable backend.service
systemctl enable frontend.service

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl start backend.service
systemctl start frontend.service

# Check status
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Service Status:"
systemctl status backend.service --no-pager
systemctl status frontend.service --no-pager
echo ""
echo -e "${GREEN}✅ Access the application at:${NC}"
echo "   Frontend: http://localhost:8501"
echo "   API: http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  systemctl status backend    - Check backend status"
echo "  systemctl restart backend   - Restart backend"
echo "  journalctl -u backend -f    - View backend logs"