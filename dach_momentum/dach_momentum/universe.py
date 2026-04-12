"""
Universe construction for the DACH small/mid-cap momentum strategy.

Scrapes index constituents from Wikipedia, normalises ticker symbols
to yfinance-compatible format, deduplicates across overlapping indices,
and saves the result to CSV.

At this step we produce the RAW list of tickers plus metadata.
Market-cap / volume / free-float filtering happens at Step 2 after
we pull price and fundamental data.

Run from the project root:
    python -m dach_momentum.universe
"""
from __future__ import annotations

import logging
import re
from io import StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from . import config

logger = logging.getLogger(__name__)

USER_AGENT = (
    "DACH-Momentum-Research/0.1 "
    "(personal research project)"
)


# ========================================================================== #
# Low-level helpers
# ========================================================================== #


def _fetch_wikipedia_tables(url: str) -> list[pd.DataFrame]:
    """Fetch every HTML table from a Wikipedia page."""
    headers = {"User-Agent": USER_AGENT}
    logger.info("Fetching %s", url)
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return pd.read_html(StringIO(resp.text))


def _flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse pd.MultiIndex columns into single-level strings."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            " ".join(str(c) for c in col if str(c) != "").strip()
            for col in df.columns
        ]
    return df


def _find_constituent_table(
    tables: list[pd.DataFrame],
    min_rows: int = 10,
    max_rows: int = 300,
) -> Optional[pd.DataFrame]:
    """
    Heuristically select the index-constituent table from all tables
    on a Wikipedia page.  Picks the largest table whose columns include
    a plausible company-name or ticker keyword.
    """
    candidates: list[pd.DataFrame] = []

    for i, t in enumerate(tables):
        t = _flatten_multiindex(t.copy())
        if not (min_rows <= len(t) <= max_rows):
            continue

        cols_joined = " | ".join(str(c).lower() for c in t.columns)
        has_company_col = any(
            kw in cols_joined
            for kw in (
                "company", "name", "symbol", "ticker",
                "unternehmen", "firma",          # German labels
                "constituent",
            )
        )
        if has_company_col:
            candidates.append(t)
            logger.debug(
                "  candidate table %d: %d rows, cols=%s",
                i, len(t), list(t.columns)[:6],
            )

    if not candidates:
        return None
    return max(candidates, key=len)


def _first_matching_col(
    df: pd.DataFrame,
    candidates: list[str],
) -> Optional[str]:
    """
    Return the actual column name whose lower-cased, stripped form
    matches (exactly or as substring) any of *candidates*.
    """
    col_map = {str(c).lower().strip(): c for c in df.columns}

    # Exact match first
    for want in candidates:
        if want.lower() in col_map:
            return col_map[want.lower()]

    # Substring match
    for want in candidates:
        for col_lower, col_actual in col_map.items():
            if want.lower() in col_lower:
                return col_actual
    return None


def _clean_ticker(raw) -> Optional[str]:
    """Normalise a raw ticker value: uppercase, strip noise."""
    if pd.isna(raw):
        return None
    s = str(raw).strip().upper()
    # Remove Wikipedia reference annotations  [1], [note], etc.
    s = re.sub(r"\[.*?\]", "", s).strip()
    # Remove common exchange suffixes (we re-add the correct one later)
    s = re.sub(r"\.(DE|F|VI|SW|SWX)$", "", s)
    # Keep only alphanumeric, dots, dashes
    s = re.sub(r"[^A-Z0-9.\-]", "", s)
    return s or None


# ========================================================================== #
# Per-index scraper
# ========================================================================== #


def fetch_index_constituents(
    index_name: str,
    source: dict,
) -> pd.DataFrame:
    """
    Scrape one Wikipedia index page and return a tidy DataFrame:
        ticker | name | sector | country | suffix | index | yf_ticker
    Returns an empty DataFrame on any failure.
    """
    try:
        tables = _fetch_wikipedia_tables(source["url"])
    except Exception as exc:
        logger.error("Failed to fetch %s: %s", index_name, exc)
        return pd.DataFrame()

    table = _find_constituent_table(tables)
    if table is None:
        logger.warning(
            "No constituent table found for %s — page layout may have "
            "changed.  URL: %s", index_name, source["url"],
        )
        return pd.DataFrame()

    # Identify the columns we care about
    ticker_col = _first_matching_col(
        table,
        ["Symbol", "Ticker", "Ticker symbol", "Code", "Trading symbol"],
    )
    name_col = _first_matching_col(
        table,
        ["Company", "Name", "Company name", "Unternehmen", "Constituent"],
    )
    sector_col = _first_matching_col(
        table,
        [
            "GICS Sector", "Sector", "Industry", "GICS sector",
            "ICB Industry", "Prime Standard", "Branche",
        ],
    )

    if name_col is None:
        logger.warning(
            "No company-name column for %s; columns found: %s",
            index_name, list(table.columns),
        )
        return pd.DataFrame()

    suffix = source["suffix"]
    rows: list[dict] = []

    for _, row in table.iterrows():
        # --- name (mandatory) ---
        name_raw = row[name_col]
        if pd.isna(name_raw):
            continue
        name = re.sub(r"\[.*?\]", "", str(name_raw)).strip()
        if not name:
            continue

        # --- ticker ---
        ticker: Optional[str] = None
        if ticker_col is not None:
            ticker = _clean_ticker(row[ticker_col])

        if ticker is None:
            # Some pages embed the ticker in the name column after a comma
            # or in parentheses.  Skip the row if we truly can't find one.
            logger.debug("  skipping %s (%s): no ticker", name, index_name)
            continue

        # --- sector (optional) ---
        sector = None
        if sector_col is not None:
            raw_sector = row[sector_col]
            if pd.notna(raw_sector):
                sector = re.sub(r"\[.*?\]", "", str(raw_sector)).strip()

        yf_ticker = ticker if ticker.endswith(suffix) else f"{ticker}{suffix}"

        rows.append({
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "country": source["country"],
            "suffix": suffix,
            "index": index_name,
            "yf_ticker": yf_ticker,
        })

    df = pd.DataFrame(rows)
    logger.info("  -> %d constituents from %s", len(df), index_name)
    return df


# ========================================================================== #
# Universe builder
# ========================================================================== #


def _load_seed_universe() -> pd.DataFrame:
    """
    Load the seed universe CSV as a fallback when Wikipedia is
    unreachable. The seed contains ~140 verified DACH tickers
    and should be refreshed periodically by running the scraper
    from a machine with internet access.
    """
    seed_path = config.DATA_DIR / "seed_universe.csv"
    if not seed_path.exists():
        raise FileNotFoundError(
            f"Seed universe not found at {seed_path}. "
            "Either provide the file or ensure Wikipedia is reachable."
        )
    df = pd.read_csv(seed_path, encoding="utf-8")
    logger.info("Loaded seed universe: %d tickers from %s", len(df), seed_path)
    return df


def build_universe() -> pd.DataFrame:
    """
    Scrape all configured indices, deduplicate, and return a single
    DataFrame of unique tickers.  Stocks that appear in multiple
    indices get a comma-separated ``index`` field.

    Falls back to a seed CSV if Wikipedia scraping fails entirely
    (e.g. no network, proxy blocks, etc.).
    """
    frames: list[pd.DataFrame] = []
    for index_name, source in config.INDEX_SOURCES.items():
        df = fetch_index_constituents(index_name, source)
        if not df.empty:
            frames.append(df)

    if not frames:
        logger.warning(
            "Wikipedia scraping failed for all indices. "
            "Falling back to seed universe."
        )
        return _load_seed_universe()

    universe = pd.concat(frames, ignore_index=True)

    # Deduplicate across indices
    agg = (
        universe
        .groupby("yf_ticker", as_index=False)
        .agg({
            "ticker": "first",
            "name": "first",
            "sector": "first",
            "country": "first",
            "suffix": "first",
            "index": lambda x: ",".join(sorted(set(x))),
        })
    )

    agg = agg.sort_values(["country", "yf_ticker"]).reset_index(drop=True)

    logger.info(
        "Universe built: %d unique tickers from %d index scrapes",
        len(agg), len(frames),
    )
    return agg


# ========================================================================== #
# Persistence
# ========================================================================== #


def save_universe(df: pd.DataFrame, path: Optional[Path] = None) -> None:
    """Write the universe DataFrame to CSV (UTF-8)."""
    path = path or config.UNIVERSE_CSV
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Saved universe to %s (%d rows)", path, len(df))


def load_universe(path: Optional[Path] = None) -> pd.DataFrame:
    """Read a previously saved universe CSV."""
    path = path or config.UNIVERSE_CSV
    return pd.read_csv(path, encoding="utf-8")


# ========================================================================== #
# CLI
# ========================================================================== #


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    universe = build_universe()
    save_universe(universe)

    # --- summary output -----------------------------------------------------
    sep = "=" * 60
    print(f"\n{sep}")
    print("DACH MOMENTUM — UNIVERSE SUMMARY")
    print(sep)
    print(f"Total unique tickers: {len(universe)}")

    print("\nBy country:")
    print(universe["country"].value_counts().to_string())

    print("\nBy index (counting cross-listings):")
    all_indices: list[str] = []
    for idx_str in universe["index"].dropna():
        all_indices.extend(str(idx_str).split(","))
    print(pd.Series(all_indices).value_counts().to_string())

    print("\nSector coverage (top 15):")
    print(
        universe["sector"]
        .fillna("(unknown)")
        .value_counts()
        .head(15)
        .to_string()
    )

    print(f"\nSaved to: {config.UNIVERSE_CSV}")
    print(f"\nFirst 10 rows:\n{universe.head(10).to_string()}")
    print()


if __name__ == "__main__":
    main()
