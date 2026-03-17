"""Angel One SmartAPI real-time paper trading bot.

This module converts the notebook strategy into a production-style, paper-only
bot that follows official SmartAPI SDK usage patterns:

- SmartConnect(api_key)
- generateSession(client_code, pin/password, totp)
- getfeedToken()
- getProfile(refreshToken)
- getCandleData() + ltpData()

It never places real orders. Wrapper methods for order APIs are included for
SDK compatibility checks and future extension.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pyotp
from dateutil.relativedelta import relativedelta
from SmartApi import SmartConnect

try:
    # Optional: only required if websocket streaming mode is enabled.
    from SmartApi.smartWebSocketV2 import SmartWebSocketV2
except Exception:  # pragma: no cover - runtime optional import
    SmartWebSocketV2 = None


# ------------------------------ Logging ---------------------------------
logging.basicConfig(
    level=os.getenv("BOT_LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("angel-paper-bot")


# ------------------------------ Config ----------------------------------
@dataclass(frozen=True)
class BotConfig:
    api_key: str
    client_code: str
    pin: str
    totp_secret: str
    capital: float = 300000.0
    leverage: int = 5
    max_trades: int = 2
    risk_per_trade: float = 0.01
    volume_filter: bool = True
    poll_interval_seconds: int = 300
    symbols_per_cycle: int = 8
    symbol_request_gap_seconds: float = 1.2
    interval: str = "FIVE_MINUTE"
    candle_lookback_days: int = 5
    market_start: dt.time = dt.time(9, 15)
    market_end: dt.time = dt.time(15, 30)
    retry_count: int = 3
    retry_delay_seconds: float = 1.0
    rate_limit_cooldown_seconds: int = 30
    enable_websocket: bool = False
    trade_log_file: Path = Path("paper_trades.csv")
    equity_log_file: Path = Path("paper_equity.csv")


@dataclass
class Position:
    stock: str
    exchange: str
    token: str
    direction: str
    entry_time: dt.datetime
    entry_price: float
    qty: int
    atr: float
    capital_used: float
    entry_candle: dt.datetime
    high_price: Optional[float] = None
    low_price: Optional[float] = None


TOKENS = {
    "RVNL": {"exchange": "NSE", "token": "9552"}, "IFCI": {"exchange": "NSE", "token": "1491"},
    "IRFC": {"exchange": "NSE", "token": "2029"}, "APOLLO": {"exchange": "NSE", "token": "1134"},
    "SUZLON": {"exchange": "NSE", "token": "12018"}, "ADANIGREEN": {"exchange": "NSE", "token": "3563"},
    "ADANIPORTS": {"exchange": "NSE", "token": "15083"}, "ASTRAMICRO": {"exchange": "NSE", "token": "11618"},
    "AZAD": {"exchange": "NSE", "token": "20905"}, "BEL": {"exchange": "NSE", "token": "383"},
    "RITES": {"exchange": "NSE", "token": "3761"}, "WELCORP": {"exchange": "NSE", "token": "11821"},
    "MMTC": {"exchange": "NSE", "token": "17957"}, "NAZARA": {"exchange": "NSE", "token": "2987"},
    "BHARTIHEXA": {"exchange": "NSE", "token": "23489"}, "JIOFIN": {"exchange": "NSE", "token": "18143"},
    "LTFOODS": {"exchange": "NSE", "token": "13816"}, "BSE": {"exchange": "NSE", "token": "19585"},
    "PAYTM": {"exchange": "NSE", "token": "6705"}, "ATGL": {"exchange": "NSE", "token": "6066"},
    "WAAREEENER": {"exchange": "NSE", "token": "25907"}, "AEROFLEX": {"exchange": "NSE", "token": "18268"},
    "HFCL": {"exchange": "NSE", "token": "21951"}, "BANDHANBNK": {"exchange": "NSE", "token": "2263"},
    "RBLBANK": {"exchange": "NSE", "token": "18391"}, "CGCL": {"exchange": "NSE", "token": "20329"},
    "NBCC": {"exchange": "NSE", "token": "31415"}, "BDL": {"exchange": "NSE", "token": "2144"},
    "INDIANB": {"exchange": "NSE", "token": "14309"}, "PETRONET": {"exchange": "NSE", "token": "11351"},
    "CGPOWER": {"exchange": "NSE", "token": "760"}, "FEDERALBNK": {"exchange": "NSE", "token": "1023"},
    "FORTIS": {"exchange": "NSE", "token": "14592"}, "PBFINTECH": {"exchange": "NSE", "token": "6656"},
    "MAXHEALTH": {"exchange": "NSE", "token": "22377"}, "UNIONBANK": {"exchange": "NSE", "token": "10753"},
    "SJVN": {"exchange": "NSE", "token": "18883"}, "LUMAXTECH": {"exchange": "NSE", "token": "14014"},
    "GRSE": {"exchange": "NSE", "token": "5475"}, "MAZDOCK": {"exchange": "NSE", "token": "509"},
    "ITI": {"exchange": "NSE", "token": "1675"}, "BANKINDIA": {"exchange": "NSE", "token": "4745"},
    "TITAGARH": {"exchange": "NSE", "token": "15414"}, "IRCON": {"exchange": "NSE", "token": "4986"},
    "IRCTC": {"exchange": "NSE", "token": "13611"}, "RECLTD": {"exchange": "NSE", "token": "15355"},
    "TEJASNET": {"exchange": "NSE", "token": "21131"}, "INDUSTOWER": {"exchange": "NSE", "token": "29135"},
    "JUBLFOOD": {"exchange": "NSE", "token": "18096"}, "SIEMENS": {"exchange": "NSE", "token": "3150"},
    "VOLTAS": {"exchange": "NSE", "token": "3718"}, "LUPIN": {"exchange": "NSE", "token": "10440"},
    "INFY": {"exchange": "NSE", "token": "1594"}, "HCLTECH": {"exchange": "NSE", "token": "7229"},
    "BHARTIARTL": {"exchange": "NSE", "token": "10604"}, "HUBTOWN": {"exchange": "NSE", "token": "14203"},
    "IGL": {"exchange": "NSE", "token": "11262"}, "VMM": {"exchange": "NSE", "token": "27969"},
    "HDFCBANK": {"exchange": "NSE", "token": "1330"}, "ICICIBANK": {"exchange": "NSE", "token": "11991"},
    "SBIN": {"exchange": "NSE", "token": "3045"}, "AXISBANK": {"exchange": "NSE", "token": "5900"},
    "KOTAKBANK": {"exchange": "NSE", "token": "1922"}, "INDUSINDBK": {"exchange": "NSE", "token": "5258"},
    "BANKBARODA": {"exchange": "NSE", "token": "4668"}, "PNB": {"exchange": "NSE", "token": "2733"},
    "IDFCFIRSTB": {"exchange": "NSE", "token": "1801"}, "AUBANK": {"exchange": "NSE", "token": "17656"},
}


def load_config_from_env() -> BotConfig:
    """Load runtime config from environment variables.

    Required:
    - ANGEL_API_KEY
    - ANGEL_CLIENT_CODE
    - ANGEL_PIN (or password/pin used by SmartAPI)
    - ANGEL_TOTP_SECRET

    Backward compatibility: if these are missing and key.txt exists, read key.txt
    format: API_KEY REFRESH_TOKEN CLIENT_CODE PIN TOTP_SECRET.
    """
    api_key = os.getenv("ANGEL_API_KEY")
    client_code = os.getenv("ANGEL_CLIENT_CODE")
    pin = os.getenv("ANGEL_PIN")
    totp_secret = os.getenv("ANGEL_TOTP_SECRET")

    if not all([api_key, client_code, pin, totp_secret]):
        key_path = Path("key.txt")
        if key_path.exists():
            parts = key_path.read_text(encoding="utf-8").split()
            if len(parts) >= 5:
                api_key = api_key or parts[0]
                client_code = client_code or parts[2]
                pin = pin or parts[3]
                totp_secret = totp_secret or parts[4]

    missing = [
        name
        for name, value in [
            ("ANGEL_API_KEY", api_key),
            ("ANGEL_CLIENT_CODE", client_code),
            ("ANGEL_PIN", pin),
            ("ANGEL_TOTP_SECRET", totp_secret),
        ]
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    return BotConfig(
        api_key=api_key,
        client_code=client_code,
        pin=pin,
        totp_secret=totp_secret,
        symbols_per_cycle=int(os.getenv("SYMBOLS_PER_CYCLE", "8")),
        symbol_request_gap_seconds=float(os.getenv("SYMBOL_REQUEST_GAP_SECONDS", "1.2")),
        rate_limit_cooldown_seconds=int(os.getenv("RATE_LIMIT_COOLDOWN_SECONDS", "30")),
        enable_websocket=os.getenv("ENABLE_SMARTAPI_WS", "false").lower() == "true",
    )


class SmartApiClient:
    """Thin resilient wrapper over official SmartAPI SDK methods."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.smart_api: Optional[SmartConnect] = None
        self.auth_data: Optional[dict] = None
        self.feed_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.profile: Optional[dict] = None
        self._ws = None
        self.rate_limited_until: Optional[float] = None

    def login(self) -> None:
        self.smart_api = SmartConnect(self.config.api_key)
        totp = pyotp.TOTP(self.config.totp_secret).now()

        # Official pattern: generateSession(client_code, pin/password, totp)
        self.auth_data = self.smart_api.generateSession(self.config.client_code, self.config.pin, totp)
        if not self.auth_data or not self.auth_data.get("status"):
            raise RuntimeError(f"SmartAPI login failed: {self.auth_data}")

        data = self.auth_data.get("data", {})
        self.refresh_token = data.get("refreshToken")

        # Official follow-up methods requested by user.
        self.feed_token = self.smart_api.getfeedToken()
        self.profile = self.smart_api.getProfile(self.refresh_token)
        logger.info("SmartAPI login successful for client=%s", self.config.client_code)

    def ensure_session(self) -> None:
        if self.smart_api is None:
            self.login()
            return
        try:
            self.safe_get_profile()
        except Exception:
            logger.warning("Session check failed; refreshing/relogin.")
            self.refresh_or_relogin()

    def refresh_or_relogin(self) -> None:
        if not self.smart_api:
            self.login()
            return
        try:
            if self.refresh_token:
                refreshed = self.smart_api.generateToken(self.refresh_token)
                if refreshed and refreshed.get("status"):
                    self.feed_token = self.smart_api.getfeedToken()
                    logger.info("Session refresh successful via generateToken.")
                    return
        except Exception as exc:
            logger.warning("generateToken refresh failed: %s", exc)
        self.login()

    def _retry(self, fn, *args, **kwargs):
        last_exc = None
        for attempt in range(1, self.config.retry_count + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                logger.warning("API call failed attempt %s/%s: %s", attempt, self.config.retry_count, exc)
                if attempt < self.config.retry_count:
                    time.sleep(self.config.retry_delay_seconds * attempt)
                    self.refresh_or_relogin()
        raise RuntimeError(f"API call failed after retries: {last_exc}")

    def _handle_rate_limit(self, response: dict) -> bool:
        if response.get("status") is False and response.get("errorcode") == "AB1019":
            self.rate_limited_until = time.time() + self.config.rate_limit_cooldown_seconds
            logger.warning(
                "SmartAPI rate limit hit (AB1019). Cooling down for %ss.",
                self.config.rate_limit_cooldown_seconds,
            )
            return True
        return False

    def in_rate_limit_cooldown(self) -> bool:
        return bool(self.rate_limited_until and time.time() < self.rate_limited_until)

    def safe_get_profile(self):
        return self._retry(self.smart_api.getProfile, self.refresh_token)

    def get_historical_candles(self, exchange: str, token: str, interval: str, days: int) -> pd.DataFrame:
        now = dt.datetime.now()
        fromdate = (now - relativedelta(days=days)).strftime("%Y-%m-%d 09:15")
        todate = now.strftime("%Y-%m-%d %H:%M")
        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": interval,
            "fromdate": fromdate,
            "todate": todate,
        }
        response = self._retry(self.smart_api.getCandleData, params)
        if self._handle_rate_limit(response):
            return pd.DataFrame()
        if not response.get("status") or not response.get("data"):
            return pd.DataFrame()
        df = pd.DataFrame(response["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df.set_index("datetime")

    def get_ltp(self, exchange: str, tradingsymbol: str, symboltoken: str) -> Optional[float]:
        response = self._retry(self.smart_api.ltpData, exchange, tradingsymbol, symboltoken)
        if self._handle_rate_limit(response):
            return None
        if response.get("status"):
            ltp_data = response.get("data", {})
            value = ltp_data.get("ltp")
            return float(value) if value is not None else None
        return None

    # Real-order APIs intentionally wrapped but unused in this paper bot.
    def place_order(self, order_params: dict) -> dict:
        return self._retry(self.smart_api.placeOrder, order_params)

    def modify_order(self, order_params: dict) -> dict:
        return self._retry(self.smart_api.modifyOrder, order_params)

    def cancel_order(self, order_id: str, variety: str = "NORMAL") -> dict:
        return self._retry(self.smart_api.cancelOrder, order_id, variety)

    def get_positions(self) -> dict:
        return self._retry(self.smart_api.position)

    def get_holdings(self) -> dict:
        return self._retry(self.smart_api.holding)

    def connect_websocket(self, tokens: List[Tuple[str, str]]) -> None:
        if not self.config.enable_websocket:
            return
        if SmartWebSocketV2 is None:
            logger.warning("ENABLE_SMARTAPI_WS=true but SmartWebSocketV2 import unavailable.")
            return

        self._ws = SmartWebSocketV2(self.auth_data["data"]["jwtToken"], self.config.api_key, self.config.client_code, self.feed_token)

        def on_open(_):
            subscribe_list = [{"exchangeType": 1, "tokens": [t for _, t in tokens]}]
            self._ws.subscribe("paper_bot", 1, subscribe_list)
            logger.info("WebSocket subscribed for %s symbols.", len(tokens))

        def on_data(_, message):
            # Hook point for streaming-based logic.
            logger.debug("WS tick: %s", message)

        def on_error(_, error):
            logger.warning("WS error: %s", error)

        self._ws.on_open = on_open
        self._ws.on_data = on_data
        self._ws.on_error = on_error
        self._ws.connect()


class PatternStrategy:
    def __init__(self, volume_filter: bool = True):
        self.volume_filter = volume_filter

    @staticmethod
    def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if len(df) < 20:
            return pd.DataFrame()
        df["MA20"] = df["close"].rolling(window=20).mean()
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - df["close"].shift()).abs(),
                (df["low"] - df["close"].shift()).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()
        df["RSI"] = self.compute_rsi(df["close"], 14)
        return df.dropna()

    def detect_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["3WS"] = False
        df["3BC"] = False
        for i in range(2, len(df)):
            c1, c2, c3 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]

            ws_checks = [
                c1["close"] > c1["open"] * 1.002,
                c2["close"] > c2["open"] * 1.002,
                c3["close"] > c3["open"] * 1.002,
                c2["open"] > c1["open"],
                c3["open"] > c2["open"],
                c2["close"] > c1["close"],
                c3["close"] > c2["close"],
            ]
            bc_checks = [
                c1["close"] < c1["open"] * 0.998,
                c2["close"] < c2["open"] * 0.998,
                c3["close"] < c3["open"] * 0.998,
                c2["open"] < c1["open"],
                c3["open"] < c2["open"],
                c2["close"] < c1["close"],
                c3["close"] < c2["close"],
            ]
            if self.volume_filter:
                vol_check = c1["volume"] < c2["volume"] < c3["volume"]
                ws_checks.append(vol_check)
                bc_checks.append(vol_check)
            if all(ws_checks):
                df.at[df.index[i], "3WS"] = True
            if all(bc_checks):
                df.at[df.index[i], "3BC"] = True
        return df

    def signal(self, row: pd.Series) -> Optional[str]:
        if bool(row.get("3WS")) and row["close"] > row["MA20"] and row["RSI"] < 70:
            return "long"
        if bool(row.get("3BC")) and row["close"] < row["MA20"] and row["RSI"] > 30:
            return "short"
        return None


class PaperExecutionEngine:
    def __init__(self, config: BotConfig):
        self.config = config
        self.capital = config.capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[dict] = []
        self.equity_rows: List[dict] = []

    @staticmethod
    def mtm(position: Position, price: float) -> float:
        pnl_per_share = (price - position.entry_price) if position.direction == "long" else (position.entry_price - price)
        return pnl_per_share * position.qty

    def can_open(self, capital_required: float) -> bool:
        capital_used = sum(p.capital_used for p in self.positions.values())
        return len(self.positions) < self.config.max_trades and capital_required <= (self.capital - capital_used)

    def compute_qty(self, entry_price: float) -> int:
        stop_distance = entry_price * 0.01
        qty_risk = int((self.config.risk_per_trade * self.capital) / stop_distance)
        max_position_size = self.config.leverage * self.capital
        valid_qty = [q for q in [100, 200, 500, 1000, 2000, 3000, 4000, 5000] if q * entry_price <= max_position_size]
        if not valid_qty:
            return 0
        return max(0, min(qty_risk, max(valid_qty)))

    def try_entry(self, stock: str, exchange: str, token: str, now: dt.datetime, candle_ts: dt.datetime, row: pd.Series, direction: str) -> None:
        if stock in self.positions:
            return
        entry_price = float(row["close"])
        atr = float(row["ATR"])
        if atr <= 0:
            return
        qty = self.compute_qty(entry_price)
        if qty <= 0:
            return
        capital_required = (qty * entry_price) / self.config.leverage
        if not self.can_open(capital_required):
            return
        pos = Position(
            stock=stock,
            exchange=exchange,
            token=token,
            direction=direction,
            entry_time=now,
            entry_price=entry_price,
            qty=qty,
            atr=atr,
            capital_used=capital_required,
            entry_candle=candle_ts,
            high_price=entry_price if direction == "long" else None,
            low_price=entry_price if direction == "short" else None,
        )
        self.positions[stock] = pos
        logger.info("ENTRY %s %s qty=%s @ %.2f", stock, direction.upper(), qty, entry_price)

    def manage_exit(self, stock: str, row: pd.Series, now: dt.datetime) -> None:
        if stock not in self.positions:
            return
        pos = self.positions[stock]
        close_price = float(row["close"])

        if pos.direction == "long":
            pos.high_price = max(pos.high_price or pos.entry_price, float(row["high"]))
            target = pos.entry_price + 1.5 * pos.atr
            stop = pos.entry_price * 0.99
            trailing = (pos.high_price or pos.entry_price) * 0.99
            hit = "target_hit" if close_price >= target else "stop_loss" if close_price <= stop else "trailing_stop" if close_price <= trailing else None
        else:
            pos.low_price = min(pos.low_price or pos.entry_price, float(row["low"]))
            target = pos.entry_price - 1.5 * pos.atr
            stop = pos.entry_price * 1.01
            trailing = (pos.low_price or pos.entry_price) * 1.01
            hit = "target_hit" if close_price <= target else "stop_loss" if close_price >= stop else "trailing_stop" if close_price >= trailing else None

        bars_held = int((row.name - pos.entry_candle).total_seconds() // 300)
        reason = hit or ("time_exit" if bars_held >= 6 else None)
        if reason:
            pnl = self.mtm(pos, close_price)
            self.capital += pnl
            self.trades.append(
                {
                    "stock": stock,
                    "direction": pos.direction,
                    "entry_time": pos.entry_time,
                    "exit_time": now,
                    "entry_price": pos.entry_price,
                    "exit_price": close_price,
                    "qty": pos.qty,
                    "net_pnl": pnl,
                    "reason": reason,
                }
            )
            del self.positions[stock]
            logger.info("EXIT %s pnl=%.2f reason=%s", stock, pnl, reason)

    def snapshot(self, now: dt.datetime, ltp_prices: Dict[str, float]) -> None:
        unrealized = sum(self.mtm(pos, ltp_prices.get(sym, pos.entry_price)) for sym, pos in self.positions.items())
        equity = self.capital + unrealized
        self.equity_rows.append(
            {
                "timestamp": now,
                "capital": self.capital,
                "unrealized": unrealized,
                "equity": equity,
                "open_positions": len(self.positions),
            }
        )
        pd.DataFrame(self.trades).to_csv(self.config.trade_log_file, index=False)
        pd.DataFrame(self.equity_rows).to_csv(self.config.equity_log_file, index=False)
        logger.info("EQUITY %.2f | CAPITAL %.2f | UPNL %.2f | OPEN %s", equity, self.capital, unrealized, len(self.positions))


class RealTimePaperBot:
    def __init__(self, config: BotConfig, symbols: Dict[str, Dict[str, str]]):
        self.config = config
        self.symbols = symbols
        self.api = SmartApiClient(config)
        self.strategy = PatternStrategy(volume_filter=config.volume_filter)
        self.engine = PaperExecutionEngine(config)
        self.last_signal_candle: Dict[str, pd.Timestamp] = {}
        self.symbol_queue = deque(self.symbols.keys())

    def should_trade_now(self, now: dt.datetime) -> bool:
        return self.config.market_start <= now.time() <= self.config.market_end and now.weekday() < 5

    def run(self) -> None:
        self.api.login()
        if self.config.enable_websocket:
            token_pairs = [(meta["exchange"], meta["token"]) for _, meta in self.symbols.items()]
            self.api.connect_websocket(token_pairs)

        logger.info("Paper bot started. Press Ctrl+C to stop.")
        while True:
            now = dt.datetime.now()
            if not self.should_trade_now(now):
                logger.info("Market closed window. Sleeping 60s.")
                time.sleep(60)
                continue

            self.api.ensure_session()
            ltp_prices: Dict[str, float] = {}

            if self.api.in_rate_limit_cooldown():
                wait_left = max(1, int(self.api.rate_limited_until - time.time()))
                logger.info("Rate-limit cooldown active. Sleeping %ss.", wait_left)
                time.sleep(wait_left)
                continue

            cycle_symbols = []
            for _ in range(min(self.config.symbols_per_cycle, len(self.symbol_queue))):
                s = self.symbol_queue.popleft()
                cycle_symbols.append(s)
                self.symbol_queue.append(s)

            for stock in cycle_symbols:
                meta = self.symbols[stock]
                exchange, token = meta["exchange"], meta["token"]
                try:
                    candles = self.api.get_historical_candles(exchange, token, self.config.interval, self.config.candle_lookback_days)
                    if candles.empty:
                        continue
                    df = self.strategy.add_indicators(candles)
                    if df.empty:
                        continue
                    df = self.strategy.detect_patterns(df)
                    last = df.iloc[-1]
                    last_ts = df.index[-1]

                    self.engine.manage_exit(stock, last, now)

                    if stock in self.engine.positions:
                        ltp = self.api.get_ltp(exchange, stock, token)
                        if ltp is not None:
                            ltp_prices[stock] = ltp

                    if self.last_signal_candle.get(stock) == last_ts:
                        continue
                    signal = self.strategy.signal(last)
                    if signal:
                        self.engine.try_entry(stock, exchange, token, now, last_ts, last, signal)
                        self.last_signal_candle[stock] = last_ts
                except Exception as exc:
                    logger.warning("%s failed: %s", stock, exc)

                time.sleep(self.config.symbol_request_gap_seconds)

            self.engine.snapshot(now, ltp_prices)
            time.sleep(self.config.poll_interval_seconds)


def main() -> None:
    config = load_config_from_env()
    bot = RealTimePaperBot(config, TOKENS)
    bot.run()


if __name__ == "__main__":
    main()
