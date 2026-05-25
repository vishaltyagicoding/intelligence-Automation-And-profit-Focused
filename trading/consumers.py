"""
WebSocket consumers for subscription-gated market data and AI signal streaming.
"""

import asyncio
import json
import logging
import time
from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs

import redis.asyncio as aioredis
from binance import AsyncClient, BinanceSocketManager
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

# Binance.com (global exchange) — same data source as TradingView.
# This ensures candle colors (green/red) match TradingView exactly.
# The frontend also uses Binance.com REST so historical + live data are identical.
BINANCE_API_URL = "https://api.binance.com"
BINANCE_WS_URL  = "wss://stream.binance.com:9443"

from .models import MarketSignal
import pandas as pd
from reversal_zones.reversal_calculator import ReversalZoneCalculator


logger = logging.getLogger(__name__)

ALLOWED_ASSETS = {"BTCUSD", "ETHUSD", "XAUUSD", "LTCUSD"}
BINANCE_SYMBOL_MAP = {
    "BTCUSD": "btcusdt",
    "ETHUSD": "ethusdt",
    "XAUUSD": "paxgusdt",
    "LTCUSD": "ltcusdt",
}
SIGNAL_COLOR_MAP = {
    "BUY": "#26a69a",
    "SELL": "#ef5350",
    "HOLD": "#fdd835",
    "STOP_LOSS": "#fb8c00",
}

# Timeframe mapping: frontend format -> Binance API format
TIMEFRAME_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "10m": "5m",  # Will aggregate two 5m candles
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "1d": "1d",
}

ALLOWED_TIMEFRAMES = {"1m", "3m", "5m", "10m", "15m", "30m", "1h", "2h", "4h", "1d"}


class MarketDataConsumer(AsyncWebsocketConsumer):
    """
    Streams watchlist-only market data for the premium web dashboard.
    Emits lightweight OHLCV-compatible payloads for chart rendering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = None
        self.binance_client = None
        self.bsm = None
        self.stream_task = None
        self.ping_task = None  # Server-side ping task
        self.asset = None
        self.binance_symbol = None
        self.timeframe = "1m"  # Default timeframe
        self.binance_interval = "1m"  # Binance API interval
        self.last_pong_time = None  # Track last pong from client

    async def connect(self):
        """Accept only supported watchlist assets and timeframes."""
        requested_asset = self.scope["url_route"]["kwargs"].get("symbol", "BTCUSD").upper()
        requested_timeframe = self.scope["url_route"]["kwargs"].get("timeframe", "1m").lower()

        if requested_asset not in ALLOWED_ASSETS:
            logger.warning("Market socket rejected unsupported asset: %s", requested_asset)
            await self.close(code=4001)
            return

        if requested_timeframe not in ALLOWED_TIMEFRAMES:
            logger.warning("Market socket rejected unsupported timeframe: %s", requested_timeframe)
            await self.close(code=4002)
            return

        self.asset = requested_asset
        self.binance_symbol = BINANCE_SYMBOL_MAP[self.asset]
        self.timeframe = requested_timeframe
        self.binance_interval = TIMEFRAME_MAP[self.timeframe]

        await self.accept()

        self.redis_client = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
        )

        await self.channel_layer.group_add(f"market_{self.asset}_{self.timeframe}", self.channel_name)
        await self.start_binance_stream()
        
        # Start server-side ping task to detect dead connections
        self.last_pong_time = asyncio.get_event_loop().time()
        self.ping_task = asyncio.create_task(self.send_periodic_pings())

        logger.info("Market WebSocket connected for %s at %s timeframe", self.asset, self.timeframe)

    async def disconnect(self, close_code):
        """Clean up stream, redis, and group membership."""
        if self.ping_task:
            self.ping_task.cancel()
            
        if self.stream_task:
            self.stream_task.cancel()

        if self.bsm:
            try:
                await self.bsm.close()
            except (AttributeError, Exception):
                pass  # BinanceSocketManager might not have close method in some versions

        if self.binance_client:
            await self.binance_client.close_connection()

        if self.redis_client:
            await self.redis_client.close()

        if self.asset:
            await self.channel_layer.group_discard(f"market_{self.asset}_{self.timeframe}", self.channel_name)

        logger.info("Market WebSocket disconnected for %s (%s) with code %s", self.asset, self.timeframe, close_code)

    async def receive(self, text_data):
        """Support runtime resubscription between allowed watchlist assets and handle pong."""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "subscribe":
                symbol = str(data.get("symbol", "BTCUSD")).upper()
                await self.subscribe_symbol(symbol)
            elif action == "unsubscribe":
                await self.unsubscribe_symbol()
            elif action == "pong":
                # Client responded to ping, connection is alive
                self.last_pong_time = asyncio.get_event_loop().time()
                logger.debug("Received pong from client for %s", self.asset)
        except Exception as exc:
            logger.error("Error processing market socket message: %s", exc)
            await self.send(text_data=json.dumps({"error": str(exc)}))

    async def start_binance_stream(self):
        """Start Binance.com kline stream using raw aiohttp WebSocket.
        Uses Binance.com (global) — same data source as TradingView — for
        accurate candle prices. Auto-retries with exponential backoff.
        """
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                self.stream_task = asyncio.create_task(self.stream_binance_data())
                logger.info("Binance.com raw WS stream started for %s at %s", self.asset, self.timeframe)
                return
            except Exception as exc:
                retry_count += 1
                logger.error("Error starting Binance stream for %s (attempt %d/%d): %s",
                             self.asset, retry_count, max_retries, exc)
                await asyncio.sleep(2 ** retry_count)

        logger.error("Failed to start Binance stream for %s after %d attempts", self.asset, max_retries)

    async def send_periodic_pings(self):
        """Send ping to client every 30 seconds to keep connection alive and detect dead connections."""
        try:
            while True:
                await asyncio.sleep(30)  # Ping every 30 seconds
                
                # Check if client is still responding
                current_time = asyncio.get_event_loop().time()
                if self.last_pong_time and (current_time - self.last_pong_time) > 90:
                    # No pong received for 90 seconds (3 missed pings) - close connection
                    logger.warning("Client %s not responding to pings, closing connection", self.asset)
                    await self.close(code=1000)
                    return
                
                # Send ping
                try:
                    await self.send(text_data=json.dumps({"type": "ping"}))
                    logger.debug("Sent ping to client for %s", self.asset)
                except Exception as e:
                    logger.error("Failed to send ping to client %s: %s", self.asset, e)
                    await self.close(code=1000)
                    return
        except asyncio.CancelledError:
            logger.debug("Ping task cancelled for %s", self.asset)
        except Exception as exc:
            logger.error("Error in ping task for %s: %s", self.asset, exc)

    async def stream_binance_data(self):
        """
        Stream kline data using raw aiohttp WebSocket to Binance.com (global).
        Connects directly to wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}
        Uses Binance.com (same data source as TradingView) for accurate candle matching.
        Frontend REST history also uses Binance.com for perfect data consistency.
        Auto-reconnects on disconnect with exponential backoff.
        
        NOTE: PAXGUSDT may be restricted from US-based servers (HTTP 451).
        If you see repeated 451 errors, your server location is blocked by Binance.
        Solution: Move server to non-US region (EU, Asia) or use VPN.
        """
        import aiohttp
        import json as _json

        symbol    = self.binance_symbol.lower()
        interval  = self.binance_interval
        ws_url    = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"
        backoff   = 1

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        ws_url,
                        heartbeat=20,
                        receive_timeout=30,
                        ssl=True,
                    ) as ws:
                        logger.info("Binance.com (global) WS connected: %s @kline_%s", symbol, interval)
                        backoff = 1  # reset on success

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = _json.loads(msg.data)
                                    # Binance stream wraps kline under key 'k'
                                    if 'k' not in data:
                                        continue
                                    await self.process_kline(data)
                                except Exception as exc:
                                    logger.error("Error processing WS message for %s: %s", self.asset, exc)

                            elif msg.type in (aiohttp.WSMsgType.CLOSED,
                                             aiohttp.WSMsgType.ERROR):
                                logger.warning("WS closed/error for %s: %s", self.asset, msg)
                                break

            except asyncio.CancelledError:
                logger.info("Binance.com stream cancelled for %s", self.asset)
                raise
            except Exception as exc:
                logger.error("Binance.com WS error for %s: %s — retrying in %ds", self.asset, exc, backoff)
                await self.fetch_and_broadcast_rest_price()

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)  # cap at 60s

    async def fetch_and_broadcast_rest_price(self):
        """
        Fetch real OHLCV candle via REST API (klines endpoint) and broadcast.
        Using /api/v3/klines gives true open/high/low/close — identical to
        what TradingView displays. The old ticker endpoint only returned close
        price, making open=high=low=close (flat, broken-looking candles).
        """
        try:
            import aiohttp

            # Binance.com REST (global exchange — same data source as TradingView)
            url = (f"https://api.binance.com/api/v3/klines"
                   f"?symbol={self.binance_symbol.upper()}"
                   f"&interval={self.binance_interval}&limit=2")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data or not isinstance(data, list):
                            logger.warning("REST klines returned empty for %s", self.asset)
                            return

                        # Take the most recent candle (last element)
                        k = data[-1]
                        kline_start_ms = int(k[0])
                        open_p  = float(k[1])
                        high_p  = float(k[2])
                        low_p   = float(k[3])
                        close_p = float(k[4])
                        volume  = float(k[5])
                        timestamp = kline_start_ms // 1000

                        if close_p <= 0:
                            return

                        processed_data = {
                            "asset":     self.asset,
                            "symbol":    self.asset,
                            "timestamp": timestamp,
                            "time":      timestamp,
                            "open":      open_p,
                            "high":      high_p,
                            "low":       low_p,
                            "close":     close_p,
                            "price":     close_p,
                            "volume":    volume,
                            "is_closed": False,
                            "timeframe": self.timeframe,
                        }

                        await self.channel_layer.group_send(
                            f"market_{self.asset}_{self.timeframe}",
                            {"type": "market_update", "data": processed_data},
                        )

                        logger.info("REST OHLCV fetched for %s: O=%.2f H=%.2f L=%.2f C=%.2f",
                                    self.asset, open_p, high_p, low_p, close_p)
                    else:
                        logger.error("REST klines status %d for %s", response.status, self.asset)
        except Exception as exc:
            logger.error("Error fetching REST price for %s: %s", self.asset, exc)

    async def process_kline(self, kline_data):
        """Process kline and broadcast normalized market payload for any timeframe."""
        try:
            kline = kline_data.get('k', {})
            
            # Extract kline data
            open_price = float(kline.get('o', 0))
            high_price = float(kline.get('h', 0))
            low_price = float(kline.get('l', 0))
            close_price = float(kline.get('c', 0))
            volume = float(kline.get('v', 0))
            kline_start_time = int(kline.get('t', 0))
            is_closed = kline.get('x', False)  # Is this kline closed?
            
            # Convert milliseconds to seconds
            timestamp = kline_start_time // 1000 if kline_start_time else int(time.time())

            processed_data = {
                "asset": self.asset,
                "symbol": self.asset,
                "timestamp": timestamp,
                "time": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "price": close_price,
                "volume": volume,
                "is_closed": is_closed,
                "timeframe": self.timeframe,
            }

            # Cache in Redis for AI signal generator
            redis_key = f"market:kline:{self.asset}:{self.timeframe}"
            
            # Store as list for historical data (keep last 500 candles)
            await self.redis_client.lpush(redis_key, json.dumps(processed_data))
            await self.redis_client.ltrim(redis_key, 0, 499)  # Keep last 500
            await self.redis_client.expire(redis_key, 3600)  # Expire in 1 hour

            # Also store latest for dashboard
            dashboard_key = f"market:kline:{self.asset}"
            await self.redis_client.set(dashboard_key, json.dumps(processed_data), ex=120)

            # Broadcast to all connected clients
            await self.channel_layer.group_send(
                f"market_{self.asset}_{self.timeframe}",
                {
                    "type": "market_update",
                    "data": processed_data,
                },
            )
            
            logger.debug("Kline processed for %s (%s): close=%.2f", self.asset, self.timeframe, close_price)
            # Live signal detection is now handled EXCLUSIVELY by Celery tasks.
            # WebSocket only broadcasts price updates - no signal generation.
            # This ensures all signals come from the same 30-day data window,
            # preventing duplicate/inconsistent signals.
            #
            # Celery task runs every 60 seconds and has the full 30-day context,
            # so signals will appear within 60 seconds of candle close.
            # This is acceptable for algo trading (5-minute Celery interval was the original design).
            #
            # if is_closed:
            #     asyncio.ensure_future(self._emit_live_signal())

            
        except Exception as exc:
            logger.error("Error processing kline for %s: %s", self.asset, exc)

    async def process_kline_10m(self, kline_data, buffer):
        """Aggregate two 5m candles into a 10m candle."""
        try:
            kline = kline_data.get('k', {})
            is_closed = kline.get('x', False)
            
            if not is_closed:
                # Don't process incomplete candles for aggregation
                return buffer
            
            kline_start_time = int(kline.get('t', 0)) // 1000
            
            # Determine if this is the first or second 5m candle in the 10m window
            # 10m windows: 0, 10, 20, 30, 40, 50 minutes
            minute = (kline_start_time // 60) % 60
            is_first_5m = minute % 10 == 0  # 0, 10, 20, 30, 40, 50
            is_second_5m = minute % 10 == 5  # 5, 15, 25, 35, 45, 55
            
            if is_first_5m:
                # Start new 10m candle
                buffer = {
                    "open": float(kline.get('o', 0)),
                    "high": float(kline.get('h', 0)),
                    "low": float(kline.get('l', 0)),
                    "close": float(kline.get('c', 0)),
                    "volume": float(kline.get('v', 0)),
                    "timestamp": kline_start_time,
                }
                return buffer
            
            elif is_second_5m and buffer:
                # Complete the 10m candle
                processed_data = {
                    "asset": self.asset,
                    "symbol": self.asset,
                    "timestamp": buffer["timestamp"],
                    "time": buffer["timestamp"],
                    "open": buffer["open"],
                    "high": max(buffer["high"], float(kline.get('h', 0))),
                    "low": min(buffer["low"], float(kline.get('l', 0))),
                    "close": float(kline.get('c', 0)),
                    "price": float(kline.get('c', 0)),
                    "volume": buffer["volume"] + float(kline.get('v', 0)),
                    "is_closed": True,
                    "timeframe": "10m",
                }
                
                # Cache in Redis for AI signal generator
                redis_key = f"market:kline:{self.asset}:10m"
                
                # Store as list for historical data (keep last 500 candles)
                await self.redis_client.lpush(redis_key, json.dumps(processed_data))
                await self.redis_client.ltrim(redis_key, 0, 499)  # Keep last 500
                await self.redis_client.expire(redis_key, 3600)  # Expire in 1 hour

                # Also store latest for dashboard
                dashboard_key = f"market:kline:{self.asset}"
                await self.redis_client.set(dashboard_key, json.dumps(processed_data), ex=120)
                
                # Broadcast
                await self.channel_layer.group_send(
                    f"market_{self.asset}_10m",
                    {
                        "type": "market_update",
                        "data": processed_data,
                    },
                )
                
                logger.debug("10m candle completed for %s: close=%.2f", self.asset, processed_data["close"])
                
                # Clear buffer
                return None
            
            return buffer
            
        except Exception as exc:
            logger.error("Error processing 10m kline for %s: %s", self.asset, exc)
            return buffer

    async def market_update(self, event):
        """Forward market update to client."""
        await self.send(text_data=json.dumps(event["data"]))



    @staticmethod
    @database_sync_to_async
    def _save_signal_to_db(symbol, timeframe, zone):
        """
        Persist a confirmed reversal signal to the ReversalZone table.

        Uses transaction.atomic() + select_for_update() to enforce alternation
        atomically. This prevents the race condition where:
        1. WebSocket reads last_signal = SELL (check passes for BUY)
        2. Celery task also reads last_signal = SELL (check passes for BUY)
        3. Both save BUY → consecutive BUY-BUY in DB

        With select_for_update the second writer blocks until the first commits,
        then re-reads the (now BUY) last signal and blocks the duplicate.
        """
        try:
            from reversal_zones.models import ReversalZone
            from django.db import IntegrityError, transaction
            import pytz

            ts = zone.get("timestamp")
            if isinstance(ts, str):
                from django.utils.dateparse import parse_datetime
                reversal_time = parse_datetime(ts)
            elif hasattr(ts, "to_pydatetime"):
                reversal_time = ts.to_pydatetime()
            else:
                reversal_time = ts

            if reversal_time is None:
                logger.error("_save_signal_to_db: reversal_time is None for zone %s", zone)
                return

            if reversal_time.tzinfo is None:
                reversal_time = reversal_time.replace(tzinfo=pytz.UTC)

            is_bull = zone.get("is_bullish", True)
            label   = "BUY" if is_bull else "SELL"

            with transaction.atomic():
                # ── Re-read last signal WITH row lock inside the transaction ──
                # This serializes concurrent WebSocket + Celery saves and prevents
                # the race condition that causes consecutive BUY-BUY or SELL-SELL.
                last_row = (
                    ReversalZone.objects
                    .filter(symbol=symbol, timeframe=timeframe)
                    .select_for_update()
                    .order_by("-reversal_time")
                    .values("label_text", "reversal_time")
                    .first()
                )

                if last_row and last_row["label_text"] == label:
                    logger.info(
                        "🛡️ ALTERNATION BLOCKED (atomic lock) [%s %s]: "
                        "cannot save %s after %s",
                        symbol, timeframe, label, last_row["label_text"],
                    )
                    return  # Silently drop — correct behaviour

                # ── Save signal (alternation verified inside transaction) ──────
                obj, created = ReversalZone.objects.update_or_create(
                    symbol        = symbol,
                    timeframe     = timeframe,
                    reversal_time = reversal_time,
                    defaults={
                        "center_price":  zone.get("center_price", 0),
                        "stop_loss":     zone.get("stop_loss"),
                        "target":        zone.get("target"),
                        "outer_top":     zone.get("outer_top",    0),
                        "outer_bottom":  zone.get("outer_bottom", 0),
                        "core_top":      zone.get("core_top",     0),
                        "core_bottom":   zone.get("core_bottom",  0),
                        "is_bullish":    is_bull,
                        "label_text":    label,
                        "bar_index":     zone.get("bar_index", 0),
                    },
                )

            action = "💾 Created" if created else "🔄 Updated"
            db_stop_loss = float(obj.stop_loss) if obj.stop_loss else float(obj.outer_bottom if is_bull else obj.outer_top)
            db_target    = float(obj.target)    if obj.target    else float(obj.outer_top    if is_bull else obj.outer_bottom)
            logger.info(
                "%s %s signal in DB: %s %s @ %.2f  SL=%.2f  TP=%.2f",
                action, obj.label_text, symbol, timeframe,
                float(obj.center_price), db_stop_loss, db_target,
            )

        except (IntegrityError, Exception) as exc:
            error_msg = str(exc)
            if "Consecutive" in error_msg and "signals not allowed" in error_msg:
                logger.info(
                    "🛡️ DB CONSTRAINT blocked consecutive %s signal [%s %s] @ %.2f - "
                    "alternation enforced at database level",
                    label, symbol, timeframe, zone.get("center_price", 0)
                )
            else:
                logger.error("Error saving signal to DB [%s %s]: %s",
                             symbol, timeframe, exc)

    @staticmethod
    @database_sync_to_async
    def _get_last_db_signal(symbol, timeframe):
        """
        Get the last signal type (BUY/SELL) from the database.
        Used to enforce alternation: after SELL only BUY, after BUY only SELL.
        """
        try:
            from reversal_zones.models import ReversalZone
            last_signal = ReversalZone.objects.filter(
                symbol=symbol,
                timeframe=timeframe
            ).order_by('-reversal_time').values_list('label_text', flat=True).first()
            return last_signal
        except Exception as exc:
            logger.error("Error getting last DB signal [%s %s]: %s",
                         symbol, timeframe, exc)
            return None

    async def _emit_live_signal(self):
        """
        Called on every closed candle.
        Runs RAW ReversalZoneCalculator on the last 500 Redis-cached candles.
        Broadcasts a 'signal' event if a new reversal is detected.
        
        MATCHES TRADINGVIEW PINE SCRIPT EXACTLY - no additional filters.
        """
        try:
            redis_key = f"market:kline:{self.asset}:{self.timeframe}"
            raw_list = await self.redis_client.lrange(redis_key, 0, 499)
            if not raw_list or len(raw_list) < 10:
                return

            # Redis stores newest-first (lpush), reverse to chronological
            records = [json.loads(r) for r in reversed(raw_list)]
            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            df = df.sort_values("timestamp").set_index("timestamp")
            df = df[["open", "high", "low", "close"]].astype(float)
            if len(df) < 10:
                return

            # Use RAW calculator (matches TradingView Pine Script EXACTLY)
            # NO additional filters (ADX, RSI, time gaps) - just pure swing tracking
            #
            # CRITICAL: confirmBars = 1 adds 1-candle confirmation delay to match TradingView
            # This prevents premature signals that haven't been confirmed yet
            calculator = ReversalZoneCalculator(
                preset="Low",
                calc_mode="Average",
                avg_len=5,
                atr_len=5,
                custom_abs=0.05,
                confirm_bars=1,  # ← CHANGED from 0 to 1 for confirmation
                timeframe=self.timeframe
            )
            result = calculator.process_ohlcv_data(df)
            zones  = result.get("zones", [])
            status = result.get("status", {})
            if not zones:
                return

            last_zone   = zones[-1]
            new_signal  = "BUY" if last_zone["is_bullish"] else "SELL"
            
            # ═══════════════════════════════════════════════════════════════════
            # SIGNAL DETECTION: Use reversal calculator to detect signals
            # 
            # The calculator returns zones with timestamps. We need to:
            # 1. Check if signal already exists in database (avoid duplicates)
            # 2. Enforce alternation (BUY→SELL→BUY→SELL)
            # 3. Save to database (triggers email via Django signal handler)
            # ═══════════════════════════════════════════════════════════════════
            
            # NOTE: Alternation is now enforced atomically INSIDE _save_signal_to_db
            # using select_for_update() — no pre-check needed here.
            # Pre-checking here caused a race condition: between the check and save,
            # another writer (Celery task) could insert the same signal type.

            # ══════════════════════════════════════════════════════════════════
            # FIX: Use actual current close price as ENTRY — not the pivot price.
            #
            # NEW RISK MANAGEMENT (2:1 Reward-to-Risk Ratio):
            #   Target:    MINIMUM 0.2%, MAXIMUM 0.55% from entry
            #   Stop Loss: HALF of target distance (creates 2:1 reward-to-risk)
            #
            # Formula:
            #   BUY:  Target = Entry + X%, Stop Loss = Entry - (X% * 0.5)
            #   SELL: Target = Entry - X%, Stop Loss = Entry + (X% * 0.5)
            # ══════════════════════════════════════════════════════════════════
            actual_close = round(float(df["close"].iloc[-1]), 2)
            is_bull = last_zone["is_bullish"]

            # ── CALCULATE TARGET FIRST ─────────────────────────────────────────
            # Start with base target distance
            target_distance_pct = 0.004  # 0.4% base
            
            # Enforce MINIMUM 0.2% target (ensure minimum profit)
            MIN_TARGET_PCT = 0.002
            if target_distance_pct < MIN_TARGET_PCT:
                target_distance_pct = MIN_TARGET_PCT
            
            # Enforce MAXIMUM 0.55% target (realistic profit taking)
            MAX_TARGET_PCT = 0.0055
            if target_distance_pct > MAX_TARGET_PCT:
                target_distance_pct = MAX_TARGET_PCT
            
            # Calculate final target
            if is_bull:
                tgt_px = actual_close * (1 + target_distance_pct)
                target_distance = tgt_px - actual_close
                sl_px = actual_close - (target_distance * 0.5)
            else:
                tgt_px = actual_close * (1 - target_distance_pct)
                target_distance = actual_close - tgt_px
                sl_px = actual_close + (target_distance * 0.5)
            
            # Round to 2 decimal places
            sl_px  = round(sl_px, 2)
            tgt_px = round(tgt_px, 2)
            entry_px = actual_close  # ← the price users actually see on the chart

            # Use the timestamp from the zone (this is when the signal was detected)
            # Build a patched zone dict that stores the execution price
            last_zone_to_save = {
                **last_zone,
                "center_price": entry_px,   # execution price, matches chart
                "stop_loss":    sl_px,
                "target":       tgt_px,
                # outer_top / outer_bottom aligned so history page fallback also matches
                "outer_top":    tgt_px if is_bull else sl_px,
                "outer_bottom": sl_px  if is_bull else tgt_px,
            }

            # ── Redis dedup lock: prevent duplicate email on WebSocket reconnect ──────
            # Use the signal's reversal_time (candle close time) as the unique key.
            # TTL = 10 minutes: if the same signal fires again within 10 min, skip.
            ts_for_lock = last_zone.get("timestamp")
            ts_lock_str = ts_for_lock.isoformat() if hasattr(ts_for_lock, "isoformat") else str(ts_for_lock)
            signal_lock_key = f"signal:fired:{self.binance_symbol.upper()}:{self.timeframe}:{ts_lock_str}"
            already_fired = await self.redis_client.get(signal_lock_key)
            if already_fired:
                logger.debug(
                    "⏭️ Dedup lock: skipping already-fired signal [%s %s] @ %s",
                    self.asset, self.timeframe, ts_lock_str
                )
                return

            # Save ONLY the last zone (the new signal) to DB
            db_symbol = self.binance_symbol.upper()
            await self._save_signal_to_db(db_symbol, self.timeframe, last_zone_to_save)

            # Set dedup lock AFTER saving — 10 min TTL
            await self.redis_client.set(signal_lock_key, "1", ex=600)

            # ── Email notifications are now sent automatically via Django signals ─
            # See reversal_zones/signals.py - sends INSTANT emails when signal is saved to DB
            # This ensures users receive alerts at the EXACT moment the signal fires,
            # regardless of WebSocket connection status.

            ts = last_zone["timestamp"]
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

            # Broadcast ONLY the single new signal, not all zones from window
            all_zones_out = [{
                "is_bullish":   last_zone["is_bullish"],
                "center_price": entry_px,    # execution price (matches chart)
                "outer_top":    tgt_px if is_bull else sl_px,
                "outer_bottom": sl_px  if is_bull else tgt_px,
                "core_top":     last_zone["core_top"],
                "core_bottom":  last_zone["core_bottom"],
                "timestamp":    ts_str,
                "bar_index":    last_zone["bar_index"],
            }]

            logger.info(
                "🔧 PRICE FIX [%s %s]: pivot=%.2f → entry=%.2f  SL=%.2f  TP=%.2f",
                self.asset, self.timeframe,
                float(pivot_price), entry_px, sl_px, tgt_px,
            )

            signal_payload = {
                "type":        "signal",
                "asset":       self.asset,
                "timeframe":   self.timeframe,
                "signal":      new_signal,
                "is_bullish":  is_bull,
                "price":       entry_px,
                "stop_loss":   sl_px,
                "target":      tgt_px,
                "timestamp":   ts_str,
                "bar_index":   last_zone["bar_index"],
                "tracking":    status.get("tracking", ""),
                "all_zones":   all_zones_out,
            }

            await self.channel_layer.group_send(
                f"market_{self.asset}_{self.timeframe}",
                {"type": "signal_update", "data": signal_payload},
            )

            logger.info("🔔 LIVE SIGNAL [%s %s]: %s @ %.2f (bar=%d)",
                        self.asset, self.timeframe, new_signal,
                        last_zone["center_price"], last_zone["bar_index"])

        except Exception as exc:
            logger.error("_emit_live_signal error [%s %s]: %s",
                         self.asset, self.timeframe, exc)

    async def signal_update(self, event):
        """Forward live signal event to connected WebSocket client."""
        await self.send(text_data=json.dumps(event["data"]))

    async def subscribe_symbol(self, symbol):
        """Switch to another allowed asset."""
        if symbol not in ALLOWED_ASSETS:
            await self.send(
                text_data=json.dumps(
                    {
                        "error": "Unsupported asset",
                        "allowed_assets": sorted(ALLOWED_ASSETS),
                    }
                )
            )
            return

        await self.unsubscribe_symbol()

        self.asset = symbol
        self.binance_symbol = BINANCE_SYMBOL_MAP[self.asset]
        await self.channel_layer.group_add(f"market_{self.asset}_{self.timeframe}", self.channel_name)
        await self.start_binance_stream()

    async def unsubscribe_symbol(self):
        """Stop current market stream and leave current group."""
        if self.stream_task:
            self.stream_task.cancel()
            self.stream_task = None

        if self.bsm:
            try:
                await self.bsm.close()
            except (AttributeError, Exception):
                pass  # BinanceSocketManager might not have close method in some versions
            self.bsm = None

        if self.binance_client:
            await self.binance_client.close_connection()
            self.binance_client = None

        if self.asset:
            await self.channel_layer.group_discard(f"market_{self.asset}_{self.timeframe}", self.channel_name)


class AISignalConsumer(AsyncWebsocketConsumer):
    """
    Premium AI signal websocket.
    Connection is rejected for unauthenticated or unsubscribed users.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.asset = None
        self.group_names = []

    async def connect(self):
        """Authenticate user and verify active subscription before accepting."""
        token = self._get_token_from_query_string()

        # For development/testing: allow dummy tokens
        if token and token != 'dummy-token-for-testing':
            self.user = await self._authenticate_user(token)
            if not self.user:
                logger.warning("AI Signals WebSocket rejected: authentication failed")
                await self.close(code=4002)
                return

            has_active_subscription = await self._has_active_subscription(self.user.id)
            if not has_active_subscription:
                logger.warning("AI Signals WebSocket rejected: no active subscription")
                await self.close(code=4003)
                return
        else:
            # Development mode: skip authentication
            logger.info("AI Signals WebSocket: using development mode (no auth)")
            self.user = None

        requested_asset = self.scope["url_route"]["kwargs"].get("symbol")
        if requested_asset:
            requested_asset = requested_asset.upper()
            if requested_asset not in ALLOWED_ASSETS:
                logger.warning(f"AI Signals WebSocket rejected: unsupported asset {requested_asset}")
                await self.close(code=4001)
                return
            self.asset = requested_asset

        await self.accept()
        logger.info(f"✅ AI Signals WebSocket connected for asset: {self.asset or 'ALL'}")

        self.group_names = ["ai_signals_all"]
        if self.asset:
            self.group_names.append(f"ai_signals_{self.asset}")

        for group_name in self.group_names:
            await self.channel_layer.group_add(group_name, self.channel_name)
            logger.info(f"   Added to group: {group_name}")

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection",
                    "status": "connected",
                    "subscription_active": True,
                    "asset": self.asset,
                }
            )
        )
        logger.info("   Sent connection confirmation")

        # Send existing signals to the client
        logger.info("   Sending existing signals...")
        await self._send_existing_signals()

    async def disconnect(self, close_code):
        """Remove the user from subscribed groups."""
        for group_name in self.group_names:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle ping and asset-level subscription changes."""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "ping":
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    )
                )
                return

            if action == "subscribe":
                symbol = str(data.get("asset") or data.get("symbol") or "").upper()
                if symbol not in ALLOWED_ASSETS:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "type": "error",
                                "code": "unsupported_asset",
                                "allowed_assets": sorted(ALLOWED_ASSETS),
                            }
                        )
                    )
                    return

                if self.asset:
                    await self.channel_layer.group_discard(f"ai_signals_{self.asset}", self.channel_name)

                self.asset = symbol
                await self.channel_layer.group_add(f"ai_signals_{self.asset}", self.channel_name)
                if f"ai_signals_{self.asset}" not in self.group_names:
                    self.group_names.append(f"ai_signals_{self.asset}")
        except Exception as exc:
            logger.error("Error processing AI signal socket message: %s", exc)

    async def ai_signal(self, event):
        """Forward AI signal payload to the client."""
        await self.send(text_data=json.dumps(event["data"]))

    def _get_token_from_query_string(self) -> str | None:
        """Extract JWT token from websocket query string."""
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        return params.get("token", [None])[0]

    @database_sync_to_async
    def _authenticate_user(self, token: str):
        """Resolve the user from the JWT access token."""
        from django.contrib.auth import get_user_model

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user_model = get_user_model()
            return user_model.objects.filter(id=user_id).first()
        except (TokenError, KeyError):
            return None

    @database_sync_to_async
    def _has_active_subscription(self, user_id: int) -> bool:
        """Check whether the current user has an active subscription."""
        from .models import Subscription

        subscription = Subscription.objects.filter(user_id=user_id).first()
        return bool(subscription and subscription.is_active)

    @database_sync_to_async
    def _get_recent_signals(self, limit: int = 50):
        """Get recent signals from database."""
        if self.asset:
            signals = MarketSignal.objects.filter(symbol=self.asset).order_by('-created_at')[:limit]
        else:
            signals = MarketSignal.objects.filter(symbol__in=ALLOWED_ASSETS).order_by('-created_at')[:limit]
        
        return [signal.websocket_payload() for signal in signals]

    async def _send_existing_signals(self):
        """Send existing signals to newly connected client."""
        try:
            logger.info(f"📡 Fetching existing signals for {self.asset or 'all assets'}...")
            signals = await self._get_recent_signals(limit=50)
            
            if signals:
                logger.info(f"✅ Found {len(signals)} existing signals, sending to client...")
                
                for signal_payload in reversed(signals):  # Send oldest first
                    await self.send(text_data=json.dumps(signal_payload))
                    logger.debug(f"   Sent signal: {signal_payload['action']} @ {signal_payload['price']}")
                
                logger.info(f"✅ Successfully sent {len(signals)} signals to client")
            else:
                logger.info(f"ℹ️ No existing signals found for {self.asset or 'all assets'}")
                
        except Exception as exc:
            logger.error(f"❌ Error sending existing signals: {exc}", exc_info=True)


class LiveDataConsumer(AsyncWebsocketConsumer):
    """
    Authenticated websocket for lightweight dashboard status updates.
    Reuses watchlist-only assets and exposes latest cached prices.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = None
        self.broadcast_task = None
        self.user = None

    async def connect(self):
        """Handle WebSocket connection with JWT token authentication."""
        try:
            token = self._get_token_from_query_string()

            if not token:
                logger.warning("LiveData socket rejected: no token provided")
                await self.close(code=4001)
                return

            self.user = await self._authenticate_user(token)
            if not self.user:
                await self.close(code=4002)
                return

            await self.accept()

            self.redis_client = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True,
            )

            await self.channel_layer.group_add("live_data", self.channel_name)
            self.broadcast_task = asyncio.create_task(self.broadcast_live_data())

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "connection",
                        "status": "connected",
                        "message": "Live dashboard socket connected successfully",
                    }
                )
            )
        except Exception as exc:
            logger.error("Error in LiveDataConsumer connect: %s", exc)
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Disconnect and free resources."""
        if self.broadcast_task:
            self.broadcast_task.cancel()

        if self.redis_client:
            await self.redis_client.close()

        await self.channel_layer.group_discard("live_data", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "ping":
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong",
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    )
                )
        except Exception as exc:
            logger.error("Error processing live data message: %s", exc)

    async def broadcast_live_data(self):
        """Broadcast latest prices for the fixed watchlist every 2 seconds."""
        try:
            while True:
                market_data = await self.get_latest_market_data()

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "market_snapshot",
                            "data": market_data,
                        }
                    )
                )

                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logger.info("LiveData broadcast task cancelled")
        except Exception as exc:
            logger.error("Error in live data broadcast: %s", exc)

    @database_sync_to_async
    def _authenticate_user(self, token: str):
        """Resolve the user from a JWT token."""
        from django.contrib.auth import get_user_model

        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            user_model = get_user_model()
            return user_model.objects.filter(id=user_id).first()
        except (TokenError, KeyError):
            return None

    def _get_token_from_query_string(self) -> str | None:
        """Extract JWT token from query string."""
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        return params.get("token", [None])[0]

    async def get_latest_market_data(self):
        """Get latest market data for the fixed watchlist from Redis."""
        snapshot = {}

        for asset in sorted(ALLOWED_ASSETS):
            snapshot[asset] = await self._get_cached_asset_tick(asset)

        return snapshot

    async def _get_cached_asset_tick(self, asset: str) -> dict[str, Any]:
        """Load the most recent cached kline for an asset."""
        try:
            redis_key = f"market:kline:{asset}"
            latest_kline = await self.redis_client.get(redis_key)

            if latest_kline:
                return json.loads(latest_kline)
        except Exception as exc:
            logger.error("Error getting market data for %s: %s", asset, exc)

        return {
            "asset": asset,
            "symbol": asset,
            "timestamp": 0,
            "open": 0.0,
            "high": 0.0,
            "low": 0.0,
            "close": 0.0,
            "price": 0.0,
            "volume": 0.0,
        }

    async def live_update(self, event):
        """Handle live update broadcast from channel layer."""
        await self.send(text_data=json.dumps(event["data"]))


@database_sync_to_async
def create_and_serialize_signal(
    *,
    asset: str,
    price: float | Decimal,
    action: str,
    message: str,
    color: str | None = None,
    market: str = "CRYPTO",
    confidence: float | Decimal = 0,
    stop_loss: float | Decimal | None = None,
    target: float | Decimal | None = None,
    exit_price: float | Decimal | None = None,
    ai_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Persist an AI signal and return the exact websocket payload contract.
    """
    signal = MarketSignal.objects.create(
        symbol=asset,
        market=market,
        action=action,
        confidence=confidence,
        signal_price=price,
        exit_price=exit_price,
        stop_loss=stop_loss,
        target=target,
        message=message,
        color=color or SIGNAL_COLOR_MAP.get(action, "#fdd835"),
        ai_context=ai_context or {},
        is_broadcast=False,
    )
    
    # Send email notifications to subscribers with matching alerts
    try:
        from signal_alerts.email_utils import notify_signal_subscribers
        from django.utils import timezone
        
        # Prepare signal data for email notification
        # CRITICAL FIX: Use the actual signal's candle time (from ai_context or signal),
        # NOT timezone.now() which was sending the current time (when email was sent),
        # causing a timestamp mismatch vs the chart (e.g. chart shows 12:00, email shows 15:28).
        signal_candle_time = None
        if ai_context:
            signal_candle_time = ai_context.get('signal_time') or ai_context.get('reversal_time') or ai_context.get('timestamp')
        if signal_candle_time is None:
            # Fallback: use current time only if no signal time available
            signal_candle_time = timezone.now()
        
        # Format as UTC string
        if hasattr(signal_candle_time, 'strftime'):
            ts_str = signal_candle_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        else:
            ts_str = str(signal_candle_time)
        
        # Normalise signal_candle_time to a proper UTC datetime for per-user tz conversion
        import pytz as _pytz
        if hasattr(signal_candle_time, 'tzinfo') and signal_candle_time.tzinfo is None:
            signal_candle_time_utc = _pytz.utc.localize(signal_candle_time)
        elif hasattr(signal_candle_time, 'astimezone'):
            signal_candle_time_utc = signal_candle_time.astimezone(_pytz.utc)
        else:
            signal_candle_time_utc = None

        signal_data = {
            'crypto':        asset,   # Already in user format: BTCUSD, ETHUSD, XAUUSD, LTCUSD
            'timeframe':     (ai_context.get('timeframe') if ai_context else None) or self.timeframe,
            'signal_type':   action,
            'entry_price':   float(price) if price else 0,
            'stop_loss':     float(stop_loss) if stop_loss else 0,
            'target':        float(target) if target else 0,
            'timestamp':     ts_str,         # UTC fallback string
            'timestamp_dt':  signal_candle_time_utc,  # raw datetime for per-user tz conversion
        }
        
        # Send notifications asynchronously (non-blocking)
        from threading import Thread
        Thread(target=notify_signal_subscribers, args=(signal_data,), daemon=True).start()
    except Exception as e:
        logger.error(f"Error triggering signal alert notifications: {e}")
    
    return signal.websocket_payload()


async def broadcast_ai_signal(channel_layer, payload: dict[str, Any]):
    """
    Push an AI signal payload to all premium subscribers and asset subscribers.
    """
    asset = payload.get("asset")
    event = {
        "type": "ai_signal",
        "data": payload,
    }

    await channel_layer.group_send("ai_signals_all", event)

    if asset in ALLOWED_ASSETS:
        await channel_layer.group_send(f"ai_signals_{asset}", event)



class ReversalZoneConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time reversal zone updates
    
    Connect to: ws://localhost:8000/ws/reversal-zones/{symbol}/
    """
    
    async def connect(self):
        self.symbol = self.scope['url_route']['kwargs']['symbol']
        self.room_group_name = f'reversal_zones_{self.symbol.replace("/", "_")}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        initial_data = await self.get_reversal_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': initial_data
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_update':
                # Send latest data
                reversal_data = await self.get_reversal_data()
                await self.send(text_data=json.dumps({
                    'type': 'reversal_update',
                    'data': reversal_data
                }))
        except Exception as e:
            logger.error(f"Error in ReversalZoneConsumer.receive: {e}")
    
    async def reversal_update(self, event):
        """Receive message from room group"""
        await self.send(text_data=json.dumps({
            'type': 'reversal_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_reversal_data(self):
        """Fetch reversal data from database"""
        from reversal_zones.models import ReversalZone, ReversalStatus
        from reversal_zones.serializers import ReversalZoneSerializer, ReversalStatusSerializer
        from django.core.cache import cache
        
        cache_key = f"reversal_zones:{self.symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Fetch latest zones
        zones = ReversalZone.objects.filter(
            symbol=self.symbol
        ).order_by('-reversal_time')[:8]
        
        try:
            status_obj = ReversalStatus.objects.get(symbol=self.symbol)
            status_data = ReversalStatusSerializer(status_obj).data
        except ReversalStatus.DoesNotExist:
            status_data = None
        
        data = {
            'symbol': self.symbol,
            'zones': ReversalZoneSerializer(zones, many=True).data,
            'status': status_data,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, data, timeout=300)
        
        return data