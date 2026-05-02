#!/usr/bin/env python3
"""
Walk-forward validation for the BTC funding-stress overlay on super_rich.

Question: when funding-overlay parameters are chosen on data ending at the
start of year Y (training), does the chosen parameterization produce a
positive uplift during year Y (test)?

If yes for multiple folds, the signal generalizes. If only the fold where
2021 is in the training set produces positive test uplift, the signal is
a 2021-specific artifact.

Approach:
  1. Run baseline + 15 sweep cells (5 thresholds x 3 windows), keeping the
     full equity curve for each.
  2. For each fold year Y in {2021, 2022, 2023, 2024, 2025}:
       train = 2020-01-01 to Dec-31 of (Y-1)
       test  = year Y
       pick the cell maximizing CAGR uplift on train
       report its test CAGR uplift over baseline

Saves results to data/funding_walkforward.csv.
Usage: python run_walkforward_funding.py
"""
import sys
sys.path.insert(0, ".")

import logging
import time
from itertools import product

import numpy as np
import pandas as pd
import yfinance as yf

from dach_momentum import config
from dach_momentum.data import load_prices
from run_backtest import (
    precompute_backtest_inputs,
    run_backtest,
    compute_performance,
)

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)-8s %(message)s")
logging.getLogger("dach_momentum").setLevel(logging.WARNING)
logging.getLogger("run_backtest").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Sweep grid — same as run_funding_sweep.py
THRESHOLDS_BP = [3, 5, 7, 10, 15]
WINDOWS_DAYS = [3, 7, 14]
DEFAULT_MODE = "super_rich"

# Walk-forward folds: train = 2020-01 to (Y-1)-12, test = Y-01 to Y-12
FOLD_YEARS = [2021, 2022, 2023, 2024, 2025]
TRAIN_START = "2020-01-01"


def cagr_between(eq: pd.Series, start: str, end: str) -> float:
    """Annualized return between start (inclusive) and end (inclusive)."""
    s = eq.loc[start:end]
    if len(s) < 2:
        return float("nan")
    days = (s.index[-1] - s.index[0]).days
    if days <= 0:
        return float("nan")
    return (s.iloc[-1] / s.iloc[0]) ** (365.25 / days) - 1


def maxdd_between(eq: pd.Series, start: str, end: str) -> float:
    s = eq.loc[start:end]
    if len(s) < 2:
        return float("nan")
    peak = s.cummax()
    return float((s / peak - 1).min())


def main():
    args = sys.argv[1:]
    mode = DEFAULT_MODE
    for i, a in enumerate(args):
        if a == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
    print(f"\nMode: {mode}")

    print("\n[1/4] Loading prices + benchmark, precomputing signals...")
    prices = load_prices()
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)
    bench = yf.download("^GDAXI", start="2005-01-01", auto_adjust=False, progress=False)
    if isinstance(bench.columns, pd.MultiIndex):
        bench.columns = bench.columns.get_level_values(0)
    bench_close = bench["Close"]
    precomputed = precompute_backtest_inputs(prices, bench_close)
    print(f"      precomputed {len(precomputed[0])} tickers")

    # Container for all 16 equity curves: 1 baseline + 15 cells
    curves: dict[tuple, pd.Series] = {}

    print("\n[2/4] Running 1 baseline + 15 cells, keeping full equity curves...")

    def run_and_curve(funding_override=None):
        state = run_backtest(
            prices=prices, benchmark_close=bench_close,
            start_date="2010-01-01", end_date="2026-12-31",
            initial_capital=20000.0, max_positions=10, mode=mode,
            precomputed=precomputed, funding_override=funding_override,
        )
        perf = compute_performance(state)
        eq = perf["equity_curve"]["equity"].copy()
        eq.index = pd.to_datetime(eq.index)
        return eq

    # Suppress per-mode default during sweep so baseline is truly clean
    saved_overlay = dict(config.FUNDING_OVERLAY_BY_MODE)
    config.FUNDING_OVERLAY_BY_MODE = {}

    # Baseline (overlay OFF)
    t0 = time.time()
    curves[("baseline", "baseline")] = run_and_curve(funding_override=None)
    print(f"      baseline: {time.time()-t0:.1f}s")

    # Sweep cells via per-call override
    cell_n = 0
    total = len(THRESHOLDS_BP) * len(WINDOWS_DAYS)
    for w in WINDOWS_DAYS:
        for th_bp in THRESHOLDS_BP:
            cell_n += 1
            t0 = time.time()
            curves[(th_bp, w)] = run_and_curve(
                funding_override={"threshold": th_bp / 1e4, "sma_days": w}
            )
            print(f"      [{cell_n:2d}/{total}] th={th_bp:>2d}bp/w={w:>2d}d: {time.time()-t0:.1f}s")

    config.FUNDING_OVERLAY_BY_MODE = saved_overlay

    # Sanity: all curves indexed identically
    base = curves[("baseline", "baseline")]
    print(f"\n      backtest covers {base.index.min().date()} -> {base.index.max().date()}, {len(base)} points")

    print("\n[3/4] Walk-forward analysis...")
    rows = []
    for y in FOLD_YEARS:
        train_end = f"{y-1}-12-31"
        test_start = f"{y}-01-01"
        test_end = f"{y}-12-31"

        # Baseline CAGR over train and test
        base_train_cagr = cagr_between(base, TRAIN_START, train_end)
        base_test_cagr = cagr_between(base, test_start, test_end)
        base_test_dd = maxdd_between(base, test_start, test_end)

        # Find best cell on TRAIN
        best_cell = None
        best_uplift = -np.inf
        cell_train_uplifts = {}
        for cell, eq in curves.items():
            if cell == ("baseline", "baseline"):
                continue
            cell_train = cagr_between(eq, TRAIN_START, train_end)
            uplift = cell_train - base_train_cagr
            cell_train_uplifts[cell] = uplift
            if uplift > best_uplift:
                best_uplift = uplift
                best_cell = cell

        # Apply best cell's params to TEST
        eq_best = curves[best_cell]
        test_cagr = cagr_between(eq_best, test_start, test_end)
        test_dd = maxdd_between(eq_best, test_start, test_end)
        test_uplift = test_cagr - base_test_cagr
        test_dd_uplift = test_dd - base_test_dd  # positive = better

        rows.append({
            "fold_year": y,
            "train_period": f"{TRAIN_START} -> {train_end}",
            "test_period": f"{test_start} -> {test_end}",
            "best_cell_th_bp": best_cell[0],
            "best_cell_w_d": best_cell[1],
            "train_uplift_pp": best_uplift * 100,
            "base_test_cagr_pct": base_test_cagr * 100,
            "overlay_test_cagr_pct": test_cagr * 100,
            "test_uplift_pp": test_uplift * 100,
            "base_test_dd_pct": base_test_dd * 100,
            "overlay_test_dd_pct": test_dd * 100,
            "test_dd_uplift_pp": test_dd_uplift * 100,
            "n_cells_helping_train": sum(1 for v in cell_train_uplifts.values() if v > 0),
        })

    df = pd.DataFrame(rows)
    out_csv = config.DATA_DIR / f"funding_walkforward_{mode}.csv"
    df.to_csv(out_csv, index=False)

    print(f"\n[4/4] Walk-forward results ({mode}, train anchor = {TRAIN_START})")
    print()
    print(f"{'fold Y':>6} {'best (th/w)':>12} {'train Δ':>9} {'base_Y':>8} {'overlay_Y':>10} {'test Δ':>8} {'baseDD_Y':>9} {'overDD_Y':>9} {'ΔDD':>7} {'+/15':>5}")
    print("-" * 100)
    for r in rows:
        cell = f"{int(r['best_cell_th_bp'])}/{int(r['best_cell_w_d'])}d"
        print(f"{r['fold_year']:>6} {cell:>12} "
              f"{r['train_uplift_pp']:>+8.2f}pp "
              f"{r['base_test_cagr_pct']:>+7.1f}% {r['overlay_test_cagr_pct']:>+9.1f}% "
              f"{r['test_uplift_pp']:>+7.2f}pp "
              f"{r['base_test_dd_pct']:>+8.1f}% {r['overlay_test_dd_pct']:>+8.1f}% "
              f"{r['test_dd_uplift_pp']:>+6.2f} "
              f"{r['n_cells_helping_train']:>5d}")

    print()
    print("Aggregate test-period uplift across folds:")
    print(f"  mean test Δ CAGR: {df['test_uplift_pp'].mean():+.2f}pp")
    print(f"  median:           {df['test_uplift_pp'].median():+.2f}pp")
    print(f"  positive folds:   {(df['test_uplift_pp'] > 0).sum()} / {len(df)}")
    print(f"  best fold:        {df['test_uplift_pp'].max():+.2f}pp (year {df.loc[df['test_uplift_pp'].idxmax(),'fold_year']})")
    print(f"  worst fold:       {df['test_uplift_pp'].min():+.2f}pp (year {df.loc[df['test_uplift_pp'].idxmin(),'fold_year']})")
    print()
    print(f"Raw results saved to {out_csv}")


if __name__ == "__main__":
    main()
