#!/usr/bin/env python3
"""
Run the fundamental research dashboard on all trend template candidates.

First identifies which stocks pass the technical screen (trend template),
then pulls fundamental data for each to assess earnings quality,
valuation, cash flow, insider activity, and analyst coverage.

Usage: python run_dashboard.py
"""
import sys
sys.path.insert(0, ".")

import logging
import pandas as pd
import yfinance as yf
from dach_momentum import config
from dach_momentum.data import load_prices
from dach_momentum.signals import compute_all_signals, load_signals
from dach_momentum.dashboard import run_dashboard, print_dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy yfinance logs
logging.getLogger("yfinance").setLevel(logging.WARNING)


def main():
    # --- Try loading pre-computed signals first ---
    signals = load_signals()

    if not signals:
        print("No saved signals found. Computing from price data...")
        prices = load_prices()
        if not prices:
            print("ERROR: No price data. Run 'python -m dach_momentum data' first.")
            return

        # Flatten MultiIndex columns
        for t in prices:
            if isinstance(prices[t].columns, pd.MultiIndex):
                prices[t].columns = prices[t].columns.get_level_values(0)

        # Load benchmark
        bench = yf.download("^GDAXI", start="2005-01-01",
                            auto_adjust=False, progress=False)
        if isinstance(bench.columns, pd.MultiIndex):
            bench.columns = bench.columns.get_level_values(0)

        filtered_path = config.DATA_DIR / "universe_filtered.csv"
        filtered = pd.read_csv(filtered_path)
        filtered_tickers = filtered["yf_ticker"].tolist()

        signals = compute_all_signals(
            prices=prices,
            benchmark_prices=bench,
            filtered_tickers=filtered_tickers,
        )

    # --- Find trend template candidates ---
    candidates = []
    for ticker, df in signals.items():
        if df.empty:
            continue
        last = df.iloc[-1]
        if last.get("trend_template_pass", False):
            candidates.append({
                "ticker": ticker,
                "mom_12_1": last.get("mom_12_1", 0),
                "pct_from_52w_high": last.get("pct_from_52w_high", 0),
                "close": last.get("Close", 0),
                "regime_on": last.get("regime_on", False),
            })

    if not candidates:
        print("\nNo stocks currently pass the trend template.")
        print("The market regime may be OFF (bearish).")
        print("\nRunning dashboard on top 6 by momentum instead...\n")

        # Fallback: show top momentum stocks even if template doesn't pass
        all_mom = []
        for ticker, df in signals.items():
            if df.empty:
                continue
            last = df.iloc[-1]
            mom = last.get("mom_12_1")
            if pd.notna(mom):
                all_mom.append({"ticker": ticker, "mom_12_1": mom})

        all_mom.sort(key=lambda x: x["mom_12_1"], reverse=True)
        candidates = all_mom[:6]

    # --- Sort by momentum ---
    candidates.sort(key=lambda x: x.get("mom_12_1", 0), reverse=True)

    print("\n" + "=" * 60)
    print("FUNDAMENTAL RESEARCH DASHBOARD")
    print(f"Analyzing {len(candidates)} trend template candidates")
    print("=" * 60)

    # Check regime
    if candidates and "regime_on" in candidates[0]:
        regime = "ON" if candidates[0]["regime_on"] else "OFF"
        print(f"Market regime: {regime}")
        if regime == "OFF":
            print("NOTE: Regime is OFF — these are watchlist candidates, NOT buys.")

    # --- Print technical summary first ---
    print("\nTechnical Summary:")
    print(f"  {'Ticker':<12} {'Close':>8} {'12m Mom':>10} {'vs 52w High':>12}")
    print(f"  {'─'*12} {'─'*8} {'─'*10} {'─'*12}")
    for c in candidates:
        print(f"  {c['ticker']:<12} {c.get('close',0):>8.2f} "
              f"{c.get('mom_12_1',0):>+9.1%} "
              f"{c.get('pct_from_52w_high',0):>+11.1%}")

    # --- Run fundamental dashboard for each ---
    tickers = [c["ticker"] for c in candidates]
    print(f"\nFetching fundamental data for {len(tickers)} stocks...")
    results = run_dashboard(tickers)

    # --- Final summary table ---
    print("\n" + "=" * 60)
    print("COMPOSITE ASSESSMENT")
    print("=" * 60)
    print(f"\n  {'Ticker':<12} {'EPS Accel':>10} {'Rev Accel':>10} "
          f"{'CF Quality':>10} {'Insiders':>10} {'PEG':>8} {'Verdict':>10}")
    print(f"  {'─'*12} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*8} {'─'*10}")

    for r in results:
        e = r["earnings"]
        cf = r["cashflow"]
        ins = r["insiders"]
        v = r["valuation"]

        eps_acc = "YES" if e["eps_accelerating"] else "no"
        rev_acc = "YES" if e["revenue_accelerating"] else "no"
        cf_qual = cf["quality_flag"]
        insider = ins["net_insider_signal"]
        peg = f"{v['peg_ratio']:.1f}" if v["peg_ratio"] else "N/A"

        # Simple scoring
        score = 0
        if e["eps_accelerating"]:
            score += 2
        if e["revenue_accelerating"]:
            score += 1
        if cf["quality_flag"] == "GOOD":
            score += 1
        elif cf["quality_flag"] == "WARNING":
            score -= 1
        if ins["net_insider_signal"] == "BUYING":
            score += 2
        elif ins["net_insider_signal"] == "SELLING":
            score -= 1
        if v["peg_ratio"] and v["peg_ratio"] < 1.5:
            score += 1
        elif v["peg_ratio"] and v["peg_ratio"] > 3.0:
            score -= 1

        if score >= 4:
            verdict = "STRONG"
        elif score >= 2:
            verdict = "OK"
        elif score >= 0:
            verdict = "WEAK"
        else:
            verdict = "AVOID"

        print(f"  {r['ticker']:<12} {eps_acc:>10} {rev_acc:>10} "
              f"{cf_qual:>10} {insider:>10} {peg:>8} {verdict:>10}")

    print()


if __name__ == "__main__":
    main()
