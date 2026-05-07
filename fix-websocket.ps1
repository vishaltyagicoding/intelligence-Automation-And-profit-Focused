#!/usr/bin/env pwsh
# WebSocket Fix - Rebuild and Restart Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WebSocket Connection Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if .env has Binance credentials
Write-Host "[1/5] Checking Binance API credentials..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw
if ($envContent -match "BINANCE_API_KEY=your-binance-api-key" -or $envContent -match "BINANCE_API_SECRET=your-binance-api-secret") {
    Write-Host "WARNING: Binance API credentials are not set!" -ForegroundColor Red
    Write-Host "Please update .env file with your real Binance API credentials." -ForegroundColor Red
    Write-Host "See WEBSOCKET_FIX_GUIDE.md for instructions." -ForegroundColor Red
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Exiting. Please set up Binance API credentials first." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Binance API credentials found" -ForegroundColor Green
}
Write-Host ""

# Step 2: Stop containers
Write-Host "[2/5] Stopping containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml stop backend
Write-Host "✓ Backend stopped" -ForegroundColor Green
Write-Host ""

# Step 3: Rebuild backend
Write-Host "[3/5] Rebuilding backend with WebSocket fixes..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml build backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Backend build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Backend rebuilt successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Rebuild frontend
Write-Host "[4/5] Rebuilding frontend with ping/pong handlers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml build frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Frontend rebuilt successfully" -ForegroundColor Green
Write-Host ""

# Step 5: Start containers
Write-Host "[5/5] Starting containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml up -d backend frontend
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start containers!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Containers started" -ForegroundColor Green
Write-Host ""

# Show status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps
Write-Host ""

# Show logs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recent Backend Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml logs --tail=20 backend
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "WebSocket Fix Applied Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "2. Check that prices are updating (not $0.0000)" -ForegroundColor White
Write-Host "3. Open browser DevTools (F12) and check Console for WebSocket messages" -ForegroundColor White
Write-Host "4. Monitor for 10-15 minutes to ensure stability" -ForegroundColor White
Write-Host ""
Write-Host "To view live logs:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose.prod.yml logs -f backend" -ForegroundColor White
Write-Host ""
Write-Host "If you see 'Invalid API-key' errors, update .env with real Binance credentials." -ForegroundColor Yellow
Write-Host "See WEBSOCKET_FIX_GUIDE.md for detailed instructions." -ForegroundColor Yellow
