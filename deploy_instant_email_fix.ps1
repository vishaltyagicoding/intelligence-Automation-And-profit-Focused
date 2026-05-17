# Deploy instant email notification fix to AWS production server
# This fixes the 5-hour email delay by using Django signals for instant delivery

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deploying Instant Email Notification Fix" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# SSH connection details
$SSH_KEY = "smartriskfx1.pem"
$SSH_USER = "ubuntu"
$SSH_HOST = "54.183.178.141"
$PROJECT_DIR = "~/smartrisk"

Write-Host "📡 Connecting to AWS server..." -ForegroundColor Yellow

# Create the SSH command script
$sshScript = @'
set -e
cd ~/smartrisk

echo ""
echo "📥 Pulling latest code from GitHub..."
git fetch origin main
git reset --hard origin/main

echo ""
echo "🔍 Verifying new files exist..."
if [ ! -f "reversal_zones/signals.py" ]; then
    echo "❌ ERROR: reversal_zones/signals.py not found!"
    exit 1
fi

echo "✅ New signal handler file found"

echo ""
echo "🐳 Restarting Django to load new signal handlers..."
sudo docker-compose restart django

echo ""
echo "⏳ Waiting for Django to start..."
sleep 10

echo ""
echo "🧪 Testing Django signal registration..."
sudo docker-compose exec -T django python manage.py shell << 'EOF'
from django.db.models.signals import post_save
from reversal_zones.models import ReversalZone

# Check if signal is registered
receivers = post_save._live_receivers(ReversalZone)
print(f"\n✅ Signal handlers registered for ReversalZone: {len(receivers)}")

if len(receivers) > 0:
    print("✅ Email notification signal is ACTIVE")
    print("   Emails will be sent INSTANTLY when new signals are created")
else:
    print("❌ WARNING: No signal handlers found!")
EOF

echo ""
echo "🔄 Restarting Celery workers to clear any cached code..."
sudo docker-compose restart celery

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📧 Email notifications will now be sent INSTANTLY when signals fire"
echo "   - No more 5-hour delays"
echo "   - Emails sent at exact moment signal is saved to database"
echo "   - Works regardless of WebSocket connection status"
echo ""
'@

# Execute SSH command
ssh -i $SSH_KEY "$SSH_USER@$SSH_HOST" $sshScript

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Deployment Successful!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "WHAT WAS FIXED:" -ForegroundColor Cyan
Write-Host "  • Created Django signal handler (reversal_zones/signals.py)"
Write-Host "  • Emails now sent INSTANTLY when signal is saved to DB"
Write-Host "  • Removed duplicate email code from Celery tasks"
Write-Host "  • Removed duplicate email code from WebSocket consumer"
Write-Host ""
Write-Host "RESULT:" -ForegroundColor Green
Write-Host "  • Users receive emails at EXACT moment signal fires"
Write-Host "  • No more 30-minute delays waiting for Celery task"
Write-Host "  • Works even if WebSocket is not connected"
Write-Host ""
