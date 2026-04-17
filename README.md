# Binance Auto-Trader

Bot de trading automatique connecté à l'API Binance, supportant plusieurs stratégies sur plusieurs paires de crypto-monnaies.

---

## Fonctionnalités

- **4 stratégies** : RSI+MACD, SMA Cross, EMA Cross, Bollinger Bands
- **Mode Paper Trading** (dry run) — aucun argent réel n'est engagé
- **Stop-Loss / Take-Profit** automatiques
- **Trailing Stop** optionnel
- **Gestion du risque** : limite de perte journalière, drawdown max
- **Notifications Telegram** optionnelles
- **Logs colorés** en console + fichier `logs/bot.log`
- **Persistance des trades** dans `logs/trades.json`

---

## Installation

```bash
# 1. Cloner le dépôt
git clone <repo-url>
cd binance-auto-trader

# 2. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les clés API
cp .env.example .env
# Éditer .env et renseigner BINANCE_API_KEY / BINANCE_API_SECRET
```

---

## Configuration

### `.env`

```env
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=yyy
USE_TESTNET=True        # True = testnet Binance (recommandé pour débuter)
TRADING_MODE=paper      # paper | live
```

### `config.json`

| Clé | Description | Défaut |
|-----|-------------|--------|
| `symbols` | Paires à trader | `["BTCUSDT","ETHUSDT","BNBUSDT"]` |
| `interval` | Intervalle de bougie | `1h` |
| `strategy` | Stratégie active | `rsi_macd` |
| `max_open_trades` | Trades simultanés max | `3` |
| `stake_amount` | Mise par trade (USDT) | `50` |
| `stop_loss_pct` | Stop-loss en % | `2.0` |
| `take_profit_pct` | Take-profit en % | `4.0` |
| `trailing_stop` | Activer le trailing stop | `false` |
| `dry_run` | Mode paper trading | `true` |

---

## Utilisation

```bash
# Démarrer le bot (mode paper par défaut)
python main.py

# Une seule analyse puis arrêt
python main.py --once

# Forcer le mode dry-run
python main.py --dry-run

# Utiliser un fichier de config personnalisé
python main.py --config my_config.json
```

---

## Stratégies disponibles

| Nom | Description |
|-----|-------------|
| `rsi_macd` | Achète quand RSI < 30 ET MACD croise à la hausse |
| `sma_cross` | Golden cross / Death cross sur SMA |
| `ema_cross` | Croisement EMA rapide/lente |
| `bollinger` | Achat sur bande basse + RSI, vente sur bande haute |

---

## Notifications Telegram (optionnel)

1. Créer un bot via [@BotFather](https://t.me/BotFather)
2. Récupérer le token et votre `chat_id`
3. Dans `config.json` :
```json
"notifications": {
  "enabled": true,
  "telegram_token": "123456:ABC...",
  "telegram_chat_id": "987654321"
}
```

---

## Structure du projet

```
├── main.py               # Point d'entrée
├── bot.py                # Moteur principal du bot
├── config.json           # Configuration
├── requirements.txt
├── .env.example
├── core/
│   ├── config.py         # Chargement de la configuration
│   ├── exchange.py       # Interface Binance API
│   ├── trade_manager.py  # Gestion des trades ouverts/fermés
│   ├── notifier.py       # Notifications Telegram
│   └── logger.py         # Système de logs
└── strategies/
    ├── base.py           # Classe abstraite de stratégie
    ├── rsi_macd.py
    ├── sma_cross.py
    ├── ema_cross.py
    └── bollinger.py
```

---

## Avertissement

> **Ce bot est fourni à des fins éducatives.** Le trading de crypto-monnaies comporte des risques importants. Commencez toujours en mode `dry_run=true` et testez avec le testnet Binance avant tout trading réel.
