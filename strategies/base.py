from abc import ABC, abstractmethod
from enum import Enum
import pandas as pd


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    def __init__(self, params: dict):
        self.params = params

    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> Signal:
        """Return BUY, SELL, or HOLD based on the OHLCV dataframe."""

    def _validate_df(self, df: pd.DataFrame, min_rows: int = 50) -> bool:
        return df is not None and len(df) >= min_rows
