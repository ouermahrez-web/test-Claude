from .base import BaseStrategy
from .rsi_macd import RsiMacdStrategy
from .sma_cross import SmaCrossStrategy
from .ema_cross import EmaCrossStrategy
from .bollinger import BollingerStrategy

STRATEGIES = {
    "rsi_macd": RsiMacdStrategy,
    "sma_cross": SmaCrossStrategy,
    "ema_cross": EmaCrossStrategy,
    "bollinger": BollingerStrategy,
}


def get_strategy(name: str, params: dict):
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name](params)
