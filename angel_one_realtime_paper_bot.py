"""Real-time paper trading bot for Angel One SmartAPI.

This script is a production-style conversion of the notebook strategy into a
continuous paper-trading loop. It does not place real orders; instead it keeps
track of virtual positions, P&L, exits, and trade logs.
"""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import pyotp
from dateutil.relativedelta import relativedelta
from SmartApi import SmartConnect

# ------------------------- Strategy configuration -------------------------
CAPITAL = 300000.0
LEVERAGE = 5
MAX_TRADES = 2
VOLUME_FILTER = True
RISK_PER_TRADE = 0.01
POLL_INTERVAL_SECONDS = 300  # 5 minutes
INTERVAL = "FIVE_MINUTE"
CANDLE_LOOKBACK_DAYS = 5
MARKET_START = dt.time(9, 15)
MARKET_END = dt.time(15, 30)

TRADE_LOG_FILE = Path("paper_trades.csv")
EQUITY_LOG_FILE = Path("paper_equity.csv")

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


@dataclass
class Position:
    stock: str
    direction: str
    entry_time: dt.datetime
    entry_price: float
    qty: int
    atr: float
    capital_used: float
    entry_candle: dt.datetime
    high_price: Optional[float] = None
    low_price: Optional[float] = None


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def detect_three_white_soldiers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["3WS"] = False
    for i in range(2, len(df)):
        c1, c2, c3 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
        checks = [
            c1["close"] > c1["open"] * 1.002,
            c2["close"] > c2["open"] * 1.002,
            c3["close"] > c3["open"] * 1.002,
            c2["open"] > c1["open"],
            c3["open"] > c2["open"],
            c2["close"] > c1["close"],
            c3["close"] > c2["close"],
        ]
        if VOLUME_FILTER:
            checks.append(c1["volume"] < c2["volume"] < c3["volume"])
        if all(checks):
            df.at[df.index[i], "3WS"] = True
    return df


def detect_three_black_crows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["3BC"] = False
    for i in range(2, len(df)):
        c1, c2, c3 = df.iloc[i - 2], df.iloc[i - 1], df.iloc[i]
        checks = [
            c1["close"] < c1["open"] * 0.998,
            c2["close"] < c2["open"] * 0.998,
            c3["close"] < c3["open"] * 0.998,
            c2["open"] < c1["open"],
            c3["open"] < c2["open"],
            c2["close"] < c1["close"],
            c3["close"] < c2["close"],
        ]
        if VOLUME_FILTER:
            checks.append(c1["volume"] < c2["volume"] < c3["volume"])
        if all(checks):
            df.at[df.index[i], "3BC"] = True
    return df


def load_credentials(path: str = "key.txt") -> list[str]:
    parts = Path(path).read_text(encoding="utf-8").split()
    if len(parts) < 5:
        raise ValueError("key.txt must contain: API_KEY REFRESH_TOKEN CLIENT_CODE PASSWORD TOTP_SECRET")
    return parts


def create_session() -> SmartConnect:
    key_secret = load_credentials()
    smart_api = SmartConnect(api_key=key_secret[0])
    login = smart_api.generateSession(
        clientCode=key_secret[2],
        password=key_secret[3],
        totp=pyotp.TOTP(key_secret[4]).now(),
    )
    if not login.get("status"):
        raise RuntimeError(f"Login failed: {login.get('message', 'unknown error')}")
    return smart_api


def fetch_candles(smart_api: SmartConnect, symbol: str, exchange: str, token: str) -> pd.DataFrame:
    fromdate = (dt.datetime.now() - relativedelta(days=CANDLE_LOOKBACK_DAYS)).strftime("%Y-%m-%d 09:15")
    todate = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": INTERVAL,
        "fromdate": fromdate,
        "todate": todate,
    }

    response = smart_api.getCandleData(params)
    if not response.get("status") or not response.get("data"):
        return pd.DataFrame()

    df = pd.DataFrame(response["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

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
    df["RSI"] = compute_rsi(df["close"], 14)
    df = detect_three_white_soldiers(df)
    df = detect_three_black_crows(df)
    return df.dropna()


def mark_to_market(position: Position, price: float) -> float:
    pnl_per_share = (price - position.entry_price) if position.direction == "long" else (position.entry_price - price)
    return pnl_per_share * position.qty


def should_trade_now(now: dt.datetime) -> bool:
    return MARKET_START <= now.time() <= MARKET_END and now.weekday() < 5


def run() -> None:
    smart_api = create_session()
    current_capital = CAPITAL
    positions: Dict[str, Position] = {}
    trades = []
    equity_rows = []
    last_signal_candle: Dict[str, pd.Timestamp] = {}

    print("✅ Paper bot started. Press Ctrl+C to stop.")
    while True:
        cycle_time = dt.datetime.now()
        if not should_trade_now(cycle_time):
            print(f"[{cycle_time:%Y-%m-%d %H:%M:%S}] Market closed. Sleeping...")
            time.sleep(60)
            continue

        latest_prices = {}

        for stock, info in TOKENS.items():
            try:
                df = fetch_candles(smart_api, stock, info["exchange"], info["token"])
                time.sleep(0.35)  # small delay for API hygiene
                if df.empty:
                    continue

                last = df.iloc[-1]
                last_ts = df.index[-1]
                latest_prices[stock] = float(last["close"])

                # -------- Exit management --------
                if stock in positions:
                    pos = positions[stock]
                    close_price = float(last["close"])
                    if pos.direction == "long":
                        pos.high_price = max(pos.high_price or pos.entry_price, float(last["high"]))
                        target = pos.entry_price + 1.5 * pos.atr
                        stop = pos.entry_price * 0.99
                        trailing = (pos.high_price or pos.entry_price) * 0.99
                        exit_reason = None
                        if close_price >= target:
                            exit_reason = "target_hit"
                        elif close_price <= stop:
                            exit_reason = "stop_loss"
                        elif close_price <= trailing:
                            exit_reason = "trailing_stop"
                    else:
                        pos.low_price = min(pos.low_price or pos.entry_price, float(last["low"]))
                        target = pos.entry_price - 1.5 * pos.atr
                        stop = pos.entry_price * 1.01
                        trailing = (pos.low_price or pos.entry_price) * 1.01
                        exit_reason = None
                        if close_price <= target:
                            exit_reason = "target_hit"
                        elif close_price >= stop:
                            exit_reason = "stop_loss"
                        elif close_price >= trailing:
                            exit_reason = "trailing_stop"

                    bars_held = int((last_ts - pos.entry_candle).total_seconds() // 300)
                    if bars_held >= 6 and exit_reason is None:
                        exit_reason = "time_exit"

                    if exit_reason:
                        pnl = mark_to_market(pos, close_price)
                        current_capital += pnl
                        trades.append(
                            {
                                "stock": stock,
                                "direction": pos.direction,
                                "entry_time": pos.entry_time,
                                "exit_time": cycle_time,
                                "entry_price": pos.entry_price,
                                "exit_price": close_price,
                                "qty": pos.qty,
                                "net_pnl": pnl,
                                "reason": exit_reason,
                            }
                        )
                        print(f"❎ EXIT {stock} {pos.direction.upper()} pnl={pnl:.2f} reason={exit_reason}")
                        del positions[stock]

                # -------- Entry management --------
                if stock in positions or len(positions) >= MAX_TRADES:
                    continue

                if last_signal_candle.get(stock) == last_ts:
                    continue

                direction = None
                if bool(last.get("3WS")) and last["close"] > last["MA20"] and last["RSI"] < 70:
                    direction = "long"
                elif bool(last.get("3BC")) and last["close"] < last["MA20"] and last["RSI"] > 30:
                    direction = "short"

                if direction is None:
                    continue

                entry_price = float(last["close"])
                atr = float(last["ATR"])
                if atr <= 0:
                    continue

                stop_distance = entry_price * 0.01
                qty_risk = int((RISK_PER_TRADE * current_capital) / stop_distance)
                max_position_size = LEVERAGE * current_capital
                valid_qty = [q for q in [100, 200, 500, 1000, 2000, 3000, 4000, 5000] if q * entry_price <= max_position_size]
                if not valid_qty:
                    continue

                qty = min(qty_risk, max(valid_qty))
                if qty <= 0:
                    continue

                capital_required = (qty * entry_price) / LEVERAGE
                capital_used = sum(p.capital_used for p in positions.values())
                if capital_required > (current_capital - capital_used):
                    continue

                pos = Position(
                    stock=stock,
                    direction=direction,
                    entry_time=cycle_time,
                    entry_price=entry_price,
                    qty=qty,
                    atr=atr,
                    capital_used=capital_required,
                    entry_candle=last_ts,
                    high_price=entry_price if direction == "long" else None,
                    low_price=entry_price if direction == "short" else None,
                )
                positions[stock] = pos
                last_signal_candle[stock] = last_ts
                print(f"✅ ENTRY {stock} {direction.upper()} qty={qty} @ {entry_price:.2f}")
            except Exception as exc:
                print(f"⚠️ {stock}: {exc}")

        unrealized = sum(mark_to_market(pos, latest_prices.get(sym, pos.entry_price)) for sym, pos in positions.items())
        equity = current_capital + unrealized
        equity_rows.append(
            {
                "timestamp": cycle_time,
                "capital": current_capital,
                "unrealized": unrealized,
                "equity": equity,
                "open_positions": len(positions),
            }
        )

        pd.DataFrame(trades).to_csv(TRADE_LOG_FILE, index=False)
        pd.DataFrame(equity_rows).to_csv(EQUITY_LOG_FILE, index=False)
        print(
            f"[{cycle_time:%H:%M:%S}] Equity={equity:.2f} Capital={current_capital:.2f} "
            f"Unrealized={unrealized:.2f} Open={len(positions)}"
        )

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
