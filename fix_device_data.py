#!/usr/bin/env python3
"""Fix device fingerprint data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from users.models import DeviceFingerprint, User
from django.utils import timezone

print("\n" + "="*60)
print("FIXING DEVICE FINGERPRINT DATA")
print("="*60)

# Get the device record
device = DeviceFingerprint.objects.first()

if device:
    print(f"\nCurrent Device State:")
    print(f"  Device ID: {device.device_id[:30]}...")
    print(f"  Trial Granted: {device.trial_granted}")
    print(f"  Trial Count: {device.trial_count}")
    
    # Find the FIRST user who registered with this device
    first_user = User.objects.filter(device_id=device.device_id).order_by('created_at').first()
    
    if first_user:
        print(f"\nFirst User on this Device:")
        print(f"  Email: {first_user.email}")
        print(f"  Created: {first_user.created_at}")
        print(f"  Trial Allowed: {first_user.trial_allowed}")
        
        # Fix: First user should have trial_granted=True
        device.trial_granted = True
        device.user = first_user
        device.save()
        
        # Also ensure first user has trial_allowed=True
        if not first_user.trial_allowed:
            first_user.trial_allowed = True
            first_user.save()
        
        print(f"\n✅ FIXED: Device trial_granted set to True for first user")
        
        # Check if there are other users with same device
        other_users = User.objects.filter(device_id=device.device_id).exclude(id=first_user.id)
        
        if other_users.exists():
            print(f"\nOther Users on Same Device:")
            for u in other_users:
                print(f"  Email: {u.email}")
                print(f"  Trial Allowed: {u.trial_allowed}")
                
                # These users should NOT have trial
                if u.trial_allowed:
                    u.trial_allowed = False
                    u.save()
                    print(f"  ✅ FIXED: Set trial_allowed=False")
    
    print("\n" + "="*60)
    print("FINAL STATE:")
    print("="*60)
    print(f"Device trial_granted: {device.trial_granted}")
    print(f"Device trial_count: {device.trial_count}")
    
    for u in User.objects.filter(device_id=device.device_id).order_by('created_at'):
        print(f"\n{u.email}:")
        print(f"  Trial Allowed: {u.trial_allowed}")
        print(f"  Created: {u.created_at}")
    
    print("\n" + "="*60 + "\n")
else:
    print("\n⚠️  No device fingerprints found!\n")
