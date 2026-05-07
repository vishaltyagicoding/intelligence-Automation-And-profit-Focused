# Start AI Signal Generation for BTCUSD
# This script starts the continuous signal generation in the background

Write-Host "🤖 Starting AI Signal Generation for BTCUSD..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Start signal generation using Django management command
docker-compose -f docker-compose.prod.yml exec -d backend python manage.py start_signals --interval 60

Write-Host "✅ AI Signal Generation started!" -ForegroundColor Green
Write-Host ""
Write-Host "Signals will be generated every 60 seconds" -ForegroundColor Yellow
Write-Host "View signals at: http://localhost" -ForegroundColor Yellow
Write-Host "View signal history at: http://localhost/history" -ForegroundColor Yellow
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose.prod.yml logs -f backend | Select-String 'AI Signal'" -ForegroundColor White
Write-Host ""
Write-Host "To stop signal generation:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose.prod.yml restart backend" -ForegroundColor White
