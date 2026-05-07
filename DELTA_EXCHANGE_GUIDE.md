# 🚀 Delta Exchange Integration Guide

## ⚠️ IMPORTANT SECURITY WARNING

**YOU SHARED YOUR API KEYS PUBLICLY!** This is extremely dangerous.

### Immediate Actions Required:

1. **Go to**: https://www.delta.exchange/app/account/api
2. **Revoke** the exposed API keys immediately
3. **Generate** new API keys
4. **Never** share API keys publicly again
5. **Use** environment variables (`.env` file)

---

## 🎯 What is Delta Exchange?

Delta Exchange is a cryptocurrency derivatives exchange offering:
- **Perpetual Futures** - BTC, ETH, and 100+ altcoins
- **Futures Contracts** - Quarterly and monthly expiry
- **Options** - Call and Put options
- **Spot Trading** - Direct crypto trading
- **High Leverage** - Up to 100x leverage
- **Low Fees** - Competitive trading fees

**Website**: https://www.delta.exchange/

---

## ✅ Integration Complete!

I've integrated Delta Exchange into your NeuralTrade system:

### Files Created:
1. **`market_data/delta_client.py`** - Complete Delta Exchange API client
2. **`trading/delta_consumer.py`** - WebSocket consumer for real-time data
3. Updated **`trading/routing.py`** - Added Delta WebSocket routes
4. Updated **`neuraltrade/settings.py`** - Added Delta configuration
5. Updated **`.env.example`** - Added Delta API key placeholders

---

## 🔧 Setup Instructions

### Step 1: Get API Keys (Securely!)

1. Go to https://www.delta.exchange/
2. Create account / Login
3. Go to **Account → API Management**
4. Click **"Create New API Key"**
5. Set permissions:
   - ✅ Read (for market data)
   - ✅ Trade (for placing orders)
   - ❌ Withdraw (keep disabled for security)
6. **Copy** API Key and Secret
7. **Store securely** in `.env` file

### Step 2: Configure Environment

```bash
# Edit your .env file
nano .env

# Add Delta Exchange credentials
DELTA_API_KEY=your_new_api_key_here
DELTA_API_SECRET=your_new_api_secret_here
```

### Step 3: Install Dependencies

```bash
# Delta Exchange uses standard requests library (already installed)
pip install websocket-client
```

### Step 4: Restart Services

```bash
# If using Docker
docker-compose restart django celery_worker

# If running manually
# Stop and restart Django and Celery
```

---

## 🎯 Available Trading Symbols on Delta Exchange

### Perpetual Futures (Most Popular)
- **BTCUSDT** - Bitcoin
- **ETHUSDT** - Ethereum
- **BNBUSDT** - Binance Coin
- **ADAUSDT** - Cardano
- **XRPUSDT** - Ripple
- **SOLUSDT** - Solana
- **DOGEUSDT** - Dogecoin
- **DOTUSDT** - Polkadot
- **MATICUSDT** - Polygon
- **AVAXUSDT** - Avalanche
- **LINKUSDT** - Chainlink
- **UNIUSDT** - Uniswap
- **ATOMUSDT** - Cosmos
- **LTCUSDT** - Litecoin
- **ETCUSDT** - Ethereum Classic

**Total**: 100+ perpetual futures available!

### Futures Contracts
- **BTCUSD_QUARTERLY** - Bitcoin quarterly futures
- **ETHUSD_QUARTERLY** - Ethereum quarterly futures
- **BTCUSD_MONTHLY** - Bitcoin monthly futures

### Options
- **BTC-OPTIONS** - Bitcoin options (Call/Put)
- **ETH-OPTIONS** - Ethereum options (Call/Put)

---

## 📡 Real-time Data Streaming

### WebSocket Connection

```javascript
// Connect to Delta Exchange WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/delta/BTCUSDT/');

// Receive real-time updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'ticker') {
    console.log('Price:', data.data.close);
    console.log('Volume:', data.data.volume);
  }
  
  if (data.type === 'orderbook') {
    console.log('Bids:', data.data.buy);
    console.log('Asks:', data.data.sell);
  }
  
  if (data.type === 'trade') {
    console.log('Trade:', data.data);
  }
};

// Request account balance
ws.send(JSON.stringify({
  action: 'get_balance'
}));

// Request available products
ws.send(JSON.stringify({
  action: 'get_products'
}));
```

---

## 🔌 API Usage Examples

### 1. Get Market Data

```python
from market_data.delta_client import DeltaExchangeClient

# Initialize client
client = DeltaExchangeClient(
    api_key='your_api_key',
    api_secret='your_api_secret'
)

# Get ticker
ticker = client.get_ticker('BTCUSDT')
print(f"Price: {ticker['close']}")
print(f"Volume: {ticker['volume']}")

# Get orderbook
orderbook = client.get_orderbook('BTCUSDT', depth=20)
print(f"Best bid: {orderbook['buy'][0]}")
print(f"Best ask: {orderbook['sell'][0]}")

# Get OHLC data
candles = client.get_ohlc('BTCUSDT', resolution='1', start=start_time, end=end_time)
for candle in candles:
    print(f"Time: {candle['time']}, Close: {candle['close']}")

# Get recent trades
trades = client.get_recent_trades('BTCUSDT', limit=100)
for trade in trades:
    print(f"Price: {trade['price']}, Size: {trade['size']}")
```

### 2. Get Account Information

```python
# Get balance
balance = client.get_balance()
print(f"Available: {balance['available_balance']}")
print(f"Total: {balance['balance']}")

# Get open positions
positions = client.get_positions()
for position in positions:
    print(f"Symbol: {position['product_symbol']}")
    print(f"Size: {position['size']}")
    print(f"PnL: {position['unrealized_pnl']}")

# Get open orders
orders = client.get_orders(state='open')
for order in orders:
    print(f"Order ID: {order['id']}")
    print(f"Symbol: {order['product_symbol']}")
    print(f"Side: {order['side']}")
    print(f"Price: {order['limit_price']}")
```

### 3. Place Orders

```python
# Place limit order
order = client.place_order(
    symbol='BTCUSDT',
    side='buy',
    order_type='limit_order',
    size=0.001,
    price=50000,
    stop_loss=49000,  # Optional
    take_profit=52000  # Optional
)
print(f"Order placed: {order['id']}")

# Place market order
order = client.place_order(
    symbol='BTCUSDT',
    side='sell',
    order_type='market_order',
    size=0.001
)

# Cancel order
result = client.cancel_order(order_id='12345')
print(f"Order cancelled: {result}")

# Cancel all orders
result = client.cancel_all_orders(symbol='BTCUSDT')
print(f"All orders cancelled")

# Close position
result = client.close_position('BTCUSDT')
print(f"Position closed")
```

---

## 🤖 AI Trading with Delta Exchange

### Update AI Orchestrator

```python
# In ai_agents/orchestrator.py

from market_data.delta_client import DeltaExchangeClient

class AIOrchestrator:
    def __init__(self):
        # ... existing code ...
        
        # Add Delta Exchange client
        self.delta_client = DeltaExchangeClient(
            api_key=settings.DELTA_API_KEY,
            api_secret=settings.DELTA_API_SECRET
        )
    
    async def analyze(self, symbol: str, market: str = 'CRYPTO', exchange: str = 'BINANCE'):
        """
        Analyze market and make trading decision
        
        Args:
            symbol: Trading symbol
            market: 'CRYPTO' or 'COMMODITY'
            exchange: 'BINANCE' or 'DELTA'
        """
        # Fetch data based on exchange
        if exchange == 'DELTA':
            ticker = await sync_to_async(self.delta_client.get_ticker)(symbol)
            ohlc = await sync_to_async(self.delta_client.get_ohlc)(symbol, resolution='1')
        else:
            # Use Binance (existing code)
            ticker = await self.fetch_binance_data(symbol)
        
        # Run AI analysis (same for all exchanges)
        decision = await self.agent_a.analyze(ticker, ohlc)
        
        # Execute trade on correct exchange
        if exchange == 'DELTA':
            result = await self.execute_delta_trade(symbol, decision)
        else:
            result = await self.execute_binance_trade(symbol, decision)
        
        return result
    
    async def execute_delta_trade(self, symbol: str, decision: Dict):
        """Execute trade on Delta Exchange"""
        if decision['action'] == 'BUY':
            order = await sync_to_async(self.delta_client.place_order)(
                symbol=symbol,
                side='buy',
                order_type='market_order',
                size=decision['size'],
                stop_loss=decision['stop_loss']
            )
            return order
        
        elif decision['action'] == 'SELL':
            order = await sync_to_async(self.delta_client.place_order)(
                symbol=symbol,
                side='sell',
                order_type='market_order',
                size=decision['size']
            )
            return order
```

---

## 📊 Training Model with Delta Exchange Data

### Update Training Script

```python
# In kaggle_training_notebook.py or ai_agents/training/data_preparation.py

from market_data.delta_client import DeltaExchangeClient

def fetch_delta_historical_data(symbol='BTCUSDT', days=365):
    """Fetch historical data from Delta Exchange"""
    client = DeltaExchangeClient(
        api_key=settings.DELTA_API_KEY,
        api_secret=settings.DELTA_API_SECRET
    )
    
    # Calculate timestamps
    end_time = int(time.time())
    start_time = end_time - (days * 24 * 60 * 60)
    
    # Fetch OHLC data (1-minute candles)
    candles = client.get_ohlc(
        symbol=symbol,
        resolution='1',  # 1 minute
        start=start_time,
        end=end_time
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(candles)
    df['timestamp'] = pd.to_datetime(df['time'], unit='s')
    
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

# Use in training
df = fetch_delta_historical_data(symbol='BTCUSDT', days=365)
cnn_data, lstm_data, labels = prepare_dataset(df)
```

---

## 🔒 Security Best Practices

### 1. API Key Permissions
- ✅ Enable: Read, Trade
- ❌ Disable: Withdraw
- ✅ Set IP whitelist if possible

### 2. Environment Variables
```bash
# NEVER commit .env file to git
echo ".env" >> .gitignore

# Use strong API secrets
# Rotate keys regularly
```

### 3. Rate Limiting
```python
# Delta Exchange has rate limits
# Implement exponential backoff

import time
from functools import wraps

def rate_limit(max_per_second=10):
    min_interval = 1.0 / max_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

---

## 🎯 Comparison: Binance vs Delta Exchange

| Feature | Binance | Delta Exchange |
|---------|---------|----------------|
| **Spot Trading** | ✅ Yes | ✅ Yes |
| **Futures** | ✅ Yes | ✅ Yes |
| **Options** | ❌ No | ✅ Yes |
| **Leverage** | Up to 125x | Up to 100x |
| **Fees** | 0.1% | 0.05% |
| **API** | Excellent | Good |
| **Liquidity** | Very High | Medium |
| **KYC** | Required | Required |
| **Indian Users** | ⚠️ Restricted | ✅ Supported |

---

## 🚀 Quick Start Commands

```bash
# 1. Add API keys to .env
echo "DELTA_API_KEY=your_key" >> .env
echo "DELTA_API_SECRET=your_secret" >> .env

# 2. Test connection
python manage.py shell
>>> from market_data.delta_client import DeltaExchangeClient
>>> from django.conf import settings
>>> client = DeltaExchangeClient(settings.DELTA_API_KEY, settings.DELTA_API_SECRET)
>>> client.test_connection()
True

# 3. Get available symbols
>>> symbols = client.get_available_symbols()
>>> print(symbols[:10])

# 4. Start WebSocket
# Connect to: ws://localhost:8000/ws/delta/BTCUSDT/

# 5. Test AI with Delta
curl -X POST http://localhost:8000/api/ai/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","market":"CRYPTO","exchange":"DELTA"}'
```

---

## ✅ Summary

**Delta Exchange is now integrated!**

### What You Can Do:
- ✅ Stream real-time market data
- ✅ Place orders (market, limit, stop-loss)
- ✅ Get account balance and positions
- ✅ Train AI model with Delta data
- ✅ Trade 100+ crypto pairs
- ✅ Use high leverage (up to 100x)

### Your Users Can Trade:
- **Perpetual Futures**: BTC, ETH, 100+ altcoins
- **Futures Contracts**: Quarterly, monthly
- **Options**: Call and Put options
- **Spot**: Direct crypto trading

### Next Steps:
1. **Revoke** exposed API keys
2. **Generate** new keys securely
3. **Add** to `.env` file
4. **Test** connection
5. **Start** trading!

---

**🔒 Remember: NEVER share API keys publicly!**
