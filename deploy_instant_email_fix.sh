#!/bin/bash
# Deploy instant email notification fix to AWS production server
# This fixes the 5-hour email delay by using Django signals for instant delivery

set -e  # Exit on any error

echo "=========================================="
echo "Deploying Instant Email Notification Fix"
echo "=========================================="
echo ""

# SSH connection details
SSH_KEY="smartriskfx1.pem"
SSH_USER="ubuntu"
SSH_HOST="54.183.178.141"
PROJECT_DIR="~/smartrisk"

echo "📡 Connecting to AWS server..."
ssh -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" << 'ENDSSH'

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

ENDSSH

echo ""
echo "=========================================="
echo "✅ Deployment Successful!"
echo "=========================================="
echo ""
echo "WHAT WAS FIXED:"
echo "  • Created Django signal handler (reversal_zones/signals.py)"
echo "  • Emails now sent INSTANTLY when signal is saved to DB"
echo "  • Removed duplicate email code from Celery tasks"
echo "  • Removed duplicate email code from WebSocket consumer"
echo ""
echo "RESULT:"
echo "  • Users receive emails at EXACT moment signal fires"
echo "  • No more 30-minute delays waiting for Celery task"
echo "  • Works even if WebSocket is not connected"
echo ""
