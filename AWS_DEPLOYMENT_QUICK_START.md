# 🚀 SmartRisk AWS EC2 Deployment - Quick Start

## One-Command Deployment

### Prerequisites
- AWS EC2 instance (Ubuntu 20.04 or 22.04)
- SSH access to the instance
- Security group configured (ports: 22, 80, 443, 8000, 8001)

---

## Step 1: SSH into EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

---

## Step 2: Clone Repository

```bash
git clone https://github.com/your-username/smartrisk.git
cd smartrisk
```

---

## Step 3: Configure Environment

```bash
# Copy template
cp .env.aws.template .env

# Edit with your settings
nano .env
```

**Required Environment Variables:**
```env
# Database
POSTGRES_DB=neuraltrade
POSTGRES_USER=neuraltrade
POSTGRES_PASSWORD=your_secure_password_here

# Django
SECRET_KEY=your_django_secret_key_here
DEBUG=False
ALLOWED_HOSTS=your-ec2-ip,your-domain.com

# Email (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis
REDIS_URL=redis://redis:6379/1

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

---

## Step 4: Run Deployment Script

```bash
sudo bash deploy_aws.sh
```

**This script will:**
1. ✅ Install Docker & Docker Compose
2. ✅ Configure firewall
3. ✅ Build Docker images
4. ✅ Start all services
5. ✅ Run database migrations
6. ✅ Create superuser
7. ✅ Configure Celery Beat tasks
8. ✅ Show service status

**Deployment time**: ~10-15 minutes

---

## Step 5: Verify Deployment

### Check Services
```bash
docker-compose ps
```

**Expected output:**
```
NAME                      STATUS
neuraltrade_db            Up (healthy)
neuraltrade_redis         Up (healthy)
neuraltrade_django        Up (healthy)
neuraltrade_celery_worker Up (healthy)
neuraltrade_celery_beat   Up (healthy)
neuraltrade_frontend      Up
neuraltrade_nginx         Up
```

### Check Logs
```bash
# Django logs
docker-compose logs -f django

# Celery Beat logs
docker-compose logs -f celery_beat

# Celery Worker logs
docker-compose logs -f celery_worker
```

### Test API
```bash
curl http://localhost:8000/health/
# Expected: {"status": "healthy"}
```

---

## Step 6: Access Application

### Frontend
```
http://your-ec2-public-ip
```

### Admin Panel
```
http://your-ec2-public-ip:8000/admin/
```

**Credentials:**
- Email: `alberttyagi123@gmail.com`
- Password: `SmartRisk@2026!`

---

## 🔧 Useful Commands

### View Logs
```bash
docker-compose logs -f [service-name]
```

### Restart Service
```bash
docker-compose restart [service-name]
```

### Stop All Services
```bash
docker-compose down
```

### Start All Services
```bash
docker-compose up -d
```

### Rebuild Service
```bash
docker-compose up -d --build [service-name]
```

### Execute Command in Container
```bash
docker-compose exec django python manage.py [command]
```

### Database Shell
```bash
docker-compose exec db psql -U neuraltrade -d neuraltrade
```

### Django Shell
```bash
docker-compose exec django python manage.py shell
```

---

## 🔐 Security Checklist

### AWS Security Group Rules
- [x] Port 22 (SSH) - Your IP only
- [x] Port 80 (HTTP) - 0.0.0.0/0
- [x] Port 443 (HTTPS) - 0.0.0.0/0
- [x] Port 8000 (API) - 0.0.0.0/0
- [x] Port 8001 (WebSocket) - 0.0.0.0/0

### Environment Security
- [x] Change default passwords
- [x] Use strong SECRET_KEY
- [x] Set DEBUG=False
- [x] Configure ALLOWED_HOSTS
- [x] Use HTTPS in production

---

## 📊 Monitoring

### Check Celery Tasks
```bash
docker-compose exec django python manage.py shell
```

```python
from django_celery_beat.models import PeriodicTask
PeriodicTask.objects.all()
```

### Check Database
```bash
docker-compose exec db psql -U neuraltrade -d neuraltrade -c "SELECT COUNT(*) FROM users_user;"
```

### Check Redis
```bash
docker-compose exec redis redis-cli PING
```

---

## 🐛 Troubleshooting

### Service Not Starting
```bash
# Check logs
docker-compose logs [service-name]

# Restart service
docker-compose restart [service-name]
```

### Database Connection Error
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db
```

### Celery Not Processing Tasks
```bash
# Check Celery worker logs
docker-compose logs celery_worker

# Check Celery beat logs
docker-compose logs celery_beat

# Restart Celery services
docker-compose restart celery_worker celery_beat
```

### Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

---

## 🔄 Updates & Maintenance

### Pull Latest Code
```bash
git pull origin main
```

### Rebuild & Restart
```bash
docker-compose down
docker-compose up -d --build
```

### Run Migrations
```bash
docker-compose exec django python manage.py migrate
```

### Collect Static Files
```bash
docker-compose exec django python manage.py collectstatic --noinput
```

---

## 📞 Support

**Email**: alberttyagi123@gmail.com  
**Email**: smarttriskfx@gmail.com

---

## ✅ Production Ready

Your SmartRisk application is now live on AWS EC2!

**Services Running:**
- ✅ PostgreSQL (TimescaleDB)
- ✅ Redis
- ✅ Django (Daphne ASGI)
- ✅ Celery Worker
- ✅ Celery Beat
- ✅ Next.js Frontend
- ✅ Nginx

**Features Working:**
- ✅ User registration with email verification
- ✅ 3-day free trial with countdown timer
- ✅ Automatic trial expiration
- ✅ Subscription management
- ✅ Real-time trading signals
- ✅ Live charts with WebSocket
- ✅ Email notifications
- ✅ Admin panel

---

**🎉 Congratulations! Your production application is live!**
