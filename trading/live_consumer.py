"""
Live data WebSocket consumer for real-time updates.
Sends market data, balance updates, and AI activity to connected clients.
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class LiveDataConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live trading data.
    Sends real-time market data, balance, and AI activity updates.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        # Get token from query string
        query_string = self.scope.get('query_string', b'').decode()
        token = None
        
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if not token:
            await self.close(code=4001)
            return
        
        # Validate token and get user
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            self.user = await self.get_user(user_id)
            
            if not self.user:
                await self.close(code=4002)
                return
                
        except TokenError:
            await self.close(code=4003)
            return
        
        # Accept connection
        await self.accept()
        
        # Add to live data group
        await self.channel_layer.group_add(
            f"live_data_{self.user.id}",
            self.channel_name
        )
        
        # Send initial connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'message': 'WebSocket connected successfully'
        }))
        
        # Start sending periodic updates
        self.update_task = asyncio.create_task(self.send_periodic_updates())

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel update task
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        
        # Remove from live data group
        if hasattr(self, 'user'):
            await self.channel_layer.group_discard(
                f"live_data_{self.user.id}",
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            pass

    async def send_periodic_updates(self):
        """Send periodic updates to the client."""
        try:
            while True:
                try:
                    # Get latest market data as candle
                    candle_data = await self.get_market_data()
                    
                    # Send candle update (format expected by Flutter app)
                    await self.send(text_data=json.dumps({
                        'type': 'candle_update',
                        'data': candle_data
                    }))
                    
                    print(f"Sent candle update: {candle_data}")
                    
                except Exception as e:
                    print(f"Error sending candle update: {e}")
                
                # Wait 5 seconds before next update
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            print("Periodic updates cancelled")
            pass

    @database_sync_to_async
    def get_user(self, user_id):
        """Get user from database."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_market_data(self):
        """Get latest market data as candle format."""
        import time
        import random
        
        # Generate realistic dummy candle data for production
        # TODO: Replace with real market data from your data source
        base_price = 64000.0
        variation = random.uniform(-100, 100)
        
        open_price = base_price + variation
        high_price = open_price + random.uniform(0, 150)
        low_price = open_price - random.uniform(0, 150)
        close_price = random.uniform(low_price, high_price)
        
        return {
            'timestamp': int(time.time()),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': round(random.uniform(10, 50), 2)
        }

    # Group message handlers
    async def market_update(self, event):
        """Handle market update from group."""
        await self.send(text_data=json.dumps({
            'type': 'market_data',
            'data': event['data']
        }))

    async def balance_update(self, event):
        """Handle balance update from group."""
        await self.send(text_data=json.dumps({
            'type': 'balance',
            'data': event['data']
        }))

    async def ai_activity(self, event):
        """Handle AI activity from group."""
        await self.send(text_data=json.dumps({
            'type': 'ai_activity',
            'data': event['data']
        }))
