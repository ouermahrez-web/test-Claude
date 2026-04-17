import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from .logger import get_logger

log = get_logger("trade_manager")
TRADES_FILE = Path(__file__).resolve().parent.parent / "logs" / "trades.json"


@dataclass
class Trade:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    stake: float
    stop_loss: float
    take_profit: float
    open_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    order_id: str = ""
    is_open: bool = True
    close_price: float = 0.0
    close_time: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0


class TradeManager:
    def __init__(self):
        self.trades: list[Trade] = []
        self._load()

    def open_trade(self, trade: Trade) -> None:
        self.trades.append(trade)
        log.info("Trade opened: %s %s entry=%.4f qty=%.6f", trade.side, trade.symbol, trade.entry_price, trade.quantity)
        self._save()

    def close_trade(self, symbol: str, close_price: float) -> Trade | None:
        for t in self.trades:
            if t.symbol == symbol and t.is_open:
                t.is_open = False
                t.close_price = close_price
                t.close_time = datetime.utcnow().isoformat()
                t.pnl = (close_price - t.entry_price) * t.quantity
                t.pnl_pct = ((close_price - t.entry_price) / t.entry_price) * 100
                log.info("Trade closed: %s PnL=%.2f USDT (%.2f%%)", symbol, t.pnl, t.pnl_pct)
                self._save()
                return t
        return None

    def get_open_trade(self, symbol: str) -> Trade | None:
        return next((t for t in self.trades if t.symbol == symbol and t.is_open), None)

    def open_trades(self) -> list[Trade]:
        return [t for t in self.trades if t.is_open]

    def daily_pnl(self) -> float:
        today = datetime.utcnow().date().isoformat()
        return sum(t.pnl for t in self.trades if not t.is_open and t.close_time.startswith(today))

    def _save(self) -> None:
        TRADES_FILE.parent.mkdir(exist_ok=True)
        with open(TRADES_FILE, "w") as f:
            json.dump([asdict(t) for t in self.trades], f, indent=2)

    def _load(self) -> None:
        if TRADES_FILE.exists():
            with open(TRADES_FILE) as f:
                data = json.load(f)
            self.trades = [Trade(**d) for d in data]
            open_count = len(self.open_trades())
            if open_count:
                log.info("Loaded %d open trade(s) from disk.", open_count)
