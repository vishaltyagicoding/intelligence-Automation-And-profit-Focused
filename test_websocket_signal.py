#!/usr/bin/env python
"""
Test script to manually broadcast a signal via WebSocket to test frontend reception.
"""

import os
import sys
import django
import asyncio
import json
from datetime import datetime
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neuraltrade.settings')
django.setup()

from trading.models import MarketSignal
from trading.consumers import broadcast_ai_signal
from channels.layers import get_channel_layer

from channels.db import database_sync_to_async

@database_sync_to_async
def get_existing_signal():
    return MarketSignal.objects.filter(symbol='BTCUSD').first()

@database_sync_to_async  
def create_test_signal():
    return MarketSignal.objects.create(
        symbol='BTCUSD',
        market='CRYPTO',
        action='BUY',
        confidence=Decimal('88.5'),
        signal_price=Decimal('78200.00'),
        message='🧪 TEST SIGNAL - Manual WebSocket broadcast test',
        color='#22c55e',
        ai_context={'test': True, 'is_current_signal': True},
        is_broadcast=True
    )

async def test_websocket_signal():
    """Test sending a signal via WebSocket"""
    
    print("🧪 Testing WebSocket Signal Broadcasting")
    print("=" * 50)
    
    # Get existing signal
    existing_signal = await get_existing_signal()
    
    if existing_signal:
        print(f"📊 Found existing signal: {existing_signal.action} @ ${existing_signal.signal_price}")
        payload = existing_signal.websocket_payload()
        print(f"📡 WebSocket payload: {payload}")
        
        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        await broadcast_ai_signal(channel_layer, payload)
        
        print("✅ Signal broadcasted via WebSocket!")
        print("🔍 Check frontend console for received signal")
    else:
        print("❌ No existing signals found")
        
        # Create a new test signal
        print("📊 Creating new test signal...")
        signal = await create_test_signal()
        
        payload = signal.websocket_payload()
        print(f"📡 WebSocket payload: {payload}")
        
        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        await broadcast_ai_signal(channel_layer, payload)
        
        print("✅ Test signal created and broadcasted!")
        print("🔍 Check frontend console for received signal")

if __name__ == '__main__':
    asyncio.run(test_websocket_signal())