from django.shortcuts import render
from django.conf import settings


def api_documentation(request):
    """
    API Documentation Homepage
    Displays all available endpoints with examples
    """
    
    # Base URL for API
    base_url = request.build_absolute_uri('/api/')
    
    context = {
        'base_url': base_url,
        'host': request.get_host(),
    }
    
    return render(request, 'api_docs/index.html', context)
