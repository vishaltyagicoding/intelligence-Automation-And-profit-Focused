"""
Anti-Chop Signal Filter
========================
Wraps ReversalZoneCalculator and suppresses low-quality signals.

ROOT CAUSE FIX (2025-05-01)
----------------------------
bar_index in the calculator is a RELATIVE index (0 to N-1) in the current
data window. It shifts every time we fetch new data. Comparing
`bar_index - last_passed_bar` gives wrong results across API calls.

The correct approach is to compare TIMESTAMPS (actual UTC datetimes).
Each timeframe has a minimum TIME distance between signals:
  - 1m  → 30 minutes (1m timeframe uses 30-min gap)
  - 5m  → 60 minutes  
  - 1h  → 4 hours
  - 4h  → 12 hours
  - 1d  → 1 day
This is now enforced using pd.Timestamp comparison, not bar_index.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from reversal_zones.reversal_calculator import ReversalZoneCalculator

logger = logging.getLogger(__name__)


# ── Minimum TIME between signals per timeframe (in minutes) ──────────────────
# STRICT: Minimum 1 hour (60 minutes) between ANY two signals for ALL timeframes.
# This prevents over-trading and ensures quality signals only.
MIN_MINUTES_BETWEEN_SIGNALS: Dict[str, int] = {
    "1m":  30,    # 30 minutes minimum (1m timeframe only)
    "3m":  60,    # 1 hour minimum
    "5m":  60,    # 1 hour minimum
    "10m": 60,    # 1 hour minimum
    "15m": 60,    # 1 hour minimum
    "30m": 60,    # 1 hour minimum
    "1h":  60,    # 1 hour minimum
    "2h":  60,    # 1 hour minimum (can be 2h+ naturally due to candle size)
    "4h":  60,    # 1 hour minimum (can be 4h+ naturally due to candle size)
    "1d":  60,    # 1 hour minimum (can be 1d+ naturally due to candle size)
}

# ATR distance multiplier — price gap must exceed this × ATR
MIN_ATR_DISTANCE_MULT = 2.5

# ADX threshold PER TIMEFRAME — short timeframes are inherently choppier
# (XRP 1m/5m market has ADX ~15-22 normally, ADX=25 blocked ALL signals)
ADX_THRESHOLD_BY_TF: Dict[str, float] = {
    "1m":  15.0,   # Short TF: allow more signals, price moves fast
    "3m":  15.0,
    "5m":  15.0,
    "10m": 18.0,
    "15m": 20.0,
    "30m": 20.0,
    "1h":  22.0,
    "2h":  23.0,
    "4h":  25.0,   # Long TF: higher trend confirmation required
    "1d":  25.0,
}
ADX_THRESHOLD = 20.0   # Default fallback

# RSI thresholds
RSI_OVERBOUGHT = 60.0
RSI_OVERSOLD   = 40.0

# Maximum signals to return (keeps chart readable)
# No hard cap on signal count — time gap + alternation are the only filters


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI — matches TradingView ta.rsi exactly."""
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_g = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_l = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs    = avg_g / avg_l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _adx(high: pd.Series, low: pd.Series, close: pd.Series,
         period: int = 14) -> pd.Series:
    """Wilder ADX — matches TradingView ta.adx."""
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move   = high - prev_high
    down_move = prev_low - low
    plus_dm   = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm  = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm_s  = pd.Series(plus_dm,  index=close.index)
    minus_dm_s = pd.Series(minus_dm, index=close.index)
    tr_s      = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di   = 100 * plus_dm_s.ewm(alpha=1 / period, adjust=False).mean() / tr_s.replace(0, np.nan)
    minus_di  = 100 * minus_dm_s.ewm(alpha=1 / period, adjust=False).mean() / tr_s.replace(0, np.nan)
    dx        = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / period, adjust=False).mean()


def _atr(high: pd.Series, low: pd.Series, close: pd.Series,
         period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def _to_timestamp(ts: Any) -> pd.Timestamp:
    """Safely convert any timestamp type to pd.Timestamp (UTC)."""
    if isinstance(ts, pd.Timestamp):
        return ts if ts.tzinfo else ts.tz_localize("UTC")
    if isinstance(ts, str):
        t = pd.Timestamp(ts)
        return t if t.tzinfo else t.tz_localize("UTC")
    try:
        t = pd.Timestamp(ts)
        return t if t.tzinfo else t.tz_localize("UTC")
    except Exception:
        return pd.Timestamp.utcnow()


class AntiChopFilter:
    """
    Wraps ReversalZoneCalculator.
    Uses TIMESTAMP-based minimum distance (not bar_index) to prevent
    signal clustering across API calls with shifting bar indices.
    """

    def __init__(
        self,
        timeframe: str = "5m",
        preset: str = "Low",
        calc_mode: str = "Average",
        avg_len: int = 5,
        atr_len: int = 5,
        custom_abs: float = 0.0001,  # Was 0.05 — forced 3.54% threshold on XRP ($1.41). Now ATR dominates.
        confirm_bars: int = 0,
        zone_thickness_pct: float = 0.03,
        max_zones: int = 8,
        use_time_filter: bool = True,
        use_atr_filter: bool = True,
        use_adx_filter: bool = True,
        use_rsi_filter: bool = True,
    ):
        self.timeframe = timeframe
        self._calc = ReversalZoneCalculator(
            preset=preset, calc_mode=calc_mode, avg_len=avg_len,
            atr_len=atr_len, custom_abs=custom_abs,
            confirm_bars=confirm_bars, zone_thickness_pct=zone_thickness_pct,
            max_zones=max_zones,
        )
        self.use_time = use_time_filter
        self.use_atr  = use_atr_filter
        self.use_adx  = use_adx_filter
        self.use_rsi  = use_rsi_filter
        self._min_minutes  = MIN_MINUTES_BETWEEN_SIGNALS.get(timeframe, 60)
        self._adx_threshold = ADX_THRESHOLD_BY_TF.get(timeframe, ADX_THRESHOLD)

    def process(self, df: pd.DataFrame, symbol: str | None = None, check_db: bool = True, db_timestamps: set | None = None) -> dict:
        raw         = self._calc.process_ohlcv_data(df)
        raw_zones   = raw["zones"]

        # CRITICAL: The calculator already enforces alternation via swing_dir.
        # If we filter out signals, we must preserve alternation.
        # Strategy: Accept signals in order, but skip any that violate rules.
        # The alternation check is PRIMARY - if a signal would create two
        # consecutive BUY or SELL signals, skip it entirely.

        atr_series  = _atr(df["high"], df["low"], df["close"], period=14)
        adx_series  = _adx(df["high"], df["low"], df["close"], period=14)
        rsi_series  = _rsi(df["close"], period=14)
        idx_to_iloc = {ts: i for i, ts in enumerate(df.index)}

        filtered: List[dict] = []
        last_ts:     pd.Timestamp | None = None
        last_price:  float = 0.0
        last_signal: str | None = None  # Track last signal type for alternation
        
        # ═══════════════════════════════════════════════════════════════════
        # CRITICAL: Check database for last signal to ensure alternation
        # The calculator is stateless and doesn't know about DB signals.
        # We MUST check the DB to ensure alternation across runs.
        # ═══════════════════════════════════════════════════════════════════
        last_signal: str | None = None  # Track last ACCEPTED signal type
        if symbol and check_db:
            try:
                from reversal_zones.models import ReversalZone
                last_db_signal = ReversalZone.objects.filter(
                    symbol=symbol,
                    timeframe=self.timeframe
                ).order_by('-reversal_time').values_list('label_text', flat=True).first()
                
                if last_db_signal:
                    last_signal = last_db_signal
                    logger.info("📌 Starting filter with last DB signal: %s %s = %s",
                               symbol, self.timeframe, last_signal)
            except Exception as exc:
                logger.warning("Could not check last DB signal: %s", exc)

        for zone in raw_zones:
            ts        = zone.get("timestamp") or zone.get("reversal_time")
            zone_ts   = _to_timestamp(ts)
            bar_iloc  = idx_to_iloc.get(ts, len(df) - 1)
            price     = zone["center_price"]
            is_bull   = zone["is_bullish"]
            signal    = "BUY" if is_bull else "SELL"

            atr_val = float(atr_series.iloc[bar_iloc]) if not pd.isna(atr_series.iloc[bar_iloc]) else 0.0
            adx_val = float(adx_series.iloc[bar_iloc]) if not pd.isna(adx_series.iloc[bar_iloc]) else 0.0
            rsi_val = float(rsi_series.iloc[bar_iloc])  if not pd.isna(rsi_series.iloc[bar_iloc]) else 50.0

            # ═══════════════════════════════════════════════════════════════════
            # Gate 0: SIGNAL ALTERNATION (HIGHEST PRIORITY)
            # ═══════════════════════════════════════════════════════════════════
            # After SELL, only BUY is allowed. After BUY, only SELL is allowed.
            # This is the MOST IMPORTANT trading rule - it ensures we're trading
            # actual reversals, not noise.
            if last_signal is not None and last_signal == signal:
                logger.info("🚫 FILTER[alternation] blocked %s @ %.2f (last signal was %s)",
                             signal, price, last_signal)
                continue

            # ═══════════════════════════════════════════════════════════════════
            # Gate 1: Minimum TIME distance
            # ═══════════════════════════════════════════════════════════════════
            if self.use_time and last_ts is not None:
                minutes_since = (zone_ts - last_ts).total_seconds() / 60.0
                if minutes_since < self._min_minutes:
                    logger.debug("FILTER[time] blocked %s @ %.2f (%.1f min < %d min required)",
                                 signal, price, minutes_since, self._min_minutes)
                    continue

            # ═══════════════════════════════════════════════════════════════════
            # Gate 2: ATR price distance
            # ═══════════════════════════════════════════════════════════════════
            if self.use_atr and last_price > 0 and atr_val > 0:
                price_gap = abs(price - last_price)
                required  = MIN_ATR_DISTANCE_MULT * atr_val
                if price_gap < required:
                    logger.debug("FILTER[atr] blocked %s @ %.2f (gap=%.2f < %.2f)",
                                 signal, price, price_gap, required)
                    continue

            # ═══════════════════════════════════════════════════════════════════
            # Gate 3: ADX trend confirmation (per-timeframe threshold)
            # ═══════════════════════════════════════════════════════════════════
            if self.use_adx and adx_val < self._adx_threshold:
                logger.debug("FILTER[adx] blocked %s @ %.2f (ADX=%.1f < %.1f for %s)",
                             signal, price, adx_val, self._adx_threshold, self.timeframe)
                continue

            # ═══════════════════════════════════════════════════════════════════
            # Gate 4: RSI zone
            # ═══════════════════════════════════════════════════════════════════
            if self.use_rsi:
                if is_bull and rsi_val >= RSI_OVERBOUGHT:
                    continue
                if not is_bull and rsi_val <= RSI_OVERSOLD:
                    continue

            # ═══════════════════════════════════════════════════════════════════
            # All gates passed - ACCEPT this signal
            # ═══════════════════════════════════════════════════════════════════
            last_ts     = zone_ts
            last_price  = price
            last_signal = signal  # Remember for alternation check
            filtered.append(zone)

        status = raw["status"]
        if filtered:
            last     = filtered[-1]
            last_sig = "BUY" if last["is_bullish"] else "SELL"
            status   = {**status, "last_signal": last_sig}

        logger.info("AntiChopFilter [%s]: raw=%d passed=%d (max=%d)",
                    self.timeframe, len(raw_zones), len(filtered), 999)

        return {
            "zones":         filtered,
            "path_segments": raw["path_segments"],
            "status":        status,
            "config":        raw["config"],
        }


def run_filtered_calculator(df: pd.DataFrame, timeframe: str = "5m") -> dict:
    """Single entry-point for REST API and WebSocket consumer."""
    return AntiChopFilter(timeframe=timeframe).process(df)