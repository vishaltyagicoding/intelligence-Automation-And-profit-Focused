#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# AWS PRODUCTION DEPLOYMENT - QUICK COMMAND REFERENCE
# ═══════════════════════════════════════════════════════════════════════════════
# Copy and paste these commands in order on your AWS EC2 instance
# Replace YOUR_EC2_IP, YOUR_DOMAIN, YOUR_KEY.pem with actual values
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# STEP 1: CONNECT TO AWS (Run from your LOCAL machine)
# ───────────────────────────────────────────────────────────────────────────────
chmod 400 YOUR_KEY.pem
ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP

# ───────────────────────────────────────────────────────────────────────────────
# STEP 2: UPDATE SYSTEM (Run on AWS server)
# ───────────────────────────────────────────────────────────────────────────────
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano htop net-tools

# ───────────────────────────────────────────────────────────────────────────────
# STEP 3: CREATE SWAP SPACE
# ───────────────────────────────────────────────────────────────────────────────
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h

# ───────────────────────────────────────────────────────────────────────────────
# STEP 4: INSTALL DOCKER
# ───────────────────────────────────────────────────────────────────────────────
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# ───────────────────────────────────────────────────────────────────────────────
# STEP 5: INSTALL DOCKER COMPOSE
# ───────────────────────────────────────────────────────────────────────────────
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker --version
docker-compose --version

# ───────────────────────────────────────────────────────────────────────────────
# STEP 6: LOGOUT AND LOGIN (REQUIRED!)
# ───────────────────────────────────────────────────────────────────────────────
exit
# Then reconnect: ssh -i YOUR_KEY.pem ubuntu@YOUR_EC2_IP

# ───────────────────────────────────────────────────────────────────────────────
# STEP 7: UPLOAD PROJECT (Choose ONE method)
# ───────────────────────────────────────────────────────────────────────────────

# Method A: Using Git (Recommended)
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git neuraltrade
cd neuraltrade

# Method B: Using SCP (from LOCAL machine)
# scp -i YOUR_KEY.pem -r /path/to/project ubuntu@YOUR_EC2_IP:~/neuraltrade

# ───────────────────────────────────────────────────────────────────────────────
# STEP 8: CONFIGURE ENVIRONMENT
# ───────────────────────────────────────────────────────────────────────────────
cd ~/neuraltrade
cp .env.example .env.production

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate DB_PASSWORD
openssl rand -base64 32

# Edit environment file
nano .env.production

# Update these values in .env.production:
# - SECRET_KEY=<generated_key>
# - DB_PASSWORD=<generated_password>
# - ALLOWED_HOSTS=YOUR_EC2_IP,YOUR_DOMAIN.com
# - BINANCE_API_KEY=your_actual_key
# - BINANCE_API_SECRET=your_actual_secret

# Copy to .env
cp .env.production .env

# ───────────────────────────────────────────────────────────────────────────────
# STEP 9: DEPLOY APPLICATION
# ───────────────────────────────────────────────────────────────────────────────
chmod +x deploy.sh
./deploy.sh

# Monitor deployment (Ctrl+C to exit, containers keep running)
docker-compose -f docker-compose.prod.yml logs -f

# ───────────────────────────────────────────────────────────────────────────────
# STEP 10: VERIFY DEPLOYMENT
# ───────────────────────────────────────────────────────────────────────────────

# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Test frontend
curl -I http://localhost

# Test backend API
curl http://localhost/api/health/

# Test database
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d neuraltrade -c "SELECT 1"

# ───────────────────────────────────────────────────────────────────────────────
# STEP 11: SETUP SSL (Optional but Recommended)
# ───────────────────────────────────────────────────────────────────────────────

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx
docker-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate
sudo certbot certonly --standalone \
  -d YOUR_DOMAIN.com \
  -d www.YOUR_DOMAIN.com \
  --email your_email@example.com \
  --agree-tos \
  --no-eff-email

# Copy certificates
mkdir -p ~/neuraltrade/nginx/ssl
sudo cp /etc/letsencrypt/live/YOUR_DOMAIN.com/fullchain.pem ~/neuraltrade/nginx/ssl/
sudo cp /etc/letsencrypt/live/YOUR_DOMAIN.com/privkey.pem ~/neuraltrade/nginx/ssl/
sudo chown -R $USER:$USER ~/neuraltrade/nginx/ssl

# Update .env for HTTPS
nano ~/neuraltrade/.env
# Set: SECURE_SSL_REDIRECT=True
# Set: SESSION_COOKIE_SECURE=True
# Set: CSRF_COOKIE_SECURE=True

# Restart services
docker-compose -f docker-compose.prod.yml restart

# ───────────────────────────────────────────────────────────────────────────────
# STEP 12: SETUP AUTO-START ON REBOOT
# ───────────────────────────────────────────────────────────────────────────────

# Create systemd service
sudo tee /etc/systemd/system/neuraltrade.service > /dev/null <<EOF
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
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable neuraltrade
sudo systemctl start neuraltrade
sudo systemctl status neuraltrade

# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT COMPLETE! 🎉
# ═══════════════════════════════════════════════════════════════════════════════
# Access your application:
# - Frontend: http://YOUR_EC2_IP or https://YOUR_DOMAIN.com
# - Admin: http://YOUR_EC2_IP/admin/
# - API: http://YOUR_EC2_IP/api/
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# USEFUL MAINTENANCE COMMANDS
# ───────────────────────────────────────────────────────────────────────────────

# View logs
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml logs -f django
docker-compose -f docker-compose.prod.yml logs -f frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart
docker-compose -f docker-compose.prod.yml restart django

# Stop services
docker-compose -f docker-compose.prod.yml stop
docker-compose -f docker-compose.prod.yml down

# Update application
cd ~/neuraltrade
git pull origin main
./deploy.sh

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres neuraltrade > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres neuraltrade < backup_20260501_120000.sql

# Clear Redis cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Monitor resources
docker stats
free -h
df -h

# Clean up Docker
docker system prune -a

# ───────────────────────────────────────────────────────────────────────────────
# TROUBLESHOOTING COMMANDS
# ───────────────────────────────────────────────────────────────────────────────

# Check container status
docker ps -a

# Check specific container logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Rebuild specific container
docker-compose -f docker-compose.prod.yml build --no-cache [service-name]
docker-compose -f docker-compose.prod.yml up -d [service-name]

# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"

# Check port usage
sudo lsof -i :80
sudo lsof -i :443

# Check SSL certificate
sudo certbot certificates

# Renew SSL certificate
sudo certbot renew

# ═══════════════════════════════════════════════════════════════════════════════
# END OF QUICK COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════
