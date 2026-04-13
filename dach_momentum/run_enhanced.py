#!/usr/bin/env python3
"""
Enhanced CAN SLIM analysis using real FMP fundamental data.

Uses FMP API for actual quarterly earnings, financial ratios,
cash flow, insider transactions, and analyst estimates.

Usage:
    python run_enhanced.py                  # all trend template candidates
    python run_enhanced.py JEN.DE DRW3.DE   # specific tickers
"""
import sys
sys.path.insert(0, ".")

import logging
import pandas as pd
from dach_momentum import config
from dach_momentum.data import print_data_freshness
from dach_momentum.signals import load_signals
from dach_momentum.external_data import (
    enhanced_canslim, print_enhanced_canslim,
    canslim_score_simfin,
    get_euro_yield_curve, FMP_KEY, FRED_KEY,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)


def main():
    print_data_freshness()

    # Check API keys
    print(f"\nAPI Status:")
    print(f"  FMP:  {'configured' if FMP_KEY else 'MISSING — add FMP_API_KEY to .env'}")
    print(f"  FRED: {'configured' if FRED_KEY else 'MISSING — add FRED_API_KEY to .env'}")

    if not FMP_KEY:
        print("\nERROR: FMP API key required. Create a .env file with:")
        print("  FMP_API_KEY=your_key_here")
        print("Get a free key at: https://financialmodelingprep.com/developer")
        return

    # Macro context from FRED
    if FRED_KEY:
        print("\nMacro Context (FRED):")
        macro = get_euro_yield_curve()
        for name, vals in macro.items():
            print(f"  {name}: {vals['latest']} (as of {vals['date']})")

    # Determine tickers
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        signals = load_signals()
        if not signals:
            print("No signals. Run 'python run_signals.py' first.")
            return

        # Flatten MultiIndex
        for t in signals:
            if isinstance(signals[t].columns, pd.MultiIndex):
                signals[t].columns = signals[t].columns.get_level_values(0)

        tickers = []
        for ticker, df in signals.items():
            if not df.empty and df.iloc[-1].get("trend_template_pass", False):
                mom = df.iloc[-1].get("mom_12_1", 0)
                tickers.append((ticker, mom))

        if not tickers:
            # Fallback: top 6 by momentum
            for ticker, df in signals.items():
                if not df.empty:
                    mom = df.iloc[-1].get("mom_12_1", 0)
                    if pd.notna(mom) and mom > 0.1:
                        tickers.append((ticker, mom))

        tickers.sort(key=lambda x: x[1], reverse=True)
        tickers = [t for t, _ in tickers[:8]]

    print(f"\nAnalyzing {len(tickers)} stocks with FMP data...\n")

    results = []
    for ticker in tickers:
        try:
            # Try SimFin first (free, has historical quarterly data)
            sf_result = canslim_score_simfin(ticker)
            if sf_result.get("quality_score", 0) > 0 or "real quarterly" in sf_result.get("source", ""):
                # SimFin had data
                print(f"\n{'=' * 60}")
                print(f"  {ticker} — Source: {sf_result.get('source', 'simfin')}")
                print(f"{'=' * 60}")
                print(f"  C — Current Quarterly: {'PASS' if sf_result['C_pass'] else 'FAIL'}")
                print(f"    {sf_result['C_details']}")
                print(f"    Earnings accelerating: {'YES' if sf_result['earnings_accelerating'] else 'NO'}")
                if sf_result.get("latest_revenue_growth") is not None:
                    print(f"    Revenue growth: {sf_result['latest_revenue_growth']:+.1f}%")
                print(f"  A — Annual Growth: {'PASS' if sf_result['A_pass'] else 'FAIL'}")
                print(f"    {sf_result['A_details']}")
                print(f"  FCF Positive: {'YES' if sf_result['fcf_positive'] else 'NO'}")
                print(f"  Quality Score: {sf_result['quality_score']}/7")
                results.append({"ticker": ticker, "fmp": sf_result, "has_fmp_data": True})
            else:
                # Fall back to FMP/yfinance
                data = enhanced_canslim(ticker)
                results.append(data)
                print_enhanced_canslim(data)
        except Exception as exc:
            print(f"  {ticker}: failed — {exc}")

    # Summary table
    if results:
        print("=" * 60)
        print("  ENHANCED CAN SLIM SUMMARY")
        print("=" * 60)
        print(f"\n  {'Ticker':<14} {'C':>6} {'A':>6} {'Accel':>6} {'ROE':>6} {'FCF':>5} {'Rev':>8} {'Score':>6}")
        print(f"  {'─'*14} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*5} {'─'*8} {'─'*6}")

        for r in results:
            fmp = r.get("fmp", {})
            c = "PASS" if fmp.get("C_pass") else "FAIL"
            a = "PASS" if fmp.get("A_pass") else "FAIL"
            acc = "YES" if fmp.get("earnings_accelerating") else "no"
            roe = f"{fmp['roe']:.0f}%" if fmp.get("roe") else "N/A"
            fcf = "+" if fmp.get("fcf_positive") else "-"
            rev = f"{fmp.get('revenue_growth', 0):+.0f}%" if fmp.get("revenue_growth") is not None else "N/A"
            score = fmp.get("quality_score", 0)

            print(f"  {r['ticker']:<14} {c:>6} {a:>6} {acc:>6} {roe:>6} {fcf:>5} {rev:>8} {score:>4}/7")

        print()


if __name__ == "__main__":
    main()
