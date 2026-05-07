# 🚀 COMPLETE AWS DEPLOYMENT GUIDE - NeuralTrade Production

**Complete step-by-step guide to deploy your NeuralTrade project on AWS EC2.**  
**Follow these commands EXACTLY in order. No steps should be skipped.**

---

## 📋 PREREQUISITES

### 1. AWS EC2 Instance Requirements
- **OS**: Ubuntu 22.04 LTS (recommended) or Amazon Linux 2023
- **Instance Type**: 
  - Minimum: `t3.medium` (2 vCPU, 4GB RAM)
  - Recommended: `t3.large` (2 vCPU, 8GB RAM) or `t3.xlarge` (4 vCPU, 16GB RAM)
- **Storage**: 30GB+ SSD (gp3 recommended)
- **Region**: Choose closest to your users

### 2. Security Group Configuration
Open these ports in your AWS Security Group:
- **Port 22**: SSH (your IP only)
- **Port 80**: HTTP (0.0.0.0/0)
- **Port 443**: HTTPS (0.0.0.0/0)
- **Port 8000**: Django API (optional, for testing only)
- **Port 3000**: Frontend (optional, for testing only)

### 3. Domain Name (Optional but Recommended)
- Point your domain's A record to your EC2 Elastic IP
- Example: `neuraltrade.com` → `54.123.45.67`

---

## 🔐 STEP 1: CONNECT TO AWS EC2

```bash
# From your local machine, connect to AWS EC2
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP

# Example:
# ssh -i ~/Downloads/my-aws-key.pem ubuntu@54.123.45.67
```

**✅ You should now be connected to your AWS server.**

---

## 📦 STEP 2: INSTALL DOCKER & DOCKER COMPOSE

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git wget nano

# Install Docker (official script)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Add current user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Install Docker Compose (latest version)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# IMPORTANT: Logout and login again for group changes to take effect
exit
```

**Now reconnect to your server:**
```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP
```

**✅ Docker and Docker Compose are now installed.**

---

## 📂 STEP 3: UPLOAD YOUR PROJECT TO AWS

### Option A: Using Git (Recommended)

```bash
# Navigate to home directory
cd ~

# Clone your repository (replace with your actual repo URL)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git neuraltrade

# Navigate into project directory
cd neuraltrade

# Verify files are present
ls -la
```

### Option B: Using SCP (from your local machine)

```bash
# From your LOCAL machine (not AWS), run this command:
# Replace paths with your actual paths
scp -i /path/to/your-key.pem -r /path/to/your/project ubuntu@YOUR_EC2_IP:~/neuraltrade

# Example:
# scp -i ~/Downloads/my-aws-key.pem -r ~/Projects/neuraltrade ubuntu@54.123.45.67:~/neuraltrade

# Then SSH back into AWS and navigate to project
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP
cd ~/neuraltrade
```

**✅ Your project is now on the AWS server.**

---

## ⚙️ STEP 4: CONFIGURE ENVIRONMENT VARIABLES

```bash
# Copy production environment template
cp .env.production .env

# Edit environment file
nano .env
```

**Update these values in the `.env` file:**

```env
# Database Configuration
DB_NAME=neuraltrade
DB_USER=postgres
DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE_123!@#
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Django Configuration
SECRET_KEY=YOUR_RANDOM_SECRET_KEY_MINIMUM_50_CHARACTERS_LONG
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,YOUR_EC2_IP

# Security
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com,http://YOUR_EC2_IP

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Keys (Add your actual Binance API keys)
BINANCE_API_KEY=your_actual_binance_api_key_here
BINANCE_API_SECRET=your_actual_binance_api_secret_here

# WebSocket Configuration
WEBSOCKET_URL=ws://YOUR_EC2_IP/ws
```

**Generate a strong SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Save and exit nano:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

**✅ Environment variables are configured.**

---

## 🏗️ STEP 5: BUILD AND DEPLOY

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

**This script will:**
1. Build all Docker images (Django, Frontend, Nginx)
2. Start all containers (Database, Redis, Django, Celery, Frontend, Nginx)
3. Run database migrations
4. Create superuser
5. Collect static files
6. Initialize reversal zones
7. Start all services

**⏱️ This will take 5-10 minutes. Wait for it to complete.**

**✅ Your application is now deployed!**

---

## 🔍 STEP 6: VERIFY DEPLOYMENT

```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# You should see all containers with status "Up" and "healthy"
```

**Expected output:**
```
NAME                        STATUS
neuraltrade_db              Up (healthy)
neuraltrade_redis           Up (healthy)
neuraltrade_django          Up (healthy)
neuraltrade_celery_worker   Up (healthy)
neuraltrade_celery_beat     Up (healthy)
neuraltrade_frontend        Up (healthy)
neuraltrade_nginx           Up
```

**Test the application:**
```bash
# Test backend API
curl http://localhost/api/health/

# Test frontend
curl http://localhost/

# Test WebSocket
curl -I http://localhost/ws/market/BTCUSD/1m/
```

**✅ All services are running correctly.**

---

## 🌐 STEP 7: ACCESS YOUR APPLICATION

### From Browser:

1. **Frontend Homepage**: `http://YOUR_EC2_IP/`
2. **Live Chart**: `http://YOUR_EC2_IP/asset/btcusd`
3. **Admin Panel**: `http://YOUR_EC2_IP/admin/`
4. **API Health**: `http://YOUR_EC2_IP/api/health/`

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123` (change this immediately!)

**✅ Your application is live and accessible!**

---

## 🔒 STEP 8: SECURE YOUR APPLICATION (IMPORTANT!)

### 8.1 Change Admin Password

```bash
# Access Django shell
docker-compose -f docker-compose.prod.yml exec django python manage.py shell

# In the shell, run:
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
admin.set_password('YOUR_NEW_STRONG_PASSWORD')
admin.save()
exit()
```

### 8.2 Setup SSL/HTTPS (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate (replace with your domain)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Create SSL directory
mkdir -p nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl

# Update nginx configuration to enable HTTPS
nano nginx/nginx.conf
# (Uncomment the SSL server block)

# Restart nginx
docker-compose -f docker-compose.prod.yml up -d nginx
```

### 8.3 Setup Firewall

```bash
# Install UFW firewall
sudo apt install -y ufw

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status
```

**✅ Your application is now secured.**

---

## 📊 STEP 9: MONITOR YOUR APPLICATION

### View Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f django
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f celery_worker
docker-compose -f docker-compose.prod.yml logs -f nginx

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 django
```

### Check System Resources

```bash
# Check Docker container stats (CPU, Memory, Network)
docker stats

# Check disk usage
df -h

# Check Docker disk usage
docker system df
```

### Check Application Health

```bash
# Backend health check
curl http://localhost/api/health/

# Check reversal zones API
curl http://localhost/api/trading/reversal-zones/BTCUSD/?timeframe=1h

# Check signal history
curl http://localhost/api/trading/signal-history/BTCUSD/?timeframe=1h
```

**✅ You can now monitor your application.**

---

## 🔄 STEP 10: AUTO-START ON REBOOT

```bash
# Create systemd service file
sudo nano /etc/systemd/system/neuraltrade.service
```

**Add this content:**
```ini
[Unit]
Description=NeuralTrade Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/neuraltrade
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu
Group=docker

[Install]
WantedBy=multi-user.target
```

**Save and enable the service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable neuraltrade

# Start service now
sudo systemctl start neuraltrade

# Check status
sudo systemctl status neuraltrade
```

**Test reboot:**
```bash
# Reboot server
sudo reboot

# Wait 2-3 minutes, then reconnect
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP

# Check if containers are running
docker ps

# Check if application is accessible
curl http://localhost/api/health/
```

**✅ Your application will now start automatically on server reboot.**

---

## 🛠️ COMMON MAINTENANCE COMMANDS

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart django
docker-compose -f docker-compose.prod.yml restart frontend
docker-compose -f docker-compose.prod.yml restart nginx
```

### Stop Services

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose -f docker-compose.prod.yml down -v
```

### Update Application

```bash
# Pull latest code from Git
cd ~/neuraltrade
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Run migrations (if any)
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput
```

### Database Backup

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres neuraltrade > ~/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# List backups
ls -lh ~/backups/
```

### Database Restore

```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres neuraltrade < ~/backups/backup_20260501_120000.sql
```

### Clear Cache

```bash
# Clear Redis cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Clear Django cache
docker-compose -f docker-compose.prod.yml exec django python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### View Container Shell

```bash
# Access Django container shell
docker-compose -f docker-compose.prod.yml exec django bash

# Access database shell
docker-compose -f docker-compose.prod.yml exec db psql -U postgres neuraltrade

# Access Redis shell
docker-compose -f docker-compose.prod.yml exec redis redis-cli
```

---

## 🐛 TROUBLESHOOTING

### Problem: Containers won't start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Check specific container
docker-compose -f docker-compose.prod.yml logs django

# Rebuild without cache
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Problem: Frontend shows 502 Bad Gateway

```bash
# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Problem: Database connection errors

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

### Problem: WebSocket not connecting

```bash
# Check nginx WebSocket configuration
docker-compose -f docker-compose.prod.yml exec nginx cat /etc/nginx/nginx.conf | grep -A 10 "ws/"

# Check Django logs for WebSocket errors
docker-compose -f docker-compose.prod.yml logs django | grep -i websocket

# Restart nginx and django
docker-compose -f docker-compose.prod.yml restart nginx django
```

### Problem: Out of memory

```bash
# Check memory usage
free -h
docker stats

# Add swap space (4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap
free -h
```

### Problem: Disk space full

```bash
# Check disk usage
df -h

# Clean Docker system
docker system prune -af --volumes

# Remove old logs
sudo find /var/log -type f -name "*.log" -mtime +30 -delete

# Remove old backups
rm ~/backups/backup_*.sql
```

---

## 📈 PERFORMANCE OPTIMIZATION

### 1. Increase Docker Resources

```bash
# Edit Docker daemon config
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

```bash
# Restart Docker
sudo systemctl restart docker

# Restart containers
cd ~/neuraltrade
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Optimize Database

```bash
# Access database
docker-compose -f docker-compose.prod.yml exec db psql -U postgres neuraltrade

# Run these SQL commands:
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

# Exit and restart database
\q
docker-compose -f docker-compose.prod.yml restart db
```

### 3. Enable Redis Persistence

```bash
# Edit docker-compose.prod.yml
nano docker-compose.prod.yml

# Update Redis command to:
# command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru

# Restart Redis
docker-compose -f docker-compose.prod.yml restart redis
```

---

## 🎯 FINAL CHECKLIST

Before going live, verify:

- [ ] All containers are running and healthy
- [ ] Frontend is accessible at `http://YOUR_EC2_IP/`
- [ ] Backend API responds at `http://YOUR_EC2_IP/api/health/`
- [ ] WebSocket connects successfully
- [ ] Admin panel is accessible
- [ ] Admin password has been changed
- [ ] SSL/HTTPS is configured (if using domain)
- [ ] Firewall is enabled and configured
- [ ] Auto-start on reboot is configured
- [ ] Database backups are scheduled
- [ ] Monitoring is set up
- [ ] Environment variables are correct
- [ ] API keys are configured
- [ ] Logs are being written
- [ ] Disk space is sufficient (>10GB free)
- [ ] Memory usage is normal (<80%)

---

## 📞 SUPPORT

If you encounter any issues:

1. **Check logs first**: `docker-compose -f docker-compose.prod.yml logs -f`
2. **Verify all containers are running**: `docker ps`
3. **Check system resources**: `docker stats` and `df -h`
4. **Review this guide's troubleshooting section**
5. **Check environment variables**: `cat .env`

---

## 🎉 SUCCESS!

**Your NeuralTrade application is now live on AWS!**

**Access your application:**
- Frontend: `http://YOUR_EC2_IP/`
- Live Chart: `http://YOUR_EC2_IP/asset/btcusd`
- Admin: `http://YOUR_EC2_IP/admin/`

**What's running:**
- ✅ Frontend (Next.js) - Port 3000
- ✅ Backend (Django) - Port 8000
- ✅ Database (PostgreSQL + TimescaleDB)
- ✅ Cache (Redis)
- ✅ Background Tasks (Celery Worker + Beat)
- ✅ Reverse Proxy (Nginx) - Port 80/443
- ✅ WebSocket Support
- ✅ Auto-restart on failure
- ✅ Health checks
- ✅ Production-ready configuration

**Enjoy your production-ready algorithmic trading platform! 🚀📈**
