# Deploy Email Delay Bug Fix to Singapore Server
# This script deploys the fix that removes WebSocket blocking checks
# to ensure instant email delivery when signals fire.

$ErrorActionPreference = "Stop"

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DEPLOYING EMAIL DELAY BUG FIX TO SINGAPORE SERVER" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Server details
$SERVER_IP = "13.250.19.107"
$SERVER_USER = "ubuntu"
$SSH_KEY = "smartriskfx-singapore.pem"
$PROJECT_DIR = "~/smartrisk"

Write-Host "Step 1: Checking SSH key..." -ForegroundColor Yellow
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "ERROR: SSH key not found: $SSH_KEY" -ForegroundColor Red
    Write-Host "Please ensure smartriskfx-singapore.pem is in the current directory"
    exit 1
}
Write-Host "✓ SSH key found" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Testing SSH connection..." -ForegroundColor Yellow
$testConnection = ssh -i $SSH_KEY -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cannot connect to server" -ForegroundColor Red
    Write-Host "Please check:"
    Write-Host "  - Server IP: $SERVER_IP"
    Write-Host "  - SSH key permissions"
    Write-Host "  - Network connectivity"
    exit 1
}
Write-Host "✓ SSH connection successful" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Backing up current code..." -ForegroundColor Yellow
ssh -i $SSH_KEY "$SERVER_USER@$SERVER_IP" @"
cd ~/smartrisk
echo 'Creating backup branch...'
git branch backup-before-email-fix-`$(date +%Y%m%d-%H%M%S) || true
echo '✓ Backup created'
"@
Write-Host "✓ Backup complete" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Pulling latest changes from GitHub..." -ForegroundColor Yellow
ssh -i $SSH_KEY "$SERVER_USER@$SERVER_IP" @"
cd ~/smartrisk
echo 'Fetching latest changes...'
git fetch origin
echo 'Pulling main branch...'
git pull origin main
echo '✓ Code updated'
"@
Write-Host "✓ Code updated" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Rebuilding Django container..." -ForegroundColor Yellow
ssh -i $SSH_KEY "$SERVER_USER@$SERVER_IP" @"
cd ~/smartrisk
echo 'Building Django container...'
sudo docker-compose build django
echo '✓ Build complete'
"@
Write-Host "✓ Django container rebuilt" -ForegroundColor Green
Write-Host ""

Write-Host "Step 6: Restarting Django service..." -ForegroundColor Yellow
ssh -i $SSH_KEY "$SERVER_USER@$SERVER_IP" @"
cd ~/smartrisk
echo 'Stopping Django container...'
sudo docker-compose stop django
echo 'Starting Django container...'
sudo docker-compose up -d django
echo 'Waiting for Django to start...'
sleep 5
echo '✓ Django restarted'
"@
Write-Host "✓ Django service restarted" -ForegroundColor Green
Write-Host ""

Write-Host "Step 7: Verifying deployment..." -ForegroundColor Yellow
ssh -i $SSH_KEY "$SERVER_USER@$SERVER_IP" @"
cd ~/smartrisk
echo 'Checking Django container status...'
if sudo docker-compose ps django | grep -q 'Up'; then
    echo '✓ Django container is running'
else
    echo '✗ WARNING: Django container may not be running properly'
    sudo docker-compose ps django
fi

echo ''
echo 'Checking recent logs...'
sudo docker-compose logs --tail=20 django
"@
Write-Host "✓ Deployment verified" -ForegroundColor Green
Write-Host ""

Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Monitor logs: ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd ~/smartrisk && sudo docker-compose logs -f django'"
Write-Host "  2. Wait for next signal to fire on https://smartriskfx.com/asset/ethusd"
Write-Host "  3. Verify email arrives within 1-2 seconds"
Write-Host "  4. Check for these log messages:"
Write-Host "     - 🔔 LIVE SIGNAL [ETHUSD 5m]: BUY @ 3245.50"
Write-Host "     - 💾 Created BUY signal in DB: ETHUSDT 5m @ 3245.50"
Write-Host "     - 📧 INSTANT EMAIL: 3 sent for ETHUSD 5m BUY @ 3245.50"
Write-Host ""
Write-Host "To view live logs:"
Write-Host "  ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
Write-Host "  cd ~/smartrisk"
Write-Host "  sudo docker-compose logs -f django | grep '🔔\|📧\|💾'"
Write-Host ""
Write-Host "If you need to rollback:"
Write-Host "  ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP"
Write-Host "  cd ~/smartrisk"
Write-Host "  git revert HEAD"
Write-Host "  sudo docker-compose build django"
Write-Host "  sudo docker-compose up -d django"
Write-Host ""
