#!/usr/bin/env python3
"""
Sanity-check the super_rich funding-overlay uplift against a buy-and-hold
benchmark (^GDAXI). Asks: is the +22.8pp mean test uplift from genuine
selection alpha, or is it inflated by riding market beta during ON periods?

Workflow:
  1. Run super_rich baseline (overlay forced OFF).
  2. Load the overlay equity curve from disk (saved by `--mode super_rich`
     after the per-mode default was wired in; the file
     `data/backtest_equity_super_rich.csv` now carries 5bp/14d overlay).
  3. Fetch DAX via yfinance.
  4. Year-by-year: DAX return, super_rich base, super_rich overlay,
     alpha vs DAX (assuming β=1 for simplicity), and funding-gate fire pct.

Usage: python run_overlay_sanity.py
"""
import sys
sys.path.insert(0, ".")

import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from dach_momentum import config
from dach_momentum.data import load_prices
from dach_momentum.btc_data import load_btc_funding
from run_backtest import precompute_backtest_inputs, run_backtest, compute_performance

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)-8s %(message)s")
logging.getLogger("dach_momentum").setLevel(logging.WARNING)
logging.getLogger("run_backtest").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OVERLAY_PATH = config.DATA_DIR / "backtest_equity_super_rich.csv"


def annual_returns(eq: pd.Series) -> pd.Series:
    yr = eq.resample("YE").last()
    yr_prev = yr.shift(1).fillna(eq.iloc[0])
    return (yr / yr_prev - 1)


def main():
    print("\n[1/5] Loading prices + benchmark, precomputing signals...")
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

    print("\n[2/5] Running super_rich BASELINE (funding overlay forced OFF)...")
    saved = dict(config.FUNDING_OVERLAY_BY_MODE)
    config.FUNDING_OVERLAY_BY_MODE = {}
    t0 = time.time()
    state_base = run_backtest(
        prices=prices, benchmark_close=bench_close,
        start_date="2010-01-01", end_date="2026-12-31",
        initial_capital=20000.0, max_positions=10, mode="super_rich",
        precomputed=precomputed,
    )
    perf_base = compute_performance(state_base)
    base_eq = perf_base["equity_curve"]["equity"].copy()
    base_eq.index = pd.to_datetime(base_eq.index)
    config.FUNDING_OVERLAY_BY_MODE = saved
    print(f"      baseline run took {time.time()-t0:.1f}s, final equity {base_eq.iloc[-1]:.0f}")

    print("\n[3/5] Loading overlay equity curve from disk (5bp/14d, saved by --mode super_rich)...")
    if not OVERLAY_PATH.exists():
        raise FileNotFoundError(
            f"Overlay file {OVERLAY_PATH} missing — run "
            f"`python run_backtest.py --mode super_rich` first."
        )
    df_o = pd.read_csv(OVERLAY_PATH, parse_dates=["date"])
    overlay_eq = df_o.set_index("date")["equity"].sort_index()
    print(f"      loaded {len(overlay_eq)} points, final equity {overlay_eq.iloc[-1]:.0f}")

    print("\n[4/5] Loading DAX + computing year-by-year...")
    dax_close = bench_close.dropna()
    dax_yr = annual_returns(dax_close) * 100
    base_yr = annual_returns(base_eq) * 100
    over_yr = annual_returns(overlay_eq) * 100

    # Funding-stress fire % per year (gate at 5bp/14d, the production setting)
    fr = load_btc_funding()
    roll = fr.rolling(14, min_periods=1).mean() if fr is not None else None
    if roll is not None:
        stressed = roll > 0.0005
        fire_pct = stressed.groupby(stressed.index.year).mean() * 100
    else:
        fire_pct = pd.Series(dtype=float)

    print("\n[5/5] Year-by-year sanity table")
    print()
    print(f"{'year':>5} {'DAX %':>8} {'SR base %':>10} {'SR ovly %':>10} "
          f"{'Δ (ovly-base)':>14} {'α vs DAX (base)':>17} {'α vs DAX (ovly)':>17} {'gate fire %':>12}")
    print("-" * 112)

    for d in over_yr.index:
        y = d.year
        dax_v = dax_yr.loc[dax_yr.index.year == y].iloc[-1] if y in dax_yr.index.year else float("nan")
        bv = base_yr.loc[d] if d in base_yr.index else float("nan")
        ov = over_yr.loc[d] if d in over_yr.index else float("nan")
        diff = ov - bv
        a_b = bv - dax_v
        a_o = ov - dax_v
        f = fire_pct.get(y, 0.0)
        print(f"{y:>5} {dax_v:>+7.1f}% {bv:>+9.1f}% {ov:>+9.1f}% "
              f"{diff:>+13.1f}pp {a_b:>+16.1f}pp {a_o:>+16.1f}pp {f:>11.1f}%")

    # Test-window summary (2021-2025) — the walk-forward test years
    print()
    test_years = [2021, 2022, 2023, 2024, 2025]
    test_dax = []
    test_base = []
    test_over = []
    for y in test_years:
        d_idx = pd.Timestamp(year=y, month=12, day=31)
        # find the closest year-end in each series
        def at(s, y):
            sub = s[s.index.year == y]
            return sub.iloc[-1] if len(sub) else float("nan")
        test_dax.append(at(dax_yr, y))
        test_base.append(at(base_yr, y))
        test_over.append(at(over_yr, y))

    print(f"Walk-forward test window 2021-2025 (annualised geometric):")
    def cagr(rs):
        prod = 1.0
        n = 0
        for r in rs:
            if not np.isnan(r):
                prod *= (1 + r/100); n += 1
        return (prod ** (1/n) - 1) * 100 if n else float("nan")
    print(f"  DAX buy-and-hold:        {cagr(test_dax):>+6.2f}% / yr")
    print(f"  super_rich baseline:     {cagr(test_base):>+6.2f}% / yr")
    print(f"  super_rich overlay:      {cagr(test_over):>+6.2f}% / yr")
    print(f"  Δ overlay vs baseline:   {cagr(test_over)-cagr(test_base):>+6.2f}pp")
    print(f"  α baseline vs DAX:       {cagr(test_base)-cagr(test_dax):>+6.2f}pp/yr")
    print(f"  α overlay vs DAX:        {cagr(test_over)-cagr(test_dax):>+6.2f}pp/yr")
    print()


if __name__ == "__main__":
    main()
