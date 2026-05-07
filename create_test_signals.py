"""
Create test signals for BTCUSD to populate the chart
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from trading.models import MarketSignal
from django.utils import timezone
from decimal import Decimal
import time

def create_test_signals():
    """Create test signals for all types"""
    
    print("Creating test signals for BTCUSD...")
    
    # Create BUY signal
    buy = MarketSignal.objects.create(
        symbol='BTCUSD',
        market='CRYPTO',
        action='BUY',
        confidence=Decimal('87.5'),
        signal_price=Decimal('78800.00'),
        stop_loss=Decimal('78100.00'),
        target=Decimal('80200.00'),
        message='Agent A: Bullish pattern | Agent B: Positive sentiment | Agent C: Risk managed',
        color='#26a69a',
        is_broadcast=True
    )
    print(f'✅ Created BUY signal: {buy.id} @ ${buy.signal_price}')
    
    time.sleep(1)
    
    # Create SELL signal
    sell = MarketSignal.objects.create(
        symbol='BTCUSD',
        market='CRYPTO',
        action='SELL',
        confidence=Decimal('82.3'),
        signal_price=Decimal('79200.00'),
        stop_loss=Decimal('79900.00'),
        target=Decimal('78000.00'),
        message='Agent A: Bearish pattern | Agent B: Negative sentiment | Agent C: Risk managed',
        color='#ef5350',
        is_broadcast=True
    )
    print(f'✅ Created SELL signal: {sell.id} @ ${sell.signal_price}')
    
    time.sleep(1)
    
    # Create HOLD signal
    hold = MarketSignal.objects.create(
        symbol='BTCUSD',
        market='CRYPTO',
        action='HOLD',
        confidence=Decimal('65.0'),
        signal_price=Decimal('78950.00'),
        message='Agent A: Mixed signals | Agent B: Neutral sentiment | Agent C: Wait for better setup',
        color='#fdd835',
        is_broadcast=True
    )
    print(f'✅ Created HOLD signal: {hold.id} @ ${hold.signal_price}')
    
    time.sleep(1)
    
    # Create STOP_LOSS signal
    stop_loss = MarketSignal.objects.create(
        symbol='BTCUSD',
        market='CRYPTO',
        action='STOP_LOSS',
        confidence=Decimal('90.0'),
        signal_price=Decimal('78100.00'),
        message='Agent C: Stop loss triggered - Risk management',
        color='#fb8c00',
        is_broadcast=True
    )
    print(f'✅ Created STOP_LOSS signal: {stop_loss.id} @ ${stop_loss.signal_price}')
    
    # Count total signals
    total = MarketSignal.objects.filter(symbol='BTCUSD').count()
    buy_count = MarketSignal.objects.filter(symbol='BTCUSD', action='BUY').count()
    sell_count = MarketSignal.objects.filter(symbol='BTCUSD', action='SELL').count()
    hold_count = MarketSignal.objects.filter(symbol='BTCUSD', action='HOLD').count()
    stop_count = MarketSignal.objects.filter(symbol='BTCUSD', action='STOP_LOSS').count()
    
    print(f'\n📊 Signal Statistics:')
    print(f'   Total: {total}')
    print(f'   BUY: {buy_count}')
    print(f'   SELL: {sell_count}')
    print(f'   HOLD: {hold_count}')
    print(f'   STOP_LOSS: {stop_count}')
    print(f'\n✅ Test signals created successfully!')
    print(f'   Refresh your browser to see signals on the chart')

if __name__ == '__main__':
    create_test_signals()
