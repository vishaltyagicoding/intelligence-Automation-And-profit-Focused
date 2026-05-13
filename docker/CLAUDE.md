# Docker Configuration Documentation

## Overview
SmartRisk uses Docker Compose to orchestrate multiple services: PostgreSQL, Redis, Django backend, Next.js frontend, and Nginx reverse proxy.

## Services Architecture

### 1. Database (PostgreSQL 16)
```yaml
db:
  image: postgres:16
  container_name: db
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
```

**Purpose**: Stores all application data (users, signals, trades)
**Port**: 5432 (internal only)
**Volume**: Persistent storage for database files

### 2. Redis (Cache & Message Broker)
```yaml
redis:
  image: redis:7-alpine
  container_name: redis
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

**Purpose**: 
- Celery message broker
- Django Channels layer
- Caching layer
**Port**: 6379 (internal only)
**Volume**: Persistent storage for Redis data

### 3. Django Backend
```yaml
django:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: django
  command: >
    sh -c "python manage.py migrate &&
           python manage.py collectstatic --noinput &&
           gunicorn neuraltrade.asgi:application 
           -k uvicorn.workers.UvicornWorker 
           -b 0.0.0.0:8000 
           --workers 4"
  volumes:
    - .:/app
    - static_volume:/app/staticfiles
  environment:
    - DEBUG=False
    - ALLOWED_HOSTS=${ALLOWED_HOSTS}
  depends_on:
    - db
    - redis
```

**Purpose**: 
- REST API endpoints
- WebSocket connections
- Celery workers
- Admin interface
**Port**: 8000 (internal only)
**Workers**: 4 Gunicorn workers with Uvicorn

### 4. Next.js Frontend
```yaml
frontend:
  build:
    context: .
    dockerfile: Dockerfile.frontend
  container_name: frontend
  command: npm start
  environment:
    - NEXT_PUBLIC_API_URL=http://django:8000
    - NEXT_PUBLIC_WS_URL=ws://django:8000
  depends_on:
    - django
```

**Purpose**: User interface and client-side logic
**Port**: 3000 (internal only)
**Build**: Production optimized build

### 5. Nginx (Reverse Proxy)
```yaml
nginx:
  image: nginx:alpine
  container_name: nginx
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
```

**Purpose**: 
- SSL termination
- Reverse proxy to frontend/backend
- Static file serving
- Load balancing
**Ports**: 80 (HTTP), 443 (HTTPS)

## Dockerfiles

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "neuraltrade.asgi:application", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]
```

## Volumes

### Persistent Volumes
```yaml
volumes:
  postgres_data:      # Database files
  redis_data:         # Redis persistence
  static_volume:      # Django static files
```

**Purpose**: Data persists even when containers are removed
**Location**: `/var/lib/docker/volumes/` on host

## Networks

### Default Bridge Network
All services communicate via Docker's default bridge network.

**Internal DNS**: 
- `db` → PostgreSQL
- `redis` → Redis
- `django` → Backend
- `frontend` → Frontend
- `nginx` → Reverse proxy

## Environment Variables

### Required in .env
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

## Common Docker Commands

### Start Services
```bash
# Start all services
sudo docker-compose up -d

# Start specific service
sudo docker-compose up -d django

# Start with rebuild
sudo docker-compose up -d --build
```

### Stop Services
```bash
# Stop all services
sudo docker-compose down

# Stop and remove volumes
sudo docker-compose down -v

# Stop specific service
sudo docker-compose stop django
```

### View Logs
```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f django

# Last 100 lines
sudo docker-compose logs --tail=100 django
```

### Execute Commands
```bash
# Django shell
sudo docker-compose exec django python manage.py shell

# Database shell
sudo docker-compose exec db psql -U smartrisk_user neuraltrade

# Redis CLI
sudo docker-compose exec redis redis-cli

# Run migrations
sudo docker-compose exec django python manage.py migrate
```

### Container Management
```bash
# List running containers
sudo docker-compose ps

# View container stats
sudo docker stats

# Restart service
sudo docker-compose restart django

# View container logs
sudo docker logs django
```

## Health Checks

### Database Health
```bash
sudo docker-compose exec db pg_isready -U smartrisk_user -d neuraltrade
```

### Redis Health
```bash
sudo docker-compose exec redis redis-cli ping
```

### Django Health
```bash
curl http://localhost:8000/api/health/
```

### Frontend Health
```bash
curl http://localhost:3000/api/health
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

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Database Connection Failed
```bash
# Check database is running
sudo docker-compose ps db

# Check database logs
sudo docker-compose logs db

# Restart database
sudo docker-compose restart db
```

### Out of Disk Space
```bash
# Check disk usage
df -h

# Clean Docker
sudo docker system prune -a

# Remove unused volumes
sudo docker volume prune
```

## Production Considerations

### Resource Limits
Add resource limits to prevent container overconsumption:
```yaml
django:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### Restart Policy
Ensure containers restart on failure:
```yaml
restart: unless-stopped
```

### Logging
Configure log rotation:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Security Best Practices

1. **Never commit .env files**
2. **Use secrets management** for sensitive data
3. **Run containers as non-root** user
4. **Keep images updated** regularly
5. **Scan images** for vulnerabilities
6. **Limit container capabilities**
7. **Use read-only volumes** where possible

## Backup and Restore

### Backup Database
```bash
sudo docker-compose exec db pg_dump -U smartrisk_user neuraltrade > backup.sql
```

### Restore Database
```bash
sudo docker-compose exec -T db psql -U smartrisk_user neuraltrade < backup.sql
```

### Backup Volumes
```bash
sudo docker run --rm -v smartrisk_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```
