"""
Delta Exchange WebSocket Consumer for Real-time Market Data
"""

import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.conf import settings
import redis.asyncio as aioredis
from market_data.delta_client import DeltaExchangeClient, DeltaWebSocketClient

logger = logging.getLogger(__name__)


class DeltaMarketConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for Delta Exchange real-time market data
    
    Usage:
        ws://localhost:8000/ws/delta/BTCUSDT/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        self.room_group_name = f'delta_market_{self.symbol}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Initialize Delta WebSocket client
        self.delta_ws = DeltaWebSocketClient(
            api_key=settings.DELTA_API_KEY,
            api_secret=settings.DELTA_API_SECRET
        )
        
        # Connect to Delta Exchange
        self.delta_ws.connect()
        
        # Subscribe to ticker updates
        self.delta_ws.subscribe_ticker(self.symbol, self.on_ticker_update)
        
        # Subscribe to orderbook updates
        self.delta_ws.subscribe_orderbook(self.symbol, self.on_orderbook_update)
        
        # Subscribe to trade updates
        self.delta_ws.subscribe_trades(self.symbol, self.on_trade_update)
        
        logger.info(f"Delta WebSocket connected for {self.symbol}")
        
        # Start background task to fetch and cache data
        asyncio.create_task(self.fetch_market_data())
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Disconnect from Delta Exchange
        if hasattr(self, 'delta_ws'):
            self.delta_ws.disconnect()
        
        logger.info(f"Delta WebSocket disconnected for {self.symbol}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages from client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe_ticker':
                # Already subscribed in connect()
                pass
            elif action == 'subscribe_orderbook':
                # Already subscribed in connect()
                pass
            elif action == 'get_products':
                await self.send_available_products()
            elif action == 'get_balance':
                await self.send_account_balance()
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))
    
    async def on_ticker_update(self, data):
        """Handle ticker updates from Delta Exchange"""
        # Send to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'ticker',
            'symbol': self.symbol,
            'data': data
        }))
        
        # Cache in Redis
        await self.cache_ticker_data(data)
    
    async def on_orderbook_update(self, data):
        """Handle orderbook updates from Delta Exchange"""
        await self.send(text_data=json.dumps({
            'type': 'orderbook',
            'symbol': self.symbol,
            'data': data
        }))
    
    async def on_trade_update(self, data):
        """Handle trade updates from Delta Exchange"""
        await self.send(text_data=json.dumps({
            'type': 'trade',
            'symbol': self.symbol,
            'data': data
        }))
    
    async def fetch_market_data(self):
        """Background task to fetch and cache market data"""
        client = DeltaExchangeClient(
            api_key=settings.DELTA_API_KEY,
            api_secret=settings.DELTA_API_SECRET
        )
        
        while True:
            try:
                # Fetch ticker
                ticker = await sync_to_async(client.get_ticker)(self.symbol)
                
                # Send to WebSocket
                await self.send(text_data=json.dumps({
                    'type': 'ticker',
                    'symbol': self.symbol,
                    'data': ticker
                }))
                
                # Cache in Redis
                await self.cache_ticker_data(ticker)
                
                # Wait 1 second before next fetch
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching Delta market data: {e}")
                await asyncio.sleep(5)
    
    async def cache_ticker_data(self, data):
        """Cache ticker data in Redis"""
        try:
            redis_client = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            )
            
            # Cache ticker data
            key = f"delta:ticker:{self.symbol}"
            await redis_client.setex(
                key,
                60,  # 60 seconds TTL
                json.dumps(data)
            )
            
            # Add to time series
            ts_key = f"delta:ticks:{self.symbol}"
            await redis_client.lpush(ts_key, json.dumps({
                'timestamp': data.get('timestamp'),
                'price': data.get('close'),
                'volume': data.get('volume')
            }))
            
            # Keep only last 10,000 ticks
            await redis_client.ltrim(ts_key, 0, 9999)
            
            await redis_client.close()
            
        except Exception as e:
            logger.error(f"Error caching Delta ticker data: {e}")
    
    async def send_available_products(self):
        """Send list of available trading products"""
        try:
            client = DeltaExchangeClient(
                api_key=settings.DELTA_API_KEY,
                api_secret=settings.DELTA_API_SECRET
            )
            
            products = await sync_to_async(client.get_products)()
            
            await self.send(text_data=json.dumps({
                'type': 'products',
                'data': products
            }))
            
        except Exception as e:
            logger.error(f"Error fetching Delta products: {e}")
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def send_account_balance(self):
        """Send account balance"""
        try:
            client = DeltaExchangeClient(
                api_key=settings.DELTA_API_KEY,
                api_secret=settings.DELTA_API_SECRET
            )
            
            balance = await sync_to_async(client.get_balance)()
            
            await self.send(text_data=json.dumps({
                'type': 'balance',
                'data': balance
            }))
            
        except Exception as e:
            logger.error(f"Error fetching Delta balance: {e}")
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    # Receive message from room group
    async def market_update(self, event):
        """Handle market update from channel layer"""
        await self.send(text_data=json.dumps(event['data']))
