"""
Payment API Views
=================
REST API endpoints for payment processing
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Payment, Subscription
from .services import razorpay_service
from .serializers import PaymentSerializer, SubscriptionSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create Razorpay order for payment
    
    POST /api/payments/create-order/
    Body: {
        "plan": "monthly" | "yearly",
        "amount": 499  # Optional, will use plan default
    }
    """
    try:
        user = request.user
        plan = request.data.get('plan', 'monthly')
        
        # Get or create subscription
        subscription, created = Subscription.objects.get_or_create(user=user)
        
        # Determine amount based on plan
        if plan == 'monthly':
            amount = Decimal('499.00')  # ₹499/month
        elif plan == 'yearly':
            amount = Decimal('4999.00')  # ₹4999/year (save ₹989)
        else:
            return Response({
                'success': False,
                'error': 'Invalid plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Allow custom amount if provided
        if 'amount' in request.data:
            amount = Decimal(str(request.data['amount']))
        
        # Create Razorpay order
        order = razorpay_service.create_order(
            amount=amount,
            receipt=f"sub_{subscription.id}",
            notes={
                'user_id': str(user.id),
                'email': user.email,
                'plan': plan,
            }
        )
        
        # Create payment record
        payment = Payment.objects.create(
            user=user,
            subscription=subscription,
            amount=amount,
            razorpay_order_id=order['id'],
            payment_type='subscription' if not subscription.trial_used else 'renewal',
            notes={
                'plan': plan,
                'order_details': order,
            }
        )
        
        logger.info(f"✅ Order created for {user.email}: {order['id']}")
        
        return Response({
            'success': True,
            'order_id': order['id'],
            'amount': float(amount),
            'currency': 'INR',
            'key_id': razorpay_service.key_id,
            'payment_id': str(payment.id),
            'user': {
                'name': user.get_full_name() or user.email,
                'email': user.email,
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Order creation failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verify_payment(request):
    """
    Verify payment and activate subscription
    
    POST /api/payments/verify/
    Body: {
        "razorpay_order_id": "order_xxx",
        "razorpay_payment_id": "pay_xxx",
        "razorpay_signature": "signature_xxx"
    }
    """
    try:
        user = request.user
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({
                'success': False,
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payment record
        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                user=user
            )
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify signature
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        if not is_valid:
            payment.mark_failed('Invalid signature')
            return Response({
                'success': False,
                'error': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch payment details from Razorpay
        payment_details = razorpay_service.fetch_payment(razorpay_payment_id)
        
        # Mark payment as successful
        payment.mark_success(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            payment_method=payment_details.get('method')
        )
        
        # Activate/upgrade subscription
        subscription = payment.subscription
        plan = payment.notes.get('plan', 'monthly')
        subscription.upgrade_to_paid(plan=plan)
        
        logger.info(f"✅ Payment verified for {user.email}: {razorpay_payment_id}")
        
        return Response({
            'success': True,
            'message': 'Payment successful! Your subscription is now active.',
            'subscription': SubscriptionSerializer(subscription).data,
            'payment': PaymentSerializer(payment).data,
        })
        
    except Exception as e:
        logger.error(f"❌ Payment verification failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    Get current subscription status
    
    GET /api/payments/subscription/
    """
    try:
        user = request.user
        
        try:
            subscription = Subscription.objects.get(user=user)
        except Subscription.DoesNotExist:
            # Create trial subscription if doesn't exist
            subscription = Subscription.objects.create(user=user)
            subscription.activate_trial()
        
        return Response({
            'success': True,
            'subscription': SubscriptionSerializer(subscription).data,
            'is_active': subscription.is_active(),
            'days_remaining': subscription.days_remaining(),
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get subscription status: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_trial(request):
    """
    Activate 3-day free trial
    
    POST /api/payments/activate-trial/
    """
    try:
        user = request.user
        
        subscription, created = Subscription.objects.get_or_create(user=user)
        
        if subscription.trial_used:
            return Response({
                'success': False,
                'error': 'Trial already used'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.activate_trial()
        
        logger.info(f"✅ Trial activated for {user.email}")
        
        return Response({
            'success': True,
            'message': '3-day free trial activated!',
            'subscription': SubscriptionSerializer(subscription).data,
        })
        
    except Exception as e:
        logger.error(f"❌ Trial activation failed: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """
    Get user's payment history
    
    GET /api/payments/history/
    """
    try:
        user = request.user
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        
        return Response({
            'success': True,
            'payments': PaymentSerializer(payments, many=True).data,
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get payment history: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
