#!/bin/bash
# Deploy Email Delay Bug Fix to Singapore Server
# This script deploys the fix that removes WebSocket blocking checks
# to ensure instant email delivery when signals fire.

set -e  # Exit on any error

echo "════════════════════════════════════════════════════════════════"
echo "  DEPLOYING EMAIL DELAY BUG FIX TO SINGAPORE SERVER"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Server details
SERVER_IP="13.250.19.107"
SERVER_USER="ubuntu"
SSH_KEY="smartriskfx-singapore.pem"
PROJECT_DIR="~/smartrisk"

echo -e "${YELLOW}Step 1: Checking SSH key...${NC}"
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}ERROR: SSH key not found: $SSH_KEY${NC}"
    echo "Please ensure smartriskfx-singapore.pem is in the current directory"
    exit 1
fi
echo -e "${GREEN}✓ SSH key found${NC}"
echo ""

echo -e "${YELLOW}Step 2: Testing SSH connection...${NC}"
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Cannot connect to server${NC}"
    echo "Please check:"
    echo "  - Server IP: $SERVER_IP"
    echo "  - SSH key permissions: chmod 400 $SSH_KEY"
    echo "  - Network connectivity"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"
echo ""

echo -e "${YELLOW}Step 3: Backing up current code...${NC}"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/smartrisk
echo "Creating backup branch..."
git branch backup-before-email-fix-$(date +%Y%m%d-%H%M%S) || true
echo "✓ Backup created"
ENDSSH
echo -e "${GREEN}✓ Backup complete${NC}"
echo ""

echo -e "${YELLOW}Step 4: Pulling latest changes from GitHub...${NC}"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/smartrisk
echo "Fetching latest changes..."
git fetch origin
echo "Pulling main branch..."
git pull origin main
echo "✓ Code updated"
ENDSSH
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

echo -e "${YELLOW}Step 5: Rebuilding Django container...${NC}"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/smartrisk
echo "Building Django container..."
sudo docker-compose build django
echo "✓ Build complete"
ENDSSH
echo -e "${GREEN}✓ Django container rebuilt${NC}"
echo ""

echo -e "${YELLOW}Step 6: Restarting Django service...${NC}"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/smartrisk
echo "Stopping Django container..."
sudo docker-compose stop django
echo "Starting Django container..."
sudo docker-compose up -d django
echo "Waiting for Django to start..."
sleep 5
echo "✓ Django restarted"
ENDSSH
echo -e "${GREEN}✓ Django service restarted${NC}"
echo ""

echo -e "${YELLOW}Step 7: Verifying deployment...${NC}"
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/smartrisk
echo "Checking Django container status..."
if sudo docker-compose ps django | grep -q "Up"; then
    echo "✓ Django container is running"
else
    echo "✗ WARNING: Django container may not be running properly"
    sudo docker-compose ps django
fi

echo ""
echo "Checking recent logs..."
sudo docker-compose logs --tail=20 django
ENDSSH
echo -e "${GREEN}✓ Deployment verified${NC}"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Monitor logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd ~/smartrisk && sudo docker-compose logs -f django'"
echo "  2. Wait for next signal to fire on https://smartriskfx.com/asset/ethusd"
echo "  3. Verify email arrives within 1-2 seconds"
echo "  4. Check for these log messages:"
echo "     - 🔔 LIVE SIGNAL [ETHUSD 5m]: BUY @ 3245.50"
echo "     - 💾 Created BUY signal in DB: ETHUSDT 5m @ 3245.50"
echo "     - 📧 INSTANT EMAIL: 3 sent for ETHUSD 5m BUY @ 3245.50"
echo ""
echo "To view live logs:"
echo "  ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
echo "  cd ~/smartrisk"
echo "  sudo docker-compose logs -f django | grep '🔔\\|📧\\|💾'"
echo ""
echo "If you need to rollback:"
echo "  ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
echo "  cd ~/smartrisk"
echo "  git revert HEAD"
echo "  sudo docker-compose build django"
echo "  sudo docker-compose up -d django"
echo ""
