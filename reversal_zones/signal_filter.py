"""
AntiChopFilter — Exact Pine Script Port
=========================================
RULE: This file must match the Pine Script "Reversal Entry Zones" exactly.
The Pine Script does NOT have ADX, RSI, ATR-distance, or time-gap filters.
The ONLY signal quality control in Pine Script is:
  1. The reversal threshold (ATR × preset_mult vs. price × preset_pct)
  2. Strict alternation via swingDir (BUY→SELL→BUY→SELL)

Any extra filter causes signals visible on TradingView to be silently dropped
or delayed in the backend, diverging from what users see on the chart.

HISTORY OF REMOVED FILTERS (and why):
  - ADX filter (ADX < 15 blocks signal): NOT in Pine. Was causing 15-25 min
    delays because ADX at the signal candle might be 14.8, blocking the signal
    until the next candle where ADX calculation uses one more data point.
  - RSI filter (RSI > 60 blocks BUY): NOT in Pine. Was silently dropping valid
    reversal signals when price was near recent highs.
  - ATR distance filter (gap < 2.5×ATR blocks signal): NOT in Pine. Was
    dropping signals that were close in price but far apart in time.
  - 60-minute time gap filter: NOT in Pine. Pine has no minimum time between
    signals — the reversal threshold naturally prevents rapid-fire signals.

ONLY remaining filter: alternation (BUY→SELL→BUY→SELL), seeded from DB.
"""
from __future__ import annotations

import logging
from typing import Any, List
import pandas as pd

from reversal_zones.reversal_calculator import ReversalZoneCalculator

logger = logging.getLogger(__name__)


def _to_timestamp(ts: Any) -> pd.Timestamp:
    """Safely convert any timestamp type to pd.Timestamp (UTC-aware)."""
    if isinstance(ts, pd.Timestamp):
        return ts if ts.tzinfo else ts.tz_localize("UTC")
    try:
        t = pd.Timestamp(ts)
        return t if t.tzinfo else t.tz_localize("UTC")
    except Exception:
        return pd.Timestamp.utcnow()


class AntiChopFilter:
    """
    Wraps ReversalZoneCalculator and enforces ONE rule: strict alternation.

    The calculator already enforces alternation internally via swing_dir.
    This wrapper adds a DB-state seed so alternation is correct across
    multiple task runs (not just within a single calculation window).

    NO other filters. Matches Pine Script exactly.
    """

    def __init__(
        self,
        timeframe: str = "5m",
        preset: str = "Low",
        calc_mode: str = "Average",
        avg_len: int = 5,
        atr_len: int = 5,
        custom_abs: float = 0.0001,
        confirm_bars: int = 0,
        zone_thickness_pct: float = 0.03,
        max_zones: int = 8,
        # Legacy kwargs accepted but IGNORED (kept for call-site compatibility)
        use_time_filter: bool = False,
        use_atr_filter: bool = False,
        use_adx_filter: bool = False,
        use_rsi_filter: bool = False,
    ):
        self.timeframe = timeframe
        self._calc = ReversalZoneCalculator(
            preset=preset, calc_mode=calc_mode, avg_len=avg_len,
            atr_len=atr_len, custom_abs=custom_abs,
            confirm_bars=confirm_bars, zone_thickness_pct=zone_thickness_pct,
            max_zones=max_zones, timeframe=timeframe,
        )

    def process(
        self,
        df: pd.DataFrame,
        symbol: str | None = None,
        check_db: bool = True,
        db_timestamps: set | None = None,
    ) -> dict:
        """
        Run Pine Script logic on df, return only alternating signals.

        If `symbol` is provided and `check_db=True`, seeds `last_signal`
        from the database so alternation is maintained across task runs.
        """
        raw = self._calc.process_ohlcv_data(df)
        raw_zones: List[dict] = raw["zones"]

        # ── Seed last_signal from DB (if symbol provided) ─────────────────────
        last_signal: str | None = None
        if symbol and check_db:
            try:
                from reversal_zones.models import ReversalZone
                last_db = (
                    ReversalZone.objects
                    .filter(symbol=symbol, timeframe=self.timeframe)
                    .order_by("-reversal_time")
                    .values_list("label_text", flat=True)
                    .first()
                )
                if last_db:
                    last_signal = last_db
                    logger.debug(
                        "📌 Alternation seed from DB: %s %s → last=%s",
                        symbol, self.timeframe, last_signal
                    )
            except Exception as exc:
                logger.warning("Could not read last DB signal for alternation seed: %s", exc)

        # ── Apply ONLY alternation filter ─────────────────────────────────────
        filtered: List[dict] = []
        for zone in raw_zones:
            signal = "BUY" if zone["is_bullish"] else "SELL"

            if last_signal is not None and last_signal == signal:
                logger.info(
                    "🚫 ALTERNATION blocked consecutive %s [%s %s] @ %.4f (last=%s)",
                    signal, symbol or "?", self.timeframe,
                    zone["center_price"], last_signal,
                )
                continue

            # Signal passes — update last_signal
            last_signal = signal
            filtered.append(zone)

        logger.info(
            "AntiChopFilter [%s %s]: raw=%d → passed=%d (alternation-only filter)",
            symbol or "?", self.timeframe, len(raw_zones), len(filtered),
        )

        status = raw["status"]
        if filtered:
            status = {**status, "last_signal": "BUY" if filtered[-1]["is_bullish"] else "SELL"}

        return {
            "zones":         filtered,
            "path_segments": raw["path_segments"],
            "status":        status,
            "config":        raw["config"],
        }


def run_filtered_calculator(
    df: pd.DataFrame,
    timeframe: str = "5m",
    symbol: str | None = None,
) -> dict:
    """Single entry-point for REST API and WebSocket consumer."""
    return AntiChopFilter(timeframe=timeframe).process(df, symbol=symbol)