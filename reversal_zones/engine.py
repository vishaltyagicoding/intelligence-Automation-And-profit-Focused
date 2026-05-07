"""Reversal zones engine - delegates to reversal_calculator."""
from .reversal_calculator import ReversalZoneCalculator


class ReversalEngine:
    def __init__(self, config=None):
        config = config or {}
        self.calculator = ReversalZoneCalculator(
            preset=config.get('preset', 'Low'),
            calc_mode=config.get('calc_mode', 'Average'),
            avg_len=config.get('avg_len', 5),
            atr_len=config.get('atr_len', 5),
            custom_abs=config.get('custom_abs', 0.05),
            confirm_bars=config.get('confirm_bars', 0),
            zone_thickness_pct=config.get('zone_thickness_pct', 0.03),
            max_zones=config.get('max_zones', 8),
        )

    def process_candles(self, df):
        return self.calculator.process_ohlcv_data(df)
