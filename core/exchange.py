import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from .logger import get_logger

log = get_logger("exchange")

TESTNET_URL = "https://testnet.binance.vision/api"


class BinanceExchange:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.testnet = testnet
        if testnet:
            self.client = Client(api_key, api_secret, testnet=True)
        else:
            self.client = Client(api_key, api_secret)
        log.info("Exchange connected (testnet=%s)", testnet)

    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
        raw = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df

    def get_balance(self, asset: str) -> float:
        try:
            info = self.client.get_asset_balance(asset=asset)
            return float(info["free"]) if info else 0.0
        except BinanceAPIException as e:
            log.error("Balance error for %s: %s", asset, e)
            return 0.0

    def get_symbol_price(self, symbol: str) -> float:
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except BinanceAPIException as e:
            log.error("Price error for %s: %s", symbol, e)
            return 0.0

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict | None:
        try:
            order = self.client.order_market(symbol=symbol, side=side, quantity=quantity)
            log.info("Order placed: %s %s %.6f @ market", side, symbol, quantity)
            return order
        except BinanceAPIException as e:
            log.error("Order error %s %s: %s", side, symbol, e)
            return None

    def get_symbol_info(self, symbol: str) -> dict | None:
        try:
            return self.client.get_symbol_info(symbol)
        except BinanceAPIException as e:
            log.error("Symbol info error %s: %s", symbol, e)
            return None

    def round_step_size(self, symbol: str, quantity: float) -> float:
        info = self.get_symbol_info(symbol)
        if not info:
            return round(quantity, 6)
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
                precision = len(str(step).rstrip("0").split(".")[-1])
                return round(quantity - (quantity % step), precision)
        return round(quantity, 6)
