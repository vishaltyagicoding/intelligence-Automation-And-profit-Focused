# PowerShell script for Windows
Write-Host "🚀 NeuralTrade - Building and Running Production Environment" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Stop and remove old containers
Write-Host "📦 Stopping old containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# Remove old images
Write-Host "🗑️  Removing old images..." -ForegroundColor Yellow
docker rmi neuraltrade-backend:latest 2>$null
docker rmi neuraltrade-frontend:latest 2>$null

# Prune unused images
Write-Host "🧹 Cleaning up unused Docker images..." -ForegroundColor Yellow
docker image prune -f

# Build new images
Write-Host "🔨 Building backend image..." -ForegroundColor Cyan
docker build -f Dockerfile.backend -t neuraltrade-backend:latest .

Write-Host "🔨 Building frontend image..." -ForegroundColor Cyan
docker build -f Dockerfile.frontend -t neuraltrade-frontend:latest .

# Start services
Write-Host "🚀 Starting all services..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Show status
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access your application:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost"
Write-Host "   Backend API: http://localhost/api/"
Write-Host "   Django Admin: http://localhost/admin/"
Write-Host "   WebSocket: ws://localhost/ws/live/"
Write-Host ""
Write-Host "📝 View logs:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.prod.yml logs -f"
Write-Host ""
