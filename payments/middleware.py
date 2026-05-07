"""
Subscription Middleware
=======================
Protects Dashboard and History pages - requires active subscription
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from rest_framework import status
from .models import Subscription


class SubscriptionMiddleware:
    """
    Middleware to check subscription status
    Protects Dashboard and History pages
    """
    
    # Paths that require active subscription
    PROTECTED_PATHS = ['/dashboard', '/history', '/asset/']
    
    # Paths that don't require authentication
    PUBLIC_PATHS = ['/', '/login', '/register', '/about', '/learn', '/trial-ended', '/api/']
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for public paths
        if any(request.path.startswith(path) for path in self.PUBLIC_PATHS):
            return self.get_response(request)
        
        # Skip for protected paths check
        if not any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False,
                    'error': 'Authentication required',
                    'redirect': '/login'
                }, status=401)
            return redirect(f"/login?next={request.path}")
        
        # Check subscription status
        # User has access if:
        # 1. trial_status='active' (during 3-day trial) OR
        # 2. manual_subscription='activated' (paid subscription) OR
        # 3. Subscription.is_active() returns True
        
        # Check trial status first
        if hasattr(request.user, 'trial_status') and request.user.trial_status == 'active':
            # User is on active trial - allow access
            return self.get_response(request)
        
        # Check manual subscription
        if hasattr(request.user, 'manual_subscription') and request.user.manual_subscription == 'activated':
            # User has paid subscription - allow access
            return self.get_response(request)
        
        # Check Subscription model as fallback
        try:
            subscription = Subscription.objects.get(user=request.user)
            
            if subscription.is_active():
                # Subscription is active - allow access
                return self.get_response(request)
            else:
                # Subscription expired or not active - redirect to subscription page
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'success': False,
                        'error': 'Access denied. Active subscription required.',
                        'redirect': '/subscription'
                    }, status=status.HTTP_403_FORBIDDEN)
                return redirect('/subscription')
                
        except Subscription.DoesNotExist:
            # No subscription exists - redirect to subscription page
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied. Active subscription required.',
                    'redirect': '/subscription'
                }, status=status.HTTP_403_FORBIDDEN)
            return redirect('/subscription')
        
        return self.get_response(request)
