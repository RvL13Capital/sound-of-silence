#!/usr/bin/env python3
"""
Walk-forward validation for the DACH momentum strategy.

Splits the backtest period into train/test windows and runs the strategy
on each test period, measuring out-of-sample performance.  Since the
strategy rules are fixed (no parameter optimisation), the "train" period
is conceptual — it represents data you would have seen before going live.

The key question: "Is the strategy robust across different time periods,
or was it only good in one era?"

Usage:
    python run_walkforward.py
    python run_walkforward.py --mode canslim
"""
import sys
sys.path.insert(0, ".")

import logging
from typing import Optional

import numpy as np
import pandas as pd

from run_backtest import run_backtest, compute_performance, print_performance
from dach_momentum.data import load_prices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ========================================================================== #
# Walk-forward windows
# ========================================================================== #

WINDOWS = [
    {"name": "Window 1", "train_start": "2010-01-01", "train_end": "2014-12-31",
     "test_start": "2015-01-01", "test_end": "2016-12-31"},
    {"name": "Window 2", "train_start": "2012-01-01", "train_end": "2016-12-31",
     "test_start": "2017-01-01", "test_end": "2018-12-31"},
    {"name": "Window 3", "train_start": "2014-01-01", "train_end": "2018-12-31",
     "test_start": "2019-01-01", "test_end": "2020-12-31"},
    {"name": "Window 4", "train_start": "2016-01-01", "train_end": "2020-12-31",
     "test_start": "2021-01-01", "test_end": "2022-12-31"},
    {"name": "Window 5", "train_start": "2018-01-01", "train_end": "2022-12-31",
     "test_start": "2023-01-01", "test_end": "2024-12-31"},
    {"name": "Window 6", "train_start": "2020-01-01", "train_end": "2024-12-31",
     "test_start": "2025-01-01", "test_end": "2026-12-31"},
]


def run_single_window(
    window: dict,
    prices: dict[str, pd.DataFrame],
    benchmark_close: pd.Series,
    mode: str = "momentum",
) -> Optional[dict]:
    """Run the backtest on a single test window and return performance metrics."""
    name = window["name"]
    test_start = window["test_start"]
    test_end = window["test_end"]

    logger.info("Running %s: test period %s to %s", name, test_start, test_end)

    try:
        state = run_backtest(
            prices=prices,
            benchmark_close=benchmark_close,
            start_date=test_start,
            end_date=test_end,
            initial_capital=20000.0,
            max_positions=10,
            mode=mode,
        )
    except Exception as exc:
        logger.error("  %s failed: %s", name, exc)
        return None

    perf = compute_performance(state)
    if not perf:
        logger.warning("  %s returned empty performance (no trades?)", name)
        return None

    return perf


def print_summary_table(results: list[dict]) -> None:
    """Print a summary table of all walk-forward windows."""
    sep = "=" * 90
    print(f"\n{sep}")
    print("  WALK-FORWARD VALIDATION SUMMARY")
    print(sep)

    header = (
        f"  {'Window':<12} {'Period':<22} {'CAGR':>8} {'Sharpe':>8} "
        f"{'Max DD':>8} {'Win%':>8} {'PF':>8} {'Trades':>7}"
    )
    print(header)
    print(f"  {'─' * 12} {'─' * 22} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 7}")

    for r in results:
        if r["perf"] is None:
            print(f"  {r['name']:<12} {r['period']:<22} {'N/A':>8} {'N/A':>8} "
                  f"{'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>7}")
            continue

        p = r["perf"]
        pf_str = f"{p['profit_factor']:.2f}" if p["profit_factor"] != float("inf") else "inf"
        print(
            f"  {r['name']:<12} {r['period']:<22} "
            f"{p['cagr_pct']:>+7.1f}% {p['sharpe_ratio']:>8.2f} "
            f"{p['max_drawdown_pct']:>7.1f}% {p['win_rate_pct']:>7.1f}% "
            f"{pf_str:>8} {p['total_trades']:>7d}"
        )

    print()


def print_aggregated_metrics(results: list[dict]) -> None:
    """Print aggregated out-of-sample metrics across all windows."""
    valid = [r for r in results if r["perf"] is not None]
    if not valid:
        print("  No valid results to aggregate.\n")
        return

    cagrs = [r["perf"]["cagr_pct"] for r in valid]
    sharpes = [r["perf"]["sharpe_ratio"] for r in valid]
    max_dds = [r["perf"]["max_drawdown_pct"] for r in valid]
    win_rates = [r["perf"]["win_rate_pct"] for r in valid]
    pfs = [r["perf"]["profit_factor"] for r in valid
           if r["perf"]["profit_factor"] != float("inf")]

    sep = "-" * 50
    print(f"  {sep}")
    print("  AGGREGATED OUT-OF-SAMPLE METRICS")
    print(f"  {sep}")
    print(f"  Windows evaluated:    {len(valid)} / {len(results)}")
    print()
    print(f"  CAGR        mean: {np.mean(cagrs):>+7.1f}%   "
          f"median: {np.median(cagrs):>+7.1f}%   "
          f"min: {np.min(cagrs):>+7.1f}%   max: {np.max(cagrs):>+7.1f}%")
    print(f"  Sharpe      mean: {np.mean(sharpes):>7.2f}    "
          f"median: {np.median(sharpes):>7.2f}    "
          f"min: {np.min(sharpes):>7.2f}    max: {np.max(sharpes):>7.2f}")
    print(f"  Max DD      mean: {np.mean(max_dds):>7.1f}%   "
          f"median: {np.median(max_dds):>7.1f}%   "
          f"worst: {np.min(max_dds):>7.1f}%")
    print(f"  Win Rate    mean: {np.mean(win_rates):>7.1f}%   "
          f"median: {np.median(win_rates):>7.1f}%")
    if pfs:
        print(f"  Profit Factor mean: {np.mean(pfs):>6.2f}    "
              f"median: {np.median(pfs):>6.2f}")

    # Consistency check
    positive_windows = sum(1 for c in cagrs if c > 0)
    print(f"\n  Positive CAGR in {positive_windows}/{len(valid)} windows "
          f"({positive_windows / len(valid) * 100:.0f}%)")

    if np.min(cagrs) > 0:
        print("  VERDICT: Strategy profitable in ALL test windows.")
    elif positive_windows >= len(valid) * 0.5:
        print("  VERDICT: Strategy profitable in MOST test windows.")
    else:
        print("  VERDICT: Strategy shows inconsistent performance across periods.")

    print()


def main():
    # Parse args
    mode = "momentum"
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]

    print(f"\nWalk-Forward Validation — mode: {mode.upper()}")
    print("=" * 60)

    # Load prices
    print("\n[1/3] Loading price data...")
    prices = load_prices()
    if not prices:
        print("ERROR: No price data. Run 'python -m dach_momentum data' first.")
        return

    # Flatten MultiIndex if present
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    logger.info("Loaded %d tickers", len(prices))

    # Load benchmark
    print("\n[2/3] Loading benchmark...")
    import yfinance as yf
    bench = yf.download("^GDAXI", start="2005-01-01",
                        auto_adjust=False, progress=False)
    if isinstance(bench.columns, pd.MultiIndex):
        bench.columns = bench.columns.get_level_values(0)
    bench_close = bench["Close"]
    logger.info("Benchmark: %d rows", len(bench_close))

    # Run walk-forward
    print(f"\n[3/3] Running walk-forward validation ({len(WINDOWS)} windows)...\n")

    results = []
    for window in WINDOWS:
        perf = run_single_window(window, prices, bench_close, mode=mode)
        period_str = f"{window['test_start'][:4]}-{window['test_end'][:4]}"
        results.append({
            "name": window["name"],
            "period": f"{window['test_start']} to {window['test_end']}",
            "period_short": period_str,
            "perf": perf,
        })

        if perf:
            logger.info(
                "  %s done: CAGR=%.1f%%, Sharpe=%.2f, MaxDD=%.1f%%",
                window["name"], perf["cagr_pct"],
                perf["sharpe_ratio"], perf["max_drawdown_pct"],
            )

    # Print results
    print_summary_table(results)
    print_aggregated_metrics(results)


if __name__ == "__main__":
    main()
