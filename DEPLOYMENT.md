# NeuralTrade Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+ with TimescaleDB
- Redis 7+

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Docker Deployment

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run setup script
./scripts/setup.sh

# Or manually:
docker-compose up --build -d
```

### 3. Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f django

# Check system status
curl http://localhost/api/trading/status/
```

## Manual Setup (Without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb neuraltrade

# Enable TimescaleDB extension
psql neuraltrade -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Run migrations
python manage.py migrate
```

### 3. Redis Setup

```bash
# Start Redis
redis-server
```

### 4. Start Services

```bash
# Terminal 1: Django/Daphne
python manage.py runserver

# Terminal 2: Celery Worker
celery -A neuraltrade worker -l info

# Terminal 3: Celery Beat
celery -A neuraltrade beat -l info
```

## Production Deployment

### Gunicorn with Uvicorn Workers

```bash
gunicorn neuraltrade.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

### Nginx Configuration

Copy `nginx/nginx.conf` to `/etc/nginx/nginx.conf` and restart:

```bash
sudo systemctl restart nginx
```

### SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## Monitoring

### Health Check

```bash
curl http://localhost/api/trading/status/
```

### Logs

```bash
# Django logs
tail -f logs/neuraltrade.log

# Docker logs
docker-compose logs -f
```

### Redis Monitoring

```bash
redis-cli INFO
redis-cli MONITOR
```

## Scaling

### Horizontal Scaling

```bash
# Scale Django workers
docker-compose up -d --scale django=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=5
```

### Performance Tuning

- Increase Gunicorn workers: `--workers 8`
- Tune Redis maxmemory: `maxmemory 4gb`
- Optimize PostgreSQL: `shared_buffers`, `work_mem`
- Enable connection pooling: PgBouncer

## Troubleshooting

### WebSocket Connection Issues

Check Nginx WebSocket configuration:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### Celery Tasks Not Running

```bash
# Check Celery worker status
celery -A neuraltrade inspect active

# Restart workers
docker-compose restart celery_worker celery_beat
```

### Database Connection Errors

```bash
# Check PostgreSQL status
docker-compose logs db

# Test connection
psql -h localhost -U postgres -d neuraltrade
```

## Backup & Recovery

### Database Backup

```bash
docker-compose exec db pg_dump -U postgres neuraltrade > backup.sql
```

### Redis Backup

```bash
docker-compose exec redis redis-cli SAVE
docker cp neuraltrade_redis:/data/dump.rdb ./redis_backup.rdb
```

## Security Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable Redis authentication
- [ ] Use environment variables for secrets
- [ ] Regular security updates
