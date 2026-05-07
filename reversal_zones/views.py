from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import ReversalZone, ReversalStatus


@api_view(['GET'])
@permission_classes([AllowAny])
def list_reversal_zones(request):
    zones = ReversalZone.objects.values('symbol').distinct()
    return Response({'symbols': list(zones)})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_reversal_zone_detail(request, symbol):
    zones = ReversalZone.objects.filter(symbol=symbol).order_by('-reversal_time')[:20]
    data = [{
        'symbol': z.symbol,
        'reversal_time': z.reversal_time.isoformat(),
        'center_price': float(z.center_price),
        'is_bullish': z.is_bullish,
        'label_text': z.label_text,
    } for z in zones]
    return Response({'symbol': symbol, 'zones': data})
