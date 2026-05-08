# Fix Server Script
# Run this in PowerShell to diagnose and fix the server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SmartRisk Server Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test connectivity
Write-Host "Step 1: Testing server connectivity..." -ForegroundColor Yellow
$ping = Test-Connection -ComputerName 54.183.119.39 -Count 2 -Quiet
if ($ping) {
    Write-Host "✅ Server is reachable" -ForegroundColor Green
} else {
    Write-Host "❌ Server is not reachable" -ForegroundColor Red
    Write-Host "Please check AWS Console to see if instance is running" -ForegroundColor Yellow
    exit 1
}

# Step 2: Try SSH connection
Write-Host ""
Write-Host "Step 2: Attempting SSH connection..." -ForegroundColor Yellow
Write-Host "This may take a moment..." -ForegroundColor Gray

$sshTest = ssh -i "smartriskfx (1).pem" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@54.183.119.39 "echo 'SSH OK'" 2>&1

if ($sshTest -match "SSH OK") {
    Write-Host "✅ SSH connection successful" -ForegroundColor Green
} else {
    Write-Host "❌ SSH connection failed" -ForegroundColor Red
    Write-Host "Error: $sshTest" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible solutions:" -ForegroundColor Yellow
    Write-Host "1. Wait 2-3 minutes and try again (server might be busy)" -ForegroundColor White
    Write-Host "2. Restart EC2 instance from AWS Console" -ForegroundColor White
    Write-Host "3. Check Security Group allows SSH (port 22)" -ForegroundColor White
    exit 1
}

# Step 3: Check Docker services
Write-Host ""
Write-Host "Step 3: Checking Docker services..." -ForegroundColor Yellow

$services = ssh -i "smartriskfx (1).pem" -o ConnectTimeout=30 -o StrictHostKeyChecking=no ubuntu@54.183.119.39 "cd ~/smartrisk && sudo docker-compose ps" 2>&1

Write-Host $services
Write-Host ""

# Step 4: Check if services are running
if ($services -match "Up") {
    Write-Host "✅ Some services are running" -ForegroundColor Green
} else {
    Write-Host "⚠️ Services might be down" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Attempting to start services..." -ForegroundColor Yellow
    
    ssh -i "smartriskfx (1).pem" -o StrictHostKeyChecking=no ubuntu@54.183.119.39 @"
cd ~/smartrisk
sudo docker-compose down
sudo docker-compose up -d
"@
    
    Write-Host "✅ Services restart command sent" -ForegroundColor Green
    Write-Host "Wait 2 minutes, then check: http://54.183.119.39" -ForegroundColor Cyan
}

# Step 5: Test web access
Write-Host ""
Write-Host "Step 5: Testing web access..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://54.183.119.39" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ Website is accessible!" -ForegroundColor Green
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ Website is not accessible" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnosis Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If services are down, wait 2 minutes for them to start" -ForegroundColor White
Write-Host "2. Try accessing: http://54.183.119.39" -ForegroundColor White
Write-Host "3. If still not working, check AWS Console" -ForegroundColor White
Write-Host ""
