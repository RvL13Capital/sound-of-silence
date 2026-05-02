"""
Step 2: Price data ingestion, fundamental metadata, and universe filtering.

Downloads daily OHLCV history for the full DACH universe via yfinance,
enriches with fundamental metadata (market cap, sector, industry),
applies the v3 strategy filters, and saves clean data to Parquet.

Run from the dach_momentum project root:
    python -m dach_momentum.data
"""
from __future__ import annotations

import datetime as _dt
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
# Cache helpers
# ========================================================================== #


def _file_age_seconds(path: Path) -> float:
    """Return the age of *path* in seconds based on its mtime."""
    return time.time() - path.stat().st_mtime


def _file_age_days(path: Path) -> float:
    """Return the age of *path* in fractional days."""
    return _file_age_seconds(path) / 86400.0


def _ticker_to_filename(ticker: str) -> str:
    """Convert a yfinance ticker to a safe Parquet filename stem."""
    return ticker.replace("/", "_").replace(".", "_")


def _filename_to_ticker(stem: str) -> str:
    """Best-effort reverse of ``_ticker_to_filename``."""
    # Reconstruct common yfinance suffixes
    for suffix in (
        ".DE", ".VI", ".SW", ".PA", ".AS", ".BR", ".MI", ".MC",
        ".ST", ".CO", ".HE", ".OL", ".LS", ".WA", ".L", ".AT",
    ):
        tag = suffix.replace(".", "_")          # e.g. "_DE"
        if stem.endswith(tag):
            return stem[: -len(tag)] + suffix
    return stem


# ========================================================================== #
# Price data download
# ========================================================================== #


def download_prices(
    tickers: list[str],
    start: str = "2005-01-01",
    end: Optional[str] = None,
    batch_size: int = 20,
    pause_secs: float = 1.0,
    refresh: bool = False,
) -> dict[str, pd.DataFrame]:
    """
    Download daily OHLCV data for a list of yfinance tickers.

    Downloads in batches to avoid rate limiting.  Returns a dict
    mapping yf_ticker -> DataFrame with columns:
        Date, Open, High, Low, Close, Adj Close, Volume

    Caching behaviour (per-ticker Parquet files in ``data/prices/``):
    * If a cached file exists and is < 1 day old, skip the download.
    * If a cached file exists but is older, do an incremental download
      (fetch only from the last cached date onward and append).
    * Pass ``refresh=True`` to bypass the cache entirely.

    Tickers that return no data are logged and skipped.
    """
    results: dict[str, pd.DataFrame] = {}
    failed: list[str] = []
    to_download: list[str] = []
    # Mapping ticker -> incremental start date (None = full download)
    incremental_starts: dict[str, Optional[str]] = {}
    cached_count = 0

    one_day = 86400.0  # seconds

    for ticker in tickers:
        if refresh:
            to_download.append(ticker)
            incremental_starts[ticker] = None
            continue

        safe = _ticker_to_filename(ticker)
        cache_path = config.PRICES_DIR / f"{safe}.parquet"

        if cache_path.exists():
            age = _file_age_seconds(cache_path)
            if age < one_day:
                # Fresh cache — use as-is
                try:
                    results[ticker] = pd.read_parquet(cache_path)
                    cached_count += 1
                    continue
                except Exception:
                    pass  # fall through to download

            # Stale cache — incremental download
            try:
                cached_df = pd.read_parquet(cache_path)
                last_date = str(pd.Timestamp(cached_df.index.max()).date())
                results[ticker] = cached_df  # will be extended later
                incremental_starts[ticker] = last_date
            except Exception:
                incremental_starts[ticker] = None
            to_download.append(ticker)
        else:
            to_download.append(ticker)
            incremental_starts[ticker] = None

    total = len(tickers)

    if not to_download:
        logger.info(
            "Using cached data (less than 1 day old). "
            "Use --refresh to force re-download."
        )
        print(
            "Using cached data (less than 1 day old). "
            "Use --refresh to force re-download."
        )
        logger.info(
            "Cache report: %d/%d tickers served from cache, 0 downloaded",
            cached_count, total,
        )
        return results

    logger.info(
        "Cache report: %d/%d tickers served from cache, %d to download",
        cached_count, total, len(to_download),
    )

    dl_total = len(to_download)

    for i in range(0, dl_total, batch_size):
        batch = to_download[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (dl_total + batch_size - 1) // batch_size
        logger.info(
            "Downloading batch %d/%d (%d tickers): %s ...",
            batch_num, total_batches, len(batch),
            ", ".join(batch[:5]) + ("..." if len(batch) > 5 else ""),
        )

        # Determine start date for batch: use earliest incremental start
        # or the global start if any ticker needs a full download.
        batch_start = start
        if all(incremental_starts.get(t) for t in batch):
            batch_start = min(incremental_starts[t] for t in batch)  # type: ignore[arg-type]

        def _do_batch_download(tickers_batch, dl_start):
            return yf.download(
                tickers=tickers_batch,
                start=dl_start,
                end=end,
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False,
            )

        # First attempt
        try:
            data = _do_batch_download(batch, batch_start)
        except Exception as exc:
            logger.warning("Batch %d/%d failed: %s — retrying in 5 s ...",
                           batch_num, total_batches, exc)
            time.sleep(5)
            logger.info("Retrying batch %d/%d after failure...",
                        batch_num, total_batches)
            try:
                data = _do_batch_download(batch, batch_start)
            except Exception as exc2:
                logger.error("Batch %d/%d failed on retry: %s",
                             batch_num, total_batches, exc2)
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
                results[ticker] = _merge_incremental(
                    results.get(ticker), df,
                )
            else:
                failed.append(ticker)
        else:
            for ticker in batch:
                try:
                    if ticker in data.columns.get_level_values(0):
                        df = data[ticker].dropna(how="all")
                        if len(df) > 0:
                            df.index.name = "Date"
                            results[ticker] = _merge_incremental(
                                results.get(ticker), df,
                            )
                        else:
                            failed.append(ticker)
                    else:
                        failed.append(ticker)
                except (KeyError, TypeError):
                    failed.append(ticker)

        # Be polite to yfinance servers
        if i + batch_size < dl_total:
            time.sleep(pause_secs)

    downloaded_count = len(results) - cached_count
    logger.info(
        "Download complete: %d/%d tickers succeeded "
        "(%d from cache, %d freshly downloaded), %d failed",
        len(results), total, cached_count, downloaded_count, len(failed),
    )
    if failed:
        logger.warning("Failed tickers: %s", ", ".join(sorted(failed)))

    return results


def _merge_incremental(
    old: Optional[pd.DataFrame],
    new: pd.DataFrame,
) -> pd.DataFrame:
    """Merge an incremental download with previously cached data."""
    if old is None or old.empty:
        return new
    combined = pd.concat([old, new])
    combined = combined[~combined.index.duplicated(keep="last")]
    return combined.sort_index()


# ========================================================================== #
# Fundamental metadata
# ========================================================================== #


def fetch_metadata(tickers: list[str], refresh: bool = False) -> pd.DataFrame:
    """
    Fetch fundamental metadata for each ticker via yfinance .info.

    Returns a DataFrame indexed by yf_ticker with columns:
        market_cap, sector, industry, currency, exchange,
        short_name, quote_type

    This is slow (~1-2 sec per ticker) because yfinance makes
    individual HTTP requests.  Results are cached to disk.

    The cache expires after 7 days.  Pass ``refresh=True`` to
    force a full re-fetch regardless of age.
    """
    cache_path = config.CACHE_DIR / "metadata_cache.csv"

    METADATA_EXPIRY_DAYS = 7

    # Load cache if exists and is not expired
    cached: dict[str, dict] = {}
    if cache_path.exists() and not refresh:
        cache_age = _file_age_days(cache_path)
        if cache_age < METADATA_EXPIRY_DAYS:
            cached_df = pd.read_csv(cache_path, encoding="utf-8")
            for _, row in cached_df.iterrows():
                cached[row["yf_ticker"]] = row.to_dict()
            logger.info(
                "Loaded %d cached metadata entries (cache age: %.1f days)",
                len(cached), cache_age,
            )
        else:
            logger.info(
                "Metadata cache is %.1f days old (> %d day expiry) — "
                "re-fetching all metadata",
                cache_age, METADATA_EXPIRY_DAYS,
            )
    elif cache_path.exists() and refresh:
        logger.info("Metadata cache exists but --refresh forced; re-fetching all")

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
        ticker = _filename_to_ticker(path.stem)
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
# Data freshness report
# ========================================================================== #


def print_data_freshness() -> None:
    """
    Print a summary of how old each data artefact is.

    Checks universe.csv, price data (newest file in data/prices/),
    metadata cache, and signals directory.  Each line is tagged
    OK (fresh) or STALE (needs update) with a suggested command.
    """
    import datetime as dt

    print("\nDATA FRESHNESS REPORT")

    items: list[tuple[str, Path, float, str]] = []

    # Universe
    if config.UNIVERSE_CSV.exists():
        age = _file_age_days(config.UNIVERSE_CSV)
        items.append(("Universe", config.UNIVERSE_CSV, age,
                       "python -m dach_momentum universe --refresh"))
    else:
        items.append(("Universe", config.UNIVERSE_CSV, -1,
                       "python -m dach_momentum universe"))

    # Price data — use the most recently modified parquet file
    price_files = list(config.PRICES_DIR.glob("*.parquet"))
    if price_files:
        newest = max(price_files, key=lambda p: p.stat().st_mtime)
        age = _file_age_days(newest)
        items.append(("Price data", newest, age,
                       "python -m dach_momentum data --refresh"))
    else:
        items.append(("Price data", config.PRICES_DIR, -1,
                       "python -m dach_momentum data"))

    # Metadata cache
    meta_cache = config.CACHE_DIR / "metadata_cache.csv"
    if meta_cache.exists():
        age = _file_age_days(meta_cache)
        items.append(("Metadata", meta_cache, age,
                       "python -m dach_momentum data --refresh"))
    else:
        items.append(("Metadata", meta_cache, -1,
                       "python -m dach_momentum data"))

    # Signals
    signals_dir = config.DATA_DIR / "signals"
    sig_files = list(signals_dir.glob("*.parquet")) if signals_dir.exists() else []
    if sig_files:
        newest_sig = max(sig_files, key=lambda p: p.stat().st_mtime)
        age = _file_age_days(newest_sig)
        items.append(("Signals", newest_sig, age,
                       "python -m dach_momentum signals"))
    else:
        items.append(("Signals", signals_dir, -1,
                       "python -m dach_momentum signals"))

    for label, path, age_days, remedy in items:
        if age_days < 0:
            date_str = "MISSING"
            status = "MISSING"
            hint = f"(run: {remedy})"
        else:
            file_date = dt.datetime.fromtimestamp(path.stat().st_mtime)
            date_str = file_date.strftime("%Y-%m-%d")
            int_days = int(age_days)
            day_word = "day" if int_days == 1 else "days"
            if age_days < 2:
                status = "OK"
                hint = ""
            elif age_days < 7:
                status = "OK"
                hint = ""
            else:
                status = "STALE"
                hint = f"(run: {remedy})"

            date_str = f"{date_str} ({int_days} {day_word} old)"

        line = f"  {label + ':' :<14} {date_str:<35} — {status}"
        if hint:
            line += f"  {hint}"
        print(line)

    print()


# ========================================================================== #
# CLI entry point
# ========================================================================== #


def main(refresh: bool = False) -> None:
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
    prices = download_prices(tickers, refresh=refresh)

    # --- Save prices ---
    print("\n[2/5] Saving price data to Parquet...")
    save_prices(prices)

    # --- Fetch metadata ---
    print("\n[3/5] Fetching fundamental metadata (this takes a few minutes)...")
    valid_tickers = [t for t in tickers if t in prices]
    metadata = fetch_metadata(valid_tickers, refresh=refresh)

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
