# NeuralTrade Setup Verification Script
# Run this after docker-compose up -d to verify everything is working

Write-Host "🔍 NeuralTrade Setup Verification" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "   ✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if containers are running
Write-Host "2. Checking Containers..." -ForegroundColor Yellow
$containers = @(
    "neuraltrade_db",
    "neuraltrade_redis",
    "neuraltrade_django",
    "neuraltrade_celery_worker",
    "neuraltrade_celery_beat"
)

$allRunning = $true
foreach ($container in $containers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}"
    if ($status) {
        Write-Host "   ✅ $container is running" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $container is NOT running" -ForegroundColor Red
        $allRunning = $false
    }
}

Write-Host ""

# Check if model file exists
Write-Host "3. Checking Model File..." -ForegroundColor Yellow
if (Test-Path "models\production\model.pth") {
    $size = (Get-Item "models\production\model.pth").Length / 1MB
    Write-Host "   ✅ Model file exists ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Model file not found. Copy your trained model to models\production\model.pth" -ForegroundColor Yellow
}

Write-Host ""

# Check if .env file exists
Write-Host "4. Checking Environment File..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✅ .env file exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ .env file not found" -ForegroundColor Red
}

Write-Host ""

# Check if logs directory exists
Write-Host "5. Checking Directories..." -ForegroundColor Yellow
$dirs = @("logs", "models\production", "models\backups")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "   ✅ $dir exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dir not found" -ForegroundColor Red
    }
}

Write-Host ""

# Test web interface
Write-Host "6. Testing Web Interface..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Web interface is accessible at http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Web interface not ready yet. Wait 30 seconds and try again." -ForegroundColor Yellow
}

Write-Host ""

# Check Celery tasks
Write-Host "7. Checking Auto-Trading..." -ForegroundColor Yellow
try {
    $celeryLogs = docker logs neuraltrade_celery_beat --tail 20 2>&1
    if ($celeryLogs -match "auto-trading-loop") {
        Write-Host "   ✅ Auto-trading loop is scheduled" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Auto-trading loop not found in logs" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Could not check Celery logs" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

if ($allRunning) {
    Write-Host "🎉 Setup Complete! All systems operational." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Access web interface: http://localhost:8000" -ForegroundColor White
    Write-Host "2. Admin panel: http://localhost:8000/admin (admin/admin123)" -ForegroundColor White
    Write-Host "3. Watch auto-trading: docker-compose logs -f celery_worker" -ForegroundColor White
    Write-Host ""
    Write-Host "📚 Read QUICK_START.md for detailed instructions" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Some containers are not running. Check logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs" -ForegroundColor White
    Write-Host ""
    Write-Host "Try restarting:" -ForegroundColor Yellow
    Write-Host "   docker-compose down" -ForegroundColor White
    Write-Host "   docker-compose up -d" -ForegroundColor White
}

Write-Host ""
