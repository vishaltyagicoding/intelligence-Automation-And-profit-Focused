from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_reversal_zones, name='reversal-zones-list'),
    path('<str:symbol>/', views.get_reversal_zone_detail, name='reversal-zones-detail'),
]
