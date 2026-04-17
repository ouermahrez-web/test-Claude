import pandas as pd
import ta
from .base import BaseStrategy, Signal


class SmaCrossStrategy(BaseStrategy):
    """Golden cross / death cross on simple moving averages."""

    def analyze(self, df: pd.DataFrame) -> Signal:
        fast = self.params.get("fast_period", 10)
        slow = self.params.get("slow_period", 30)

        if not self._validate_df(df, min_rows=slow + 5):
            return Signal.HOLD

        close = df["close"]
        fast_sma = ta.trend.SMAIndicator(close, window=fast).sma_indicator()
        slow_sma = ta.trend.SMAIndicator(close, window=slow).sma_indicator()

        if fast_sma.iloc[-2] < slow_sma.iloc[-2] and fast_sma.iloc[-1] > slow_sma.iloc[-1]:
            return Signal.BUY
        if fast_sma.iloc[-2] > slow_sma.iloc[-2] and fast_sma.iloc[-1] < slow_sma.iloc[-1]:
            return Signal.SELL
        return Signal.HOLD
