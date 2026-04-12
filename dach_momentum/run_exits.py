#!/usr/bin/env python3
"""
Run exit scan on current or hypothetical positions.

Usage:
  python run_exits.py                    # simulate positions entered 30 days ago
  python run_exits.py --days 60          # simulate positions entered 60 days ago
  python run_exits.py --manual           # enter positions manually
"""
import sys
sys.path.insert(0, ".")

import logging
import pandas as pd
from dach_momentum import config
from dach_momentum.signals import load_signals
from dach_momentum.positions import (
    Position, PortfolioState,
    simulate_watchlist_positions, scan_all_exits, print_exit_scan,
    calculate_stop_price,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)


def main():
    signals = load_signals()
    if not signals:
        print("No saved signals. Run 'python run_signals.py' first.")
        return

    # Flatten MultiIndex if present
    for t in signals:
        if isinstance(signals[t].columns, pd.MultiIndex):
            signals[t].columns = signals[t].columns.get_level_values(0)

    # Determine regime
    regime_on = False
    sample = next(iter(signals.values()))
    if "regime_on" in sample.columns and not sample.empty:
        regime_on = bool(sample.iloc[-1].get("regime_on", False))

    # Parse args
    days = 30
    manual = False
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
        if arg == "--manual":
            manual = True

    print(f"\n{'=' * 70}")
    print("  POSITION & EXIT MANAGEMENT")
    print(f"  Market Regime: {'ON (bullish)' if regime_on else 'OFF (bearish)'}")
    print(f"{'=' * 70}")

    if manual:
        # Manual position entry
        portfolio = PortfolioState()
        print("\nEnter positions (ticker entry_price entry_date, empty line to finish):")
        print("Example: JEN.DE 25.50 2025-09-15")
        while True:
            line = input("> ").strip()
            if not line:
                break
            parts = line.split()
            if len(parts) >= 2:
                ticker = parts[0]
                price = float(parts[1])
                date = parts[2] if len(parts) > 2 else "2025-01-01"

                # Get ATR from signals if available
                atr = None
                if ticker in signals and not signals[ticker].empty:
                    atr_val = signals[ticker].iloc[-1].get("atr_14")
                    if pd.notna(atr_val):
                        atr = float(atr_val) if not isinstance(atr_val, pd.Series) else float(atr_val.iloc[0])

                stop = calculate_stop_price(price, atr)
                pos = Position(
                    ticker=ticker,
                    entry_date=date,
                    entry_price=price,
                    shares=100,
                    stop_price=stop,
                    risk_per_share=price - stop,
                )
                portfolio.positions.append(pos)
                print(f"  Added {ticker} @ {price:.2f}, stop @ {stop:.2f}")
    else:
        # Simulate positions entered N days ago
        print(f"\nSimulating positions as if entered {days} days ago...")
        print("(Using trend template candidates from current screen)")

        portfolio = simulate_watchlist_positions(signals, entry_offset_days=days)

        if not portfolio.open_positions:
            print("\nNo trend template candidates found to simulate.")
            print("Trying with all stocks that have strong momentum...\n")

            # Fallback: simulate positions for top momentum stocks
            top_mom = []
            for ticker, df in signals.items():
                if df.empty or len(df) < days + 1:
                    continue
                mom = df.iloc[-1].get("mom_12_1", 0)
                if pd.notna(mom) and mom > 0.2:  # >20% momentum
                    top_mom.append((ticker, mom))

            top_mom.sort(key=lambda x: x[1], reverse=True)
            for ticker, _ in top_mom[:6]:
                df = signals[ticker]
                entry_row = df.iloc[-(days + 1)]
                entry_price = entry_row.get("Close", 0)
                if isinstance(entry_price, pd.Series):
                    entry_price = entry_price.iloc[0]
                if entry_price <= 0:
                    continue

                atr = entry_row.get("atr_14")
                if isinstance(atr, pd.Series):
                    atr = atr.iloc[0]

                stop = calculate_stop_price(
                    float(entry_price),
                    float(atr) if pd.notna(atr) else None,
                )

                pos = Position(
                    ticker=ticker,
                    entry_date=str(df.index[-(days + 1)].date()),
                    entry_price=float(entry_price),
                    shares=100,
                    stop_price=stop,
                    risk_per_share=float(entry_price) - stop,
                )

                # Track high
                for _, row in df.iloc[-(days + 1):].iterrows():
                    p = row.get("Close", 0)
                    if isinstance(p, pd.Series):
                        p = p.iloc[0]
                    if p > pos.highest_since_entry:
                        pos.highest_since_entry = float(p)
                if pos.highest_since_entry >= pos.entry_price * 1.2:
                    pos.trailing_active = True

                portfolio.positions.append(pos)

    if not portfolio.open_positions:
        print("\nNo positions to scan.")
        return

    # Print position summary
    print(f"\n  Open Positions: {portfolio.position_count}")
    print(f"  {'─' * 66}")
    print(f"  {'Ticker':<12} {'Entry Date':<12} {'Entry':>8} {'Stop':>8} "
          f"{'Risk/Sh':>8} {'Trail':>6}")
    print(f"  {'─'*12} {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
    for p in portfolio.open_positions:
        trail = "YES" if p.trailing_active else "no"
        print(f"  {p.ticker:<12} {p.entry_date:<12} {p.entry_price:>8.2f} "
              f"{p.stop_price:>8.2f} {p.risk_per_share:>8.2f} {trail:>6}")

    # Run exit scan
    reports = scan_all_exits(portfolio, signals)
    print_exit_scan(reports)

    # Regime-specific guidance
    if not regime_on:
        exits_triggered = sum(1 for r in reports if r.get("exit_triggered"))
        holds = sum(1 for r in reports
                    if not r.get("exit_triggered") and r.get("current_price"))

        print(f"  {'=' * 66}")
        print("  REGIME-OFF ACTION PLAN")
        print(f"  {'=' * 66}")
        print(f"  Positions to EXIT:  {exits_triggered}")
        print(f"  Positions to HOLD:  {holds}")
        print(f"  New entries:        BLOCKED")
        print()

        if holds > 0:
            print("  Held positions are above their 10-week SMA despite")
            print("  bearish regime — showing relative strength. Continue")
            print("  monitoring weekly. Exit if they break below 10w SMA.")
        if exits_triggered > 0:
            print(f"\n  Execute {exits_triggered} exit(s) within the timeframe shown.")
            print("  Park proceeds in cash until regime turns ON.")
        print()


if __name__ == "__main__":
    main()
