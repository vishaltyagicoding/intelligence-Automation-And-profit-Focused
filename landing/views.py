"""
Landing page views for SmartRisk FX
"""
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from pathlib import Path
import re


@cache_page(60 * 15)  # Cache for 15 minutes
def landing_page(request):
    """
    Serve the SmartRisk FX marketing landing page at /join
    """
    # Serve the HTML file directly from smartriskfx-landing folder
    html_file = Path(__file__).resolve().parent.parent / 'smartriskfx-landing' / 'index.html'
    
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace all asset paths with /static-landing/ paths
        # Handle both href and src attributes
        html_content = re.sub(r'href="assets/', 'href="/static-landing/', html_content)
        html_content = re.sub(r'src="assets/', 'src="/static-landing/', html_content)
        html_content = re.sub(r'src="videos/', 'src="/static-landing/videos/', html_content)
        html_content = re.sub(r'href="videos/', 'href="/static-landing/videos/', html_content)
        
        # Also handle any {% static %} tags if present
        html_content = re.sub(
            r'{%\s*static\s*[\'"]landing/smartriskfx-landing/assets/([^\'"]+)[\'"]\s*%}',
            r'/static-landing/\1',
            html_content
        )
        
        return HttpResponse(html_content, content_type='text/html')
    else:
        return HttpResponse('<h1>Landing page not found</h1>', status=404)
