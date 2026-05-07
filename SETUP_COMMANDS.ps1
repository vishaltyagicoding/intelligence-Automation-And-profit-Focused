# ============================================================================
# NeuralTrade AI Trading Platform - Complete Setup Script
# ============================================================================
# This script sets up everything automatically!
# ============================================================================

Write-Host ""
Write-Host "🚀 NeuralTrade AI Trading Platform Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy trained model
Write-Host "📦 Step 1: Copy Your Trained Model" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "Run this command to copy your model:" -ForegroundColor White
Write-Host 'Copy-Item "$env:USERPROFILE\Downloads\best_model.pth" -Destination "models\production\model.pth"' -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter when done..." -ForegroundColor Yellow
Read-Host

# Verify model exists
if (Test-Path "models\production\model.pth") {
    $size = (Get-Item "models\production\model.pth").Length / 1MB
    Write-Host "✅ Model file found ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Model file not found. Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Build Docker images
Write-Host "🐳 Step 2: Building Docker Images" -ForegroundColor Yellow
Write-Host "----------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will take 5-10 minutes (downloading TensorFlow, PyTorch, etc.)" -ForegroundColor White
Write-Host ""
Write-Host "Building..." -ForegroundColor Cyan

docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker images built successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Docker build failed. Check errors above." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Start services
Write-Host "🚀 Step 3: Starting Services" -ForegroundColor Yellow
Write-Host "-----------------------------" -ForegroundColor Yellow
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Wait for services to be ready
Write-Host "⏳ Step 4: Waiting for Services to be Ready" -ForegroundColor Yellow
Write-Host "--------------------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "Waiting 30 seconds for database and services to initialize..." -ForegroundColor White

Start-Sleep -Seconds 30

Write-Host "✅ Services should be ready now" -ForegroundColor Green
Write-Host ""

# Step 5: Check status
Write-Host "📊 Step 5: Checking Status" -ForegroundColor Yellow
Write-Host "--------------------------" -ForegroundColor Yellow
Write-Host ""

docker-compose ps

Write-Host ""

# Step 6: Verify setup
Write-Host "🔍 Step 6: Running Verification" -ForegroundColor Yellow
Write-Host "--------------------------------" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "verify_setup.ps1") {
    .\verify_setup.ps1
} else {
    Write-Host "⚠️  Verification script not found" -ForegroundColor Yellow
}

Write-Host ""

# Final instructions
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access Points:" -ForegroundColor Cyan
Write-Host "   • Web Interface: http://localhost:8000" -ForegroundColor White
Write-Host "   • Admin Panel: http://localhost:8000/admin" -ForegroundColor White
Write-Host "     Username: admin" -ForegroundColor Gray
Write-Host "     Password: admin123" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Monitoring:" -ForegroundColor Cyan
Write-Host "   • Watch auto-trading: docker-compose logs -f celery_worker" -ForegroundColor White
Write-Host "   • Watch all logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   • Check status: docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Stop Services:" -ForegroundColor Cyan
Write-Host "   • docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Read QUICK_START.md for detailed guide" -ForegroundColor White
Write-Host "   • Read START_AUTOMATED_TRADING.md for auto-trading config" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Auto-Trading Status:" -ForegroundColor Cyan
Write-Host "   • Runs every 5 minutes automatically" -ForegroundColor White
Write-Host "   • All 3 agents analyze markets" -ForegroundColor White
Write-Host "   • Trades executed if confidence > 75%" -ForegroundColor White
Write-Host "   • All agents learn from every trade" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Enable auto-trading for users in admin panel" -ForegroundColor White
Write-Host "   2. Configure real API keys in .env file" -ForegroundColor White
Write-Host "   3. Test with paper trading for 30 days" -ForegroundColor White
Write-Host "   4. Monitor performance and profits!" -ForegroundColor White
Write-Host ""
