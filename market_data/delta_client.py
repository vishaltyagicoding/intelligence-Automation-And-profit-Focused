"""
Delta Exchange Client for Real-time Market Data
https://www.delta.exchange/
"""

import hmac
import hashlib
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DeltaExchangeClient:
    """
    Delta Exchange API Client for trading and market data
    Documentation: https://docs.delta.exchange/
    """
    
    BASE_URL = "https://api.delta.exchange"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Delta Exchange client
        
        Args:
            api_key: Your Delta Exchange API key
            api_secret: Your Delta Exchange API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        
    def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> str:
        """Generate HMAC signature for authentication"""
        timestamp = str(int(time.time()))
        signature_data = method + timestamp + endpoint + payload
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, timestamp
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make authenticated request to Delta Exchange API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # Prepare payload
        payload = ""
        if data:
            payload = json.dumps(data)
        
        # Generate signature
        signature, timestamp = self._generate_signature(method, endpoint, payload)
        
        # Set headers
        headers = {
            'api-key': self.api_key,
            'signature': signature,
            'timestamp': timestamp,
            'Content-Type': 'application/json'
        }
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Delta Exchange API error: {e}")
            raise
    
    # ============================================================================
    # Market Data Methods
    # ============================================================================
    
    def get_products(self) -> List[Dict]:
        """
        Get all available trading products
        
        Returns:
            List of products with details
        """
        response = self._request('GET', '/v2/products')
        return response.get('result', [])
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            Ticker data with price, volume, etc.
        """
        response = self._request('GET', f'/v2/tickers/{symbol}')
        return response.get('result', {})
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """
        Get orderbook (bids/asks) for a symbol
        
        Args:
            symbol: Trading symbol
            depth: Number of levels (default 20)
            
        Returns:
            Orderbook with bids and asks
        """
        params = {'depth': depth}
        response = self._request('GET', f'/v2/l2orderbook/{symbol}', params=params)
        return response.get('result', {})
    
    def get_ohlc(self, symbol: str, resolution: str = '1', start: int = None, end: int = None) -> List[Dict]:
        """
        Get OHLC (candlestick) data
        
        Args:
            symbol: Trading symbol
            resolution: Timeframe ('1' = 1min, '5' = 5min, '60' = 1hour, 'D' = 1day)
            start: Start timestamp (Unix)
            end: End timestamp (Unix)
            
        Returns:
            List of OHLC candles
        """
        params = {
            'resolution': resolution,
            'symbol': symbol
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        response = self._request('GET', '/v2/history/candles', params=params)
        return response.get('result', [])
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Get recent trades for a symbol
        
        Args:
            symbol: Trading symbol
            limit: Number of trades (max 500)
            
        Returns:
            List of recent trades
        """
        params = {'symbol': symbol}
        response = self._request('GET', '/v2/trades', params=params)
        trades = response.get('result', [])
        return trades[:limit]
    
    # ============================================================================
    # Account Methods
    # ============================================================================
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Account balance details
        """
        response = self._request('GET', '/v2/wallet/balances')
        return response.get('result', {})
    
    def get_positions(self) -> List[Dict]:
        """
        Get all open positions
        
        Returns:
            List of open positions
        """
        response = self._request('GET', '/v2/positions')
        return response.get('result', [])
    
    def get_orders(self, symbol: str = None, state: str = 'open') -> List[Dict]:
        """
        Get orders
        
        Args:
            symbol: Filter by symbol (optional)
            state: Order state ('open', 'closed', 'cancelled')
            
        Returns:
            List of orders
        """
        params = {'state': state}
        if symbol:
            params['product_id'] = symbol
            
        response = self._request('GET', '/v2/orders', params=params)
        return response.get('result', [])
    
    # ============================================================================
    # Trading Methods
    # ============================================================================
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        size: float,
        price: float = None,
        stop_loss: float = None,
        take_profit: float = None,
        time_in_force: str = 'gtc'
    ) -> Dict:
        """
        Place a new order
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            order_type: 'limit_order' or 'market_order'
            size: Order size
            price: Limit price (required for limit orders)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            time_in_force: 'gtc' (good till cancel) or 'ioc' (immediate or cancel)
            
        Returns:
            Order details
        """
        data = {
            'product_id': symbol,
            'side': side,
            'order_type': order_type,
            'size': size,
            'time_in_force': time_in_force
        }
        
        if price:
            data['limit_price'] = price
            
        if stop_loss:
            data['stop_loss_order'] = {
                'stop_price': stop_loss,
                'order_type': 'market_order'
            }
            
        if take_profit:
            data['take_profit_order'] = {
                'stop_price': take_profit,
                'order_type': 'limit_order',
                'limit_price': take_profit
            }
        
        response = self._request('POST', '/v2/orders', data=data)
        return response.get('result', {})
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        response = self._request('DELETE', f'/v2/orders/{order_id}')
        return response.get('result', {})
    
    def cancel_all_orders(self, symbol: str = None) -> Dict:
        """
        Cancel all orders
        
        Args:
            symbol: Cancel only orders for this symbol (optional)
            
        Returns:
            Cancellation result
        """
        data = {}
        if symbol:
            data['product_id'] = symbol
            
        response = self._request('DELETE', '/v2/orders/all', data=data)
        return response.get('result', {})
    
    def close_position(self, symbol: str) -> Dict:
        """
        Close a position
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Close position result
        """
        data = {'product_id': symbol}
        response = self._request('POST', '/v2/positions/close', data=data)
        return response.get('result', {})
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def get_product_info(self, symbol: str) -> Dict:
        """
        Get detailed product information
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Product details
        """
        products = self.get_products()
        for product in products:
            if product.get('symbol') == symbol:
                return product
        return {}
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of all available trading symbols
        
        Returns:
            List of symbol names
        """
        products = self.get_products()
        return [p.get('symbol') for p in products if p.get('symbol')]
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.get_balance()
            logger.info("Delta Exchange connection successful")
            return True
        except Exception as e:
            logger.error(f"Delta Exchange connection failed: {e}")
            return False


# ============================================================================
# WebSocket Client for Real-time Data
# ============================================================================

import websocket
import threading


class DeltaWebSocketClient:
    """
    Delta Exchange WebSocket client for real-time market data
    """
    
    WS_URL = "wss://socket.delta.exchange"
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize WebSocket client
        
        Args:
            api_key: API key (optional, for private channels)
            api_secret: API secret (optional, for private channels)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        self.callbacks = {}
        self.running = False
        
    def connect(self):
        """Connect to WebSocket"""
        self.ws = websocket.WebSocketApp(
            self.WS_URL,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        
        self.running = True
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
    def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
    
    def subscribe_ticker(self, symbol: str, callback):
        """
        Subscribe to ticker updates
        
        Args:
            symbol: Trading symbol
            callback: Function to call with ticker data
        """
        channel = f"v2/ticker.{symbol}"
        self.callbacks[channel] = callback
        
        self._send({
            'type': 'subscribe',
            'payload': {
                'channels': [{'name': channel}]
            }
        })
    
    def subscribe_orderbook(self, symbol: str, callback):
        """
        Subscribe to orderbook updates
        
        Args:
            symbol: Trading symbol
            callback: Function to call with orderbook data
        """
        channel = f"l2_orderbook.{symbol}"
        self.callbacks[channel] = callback
        
        self._send({
            'type': 'subscribe',
            'payload': {
                'channels': [{'name': channel}]
            }
        })
    
    def subscribe_trades(self, symbol: str, callback):
        """
        Subscribe to trade updates
        
        Args:
            symbol: Trading symbol
            callback: Function to call with trade data
        """
        channel = f"recent_trades.{symbol}"
        self.callbacks[channel] = callback
        
        self._send({
            'type': 'subscribe',
            'payload': {
                'channels': [{'name': channel}]
            }
        })
    
    def _send(self, data: Dict):
        """Send data through WebSocket"""
        if self.ws:
            self.ws.send(json.dumps(data))
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            channel = data.get('channel')
            
            if channel and channel in self.callbacks:
                self.callbacks[channel](data.get('data'))
                
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info("WebSocket connection closed")
    
    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connection opened")
