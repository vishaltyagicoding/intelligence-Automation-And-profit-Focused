# Deployment Commands

## Quick Deploy (Automated)

### Push to GitHub
```bash
# Commit changes
git add .
git commit -m "Your commit message"

# Push to main branch (triggers GitHub Actions)
git push origin main
```

### Monitor Deployment
```bash
# Watch GitHub Actions
# Go to: https://github.com/vishaltyagicoding/intelligence-Automation-And-profit-Focused/actions

# SSH and watch logs
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
sudo docker-compose logs -f
```

## Manual Deploy

### Full Deployment
```bash
# SSH into server
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk

# Pull latest code
git pull origin main

# Stop containers
sudo docker-compose down

# Rebuild and start
sudo docker-compose up -d --build

# Run migrations
sudo docker-compose exec django python manage.py migrate

# Collect static files
sudo docker-compose exec django python manage.py collectstatic --noinput

# Check status
sudo docker-compose ps
sudo docker-compose logs -f
```

### Quick Restart (No Rebuild)
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
sudo docker-compose restart django
sudo docker-compose restart frontend
```

### Backend Only
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
git pull origin main
sudo docker-compose up -d --build django
sudo docker-compose exec django python manage.py migrate
```

### Frontend Only
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
git pull origin main
sudo docker-compose up -d --build frontend
```

## Database Migrations

### Apply Migrations
```bash
sudo docker-compose exec django python manage.py migrate
```

### Create Migration
```bash
sudo docker-compose exec django python manage.py makemigrations
```

### View Migration Status
```bash
sudo docker-compose exec django python manage.py showmigrations
```

## SSL Certificate Management

### Check Certificate Status
```bash
sudo certbot certificates
```

### Renew Certificate
```bash
sudo certbot renew
sudo docker-compose restart nginx
```

### Force Renewal
```bash
sudo certbot renew --force-renewal
sudo docker-compose restart nginx
```

## Rollback Procedures

### Rollback to Previous Commit
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk

# View commit history
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-hash>

# Rebuild containers
sudo docker-compose down
sudo docker-compose up -d --build
```

### Rollback Database Migration
```bash
# Rollback to specific migration
sudo docker-compose exec django python manage.py migrate app_name 0001_initial

# Rollback all migrations for an app
sudo docker-compose exec django python manage.py migrate app_name zero
```

## Health Checks

### Verify Deployment
```bash
# Check all containers running
sudo docker-compose ps

# Test frontend
curl -I https://smartriskfx.com

# Test backend API
curl https://smartriskfx.com/api/health/

# Test WebSocket
wscat -c wss://smartriskfx.com/ws/market/BTCUSD/15m/
```

### Check Logs
```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f django
sudo docker-compose logs -f frontend
sudo docker-compose logs -f nginx

# Last 100 lines
sudo docker-compose logs --tail=100 django

# Filter errors
sudo docker-compose logs django | grep ERROR
```

## Monitoring

### Resource Usage
```bash
# Docker stats
sudo docker stats

# System resources
htop

# Disk usage
df -h

# Memory usage
free -h
```

### Database Status
```bash
# Check PostgreSQL
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade

# Active connections
sudo docker-compose exec db psql -U smartrisk_user -d neuraltrade -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
sudo docker-compose exec db psql -U smartrisk_user -d neuraltrade -c "SELECT pg_size_pretty(pg_database_size('neuraltrade'));"
```

### Celery Status
```bash
# Check active tasks
sudo docker-compose exec django celery -A neuraltrade inspect active

# Check registered tasks
sudo docker-compose exec django celery -A neuraltrade inspect registered

# Purge all tasks
sudo docker-compose exec django celery -A neuraltrade purge
```

## Backup and Restore

### Database Backup
```bash
# Create backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

### Database Restore
```bash
# Restore from backup
sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade < backup.sql
```

### Code Backup
```bash
# Create tarball
tar -czf smartrisk_backup_$(date +%Y%m%d).tar.gz ~/smartrisk

# Exclude unnecessary files
tar -czf smartrisk_backup.tar.gz \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  ~/smartrisk
```

## Emergency Procedures

### Complete System Restart
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose up -d
```

### Clear All Data and Rebuild
```bash
# WARNING: This deletes all data!
sudo docker-compose down -v
sudo docker-compose up -d --build
sudo docker-compose exec django python manage.py migrate
sudo docker-compose exec django python manage.py createsuperuser
```

### Fix Disk Space Issues
```bash
# Remove unused Docker resources
sudo docker system prune -a

# Remove old logs
sudo journalctl --vacuum-time=7d

# Check disk usage
df -h
du -sh ~/smartrisk/*
```

## Post-Deployment Verification

### Checklist
- [ ] All containers running: `sudo docker-compose ps`
- [ ] No errors in logs: `sudo docker-compose logs --tail=50`
- [ ] Frontend accessible: `curl -I https://smartriskfx.com`
- [ ] Backend API working: `curl https://smartriskfx.com/api/health/`
- [ ] WebSocket connecting: Test in browser console
- [ ] Database migrations applied: `sudo docker-compose exec django python manage.py showmigrations`
- [ ] SSL certificate valid: `sudo certbot certificates`
- [ ] Email sending working: Test signal alert
- [ ] Celery tasks running: `sudo docker-compose exec django celery -A neuraltrade inspect active`

## Deployment Schedule
- **Regular Updates**: As needed (via GitHub Actions)
- **Security Updates**: Weekly
- **Database Backups**: Daily (automated)
- **SSL Renewal**: Automatic (Let's Encrypt)
- **Dependency Updates**: Monthly
