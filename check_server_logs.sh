#!/bin/bash
# Check server logs to see what's happening with signal generation and email sending

echo "🔍 Checking server logs for signal generation and email sending..."
echo "=================================================================="

ssh -i smartriskfx-singapore.pem ubuntu@13.250.19.107 << 'EOF'
cd ~/smartrisk

echo "📋 Last 50 lines of Django logs (looking for signal and email activity):"
echo "========================================================================"
sudo docker-compose logs --tail=50 django | grep -E "(LIVE SIGNAL|INSTANT EMAIL|emit_live_signal|send_instant_email)"

echo ""
echo "📋 Last 50 lines of Celery Beat logs (checking for scheduled tasks):"
echo "====================================================================="
sudo docker-compose logs --tail=50 celery_beat | grep -E "(update.*signal|reversal)"

echo ""
echo "📋 Last 50 lines of Celery Worker logs (checking for task execution):"
echo "======================================================================"
sudo docker-compose logs --tail=50 celery_worker | grep -E "(update.*signal|reversal|email)"

echo ""
echo "🔍 Checking which Celery tasks are currently enabled:"
echo "====================================================="
sudo docker-compose exec -T django python << 'PYEOF'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django_celery_beat.models import PeriodicTask

print("\n📋 ALL Celery Beat Tasks:")
print("=" * 70)
for task in PeriodicTask.objects.all():
    status = "✅ ENABLED" if task.enabled else "❌ DISABLED"
    print(f"{status}: {task.name}")
    print(f"   Task: {task.task}")
    if task.crontab:
        print(f"   Schedule: {task.crontab}")
    if task.interval:
        print(f"   Interval: Every {task.interval.every} {task.interval.period}")
    print()

print("\n🔍 Signal-related tasks:")
print("=" * 70)
signal_tasks = PeriodicTask.objects.filter(task__icontains='signal')
if signal_tasks.exists():
    for task in signal_tasks:
        status = "✅ ENABLED" if task.enabled else "❌ DISABLED"
        print(f"{status}: {task.name} - {task.task}")
else:
    print("No signal-related tasks found")

PYEOF

echo ""
echo "🔍 Checking current Git commit on server:"
echo "=========================================="
git log --oneline -1

echo ""
echo "✅ Log check complete!"

EOF
