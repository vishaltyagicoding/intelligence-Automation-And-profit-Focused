#!/usr/bin/env python3
"""Check device fingerprints in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from users.models import DeviceFingerprint, User

print("\n" + "="*60)
print("DEVICE FINGERPRINT CHECK")
print("="*60)

# Count records
device_count = DeviceFingerprint.objects.count()
user_count = User.objects.count()

print(f"\nTotal DeviceFingerprints: {device_count}")
print(f"Total Users: {user_count}")

# Show all device fingerprints
if device_count > 0:
    print("\n" + "-"*60)
    print("DEVICE FINGERPRINTS:")
    print("-"*60)
    for d in DeviceFingerprint.objects.all():
        print(f"\nDevice ID: {d.device_id[:30]}...")
        print(f"  User: {d.user.email if d.user else 'None'}")
        print(f"  Trial Granted: {d.trial_granted}")
        print(f"  Trial Count: {d.trial_count}")
        print(f"  IP Address: {d.ip_address}")
        print(f"  First Seen: {d.first_seen}")
        print(f"  Last Seen: {d.last_seen}")
        print(f"  Blocked: {d.is_blocked}")
else:
    print("\n⚠️  NO DEVICE FINGERPRINTS FOUND!")
    print("This means device fingerprints are NOT being saved!")

# Show all users with device info
print("\n" + "-"*60)
print("USERS WITH DEVICE INFO:")
print("-"*60)
for u in User.objects.all():
    print(f"\nEmail: {u.email}")
    print(f"  Device ID: {u.device_id or 'None'}")
    print(f"  Registration IP: {u.registration_ip or 'None'}")
    print(f"  Trial Allowed: {u.trial_allowed}")
    print(f"  Trial Used: {u.trial_used}")
    print(f"  Created: {u.created_at}")

print("\n" + "="*60 + "\n")
