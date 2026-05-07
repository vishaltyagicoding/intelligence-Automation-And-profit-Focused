"""
Razorpay Service Layer
======================
Handles all Razorpay API interactions
"""
import hmac
import hashlib
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)

# Try to import razorpay, handle gracefully if not available
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Razorpay not available: {e}. Payment features will be disabled.")
    RAZORPAY_AVAILABLE = False
    razorpay = None


class RazorpayService:
    """
    Razorpay API service
    Handles order creation, payment verification, and subscriptions
    """
    
    def __init__(self):
        """Initialize Razorpay client"""
        if not RAZORPAY_AVAILABLE:
            logger.error("❌ Razorpay SDK not available. Install with: pip install razorpay")
            self.client = None
            self.key_id = None
            return
            
        try:
            self.client = razorpay.Client(auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            ))
            self.key_id = settings.RAZORPAY_KEY_ID
        except Exception as e:
            logger.error(f"❌ Failed to initialize Razorpay client: {e}")
            self.client = None
            self.key_id = None
    
    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """
        Create Razorpay order
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            receipt: Receipt ID for reference
            notes: Additional notes (dict)
        
        Returns:
            dict: Order details from Razorpay
        """
        if not self.client:
            raise Exception("Razorpay client not initialized. Check if razorpay package is installed.")
            
        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(Decimal(str(amount)) * 100)
            
            order_data = {
                'amount': amount_paise,
                'currency': currency,
                'payment_capture': 1,  # Auto capture payment
            }
            
            if receipt:
                order_data['receipt'] = receipt
            
            if notes:
                order_data['notes'] = notes
            
            order = self.client.order.create(data=order_data)
            logger.info(f"✅ Razorpay order created: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"❌ Razorpay order creation failed: {e}")
            raise
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
        
        Returns:
            bool: True if signature is valid
        """
        try:
            # Generate expected signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
            
            if is_valid:
                logger.info(f"✅ Payment signature verified: {razorpay_payment_id}")
            else:
                logger.warning(f"⚠️ Invalid payment signature: {razorpay_payment_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Signature verification failed: {e}")
            return False
    
    def fetch_payment(self, payment_id):
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
        
        Returns:
            dict: Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"❌ Failed to fetch payment {payment_id}: {e}")
            raise
    
    def capture_payment(self, payment_id, amount):
        """
        Manually capture payment (if auto-capture is disabled)
        
        Args:
            payment_id: Razorpay payment ID
            amount: Amount to capture in paise
        
        Returns:
            dict: Captured payment details
        """
        try:
            payment = self.client.payment.capture(payment_id, amount)
            logger.info(f"✅ Payment captured: {payment_id}")
            return payment
        except Exception as e:
            logger.error(f"❌ Payment capture failed: {e}")
            raise
    
    def create_subscription(self, plan_id, customer_id, total_count=None, notes=None):
        """
        Create Razorpay subscription for auto-renewal
        
        Args:
            plan_id: Razorpay plan ID
            customer_id: Razorpay customer ID
            total_count: Number of billing cycles (None = infinite)
            notes: Additional notes
        
        Returns:
            dict: Subscription details
        """
        try:
            subscription_data = {
                'plan_id': plan_id,
                'customer_id': customer_id,
                'total_count': total_count or 0,  # 0 = infinite
                'customer_notify': 1,
            }
            
            if notes:
                subscription_data['notes'] = notes
            
            subscription = self.client.subscription.create(data=subscription_data)
            logger.info(f"✅ Subscription created: {subscription['id']}")
            return subscription
            
        except Exception as e:
            logger.error(f"❌ Subscription creation failed: {e}")
            raise
    
    def cancel_subscription(self, subscription_id, cancel_at_cycle_end=False):
        """
        Cancel Razorpay subscription
        
        Args:
            subscription_id: Razorpay subscription ID
            cancel_at_cycle_end: Cancel at end of current cycle
        
        Returns:
            dict: Cancelled subscription details
        """
        try:
            subscription = self.client.subscription.cancel(
                subscription_id,
                cancel_at_cycle_end=cancel_at_cycle_end
            )
            logger.info(f"✅ Subscription cancelled: {subscription_id}")
            return subscription
        except Exception as e:
            logger.error(f"❌ Subscription cancellation failed: {e}")
            raise
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature from Razorpay
        
        Args:
            payload: Webhook payload (bytes)
            signature: X-Razorpay-Signature header
        
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                logger.info("✅ Webhook signature verified")
            else:
                logger.warning("⚠️ Invalid webhook signature")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Webhook signature verification failed: {e}")
            return False


# Singleton instance
razorpay_service = RazorpayService()
