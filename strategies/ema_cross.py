import pandas as pd
import ta
from .base import BaseStrategy, Signal


class EmaCrossStrategy(BaseStrategy):
    """EMA crossover strategy — faster reaction than SMA cross."""

    def analyze(self, df: pd.DataFrame) -> Signal:
        fast = self.params.get("fast_period", 9)
        slow = self.params.get("slow_period", 21)

        if not self._validate_df(df, min_rows=slow + 5):
            return Signal.HOLD

        close = df["close"]
        fast_ema = ta.trend.EMAIndicator(close, window=fast).ema_indicator()
        slow_ema = ta.trend.EMAIndicator(close, window=slow).ema_indicator()

        if fast_ema.iloc[-2] < slow_ema.iloc[-2] and fast_ema.iloc[-1] > slow_ema.iloc[-1]:
            return Signal.BUY
        if fast_ema.iloc[-2] > slow_ema.iloc[-2] and fast_ema.iloc[-1] < slow_ema.iloc[-1]:
            return Signal.SELL
        return Signal.HOLD
