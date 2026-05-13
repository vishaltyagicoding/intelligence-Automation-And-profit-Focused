# Deployment Guide

## Production Environment

### Server Details
- **Provider**: AWS EC2
- **Instance Type**: t3.large
- **Region**: us-west-1 (California)
- **IP Address**: 54.183.178.141
- **OS**: Ubuntu 26.04 LTS
- **Domain**: smartriskfx.com
- **SSL**: Let's Encrypt (auto-renewal enabled)

### Access
```bash
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
```

## Docker Configuration

### Services
```yaml
services:
  db:          # PostgreSQL 16
  redis:       # Redis 7
  django:      # Django backend + Celery
  nginx:       # Reverse proxy + SSL
  frontend:    # Next.js frontend
```

### Container Names
- Database: `db`
- Redis: `redis`
- Backend: `django` (NOT "backend")
- Nginx: `nginx`
- Frontend: `frontend`

### Important Files
- **Environment**: `.env` (NOT .env.production)
- **Docker Compose**: `docker-compose.yml` (NOT docker-compose.prod.yml)
- **Nginx Config**: `nginx/nginx.conf`

## Environment Variables (.env)

### Backend
```bash
# Django
SECRET_KEY=<secret>
DEBUG=False
ALLOWED_HOSTS=smartriskfx.com,54.183.178.141

# Database
DB_NAME=neuraltrade
DB_USER=smartrisk_user
DB_PASSWORD=<password>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=smarttriskfx@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=smarttriskfx@gmail.com

# Binance
BINANCE_API_KEY=<key>
BINANCE_API_SECRET=<secret>
```

### Frontend
```bash
NEXT_PUBLIC_API_URL=http://django:8000
NEXT_PUBLIC_WS_URL=ws://django:8000
```

## Deployment Process

### Automated (GitHub Actions)
1. Push to `main` branch
2. GitHub Actions workflow triggers
3. SSH into server
4. Pull latest code
5. Rebuild and restart containers
6. Health check verification

### Manual Deployment
```bash
# SSH into server
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk

# Pull latest code
git pull origin main

# Rebuild and restart
sudo docker-compose down
sudo docker-compose up -d --build

# Check logs
sudo docker-compose logs -f django
```

## Common Commands

### Docker Operations
```bash
# View running containers
sudo docker-compose ps

# View logs
sudo docker-compose logs -f django
sudo docker-compose logs -f frontend
sudo docker-compose logs -f nginx

# Restart specific service
sudo docker-compose restart django

# Execute command in container
sudo docker-compose exec django python manage.py <command>

# Database backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup.sql
```

### Django Management
```bash
# Run migrations
sudo docker-compose exec django python manage.py migrate

# Create superuser
sudo docker-compose exec django python manage.py createsuperuser

# Collect static files
sudo docker-compose exec django python manage.py collectstatic --noinput

# Django shell
sudo docker-compose exec django python manage.py shell
```

### Celery Operations
```bash
# Check Celery workers
sudo docker-compose exec django celery -A neuraltrade inspect active

# Restart Celery
sudo docker-compose restart django
```

## SSL Certificate Management

### Let's Encrypt Setup
```bash
# Initial setup (already done)
sudo certbot certonly --standalone -d smartriskfx.com

# Certificate location
/etc/letsencrypt/live/smartriskfx.com/fullchain.pem
/etc/letsencrypt/live/smartriskfx.com/privkey.pem
```

### Auto-Renewal
- Certbot auto-renewal is enabled
- Runs twice daily via systemd timer
- Manual renewal: `sudo certbot renew`

## Nginx Configuration

### HTTP → HTTPS Redirect
```nginx
server {
    listen 80;
    server_name smartriskfx.com;
    return 301 https://$server_name$request_uri;
}
```

### HTTPS Server Block
```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name smartriskfx.com;

    ssl_certificate /etc/letsencrypt/live/smartriskfx.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/smartriskfx.com/privkey.pem;

    # Proxy to frontend
    location / {
        proxy_pass http://frontend:3000;
    }

    # Proxy to backend API
    location /api/ {
        proxy_pass http://django:8000;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://django:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring and Health Checks

### Health Check Endpoints
- Frontend: `https://smartriskfx.com/api/health`
- Backend: `https://smartriskfx.com/api/trading/system-status/`

### Log Monitoring
```bash
# Real-time logs
sudo docker-compose logs -f

# Last 100 lines
sudo docker-compose logs --tail=100 django

# Filter by service
sudo docker-compose logs django | grep ERROR
```

### Database Health
```bash
# Check PostgreSQL
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade

# View active connections
sudo docker-compose exec db psql -U smartrisk_user -d neuraltrade -c "SELECT count(*) FROM pg_stat_activity;"
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
sudo docker-compose logs <service>

# Rebuild from scratch
sudo docker-compose down -v
sudo docker-compose up -d --build
```

### Database Connection Issues
```bash
# Check database is running
sudo docker-compose ps db

# Test connection
sudo docker-compose exec django python manage.py dbshell
```

### WebSocket Not Connecting
```bash
# Check nginx WebSocket config
sudo docker-compose exec nginx nginx -t

# Restart nginx
sudo docker-compose restart nginx
```

### SSL Certificate Issues
```bash
# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

## Rollback Procedure
```bash
# View git history
git log --oneline

# Rollback to previous commit
git reset --hard <commit-hash>

# Rebuild containers
sudo docker-compose down
sudo docker-compose up -d --build
```

## Security Checklist
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] SSH key-based authentication only
- [ ] SSL certificates valid and auto-renewing
- [ ] Environment variables not committed
- [ ] Database backups automated
- [ ] Django DEBUG=False in production
- [ ] CORS properly configured
- [ ] Rate limiting enabled (future)

## Performance Optimization
- Enable Nginx gzip compression
- Use Redis for caching
- Optimize database queries
- Enable CDN for static assets (future)
- Monitor resource usage with htop/docker stats
