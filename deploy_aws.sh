#!/bin/bash

###############################################################################
# SmartRisk AWS EC2 Deployment Script
# One-command deployment for production
###############################################################################

set -e  # Exit on error

echo "=========================================================================="
echo "🚀 SmartRisk AWS EC2 Deployment"
echo "=========================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo bash deploy_aws.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Step 1: Installing system dependencies...${NC}"
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    software-properties-common

echo -e "${GREEN}✅ System dependencies installed${NC}"
echo ""

echo -e "${YELLOW}📋 Step 2: Installing Docker...${NC}"
# Remove old Docker versions
apt-get remove -y docker docker-engine docker.io containerd runc || true

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
systemctl start docker
systemctl enable docker

echo -e "${GREEN}✅ Docker installed${NC}"
echo ""

echo -e "${YELLOW}📋 Step 3: Installing Docker Compose...${NC}"
# Install Docker Compose v2
DOCKER_COMPOSE_VERSION="2.24.0"
curl -SL "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

echo -e "${GREEN}✅ Docker Compose installed${NC}"
docker-compose --version
echo ""

echo -e "${YELLOW}📋 Step 4: Configuring firewall (UFW)...${NC}"
# Allow SSH, HTTP, HTTPS, and application ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Django API
ufw allow 8001/tcp  # WebSocket
ufw --force enable

echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

echo -e "${YELLOW}📋 Step 5: Setting up environment variables...${NC}"
# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env file with production settings"
    echo "Copy from .env.example and update values"
    exit 1
fi

echo -e "${GREEN}✅ Environment file found${NC}"
echo ""

echo -e "${YELLOW}📋 Step 6: Building Docker images...${NC}"
docker-compose build --no-cache

echo -e "${GREEN}✅ Docker images built${NC}"
echo ""

echo -e "${YELLOW}📋 Step 7: Starting services...${NC}"
docker-compose down || true  # Stop any existing containers
docker-compose up -d

echo -e "${GREEN}✅ Services started${NC}"
echo ""

echo -e "${YELLOW}📋 Step 8: Waiting for services to be healthy...${NC}"
sleep 30

# Check service health
echo "Checking service status..."
docker-compose ps

echo ""
echo -e "${YELLOW}📋 Step 9: Running database migrations...${NC}"
docker-compose exec -T django python manage.py migrate --noinput

echo -e "${GREEN}✅ Migrations completed${NC}"
echo ""

echo -e "${YELLOW}📋 Step 10: Creating superuser (if needed)...${NC}"
docker-compose exec -T django python manage.py shell << 'END'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='alberttyagi123@gmail.com').exists():
    print('Creating alberttyagi123@gmail.com superuser...')
    user = User.objects.create_superuser(
        email='alberttyagi123@gmail.com',
        username='alberttyagi',
        password='SmartRisk@2026!',
        first_name='Albert',
        last_name='Tyagi'
    )
    print('✅ Superuser created')
else:
    print('✅ Superuser already exists')
END

echo ""
echo -e "${YELLOW}📋 Step 11: Configuring Celery Beat tasks...${NC}"
docker-compose exec -T django python << 'END'
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

# 1. Trial expiration task (every 1 minute)
interval, _ = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.MINUTES,
)

task, created = PeriodicTask.objects.update_or_create(
    name='check-expired-subscriptions',
    defaults={
        'task': 'users.tasks.check_and_expire_subscriptions',
        'interval': interval,
        'enabled': True,
    }
)

if created:
    print('✅ Trial expiration task created (every 1 minute)')
else:
    print('✅ Trial expiration task already exists (every 1 minute)')

# 2. Signal update task (every 15 minutes)
try:
    signal_task = PeriodicTask.objects.get(name='update-all-recent-signals-every-30min')
    cron, _ = CrontabSchedule.objects.get_or_create(
        minute='*/15',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='Asia/Kolkata'
    )
    signal_task.crontab = cron
    signal_task.save()
    print('✅ Signal update task updated (every 15 minutes)')
except:
    print('⚠️  Signal update task not found (will be created on first run)')
END

echo ""
echo -e "${YELLOW}📋 Step 12: Checking service logs...${NC}"
echo "Django logs:"
docker-compose logs --tail=10 django

echo ""
echo "Celery Beat logs:"
docker-compose logs --tail=10 celery_beat

echo ""
echo "Celery Worker logs:"
docker-compose logs --tail=10 celery_worker

echo ""
echo "=========================================================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=========================================================================="
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://$(curl -s ifconfig.me)"
echo "   API:      http://$(curl -s ifconfig.me):8000"
echo "   Admin:    http://$(curl -s ifconfig.me):8000/admin/"
echo ""
echo "👤 Superuser Credentials:"
echo "   Email:    alberttyagi123@gmail.com"
echo "   Password: SmartRisk@2026!"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        docker-compose logs -f [service]"
echo "   Restart service:  docker-compose restart [service]"
echo "   Stop all:         docker-compose down"
echo "   Start all:        docker-compose up -d"
echo ""
echo "🔧 Services Running:"
echo "   ✅ PostgreSQL (TimescaleDB)"
echo "   ✅ Redis"
echo "   ✅ Django (Daphne ASGI)"
echo "   ✅ Celery Worker"
echo "   ✅ Celery Beat"
echo "   ✅ Next.js Frontend"
echo "   ✅ Nginx"
echo ""
echo "=========================================================================="
