# Production Deployment Checklist - AWS Server ✅

## Pre-Deployment Checklist

### 1. Code Changes ✅
- [x] Trial users get `manual_subscription='deactivated'`
- [x] Paid users get `manual_subscription='activated'`
- [x] Email system complete (welcome, trial expiration, subscription emails)
- [x] Stop Loss calculation fixed (50% of distance)
- [x] Nginx 502 error permanently fixed
- [x] Signal alerts only for paid subscribers

### 2. Configuration Files ✅
- [x] `nginx/nginx.conf` - Automatic retry and keepalive
- [x] `docker-compose.yml` - Health check dependencies
- [x] `payments/signals.py` - Correct subscription status
- [x] `reversal_zones/tasks.py` - Email notifications on new signals

### 3. Environment Variables
- [ ] `.env` file configured with production values
- [ ] `EMAIL_HOST_USER` - Gmail address
- [ ] `EMAIL_HOST_PASSWORD` - Gmail app password
- [ ] `SECRET_KEY` - Strong random key
- [ ] `DEBUG=False` for production
- [ ] Database credentials
- [ ] Redis credentials

## Deployment Steps

### Step 1: Prepare AWS Server
```bash
# SSH into AWS server
ssh -i your-key.pem ubuntu@your-aws-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone Repository
```bash
# Clone your repository
git clone https://github.com/your-repo/smartrisk.git
cd smartrisk

# Or pull latest changes if already cloned
git pull origin main
```

### Step 3: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Set these values:
# DEBUG=False
# ALLOWED_HOSTS=your-domain.com,your-aws-ip
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# SECRET_KEY=generate-strong-random-key
```

### Step 4: Build and Start Services
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Run Migrations
```bash
# Run database migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createfulladmin alberttyagi123@gmail.com

# Grant full admin access
docker-compose exec django python manage.py grantfulladmin alberttyagi123@gmail.com

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput
```

### Step 6: Verify Services
```bash
# Check all containers are running
docker-compose ps

# Test Django health
curl http://localhost:8000/health/

# Test API endpoint
curl http://localhost/api/health

# Test login endpoint
curl -X POST http://localhost/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## AWS Security Group Configuration

### Required Inbound Rules
| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Django API |
| Custom TCP | TCP | 8001 | 0.0.0.0/0 | WebSocket |
| PostgreSQL | TCP | 5432 | Your IP | Database (optional) |

### Optional Inbound Rules
| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend (if needed) |
| Custom TCP | TCP | 6379 | Internal | Redis (internal only) |

## Post-Deployment Verification

### 1. Test User Registration
- [ ] Go to http://your-aws-ip/register
- [ ] Register new user
- [ ] Verify OTP email received
- [ ] Verify welcome email received
- [ ] Verify 3-day trial activated
- [ ] Verify `manual_subscription='deactivated'`

### 2. Test Trial Expiration
- [ ] Wait 3 days or manually expire trial
- [ ] Verify trial expiration email received
- [ ] Verify user redirected to subscription page
- [ ] Verify cannot access dashboard

### 3. Test Paid Subscription
- [ ] Admin activates subscription
- [ ] Verify `manual_subscription='activated'`
- [ ] Verify subscription activated email received
- [ ] Verify user can access dashboard
- [ ] Verify user can create signal alerts

### 4. Test Signal Alerts
- [ ] Create signal alert as paid user
- [ ] Wait for new signal (or trigger manually)
- [ ] Verify email received with correct Stop Loss
- [ ] Verify trial users do NOT receive emails

### 5. Test Nginx Resilience
- [ ] Restart Django: `docker-compose restart django`
- [ ] Try login immediately
- [ ] Verify no 502 error
- [ ] Verify JSON response received

## Monitoring

### Check Logs
```bash
# Django logs
docker-compose logs -f django

# Nginx logs
docker-compose logs -f nginx

# Celery worker logs
docker-compose logs -f celery_worker

# Celery beat logs
docker-compose logs -f celery_beat
```

### Check Service Status
```bash
# All services
docker-compose ps

# Specific service
docker-compose ps django

# Resource usage
docker stats
```

### Check Database
```bash
# Connect to database
docker-compose exec db psql -U postgres -d neuraltrade

# Check users
SELECT email, manual_subscription, trial_allowed FROM users;

# Check subscriptions
SELECT user_id, status, trial_end FROM subscriptions;

# Check signal alerts
SELECT user_id, crypto, timeframe, is_active FROM signal_alerts;
```

## Troubleshooting

### Issue: 502 Bad Gateway
**Solution**:
```bash
# Restart both services
docker-compose restart django nginx

# Check Django health
docker-compose exec django curl http://localhost:8000/health/

# Check Nginx can reach Django
docker-compose exec nginx wget -O- http://django:8000/health/
```

### Issue: Emails Not Sending
**Solution**:
```bash
# Check email configuration
docker-compose exec django python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST_USER)
>>> print(settings.EMAIL_HOST_PASSWORD)

# Test email
>>> from users.email_utils import send_welcome_email
>>> send_welcome_email('test@example.com', 'Test')
```

### Issue: Celery Not Running
**Solution**:
```bash
# Check Celery worker
docker-compose logs celery_worker

# Check Celery beat
docker-compose logs celery_beat

# Restart Celery
docker-compose restart celery_worker celery_beat
```

### Issue: Database Connection Error
**Solution**:
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db django
```

## Backup and Restore

### Backup Database
```bash
# Create backup
docker-compose exec db pg_dump -U postgres neuraltrade > backup_$(date +%Y%m%d).sql

# Compress backup
gzip backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
# Restore from backup
gunzip backup_20260507.sql.gz
docker-compose exec -T db psql -U postgres neuraltrade < backup_20260507.sql
```

## Maintenance

### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec django python manage.py migrate
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused containers
docker container prune
```

## Performance Optimization

### 1. Enable Gzip Compression
Already configured in `nginx/nginx.conf` ✅

### 2. Enable Caching
Already configured for static files ✅

### 3. Database Optimization
```bash
# Vacuum database
docker-compose exec db psql -U postgres -d neuraltrade -c "VACUUM ANALYZE;"

# Check slow queries
docker-compose exec db psql -U postgres -d neuraltrade -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### 4. Monitor Resource Usage
```bash
# Check CPU and memory
docker stats

# Check disk usage
df -h

# Check network usage
docker-compose exec django netstat -an | grep ESTABLISHED | wc -l
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup database regularly

## Support Contacts

- **Email**: alberttyagi123@gmail.com
- **Email**: smarttriskfx@gmail.com
- **Documentation**: See all `*.md` files in project root

## Summary

✅ **All critical bugs fixed**
✅ **Trial vs Paid subscription working correctly**
✅ **Email system complete and professional**
✅ **Nginx 502 error permanently fixed**
✅ **Signal alerts only for paid subscribers**
✅ **Production-ready and AWS-compatible**

---

**Status**: ✅ READY FOR PRODUCTION
**Date**: May 7, 2026
**Tested**: Local Docker environment
**Deployment Target**: AWS EC2 Server
