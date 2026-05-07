"""
Device Fingerprinting Utilities
================================
Utilities for device fingerprint validation and trial abuse prevention
"""
import logging
from django.utils import timezone
from .models import DeviceFingerprint, User

logger = logging.getLogger(__name__)

# Configuration
MAX_ACCOUNTS_PER_IP = 5  # Maximum accounts from same IP
MAX_ACCOUNTS_PER_DEVICE = 1  # Maximum accounts from same device (strict)


def check_device_trial_eligibility(device_id, ip_address, user_agent):
    """
    Check if a device is eligible for free trial
    
    Args:
        device_id (str): FingerprintJS visitorId
        ip_address (str): Client IP address
        user_agent (str): Browser user agent
    
    Returns:
        dict: {
            'trial_allowed': bool,
            'reason': str,
            'device_record': DeviceFingerprint or None
        }
    """
    
    # Handle missing device_id (incognito/privacy mode)
    if not device_id or device_id == 'unknown':
        logger.warning(f"⚠️  Missing device_id from IP {ip_address}")
        return {
            'trial_allowed': True,  # Allow but log for monitoring
            'reason': 'Device fingerprint unavailable (privacy mode)',
            'device_record': None,
            'warning': 'Unable to verify device uniqueness'
        }
    
    # Check if device already exists
    device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
    
    if device_record:
        # Device exists - this means someone already registered from this device
        # NO ONE ELSE gets a trial, regardless of trial_granted status
        logger.warning(f"❌ Device {device_id[:8]}... already used for registration (user: {device_record.user.email if device_record.user else 'unknown'})")
        return {
            'trial_allowed': False,
            'reason': f'Free trial already used on this device. Trial was activated on {device_record.first_seen.strftime("%B %d, %Y")}.',
            'device_record': device_record
        }
    
    # New device - check IP-based restrictions
    ip_account_count = User.objects.filter(registration_ip=ip_address).count()
    
    if ip_account_count >= MAX_ACCOUNTS_PER_IP:
        logger.warning(f"⚠️  IP {ip_address} has {ip_account_count} accounts (limit: {MAX_ACCOUNTS_PER_IP})")
        # Still allow but flag for review
        return {
            'trial_allowed': True,
            'reason': 'New device from IP with multiple accounts',
            'device_record': None,
            'warning': f'This IP address has {ip_account_count} registered accounts'
        }
    
    # New device, eligible for trial
    logger.info(f"✅ New device {device_id[:8]}... eligible for trial")
    return {
        'trial_allowed': True,
        'reason': 'New device eligible for trial',
        'device_record': None
    }


def create_device_fingerprint(device_id, user, ip_address, user_agent, trial_granted=True):
    """
    Create or update device fingerprint record
    
    Args:
        device_id (str): FingerprintJS visitorId
        user (User): User instance
        ip_address (str): Client IP address
        user_agent (str): Browser user agent
        trial_granted (bool): Whether trial was granted
    
    Returns:
        DeviceFingerprint: Created or updated device record
    """
    
    if not device_id or device_id == 'unknown':
        logger.warning(f"⚠️  Cannot create device fingerprint without device_id for user {user.email}")
        return None
    
    # Check if device already exists
    device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
    
    if device_record:
        # Update existing record
        device_record.user = user
        device_record.ip_address = ip_address
        device_record.user_agent = user_agent
        device_record.trial_granted = trial_granted
        device_record.last_seen = timezone.now()
        device_record.save()
        
        logger.info(f"✅ Updated device fingerprint {device_id[:8]}... for user {user.email}")
    else:
        # Create new record
        device_record = DeviceFingerprint.objects.create(
            device_id=device_id,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            trial_granted=trial_granted,
            trial_count=1 if trial_granted else 0
        )
        
        logger.info(f"✅ Created device fingerprint {device_id[:8]}... for user {user.email}")
    
    return device_record


def get_device_info(device_id):
    """
    Get device information and usage statistics
    
    Args:
        device_id (str): FingerprintJS visitorId
    
    Returns:
        dict: Device information
    """
    
    if not device_id or device_id == 'unknown':
        return {
            'exists': False,
            'trial_used': False,
            'account_count': 0
        }
    
    device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
    
    if not device_record:
        return {
            'exists': False,
            'trial_used': False,
            'account_count': 0
        }
    
    # Count accounts from this device
    account_count = User.objects.filter(device_id=device_id).count()
    
    return {
        'exists': True,
        'trial_used': device_record.trial_granted,
        'trial_count': device_record.trial_count,
        'account_count': account_count,
        'first_seen': device_record.first_seen,
        'last_seen': device_record.last_seen,
        'is_blocked': device_record.is_blocked,
        'block_reason': device_record.block_reason
    }


def block_device(device_id, reason):
    """
    Block a device from creating new accounts
    
    Args:
        device_id (str): FingerprintJS visitorId
        reason (str): Reason for blocking
    
    Returns:
        bool: Success status
    """
    
    if not device_id or device_id == 'unknown':
        return False
    
    device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
    
    if device_record:
        device_record.is_blocked = True
        device_record.block_reason = reason
        device_record.save(update_fields=['is_blocked', 'block_reason'])
        
        logger.warning(f"🚫 Blocked device {device_id[:8]}... - Reason: {reason}")
        return True
    
    return False


def detect_suspicious_activity(device_id, ip_address):
    """
    Detect suspicious registration patterns
    
    Args:
        device_id (str): FingerprintJS visitorId
        ip_address (str): Client IP address
    
    Returns:
        dict: {
            'is_suspicious': bool,
            'reasons': list of str,
            'risk_score': int (0-100)
        }
    """
    
    reasons = []
    risk_score = 0
    
    # Check device-based patterns
    if device_id and device_id != 'unknown':
        device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
        
        if device_record:
            # Multiple trial attempts
            if device_record.trial_count > 3:
                reasons.append(f'Multiple trial attempts from this device ({device_record.trial_count})')
                risk_score += 40
            
            # Rapid account creation
            recent_users = User.objects.filter(
                device_id=device_id,
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            if recent_users > 2:
                reasons.append(f'{recent_users} accounts created in last 24 hours')
                risk_score += 30
    
    # Check IP-based patterns
    ip_users = User.objects.filter(registration_ip=ip_address)
    ip_count = ip_users.count()
    
    if ip_count > MAX_ACCOUNTS_PER_IP:
        reasons.append(f'{ip_count} accounts from this IP address')
        risk_score += 20
    
    # Check for rapid registrations from same IP
    recent_ip_users = ip_users.filter(
        created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    
    if recent_ip_users > 2:
        reasons.append(f'{recent_ip_users} accounts from this IP in last hour')
        risk_score += 30
    
    is_suspicious = risk_score >= 50
    
    if is_suspicious:
        logger.warning(f"⚠️  Suspicious activity detected - Device: {device_id[:8] if device_id else 'unknown'}..., IP: {ip_address}, Risk: {risk_score}")
    
    return {
        'is_suspicious': is_suspicious,
        'reasons': reasons,
        'risk_score': risk_score
    }
