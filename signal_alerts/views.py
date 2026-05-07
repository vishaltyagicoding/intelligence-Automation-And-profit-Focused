from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import SignalAlert
import logging

logger = logging.getLogger(__name__)


class SignalAlertView(APIView):
    """
    API endpoint to create/update signal alerts for paid subscribers
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create or update a signal alert
        Only available for paid subscribers (not trial users)
        """
        user = request.user
        
        # Check if user has paid subscription (manual_subscription = 'activated')
        if not hasattr(user, 'manual_subscription') or user.manual_subscription != 'activated':
            return Response(
                {'error': 'Signal alerts are only available for paid subscribers'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get data from request
        crypto = request.data.get('crypto')
        timeframe = request.data.get('timeframe')
        email = request.data.get('email', user.email)
        
        # Validate required fields
        if not crypto or not timeframe:
            return Response(
                {'error': 'Crypto and timeframe are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate crypto choice
        valid_cryptos = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XAUUSD']
        if crypto not in valid_cryptos:
            return Response(
                {'error': f'Invalid crypto. Must be one of: {", ".join(valid_cryptos)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate timeframe choice
        valid_timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '1d']
        if timeframe not in valid_timeframes:
            return Response(
                {'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create or update signal alert
            alert, created = SignalAlert.objects.update_or_create(
                user=user,
                crypto=crypto,
                timeframe=timeframe,
                defaults={
                    'email': email,
                    'is_active': True
                }
            )
            
            logger.info(
                f"Signal alert {'created' if created else 'updated'} for user {user.username}: "
                f"{crypto} {timeframe} -> {email}"
            )
            
            return Response({
                'success': True,
                'message': f'Signal alert {"activated" if created else "updated"} successfully',
                'alert': {
                    'crypto': alert.crypto,
                    'timeframe': alert.timeframe,
                    'email': alert.email,
                    'is_active': alert.is_active,
                }
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating signal alert for {user.username}: {e}")
            return Response(
                {'error': 'Failed to create signal alert'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Get all active signal alerts for the authenticated user
        """
        user = request.user
        alerts = SignalAlert.objects.filter(user=user, is_active=True)
        
        alert_data = [{
            'id': alert.id,
            'crypto': alert.crypto,
            'timeframe': alert.timeframe,
            'email': alert.email,
            'created_at': alert.created_at,
        } for alert in alerts]
        
        return Response({
            'alerts': alert_data,
            'count': len(alert_data)
        })
    
    def delete(self, request):
        """
        Deactivate a signal alert
        """
        user = request.user
        alert_id = request.data.get('alert_id')
        
        if not alert_id:
            return Response(
                {'error': 'alert_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            alert = SignalAlert.objects.get(id=alert_id, user=user)
            alert.is_active = False
            alert.save()
            
            logger.info(f"Signal alert deactivated for user {user.username}: {alert.crypto} {alert.timeframe}")
            
            return Response({
                'success': True,
                'message': 'Signal alert deactivated successfully'
            })
        except SignalAlert.DoesNotExist:
            return Response(
                {'error': 'Signal alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )