"""
BTC daily price data via the CoinDesk Data API (CCIX composite index).

Used as a secondary regime filter alongside CDAX. The CCIX composite is an
exchange-aggregated BTC-USD index and is more robust than any single venue.

Run from the dach_momentum project root to refresh the cache:
    python -m dach_momentum.btc_data
"""
from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path

import pandas as pd
import requests

from . import config

logger = logging.getLogger(__name__)

COINDESK_DAILY_URL = "https://data-api.cryptocompare.com/index/cc/v1/historical/days"
COINDESK_FUNDING_URL = "https://data-api.cryptocompare.com/futures/v1/historical/funding-rate/days"
INDEX_MARKET = "ccix"
INDEX_INSTRUMENT = "BTC-USD"
FUNDING_MARKET = "binance"
FUNDING_INSTRUMENT = "BTC-USDT-VANILLA-PERPETUAL"
PAGE_LIMIT = 5000  # API max per call for daily candles

BTC_DAILY_CSV = config.DATA_DIR / "btc_daily.csv"
BTC_FUNDING_CSV = config.DATA_DIR / "btc_funding.csv"


def _fetch_page(to_ts: int | None = None) -> list[dict]:
    params = {
        "market": INDEX_MARKET,
        "instrument": INDEX_INSTRUMENT,
        "limit": PAGE_LIMIT,
    }
    if to_ts is not None:
        params["to_ts"] = to_ts
    resp = requests.get(COINDESK_DAILY_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    err = payload.get("Err") or {}
    if err:
        raise RuntimeError(f"CoinDesk API error: {err}")
    return payload.get("Data", [])


def fetch_btc_history(start_date: str = "2010-01-01") -> pd.DataFrame:
    """Fetch full daily BTC-USD history from CoinDesk CCIX, paginating backward."""
    start_ts = int(pd.Timestamp(start_date).timestamp())
    rows: list[dict] = []
    to_ts: int | None = None

    while True:
        page = _fetch_page(to_ts=to_ts)
        if not page:
            break
        rows.extend(page)
        oldest_ts = page[0]["TIMESTAMP"]
        if oldest_ts <= start_ts or len(page) < PAGE_LIMIT:
            break
        to_ts = oldest_ts - 86400  # next call ends just before this page's oldest
        logger.info("  fetched through %s; paginating back...",
                    _dt.date.fromtimestamp(oldest_ts))

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["TIMESTAMP"]).sort_values("TIMESTAMP")
    df["date"] = pd.to_datetime(df["TIMESTAMP"], unit="s", utc=True).dt.tz_localize(None)
    df = df[["date", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME", "QUOTE_VOLUME"]]
    df = df.rename(columns={
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VOLUME": "volume_btc",
        "QUOTE_VOLUME": "volume_usd",
    })
    df = df[df["date"] >= pd.Timestamp(start_date)].reset_index(drop=True)
    return df


def save_btc_history(df: pd.DataFrame, path: Path = BTC_DAILY_CSV) -> None:
    df.to_csv(path, index=False)
    logger.info("Saved %d BTC daily records to %s (%s -> %s)",
                len(df), path, df["date"].min().date(), df["date"].max().date())


def load_btc_close() -> pd.Series | None:
    """Load the cached BTC close series indexed by date. Returns None if missing."""
    if not BTC_DAILY_CSV.exists():
        return None
    df = pd.read_csv(BTC_DAILY_CSV, parse_dates=["date"])
    return df.set_index("date")["close"].sort_index()


# --------------------------------------------------------------------------- #
# Funding rate (BTC perp on Binance) — proxy for crypto-leverage stress
# --------------------------------------------------------------------------- #

def _fetch_funding_page(to_ts: int | None = None) -> list[dict]:
    params = {
        "market": FUNDING_MARKET,
        "instrument": FUNDING_INSTRUMENT,
        "limit": PAGE_LIMIT,
    }
    if to_ts is not None:
        params["to_ts"] = to_ts
    resp = requests.get(COINDESK_FUNDING_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    err = payload.get("Err") or {}
    if err:
        raise RuntimeError(f"CoinDesk API error: {err}")
    return payload.get("Data", [])


def fetch_btc_funding() -> pd.DataFrame:
    """Fetch full daily BTC perp funding-rate history (Binance, USDT-margined)."""
    rows: list[dict] = []
    to_ts: int | None = None
    while True:
        page = _fetch_funding_page(to_ts=to_ts)
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE_LIMIT:
            break
        to_ts = page[0]["TIMESTAMP"] - 86400

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["TIMESTAMP"]).sort_values("TIMESTAMP").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["TIMESTAMP"], unit="s", utc=True).dt.tz_localize(None)
    df = df[["date", "OPEN", "HIGH", "LOW", "CLOSE"]].rename(columns={
        "OPEN": "fr_open", "HIGH": "fr_high", "LOW": "fr_low", "CLOSE": "fr_close",
    })
    return df


def save_btc_funding(df: pd.DataFrame, path: Path = BTC_FUNDING_CSV) -> None:
    df.to_csv(path, index=False)
    logger.info("Saved %d BTC funding records to %s (%s -> %s)",
                len(df), path, df["date"].min().date(), df["date"].max().date())


def load_btc_funding() -> pd.Series | None:
    """Load the cached funding-rate close series indexed by date. None if missing."""
    if not BTC_FUNDING_CSV.exists():
        return None
    df = pd.read_csv(BTC_FUNDING_CSV, parse_dates=["date"])
    return df.set_index("date")["fr_close"].sort_index()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
    logger.info("Fetching BTC daily price history from CoinDesk (%s/%s)...",
                INDEX_MARKET, INDEX_INSTRUMENT)
    df = fetch_btc_history()
    save_btc_history(df)
    logger.info("Fetching BTC perp funding rate from CoinDesk (%s/%s)...",
                FUNDING_MARKET, FUNDING_INSTRUMENT)
    fr = fetch_btc_funding()
    save_btc_funding(fr)


if __name__ == "__main__":
    main()
