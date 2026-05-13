# Build Commands

## Local Development

### Backend (Django)
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver 0.0.0.0:8000

# Run Celery worker
celery -A neuraltrade worker -l info

# Run Celery beat (scheduler)
celery -A neuraltrade beat -l info
```

### Frontend (Next.js)
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Docker Build

### Build All Services
```bash
# Build and start all containers
docker-compose up -d --build

# Build specific service
docker-compose build django
docker-compose build frontend

# Rebuild without cache
docker-compose build --no-cache
```

### Stop and Remove
```bash
# Stop all containers
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop django
```

## Production Build

### On Server
```bash
# SSH into server
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk

# Pull latest code
git pull origin main

# Rebuild containers
sudo docker-compose down
sudo docker-compose up -d --build

# Check status
sudo docker-compose ps
```

### Build Verification
```bash
# Check logs
sudo docker-compose logs -f django
sudo docker-compose logs -f frontend

# Test health endpoints
curl http://localhost:8000/api/health/
curl http://localhost:3000/api/health
```

## Database Setup

### Initial Setup
```bash
# Create database
docker-compose exec db createdb -U smartrisk_user neuraltrade

# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser
```

### Load Initial Data
```bash
# Load fixtures
docker-compose exec django python manage.py loaddata fixtures/initial_data.json
```

## Environment Setup

### Backend .env
```bash
cp .env.example .env
# Edit .env with your values
```

### Frontend .env.local
```bash
cp .env.example .env.local
# Edit .env.local with your values
```

## Dependency Management

### Backend
```bash
# Install new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt
```

### Frontend
```bash
# Install new package
npm install package-name

# Install dev dependency
npm install --save-dev package-name

# Update all packages
npm update

# Check for outdated packages
npm outdated
```

## Build Optimization

### Backend
- Use gunicorn for production
- Enable Redis caching
- Optimize database queries
- Use connection pooling

### Frontend
- Enable Next.js production mode
- Optimize images
- Code splitting
- Tree shaking
- Minification (automatic)

## Troubleshooting Build Issues

### Backend
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check for migration conflicts
python manage.py showmigrations
```

### Frontend
```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

### Docker
```bash
# Remove all containers and images
docker-compose down -v --rmi all

# Prune unused Docker resources
docker system prune -a

# Check disk space
df -h
```

## Pre-deployment Checklist
- [ ] All tests passing
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificates valid
- [ ] Health checks passing
