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
import logging
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


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
    Professional stop loss & target for real algo trading with STRICT risk management.

    LOGIC:
    - Stop Loss BUY: Find previous GREEN candle where OPEN < current signal OPEN, 
                     use that candle's OPEN price as stop loss
    - Stop Loss SELL: Find previous RED candle where OPEN > current signal OPEN,
                      use that candle's OPEN price as stop loss
    
    NEW RISK MANAGEMENT RULES (2:1 Reward-to-Risk Ratio):
    - Target:    MINIMUM 0.2%, MAXIMUM 0.55% from entry
    - Stop Loss: HALF of target distance (creates 2:1 reward-to-risk)
    
    Formula:
    - BUY:  Target = Entry + X%, Stop Loss = Entry - (X% * 0.5)
    - SELL: Target = Entry - X%, Stop Loss = Entry + (X% * 0.5)
    
    Example (BUY at $50,000):
    - Target = $50,200 (0.4% above entry)
    - Stop Loss = $49,900 (0.2% below entry = half of 0.4%)
    - Reward-to-Risk = 2:1
    
    This ensures:
    1. Target never too small (>= 0.2%) - ensures minimum profit
    2. Target never too large (<= 0.55%) - realistic profit taking
    3. Stop loss is always half of target - perfect 2:1 ratio
    4. Risk is controlled and consistent across all signals
    """
    # ── STRICT RISK MANAGEMENT CONSTANTS ─────────────────────────────────
    # Target Constraints (Stop Loss will be calculated as half of target distance)
    MIN_TARGET_PCT  = 0.002     # MINIMUM 0.2% target (ensure minimum profit)
    MAX_TARGET_PCT  = 0.0055    # MAXIMUM 0.55% target (realistic profit taking)
    
    # Calculation Parameters
    LOOKBACK        = 50        # max candles to look back (not used in new formula)
    DOJI_THRESHOLD  = 0.001     # candle body < 0.1% of price = doji (not used in new formula)

    n           = len(df)
    
    # Use center_price (entry price) as the reference point for calculation
    # center_price is the actual signal entry price (high for SELL, low for BUY)

    if is_bullish:
        # ── BUY SIGNAL: Calculate Target First, then Stop Loss = Half of Target Distance ──
        
        # Step 1: Calculate initial target using risk-reward ratio
        # Start with a base target distance
        initial_target_pct = 0.004  # Start with 0.4% as base
        
        # Calculate initial target
        initial_target = center_price * (1 + initial_target_pct)
        
        # Step 2: Apply target constraints (0.2% - 0.55%)
        target_distance_pct = initial_target_pct
        
        # Enforce MINIMUM 0.2% target (ensure minimum profit)
        if target_distance_pct < MIN_TARGET_PCT:
            target_distance_pct = MIN_TARGET_PCT
        
        # Enforce MAXIMUM 0.55% target (realistic profit taking)
        if target_distance_pct > MAX_TARGET_PCT:
            target_distance_pct = MAX_TARGET_PCT
        
        # Calculate final target
        target = center_price * (1 + target_distance_pct)
        
        # Step 3: Calculate stop loss = half of target distance
        # Formula: SL = Entry - (Target Distance * 0.5)
        target_distance = target - center_price
        sl_distance = target_distance * 0.5
        stop_loss = center_price - sl_distance

    else:
        # ── SELL SIGNAL: Calculate Target First, then Stop Loss = Half of Target Distance ──
        
        # Step 1: Calculate initial target using risk-reward ratio
        # Start with a base target distance
        initial_target_pct = 0.004  # Start with 0.4% as base
        
        # Calculate initial target
        initial_target = center_price * (1 - initial_target_pct)
        
        # Step 2: Apply target constraints (0.2% - 0.55%)
        target_distance_pct = initial_target_pct
        
        # Enforce MINIMUM 0.2% target (ensure minimum profit)
        if target_distance_pct < MIN_TARGET_PCT:
            target_distance_pct = MIN_TARGET_PCT
        
        # Enforce MAXIMUM 0.55% target (realistic profit taking)
        if target_distance_pct > MAX_TARGET_PCT:
            target_distance_pct = MAX_TARGET_PCT
        
        # Calculate final target
        target = center_price * (1 - target_distance_pct)
        
        # Step 3: Calculate stop loss = half of target distance
        # Formula: SL = Entry + (Target Distance * 0.5)
        target_distance = center_price - target
        sl_distance = target_distance * 0.5
        stop_loss = center_price + sl_distance

    # Round to 2 decimal places for consistency
    stop_loss = round(stop_loss, 2)
    target = round(target, 2)

    return float(stop_loss), float(target)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    """
    Average True Range — Wilder RMA, exactly matching Pine Script ta.atr().

    Pine uses Wilder's smoothing (RMA): alpha = 1/length
    Python ewm(span=length) uses EMA: alpha = 2/(length+1)
    These produce different values and would cause signal timing mismatches.

    Wilder RMA formula: ATR[i] = ATR[i-1] * (length-1)/length + TR[i] * (1/length)
    Equivalent to:      ATR[i] = alpha * TR[i] + (1-alpha) * ATR[i-1]  where alpha = 1/length
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder RMA: alpha = 1/length (NOT EMA which uses 2/(length+1))
    return tr.ewm(alpha=1.0 / length, adjust=False).mean()


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
        
        # ── CRITICAL: Exclude the last (open/live) candle ─────────────────
        # Binance klines API always returns the current OPEN candle as the
        # last row. Its high/low are NOT final — they change every tick.
        # Pine Script only fires pivotReady on CLOSED bars. If we process
        # the open candle, we generate phantom signals that TradingView
        # never confirms, causing BUY/SELL arrows to appear at wrong times.
        # Fix: use len(df) - 1 so the loop never touches the last row.
        n = len(df) - 1   # skip last (open) candle — only process closed bars
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
                    logger.debug(
                        "Swing tracking: swingDir=1 (upswing), emitting BEARISH reversal at bar %d (price %.2f)",
                        self._run_high_bar,
                        self._run_high_raw
                    )
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
                    logger.debug(
                        "Swing tracking: swingDir=-1 (downswing), emitting BULLISH reversal at bar %d (price %.2f)",
                        self._run_low_bar,
                        self._run_low_raw
                    )
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
        
        # ── FINAL ALTERNATION PASS ────────────────────────────────────────────
        # Belt-and-suspenders: even if _emit_reversal's safety check somehow
        # allowed two consecutive same-type signals, this pass removes them
        # before any output leaves the calculator.
        # This guarantees the zones list is ALWAYS strictly alternating.
        strictly_alternating: list = []
        for rev in self.reversals:
            if strictly_alternating and strictly_alternating[-1].is_bullish == rev.is_bullish:
                # Replace the earlier duplicate with the later one (more recent is better)
                strictly_alternating[-1] = rev
            else:
                strictly_alternating.append(rev)
        self.reversals = strictly_alternating

        # ── Build output with stop loss and target ──────────────────────────
        # Zones output uses ORIGINAL pivot timestamps.
        # The newest zone also carries confirmation-candle data so the API
        # can override its display timestamp without touching the DB timestamp.
        zones = []
        n_df  = len(df)

        # Confirmation candle = last closed bar (df has open candle stripped)
        confirm_bar_idx = n_df - 1
        confirm_ts      = df.index[confirm_bar_idx]
        confirm_high    = float(df['high'].iloc[confirm_bar_idx])
        confirm_low     = float(df['low'].iloc[confirm_bar_idx])

        for idx_r, r in enumerate(self.reversals[-self.cfg.max_zones:]):
            bar_idx = min(max(r.bar_index, 0), n_df - 1)
            entry   = r.price

            # ── SL and Target: NEW rules (per-signal, from the signal bar) ────
            # BUY:  SL = low  of signal bar; Target = Entry + 2×risk (1:2 RR)
            # SELL: SL = high of signal bar; Target = Entry − 2×risk (1:2 RR)
            sig_high = float(df['high'].iloc[bar_idx])
            sig_low  = float(df['low'].iloc[bar_idx])

            if r.is_bullish:
                stop_loss = sig_low
                risk      = abs(entry - stop_loss)
                target    = entry + 2.0 * risk
            else:
                stop_loss = sig_high
                risk      = abs(stop_loss - entry)
                target    = entry - 2.0 * risk

            # Safety guards: SL and Target must be on correct side
            if r.is_bullish:
                stop_loss = min(stop_loss, entry * 0.9999)
                target    = max(target,    entry * 1.0001)
            else:
                stop_loss = max(stop_loss, entry * 1.0001)
                target    = min(target,    entry * 0.9999)

            stop_loss = round(stop_loss, 8)
            target    = round(target,    8)

            if r.is_bullish:
                outer_top_val    = target
                outer_bottom_val = stop_loss
            else:
                outer_top_val    = stop_loss
                outer_bottom_val = target

            atr_val = (
                float(self._atr_series.iloc[bar_idx])
                if bar_idx < len(self._atr_series)
                   and not pd.isna(self._atr_series.iloc[bar_idx])
                else abs(entry) * 0.002
            )
            core_half = max(atr_val * 0.12, abs(entry) * 0.00015)

            ts = r.timestamp if hasattr(r, 'timestamp') else df.index[bar_idx]

            is_newest = (idx_r == len(self.reversals[-self.cfg.max_zones:]) - 1)

            zones.append({
                'bar_index':      r.bar_index,
                'center_price':   entry,
                'stop_loss':      stop_loss,
                'target':         target,
                'outer_top':      outer_top_val,
                'outer_bottom':   outer_bottom_val,
                'core_top':       entry + core_half,
                'core_bottom':    entry - core_half,
                'is_bullish':     r.is_bullish,
                'label_text':     'BUY' if r.is_bullish else 'SELL',
                'reversal_time':  ts,              # original pivot timestamp (DB key)
                'timestamp':      ts,              # original pivot timestamp
                # Extra confirmation-candle data on the NEWEST zone only.
                # views.py uses this to show the newest signal on the current
                # candle without changing the DB timestamp.
                'confirm_ts':     confirm_ts    if is_newest else None,
                'confirm_high':   confirm_high  if is_newest else None,
                'confirm_low':    confirm_low   if is_newest else None,
                'is_newest':      is_newest,
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
        """
        Build a ReversalEvent and append it to self.reversals.
        
        CRITICAL ALTERNATION CHECK:
        Before emitting any reversal, check if the last reversal has the SAME direction.
        If so, SKIP this reversal (this should NEVER happen if swing logic is correct,
        but this is a safety net to prevent consecutive BUY→BUY or SELL→SELL).
        """
        # ── SAFETY CHECK: Prevent consecutive signals of same type ────────────
        if self.reversals:
            last_reversal = self.reversals[-1]
            if last_reversal.is_bullish == is_bullish:
                # This should NEVER happen if swing_dir logic is correct
                # But if it does, log it and SKIP this reversal
                signal_type = "BUY" if is_bullish else "SELL"
                logger.warning(
                    "⚠️ CALCULATOR BUG: Attempted to emit consecutive %s signals at bar %d (price %.2f). "
                    "Last signal was at bar %d (price %.2f). SKIPPING to enforce alternation.",
                    signal_type,
                    bar_index,
                    center_price,
                    last_reversal.bar_index,
                    last_reversal.price
                )
                return  # SKIP this reversal
        
        # ── Emit reversal (alternation is valid) ──────────────────────────────
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