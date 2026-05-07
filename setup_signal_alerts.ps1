# PowerShell script to set up Signal Alerts System

Write-Host "🔔 Setting up Signal Alerts System" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Run migrations
Write-Host "📦 Running database migrations..." -ForegroundColor Yellow
docker-compose exec django python manage.py makemigrations signal_alerts
docker-compose exec django python manage.py migrate signal_alerts
Write-Host "✅ Migrations completed" -ForegroundColor Green
Write-Host ""

# Test the system
Write-Host "🧪 Testing signal alert system..." -ForegroundColor Yellow
docker-compose exec django python manage.py test_signal_alerts
Write-Host ""

Write-Host "✅ Setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "1. Visit http://localhost/signal-alerts to create an alert"
Write-Host "2. Make sure you have a paid subscription (not trial)"
Write-Host "3. When a new signal is generated, you'll receive an email"
Write-Host ""
Write-Host "🔍 To test with a specific email:" -ForegroundColor Yellow
Write-Host "docker-compose exec django python manage.py test_signal_alerts --email=your@email.com --username=YourName"
