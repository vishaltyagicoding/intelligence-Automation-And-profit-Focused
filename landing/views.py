"""
Landing page views for SmartRisk FX
"""
from django.shortcuts import render
from django.views.decorators.cache import cache_page


@cache_page(60 * 15)  # Cache for 15 minutes
def landing_page(request):
    """
    Serve the SmartRisk FX marketing landing page at /join
    """
    return render(request, 'landing/index.html')
