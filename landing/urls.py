"""
URL configuration for landing page
"""
from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('join/', views.landing_page, name='join'),
]
