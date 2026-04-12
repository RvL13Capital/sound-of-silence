#!/usr/bin/env python3
"""
Find the top 50 highest percentage gains within any 6-month period
across the entire universe.
"""
import sys
sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from dach_momentum.data import load_prices

print("Loading prices...")
prices = load_prices()

# Flatten MultiIndex
for t in prices:
    if isinstance(prices[t].columns, pd.MultiIndex):
        prices[t].columns = prices[t].columns.get_level_values(0)

print(f"Loaded {len(prices)} tickers\n")

# Find max 6-month (126 trading days) gain for each stock across all history
results = []

for ticker, df in prices.items():
    if "Close" not in df.columns or len(df) < 126:
        continue

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    # Rolling 126-day return
    ret_6m = close / close.shift(126) - 1

    if ret_6m.dropna().empty:
        continue

    # Find the maximum 6-month gain
    idx_max = ret_6m.idxmax()
    max_gain = ret_6m.loc[idx_max]

    if pd.isna(max_gain):
        continue

    # Get the start date (126 trading days before the peak)
    peak_loc = df.index.get_loc(idx_max)
    start_loc = max(0, peak_loc - 126)
    start_date = df.index[start_loc]
    start_price = float(close.iloc[start_loc])
    end_price = float(close.loc[idx_max])

    results.append({
        "ticker": ticker,
        "gain_pct": round(float(max_gain) * 100, 1),
        "start_date": str(start_date.date()),
        "end_date": str(idx_max.date()),
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
    })

# Sort by gain and take top 50
results.sort(key=lambda x: x["gain_pct"], reverse=True)
top50 = results[:50]

print(f"{'Rank':<6} {'Ticker':<14} {'Gain':>8} {'Start Date':<12} {'End Date':<12} {'Start':>8} {'End':>8}")
print(f"{'─'*6} {'─'*14} {'─'*8} {'─'*12} {'─'*12} {'─'*8} {'─'*8}")

for i, r in enumerate(top50, 1):
    print(f"{i:<6} {r['ticker']:<14} {r['gain_pct']:>+7.1f}% "
          f"{r['start_date']:<12} {r['end_date']:<12} "
          f"{r['start_price']:>8.2f} {r['end_price']:>8.2f}")

print(f"\nTotal stocks analyzed: {len(results)}")
