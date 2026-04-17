#!/usr/bin/env python3
"""
Binance Auto-Trader — entry point.

Usage:
    python main.py                        # start with default config.json
    python main.py --config my_cfg.json  # custom config file
    python main.py --once                 # run a single cycle then exit
    python main.py --backtest             # show last signals without trading
"""

import argparse
import sys
from pathlib import Path

from core.config import Config
from core.logger import get_logger
from bot import TradingBot

log = get_logger("main")


def parse_args():
    parser = argparse.ArgumentParser(description="Binance Auto-Trader")
    parser.add_argument("--config", default="config.json", help="Path to config JSON file")
    parser.add_argument("--once", action="store_true", help="Run a single analysis cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Override config to force dry-run mode")
    return parser.parse_args()


def main():
    args = parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        log.error("Config file not found: %s", cfg_path)
        sys.exit(1)

    cfg = Config(str(cfg_path))
    if args.dry_run:
        cfg.dry_run = True

    try:
        cfg.validate()
    except ValueError as e:
        log.error("Configuration error: %s", e)
        sys.exit(1)

    log.info("=" * 60)
    log.info("  Binance Auto-Trader")
    log.info("  Strategy  : %s", cfg.strategy)
    log.info("  Symbols   : %s", ", ".join(cfg.symbols))
    log.info("  Interval  : %s", cfg.interval)
    log.info("  Mode      : %s", "DRY RUN (paper)" if cfg.dry_run else "LIVE")
    log.info("  Testnet   : %s", cfg.use_testnet)
    log.info("=" * 60)

    bot = TradingBot(cfg)

    if args.once:
        bot.run_once()
    else:
        bot.run()


if __name__ == "__main__":
    main()
