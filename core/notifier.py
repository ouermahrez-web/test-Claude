import requests
from .logger import get_logger

log = get_logger("notifier")


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send(self, message: str) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            log.warning("Telegram notification failed: %s", e)
            return False


class NullNotifier:
    def send(self, message: str) -> bool:
        return True
