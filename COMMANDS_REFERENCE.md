# 📋 Commands Reference - SmartRisk

## 🚀 One-Time EC2 Setup Commands

### Complete Setup Script (Copy-Paste All)
```bash
#!/bin/bash
# SmartRisk EC2 Setup - Run this ONCE on new EC2 instance

echo "Starting SmartRisk EC2 Setup..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker prerequisites
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django API
sudo ufw allow 8001/tcp  # WebSocket
sudo ufw --force enable

# Create project directory
mkdir -p ~/smartrisk

# Verify installations
echo ""
echo "=== Verification ==="
echo "Docker: $(docker --version)"
echo "Docker Compose: $(docker-compose --version)"
echo ""
echo "✅ Setup Complete!"
echo ""
echo "⚠️  IMPORTANT: Logout and login again for docker group changes!"
echo "Run: exit"
echo "Then: ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
```

---

## 🔍 Verification Commands

### After Setup, Verify Docker Works
```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Test Docker without sudo (should work after logout/login)
docker ps

# Check disk space
df -h

# Check memory
free -h

# Check firewall status
sudo ufw status
```

---

## 📦 Deployment Commands

### Local Machine (Your Computer)
```bash
# Navigate to project
cd /path/to/your/smartrisk/project

# Check status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Production deployment"

# Push to GitHub (triggers automatic deployment)
git push origin main
```

---

## 🐳 Docker Commands (On EC2)

### Check Services Status
```bash
# Navigate to project
cd ~/smartrisk

# Check all services
sudo docker-compose ps

# Check specific service
sudo docker-compose ps django
sudo docker-compose ps celery_beat
```

### View Logs
```bash
# All services (last 50 lines)
sudo docker-compose logs --tail=50

# Specific service
sudo docker-compose logs django --tail=100
sudo docker-compose logs celery_beat --tail=50
sudo docker-compose logs celery_worker --tail=50
sudo docker-compose logs frontend --tail=50

# Follow logs (real-time)
sudo docker-compose logs -f django
```

### Restart Services
```bash
# Restart all services
sudo docker-compose restart

# Restart specific service
sudo docker-compose restart django
sudo docker-compose restart celery_beat
sudo docker-compose restart celery_worker
```

### Stop/Start Services
```bash
# Stop all services
sudo docker-compose down

# Start all services
sudo docker-compose up -d

# Start specific service
sudo docker-compose up -d django
```

### Rebuild Services
```bash
# Rebuild all images
sudo docker-compose build

# Rebuild specific service
sudo docker-compose build django
sudo docker-compose build frontend

# Rebuild and restart
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

---

## 🗄️ Database Commands

### Access Database
```bash
# PostgreSQL shell
sudo docker-compose exec db psql -U smartrisk_user -d smartrisk_db

# Inside PostgreSQL:
\dt              # List tables
\d users_user    # Describe table
SELECT * FROM users_user LIMIT 5;
\q               # Quit
```

### Run Migrations
```bash
# Run migrations
sudo docker-compose exec django python manage.py migrate

# Check migration status
sudo docker-compose exec django python manage.py showmigrations

# Create new migrations
sudo docker-compose exec django python manage.py makemigrations
```

### Database Backup
```bash
# Create backup
sudo docker-compose exec -T db pg_dump -U smartrisk_user smartrisk_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo docker-compose exec -T db psql -U smartrisk_user smartrisk_db < backup_20260508_120000.sql
```

---

## 🔴 Redis Commands

### Access Redis
```bash
# Redis CLI
sudo docker-compose exec redis redis-cli

# Inside Redis:
PING              # Test connection
KEYS *            # List all keys
GET key_name      # Get value
FLUSHALL          # Clear all data (careful!)
exit              # Quit
```

### Check Redis Status
```bash
# Ping Redis
sudo docker-compose exec redis redis-cli ping

# Get Redis info
sudo docker-compose exec redis redis-cli info
```

---

## 🎯 Django Management Commands

### Create Superuser
```bash
# Interactive
sudo docker-compose exec django python manage.py createsuperuser

# Non-interactive (scripted)
sudo docker-compose exec django python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'password123')
EOF
```

### Collect Static Files
```bash
sudo docker-compose exec django python manage.py collectstatic --noinput
```

### Django Shell
```bash
# Open Django shell
sudo docker-compose exec django python manage.py shell

# Inside shell:
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.all()
exit()
```

### Check Django Settings
```bash
# Show settings
sudo docker-compose exec django python manage.py diffsettings

# Check for issues
sudo docker-compose exec django python manage.py check
```

---

## ⏰ Celery Commands

### Check Celery Status
```bash
# Celery Beat logs
sudo docker-compose logs celery_beat --tail=50

# Celery Worker logs
sudo docker-compose logs celery_worker --tail=50

# Check active tasks
sudo docker-compose exec celery_worker celery -A neuraltrade inspect active

# Check scheduled tasks
sudo docker-compose exec celery_worker celery -A neuraltrade inspect scheduled
```

### Restart Celery
```bash
# Restart both
sudo docker-compose restart celery_beat celery_worker

# Restart individually
sudo docker-compose restart celery_beat
sudo docker-compose restart celery_worker
```

### Check Periodic Tasks
```bash
# Django shell
sudo docker-compose exec django python manage.py shell

# Inside shell:
from django_celery_beat.models import PeriodicTask
PeriodicTask.objects.all()
PeriodicTask.objects.filter(enabled=True)
exit()
```

---

## 🏥 Health Check Commands

### Check All Services
```bash
# Service status
sudo docker-compose ps

# Health checks
sudo docker-compose exec django curl -f http://localhost:8000/health/
sudo docker-compose exec redis redis-cli ping
sudo docker-compose exec db pg_isready -U smartrisk_user
```

### System Resources
```bash
# Disk usage
df -h

# Memory usage
free -h

# Docker disk usage
sudo docker system df

# Container resource usage
sudo docker stats --no-stream
```

### Network Check
```bash
# Check open ports
sudo netstat -tulpn | grep LISTEN

# Check firewall
sudo ufw status

# Test API endpoint
curl http://localhost:8000/health/

# Test frontend
curl http://localhost:3000
```

---

## 🧹 Cleanup Commands

### Remove Unused Docker Resources
```bash
# Remove stopped containers
sudo docker container prune -f

# Remove unused images
sudo docker image prune -a -f

# Remove unused volumes
sudo docker volume prune -f

# Remove everything unused
sudo docker system prune -a -f --volumes
```

### Clear Logs
```bash
# Truncate Docker logs
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log

# Clear application logs
sudo docker-compose exec django rm -rf /app/logs/*.log
```

---

## 🔧 Troubleshooting Commands

### Django Won't Start
```bash
# Check logs
sudo docker-compose logs django --tail=200

# Check if port is in use
sudo netstat -tulpn | grep 8000

# Try manual start
sudo docker-compose up django

# Check script permissions
sudo docker-compose exec django ls -la /app/scripts/
```

### Database Connection Issues
```bash
# Check database is running
sudo docker-compose ps db

# Check database logs
sudo docker-compose logs db --tail=100

# Test connection
sudo docker-compose exec django python manage.py dbshell
```

### Frontend Issues
```bash
# Check frontend logs
sudo docker-compose logs frontend --tail=100

# Rebuild frontend
sudo docker-compose build frontend
sudo docker-compose up -d frontend

# Check frontend health
curl http://localhost:3000/api/health
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu ~/smartrisk

# Fix docker permissions
sudo chmod 666 /var/run/docker.sock

# Re-add user to docker group
sudo usermod -aG docker ubuntu
newgrp docker
```

---

## 📊 Monitoring Commands

### Real-time Logs
```bash
# Follow all logs
sudo docker-compose logs -f

# Follow specific service
sudo docker-compose logs -f django
sudo docker-compose logs -f celery_beat
```

### Container Stats
```bash
# Real-time stats
sudo docker stats

# One-time stats
sudo docker stats --no-stream
```

### Check Celery Tasks
```bash
# Active tasks
sudo docker-compose exec celery_worker celery -A neuraltrade inspect active

# Registered tasks
sudo docker-compose exec celery_worker celery -A neuraltrade inspect registered

# Stats
sudo docker-compose exec celery_worker celery -A neuraltrade inspect stats
```

---

## 🔐 Security Commands

### Check Firewall
```bash
# UFW status
sudo ufw status verbose

# List rules
sudo ufw status numbered

# Add rule
sudo ufw allow 8080/tcp

# Delete rule
sudo ufw delete [number]
```

### Check Open Ports
```bash
# All listening ports
sudo netstat -tulpn | grep LISTEN

# Specific port
sudo netstat -tulpn | grep :8000
```

---

## 📝 Useful Aliases (Optional)

Add to `~/.bashrc` for shortcuts:

```bash
# Add these to ~/.bashrc
alias dps='cd ~/smartrisk && sudo docker-compose ps'
alias dlogs='cd ~/smartrisk && sudo docker-compose logs'
alias drestart='cd ~/smartrisk && sudo docker-compose restart'
alias ddown='cd ~/smartrisk && sudo docker-compose down'
alias dup='cd ~/smartrisk && sudo docker-compose up -d'

# Reload bashrc
source ~/.bashrc
```

---

## 🎯 Quick Reference

### Most Used Commands
```bash
# Check services
cd ~/smartrisk && sudo docker-compose ps

# View Django logs
sudo docker-compose logs django --tail=50

# Restart all services
sudo docker-compose restart

# Rebuild and restart
sudo docker-compose down && sudo docker-compose build && sudo docker-compose up -d
```

---

## ⚠️ Important Notes

### DO NOT Run:
- ❌ `docker-compose` without `sudo` (unless you've logged out/in after setup)
- ❌ `rm -rf` commands without double-checking
- ❌ `FLUSHALL` in Redis production
- ❌ Database drops in production

### Always Run:
- ✅ Check logs before restarting: `sudo docker-compose logs [service]`
- ✅ Verify services after restart: `sudo docker-compose ps`
- ✅ Test health endpoints after changes
- ✅ Backup database before major changes

---

**Keep this file handy for quick reference!** 📚
