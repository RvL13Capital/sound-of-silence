#!/usr/bin/env python3
"""
Sensitivity sweep for the BTC perp funding-stress overlay.

Tests whether the +5.2pp super_rich uplift from the funding gate is robust
to threshold and window choice (response surface) or a knife-edge fluke at
the originally chosen point (5 bp/8h, 7-day window).

Outputs a 5x3 grid per mode (CAGR delta vs baseline) and saves raw results
to data/funding_sweep.csv.

Usage:
    python run_funding_sweep.py
    python run_funding_sweep.py --modes super_rich,canslim
"""
import sys
sys.path.insert(0, ".")

import logging
import time

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
logging.getLogger("run_backtest").setLevel(logging.WARNING)  # silence per-call backtest logs
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Sweep grid
THRESHOLDS_BP = [3, 5, 7, 10, 15]                 # per-8h funding rate, bp
WINDOWS_DAYS = [3, 7, 14]                          # rolling-mean window
DEFAULT_MODES = ["super_rich", "canslim", "momentum"]


def maxdd_pct(equity_curve: pd.DataFrame) -> float:
    eq = equity_curve["equity"]
    peak = eq.cummax()
    return (eq / peak - 1).min() * 100


def cagr_pct(equity_curve: pd.DataFrame) -> float:
    eq = equity_curve["equity"]
    years = (equity_curve.index[-1] - equity_curve.index[0]).days / 365.25
    return ((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) * 100


def _run(prices, bench, precomputed, mode, funding_override=None) -> dict:
    state = run_backtest(
        prices=prices, benchmark_close=bench,
        start_date="2010-01-01", end_date="2026-12-31",
        initial_capital=20000.0, max_positions=10, mode=mode,
        precomputed=precomputed, funding_override=funding_override,
    )
    perf = compute_performance(state)
    eq = perf.get("equity_curve")
    return {
        "cagr": cagr_pct(eq),
        "maxdd": maxdd_pct(eq),
        "sharpe": perf.get("sharpe_ratio", 0),
        "n_trades": perf.get("total_trades", 0),
    }


def main():
    args = sys.argv[1:]
    modes = DEFAULT_MODES
    for i, a in enumerate(args):
        if a == "--modes" and i + 1 < len(args):
            modes = args[i + 1].split(",")

    print("\n[1/4] Loading price data + benchmark...")
    prices = load_prices()
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)
    bench = yf.download("^GDAXI", start="2005-01-01", auto_adjust=False, progress=False)
    if isinstance(bench.columns, pd.MultiIndex):
        bench.columns = bench.columns.get_level_values(0)
    bench_close = bench["Close"]

    print("[2/4] Precomputing per-ticker signals + CDAX regime (one-shot)...")
    t0 = time.time()
    precomputed = precompute_backtest_inputs(prices, bench_close)
    print(f"      precompute took {time.time()-t0:.1f}s, {len(precomputed[0])} tickers ready")

    rows = []
    grid_cells = len(THRESHOLDS_BP) * len(WINDOWS_DAYS)
    sweep_csv = config.DATA_DIR / "funding_sweep.csv"

    def flush_csv():
        pd.DataFrame(rows).to_csv(sweep_csv, index=False)

    # Baseline = no overlay anywhere; we force this via funding_override=None
    # AND temporarily clearing FUNDING_OVERLAY_BY_MODE (in case caller's mode
    # has a per-mode default that would otherwise turn the overlay on).
    saved_overlay = dict(config.FUNDING_OVERLAY_BY_MODE)
    config.FUNDING_OVERLAY_BY_MODE = {}

    for mode in modes:
        print(f"\n[3/4] Mode: {mode}", flush=True)
        # Baseline (overlay OFF)
        t0 = time.time()
        base = _run(prices, bench_close, precomputed, mode, funding_override=None)
        print(f"      baseline:                CAGR {base['cagr']:>5.2f}%  maxDD {base['maxdd']:+6.2f}%  "
              f"Sharpe {base['sharpe']:.2f}  trades {base['n_trades']}  ({time.time()-t0:.1f}s)",
              flush=True)
        rows.append({
            "mode": mode, "threshold_bp": None, "window_d": None,
            "cagr": base["cagr"], "maxdd": base["maxdd"],
            "sharpe": base["sharpe"], "n_trades": base["n_trades"],
            "cagr_delta": 0.0, "maxdd_delta": 0.0,
        })
        flush_csv()

        # Sweep — pass override per cell instead of mutating globals
        cell = 0
        for w in WINDOWS_DAYS:
            for th_bp in THRESHOLDS_BP:
                cell += 1
                override = {"threshold": th_bp / 1e4, "sma_days": w}
                t0 = time.time()
                r = _run(prices, bench_close, precomputed, mode, funding_override=override)
                d_cagr = r["cagr"] - base["cagr"]
                d_dd = r["maxdd"] - base["maxdd"]
                print(f"      [{cell:2d}/{grid_cells}] th={th_bp:>2d}bp w={w:>2d}d:  "
                      f"CAGR {r['cagr']:>5.2f}% (Δ{d_cagr:+5.2f})  "
                      f"maxDD {r['maxdd']:+6.2f}% (Δ{d_dd:+5.2f})  "
                      f"trades {r['n_trades']:>4d}  ({time.time()-t0:.1f}s)",
                      flush=True)
                rows.append({
                    "mode": mode, "threshold_bp": th_bp, "window_d": w,
                    "cagr": r["cagr"], "maxdd": r["maxdd"],
                    "sharpe": r["sharpe"], "n_trades": r["n_trades"],
                    "cagr_delta": d_cagr, "maxdd_delta": d_dd,
                })
                flush_csv()

    # Restore per-mode overlay defaults so caller env isn't mutated
    config.FUNDING_OVERLAY_BY_MODE = saved_overlay

    print("\n[4/4] Building response-surface tables...")
    df = pd.DataFrame(rows)
    df.to_csv(config.DATA_DIR / "funding_sweep.csv", index=False)
    print(f"      raw results saved to {config.DATA_DIR / 'funding_sweep.csv'}")

    for mode in modes:
        m = df[(df["mode"] == mode) & df["threshold_bp"].notna()]
        if m.empty:
            continue
        base = df[(df["mode"] == mode) & df["threshold_bp"].isna()].iloc[0]
        print(f"\n=== {mode}  baseline CAGR {base['cagr']:.2f}%  maxDD {base['maxdd']:+.2f}% ===")
        print("  Δ CAGR (pp) — rows = window (days), cols = threshold (bp/8h):")
        pivot_c = m.pivot(index="window_d", columns="threshold_bp", values="cagr_delta")
        print(pivot_c.round(2).to_string())
        print("  Δ MaxDD (pp positive=better):")
        pivot_d = m.pivot(index="window_d", columns="threshold_bp", values="maxdd_delta")
        print(pivot_d.round(2).to_string())

    print()


if __name__ == "__main__":
    main()
