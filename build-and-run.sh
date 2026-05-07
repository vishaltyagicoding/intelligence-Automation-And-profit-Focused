#!/bin/bash

echo "🚀 NeuralTrade - Building and Running Production Environment"
echo "============================================================"

# Stop and remove old containers
echo "📦 Stopping old containers..."
docker-compose -f docker-compose.prod.yml down

# Remove old images
echo "🗑️  Removing old images..."
docker rmi neuraltrade-backend:latest 2>/dev/null || true
docker rmi neuraltrade-frontend:latest 2>/dev/null || true

# Prune unused images
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

# Build new images
echo "🔨 Building backend image..."
docker build -f Dockerfile.backend -t neuraltrade-backend:latest .

echo "🔨 Building frontend image..."
docker build -f Dockerfile.frontend -t neuraltrade-frontend:latest .

# Start services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Show status
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost"
echo "   Backend API: http://localhost/api/"
echo "   Django Admin: http://localhost/admin/"
echo "   WebSocket: ws://localhost/ws/live/"
echo ""
echo "📝 View logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
