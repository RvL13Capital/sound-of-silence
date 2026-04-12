"""
Step 2: Price data ingestion, fundamental metadata, and universe filtering.

Downloads daily OHLCV history for the full DACH universe via yfinance,
enriches with fundamental metadata (market cap, sector, industry),
applies the v3 strategy filters, and saves clean data to Parquet.

Run from the dach_momentum project root:
    python -m dach_momentum.data
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from . import config

logger = logging.getLogger(__name__)

# Suppress noisy yfinance logs
logging.getLogger("yfinance").setLevel(logging.WARNING)


# ========================================================================== #
# Price data download
# ========================================================================== #


def download_prices(
    tickers: list[str],
    start: str = "2005-01-01",
    end: Optional[str] = None,
    batch_size: int = 20,
    pause_secs: float = 1.0,
) -> dict[str, pd.DataFrame]:
    """
    Download daily OHLCV data for a list of yfinance tickers.

    Downloads in batches to avoid rate limiting.  Returns a dict
    mapping yf_ticker -> DataFrame with columns:
        Date, Open, High, Low, Close, Adj Close, Volume

    Tickers that return no data are logged and skipped.
    """
    results: dict[str, pd.DataFrame] = {}
    failed: list[str] = []
    total = len(tickers)

    for i in range(0, total, batch_size):
        batch = tickers[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        logger.info(
            "Downloading batch %d/%d (%d tickers): %s ...",
            batch_num, total_batches, len(batch),
            ", ".join(batch[:5]) + ("..." if len(batch) > 5 else ""),
        )

        try:
            data = yf.download(
                tickers=batch,
                start=start,
                end=end,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )
        except Exception as exc:
            logger.error("Batch download failed: %s", exc)
            failed.extend(batch)
            continue

        if data.empty:
            logger.warning("Batch returned empty DataFrame")
            failed.extend(batch)
            continue

        # yf.download with group_by="ticker" returns MultiIndex columns
        # when multiple tickers; single ticker returns flat columns.
        if len(batch) == 1:
            ticker = batch[0]
            if not data.empty and len(data) > 0:
                df = data.copy()
                df.index.name = "Date"
                results[ticker] = df
            else:
                failed.append(ticker)
        else:
            for ticker in batch:
                try:
                    if ticker in data.columns.get_level_values(0):
                        df = data[ticker].dropna(how="all")
                        if len(df) > 0:
                            df.index.name = "Date"
                            results[ticker] = df
                        else:
                            failed.append(ticker)
                    else:
                        failed.append(ticker)
                except (KeyError, TypeError):
                    failed.append(ticker)

        # Be polite to yfinance servers
        if i + batch_size < total:
            time.sleep(pause_secs)

    logger.info(
        "Download complete: %d/%d tickers succeeded, %d failed",
        len(results), total, len(failed),
    )
    if failed:
        logger.warning("Failed tickers: %s", ", ".join(sorted(failed)))

    return results


# ========================================================================== #
# Fundamental metadata
# ========================================================================== #


def fetch_metadata(tickers: list[str]) -> pd.DataFrame:
    """
    Fetch fundamental metadata for each ticker via yfinance .info.

    Returns a DataFrame indexed by yf_ticker with columns:
        market_cap, sector, industry, currency, exchange,
        short_name, quote_type

    This is slow (~1-2 sec per ticker) because yfinance makes
    individual HTTP requests.  Results are cached to disk.
    """
    cache_path = config.CACHE_DIR / "metadata_cache.csv"

    # Load cache if exists
    cached: dict[str, dict] = {}
    if cache_path.exists():
        cached_df = pd.read_csv(cache_path, encoding="utf-8")
        for _, row in cached_df.iterrows():
            cached[row["yf_ticker"]] = row.to_dict()
        logger.info("Loaded %d cached metadata entries", len(cached))

    rows: list[dict] = []
    to_fetch = [t for t in tickers if t not in cached]
    logger.info(
        "Fetching metadata: %d cached, %d to download",
        len(tickers) - len(to_fetch), len(to_fetch),
    )

    for i, ticker in enumerate(to_fetch):
        if (i + 1) % 10 == 0 or i == 0:
            logger.info("  metadata %d/%d: %s", i + 1, len(to_fetch), ticker)
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            rows.append({
                "yf_ticker": ticker,
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
                "short_name": info.get("shortName"),
                "quote_type": info.get("quoteType"),
                "avg_volume": info.get("averageVolume"),
                "avg_volume_10d": info.get("averageDailyVolume10Day"),
                "free_float": info.get("floatShares"),
                "shares_outstanding": info.get("sharesOutstanding"),
            })
        except Exception as exc:
            logger.debug("  metadata failed for %s: %s", ticker, exc)
            rows.append({"yf_ticker": ticker})

        # Small pause to avoid rate limits
        if (i + 1) % 5 == 0:
            time.sleep(0.5)

    # Merge cached + freshly fetched
    all_rows = [cached[t] for t in tickers if t in cached]
    all_rows.extend(rows)

    meta_df = pd.DataFrame(all_rows)

    # Update cache
    if rows:
        full_cache = pd.DataFrame(
            [cached[t] for t in cached] + rows
        )
        full_cache.to_csv(cache_path, index=False, encoding="utf-8")
        logger.info("Updated metadata cache: %d entries", len(full_cache))

    return meta_df


# ========================================================================== #
# Universe filtering
# ========================================================================== #


def compute_adv(
    prices: dict[str, pd.DataFrame],
    window: int = 60,
) -> dict[str, float]:
    """
    Compute average daily volume in local currency for each ticker
    over the trailing `window` trading days.

    ADV = mean(Close × Volume) over the window.
    """
    adv: dict[str, float] = {}
    for ticker, df in prices.items():
        if "Close" not in df.columns or "Volume" not in df.columns:
            continue
        recent = df.tail(window).copy()
        if len(recent) < window // 2:
            continue
        daily_value = recent["Close"] * recent["Volume"]
        adv[ticker] = float(daily_value.mean())
    return adv


def filter_universe(
    universe: pd.DataFrame,
    metadata: pd.DataFrame,
    adv_map: dict[str, float],
    prices: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Apply the v3 strategy filters to the raw universe:
    - Market cap: EUR 100M - EUR 2B
    - ADV: >= EUR 150k (60-day)
    - Sector: exclude financials, insurance, real estate
    - Listing age: >= 1 year of price history
    - Has price data at all

    Returns a filtered DataFrame with metadata columns merged in.
    """
    # Merge universe with metadata
    merged = universe.merge(
        metadata[["yf_ticker", "market_cap", "sector", "industry",
                  "currency", "exchange", "avg_volume", "free_float",
                  "shares_outstanding"]],
        on="yf_ticker",
        how="left",
        suffixes=("_wiki", "_yf"),
    )

    # Use yfinance sector if available, fall back to Wikipedia sector
    merged["sector_final"] = merged["sector_yf"].fillna(merged["sector_wiki"])

    # Add ADV
    merged["adv_60d"] = merged["yf_ticker"].map(adv_map)

    # Add price history length
    def _history_days(ticker: str) -> int:
        if ticker in prices:
            return len(prices[ticker])
        return 0

    merged["history_days"] = merged["yf_ticker"].apply(_history_days)

    n_start = len(merged)
    logger.info("Filtering universe: %d tickers before filters", n_start)

    # --- Filter: has price data ---
    merged = merged[merged["history_days"] > 0].copy()
    logger.info("  after has-price-data: %d", len(merged))

    # --- Filter: listing age ---
    merged = merged[
        merged["history_days"] >= config.MIN_LISTING_AGE_DAYS
    ].copy()
    logger.info("  after listing age (>=%d days): %d",
                config.MIN_LISTING_AGE_DAYS, len(merged))

    # --- Filter: market cap ---
    # Some tickers won't have market cap data; keep them (filter later)
    has_mcap = merged["market_cap"].notna()
    in_range = (
        (merged["market_cap"] >= config.MIN_MARKET_CAP_EUR) &
        (merged["market_cap"] <= config.MAX_MARKET_CAP_EUR)
    )
    merged = merged[~has_mcap | in_range].copy()
    logger.info("  after market cap (EUR %dM-%dB): %d",
                config.MIN_MARKET_CAP_EUR // 1_000_000,
                config.MAX_MARKET_CAP_EUR // 1_000_000_000,
                len(merged))

    # --- Filter: ADV ---
    has_adv = merged["adv_60d"].notna()
    adv_ok = merged["adv_60d"] >= config.MIN_AVG_DAILY_VOLUME_EUR
    merged = merged[~has_adv | adv_ok].copy()
    logger.info("  after ADV (>=EUR %dk): %d",
                config.MIN_AVG_DAILY_VOLUME_EUR // 1_000, len(merged))

    # --- Filter: sector exclusion ---
    excluded = config.EXCLUDED_SECTORS
    sector_ok = ~merged["sector_final"].fillna("").apply(
        lambda s: any(ex.lower() in s.lower() for ex in excluded)
    )
    merged = merged[sector_ok].copy()
    logger.info("  after sector exclusion: %d", len(merged))

    logger.info(
        "Filtered universe: %d -> %d tickers passed all filters",
        n_start, len(merged),
    )

    return merged.reset_index(drop=True)


# ========================================================================== #
# Data quality report
# ========================================================================== #


def data_quality_report(
    prices: dict[str, pd.DataFrame],
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce a summary of data quality for each ticker in the universe.
    """
    rows = []
    for _, urow in universe.iterrows():
        ticker = urow["yf_ticker"]
        df = prices.get(ticker)
        if df is None or df.empty:
            rows.append({
                "yf_ticker": ticker,
                "name": urow.get("name", ""),
                "has_data": False,
                "rows": 0,
            })
            continue

        rows.append({
            "yf_ticker": ticker,
            "name": urow.get("name", ""),
            "has_data": True,
            "rows": len(df),
            "start_date": str(df.index.min().date()) if len(df) > 0 else None,
            "end_date": str(df.index.max().date()) if len(df) > 0 else None,
            "pct_nan_close": float(df["Close"].isna().mean() * 100)
                if "Close" in df.columns else 100.0,
            "last_close": float(df["Close"].dropna().iloc[-1])
                if "Close" in df.columns and not df["Close"].dropna().empty
                else None,
        })

    return pd.DataFrame(rows)


# ========================================================================== #
# Persistence
# ========================================================================== #


def save_prices(prices: dict[str, pd.DataFrame]) -> None:
    """Save all price DataFrames to individual Parquet files."""
    config.PRICES_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for ticker, df in prices.items():
        safe_name = ticker.replace("/", "_").replace(".", "_")
        path = config.PRICES_DIR / f"{safe_name}.parquet"
        df.to_parquet(path)
        count += 1
    logger.info("Saved %d price files to %s", count, config.PRICES_DIR)


def load_prices(tickers: Optional[list[str]] = None) -> dict[str, pd.DataFrame]:
    """Load price DataFrames from Parquet files."""
    results = {}
    if not config.PRICES_DIR.exists():
        return results

    for path in config.PRICES_DIR.glob("*.parquet"):
        # Reconstruct ticker from filename
        ticker = path.stem.replace("_DE", ".DE").replace("_VI", ".VI").replace("_SW", ".SW")
        if tickers is not None and ticker not in tickers:
            continue
        results[ticker] = pd.read_parquet(path)

    logger.info("Loaded %d price files from %s", len(results), config.PRICES_DIR)
    return results


def save_filtered_universe(df: pd.DataFrame) -> None:
    """Save the filtered universe to CSV."""
    path = config.DATA_DIR / "universe_filtered.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Saved filtered universe to %s (%d rows)", path, len(df))


# ========================================================================== #
# CLI entry point
# ========================================================================== #


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    # --- Load universe ---
    from .universe import load_universe
    universe = load_universe()
    tickers = universe["yf_ticker"].tolist()
    logger.info("Loaded universe: %d tickers", len(tickers))

    # --- Download prices ---
    print("\n[1/5] Downloading price history...")
    prices = download_prices(tickers)

    # --- Save prices ---
    print("\n[2/5] Saving price data to Parquet...")
    save_prices(prices)

    # --- Fetch metadata ---
    print("\n[3/5] Fetching fundamental metadata (this takes a few minutes)...")
    valid_tickers = [t for t in tickers if t in prices]
    metadata = fetch_metadata(valid_tickers)

    # --- Compute ADV ---
    print("\n[4/5] Computing average daily volume...")
    adv_map = compute_adv(prices, window=60)

    # --- Filter universe ---
    print("\n[5/5] Applying strategy filters...")
    filtered = filter_universe(universe, metadata, adv_map, prices)
    save_filtered_universe(filtered)

    # --- Data quality report ---
    quality = data_quality_report(prices, universe)
    quality_path = config.DATA_DIR / "data_quality.csv"
    quality.to_csv(quality_path, index=False)

    # --- Summary ---
    sep = "=" * 60
    print(f"\n{sep}")
    print("STEP 2 COMPLETE — DATA INGESTION SUMMARY")
    print(sep)

    print(f"\nPrice data downloaded: {len(prices)}/{len(tickers)} tickers")

    no_data = [t for t in tickers if t not in prices]
    if no_data:
        print(f"No data returned for {len(no_data)} tickers:")
        for t in sorted(no_data)[:20]:
            print(f"  {t}")
        if len(no_data) > 20:
            print(f"  ... and {len(no_data) - 20} more")

    print(f"\nFiltered universe: {len(filtered)} tickers")
    print("\nBy country:")
    print(filtered["country"].value_counts().to_string())

    print("\nBy sector:")
    print(
        filtered["sector_final"]
        .fillna("(unknown)")
        .value_counts()
        .head(15)
        .to_string()
    )

    if "market_cap" in filtered.columns:
        has_mcap = filtered["market_cap"].dropna()
        if not has_mcap.empty:
            print(f"\nMarket cap range (EUR):")
            print(f"  Min:    {has_mcap.min():>15,.0f}")
            print(f"  Median: {has_mcap.median():>15,.0f}")
            print(f"  Max:    {has_mcap.max():>15,.0f}")

    print(f"\nFiles saved:")
    print(f"  Price data:        {config.PRICES_DIR}/ ({len(prices)} files)")
    print(f"  Filtered universe: {config.DATA_DIR / 'universe_filtered.csv'}")
    print(f"  Data quality:      {quality_path}")
    print(f"  Metadata cache:    {config.CACHE_DIR / 'metadata_cache.csv'}")
    print()


if __name__ == "__main__":
    main()
