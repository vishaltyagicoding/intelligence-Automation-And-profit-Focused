"""
Security API views.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import qrcode
from io import BytesIO
import base64

from .models import TwoFactorAuth, LoginAttempt


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_2fa(request):
    """
    Setup 2FA for user.
    """
    try:
        user = request.user
        
        # Get or create 2FA
        two_factor, created = TwoFactorAuth.objects.get_or_create(user=user)
        
        if not created and two_factor.is_enabled:
            return Response(
                {'error': '2FA already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new secret
        secret = two_factor.generate_secret()
        
        # Generate QR code
        totp_uri = two_factor.get_totp_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_code_base64}',
            'message': 'Scan QR code with authenticator app'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa(request):
    """
    Verify and enable 2FA.
    """
    try:
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        two_factor = TwoFactorAuth.objects.get(user=user)
        
        if two_factor.verify_token(token):
            two_factor.is_enabled = True
            two_factor.save()
            
            return Response({
                'message': '2FA enabled successfully'
            })
        else:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except TwoFactorAuth.DoesNotExist:
        return Response(
            {'error': '2FA not setup'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """
    Disable 2FA.
    """
    try:
        user = request.user
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token required for verification'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        two_factor = TwoFactorAuth.objects.get(user=user)
        
        if two_factor.verify_token(token):
            two_factor.is_enabled = False
            two_factor.save()
            
            return Response({
                'message': '2FA disabled successfully'
            })
        else:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except TwoFactorAuth.DoesNotExist:
        return Response(
            {'error': '2FA not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
