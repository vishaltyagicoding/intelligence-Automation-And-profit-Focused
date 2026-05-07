"""
Razorpay Webhook Handler
=========================
Handles webhook events from Razorpay
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Payment, Subscription, WebhookLog
from .services import razorpay_service

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Handle Razorpay webhook events
    
    POST /api/payments/webhook/
    """
    try:
        # Get signature from header
        signature = request.headers.get('X-Razorpay-Signature')
        if not signature:
            logger.warning("⚠️ Webhook received without signature")
            return HttpResponse(status=400)
        
        # Verify signature
        is_valid = razorpay_service.verify_webhook_signature(
            request.body,
            signature
        )
        
        if not is_valid:
            logger.warning("⚠️ Invalid webhook signature")
            return HttpResponse(status=400)
        
        # Parse payload
        payload = json.loads(request.body)
        event_type = payload.get('event')
        
        # Log webhook
        webhook_log = WebhookLog.objects.create(
            event_type=event_type,
            payload=payload
        )
        
        logger.info(f"📨 Webhook received: {event_type}")
        
        # Handle different event types
        if event_type == 'payment.captured':
            handle_payment_captured(payload, webhook_log)
        
        elif event_type == 'payment.failed':
            handle_payment_failed(payload, webhook_log)
        
        elif event_type == 'subscription.charged':
            handle_subscription_charged(payload, webhook_log)
        
        elif event_type == 'subscription.cancelled':
            handle_subscription_cancelled(payload, webhook_log)
        
        else:
            logger.info(f"ℹ️ Unhandled event type: {event_type}")
        
        webhook_log.processed = True
        webhook_log.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}", exc_info=True)
        if 'webhook_log' in locals():
            webhook_log.error = str(e)
            webhook_log.save()
        return HttpResponse(status=500)


@transaction.atomic
def handle_payment_captured(payload, webhook_log):
    """Handle payment.captured event"""
    try:
        payment_entity = payload['payload']['payment']['entity']
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')
        
        if not order_id:
            logger.warning("⚠️ Payment captured without order_id")
            return
        
        # Find payment record
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
        except Payment.DoesNotExist:
            logger.warning(f"⚠️ Payment not found for order: {order_id}")
            return
        
        # Update payment status
        if payment.status != 'success':
            payment.mark_success(
                razorpay_payment_id=payment_id,
                razorpay_signature='webhook',  # Signature already verified
                payment_method=payment_entity.get('method')
            )
            
            # Activate subscription if not already active
            if payment.subscription and not payment.subscription.is_active():
                plan = payment.notes.get('plan', 'monthly')
                payment.subscription.upgrade_to_paid(plan=plan)
            
            logger.info(f"✅ Payment captured via webhook: {payment_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to handle payment.captured: {e}", exc_info=True)
        raise


@transaction.atomic
def handle_payment_failed(payload, webhook_log):
    """Handle payment.failed event"""
    try:
        payment_entity = payload['payload']['payment']['entity']
        order_id = payment_entity.get('order_id')
        error_description = payment_entity.get('error_description', 'Payment failed')
        
        if not order_id:
            return
        
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
            payment.mark_failed(error_description)
            logger.info(f"❌ Payment failed via webhook: {order_id}")
        except Payment.DoesNotExist:
            logger.warning(f"⚠️ Payment not found for order: {order_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to handle payment.failed: {e}", exc_info=True)
        raise


@transaction.atomic
def handle_subscription_charged(payload, webhook_log):
    """Handle subscription.charged event (auto-renewal)"""
    try:
        subscription_entity = payload['payload']['subscription']['entity']
        payment_entity = payload['payload']['payment']['entity']
        
        razorpay_subscription_id = subscription_entity.get('id')
        payment_id = payment_entity.get('id')
        
        # Find subscription
        try:
            subscription = Subscription.objects.get(
                razorpay_subscription_id=razorpay_subscription_id
            )
        except Subscription.DoesNotExist:
            logger.warning(f"⚠️ Subscription not found: {razorpay_subscription_id}")
            return
        
        # Create payment record for renewal
        amount = payment_entity.get('amount', 0) / 100  # Convert paise to rupees
        payment = Payment.objects.create(
            user=subscription.user,
            subscription=subscription,
            amount=amount,
            razorpay_order_id=payment_entity.get('order_id', f"auto_{payment_id}"),
            razorpay_payment_id=payment_id,
            payment_type='renewal',
            status='success',
            payment_method=payment_entity.get('method'),
        )
        
        # Extend subscription
        subscription.upgrade_to_paid(
            plan=subscription.plan,
            razorpay_subscription_id=razorpay_subscription_id
        )
        
        logger.info(f"✅ Subscription auto-renewed: {razorpay_subscription_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to handle subscription.charged: {e}", exc_info=True)
        raise


@transaction.atomic
def handle_subscription_cancelled(payload, webhook_log):
    """Handle subscription.cancelled event"""
    try:
        subscription_entity = payload['payload']['subscription']['entity']
        razorpay_subscription_id = subscription_entity.get('id')
        
        try:
            subscription = Subscription.objects.get(
                razorpay_subscription_id=razorpay_subscription_id
            )
            subscription.status = 'cancelled'
            subscription.auto_renew = False
            subscription.save()
            
            logger.info(f"✅ Subscription cancelled: {razorpay_subscription_id}")
        except Subscription.DoesNotExist:
            logger.warning(f"⚠️ Subscription not found: {razorpay_subscription_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to handle subscription.cancelled: {e}", exc_info=True)
        raise
