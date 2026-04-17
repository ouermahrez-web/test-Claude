import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config(path: str = None) -> dict:
    config_path = path or BASE_DIR / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


class Config:
    def __init__(self, config_path: str = None):
        self._cfg = load_config(config_path)

        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
        self.trading_mode = os.getenv("TRADING_MODE", "paper").lower()

        self.symbols: list = self._cfg["trading"]["symbols"]
        self.interval: str = self._cfg["trading"]["interval"]
        self.strategy: str = self._cfg["trading"]["strategy"]
        self.max_open_trades: int = self._cfg["trading"]["max_open_trades"]
        self.stake_amount: float = self._cfg["trading"]["stake_amount"]
        self.stake_currency: str = self._cfg["trading"]["stake_currency"]
        self.max_stake_per_trade: float = self._cfg["trading"]["max_stake_per_trade"]
        self.stop_loss_pct: float = self._cfg["trading"]["stop_loss_pct"]
        self.take_profit_pct: float = self._cfg["trading"]["take_profit_pct"]
        self.trailing_stop: bool = self._cfg["trading"]["trailing_stop"]
        self.trailing_stop_pct: float = self._cfg["trading"]["trailing_stop_pct"]

        self.strategy_params: dict = self._cfg["strategies"].get(self.strategy, {})

        risk = self._cfg["risk_management"]
        self.max_daily_loss_pct: float = risk["max_daily_loss_pct"]
        self.max_drawdown_pct: float = risk["max_drawdown_pct"]
        self.cooldown_minutes: int = risk["cooldown_after_loss_minutes"]

        notif = self._cfg["notifications"]
        self.notifications_enabled: bool = notif["enabled"]
        self.telegram_token: str = notif["telegram_token"]
        self.telegram_chat_id: str = notif["telegram_chat_id"]

        bot = self._cfg["bot"]
        self.dry_run: bool = bot["dry_run"]
        self.loop_interval: int = bot["loop_interval_seconds"]
        self.log_level: str = bot["log_level"]

    @property
    def is_live(self) -> bool:
        return self.trading_mode == "live" and not self.dry_run

    def validate(self) -> None:
        if self.is_live and (not self.api_key or not self.api_secret):
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET are required for live trading.")
        if not self.symbols:
            raise ValueError("At least one trading symbol must be configured.")
        if self.stop_loss_pct <= 0 or self.take_profit_pct <= 0:
            raise ValueError("stop_loss_pct and take_profit_pct must be positive.")
