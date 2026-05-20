#!/usr/bin/env python3
"""
NUCLEAR OPTION: Disable ALL signal-related Celery tasks

This script connects to the server and disables EVERY Celery Beat task
that has "signal" in its name or task path. This ensures NO background
tasks are interfering with the WebSocket live signal detection.
"""

DISABLE_SCRIPT = """
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from django_celery_beat.models import PeriodicTask

print("🔍 Finding ALL signal-related Celery tasks...")
print("=" * 70)

# Find all tasks with "signal" in name or task
signal_tasks = PeriodicTask.objects.filter(
    task__icontains='signal'
) | PeriodicTask.objects.filter(
    name__icontains='signal'
)

if not signal_tasks.exists():
    print("✅ No signal-related tasks found")
else:
    print(f"Found {signal_tasks.count()} signal-related tasks:\\n")
    
    for task in signal_tasks:
        status_before = "ENABLED" if task.enabled else "DISABLED"
        print(f"📋 {task.name}")
        print(f"   Task: {task.task}")
        print(f"   Status BEFORE: {status_before}")
        
        if task.enabled:
            task.enabled = False
            task.save()
            print(f"   Status AFTER: ❌ DISABLED")
            print(f"   ✅ Task has been DISABLED!")
        else:
            print(f"   Status AFTER: ❌ DISABLED (already)")
        print()

print("=" * 70)
print("✅ ALL signal-related tasks have been disabled!")
print("\\nWebSocket live signals are now the ONLY source of truth.")
"""

print("This script will disable ALL signal-related Celery tasks on the server.")
print("=" * 70)
print()
print("MANUAL STEPS:")
print("1. SSH to server: ssh -i smartriskfx-singapore.pem ubuntu@13.250.19.107")
print("2. Navigate: cd ~/smartrisk")
print("3. Open shell: sudo docker-compose exec django python manage.py shell")
print("4. Paste this code:")
print()
print(DISABLE_SCRIPT)
print()
print("5. Exit shell: exit()")
print("6. Restart Celery: sudo docker-compose restart celery_beat celery_worker")
print("=" * 70)
