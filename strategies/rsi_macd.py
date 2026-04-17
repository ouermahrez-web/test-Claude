import pandas as pd
import ta
from .base import BaseStrategy, Signal


class RsiMacdStrategy(BaseStrategy):
    """Buy when RSI is oversold AND MACD crosses up. Sell on overbought or MACD cross down."""

    def analyze(self, df: pd.DataFrame) -> Signal:
        if not self._validate_df(df, min_rows=50):
            return Signal.HOLD

        rsi_period = self.params.get("rsi_period", 14)
        oversold = self.params.get("rsi_oversold", 30)
        overbought = self.params.get("rsi_overbought", 70)
        macd_fast = self.params.get("macd_fast", 12)
        macd_slow = self.params.get("macd_slow", 26)
        macd_signal = self.params.get("macd_signal", 9)

        close = df["close"]

        rsi = ta.momentum.RSIIndicator(close, window=rsi_period).rsi()
        macd_ind = ta.trend.MACD(close, window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
        macd_line = macd_ind.macd()
        signal_line = macd_ind.macd_signal()

        last_rsi = rsi.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        last_macd = macd_line.iloc[-1]
        prev_sig = signal_line.iloc[-2]
        last_sig = signal_line.iloc[-1]

        macd_cross_up = prev_macd < prev_sig and last_macd > last_sig
        macd_cross_down = prev_macd > prev_sig and last_macd < last_sig

        if last_rsi < oversold and macd_cross_up:
            return Signal.BUY
        if last_rsi > overbought or macd_cross_down:
            return Signal.SELL
        return Signal.HOLD
