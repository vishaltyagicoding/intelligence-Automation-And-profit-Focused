# 🚨 Binance Geo-Restriction Issue

## ❌ Current Problem:

Your AWS EC2 server (us-west-1) is being blocked by Binance API with error:
```
APIError(code=0): Service unavailable from a restricted location 
according to 'b. Eligibility' in https://www.binance.com/en/terms
```

This is why:
- ❌ No market prices showing on dashboard
- ❌ "LIVE MARKET FEED" shows no data
- ❌ Charts not loading
- ❌ WebSocket connection failing

---

## 🔧 Solutions:

### Option 1: Use Binance.US (If Targeting US Users)
**Best for:** US-based trading platform

**Steps:**
1. Sign up for Binance.US API keys
2. Update `trading/consumers.py` to use Binance.US endpoints
3. Change API base URL from `api.binance.com` to `api.binance.us`

**Pros:** Official Binance service for US
**Cons:** Requires API keys, fewer trading pairs

---

### Option 2: Use CoinGecko API (Recommended - FREE)
**Best for:** Quick fix, no restrictions, free

**Steps:**
1. No API key needed
2. Replace Binance WebSocket with CoinGecko REST API
3. Poll for price updates every 10-30 seconds

**Pros:** 
- ✅ No geo-restrictions
- ✅ Free (50 calls/minute)
- ✅ No API key needed
- ✅ Works worldwide

**Cons:** 
- REST API (not WebSocket)
- Slightly delayed data (10-30 seconds)

**CoinGecko API Endpoints:**
```
# Bitcoin price
https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd

# Ethereum price
https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd

# Historical data (for charts)
https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1
```

---

### Option 3: Use CryptoCompare API
**Best for:** Professional features, good documentation

**Steps:**
1. Sign up at https://www.cryptocompare.com/
2. Get free API key (100,000 calls/month)
3. Update code to use CryptoCompare WebSocket

**Pros:**
- ✅ WebSocket support
- ✅ No geo-restrictions
- ✅ Good free tier

**Cons:**
- Requires API key
- Rate limits on free tier

---

### Option 4: Use Twelve Data API
**Best for:** Stock + Crypto data

**Steps:**
1. Sign up at https://twelvedata.com/
2. Get free API key (800 calls/day)
3. Supports both REST and WebSocket

**Pros:**
- ✅ Stocks + Crypto
- ✅ WebSocket support
- ✅ No geo-restrictions

**Cons:**
- Limited free tier
- Requires API key

---

### Option 5: Use VPN/Proxy on EC2
**Best for:** Keep using Binance

**Steps:**
1. Install VPN client on EC2
2. Route traffic through allowed region
3. Keep existing Binance code

**Pros:**
- ✅ Keep existing code
- ✅ Real-time Binance data

**Cons:**
- ❌ Additional cost
- ❌ Slower connection
- ❌ Against Binance ToS
- ❌ May get banned

---

## 🎯 Recommended Solution: CoinGecko API

I recommend using **CoinGecko API** because:
1. ✅ Free and no restrictions
2. ✅ No API key needed
3. ✅ Works from any location
4. ✅ Easy to implement
5. ✅ Reliable service

---

## 📝 Quick Implementation Guide (CoinGecko):

### Step 1: Install requests library (already installed)
```bash
# Already in requirements.txt
pip install requests
```

### Step 2: Create CoinGecko price fetcher
```python
# trading/coingecko_client.py
import requests
import logging

logger = logging.getLogger(__name__)

class CoinGeckoClient:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    SYMBOL_MAP = {
        "BTCUSD": "bitcoin",
        "ETHUSD": "ethereum",
        "LTCUSD": "litecoin",
        "XAUUSD": "pax-gold",  # Gold-backed token
    }
    
    @classmethod
    async def get_price(cls, symbol):
        """Get current price for a symbol"""
        coin_id = cls.SYMBOL_MAP.get(symbol)
        if not coin_id:
            return None
            
        try:
            url = f"{cls.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if coin_id in data:
                return {
                    "symbol": symbol,
                    "price": data[coin_id]["usd"],
                    "change_24h": data[coin_id].get("usd_24h_change", 0)
                }
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    @classmethod
    async def get_historical_data(cls, symbol, days=1):
        """Get historical price data for charts"""
        coin_id = cls.SYMBOL_MAP.get(symbol)
        if not coin_id:
            return None
            
        try:
            url = f"{cls.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "hourly" if days > 1 else "minutely"
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            return data.get("prices", [])
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
```

### Step 3: Update WebSocket consumer
Replace Binance WebSocket with CoinGecko polling in `trading/consumers.py`

---

## 🚀 Temporary Fix: Mock Data

Until you implement a new API, I can add mock/demo data so your site works:

```python
# Mock prices for demo
MOCK_PRICES = {
    "BTCUSD": 95234.50,
    "ETHUSD": 3456.78,
    "LTCUSD": 145.23,
    "XAUUSD": 2345.67,
}
```

This will:
- ✅ Show prices on dashboard
- ✅ Display charts with sample data
- ✅ Allow users to test the platform
- ✅ Work immediately

---

## 📊 What I Recommend:

### Immediate (Today):
1. Add mock data to show prices
2. Display "Demo Mode" notice
3. Site works for testing

### Short-term (This Week):
1. Implement CoinGecko API
2. Real prices from CoinGecko
3. Remove "Demo Mode" notice

### Long-term (Future):
1. Get Binance.US API keys (if targeting US)
2. Or use professional API (CryptoCompare, Twelve Data)
3. Add multiple data sources for redundancy

---

## 🎯 Next Steps:

**Choose one:**

1. **Quick Fix (5 minutes):** I'll add mock data so site works now
2. **Real Fix (30 minutes):** I'll implement CoinGecko API for real prices
3. **Professional Fix (1 hour):** Set up CryptoCompare with WebSocket

**Which would you like me to do?**

---

## 📞 Need Help?

The issue is clear: Binance blocks your AWS region. You need an alternative data source.

**My recommendation:** Let me implement CoinGecko API (Option 2) - it's free, reliable, and works everywhere.

Would you like me to proceed with CoinGecko implementation?
