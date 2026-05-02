"""
Step 3: Signal calculation for the DACH momentum + quality strategy.

Computes all screening signals from the v3 strategy spec:
- Minervini Trend Template (8 criteria)
- Cross-sectional momentum (12-1 month)
- 52-week high proximity
- Relative strength vs CDAX
- ATR and volatility metrics
- Regime filter (CDAX vs 40-week SMA)

Run from the dach_momentum project root:
    python -m dach_momentum signals
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from . import config

logger = logging.getLogger(__name__)


# ========================================================================== #
# Individual signal calculators
# ========================================================================== #


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=window, min_periods=window, adjust=False).mean()


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    return tr.rolling(window=window, min_periods=window).mean()


def rolling_return(series: pd.Series, window: int) -> pd.Series:
    """Rolling percentage return over `window` trading days."""
    return series / series.shift(window) - 1.0


def rolling_high(series: pd.Series, window: int) -> pd.Series:
    """Rolling maximum over `window` trading days."""
    return series.rolling(window=window, min_periods=window).max()


def rolling_low(series: pd.Series, window: int) -> pd.Series:
    """Rolling minimum over `window` trading days."""
    return series.rolling(window=window, min_periods=window).min()


def bollinger_bandwidth(series: pd.Series, window: int = 20) -> pd.Series:
    """Bollinger Band width = (upper - lower) / middle."""
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    return (2 * std) / mid


# ========================================================================== #
# Trend Template (Minervini 8-criteria)
# ========================================================================== #


def compute_trend_template(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all 8 Minervini Trend Template criteria for a single stock.

    Returns a DataFrame with boolean columns for each criterion plus
    a combined `trend_template_pass` column (all 8 must be True).

    Criteria:
      1. Price > 150-day SMA
      2. Price > 200-day SMA
      3. 150-day SMA > 200-day SMA
      4. 200-day SMA trending up (vs 1 month ago)
      5. 50-day SMA > 150-day SMA
      6. Price > 50-day SMA
      7. Price >= 30% above 52-week low
      8. Price >= 90% of 52-week high (within 10%)
    """
    close = df["Close"]

    sma_50 = sma(close, config.TREND_SMA_SHORT)
    sma_150 = sma(close, config.TREND_SMA_MED)
    sma_200 = sma(close, config.TREND_SMA_LONG)

    high_52w = rolling_high(close, 252)
    low_52w = rolling_low(close, 252)

    # 200-day SMA 1 month ago for trend direction
    sma_200_1m_ago = sma_200.shift(21)

    result = pd.DataFrame(index=df.index)

    result["tt1_price_above_150"] = close > sma_150
    result["tt2_price_above_200"] = close > sma_200
    result["tt3_150_above_200"] = sma_150 > sma_200
    result["tt4_200_trending_up"] = sma_200 > sma_200_1m_ago
    result["tt5_50_above_150"] = sma_50 > sma_150
    result["tt6_price_above_50"] = close > sma_50
    result["tt7_above_52w_low"] = close >= (low_52w * config.TREND_52W_LOW_DISTANCE)
    result["tt8_near_52w_high"] = close >= (high_52w * config.TREND_52W_HIGH_PROXIMITY)

    result["trend_template_pass"] = (
        result["tt1_price_above_150"] &
        result["tt2_price_above_200"] &
        result["tt3_150_above_200"] &
        result["tt4_200_trending_up"] &
        result["tt5_50_above_150"] &
        result["tt6_price_above_50"] &
        result["tt7_above_52w_low"] &
        result["tt8_near_52w_high"]
    )

    return result


# ========================================================================== #
# Momentum signals
# ========================================================================== #


def compute_momentum_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute momentum-related signals for a single stock.

    Returns columns:
      - mom_12_1: 12-month return excluding most recent month
      - mom_6_1: 6-month return excluding most recent month
      - mom_3_0: 3-month return (for short-term context)
      - pct_from_52w_high: how far below the 52-week high
      - pct_from_52w_low: how far above the 52-week low
    """
    close = df["Close"]

    result = pd.DataFrame(index=df.index)

    # 12-1 momentum: return from 252 days ago to 21 days ago
    close_12m = close.shift(config.MOMENTUM_LOOKBACK_DAYS)
    close_1m = close.shift(config.MOMENTUM_SKIP_DAYS)
    result["mom_12_1"] = close_1m / close_12m - 1.0

    # 6-1 momentum
    close_6m = close.shift(126)
    result["mom_6_1"] = close_1m / close_6m - 1.0

    # 3-month momentum (no skip)
    result["mom_3_0"] = rolling_return(close, 63)

    # 52-week high/low proximity
    high_52w = rolling_high(close, 252)
    low_52w = rolling_low(close, 252)
    result["pct_from_52w_high"] = close / high_52w - 1.0  # 0 = at high, negative = below
    result["pct_from_52w_low"] = close / low_52w - 1.0    # 0 = at low, positive = above

    return result


# ========================================================================== #
# Volatility signals
# ========================================================================== #


def compute_volatility_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute volatility-related signals for stop-loss sizing and
    volatility contraction detection.
    """
    close = df["Close"]

    result = pd.DataFrame(index=df.index)

    result["atr_14"] = atr(df, window=14)
    result["atr_pct"] = result["atr_14"] / close  # ATR as % of price

    # Bollinger Band width (volatility contraction indicator)
    result["bb_width_20"] = bollinger_bandwidth(close, 20)

    # Historical volatility (annualised, 20-day)
    log_ret = np.log(close / close.shift(1))
    result["hvol_20"] = log_ret.rolling(20).std() * np.sqrt(252)

    # Volatility contraction: is current BB width below its 50-day average?
    bb_avg = result["bb_width_20"].rolling(50).mean()
    result["vol_contracting"] = result["bb_width_20"] < bb_avg

    return result


# ========================================================================== #
# Relative strength
# ========================================================================== #


def compute_relative_strength(
    stock_close: pd.Series,
    benchmark_close: pd.Series,
) -> pd.DataFrame:
    """
    Compute relative strength of a stock vs a benchmark.

    Returns:
      - rs_line: stock / benchmark ratio (rising = outperforming)
      - rs_sma_50: 50-day SMA of RS line
      - rs_rising: RS line above its 50-day SMA
    """
    # Align indices
    aligned = pd.DataFrame({
        "stock": stock_close,
        "bench": benchmark_close,
    }).dropna()

    if aligned.empty:
        return pd.DataFrame(
            index=stock_close.index,
            columns=["rs_line", "rs_sma_50", "rs_rising"],
        )

    result = pd.DataFrame(index=aligned.index)
    result["rs_line"] = aligned["stock"] / aligned["bench"]
    result["rs_sma_50"] = sma(result["rs_line"], 50)
    result["rs_rising"] = result["rs_line"] > result["rs_sma_50"]

    # Reindex to full stock index
    return result.reindex(stock_close.index)


# ========================================================================== #
# Regime filter
# ========================================================================== #


def compute_regime(benchmark_close: pd.Series) -> pd.DataFrame:
    """
    Compute the market regime filter based on CDAX (or substitute).

    Regime ON (bullish): benchmark above rising 40-week SMA.
    """
    result = pd.DataFrame(index=benchmark_close.index)

    sma_40w = sma(benchmark_close, config.REGIME_MA_WEEKS * 5)  # weeks -> trading days
    sma_40w_prev = sma_40w.shift(5)  # 1 week ago

    result["regime_sma"] = sma_40w
    result["regime_above_sma"] = benchmark_close > sma_40w
    result["regime_sma_rising"] = sma_40w > sma_40w_prev
    result["regime_on"] = result["regime_above_sma"] & result["regime_sma_rising"]

    return result


def compute_funding_stress(
    funding_close: pd.Series,
    threshold: float | None = None,
    sma_days: int | None = None,
) -> pd.DataFrame:
    """
    Crypto-leverage stress signal from BTC perp funding rate.

    `funding_close` is the daily close of the per-8h funding rate (Binance
    BTC-USDT perpetual via CoinDesk). Stress = N-day rolling mean above
    threshold, indicating overheated long positioning (a contrarian signal
    that often precedes broad-market mean reversion).

    Threshold and window default to the legacy module-level constants when
    not provided, so ad-hoc sweep scripts that mutate config still work.
    """
    if threshold is None:
        threshold = config.FUNDING_STRESS_THRESHOLD
    if sma_days is None:
        sma_days = config.FUNDING_SMA_DAYS
    result = pd.DataFrame(index=funding_close.index)
    roll = funding_close.rolling(sma_days, min_periods=1).mean()
    result["funding_smoothed"] = roll
    result["funding_stress"] = roll > threshold
    return result


def compute_btc_regime(btc_close: pd.Series) -> pd.DataFrame:
    """
    Secondary regime gate based on BTC-USD trend (CoinDesk CCIX).

    Same rule as CDAX: bullish when price is above a rising 40-week SMA.
    BTC is a daily series (no weekend gap), so the SMA window is 40w * 7d.
    """
    result = pd.DataFrame(index=btc_close.index)
    window = config.BTC_REGIME_MA_WEEKS * 7
    sma_btc = sma(btc_close, window)
    sma_btc_prev = sma_btc.shift(7)

    result["btc_sma"] = sma_btc
    result["btc_above_sma"] = btc_close > sma_btc
    result["btc_sma_rising"] = sma_btc > sma_btc_prev
    result["btc_regime_on"] = result["btc_above_sma"] & result["btc_sma_rising"]

    return result


# ========================================================================== #
# Exit signals
# ========================================================================== #


def compute_exit_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the exit-related signals:
      - Weekly close below 30-week SMA
      - 10-week SMA (for regime-off emergency exit)
    """
    close = df["Close"]

    result = pd.DataFrame(index=df.index)

    sma_30w = sma(close, config.EXIT_MA_WEEKS * 5)
    sma_10w = sma(close, 50)  # 10 weeks * 5 days

    result["exit_sma_30w"] = sma_30w
    result["below_30w_sma"] = close < sma_30w
    result["exit_sma_10w"] = sma_10w
    result["below_10w_sma"] = close < sma_10w

    return result


# ========================================================================== #
# Combined signal computation for full universe
# ========================================================================== #


def compute_all_signals(
    prices: dict[str, pd.DataFrame],
    benchmark_prices: Optional[pd.DataFrame] = None,
    filtered_tickers: Optional[list[str]] = None,
) -> dict[str, pd.DataFrame]:
    """
    Compute all signals for every ticker in the universe.

    Returns a dict mapping yf_ticker -> DataFrame with all signal columns
    joined to the original OHLCV data.
    """
    # Determine benchmark for relative strength
    if benchmark_prices is not None and "Close" in benchmark_prices.columns:
        bench_close = benchmark_prices["Close"]
    else:
        # Fallback: use equal-weight of all tickers as pseudo-benchmark
        logger.warning(
            "No benchmark provided; using equal-weight portfolio as proxy"
        )
        all_closes = pd.DataFrame({
            t: df["Close"] for t, df in prices.items()
            if "Close" in df.columns
        })
        bench_close = all_closes.pct_change().mean(axis=1).add(1).cumprod()
        bench_close.iloc[0] = 1.0

    # Compute regime
    regime = compute_regime(bench_close)

    # Compute per-ticker signals
    tickers_to_process = filtered_tickers or list(prices.keys())
    results: dict[str, pd.DataFrame] = {}

    for i, ticker in enumerate(tickers_to_process):
        if ticker not in prices:
            continue

        df = prices[ticker].copy()
        if df.empty or "Close" not in df.columns:
            continue

        if (i + 1) % 20 == 0 or i == 0:
            logger.info(
                "Computing signals %d/%d: %s",
                i + 1, len(tickers_to_process), ticker,
            )

        # Compute all signal groups
        trend = compute_trend_template(df)
        momentum = compute_momentum_signals(df)
        volatility = compute_volatility_signals(df)
        rs = compute_relative_strength(df["Close"], bench_close)
        exits = compute_exit_signals(df)
        breakout = compute_breakout_signals(df)

        # Join regime (aligned to stock's dates)
        regime_aligned = regime.reindex(df.index)

        # Combine everything
        combined = pd.concat(
            [df, trend, momentum, volatility, rs, exits, breakout, regime_aligned],
            axis=1,
        )

        # Remove duplicate column names (if any overlap)
        combined = combined.loc[:, ~combined.columns.duplicated()]

        results[ticker] = combined

    logger.info("Computed signals for %d tickers", len(results))

    # Compute cross-sectional momentum rank (percentile within universe)
    _add_cross_sectional_ranks(results)

    return results


def _add_cross_sectional_ranks(signals: dict[str, pd.DataFrame]) -> None:
    """
    Add cross-sectional percentile ranks for momentum and RS.
    Modifies the signal DataFrames in place.
    """
    # Collect all mom_12_1 values by date
    mom_data = {}
    for ticker, df in signals.items():
        if "mom_12_1" in df.columns:
            mom_data[ticker] = df["mom_12_1"]

    if not mom_data:
        return

    mom_df = pd.DataFrame(mom_data)

    # Compute percentile rank (0-100) for each stock on each date
    mom_rank = mom_df.rank(axis=1, pct=True) * 100

    # Write back
    for ticker in signals:
        if ticker in mom_rank.columns:
            signals[ticker]["mom_rank_pct"] = mom_rank[ticker].reindex(
                signals[ticker].index
            )
        else:
            signals[ticker]["mom_rank_pct"] = np.nan


# ========================================================================== #
# Breakout signals (for "Get Rich Quick" strategy)
# ========================================================================== #


def compute_breakout_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute breakout-specific signals for the aggressive strategy.

    Returns columns:
      - near_52w_high: price within RQ_HIGH_PROXIMITY_PCT of 52-week high
      - volume_surge: 10-day avg volume >= RQ_VOLUME_SURGE_MULT * 50-day avg
      - breakout_score: composite breakout strength (0-100)
    """
    close = df["Close"]

    result = pd.DataFrame(index=df.index)

    # 52-week high proximity
    high_52w = rolling_high(close, 252)
    proximity = close / high_52w
    result["near_52w_high"] = proximity >= config.RQ_HIGH_PROXIMITY_PCT

    # Volume surge: recent volume well above average
    if "Volume" in df.columns:
        vol = df["Volume"]
        vol_50d = vol.rolling(50, min_periods=20).mean()
        vol_10d = vol.rolling(10, min_periods=5).mean()
        result["volume_surge"] = vol_10d >= (vol_50d * config.RQ_VOLUME_SURGE_MULT)

        # Volume ratio for scoring
        vol_ratio = (vol_10d / vol_50d.replace(0, np.nan)).clip(0, 5)
        result["vol_ratio"] = vol_ratio
    else:
        result["volume_surge"] = False
        result["vol_ratio"] = 1.0

    # Price acceleration: 1-month return > 2-month return / 2
    mom_1m = close / close.shift(21) - 1.0
    mom_2m = close / close.shift(42) - 1.0
    result["price_accelerating"] = mom_1m > (mom_2m / 2)

    # Breakout score (0-100): weighted composite
    #   40% - proximity to 52-week high
    #   30% - volume surge strength
    #   20% - short-term momentum acceleration
    #   10% - volatility contraction (tighter = better base)
    proximity_score = (proximity.clip(0.8, 1.0) - 0.8) / 0.2 * 100
    vol_score = (result["vol_ratio"].clip(0.5, 3.0) - 0.5) / 2.5 * 100
    accel_score = mom_1m.clip(-0.1, 0.3) / 0.3 * 100

    bb_w = bollinger_bandwidth(close, 20)
    bb_avg = bb_w.rolling(50).mean()
    contraction_score = ((bb_avg - bb_w) / bb_avg.replace(0, np.nan)).clip(0, 1) * 100

    result["breakout_score"] = (
        proximity_score * 0.4 +
        vol_score * 0.3 +
        accel_score * 0.2 +
        contraction_score.fillna(0) * 0.1
    ).clip(0, 100)

    return result


# ========================================================================== #
# Screening: find current candidates
# ========================================================================== #


def screen_candidates(
    signals: dict[str, pd.DataFrame],
    as_of: Optional[str] = None,
) -> pd.DataFrame:
    """
    Screen for stocks passing all entry criteria on a specific date.

    Returns a DataFrame of candidates sorted by composite score.
    """
    rows = []

    for ticker, df in signals.items():
        if df.empty:
            continue

        if as_of:
            # Get the last available row on or before as_of
            mask = df.index <= pd.Timestamp(as_of)
            if not mask.any():
                continue
            row = df.loc[mask].iloc[-1]
            date = df.loc[mask].index[-1]
        else:
            row = df.iloc[-1]
            date = df.index[-1]

        # Check all entry criteria
        passes_trend = bool(row.get("trend_template_pass", False))
        passes_regime = bool(row.get("regime_on", False))
        mom_rank = row.get("mom_rank_pct", 0)
        passes_momentum = mom_rank >= 50  # top 50% of universe
        rs_rising = bool(row.get("rs_rising", False))

        if passes_trend and passes_regime and passes_momentum:
            rows.append({
                "date": date,
                "ticker": ticker,
                "close": row.get("Close"),
                "trend_template": passes_trend,
                "regime_on": passes_regime,
                "mom_12_1": row.get("mom_12_1"),
                "mom_rank_pct": mom_rank,
                "pct_from_52w_high": row.get("pct_from_52w_high"),
                "rs_rising": rs_rising,
                "vol_contracting": bool(row.get("vol_contracting", False)),
                "atr_pct": row.get("atr_pct"),
                "bb_width_20": row.get("bb_width_20"),
                "hvol_20": row.get("hvol_20"),
                # Composite score: higher is better
                "composite_score": (
                    (mom_rank / 100) * 0.4 +
                    (1 + row.get("pct_from_52w_high", -1)) * 0.3 +
                    (1.0 if rs_rising else 0.0) * 0.2 +
                    (1.0 if row.get("vol_contracting", False) else 0.0) * 0.1
                ),
            })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result = result.sort_values("composite_score", ascending=False)
    return result.reset_index(drop=True)


# ========================================================================== #
# Persistence
# ========================================================================== #


def save_signals(signals: dict[str, pd.DataFrame]) -> None:
    """Save computed signals to Parquet files."""
    signals_dir = config.DATA_DIR / "signals"
    signals_dir.mkdir(parents=True, exist_ok=True)

    for ticker, df in signals.items():
        safe_name = ticker.replace("/", "_").replace(".", "_")
        df.to_parquet(signals_dir / f"{safe_name}.parquet")

    logger.info("Saved signals for %d tickers to %s", len(signals), signals_dir)


def load_signals(tickers: Optional[list[str]] = None) -> dict[str, pd.DataFrame]:
    """Load previously computed signals from Parquet."""
    signals_dir = config.DATA_DIR / "signals"
    results = {}

    if not signals_dir.exists():
        return results

    for path in signals_dir.glob("*.parquet"):
        ticker = (
            path.stem
            .replace("_DE", ".DE")
            .replace("_VI", ".VI")
            .replace("_SW", ".SW")
        )
        if tickers is not None and ticker not in tickers:
            continue
        results[ticker] = pd.read_parquet(path)

    logger.info("Loaded signals for %d tickers", len(results))
    return results


# ========================================================================== #
# CLI
# ========================================================================== #


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    from .data import load_prices

    # Load price data
    print("\n[1/4] Loading price data from Parquet...")
    prices = load_prices()
    logger.info("Loaded prices for %d tickers", len(prices))

    if not prices:
        print("ERROR: No price data found. Run 'python -m dach_momentum data' first.")
        return

    # Try to load CDAX as benchmark; fall back to DAX
    print("\n[2/4] Loading benchmark for relative strength...")
    import yfinance as yf

    bench_ticker = config.REGIME_INDEX_TICKER  # ^CDAXI
    bench_df = None

    for candidate in [bench_ticker, "^GDAXI"]:  # CDAX, then DAX as fallback
        try:
            logger.info("Trying benchmark: %s", candidate)
            bench_data = yf.download(
                candidate, start="2005-01-01",
                auto_adjust=False, progress=False,
            )
            if bench_data is not None and len(bench_data) > 100:
                bench_df = bench_data
                logger.info(
                    "Using %s as benchmark (%d rows)",
                    candidate, len(bench_df),
                )
                break
        except Exception as exc:
            logger.warning("Benchmark %s failed: %s", candidate, exc)

    # Load filtered universe tickers
    filtered_path = config.DATA_DIR / "universe_filtered.csv"
    if filtered_path.exists():
        filtered = pd.read_csv(filtered_path)
        filtered_tickers = filtered["yf_ticker"].tolist()
        logger.info("Using filtered universe: %d tickers", len(filtered_tickers))
    else:
        filtered_tickers = None
        logger.info("No filtered universe found; computing signals for all tickers")

    # Compute signals
    print("\n[3/4] Computing signals for all tickers...")
    signals = compute_all_signals(
        prices=prices,
        benchmark_prices=bench_df,
        filtered_tickers=filtered_tickers,
    )

    # Save signals
    save_signals(signals)

    # Screen for current candidates
    print("\n[4/4] Screening for current candidates...")
    candidates = screen_candidates(signals)

    # Summary
    sep = "=" * 60
    print(f"\n{sep}")
    print("STEP 3 COMPLETE \u2014 SIGNAL COMPUTATION SUMMARY")
    print(sep)

    print(f"\nSignals computed for: {len(signals)} tickers")

    # Count how many pass trend template today
    today_pass = sum(
        1 for df in signals.values()
        if not df.empty and df.iloc[-1].get("trend_template_pass", False)
    )
    print(f"Currently passing trend template: {today_pass}")

    # Regime status
    if signals:
        sample = next(iter(signals.values()))
        if "regime_on" in sample.columns and not sample.empty:
            regime_status = "ON (bullish)" if sample.iloc[-1].get("regime_on", False) else "OFF (bearish)"
            print(f"Market regime: {regime_status}")

    # Candidates
    if not candidates.empty:
        print(f"\nCurrent entry candidates ({len(candidates)}):")
        display_cols = [
            "ticker", "close", "mom_12_1", "mom_rank_pct",
            "pct_from_52w_high", "rs_rising", "vol_contracting",
            "composite_score",
        ]
        available_cols = [c for c in display_cols if c in candidates.columns]
        print(candidates[available_cols].to_string(index=False))
    else:
        print("\nNo candidates currently pass all entry criteria.")

    print(f"\nSignals saved to: {config.DATA_DIR / 'signals'}/")
    print()


if __name__ == "__main__":
    main()
