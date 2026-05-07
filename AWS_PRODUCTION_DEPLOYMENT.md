# 🚀 AWS Production Deployment Guide - Complete Step-by-Step

**Production-Ready Deployment for NeuralTrade Trading Platform**

This guide contains EVERY command you need to deploy your project to AWS. Follow each step exactly as written.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EC2 Setup](#aws-ec2-setup)
3. [Server Preparation](#server-preparation)
4. [Project Upload](#project-upload)
5. [Environment Configuration](#environment-configuration)
6. [Docker Installation](#docker-installation)
7. [Production Deployment](#production-deployment)
8. [SSL/HTTPS Setup](#ssl-https-setup)
9. [Verification & Testing](#verification-testing)
10. [Maintenance Commands](#maintenance-commands)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

### AWS Requirements
- **EC2 Instance**: t3.large (2 vCPU, 8GB RAM) - Recommended
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB+ SSD
- **Elastic IP**: Assigned to your instance
- **Domain**: (Optional) Pointed to your Elastic IP

### Security Group Configuration
Open these ports in your AWS Security Group:
- **22** (SSH) - Your IP only
- **80** (HTTP) - 0.0.0.0/0
- **443** (HTTPS) - 0.0.0.0/0

### Local Requirements
- SSH key pair (.pem file)
- Git installed (if using Git method)
- Your project code ready

---

## 🖥️ AWS EC2 Setup

### Step 1: Launch EC2 Instance

1. Go to AWS Console → EC2 → Launch Instance
2. **Name**: `neuraltrade-production`
3. **AMI**: Ubuntu Server 22.04 LTS
4. **Instance Type**: t3.large
5. **Key Pair**: Create new or select existing
6. **Storage**: 30GB gp3
7. **Security Group**: Create with ports 22, 80, 443
8. Click **Launch Instance**

### Step 2: Allocate Elastic IP

```bash
# In AWS Console:
# EC2 → Elastic IPs → Allocate Elastic IP address
# Then: Actions → Associate Elastic IP address → Select your instance
```

### Step 3: Connect to Your Instance

```bash
# From your local machine
# Replace YOUR_KEY.pem with your actual key file
# Replace YOUR_EC2_IP with your Elastic IP

chmod 400 YOUR_KEY.pem
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP
```

**✅ You should now be connected to your AWS server**

---

## 🔧 Server Preparation

### Step 1: Update System

```bash
# Update package lists
sudo apt update

# Upgrade all packages (this may take 5-10 minutes)
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git nano htop net-tools
```

### Step 2: Set Timezone (Optional but Recommended)

```bash
# Set to UTC (recommended for servers)
sudo timedatectl set-timezone UTC

# Or set to your timezone
# sudo timedatectl set-timezone America/New_York

# Verify
timedatectl
```

### Step 3: Increase System Limits

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Increase max user processes
echo "* soft nproc 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nproc 65536" | sudo tee -a /etc/security/limits.conf
```

### Step 4: Create Swap Space (Important for 8GB RAM)

```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile

# Set permissions
sudo chmod 600 /swapfile

# Make it a swap file
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Make it permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is active
free -h
```

**✅ Server preparation complete**

---

## 📦 Docker Installation

### Step 1: Install Docker

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run installation script
sudo sh get-docker.sh

# Add current user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Clean up
rm get-docker.sh
```

### Step 2: Install Docker Compose

```bash
# Download latest Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink (optional, for convenience)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

### Step 3: Verify Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Test Docker (should show "Hello from Docker!")
docker run hello-world
```

### Step 4: Logout and Login Again

```bash
# This is REQUIRED for group changes to take effect
exit

# Then reconnect
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP
```

**✅ Docker installation complete**

---

## 📁 Project Upload

### Method 1: Using Git (Recommended)

```bash
# Navigate to home directory
cd ~

# Clone your repository
# Replace with your actual repository URL
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git neuraltrade

# Navigate to project directory
cd neuraltrade

# Verify files are present
ls -la
```

### Method 2: Using SCP (From Your Local Machine)

```bash
# From your LOCAL machine (not AWS server)
# Navigate to your project directory
cd /path/to/your/project

# Upload entire project to AWS
scp -i YOUR_KEY.pem -r . ubuntu@YOUR_EC2_IP:~/neuraltrade

# Then connect to AWS and navigate to project
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP
cd ~/neuraltrade
```

### Method 3: Using SFTP (Alternative)

```bash
# From your LOCAL machine
sftp -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP

# In SFTP prompt:
put -r /path/to/your/project neuraltrade
exit

# Then connect to AWS
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP
cd ~/neuraltrade
```

**✅ Project uploaded to AWS**

---

## ⚙️ Environment Configuration

### Step 1: Create Production Environment File

```bash
# Navigate to project directory
cd ~/neuraltrade

# Copy example environment file
cp .env.example .env.production

# Edit production environment
nano .env.production
```

### Step 2: Configure Environment Variables

**Copy and paste this template, then update the values:**

```env
# ═══════════════════════════════════════════════════════════════
# PRODUCTION ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# ─── Django Settings ───────────────────────────────────────────
DEBUG=False
SECRET_KEY=GENERATE_THIS_BELOW
ALLOWED_HOSTS=YOUR_EC2_IP,YOUR_DOMAIN.com,www.YOUR_DOMAIN.com
CSRF_TRUSTED_ORIGINS=https://YOUR_DOMAIN.com,https://www.YOUR_DOMAIN.com

# ─── Database Settings ─────────────────────────────────────────
DB_NAME=neuraltrade
DB_USER=postgres
DB_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD
DB_HOST=db
DB_PORT=5432

# ─── Redis Settings ────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# ─── Celery Settings ───────────────────────────────────────────
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ─── API Keys ──────────────────────────────────────────────────
BINANCE_API_KEY=your_actual_binance_api_key_here
BINANCE_API_SECRET=your_actual_binance_api_secret_here

# ─── Security ──────────────────────────────────────────────────
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# ─── CORS Settings ─────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=https://YOUR_DOMAIN.com,https://www.YOUR_DOMAIN.com

# ─── Email Settings (Optional) ─────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# ─── Logging ───────────────────────────────────────────────────
LOG_LEVEL=INFO
```

### Step 3: Generate SECRET_KEY

```bash
# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Copy the output and paste it as SECRET_KEY in .env.production
```

### Step 4: Generate Strong Database Password

```bash
# Generate a strong database password
openssl rand -base64 32

# Copy the output and paste it as DB_PASSWORD in .env.production
```

### Step 5: Update Specific Values

**Edit .env.production and replace:**
- `YOUR_EC2_IP` → Your actual Elastic IP (e.g., `54.123.45.67`)
- `YOUR_DOMAIN.com` → Your actual domain (or remove if no domain)
- `CHANGE_THIS_TO_STRONG_PASSWORD` → The password you generated above
- `GENERATE_THIS_BELOW` → The SECRET_KEY you generated above
- `your_actual_binance_api_key_here` → Your real Binance API key
- `your_actual_binance_api_secret_here` → Your real Binance API secret

**Save the file:**
- Press `Ctrl + O` to save
- Press `Enter` to confirm
- Press `Ctrl + X` to exit

### Step 6: Copy to .env

```bash
# Copy production config to .env (used by Docker)
cp .env.production .env

# Verify the file
cat .env | grep -v "SECRET\|PASSWORD\|API"
```

**✅ Environment configuration complete**

---

## 🚀 Production Deployment

### Step 1: Make Deploy Script Executable

```bash
# Navigate to project directory
cd ~/neuraltrade

# Make deploy script executable
chmod +x deploy.sh

# Verify it's executable
ls -la deploy.sh
```

### Step 2: Run Deployment

```bash
# Run the deployment script
# This will:
# - Build all Docker images
# - Start all containers
# - Run database migrations
# - Create superuser
# - Collect static files
# - Start all services

./deploy.sh
```

**⏱️ This will take 10-15 minutes on first run**

### Step 3: Monitor Deployment

```bash
# Watch the deployment progress
# Press Ctrl+C to stop watching (containers keep running)

docker-compose -f docker-compose.prod.yml logs -f
```

**Look for these success messages:**
- ✅ `django_1 | Starting server...`
- ✅ `frontend_1 | Ready in XXXms`
- ✅ `nginx_1 | start worker processes`
- ✅ `celery_worker_1 | celery@... ready`
- ✅ `celery_beat_1 | beat: Starting...`

### Step 4: Verify All Containers Are Running

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# You should see 7 containers running:
# - neuraltrade_django
# - neuraltrade_frontend
# - neuraltrade_nginx
# - neuraltrade_db
# - neuraltrade_redis
# - neuraltrade_celery_worker
# - neuraltrade_celery_beat
```

**✅ Production deployment complete**

---

## 🔒 SSL/HTTPS Setup (Recommended)

### Prerequisites
- Domain name pointed to your Elastic IP
- Ports 80 and 443 open in Security Group

### Step 1: Install Certbot

```bash
# Install Certbot and Nginx plugin
sudo apt install -y certbot python3-certbot-nginx
```

### Step 2: Stop Nginx Temporarily

```bash
# Stop nginx container
docker-compose -f docker-compose.prod.yml stop nginx
```

### Step 3: Obtain SSL Certificate

```bash
# Replace YOUR_DOMAIN.com with your actual domain
sudo certbot certonly --standalone \
  -d YOUR_DOMAIN.com \
  -d www.YOUR_DOMAIN.com \
  --email your_email@example.com \
  --agree-tos \
  --no-eff-email
```

### Step 4: Copy Certificates to Project

```bash
# Create SSL directory
mkdir -p ~/neuraltrade/nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/YOUR_DOMAIN.com/fullchain.pem ~/neuraltrade/nginx/ssl/
sudo cp /etc/letsencrypt/live/YOUR_DOMAIN.com/privkey.pem ~/neuraltrade/nginx/ssl/

# Set permissions
sudo chown -R $USER:$USER ~/neuraltrade/nginx/ssl
chmod 644 ~/neuraltrade/nginx/ssl/*.pem
```

### Step 5: Update Nginx Configuration

```bash
# Edit nginx configuration
nano ~/neuraltrade/nginx/nginx.conf
```

**Add this SSL server block:**

```nginx
# HTTPS server
server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Rest of your nginx configuration...
    # (copy from the HTTP server block)
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;
    return 301 https://$server_name$request_uri;
}
```

### Step 6: Update Environment for HTTPS

```bash
# Edit .env
nano ~/neuraltrade/.env
```

**Update these values:**
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Step 7: Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Verify HTTPS is working
curl -I https://YOUR_DOMAIN.com
```

### Step 8: Auto-Renew SSL Certificate

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add this line (runs twice daily):
0 0,12 * * * certbot renew --quiet --post-hook "docker-compose -f /home/ubuntu/neuraltrade/docker-compose.prod.yml restart nginx"
```

**✅ SSL/HTTPS setup complete**

---

## ✅ Verification & Testing

### Step 1: Test Frontend

```bash
# Test homepage
curl -I http://YOUR_EC2_IP

# Should return: HTTP/1.1 200 OK
```

### Step 2: Test Backend API

```bash
# Test health endpoint
curl http://YOUR_EC2_IP/api/health/

# Should return: {"status":"healthy",...}
```

### Step 3: Test WebSocket

```bash
# Test WebSocket connection (should upgrade to 101)
curl -I -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://YOUR_EC2_IP/ws/market/BTCUSD/1m/
```

### Step 4: Test Database

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d neuraltrade

# Run test query
SELECT COUNT(*) FROM reversal_zones;

# Exit
\q
```

### Step 5: Access Admin Panel

```bash
# Get superuser credentials (if you forgot)
docker-compose -f docker-compose.prod.yml logs django | grep "Superuser"

# Or create new superuser
docker-compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

**Then visit:** `http://YOUR_EC2_IP/admin/`

### Step 6: Test Trading Signals

```bash
# Trigger signal calculation
curl -X POST http://YOUR_EC2_IP/api/trading/calculate-history/all/

# Check signals
curl http://YOUR_EC2_IP/api/trading/signal-history/BTCUSD/?timeframe=1h
```

### Step 7: Browser Testing

**Open in your browser:**
1. `http://YOUR_EC2_IP` - Homepage
2. `http://YOUR_EC2_IP/asset/btcusd` - Trading chart
3. `http://YOUR_EC2_IP/admin/` - Admin panel

**✅ All tests should pass**

---

## 🔧 Maintenance Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f django
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 django
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart django
docker-compose -f docker-compose.prod.yml restart frontend
docker-compose -f docker-compose.prod.yml restart nginx
```

### Stop Services

```bash
# Stop all (containers remain)
docker-compose -f docker-compose.prod.yml stop

# Stop and remove containers
docker-compose -f docker-compose.prod.yml down

# Stop and remove everything including volumes (⚠️ DELETES DATA)
docker-compose -f docker-compose.prod.yml down -v
```

### Update Application

```bash
# Pull latest code
cd ~/neuraltrade
git pull origin main

# Rebuild and restart
./deploy.sh
```

### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres neuraltrade > backup_$(date +%Y%m%d_%H%M%S).sql

# List backups
ls -lh backup_*.sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres neuraltrade < backup_20260501_120000.sql
```

### Clear Redis Cache

```bash
# Clear all cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Clear specific keys
docker-compose -f docker-compose.prod.yml exec redis redis-cli KEYS "signal:*"
docker-compose -f docker-compose.prod.yml exec redis redis-cli DEL "signal:last:BTCUSD:1m"
```

### Monitor Resources

```bash
# Real-time container stats
docker stats

# Disk usage
df -h
docker system df

# Memory usage
free -h

# CPU usage
htop
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Check container status
docker ps -a

# Rebuild specific container
docker-compose -f docker-compose.prod.yml build --no-cache [service-name]
docker-compose -f docker-compose.prod.yml up -d [service-name]
```

### Database Connection Error

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### WebSocket Not Connecting

```bash
# Check Django logs
docker-compose -f docker-compose.prod.yml logs django | grep -i websocket

# Check nginx WebSocket configuration
docker-compose -f docker-compose.prod.yml exec nginx cat /etc/nginx/nginx.conf | grep -A 10 "ws/"

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Increase swap if needed
sudo swapoff /swapfile
sudo rm /swapfile
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Port Already in Use

```bash
# Check what's using port 80
sudo lsof -i :80

# Kill process using port
sudo kill -9 [PID]

# Or change port in docker-compose.prod.yml
```

### SSL Certificate Issues

```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renew
sudo certbot renew --force-renewal
```

---

## 🔄 Auto-Start on Reboot

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/neuraltrade.service
```

**Paste this content:**

```ini
[Unit]
Description=NeuralTrade Docker Compose Application
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/neuraltrade
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0
User=ubuntu
Group=docker

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable neuraltrade

# Start service now
sudo systemctl start neuraltrade

# Check status
sudo systemctl status neuraltrade

# Test reboot
sudo reboot

# After reboot, verify containers are running
docker ps
```

**✅ Auto-start configured**

---

## 📊 Monitoring & Alerts

### Setup CloudWatch (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb

# Configure CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### Setup Email Alerts (Optional)

```bash
# Install mailutils
sudo apt install -y mailutils

# Test email
echo "Test email from NeuralTrade server" | mail -s "Test" your_email@example.com
```

---

## 🎯 Performance Optimization

### Enable Docker BuildKit

```bash
# Add to ~/.bashrc
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc
source ~/.bashrc
```

### Optimize PostgreSQL

```bash
# Edit PostgreSQL config
docker-compose -f docker-compose.prod.yml exec db bash -c "cat >> /var/lib/postgresql/data/postgresql.conf << EOF
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
EOF"

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

### Enable Nginx Caching

Already configured in `nginx/nginx.conf` with:
- Gzip compression
- Browser caching
- Static file caching

---

## 📝 Final Checklist

Before going live, verify:

- [ ] All containers are running (`docker ps`)
- [ ] Frontend loads (`http://YOUR_EC2_IP`)
- [ ] Backend API works (`http://YOUR_EC2_IP/api/health/`)
- [ ] WebSocket connects (check browser console)
- [ ] Database is accessible
- [ ] Redis is working
- [ ] Celery tasks are running
- [ ] SSL certificate installed (if using HTTPS)
- [ ] Environment variables are correct
- [ ] Backups are configured
- [ ] Auto-start on reboot is enabled
- [ ] Monitoring is setup
- [ ] Security group rules are correct
- [ ] Domain DNS is configured (if using domain)

---

## 🎉 Success!

Your NeuralTrade platform is now running in production on AWS!

**Access your application:**
- Frontend: `http://YOUR_EC2_IP` or `https://YOUR_DOMAIN.com`
- Admin: `http://YOUR_EC2_IP/admin/`
- API: `http://YOUR_EC2_IP/api/`

**Next steps:**
1. Test all features thoroughly
2. Set up regular backups
3. Configure monitoring and alerts
4. Add your domain and SSL
5. Optimize performance based on usage

---

## 📞 Support

If you encounter any issues:

1. Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Verify containers: `docker ps`
3. Check resources: `docker stats`
4. Review troubleshooting section above
5. Check environment variables: `cat .env | grep -v SECRET`

---

## 🔐 Security Reminders

- ✅ Change all default passwords
- ✅ Use strong SECRET_KEY
- ✅ Keep DEBUG=False in production
- ✅ Configure ALLOWED_HOSTS properly
- ✅ Use HTTPS with SSL certificates
- ✅ Regular security updates
- ✅ Monitor logs for suspicious activity
- ✅ Regular database backups
- ✅ Restrict SSH access to your IP only
- ✅ Use AWS Security Groups effectively

---

**🚀 Your production deployment is complete!**

