# Deployment Skill

## Overview
Docker-based deployment on AWS EC2 with nginx reverse proxy, SSL certificates, and automated CI/CD via GitHub Actions.

## Infrastructure

### Server
- **Provider**: AWS EC2
- **Instance**: t3.medium
- **Region**: us-west-1 (California)
- **IP**: 54.183.178.141
- **OS**: Ubuntu 26.04 LTS
- **Domain**: smartriskfx.com

### Services
- **Web Server**: Nginx (reverse proxy + SSL termination)
- **Backend**: Django + Gunicorn
- **Frontend**: Next.js
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery

## Docker Architecture

### docker-compose.yml
```yaml
services:
  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine

  django:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn neuraltrade.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    command: npm start
    depends_on:
      - django

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - django
      - frontend
```

## SSL Configuration

### Let's Encrypt Setup
```bash
# Install certbot
sudo apt install certbot

# Obtain certificate
sudo certbot certonly --standalone -d smartriskfx.com

# Certificate location
/etc/letsencrypt/live/smartriskfx.com/fullchain.pem
/etc/letsencrypt/live/smartriskfx.com/privkey.pem
```

### Auto-Renewal
- Certbot systemd timer runs twice daily
- Automatically renews certificates within 30 days of expiry
- Manual renewal: `sudo certbot renew`

## Nginx Configuration

### Main Config
```nginx
http {
    upstream django_backend {
        server django:8000;
    }

    upstream frontend_server {
        server frontend:3000;
    }

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name smartriskfx.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl;
        http2 on;
        server_name smartriskfx.com;

        ssl_certificate /etc/letsencrypt/live/smartriskfx.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/smartriskfx.com/privkey.pem;

        # Frontend
        location / {
            proxy_pass http://frontend_server;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api/ {
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://django_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # Static files
        location /static/ {
            alias /app/staticfiles/;
        }
    }
}
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/smartrisk
            git pull origin main
            sudo docker-compose down
            sudo docker-compose up -d --build
            sudo docker-compose exec -T django python manage.py migrate
            sudo docker-compose exec -T django python manage.py collectstatic --noinput
```

### Secrets Configuration
- `EC2_HOST`: 54.183.178.141
- `EC2_SSH_KEY`: Contents of smartriskfx1.pem

## Deployment Process

### Automated Deployment
1. Push code to `main` branch
2. GitHub Actions triggers
3. SSH into EC2 server
4. Pull latest code
5. Rebuild Docker containers
6. Run migrations
7. Collect static files
8. Health check

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

# Run migrations
sudo docker-compose exec django python manage.py migrate

# Collect static files
sudo docker-compose exec django python manage.py collectstatic --noinput

# Check status
sudo docker-compose ps
sudo docker-compose logs -f
```

## Environment Configuration

### Production .env
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

# Binance
BINANCE_API_KEY=<key>
BINANCE_API_SECRET=<secret>
```

### Frontend .env
```bash
NEXT_PUBLIC_API_URL=http://django:8000
NEXT_PUBLIC_WS_URL=ws://django:8000
```

## Monitoring

### Health Checks
```bash
# Frontend
curl -I https://smartriskfx.com

# Backend API
curl https://smartriskfx.com/api/health/

# System status
curl https://smartriskfx.com/api/trading/system-status/
```

### Log Monitoring
```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f django
sudo docker-compose logs -f frontend
sudo docker-compose logs -f nginx

# Filter errors
sudo docker-compose logs django | grep ERROR
```

### Resource Monitoring
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

## Backup Strategy

### Database Backup
```bash
# Create backup
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup_$(date +%Y%m%d).sql

# Compress
gzip backup_*.sql

# Restore
sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade < backup.sql
```

### Code Backup
```bash
# Create tarball
tar -czf smartrisk_backup_$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='__pycache__' \
  ~/smartrisk
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
# Rollback migration
sudo docker-compose exec django python manage.py migrate app_name 0001_initial
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

### SSL Issues
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew
sudo docker-compose restart nginx
```

### Database Connection Issues
```bash
# Check database
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade

# Restart database
sudo docker-compose restart db
```

## Security Checklist
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] SSH key-based authentication
- [ ] SSL certificates valid
- [ ] Environment variables not committed
- [ ] Database backups automated
- [ ] Django DEBUG=False
- [ ] CORS properly configured

## Performance Optimization
- Enable nginx gzip compression
- Use Redis for caching
- Optimize database queries
- Enable CDN for static assets
- Monitor resource usage
