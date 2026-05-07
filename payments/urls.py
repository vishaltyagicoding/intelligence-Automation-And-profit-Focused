from django.urls import path
from . import views, webhooks

urlpatterns = [
    # Payment APIs
    path('create-order/', views.create_order, name='create_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('subscription/', views.subscription_status, name='subscription_status'),
    path('activate-trial/', views.activate_trial, name='activate_trial'),
    path('history/', views.payment_history, name='payment_history'),
    
    # Webhook (public endpoint)
    path('webhook/', webhooks.razorpay_webhook, name='razorpay_webhook'),
]
