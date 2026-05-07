from rest_framework import serializers
from .models import Payment, Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'trial_start', 'trial_end',
            'trial_used', 'start_date', 'end_date', 'auto_renew',
            'is_active', 'days_remaining', 'created_at'
        ]
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_days_remaining(self, obj):
        return obj.days_remaining()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'razorpay_order_id',
            'razorpay_payment_id', 'payment_type', 'status',
            'payment_method', 'created_at', 'paid_at'
        ]
