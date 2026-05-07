# AWS Deployment Guide - NeuralTrade

Complete guide to deploy NeuralTrade (Frontend + Backend) on AWS using Docker.

---

## Prerequisites

1. **AWS EC2 Instance**
   - Ubuntu 22.04 LTS or Amazon Linux 2023
   - Minimum: t3.medium (2 vCPU, 4GB RAM)
   - Recommended: t3.large (2 vCPU, 8GB RAM)
   - Storage: 30GB+ SSD

2. **Security Group Rules**
   - Port 22 (SSH)
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
   - Port 8000 (Django - optional, for testing)
   - Port 3000 (Frontend - optional, for testing)

---

## Step 1: Connect to AWS EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

---

## Step 2: Install Docker & Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login again for group changes
exit
```

---

## Step 3: Upload Project to AWS

### Option A: Using Git (Recommended)

```bash
# On AWS server
cd ~
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Option B: Using SCP (from your local machine)

```bash
# From your local machine
scp -i your-key.pem -r /path/to/project ubuntu@your-ec2-ip:~/neuraltrade
```

---

## Step 4: Configure Environment Variables

```bash
# Copy production environment file
cp .env.production .env

# Edit environment variables
nano .env
```

**Update these values:**
```env
DB_PASSWORD=YOUR_STRONG_PASSWORD_HERE
SECRET_KEY=YOUR_RANDOM_SECRET_KEY_50_CHARS_MIN
ALLOWED_HOSTS=your-domain.com,your-ec2-ip
CSRF_TRUSTED_ORIGINS=https://your-domain.com
BINANCE_API_KEY=your_actual_api_key
BINANCE_API_SECRET=your_actual_api_secret
```

**Generate SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 5: Deploy with One Command

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**That's it! Everything will be deployed automatically.**

---

## Step 6: Verify Deployment

```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl http://localhost/api/health/
curl http://localhost
```

---

## Access Your Application

- **Frontend**: `http://your-ec2-ip` or `http://your-domain.com`
- **Backend API**: `http://your-ec2-ip/api/`
- **Admin Panel**: `http://your-ec2-ip/admin/`

---

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f django
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart django
docker-compose -f docker-compose.prod.yml restart frontend
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./deploy.sh
```

### Database Backup
```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres neuraltrade > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres neuraltrade < backup_20260428.sql
```

### Clean Up
```bash
# Remove all containers and volumes
docker-compose -f docker-compose.prod.yml down -v

# Remove unused images
docker system prune -af
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Check container status
docker ps -a
```

### Database connection issues
```bash
# Check database is running
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "SELECT 1"

# Reset database (WARNING: deletes all data)
docker-compose -f docker-compose.prod.yml down -v
./deploy.sh
```

### Frontend not loading
```bash
# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Out of memory
```bash
# Check memory usage
docker stats

# Increase swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## SSL/HTTPS Setup (Optional but Recommended)

### Using Let's Encrypt (Free SSL)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to nginx folder
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Update nginx.conf to use SSL (uncomment SSL section)
nano nginx/nginx.conf

# Restart nginx
docker-compose -f docker-compose.prod.yml up -d nginx
```

---

## Monitoring

### Check System Resources
```bash
# CPU and Memory
docker stats

# Disk usage
df -h
docker system df
```

### Check Application Health
```bash
# Health check endpoints
curl http://localhost/api/health/
curl http://localhost/api/trading/reversal-zones/BTCUSD/
```

---

## Auto-Start on Reboot

```bash
# Create systemd service
sudo nano /etc/systemd/system/neuraltrade.service
```

Add this content:
```ini
[Unit]
Description=NeuralTrade Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/neuraltrade
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable neuraltrade
sudo systemctl start neuraltrade
sudo systemctl status neuraltrade
```

---

## Performance Optimization

### 1. Enable Docker BuildKit
```bash
export DOCKER_BUILDKIT=1
```

### 2. Optimize Docker Images
Already optimized in Dockerfile with multi-stage builds.

### 3. Configure Nginx Caching
Already configured in nginx.conf with gzip compression.

### 4. Database Optimization
```bash
# Increase shared_buffers (inside container)
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -c "ALTER SYSTEM SET shared_buffers = '256MB';"
docker-compose -f docker-compose.prod.yml restart db
```

---

## Security Best Practices

1. ✅ Change default passwords in `.env`
2. ✅ Use strong SECRET_KEY
3. ✅ Set DEBUG=False in production
4. ✅ Configure ALLOWED_HOSTS properly
5. ✅ Use HTTPS with SSL certificates
6. ✅ Keep Docker and system updated
7. ✅ Use AWS Security Groups to restrict access
8. ✅ Regular backups of database
9. ✅ Monitor logs for suspicious activity
10. ✅ Use environment variables for secrets

---

## Support

If you encounter issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Verify all containers are running: `docker ps`
3. Check system resources: `docker stats`
4. Review this guide's troubleshooting section

---

## Summary

**One-Command Deployment:**
```bash
./deploy.sh
```

**That's it! Your application is now running on AWS with:**
- ✅ Frontend (Next.js)
- ✅ Backend (Django)
- ✅ Database (PostgreSQL)
- ✅ Cache (Redis)
- ✅ Background Tasks (Celery)
- ✅ Reverse Proxy (Nginx)
- ✅ All services in Docker
- ✅ Auto-restart on failure
- ✅ Health checks
- ✅ Production-ready configuration
