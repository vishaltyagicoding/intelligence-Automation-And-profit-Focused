"""
ASGI config for NeuralTrade project.
Exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import trading.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(
        trading.routing.websocket_urlpatterns
    ),
})
