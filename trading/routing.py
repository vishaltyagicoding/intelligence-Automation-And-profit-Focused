"""
WebSocket URL routing for trading app.
"""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/live/$", consumers.LiveDataConsumer.as_asgi()),
    # Market data with optional timeframe (e.g. ws/market/BTCUSD/5m/)
    re_path(
        r"ws/market/(?P<symbol>[A-Z0-9]+)/(?P<timeframe>[a-zA-Z0-9]+)/$",
        consumers.MarketDataConsumer.as_asgi(),
    ),
    # Market data without timeframe — defaults to 1m (backward compatible)
    re_path(
        r"ws/market/(?P<symbol>[A-Z0-9]+)/$",
        consumers.MarketDataConsumer.as_asgi(),
    ),
    # Reversal zones WebSocket
    re_path(
        r"ws/reversal-zones/(?P<symbol>[^/]+)/$",
        consumers.ReversalZoneConsumer.as_asgi(),
    ),
    # AI Signals WebSocket (used by asset page)
    re_path(
        r"ws/ai-signals/$",
        consumers.AISignalConsumer.as_asgi(),
    ),
]