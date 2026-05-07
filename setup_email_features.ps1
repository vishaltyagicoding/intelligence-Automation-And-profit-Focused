# PowerShell script for Windows
Write-Host "🚀 Setting up Email Verification & Password Reset Features" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create migrations
Write-Host "📝 Step 1: Creating database migrations..." -ForegroundColor Yellow
docker-compose exec -T django python manage.py makemigrations users
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create migrations" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Apply migrations
Write-Host "📝 Step 2: Applying migrations..." -ForegroundColor Yellow
docker-compose exec -T django python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations applied successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Rebuild backend
Write-Host "🔨 Step 3: Rebuilding backend container..." -ForegroundColor Yellow
docker-compose stop django celery_worker celery_beat
docker-compose build django
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to rebuild backend" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Start backend
Write-Host "▶️  Step 4: Starting backend services..." -ForegroundColor Yellow
docker-compose up -d django celery_worker celery_beat
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start backend services" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 5: Rebuild frontend
Write-Host "🔨 Step 5: Rebuilding frontend container..." -ForegroundColor Yellow
docker-compose stop frontend
docker-compose build frontend
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to rebuild frontend" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 6: Start frontend
Write-Host "▶️  Step 6: Starting frontend service..." -ForegroundColor Yellow
docker-compose up -d frontend
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend service started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start frontend service" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host ""

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Yellow
docker-compose ps
Write-Host ""

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Clear your browser cache (Ctrl + Shift + R)"
Write-Host "2. Go to http://localhost/register"
Write-Host "3. Test email verification"
Write-Host "4. Test forgot password from login page"
Write-Host ""
Write-Host "📧 Email Configuration:" -ForegroundColor Yellow
Write-Host "   Email: alberttyagi123@gmail.com"
Write-Host "   Check your inbox for OTP codes"
Write-Host ""
Write-Host "📚 For more details, see SETUP_INSTRUCTIONS.md" -ForegroundColor Cyan
Write-Host ""
