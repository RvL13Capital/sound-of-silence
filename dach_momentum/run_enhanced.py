#!/usr/bin/env python3
"""
Enhanced analysis: yfinance fundamentals + FRED macro context.

Combines our existing CAN SLIM dashboard (yfinance) with FRED
macro data. No FMP or SimFin needed.

Usage:
    python run_enhanced.py                  # all candidates
    python run_enhanced.py JEN.DE DRW3.DE   # specific tickers
"""
import sys
sys.path.insert(0, ".")

import logging
import pandas as pd
from dach_momentum import config
from dach_momentum.data import load_prices, print_data_freshness
from dach_momentum.signals import load_signals
from dach_momentum.canslim import deep_dive, print_deep_dive
from dach_momentum.external_data import get_euro_yield_curve, FRED_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)


def main():
    print_data_freshness()

    # Macro context from FRED
    if FRED_KEY:
        print("\nMacro Context (FRED):")
        macro = get_euro_yield_curve()
        for name, vals in macro.items():
            print(f"  {name}: {vals['latest']} (as of {vals['date']})")
    else:
        print("\nFRED_API_KEY not set — skipping macro context")

    # Determine tickers
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        signals = load_signals()
        if not signals:
            print("No signals. Run 'python run_signals.py' first.")
            return

        for t in signals:
            if isinstance(signals[t].columns, pd.MultiIndex):
                signals[t].columns = signals[t].columns.get_level_values(0)

        tickers = []
        for ticker, df in signals.items():
            if not df.empty and df.iloc[-1].get("trend_template_pass", False):
                mom = df.iloc[-1].get("mom_12_1", 0)
                tickers.append((ticker, mom))

        if not tickers:
            for ticker, df in signals.items():
                if not df.empty:
                    mom = df.iloc[-1].get("mom_12_1", 0)
                    if pd.notna(mom) and mom > 0.1:
                        tickers.append((ticker, mom))

        tickers.sort(key=lambda x: x[1], reverse=True)
        tickers = [t for t, _ in tickers[:8]]

    # Load prices for volume analysis
    prices = load_prices()
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    print(f"\nAnalyzing {len(tickers)} stocks...\n")

    # Run full CAN SLIM deep dive (uses yfinance — already works)
    results = []
    for ticker in tickers:
        try:
            data = deep_dive(
                ticker,
                signals=load_signals() if not tickers else None,
                all_prices=prices,
            )
            results.append(data)
            print_deep_dive(data, regime_on=False)
        except Exception as exc:
            print(f"  {ticker}: failed — {exc}")

    # Summary
    if results:
        print("=" * 64)
        print("  COMPOSITE ASSESSMENT")
        print("=" * 64)
        print(f"\n  {'Ticker':<14} {'C':>4} {'A':>4} {'N':>6} {'S':>6} {'L':>7} {'I':>6}  {'Score':>6}")
        print(f"  {'---'*20}")

        for r in results:
            def _icon(status):
                if status in ("PASS", "STRONG", "LEADER"):
                    return "Y"
                elif status == "PARTIAL":
                    return "~"
                return "N"

            score = 0
            for key in ["C", "A", "N", "S", "L", "I"]:
                st = r[key]["status"]
                if st in ("PASS", "STRONG", "LEADER"):
                    score += 1
                elif st == "PARTIAL":
                    score += 0.5

            print(
                f"  {r['ticker']:<14} "
                f"{_icon(r['C']['status']):>4} "
                f"{_icon(r['A']['status']):>4} "
                f"{_icon(r['N']['status']):>6} "
                f"{_icon(r['S']['status']):>6} "
                f"{_icon(r['L']['status']):>7} "
                f"{_icon(r['I']['status']):>6}  "
                f"{score:.0f}/6"
            )
        print()


if __name__ == "__main__":
    main()
