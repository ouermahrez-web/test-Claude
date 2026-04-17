import pandas as pd
import ta
from .base import BaseStrategy, Signal


class BollingerStrategy(BaseStrategy):
    """Buy when price touches lower band + RSI oversold. Sell at upper band."""

    def analyze(self, df: pd.DataFrame) -> Signal:
        period = self.params.get("period", 20)
        std_dev = self.params.get("std_dev", 2.0)
        rsi_period = self.params.get("rsi_period", 14)

        if not self._validate_df(df, min_rows=period + rsi_period):
            return Signal.HOLD

        close = df["close"]
        bb = ta.volatility.BollingerBands(close, window=period, window_dev=std_dev)
        rsi = ta.momentum.RSIIndicator(close, window=rsi_period).rsi()

        last_close = close.iloc[-1]
        lower = bb.bollinger_lband().iloc[-1]
        upper = bb.bollinger_hband().iloc[-1]
        last_rsi = rsi.iloc[-1]

        if last_close <= lower and last_rsi < 35:
            return Signal.BUY
        if last_close >= upper:
            return Signal.SELL
        return Signal.HOLD
