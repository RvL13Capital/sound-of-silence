#!/usr/bin/env python3
"""
Run CAN SLIM deep dive analysis on trend template candidates.

Usage: python run_canslim.py                 # analyze all candidates
       python run_canslim.py JEN.DE DRW3.DE  # analyze specific tickers
"""
import sys
sys.path.insert(0, ".")

import logging
import pandas as pd
import yfinance as yf
from dach_momentum import config
from dach_momentum.data import load_prices
from dach_momentum.signals import load_signals
from dach_momentum.canslim import deep_dive, print_deep_dive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main():
    # Load saved signals
    signals = load_signals()
    if not signals:
        print("No saved signals. Run 'python run_signals.py' first.")
        return

    # Load prices (for volume analysis)
    prices = load_prices()
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    # Determine regime status
    regime_on = False
    if signals:
        sample = next(iter(signals.values()))
        if "regime_on" in sample.columns and not sample.empty:
            regime_on = bool(sample.iloc[-1].get("regime_on", False))

    # Determine which tickers to analyze
    if len(sys.argv) > 1:
        # User specified tickers
        tickers = sys.argv[1:]
    else:
        # Find trend template candidates (or top momentum if none)
        tickers = []
        for ticker, df in signals.items():
            if not df.empty and df.iloc[-1].get("trend_template_pass", False):
                mom = df.iloc[-1].get("mom_12_1", 0)
                tickers.append((ticker, mom))

        if not tickers:
            print("No trend template candidates. Using top 6 by momentum.\n")
            all_mom = []
            for ticker, df in signals.items():
                if not df.empty:
                    mom = df.iloc[-1].get("mom_12_1", 0)
                    if pd.notna(mom):
                        all_mom.append((ticker, mom))
            all_mom.sort(key=lambda x: x[1], reverse=True)
            tickers = [t for t, _ in all_mom[:6]]
        else:
            tickers.sort(key=lambda x: x[1], reverse=True)
            tickers = [t for t, _ in tickers]

    print(f"\n{'=' * 64}")
    print(f"  CAN SLIM + MINERVINI DEEP DIVE ANALYSIS")
    print(f"  Analyzing {len(tickers)} stocks")
    print(f"  Market Regime: {'ON (bullish)' if regime_on else 'OFF (bearish)'}")
    print(f"{'=' * 64}")

    # Run deep dive for each
    results = []
    for ticker in tickers:
        try:
            data = deep_dive(
                ticker,
                signals=signals,
                all_prices=prices,
            )
            results.append(data)
            print_deep_dive(data, regime_on=regime_on)
        except Exception as exc:
            logger.error("Failed to analyze %s: %s", ticker, exc)

    # Final summary table
    if results:
        print(f"\n{'=' * 64}")
        print("  SUMMARY SCORECARD")
        print(f"{'=' * 64}")
        print(f"\n  {'Ticker':<12} {'C':>4} {'A':>4} {'N':>6} {'S':>6} {'L':>7} {'I':>6} {'M':>4}  {'Score':>6}")
        print(f"  {'─' * 12} {'─' * 4} {'─' * 4} {'─' * 6} {'─' * 6} {'─' * 7} {'─' * 6} {'─' * 4}  {'─' * 6}")

        for r in results:
            def _icon(status):
                if status in ("PASS", "STRONG", "LEADER"):
                    return "✓"
                elif status == "PARTIAL":
                    return "◐"
                return "✗"

            score = 0
            for key, status_key in [
                ("C", "status"), ("A", "status"), ("N", "status"),
                ("S", "status"), ("L", "status"), ("I", "status"),
            ]:
                st = r[key][status_key]
                if st in ("PASS", "STRONG", "LEADER"):
                    score += 1
                elif st == "PARTIAL":
                    score += 0.5
            if regime_on:
                score += 1

            print(
                f"  {r['ticker']:<12} "
                f"{_icon(r['C']['status']):>4} "
                f"{_icon(r['A']['status']):>4} "
                f"{_icon(r['N']['status']):>6} "
                f"{_icon(r['S']['status']):>6} "
                f"{_icon(r['L']['status']):>7} "
                f"{_icon(r['I']['status']):>6} "
                f"{'✓' if regime_on else '✗':>4}  "
                f"{score:.0f}/7"
            )

        print()


if __name__ == "__main__":
    main()
