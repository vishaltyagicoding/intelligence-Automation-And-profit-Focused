#!/usr/bin/env python3
"""
Test OTP Registration Flow
===========================
This script tests the complete OTP registration flow to identify any issues.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from users.models import EmailVerification, User
from django.utils import timezone

def test_otp_flow():
    """Test the OTP flow for a specific email"""
    
    # Email to test
    test_email = "pythonbyvishal@gmail.com"
    
    print(f"\n{'='*60}")
    print(f"Testing OTP Flow for: {test_email}")
    print(f"{'='*60}\n")
    
    # Get all verification records for this email
    verifications = EmailVerification.objects.filter(email=test_email).order_by('-created_at')
    
    if not verifications.exists():
        print(f"❌ No verification records found for {test_email}")
        return
    
    print(f"Found {verifications.count()} verification record(s):\n")
    
    for i, v in enumerate(verifications, 1):
        print(f"Record #{i}:")
        print(f"  ID: {v.id}")
        print(f"  OTP: {v.otp}")
        print(f"  Username: {v.username}")
        print(f"  Verified: {v.is_verified}")
        print(f"  Attempts: {v.attempts}/5")
        print(f"  Created: {v.created_at}")
        print(f"  Expires: {v.expires_at}")
        print(f"  Expired: {v.is_expired()}")
        print(f"  Can Retry: {v.can_retry()}")
        print()
    
    # Get the latest unverified record
    latest = verifications.filter(is_verified=False).first()
    
    if latest:
        print(f"{'='*60}")
        print(f"LATEST ACTIVE VERIFICATION:")
        print(f"{'='*60}")
        print(f"  ID: {latest.id}")
        print(f"  OTP: {latest.otp}")
        print(f"  Attempts: {latest.attempts}/5")
        print(f"  Expired: {latest.is_expired()}")
        print(f"  Can Retry: {latest.can_retry()}")
        print()
        
        if latest.is_expired():
            print("⚠️  This OTP has EXPIRED. User needs to request a new one.")
        elif not latest.can_retry():
            print("⚠️  Maximum attempts reached. User needs to request a new OTP.")
        else:
            print(f"✅ This OTP is VALID. User should enter: {latest.otp}")
            print(f"   Remaining attempts: {5 - latest.attempts}")
    else:
        print("❌ No active verification found. All records are either verified or expired.")
    
    # Check if user already exists
    print(f"\n{'='*60}")
    print(f"USER STATUS:")
    print(f"{'='*60}")
    
    if User.objects.filter(email=test_email).exists():
        user = User.objects.get(email=test_email)
        print(f"✅ User ALREADY EXISTS:")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Created: {user.created_at}")
        print(f"   Email Verified: {user.email_verified}")
    else:
        print(f"❌ User does NOT exist yet (waiting for email verification)")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    test_otp_flow()
