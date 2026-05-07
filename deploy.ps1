# AWS Deployment Script for NeuralTrade (PowerShell)
# This script deploys both frontend and backend in Docker on AWS

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting NeuralTrade Deployment..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.production to .env and update with your values"
    exit 1
}

# Stop and remove old containers
Write-Host "📦 Stopping old containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down 2>$null

# Build images
Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml build --no-cache

# Start all services
Write-Host "🚀 Starting all services..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Run migrations
Write-Host "📊 Running database migrations..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml exec -T django python manage.py migrate --noinput

# Collect static files
Write-Host "📁 Collecting static files..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml exec -T django python manage.py collectstatic --noinput

# Check container status
Write-Host "📋 Checking container status..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml ps

# Show logs
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps
Write-Host ""
Write-Host "🌐 Access your application at:"
Write-Host "   Frontend: http://your-server-ip"
Write-Host "   Backend API: http://your-server-ip/api/"
Write-Host "   Admin Panel: http://your-server-ip/admin/"
Write-Host ""
Write-Host "📝 View logs with:"
Write-Host "   docker-compose -f docker-compose.prod.yml logs -f"
Write-Host ""
Write-Host "🛑 Stop services with:"
Write-Host "   docker-compose -f docker-compose.prod.yml down"
