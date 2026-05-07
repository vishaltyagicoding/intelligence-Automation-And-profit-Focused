#!/usr/bin/env pwsh
# ============================================================================
# NeuralTrade AI Trading Platform - One-Click Setup
# ============================================================================
# This script does EVERYTHING automatically!
# Just run: .\START_EVERYTHING.ps1
# ============================================================================

param(
    [switch]$SkipModelCheck,
    [switch]$QuickStart
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Step { param($msg) Write-Host "`n🔹 $msg" -ForegroundColor Magenta }

Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║        🚀 NeuralTrade AI Trading Platform 🚀              ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║        Fully Automated AI Trading System                  ║" -ForegroundColor Cyan
Write-Host "║        Users Deposit → AI Does Everything!                ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

Write-Step "Pre-Flight Checks"

# Check Docker
Write-Info "Checking Docker..."
try {
    $dockerVersion = docker --version
    Write-Success "Docker is installed: $dockerVersion"
} catch {
    Write-Error "Docker is not installed or not running!"
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker is running
try {
    docker ps | Out-Null
    Write-Success "Docker is running"
} catch {
    Write-Error "Docker is not running!"
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check docker-compose
Write-Info "Checking docker-compose..."
try {
    $composeVersion = docker-compose --version
    Write-Success "docker-compose is installed: $composeVersion"
} catch {
    Write-Error "docker-compose is not installed!"
    exit 1
}

# ============================================================================
# DIRECTORY SETUP
# ============================================================================

Write-Step "Setting Up Directories"

$dirs = @("logs", "models/production", "models/backups", "staticfiles", "media")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Success "Created directory: $dir"
    } else {
        Write-Info "Directory exists: $dir"
    }
}

# ============================================================================
# MODEL FILE CHECK
# ============================================================================

if (-not $SkipModelCheck) {
    Write-Step "Checking Model File"
    
    if (Test-Path "models/production/model.pth") {
        $size = (Get-Item "models/production/model.pth").Length / 1MB
        Write-Success "Model file found ($([math]::Round($size, 2)) MB)"
    } else {
        Write-Warning "Model file not found!"
        Write-Host ""
        Write-Host "Please copy your trained model:" -ForegroundColor Yellow
        Write-Host 'Copy-Item "$env:USERPROFILE\Downloads\best_model.pth" -Destination "models\production\model.pth"' -ForegroundColor White
        Write-Host ""
        Write-Host "Press Enter to continue without model (you can add it later)..." -ForegroundColor Yellow
        Write-Host "Or press Ctrl+C to exit and add the model first." -ForegroundColor Yellow
        Read-Host
    }
}

# ============================================================================
# ENVIRONMENT FILE CHECK
# ============================================================================

Write-Step "Checking Environment Configuration"

if (Test-Path ".env") {
    Write-Success ".env file exists"
} else {
    Write-Warning ".env file not found, but it should have been created!"
}

# ============================================================================
# DOCKER BUILD
# ============================================================================

Write-Step "Building Docker Images"

Write-Info "This will take 5-10 minutes (downloading TensorFlow, PyTorch, etc.)"
Write-Info "Building images..."
Write-Host ""

if ($QuickStart) {
    Write-Warning "Quick start mode: Skipping build (using existing images)"
} else {
    docker-compose build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker images built successfully"
    } else {
        Write-Error "Docker build failed!"
        Write-Host ""
        Write-Host "Common issues:" -ForegroundColor Yellow
        Write-Host "1. Network timeout → Try again" -ForegroundColor White
        Write-Host "2. Disk space → Free up space" -ForegroundColor White
        Write-Host "3. Memory → Close other applications" -ForegroundColor White
        Write-Host ""
        exit 1
    }
}

# ============================================================================
# START SERVICES
# ============================================================================

Write-Step "Starting Services"

Write-Info "Starting all containers..."
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Success "All services started"
} else {
    Write-Error "Failed to start services!"
    Write-Host ""
    Write-Host "Check logs: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# WAIT FOR SERVICES
# ============================================================================

Write-Step "Waiting for Services to Initialize"

Write-Info "Waiting 30 seconds for database and services to be ready..."
$seconds = 30
for ($i = $seconds; $i -gt 0; $i--) {
    Write-Progress -Activity "Initializing Services" -Status "$i seconds remaining..." -PercentComplete ((($seconds - $i) / $seconds) * 100)
    Start-Sleep -Seconds 1
}
Write-Progress -Activity "Initializing Services" -Completed

Write-Success "Services should be ready"

# ============================================================================
# VERIFY SETUP
# ============================================================================

Write-Step "Verifying Setup"

Write-Info "Checking container status..."
Write-Host ""

$containers = @(
    "neuraltrade_db",
    "neuraltrade_redis",
    "neuraltrade_django",
    "neuraltrade_celery_worker",
    "neuraltrade_celery_beat"
)

$allHealthy = $true
foreach ($container in $containers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}"
    if ($status) {
        if ($status -match "healthy" -or $status -match "Up") {
            Write-Success "$container is running"
        } else {
            Write-Warning "$container status: $status"
        }
    } else {
        Write-Error "$container is NOT running"
        $allHealthy = $false
    }
}

Write-Host ""

# ============================================================================
# TEST WEB INTERFACE
# ============================================================================

Write-Step "Testing Web Interface"

Write-Info "Waiting for web interface to be ready..."
$maxAttempts = 10
$attempt = 0
$webReady = $false

while ($attempt -lt $maxAttempts -and -not $webReady) {
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $webReady = $true
            Write-Success "Web interface is accessible"
        }
    } catch {
        Write-Info "Attempt $attempt/$maxAttempts - Waiting for web interface..."
        Start-Sleep -Seconds 3
    }
}

if (-not $webReady) {
    Write-Warning "Web interface not ready yet. It may need more time."
    Write-Info "Check logs: docker-compose logs django"
}

# ============================================================================
# FINAL STATUS
# ============================================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║                  🎉 SETUP COMPLETE! 🎉                    ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📍 ACCESS POINTS:" -ForegroundColor Cyan
Write-Host "   • Web Interface:  http://localhost:8000" -ForegroundColor White
Write-Host "   • Admin Panel:    http://localhost:8000/admin" -ForegroundColor White
Write-Host "     Username: admin" -ForegroundColor Gray
Write-Host "     Password: admin123" -ForegroundColor Gray
Write-Host ""

Write-Host "📊 MONITORING:" -ForegroundColor Cyan
Write-Host "   • Watch auto-trading:  docker-compose logs -f celery_worker" -ForegroundColor White
Write-Host "   • Watch all logs:      docker-compose logs -f" -ForegroundColor White
Write-Host "   • Check status:        docker-compose ps" -ForegroundColor White
Write-Host ""

Write-Host "⚡ AUTO-TRADING STATUS:" -ForegroundColor Cyan
Write-Host "   • Runs every 5 minutes automatically" -ForegroundColor White
Write-Host "   • All 3 agents analyze markets" -ForegroundColor White
Write-Host "   • Trades executed if confidence > 75%" -ForegroundColor White
Write-Host "   • All agents learn from every trade" -ForegroundColor White
Write-Host ""

Write-Host "🛑 STOP SERVICES:" -ForegroundColor Cyan
Write-Host "   • docker-compose down" -ForegroundColor White
Write-Host ""

Write-Host "📚 DOCUMENTATION:" -ForegroundColor Cyan
Write-Host "   • QUICK_START.md - Quick start guide" -ForegroundColor White
Write-Host "   • START_AUTOMATED_TRADING.md - Auto-trading config" -ForegroundColor White
Write-Host "   • FINAL_DEPLOYMENT_SUMMARY.md - Complete overview" -ForegroundColor White
Write-Host ""

Write-Host "🎯 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "   1. Open http://localhost:8000 in your browser" -ForegroundColor White
Write-Host "   2. Login to admin panel (admin/admin123)" -ForegroundColor White
Write-Host "   3. Enable auto-trading for users" -ForegroundColor White
Write-Host "   4. Watch the magic happen!" -ForegroundColor White
Write-Host ""

Write-Host "💡 TIP: Run .\verify_setup.ps1 to verify everything is working" -ForegroundColor Yellow
Write-Host ""

# Open browser automatically
if ($allHealthy -and $webReady) {
    Write-Info "Opening web interface in browser..."
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"
}

Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
