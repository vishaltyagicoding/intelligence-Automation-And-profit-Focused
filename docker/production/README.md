# Production Deployment Configuration

## Overview
Production deployment on AWS EC2 with Docker Compose, Nginx reverse proxy, SSL certificates, and automated CI/CD.

## Server Specifications

### AWS EC2 Instance
- **Instance Type**: t3.medium
- **vCPUs**: 2
- **Memory**: 4 GB
- **Storage**: 120 GB SSD
- **Region**: us-west-1 (California)
- **IP Address**: 54.183.178.141
- **OS**: Ubuntu 26.04 LTS

### Network Configuration
- **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
- **Elastic IP**: 54.183.178.141
- **Domain**: smartriskfx.com (A record pointing to Elastic IP)

## Production Environment

### Environment Variables (.env)
```bash
# Django
SECRET_KEY=<production-secret-key>
DEBUG=False
ALLOWED_HOSTS=smartriskfx.com,54.183.178.141
CSRF_TRUSTED_ORIGINS=https://smartriskfx.com

# Database
DB_NAME=neuraltrade
DB_USER=smartrisk_user
DB_PASSWORD=<secure-password>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Email (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=smarttriskfx@gmail.com
EMAIL_HOST_PASSWORD=<gmail-app-password>
DEFAULT_FROM_EMAIL=smarttriskfx@gmail.com

# Binance API
BINANCE_API_KEY=<api-key>
BINANCE_API_SECRET=<api-secret>

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Frontend Environment (.env)
```bash
NEXT_PUBLIC_API_URL=http://django:8000
NEXT_PUBLIC_WS_URL=ws://django:8000
NODE_ENV=production
```

## Docker Compose Production Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    container_name: db
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  django:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: django
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn neuraltrade.asgi:application 
             -k uvicorn.workers.UvicornWorker 
             -b 0.0.0.0:8000 
             --workers 4 
             --timeout 120"
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    environment:
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    env_file:
      - .env

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: frontend
    restart: unless-stopped
    command: npm start
    depends_on:
      - django
    env_file:
      - .env

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - static_volume:/app/staticfiles:ro
    depends_on:
      - django
      - frontend

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

## SSL Certificate Setup

### Initial Certificate Generation
```bash
# Stop nginx if running
sudo docker-compose stop nginx

# Generate certificate
sudo certbot certonly --standalone -d smartriskfx.com

# Certificate files created at:
# /etc/letsencrypt/live/smartriskfx.com/fullchain.pem
# /etc/letsencrypt/live/smartriskfx.com/privkey.pem

# Start nginx
sudo docker-compose up -d nginx
```

### Auto-Renewal
Certbot automatically renews certificates via systemd timer.

**Check renewal status:**
```bash
sudo certbot certificates
```

**Test renewal:**
```bash
sudo certbot renew --dry-run
```

**Force renewal:**
```bash
sudo certbot renew --force-renewal
sudo docker-compose restart nginx
```

## Deployment Process

### Automated Deployment (GitHub Actions)
1. Push code to `main` branch
2. GitHub Actions workflow triggers
3. SSH into EC2 server
4. Pull latest code
5. Rebuild Docker containers
6. Run migrations
7. Collect static files
8. Health check verification

### Manual Deployment
```bash
# SSH into server
ssh -i smartriskfx1.pem ubuntu@54.183.178.141

# Navigate to project
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

# View logs
sudo docker-compose logs -f
```

## Monitoring and Health Checks

### Service Health
```bash
# Check all containers
sudo docker-compose ps

# Check specific service
sudo docker-compose ps django

# View resource usage
sudo docker stats
```

### Application Health
```bash
# Frontend
curl -I https://smartriskfx.com

# Backend API
curl https://smartriskfx.com/api/health/

# System status
curl https://smartriskfx.com/api/trading/system-status/
```

### Database Health
```bash
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade
```

### Redis Health
```bash
sudo docker-compose exec redis redis-cli ping
```

### Celery Health
```bash
sudo docker-compose exec django celery -A neuraltrade inspect active
```

## Log Management

### View Logs
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

### Log Rotation
Docker automatically rotates logs. Configure in docker-compose.yml:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Backup Strategy

### Database Backup
```bash
# Create backup directory
mkdir -p /home/ubuntu/backups

# Manual backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade | gzip > /home/ubuntu/backups/neuraltrade_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated daily backup (cron)
# Add to crontab: crontab -e
0 2 * * * cd /home/ubuntu/smartrisk && sudo docker-compose exec -T db pg_dump -U smartrisk_user neuraltrade | gzip > /home/ubuntu/backups/neuraltrade_$(date +\%Y\%m\%d).sql.gz
```

### Code Backup
```bash
# Backup entire project
tar -czf /home/ubuntu/backups/smartrisk_$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  /home/ubuntu/smartrisk
```

### Volume Backup
```bash
# Backup PostgreSQL volume
sudo docker run --rm \
  -v smartrisk_postgres_data:/data \
  -v /home/ubuntu/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz /data
```

## Security Hardening

### Firewall (UFW)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### SSH Security
```bash
# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### Docker Security
- Run containers as non-root user
- Use read-only volumes where possible
- Limit container resources
- Scan images for vulnerabilities

## Performance Optimization

### Database
- Connection pooling enabled
- Indexes on frequently queried fields
- Regular VACUUM and ANALYZE

### Redis
- Persistent storage enabled
- Memory limit configured
- Eviction policy set

### Nginx
- Gzip compression enabled
- Static file caching
- HTTP/2 enabled
- SSL session caching

### Django
- DEBUG=False in production
- Static files served by Nginx
- Database query optimization
- Celery for async tasks

## Troubleshooting

### Container Won't Start
```bash
# Check logs
sudo docker-compose logs <service>

# Rebuild from scratch
sudo docker-compose down -v
sudo docker-compose up -d --build
```

### High Memory Usage
```bash
# Check usage
sudo docker stats

# Restart containers
sudo docker-compose restart

# Clear cache
sudo docker-compose exec redis redis-cli FLUSHALL
```

### Disk Space Full
```bash
# Check disk usage
df -h

# Clean Docker
sudo docker system prune -a

# Remove old logs
sudo journalctl --vacuum-time=7d

# Clean old backups
find /home/ubuntu/backups -name "*.sql.gz" -mtime +30 -delete
```

### SSL Certificate Issues
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew
sudo docker-compose restart nginx
```

## Rollback Procedure

### Code Rollback
```bash
# View commit history
git log --oneline -10

# Rollback to specific commit
git reset --hard <commit-hash>

# Rebuild containers
sudo docker-compose down
sudo docker-compose up -d --build
```

### Database Rollback
```bash
# Restore from backup
gunzip -c /home/ubuntu/backups/neuraltrade_20260510.sql.gz | \
  sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade
```

## Maintenance Schedule

### Daily
- Automated database backup (2 AM)
- Log monitoring
- Health check verification

### Weekly
- Security updates
- Log rotation
- Backup verification

### Monthly
- Dependency updates
- Performance review
- Capacity planning
- Backup cleanup (keep 30 days)

## Emergency Contacts
- **Admin**: alberttyagi123@gmail.com
- **Support**: smarttriskfx@gmail.com
- **AWS Support**: Via AWS Console
