"""
User Authentication Views
=========================
JWT-based authentication with 3-day persistent login
Email verification with OTP before user creation
"""
import logging
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer
)
from .models import UserSession, EmailVerification, PasswordReset, DeviceFingerprint
from .email_utils import send_otp_email, send_welcome_email, send_password_reset_email
from .device_utils import (
    check_device_trial_eligibility,
    create_device_fingerprint,
    detect_suspicious_activity
)
from payments.models import Subscription

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with 3-day token expiry"""
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Step 1: Send OTP to email for verification
    User is NOT created until email is verified
    
    POST /api/users/register/
    Body: {
        "email": "user@example.com",
        "username": "username",
        "password": "password123",
        "password2": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "device_id": "FingerprintJS_visitorId"  # REQUIRED for trial validation
    }
    """
    from django.db import transaction
    
    try:
        # Get device fingerprint
        device_id = request.data.get('device_id', '').strip()
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Validate device fingerprint
        if not device_id:
            logger.warning(f"❌ Registration attempt without device_id from IP {ip_address}")
            return Response({
                'success': False,
                'error': 'Device verification required. Please enable JavaScript and try again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check device trial eligibility
        eligibility = check_device_trial_eligibility(device_id, ip_address, user_agent)
        
        # Detect suspicious activity
        suspicious = detect_suspicious_activity(device_id, ip_address)
        
        if suspicious['is_suspicious'] and suspicious['risk_score'] >= 80:
            logger.error(f"🚫 Blocked suspicious registration - Device: {device_id[:8]}..., IP: {ip_address}, Risk: {suspicious['risk_score']}")
            return Response({
                'success': False,
                'error': 'Registration blocked due to suspicious activity. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate input
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"❌ Registration validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'errors': {'email': ['A user with this email already exists.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'errors': {'username': ['A user with this username already exists.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete any existing unverified verification for this email
        EmailVerification.objects.filter(email=email, is_verified=False).delete()
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Create email verification record (user NOT created yet)
        with transaction.atomic():
            verification = EmailVerification.objects.create(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password_hash=make_password(password),  # Store hashed password
                device_id=device_id,  # Store device fingerprint
                otp=otp,
                expires_at=timezone.now() + timedelta(minutes=10),
                ip_address=ip_address
            )
            
            # Log OTP for debugging (remove in production)
            logger.info(f"🔑 Generated OTP for {email}: {otp} (ID: {verification.id})")
            logger.info(f"🔍 Device: {device_id[:8]}..., Trial Allowed: {eligibility['trial_allowed']}")
        
        # Send OTP email
        email_sent = send_otp_email(email, otp, username)
        
        if not email_sent:
            # Delete the verification record if email fails
            verification.delete()
            return Response({
                'success': False,
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"✅ OTP email sent successfully to {email}")
        
        # Prepare response with trial eligibility info
        response_data = {
            'success': True,
            'message': 'Verification code sent to your email. Please check your inbox.',
            'verification_id': str(verification.id),
            'email': email,
            'trial_info': {
                'trial_allowed': eligibility['trial_allowed'],
                'reason': eligibility['reason']
            }
        }
        
        # Add warning if suspicious but not blocked
        if suspicious['is_suspicious']:
            response_data['warning'] = 'Your registration is being reviewed for security.'
        
        # Add warning if trial not allowed
        if not eligibility['trial_allowed']:
            response_data['trial_info']['message'] = 'You can still create an account, but the free trial is not available on this device.'
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Step 2: Verify OTP and create user account
    
    POST /api/users/verify-otp/
    Body: {
        "verification_id": "uuid",
        "otp": "123456"
    }
    """
    from django.db import transaction
    
    try:
        verification_id = request.data.get('verification_id')
        otp = request.data.get('otp')
        
        if not verification_id or not otp:
            return Response({
                'success': False,
                'error': 'Verification ID and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get verification record
        try:
            verification = EmailVerification.objects.get(
                id=verification_id,
                is_verified=False
            )
        except EmailVerification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid verification ID or already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if expired
        if verification.is_expired():
            return Response({
                'success': False,
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check attempts
        if not verification.can_retry():
            return Response({
                'success': False,
                'error': 'Too many failed attempts. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        if verification.otp != otp:
            verification.attempts += 1
            verification.save(update_fields=['attempts'])
            
            remaining = 5 - verification.attempts
            logger.warning(f"❌ Invalid OTP attempt for {verification.email}. Expected: {verification.otp}, Got: {otp}, Attempts: {verification.attempts}/5")
            return Response({
                'success': False,
                'error': f'Invalid OTP. {remaining} attempts remaining.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP is correct - Create user account
        with transaction.atomic():
            # Double-check user doesn't exist
            if User.objects.filter(email=verification.email).exists():
                return Response({
                    'success': False,
                    'error': 'User already exists with this email'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get device info
            device_id = verification.device_id or 'unknown'
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # Re-check trial eligibility at user creation time
            eligibility = check_device_trial_eligibility(device_id, ip_address, user_agent)
            trial_allowed = eligibility['trial_allowed']
            
            # Create user
            user = User.objects.create(
                email=verification.email,
                username=verification.username,
                first_name=verification.first_name,
                last_name=verification.last_name,
                password=verification.password_hash,  # Already hashed
                is_active=True,
                email_verified=True,
                # Device fingerprinting fields
                device_id=device_id,
                registration_ip=ip_address,
                registration_user_agent=user_agent,
                trial_used=False,  # Will be set to True when trial is activated
                trial_allowed=trial_allowed  # Whether this user can get trial
            )
            
            # Create or update device fingerprint record
            if device_id != 'unknown':
                # For the FIRST user on this device, grant trial
                # For subsequent users, deny trial
                device_record = DeviceFingerprint.objects.filter(device_id=device_id).first()
                
                if device_record:
                    # Device already exists - this is NOT the first user
                    # Update the device record with new user
                    device_record.user = user
                    device_record.ip_address = ip_address
                    device_record.user_agent = user_agent
                    device_record.last_seen = timezone.now()
                    device_record.trial_count += 1
                    device_record.save()
                    
                    logger.info(f"✅ Updated existing device {device_id[:8]}... for user {user.email}, Trial: {device_record.trial_granted}")
                else:
                    # New device - this IS the first user - GRANT TRIAL
                    device_record = DeviceFingerprint.objects.create(
                        device_id=device_id,
                        user=user,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        trial_granted=True,  # FIRST user gets trial
                        trial_count=1
                    )
                    
                    logger.info(f"✅ Created NEW device {device_id[:8]}... for user {user.email}, Trial GRANTED")
            
            # Subscription will be created automatically by signal based on trial_allowed
            
            # Mark verification as complete
            verification.is_verified = True
            verification.verified_at = timezone.now()
            verification.save(update_fields=['is_verified', 'verified_at'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Create session
            create_user_session(
                user=user,
                token=str(refresh.access_token),
                request=request
            )
            
            # Send welcome email (async, don't wait)
            try:
                send_welcome_email(user.email, user.username)
            except:
                pass  # Don't fail if welcome email fails
            
            logger.info(f"✅ User created and verified: {user.email}, Trial Allowed: {trial_allowed}")
            
            # Prepare success message
            if trial_allowed:
                message = '🎉 Welcome to SmartRisk! You have 3 days of FREE access!'
            else:
                message = f'✅ Account created successfully! Note: {eligibility["reason"]}'
            
            return Response({
                'success': True,
                'message': message,
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'trial_info': {
                    'trial_allowed': trial_allowed,
                    'reason': eligibility['reason']
                }
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"❌ OTP verification failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    Resend OTP to email
    
    POST /api/users/resend-otp/
    Body: {
        "verification_id": "uuid"
    }
    """
    try:
        verification_id = request.data.get('verification_id')
        
        if not verification_id:
            return Response({
                'success': False,
                'error': 'Verification ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get verification record
        try:
            verification = EmailVerification.objects.get(
                id=verification_id,
                is_verified=False
            )
        except EmailVerification.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid verification ID or already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Update verification record
        verification.otp = otp
        verification.attempts = 0  # Reset attempts
        verification.expires_at = timezone.now() + timedelta(minutes=10)
        verification.save(update_fields=['otp', 'attempts', 'expires_at'])
        
        # Send OTP email
        email_sent = send_otp_email(verification.email, otp, verification.username)
        
        if not email_sent:
            return Response({
                'success': False,
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"✅ OTP resent to {verification.email}")
        
        return Response({
            'success': True,
            'message': 'New verification code sent to your email'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Resend OTP failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User login with 3-day persistent session
    
    POST /api/users/login/
    Body: {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.check_password(password):
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'error': 'Account is disabled'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens with 3-day expiry
        refresh = RefreshToken.for_user(user)
        refresh.set_exp(lifetime=timedelta(days=3))
        
        # Create session
        create_user_session(
            user=user,
            token=str(refresh.access_token),
            request=request
        )
        
        # Update last login
        user.last_login = timezone.now()
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        logger.info(f"✅ User logged in: {user.email}")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    User logout - invalidate session
    
    POST /api/users/logout/
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Deactivate session
            UserSession.objects.filter(
                user=request.user,
                token=token
            ).update(is_active=False)
        
        logger.info(f"✅ User logged out: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        })
        
    except Exception as e:
        logger.error(f"❌ Logout failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get user profile
    
    GET /api/users/profile/
    """
    try:
        user = request.user
        return Response({
            'success': True,
            'user': UserSerializer(user).data
        })
    except Exception as e:
        logger.error(f"❌ Failed to get profile: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile
    
    PUT/PATCH /api/users/profile/
    Body: {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "bio": "Crypto trader"
    }
    """
    try:
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"❌ Profile update failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    
    POST /api/users/change-password/
    Body: {
        "old_password": "oldpass123",
        "new_password": "newpass123",
        "new_password2": "newpass123"
    }
    """
    try:
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response({
                    'success': False,
                    'error': 'Old password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            # Invalidate all sessions
            UserSession.objects.filter(user=user).update(is_active=False)
            
            logger.info(f"✅ Password changed: {user.email}")
            
            return Response({
                'success': True,
                'message': 'Password changed successfully. Please login again.'
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"❌ Password change failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    """
    Check if user is authenticated
    
    GET /api/users/check-auth/
    """
    return Response({
        'success': True,
        'authenticated': True,
        'user': UserSerializer(request.user).data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_device_eligibility(request):
    """
    Check if a device is eligible for free trial
    
    POST /api/users/check-device/
    Body: {
        "device_id": "FingerprintJS_visitorId"
    }
    """
    try:
        device_id = request.data.get('device_id', '').strip()
        
        if not device_id:
            return Response({
                'success': False,
                'error': 'Device ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Check eligibility
        eligibility = check_device_trial_eligibility(device_id, ip_address, user_agent)
        
        # Detect suspicious activity
        suspicious = detect_suspicious_activity(device_id, ip_address)
        
        return Response({
            'success': True,
            'trial_allowed': eligibility['trial_allowed'],
            'reason': eligibility['reason'],
            'suspicious': suspicious['is_suspicious'],
            'risk_score': suspicious['risk_score']
        })
        
    except Exception as e:
        logger.error(f"❌ Device check failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper functions
def create_user_session(user, token, request):
    """Create user session record"""
    UserSession.objects.create(
        user=user,
        token=token,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        expires_at=timezone.now() + timedelta(days=3)
    )


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Step 1: Send OTP to email for password reset
    
    POST /api/users/forgot-password/
    Body: {
        "email": "user@example.com"
    }
    """
    try:
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security)
            return Response({
                'success': True,
                'message': 'If this email is registered, you will receive a password reset code.'
            }, status=status.HTTP_200_OK)
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Delete any existing unused reset for this user
        PasswordReset.objects.filter(user=user, is_used=False).delete()
        
        # Create password reset record
        reset = PasswordReset.objects.create(
            user=user,
            email=email,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address=get_client_ip(request)
        )
        
        # Send OTP email
        email_sent = send_password_reset_email(email, otp, user.username)
        
        if not email_sent:
            return Response({
                'success': False,
                'error': 'Failed to send reset email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"✅ Password reset OTP sent to {email}")
        
        return Response({
            'success': True,
            'message': 'Password reset code sent to your email.',
            'reset_id': str(reset.id),
            'email': email
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Forgot password failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_otp(request):
    """
    Step 2: Verify OTP for password reset
    
    POST /api/users/verify-reset-otp/
    Body: {
        "reset_id": "uuid",
        "otp": "123456"
    }
    """
    try:
        reset_id = request.data.get('reset_id')
        otp = request.data.get('otp')
        
        if not reset_id or not otp:
            return Response({
                'success': False,
                'error': 'Reset ID and OTP are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get reset record
        try:
            reset = PasswordReset.objects.get(
                id=reset_id,
                is_used=False
            )
        except PasswordReset.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid reset ID or already used'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if expired
        if reset.is_expired():
            return Response({
                'success': False,
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check attempts
        if not reset.can_retry():
            return Response({
                'success': False,
                'error': 'Too many failed attempts. Please request a new OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP
        if reset.otp != otp:
            reset.attempts += 1
            reset.save(update_fields=['attempts'])
            
            remaining = 5 - reset.attempts
            return Response({
                'success': False,
                'error': f'Invalid OTP. {remaining} attempts remaining.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP is correct
        logger.info(f"✅ Password reset OTP verified for {reset.email}")
        
        return Response({
            'success': True,
            'message': 'OTP verified. You can now reset your password.',
            'reset_id': str(reset.id)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Verify reset OTP failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Step 3: Reset password with verified OTP
    
    POST /api/users/reset-password/
    Body: {
        "reset_id": "uuid",
        "otp": "123456",
        "new_password": "newpass123",
        "new_password2": "newpass123"
    }
    """
    from django.db import transaction
    
    try:
        reset_id = request.data.get('reset_id')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        new_password2 = request.data.get('new_password2')
        
        if not all([reset_id, otp, new_password, new_password2]):
            return Response({
                'success': False,
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate passwords match
        if new_password != new_password2:
            return Response({
                'success': False,
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(new_password) < 8:
            return Response({
                'success': False,
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get reset record
        try:
            reset = PasswordReset.objects.get(
                id=reset_id,
                is_used=False
            )
        except PasswordReset.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid reset ID or already used'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if expired
        if reset.is_expired():
            return Response({
                'success': False,
                'error': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify OTP one more time
        if reset.otp != otp:
            return Response({
                'success': False,
                'error': 'Invalid OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Reset password
        with transaction.atomic():
            user = reset.user
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Mark reset as used
            reset.is_used = True
            reset.used_at = timezone.now()
            reset.save(update_fields=['is_used', 'used_at'])
            
            # Invalidate all existing sessions for security
            UserSession.objects.filter(user=user).update(is_active=False)
            
            logger.info(f"✅ Password reset successful for {user.email}")
            
            return Response({
                'success': True,
                'message': 'Password reset successful! Please login with your new password.'
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Reset password failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_reset_otp(request):
    """
    Resend password reset OTP
    
    POST /api/users/resend-reset-otp/
    Body: {
        "reset_id": "uuid"
    }
    """
    try:
        reset_id = request.data.get('reset_id')
        
        if not reset_id:
            return Response({
                'success': False,
                'error': 'Reset ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get reset record
        try:
            reset = PasswordReset.objects.get(
                id=reset_id,
                is_used=False
            )
        except PasswordReset.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid reset ID or already used'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Update reset record
        reset.otp = otp
        reset.attempts = 0  # Reset attempts
        reset.expires_at = timezone.now() + timedelta(minutes=10)
        reset.save(update_fields=['otp', 'attempts', 'expires_at'])
        
        # Send OTP email
        email_sent = send_password_reset_email(reset.email, otp, reset.user.username)
        
        if not email_sent:
            return Response({
                'success': False,
                'error': 'Failed to send reset email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f"✅ Password reset OTP resent to {reset.email}")
        
        return Response({
            'success': True,
            'message': 'New password reset code sent to your email'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Resend reset OTP failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
