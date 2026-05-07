#!/bin/bash

# AWS Deployment Script for NeuralTrade
# This script deploys both frontend and backend in Docker on AWS

set -e  # Exit on error

echo "🚀 Starting NeuralTrade Deployment..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please copy .env.production to .env and update with your values"
    exit 1
fi

# Stop and remove old containers
echo -e "${YELLOW}📦 Stopping old containers...${NC}"
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Remove old images (optional, comment out if you want to keep them)
# docker system prune -af --volumes

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Start all services
echo -e "${YELLOW}🚀 Starting all services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 20

# Run migrations
echo -e "${YELLOW}📊 Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T django python manage.py migrate --noinput

# Collect static files
echo -e "${YELLOW}📁 Collecting static files...${NC}"
docker-compose -f docker-compose.prod.yml exec -T django python manage.py collectstatic --noinput

# Create superuser (optional, comment out if not needed)
# echo -e "${YELLOW}👤 Creating superuser...${NC}"
# docker-compose -f docker-compose.prod.yml exec -T django python manage.py createsuperuser --noinput --email admin@example.com || true

# Check container status
echo -e "${YELLOW}📋 Checking container status...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🌐 Access your application at:"
echo "   Frontend: http://your-server-ip"
echo "   Backend API: http://your-server-ip/api/"
echo "   Admin Panel: http://your-server-ip/admin/"
echo ""
echo "📝 View logs with:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🛑 Stop services with:"
echo "   docker-compose -f docker-compose.prod.yml down"
