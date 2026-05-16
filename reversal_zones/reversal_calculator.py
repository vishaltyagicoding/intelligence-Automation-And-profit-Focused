"""
Reversal Entry Zones — Python Port
====================================
Direct conversion of the TradingView Pine Script "Reversal Entry Zones" indicator.

DO NOT MODIFY THIS LOGIC - IT IS THE EXACT TRADINGVIEW PINE SCRIPT CONVERSION.

Workflow:
1) Track running highs/lows from selected price source (High/Low or EMA-smoothed)
2) Confirm a pivot only when price reverses by a minimum threshold
3) Mark the reversal level as bullish or bearish
4) Draw core zone, outer zone, and optional projected zone
5) Optionally connect confirmed reversals with a synthetic path
6) Summarise current state in a status panel
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd


@dataclass
class ReversalEvent:
    """Stores a single confirmed reversal pivot."""
    bar_index: int
    price: float
    is_bullish: bool          # True = low pivot (bullish reversal)
    core_half: float          # half-height of core box
    outer_half: float         # half-height of outer box
    zone_half: float          # half-height of projected zone


@dataclass
class Config:
    """All user-configurable parameters (mirrors Pine Script inputs)."""
    # Confirmation
    confirm_bars: int = 0       # extra bars before confirming pivot
    
    # Sensitivity
    preset: str = "Low"         # "Low" | "Very Low"
    
    # Reversal Calculation
    calc_mode: str = "Average"  # "Average" | "High/Low"
    avg_len: int = 5            # EMA length for smoothed source
    atr_len: int = 5            # ATR period
    custom_abs: float = 0.05    # minimum absolute reversal size
    
    # Zone Display
    show_reversal_labels: bool = True
    show_zones: bool = True
    max_zones: int = 8
    zone_extend: int = 10       # bars to extend zone boxes (display only)
    zone_thickness_pct: float = 0.03  # projected zone thickness %
    
    # Reversal Lines
    level_extend: int = 10      # bars to extend level lines (display only)
    max_levels: int = 12
    
    # Synthetic Path
    show_synthetic_path: bool = True
    max_synthetic_lines: int = 40


def _ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential moving average (same as ta.ema in Pine)."""
    return series.ewm(span=length, adjust=False).mean()


def _professional_sl_target(
    df: pd.DataFrame,
    bar_index: int,
    center_price: float,
    is_bullish: bool,
    atr_now: float,
    timeframe: str = '5m',
) -> tuple[float, float]:
    """
    Universal stop loss & target calculation that adapts to symbol price levels.

    LOGIC:
    - High-priced symbols (price > $1000): Use absolute point-based buffers
    - Low-priced symbols (price ≤ $1000): Use percentage-based buffers
    - BUY signal → scans backwards to find first bearish (red) candle
    - SELL signal → finds first bullish (green) candle
    - Skips doji/flat candles (body < 0.01% of price)
    - Target = always 2:1 Risk:Reward (entry + 2 × risk for BUY)
    - ATR safety guards: minimum 1.5× ATR distance, cap at 3× ATR
    """
    # ── Universal Constants ──────────────────────────────────────────────
    HIGH_PRICE_THRESHOLD = 1000.0  # symbols > $1000 use absolute points
    
    # High-priced symbol constants (absolute points)
    BUFFER_POINTS_HIGH   = 20.0    # fixed buffer in real price points
    SMALL_MOVE_HIGH      = 20.0    # if candle moved < 20 points
    MEDIUM_MOVE_HIGH     = 30.0    # if candle moved 20-30 points
    EXTRA_BUFFER_HIGH    = 20.0    # extra buffer for small/medium moves
    
    # Low-priced symbol constants (percentages)
    BUFFER_PCT_LOW       = 0.0003  # 0.03% buffer
    SMALL_MOVE_PCT_LOW   = 0.0002  # if candle moved < 0.02%
    MEDIUM_MOVE_PCT_LOW  = 0.0005  # if candle moved 0.02%-0.05%
    
    # Common constants
    ATR_MIN_MULT    = 1.5   # minimum SL distance = 1.5 × ATR
    ATR_MAX_MULT    = 3.0   # cap SL distance at 3.0 × ATR
    RR_RATIO        = 2.0   # profit target = risk × 2
    LOOKBACK        = 30    # max candles to look back
    DOJI_THRESHOLD  = 0.0001 # candle body < 0.01% of price = doji

    # Determine if high-priced or low-priced symbol
    is_high_priced = center_price > HIGH_PRICE_THRESHOLD

    n           = len(df)
    look_start  = max(0, bar_index - LOOKBACK)
    sl_level    = None

    if is_bullish:
        # ── BUY: find previous bearish (red) candle ──────────────────────
        for i in range(bar_index - 1, look_start - 1, -1):
            if i < 0 or i >= n:
                continue
            o   = float(df['open'].iloc[i])
            c   = float(df['close'].iloc[i])
            low = float(df['low'].iloc[i])

            if c >= o:
                continue   # not a bearish candle

            body_pct = abs(o - c) / o if o > 0 else 0

            if body_pct < DOJI_THRESHOLD:
                # Doji (body < 0.01% of price) — skip, look further back
                continue

            # Found meaningful bearish candle
            candle_move = abs(o - c)  # real price points moved
            
            if is_high_priced:
                # ── HIGH-PRICED SYMBOL: Absolute point-based buffer ──────
                if SMALL_MOVE_HIGH <= candle_move <= MEDIUM_MOVE_HIGH:
                    # Candle moved 20-30 points → add 20 extra buffer
                    buffer = candle_move + EXTRA_BUFFER_HIGH
                elif candle_move < SMALL_MOVE_HIGH:
                    # Candle moved < 20 points → add 20 extra buffer
                    buffer = candle_move + EXTRA_BUFFER_HIGH
                else:
                    # Candle moved > 30 points → use move as buffer
                    buffer = candle_move
                
                sl_level = low - buffer
            else:
                # ── LOW-PRICED SYMBOL: Percentage-based buffer ───────────
                move_pct = candle_move / center_price
                
                if SMALL_MOVE_PCT_LOW <= move_pct <= MEDIUM_MOVE_PCT_LOW:
                    # Candle moved 0.02%-0.05% → add 0.03% buffer
                    buffer = candle_move + (center_price * BUFFER_PCT_LOW)
                elif move_pct < SMALL_MOVE_PCT_LOW:
                    # Candle moved < 0.02% → add 0.03% buffer
                    buffer = candle_move + (center_price * BUFFER_PCT_LOW)
                else:
                    # Candle moved > 0.05% → use move as buffer
                    buffer = candle_move
                
                sl_level = low - buffer
            
            break

        if sl_level is None:
            # No suitable bearish candle found – ATR fallback
            sl_level = center_price - (atr_now * ATR_MIN_MULT)

        # ── ATR safety guards ────────────────────────────────────────────
        atr_min_sl = center_price - (atr_now * ATR_MIN_MULT)
        atr_max_sl = center_price - (atr_now * ATR_MAX_MULT)

        stop_loss = min(sl_level, atr_min_sl)  # take the lower (more protection)
        stop_loss = max(stop_loss, atr_max_sl)  # cap: don't go beyond 3× ATR

        # ── Target: 2 : 1 R : R ──────────────────────────────────────────
        risk   = center_price - stop_loss
        if risk <= 0:
            risk = atr_now * ATR_MIN_MULT
        target = center_price + (risk * RR_RATIO)

    else:
        # ── SELL: find previous bullish (green) candle ────────────────────
        for i in range(bar_index - 1, look_start - 1, -1):
            if i < 0 or i >= n:
                continue
            o    = float(df['open'].iloc[i])
            c    = float(df['close'].iloc[i])
            high = float(df['high'].iloc[i])

            if c <= o:
                continue   # not a bullish candle

            body_pct = abs(c - o) / o if o > 0 else 0

            if body_pct < DOJI_THRESHOLD:
                continue   # doji – skip

            # Found meaningful bullish candle
            candle_move = abs(c - o)  # real price points moved
            
            if is_high_priced:
                # ── HIGH-PRICED SYMBOL: Absolute point-based buffer ──────
                if SMALL_MOVE_HIGH <= candle_move <= MEDIUM_MOVE_HIGH:
                    # Candle moved 20-30 points → add 20 extra buffer
                    buffer = candle_move + EXTRA_BUFFER_HIGH
                elif candle_move < SMALL_MOVE_HIGH:
                    # Candle moved < 20 points → add 20 extra buffer
                    buffer = candle_move + EXTRA_BUFFER_HIGH
                else:
                    # Candle moved > 30 points → use move as buffer
                    buffer = candle_move
                
                sl_level = high + buffer
            else:
                # ── LOW-PRICED SYMBOL: Percentage-based buffer ───────────
                move_pct = candle_move / center_price
                
                if SMALL_MOVE_PCT_LOW <= move_pct <= MEDIUM_MOVE_PCT_LOW:
                    # Candle moved 0.02%-0.05% → add 0.03% buffer
                    buffer = candle_move + (center_price * BUFFER_PCT_LOW)
                elif move_pct < SMALL_MOVE_PCT_LOW:
                    # Candle moved < 0.02% → add 0.03% buffer
                    buffer = candle_move + (center_price * BUFFER_PCT_LOW)
                else:
                    # Candle moved > 0.05% → use move as buffer
                    buffer = candle_move
                
                sl_level = high + buffer
            
            break

        if sl_level is None:
            sl_level = center_price + (atr_now * ATR_MIN_MULT)

        # ── ATR safety guards ────────────────────────────────────────────
        atr_min_sl = center_price + (atr_now * ATR_MIN_MULT)
        atr_max_sl = center_price + (atr_now * ATR_MAX_MULT)

        stop_loss = max(sl_level, atr_min_sl)  # take the higher (more protection)
        stop_loss = min(stop_loss, atr_max_sl)  # cap: don't go beyond 3× ATR

        # ── Target: 2 : 1 R : R ──────────────────────────────────────────
        risk   = stop_loss - center_price
        if risk <= 0:
            risk = atr_now * ATR_MIN_MULT
        target = center_price - (risk * RR_RATIO)

    # Round to 2 decimal places for consistency
    stop_loss = round(stop_loss, 2)
    target = round(target, 2)

    return float(stop_loss), float(target)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=length, adjust=False).mean()


class ReversalZoneCalculator:
    """
    Python port of the Pine Script "Reversal Entry Zones" indicator.
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV DataFrame with columns 'open', 'high', 'low', 'close'.
        Index should be a DatetimeIndex or integer range.
    config : Config, optional
        Parameter object. Defaults to Config() which mirrors Pine defaults.
    """
    
    def __init__(self, 
                 preset="Low",
                 calc_mode="Average",
                 avg_len=5,
                 atr_len=5,
                 custom_abs=0.05,
                 confirm_bars=0,
                 zone_thickness_pct=0.03,
                 max_zones=8,
                 timeframe="5m"):
        self.cfg = Config(
            preset=preset,
            calc_mode=calc_mode,
            avg_len=avg_len,
            atr_len=atr_len,
            custom_abs=custom_abs,
            confirm_bars=confirm_bars,
            zone_thickness_pct=zone_thickness_pct,
            max_zones=max_zones,
        )
        self.timeframe = timeframe  # Store timeframe for SL/Target calculation
        
        # Outputs populated by run()
        self.reversals: List[ReversalEvent] = []
        self._atr_series: pd.Series = pd.Series(dtype=float)
        
        # Internal swing-tracking state
        self._run_high: float = math.nan
        self._run_low: float = math.nan
        self._run_high_raw: float = math.nan
        self._run_low_raw: float = math.nan
        self._run_high_bar: int = -1
        self._run_low_bar: int = -1
        self._swing_dir: int = 1   # 1 = tracking high, -1 = tracking low
    
    @property
    def _preset_atr_mult(self) -> float:
        return 3.5 if self.cfg.preset == "Very Low" else 2.8
    
    @property
    def _preset_pct(self) -> float:
        return 0.02 if self.cfg.preset == "Very Low" else 0.015
    
    def _build_sources(self, df: pd.DataFrame) -> tuple:
        """
        Returns (hi_base, lo_base, hi_raw, lo_raw) with confirm_bars shift applied.
        
        Pine logic:
        hiBase = calcMode == "High/Low" ? high : ema(high, avgLen)
        loBase = calcMode == "High/Low" ? low  : ema(low,  avgLen)
        hiRef    = hiBase[confirmBars]
        loRef    = loBase[confirmBars]
        hiRawRef = high[confirmBars]
        loRawRef = low [confirmBars]
        """
        cb = self.cfg.confirm_bars
        
        if self.cfg.calc_mode == "High/Low":
            hi_base = df["high"]
            lo_base = df["low"]
        else:
            hi_base = _ema(df["high"], self.cfg.avg_len)
            lo_base = _ema(df["low"],  self.cfg.avg_len)
        
        hi_ref     = hi_base.shift(cb)
        lo_ref     = lo_base.shift(cb)
        hi_raw_ref = df["high"].shift(cb)
        lo_raw_ref = df["low"].shift(cb)
        
        return hi_ref, lo_ref, hi_raw_ref, lo_raw_ref
    
    def process_ohlcv_data(self, df: pd.DataFrame) -> dict:
        """
        Execute the full pivot-detection pass over df.
        Returns dict with zones, path_segments, status, config.
        """
        self.reversals.clear()
        
        df = df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
        
        # Pre-compute ATR and threshold series
        self._atr_series = _atr(df["high"], df["low"], df["close"], self.cfg.atr_len)
        hi_ref, lo_ref, hi_raw_ref, lo_raw_ref = self._build_sources(df)
        
        # Reset swing state
        self._run_high  = math.nan
        self._run_low   = math.nan
        self._run_high_raw = math.nan
        self._run_low_raw  = math.nan
        self._run_high_bar = -1
        self._run_low_bar  = -1
        self._swing_dir = 1
        
        n = len(df)
        for i in range(n):
            hi  = hi_ref.iloc[i]
            lo  = lo_ref.iloc[i]
            hir = hi_raw_ref.iloc[i]
            lor = lo_raw_ref.iloc[i]
            atr_now = self._atr_series.iloc[i]
            close_now = df["close"].iloc[i]
            
            if pd.isna(hi) or pd.isna(lo):
                continue
            
            # reversal threshold  (mirrors Pine: math.max of three values)
            threshold = max(
                close_now * self._preset_pct / 100.0,
                self.cfg.custom_abs,
                self._preset_atr_mult * atr_now,
            )
            
            actual_bar = i - self.cfg.confirm_bars  # the bar the pivot belongs to
            
            # ── initialise on first valid bar ────────────────────────────────
            if math.isnan(self._run_high):
                self._run_high     = hi
                self._run_low      = lo
                self._run_high_raw = hir
                self._run_low_raw  = lor
                self._run_high_bar = actual_bar
                self._run_low_bar  = actual_bar
                self._swing_dir    = 1
                continue
            
            # ── tracking upswing (looking for bearish reversal) ───────────────
            if self._swing_dir == 1:
                if hi > self._run_high:
                    self._run_high     = hi
                    self._run_high_raw = hir
                    self._run_high_bar = actual_bar
                
                if (self._run_high - lo) >= threshold:
                    # confirmed HIGH pivot → bearish reversal signal
                    self._emit_reversal(
                        bar_index     = self._run_high_bar,
                        center_price  = self._run_high_raw,
                        is_bullish    = False,
                        atr_now       = atr_now,
                        zone_center   = self._run_high_raw,
                        timestamp     = df.index[max(0, self._run_high_bar)]
                    )
                    
                    # flip direction, reset low tracker
                    self._swing_dir    = -1
                    self._run_low      = lo
                    self._run_low_raw  = lor
                    self._run_low_bar  = actual_bar
            
            # ── tracking downswing (looking for bullish reversal) ─────────────
            else:
                if lo < self._run_low:
                    self._run_low     = lo
                    self._run_low_raw = lor
                    self._run_low_bar = actual_bar
                
                if (hi - self._run_low) >= threshold:
                    # confirmed LOW pivot → bullish reversal signal
                    self._emit_reversal(
                        bar_index     = self._run_low_bar,
                        center_price  = self._run_low_raw,
                        is_bullish    = True,
                        atr_now       = atr_now,
                        zone_center   = self._run_low_raw,
                        timestamp     = df.index[max(0, self._run_low_bar)]
                    )
                    
                    # flip direction, reset high tracker
                    self._swing_dir    = 1
                    self._run_high     = hi
                    self._run_high_raw = hir
                    self._run_high_bar = actual_bar
        
        # ── Build output with PROFESSIONAL stop loss and target ──────────────
        # Replace the old tiny outer_half formula with swing-structure SL/Target.
        # outer_top  = higher price level  (target for BUY,  stop loss for SELL)
        # outer_bottom = lower price level (stop loss for BUY, target for SELL)
        zones = []
        n_df = len(df)
        for r in self.reversals[-self.cfg.max_zones:]:
            bar_idx = min(max(r.bar_index, 0), n_df - 1)

            # ATR at the signal bar (fallback: 0.2% of price)
            atr_val = (
                float(self._atr_series.iloc[bar_idx])
                if bar_idx < len(self._atr_series)
                   and not pd.isna(self._atr_series.iloc[bar_idx])
                else abs(r.price) * 0.002
            )

            # Professional stop loss & target
            stop_loss, target = _professional_sl_target(
                df=df,
                bar_index=bar_idx,
                center_price=r.price,
                is_bullish=r.is_bullish,
                atr_now=atr_val,
                timeframe=self.timeframe,
            )

            # Layout:
            #   BUY  → outer_bottom = stop_loss (below entry)
            #           outer_top   = target    (above entry)
            #   SELL → outer_top    = stop_loss (above entry)
            #           outer_bottom = target   (below entry)
            if r.is_bullish:
                outer_top_val    = target
                outer_bottom_val = stop_loss
            else:
                outer_top_val    = stop_loss
                outer_bottom_val = target

            # Keep core zone tight around entry for chart visualisation
            core_half = max(atr_val * 0.12, abs(r.price) * 0.00015)

            ts = r.timestamp if hasattr(r, 'timestamp') else df.index[bar_idx]
            zones.append({
                'bar_index':    r.bar_index,
                'center_price': r.price,
                'stop_loss':    stop_loss,      # Add explicit stop_loss field
                'target':       target,         # Add explicit target field
                'outer_top':    outer_top_val,
                'outer_bottom': outer_bottom_val,
                'core_top':     r.price + core_half,
                'core_bottom':  r.price - core_half,
                'is_bullish':   r.is_bullish,
                'label_text':   'BUY' if r.is_bullish else 'SELL',
                'reversal_time': ts,
                'timestamp':     ts,
            })
        
        path_segments = []
        revs = self.reversals[-self.cfg.max_synthetic_lines:]
        for i in range(len(revs) - 1):
            r1 = revs[i]
            r2 = revs[i + 1]
            path_segments.append({
                'start_bar': r1.bar_index,
                'end_bar': r2.bar_index,
                'start_price': r1.price,
                'end_price': r2.price,
                'start_time': r1.timestamp if hasattr(r1, 'timestamp') else df.index[r1.bar_index],
                'end_time': r2.timestamp if hasattr(r2, 'timestamp') else df.index[r2.bar_index],
            })
        
        last_signal = 'NONE'
        tracking = 'NONE'
        if self.reversals:
            last = self.reversals[-1]
            last_signal = 'BUY' if last.is_bullish else 'SELL'
            tracking = 'Monitoring Bullish Reversal' if self._swing_dir == -1 else 'Monitoring Bearish Reversal'
        
        return {
            'zones': zones,
            'path_segments': path_segments,
            'status': {
                'last_signal': last_signal,
                'tracking': tracking,
            },
            'config': {
                'preset': self.cfg.preset,
                'calc_mode': self.cfg.calc_mode,
                'max_zones': self.cfg.max_zones,
            }
        }
    
    def _emit_reversal(self,
                       bar_index: int,
                       center_price: float,
                       is_bullish: bool,
                       atr_now: float,
                       zone_center: float,
                       timestamp=None):
        """Build a ReversalEvent and append it to self.reversals."""
        core_half  = max(atr_now * 0.12, abs(center_price) * 0.00015)
        outer_half = core_half * 2.15
        zone_half  = (zone_center * self.cfg.zone_thickness_pct / 100.0) / 2.0
        
        evt = ReversalEvent(
            bar_index  = max(bar_index, 0),
            price      = center_price,
            is_bullish = is_bullish,
            core_half  = core_half,
            outer_half = outer_half,
            zone_half  = zone_half,
        )
        evt.timestamp = timestamp
        self.reversals.append(evt)