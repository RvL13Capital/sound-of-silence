#!/usr/bin/env python3
"""
Analyze max adverse excursion (MAE) for each trade in the backtest.
Shows how far underwater each position went before either recovering or being stopped out.
"""
import sys
sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from dach_momentum.data import load_prices, print_data_freshness
from dach_momentum import config

print_data_freshness()

# Load trade log
for mode in ["canslim", "momentum"]:
    path = config.DATA_DIR / f"backtest_trades_{mode}.csv"
    if not path.exists():
        continue

    trades = pd.read_csv(path)
    print(f"\n{'=' * 75}")
    print(f"  MAX ADVERSE EXCURSION — {mode.upper()} MODE")
    print(f"  (Worst drawdown each position experienced before exit)")
    print(f"{'=' * 75}")

    # Load prices
    prices = load_prices()
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    results = []
    for _, trade in trades.iterrows():
        ticker = trade["ticker"]
        entry_date = pd.Timestamp(trade["entry_date"])
        exit_date = pd.Timestamp(trade["exit_date"])
        entry_price = trade["entry_price"]

        # Find matching price data
        # Reconstruct yfinance ticker from trade log ticker
        yf_ticker = ticker.replace("_", ".")
        if yf_ticker not in prices:
            # Try common patterns
            for suffix in [".DE", ".VI", ".SW", ".PA", ".AS", ".BR", ".MI", ".MC", ".ST", ".CO", ".HE", ".OL", ".LS"]:
                candidate = ticker.rsplit("_", 1)[0] + suffix if "_" in ticker else ticker + suffix
                if candidate in prices:
                    yf_ticker = candidate
                    break

        if yf_ticker not in prices:
            continue

        df = prices[yf_ticker]
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # Get prices during holding period
        mask = (close.index >= entry_date) & (close.index <= exit_date)
        holding = close[mask]

        if holding.empty:
            continue

        # Calculate max adverse excursion
        min_price = holding.min()
        max_price = holding.max()
        mae_pct = (min_price / entry_price - 1) * 100  # worst drawdown from entry
        mfe_pct = (max_price / entry_price - 1) * 100  # best gain from entry
        final_pct = trade["pnl_pct"]

        results.append({
            "ticker": ticker,
            "entry_date": trade["entry_date"],
            "entry_price": entry_price,
            "exit_reason": trade["exit_reason"],
            "final_pnl_pct": round(final_pct, 1),
            "max_drawdown_pct": round(mae_pct, 1),
            "max_gain_pct": round(mfe_pct, 1),
            "gave_back_pct": round(mfe_pct - final_pct, 1) if mfe_pct > 0 else 0,
            "holding_days": trade["holding_days"],
        })

    if not results:
        print("  No trades could be analyzed.")
        continue

    df_results = pd.DataFrame(results)

    # --- Winners analysis ---
    winners = df_results[df_results["final_pnl_pct"] > 0].copy()
    losers = df_results[df_results["final_pnl_pct"] <= 0].copy()

    print(f"\n  WINNERS ({len(winners)} trades)")
    print(f"  {'─' * 71}")
    print(f"  {'Ticker':<14} {'Entry':<12} {'Final P&L':>10} {'Max DD':>8} {'Max Gain':>10} {'Gave Back':>10}")
    print(f"  {'─'*14} {'─'*12} {'─'*10} {'─'*8} {'─'*10} {'─'*10}")

    winners_sorted = winners.sort_values("final_pnl_pct", ascending=False)
    for _, r in winners_sorted.head(20).iterrows():
        print(f"  {r['ticker']:<14} {r['entry_date']:<12} {r['final_pnl_pct']:>+9.1f}% "
              f"{r['max_drawdown_pct']:>+7.1f}% {r['max_gain_pct']:>+9.1f}% "
              f"{r['gave_back_pct']:>9.1f}%")

    if len(winners) > 0:
        print(f"\n  Winner stats:")
        print(f"    Avg max drawdown during hold:  {winners['max_drawdown_pct'].mean():+.1f}%")
        print(f"    Worst drawdown on a winner:    {winners['max_drawdown_pct'].min():+.1f}%")
        print(f"    Avg gain given back at exit:   {winners['gave_back_pct'].mean():.1f}%")

    # --- Losers analysis ---
    print(f"\n  LOSERS ({len(losers)} trades)")
    print(f"  {'─' * 71}")
    print(f"  {'Ticker':<14} {'Entry':<12} {'Final P&L':>10} {'Max DD':>8} {'Max Gain':>10} {'Exit Reason':<18}")
    print(f"  {'─'*14} {'─'*12} {'─'*10} {'─'*8} {'─'*10} {'─'*18}")

    losers_sorted = losers.sort_values("final_pnl_pct")
    for _, r in losers_sorted.head(20).iterrows():
        print(f"  {r['ticker']:<14} {r['entry_date']:<12} {r['final_pnl_pct']:>+9.1f}% "
              f"{r['max_drawdown_pct']:>+7.1f}% {r['max_gain_pct']:>+9.1f}% "
              f"{r['exit_reason']:<18}")

    if len(losers) > 0:
        print(f"\n  Loser stats:")
        print(f"    Avg max drawdown:              {losers['max_drawdown_pct'].mean():+.1f}%")
        print(f"    Worst single-trade drawdown:   {losers['max_drawdown_pct'].min():+.1f}%")
        print(f"    % that were briefly profitable: {(losers['max_gain_pct'] > 0).mean()*100:.0f}%")

    # --- Overall distribution ---
    print(f"\n  DRAWDOWN DISTRIBUTION (all {len(df_results)} trades)")
    print(f"  {'─' * 71}")
    bins = [0, -5, -10, -15, -20, -30, -50, -100]
    bins.reverse()
    for i in range(len(bins) - 1):
        count = ((df_results["max_drawdown_pct"] > bins[i]) &
                 (df_results["max_drawdown_pct"] <= bins[i+1])).sum()
        pct = count / len(df_results) * 100
        bar = "█" * int(pct / 2)
        print(f"    {bins[i]:>+4d}% to {bins[i+1]:>+4d}%:  {count:>4d} ({pct:>5.1f}%)  {bar}")

    print()
