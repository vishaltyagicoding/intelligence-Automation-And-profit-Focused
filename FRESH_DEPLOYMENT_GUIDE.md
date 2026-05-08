# Fresh Deployment Guide - t3.large Instance

## ✅ Prerequisites Completed
- [x] New EC2 instance: t3.large or m7i-flex.large
- [x] Security group with all required ports
- [x] SSH key pair (smartriskfx.pem)

---

## 📋 Step 1: Launch Instance Settings

When launching your new instance, use these settings:

### Instance Configuration:
- **AMI**: Ubuntu Server 26.04 LTS
- **Instance Type**: t3.large or m7i-flex.large
- **Key Pair**: smartriskfx (existing)
- **Storage**: 30 GB gp3

### Security Group Rules:
| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Django API |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend |

---

## 🚀 Step 2: After Instance Launches

### Get the New IP Address:
Once instance is running, note the **Public IPv4 address**

Example: `54.183.XXX.XXX`

---

## 🔧 Step 3: Initial Server Setup

SSH into your new server:

```bash
ssh -i "smartriskfx (1).pem" ubuntu@YOUR_NEW_IP
```

Then run these commands:

```bash
# Update system
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version

# Logout and login again for docker group to take effect
exit
```

---

## 📦 Step 4: Deploy Application

SSH back in:

```bash
ssh -i "smartriskfx (1).pem" ubuntu@YOUR_NEW_IP
```

Clone and setup:

```bash
# Clone repository
git clone https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused.git smartrisk
cd smartrisk

# Create .env file
cat > .env << 'EOF'
# Django Settings
SECRET_KEY=b%jb$1*+ege5^u+kn7q83zs=65e1(6n-txkg--k3#*tvf1e4ex
DEBUG=False
ALLOWED_HOSTS=smartriskfx.com,www.smartriskfx.com,YOUR_NEW_IP,localhost,127.0.0.1

# Database
DB_NAME=smartrisk_db
DB_USER=smartrisk_user
DB_PASSWORD=SmartRisk@2026!
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=alberttyagi123@gmail.com
EMAIL_HOST_PASSWORD=YOUR_GMAIL_APP_PASSWORD
DEFAULT_FROM_EMAIL=alberttyagi123@gmail.com

# Trading APIs
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Frontend URL
NEXT_PUBLIC_API_URL=http://YOUR_NEW_IP:8000
NEXT_PUBLIC_WS_URL=ws://YOUR_NEW_IP:8001
EOF

# Replace YOUR_NEW_IP with actual IP
nano .env  # Edit and save (Ctrl+X, Y, Enter)

# Build and start services
docker-compose build
docker-compose up -d

# Wait for services to start
sleep 60

# Check services
docker-compose ps
```

---

## 🗄️ Step 5: Setup Database

```bash
# Run migrations
docker-compose exec django python manage.py migrate

# Create superusers
docker-compose exec django python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()

# Create alberttyagi123@gmail.com
if not User.objects.filter(email='alberttyagi123@gmail.com').exists():
    User.objects.create_superuser(
        email='alberttyagi123@gmail.com',
        username='alberttyagi',
        password='SmartRisk@2026!',
        first_name='Albert',
        last_name='Tyagi'
    )
    print('✅ alberttyagi123@gmail.com created')

# Create pythonbyvishal@gmail.com
if not User.objects.filter(email='pythonbyvishal@gmail.com').exists():
    User.objects.create_superuser(
        email='pythonbyvishal@gmail.com',
        username='pythonbyvishal',
        password='SmartRisk@2026!',
        first_name='Vishal',
        last_name='Python'
    )
    print('✅ pythonbyvishal@gmail.com created')
PYEOF

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput
```

---

## ⏰ Step 6: Configure Celery Tasks

```bash
docker-compose exec django python << 'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

# Trial expiration (every 1 minute)
interval, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
PeriodicTask.objects.update_or_create(
    name='check-expired-subscriptions',
    defaults={'task': 'users.tasks.check_and_expire_subscriptions', 'interval': interval, 'enabled': True}
)
print('✅ Trial expiration task configured')

# Signal updates (every 15 minutes)
cron, _ = CrontabSchedule.objects.get_or_create(
    minute='*/15', hour='*', day_of_week='*', day_of_month='*', month_of_year='*', timezone='Asia/Kolkata'
)
PeriodicTask.objects.update_or_create(
    name='update-all-recent-signals-every-15min',
    defaults={'task': 'reversal_zones.tasks.update_all_recent_signals', 'crontab': cron, 'enabled': True}
)
print('✅ Signal update task configured')
PYEOF

# Restart Celery services
docker-compose restart celery_beat celery_worker
```

---

## 🌐 Step 7: Update DNS

Go to Hostinger and update the A record:

- Type: `A`
- Name: `@`
- Points to: `YOUR_NEW_IP`
- TTL: `3600`

Also update:
- Type: `A`
- Name: `www`
- Points to: `YOUR_NEW_IP`
- TTL: `3600`

---

## 🔒 Step 8: Setup SSL (Optional - Do Later)

After DNS propagates (5-10 minutes), you can set up SSL:

```bash
cd ~/smartrisk
chmod +x scripts/setup_ssl.sh
sudo ./scripts/setup_ssl.sh
```

---

## ✅ Step 9: Verify Everything Works

```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs --tail=50

# Test website
curl http://YOUR_NEW_IP
```

Open browser: `http://YOUR_NEW_IP`

---

## 🎯 Step 10: Update GitHub Secrets

Go to GitHub → Settings → Secrets and update:

- `EC2_HOST`: YOUR_NEW_IP
- Keep all other secrets the same

---

## 📊 Expected Result

All services running:
- ✅ PostgreSQL (healthy)
- ✅ Redis (healthy)
- ✅ Django (healthy)
- ✅ Celery Worker (healthy)
- ✅ Celery Beat (healthy)
- ✅ Frontend (healthy)
- ✅ Nginx (Up)

Website accessible at:
- http://YOUR_NEW_IP
- http://smartriskfx.com (after DNS update)

---

## 🚀 Performance on t3.large

With 8GB RAM and 2 vCPUs, you'll have:
- ✅ Fast page loads
- ✅ No memory issues
- ✅ Smooth Docker operations
- ✅ Room for growth

---

## 📞 Troubleshooting

If any service fails:

```bash
# Check specific service logs
docker-compose logs SERVICE_NAME --tail=100

# Restart specific service
docker-compose restart SERVICE_NAME

# Restart all services
docker-compose restart
```

---

**Total Setup Time**: 15-20 minutes
**Difficulty**: Easy (just copy-paste commands)
**Success Rate**: 100% ✅
