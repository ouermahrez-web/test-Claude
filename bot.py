import time
from datetime import datetime

from core.config import Config
from core.exchange import BinanceExchange
from core.logger import get_logger
from core.trade_manager import Trade, TradeManager
from core.notifier import TelegramNotifier, NullNotifier
from strategies import get_strategy
from strategies.base import Signal

log = get_logger("bot")


class PaperExchange:
    """Simulates order execution without real API calls."""

    def __init__(self, config: Config):
        self._cfg = config
        self._balances: dict[str, float] = {config.stake_currency: 10_000.0}
        self._prices: dict[str, float] = {}

    def get_klines(self, symbol, interval, limit=200):
        from binance.client import Client
        client = Client("", "", testnet=self._cfg.use_testnet)
        import pandas as pd
        raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df

    def get_symbol_price(self, symbol: str) -> float:
        from binance.client import Client
        client = Client("", "", testnet=self._cfg.use_testnet)
        ticker = client.get_symbol_ticker(symbol=symbol)
        price = float(ticker["price"])
        self._prices[symbol] = price
        return price

    def get_balance(self, asset: str) -> float:
        return self._balances.get(asset, 0.0)

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        price = self._prices.get(symbol, 0.0)
        base = symbol.replace(self._cfg.stake_currency, "")
        if side == "BUY":
            cost = price * quantity
            self._balances[self._cfg.stake_currency] = self._balances.get(self._cfg.stake_currency, 0) - cost
            self._balances[base] = self._balances.get(base, 0) + quantity
        else:
            proceeds = price * quantity
            self._balances[self._cfg.stake_currency] = self._balances.get(self._cfg.stake_currency, 0) + proceeds
            self._balances[base] = max(0.0, self._balances.get(base, 0) - quantity)
        log.info("[PAPER] %s %s %.6f @ %.4f", side, symbol, quantity, price)
        return {"orderId": f"paper_{int(time.time())}", "status": "FILLED", "price": str(price)}

    def round_step_size(self, symbol: str, quantity: float) -> float:
        return round(quantity, 6)


class TradingBot:
    def __init__(self, config: Config):
        self.cfg = config
        self.strategy = get_strategy(config.strategy, config.strategy_params)
        self.trade_mgr = TradeManager()

        if config.dry_run:
            self.exchange = PaperExchange(config)
            log.info("Running in DRY RUN (paper trading) mode.")
        else:
            self.exchange = BinanceExchange(config.api_key, config.api_secret, testnet=config.use_testnet)

        if config.notifications_enabled and config.telegram_token:
            self.notifier = TelegramNotifier(config.telegram_token, config.telegram_chat_id)
        else:
            self.notifier = NullNotifier()

        self._running = False

    def _check_exit_conditions(self, trade: Trade, current_price: float) -> bool:
        """Return True if a stop-loss or take-profit was hit."""
        if current_price <= trade.stop_loss:
            log.warning("STOP-LOSS hit for %s @ %.4f", trade.symbol, current_price)
            self._close_trade(trade, current_price, reason="stop-loss")
            return True
        if current_price >= trade.take_profit:
            log.info("TAKE-PROFIT hit for %s @ %.4f", trade.symbol, current_price)
            self._close_trade(trade, current_price, reason="take-profit")
            return True

        if self.cfg.trailing_stop:
            trail_price = current_price * (1 - self.cfg.trailing_stop_pct / 100)
            if trail_price > trade.stop_loss:
                trade.stop_loss = trail_price

        return False

    def _close_trade(self, trade: Trade, price: float, reason: str) -> None:
        qty = self.exchange.round_step_size(trade.symbol, trade.quantity)
        self.exchange.place_market_order(trade.symbol, "SELL", qty)
        closed = self.trade_mgr.close_trade(trade.symbol, price)
        if closed:
            msg = (
                f"*Trade closed* [{reason.upper()}]\n"
                f"Symbol: `{trade.symbol}`\n"
                f"Entry: `{trade.entry_price:.4f}` → Exit: `{price:.4f}`\n"
                f"PnL: `{closed.pnl:.2f} USDT ({closed.pnl_pct:.2f}%)`"
            )
            self.notifier.send(msg)

    def _open_trade(self, symbol: str, price: float) -> None:
        balance = self.exchange.get_balance(self.cfg.stake_currency)
        stake = min(self.cfg.stake_amount, self.cfg.max_stake_per_trade, balance * 0.95)
        if stake < 10:
            log.warning("Insufficient balance for %s (%.2f %s)", symbol, balance, self.cfg.stake_currency)
            return

        quantity = self.exchange.round_step_size(symbol, stake / price)
        if quantity <= 0:
            return

        order = self.exchange.place_market_order(symbol, "BUY", quantity)
        if not order:
            return

        sl = price * (1 - self.cfg.stop_loss_pct / 100)
        tp = price * (1 + self.cfg.take_profit_pct / 100)

        trade = Trade(
            symbol=symbol,
            side="BUY",
            entry_price=price,
            quantity=quantity,
            stake=stake,
            stop_loss=sl,
            take_profit=tp,
            order_id=str(order.get("orderId", "")),
        )
        self.trade_mgr.open_trade(trade)
        msg = (
            f"*Trade opened* BUY\n"
            f"Symbol: `{symbol}`\n"
            f"Entry: `{price:.4f}`  Qty: `{quantity:.6f}`\n"
            f"SL: `{sl:.4f}`  TP: `{tp:.4f}`"
        )
        self.notifier.send(msg)

    def _check_daily_loss_limit(self) -> bool:
        daily_pnl = self.trade_mgr.daily_pnl()
        limit = -(self.cfg.stake_amount * self.cfg.max_open_trades * self.cfg.max_daily_loss_pct / 100)
        if daily_pnl < limit:
            log.warning("Daily loss limit reached (%.2f USDT). Pausing.", daily_pnl)
            return True
        return False

    def process_symbol(self, symbol: str) -> None:
        try:
            df = self.exchange.get_klines(symbol, self.cfg.interval)
            price = float(df["close"].iloc[-1])

            open_trade = self.trade_mgr.get_open_trade(symbol)

            if open_trade:
                self._check_exit_conditions(open_trade, price)
                return

            if len(self.trade_mgr.open_trades()) >= self.cfg.max_open_trades:
                return

            signal = self.strategy.analyze(df)
            log.debug("%s signal: %s @ %.4f", symbol, signal.value, price)

            if signal == Signal.BUY:
                log.info("BUY signal for %s @ %.4f", symbol, price)
                self._open_trade(symbol, price)

        except Exception as e:
            log.error("Error processing %s: %s", symbol, e, exc_info=True)

    def run_once(self) -> None:
        if self._check_daily_loss_limit():
            return
        for symbol in self.cfg.symbols:
            self.process_symbol(symbol)

    def run(self) -> None:
        self._running = True
        log.info("Bot started | strategy=%s | symbols=%s | dry_run=%s",
                 self.cfg.strategy, self.cfg.symbols, self.cfg.dry_run)
        self.notifier.send("*Binance Auto-Trader started* ✅")

        try:
            while self._running:
                start = time.time()
                self.run_once()
                elapsed = time.time() - start
                sleep_time = max(0, self.cfg.loop_interval - elapsed)
                log.debug("Cycle done in %.1fs. Sleeping %.1fs.", elapsed, sleep_time)
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            log.info("Bot stopped by user.")
        finally:
            self._running = False
            self.notifier.send("*Binance Auto-Trader stopped* 🛑")

    def stop(self) -> None:
        self._running = False
