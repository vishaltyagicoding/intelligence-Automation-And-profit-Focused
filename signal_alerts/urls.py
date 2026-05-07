from django.urls import path
from .views import SignalAlertView

urlpatterns = [
    path('', SignalAlertView.as_view(), name='signal-alerts'),
]
