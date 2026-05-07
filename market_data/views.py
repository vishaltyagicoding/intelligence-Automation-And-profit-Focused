"""
API views for market data.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import OHLCV
import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_market_data(request):
    """Get current market data for a symbol."""
    
    symbol = request.GET.get('symbol')
    if not symbol:
        return Response({
            'error': 'Symbol parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Try to get from Redis cache first
    cache_key = f"market:{symbol}:current"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        import json
        return Response(json.loads(cached_data))
    
    # Get latest OHLCV from database
    try:
        latest = OHLCV.objects.filter(symbol=symbol).first()
        if latest:
            data = {
                'symbol': symbol,
                'timestamp': latest.timestamp.isoformat(),
                'price': str(latest.close),
                'open': str(latest.open),
                'high': str(latest.high),
                'low': str(latest.low),
                'volume': str(latest.volume),
            }
            return Response(data)
        else:
            return Response({
                'error': f'No data found for symbol {symbol}'
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_historical_data(request):
    """Get historical OHLCV data for a symbol."""
    
    symbol = request.GET.get('symbol')
    if not symbol:
        return Response({
            'error': 'Symbol parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    interval = request.GET.get('interval', '4h')
    limit = int(request.GET.get('limit', 100))
    
    try:
        data = OHLCV.objects.filter(symbol=symbol).order_by('-timestamp')[:limit]
        
        return Response({
            'symbol': symbol,
            'interval': interval,
            'count': len(data),
            'data': [{
                'timestamp': item.timestamp.isoformat(),
                'open': str(item.open),
                'high': str(item.high),
                'low': str(item.low),
                'close': str(item.close),
                'volume': str(item.volume),
            } for item in reversed(list(data))]
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ohlcv(request, symbol):
    """Get OHLCV data for a symbol."""
    
    limit = int(request.GET.get('limit', 100))
    data = OHLCV.objects.filter(symbol=symbol)[:limit]
    
    return Response([{
        'timestamp': item.timestamp.isoformat(),
        'open': str(item.open),
        'high': str(item.high),
        'low': str(item.low),
        'close': str(item.close),
        'volume': str(item.volume),
    } for item in data])
