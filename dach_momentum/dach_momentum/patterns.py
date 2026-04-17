"""
Technical pattern recognition for the Super Rich strategy.

Detects high-probability chart patterns used by O'Neil and Minervini:
- VCP (Volatility Contraction Pattern)  — Minervini's signature setup
- Cup and Handle                        — O'Neil's classic base pattern
- Pocket Pivot                          — within-uptrend entry point
- Flag Breakout                         — tight consolidation after trend
- Double Bottom                         — reversal pattern

Each detector returns a confidence score 0-100.
The combined `compute_pattern_score` returns the best pattern + score.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ========================================================================== #
# VCP - Volatility Contraction Pattern (Minervini)
# ========================================================================== #


def detect_vcp(df: pd.DataFrame, lookback: int = 60) -> float:
    """
    Volatility Contraction Pattern: sequential tightening pullbacks with
    declining volume, price near the recent high.

    Returns score 0-100.
    """
    if len(df) < lookback:
        return 0.0

    recent = df.iloc[-lookback:]
    close = recent["Close"]
    high = recent["High"] if "High" in recent.columns else close
    volume = recent["Volume"] if "Volume" in recent.columns else None

    # Find local peaks/troughs with a 5-day window
    peaks: list[tuple[int, float]] = []
    troughs: list[tuple[int, float]] = []
    w = 5
    for i in range(w, len(close) - w):
        window = close.iloc[i - w:i + w + 1]
        if close.iloc[i] == window.max():
            peaks.append((i, float(close.iloc[i])))
        elif close.iloc[i] == window.min():
            troughs.append((i, float(close.iloc[i])))

    # Need at least 2 contraction cycles
    if len(peaks) < 2 or len(troughs) < 2:
        return 0.0

    # Compute last 2-3 pullback depths
    pullbacks: list[float] = []
    for i in range(min(len(peaks) - 1, 3)):
        p1_idx, p1_price = peaks[-(i + 2)]
        p2_idx, _ = peaks[-(i + 1)]
        in_between = [t for t in troughs if p1_idx < t[0] < p2_idx]
        if not in_between:
            continue
        trough_price = min(t[1] for t in in_between)
        pullbacks.append((p1_price - trough_price) / p1_price)

    if len(pullbacks) < 2:
        return 0.0

    score = 0.0

    # Pullbacks decreasing (contraction)
    contracting = all(pullbacks[i] < pullbacks[i - 1] for i in range(1, len(pullbacks)))
    if contracting:
        score += 40

    # Last pullback tight (<10%)
    if pullbacks[-1] < 0.10:
        score += 25
    elif pullbacks[-1] < 0.15:
        score += 10

    # Price near recent high
    if close.iloc[-1] >= high.max() * 0.95:
        score += 20

    # Volume declining during contractions
    if volume is not None and len(volume) >= lookback:
        early_vol = float(volume.iloc[:lookback // 2].mean())
        late_vol = float(volume.iloc[-10:].mean())
        if early_vol > 0 and late_vol < early_vol * 0.85:
            score += 15

    return min(score, 100.0)


# ========================================================================== #
# Cup and Handle (O'Neil)
# ========================================================================== #


def detect_cup_handle(df: pd.DataFrame, lookback: int = 150) -> float:
    """
    Cup and Handle: U-shaped base + small handle pullback + breakout.

    Returns score 0-100.
    """
    if len(df) < lookback:
        return 0.0

    recent = df.iloc[-lookback:]
    close = recent["Close"]

    third = len(close) // 3
    first_third = close.iloc[:third]
    middle_third = close.iloc[third:2 * third]
    last_third = close.iloc[2 * third:]

    left_high = float(first_third.max())
    cup_low = float(middle_third.min())
    right_high = float(last_third.max())
    current = float(close.iloc[-1])

    if left_high <= 0:
        return 0.0

    score = 0.0

    # Cup depth 15-35% is ideal
    cup_depth = (left_high - cup_low) / left_high
    if 0.15 <= cup_depth <= 0.35:
        score += 30
    elif 0.10 <= cup_depth <= 0.40:
        score += 15

    # Right side recovered to within 5% of left high
    if right_high >= left_high * 0.95:
        score += 25

    # Handle: last 15-20 bars, shallow pullback from right high
    handle = last_third.iloc[-20:]
    if len(handle) >= 10:
        handle_low = float(handle.min())
        handle_pullback = (right_high - handle_low) / right_high if right_high > 0 else 0
        if 0.03 <= handle_pullback <= 0.15:
            score += 20

    # Breaking out above the right_high
    if current >= right_high * 0.98:
        score += 25

    return min(score, 100.0)


# ========================================================================== #
# Pocket Pivot (Minervini/Morales)
# ========================================================================== #


def detect_pocket_pivot(df: pd.DataFrame) -> float:
    """
    Pocket Pivot: single-day up-move with volume exceeding the largest
    down-volume bar of the past 10 days. Must be above 10-day SMA.

    Returns score 0-100.
    """
    if len(df) < 20 or "Volume" not in df.columns:
        return 0.0

    recent = df.iloc[-15:]
    close = recent["Close"]
    volume = recent["Volume"]

    today_change = float(close.iloc[-1]) / float(close.iloc[-2]) - 1
    today_vol = float(volume.iloc[-1])

    # Must be up day
    if today_change <= 0:
        return 0.0

    score = 20.0  # base for valid up day

    # Volume > max down-volume of past 10 days
    past_10_close = close.iloc[-12:-1]
    past_10_changes = past_10_close.pct_change().dropna().values
    past_10_vol = volume.iloc[-11:-1].values[1:]  # align with changes
    if len(past_10_changes) > 0 and len(past_10_vol) == len(past_10_changes):
        down_vol = past_10_vol[past_10_changes < 0]
        if len(down_vol) > 0 and today_vol > float(down_vol.max()):
            score += 40

    # Price above 10-day SMA
    sma_10 = float(close.iloc[-10:].mean())
    if close.iloc[-1] > sma_10:
        score += 20

    # Price above 50-day SMA (if available)
    if len(df) >= 50:
        sma_50 = float(df["Close"].iloc[-50:].mean())
        if close.iloc[-1] > sma_50:
            score += 20

    return min(score, 100.0)


# ========================================================================== #
# Flag Breakout (classic)
# ========================================================================== #


def detect_flag_breakout(df: pd.DataFrame) -> float:
    """
    Tight flag/consolidation breakout after a strong prior uptrend.

    Returns score 0-100.
    """
    if len(df) < 60:
        return 0.0

    recent = df.iloc[-60:]
    close = recent["Close"]

    # Prior trend: first 40 days should show >= 15% gain
    prior = close.iloc[:40]
    if prior.iloc[0] <= 0:
        return 0.0
    trend_gain = float(prior.iloc[-1]) / float(prior.iloc[0]) - 1

    if trend_gain < 0.15:
        return 0.0

    # Flag: last 20 days tight sideways
    flag = close.iloc[-20:]
    flag_mean = float(flag.mean())
    if flag_mean <= 0:
        return 0.0
    flag_range = (float(flag.max()) - float(flag.min())) / flag_mean

    score = 0.0

    # Tight range (<8% is best)
    if flag_range < 0.06:
        score += 40
    elif flag_range < 0.10:
        score += 25
    elif flag_range < 0.15:
        score += 10

    # Current price breaking out of flag high
    flag_high = float(flag.iloc[:-3].max()) if len(flag) > 3 else float(flag.max())
    if close.iloc[-1] >= flag_high * 0.99:
        score += 30

    # Prior trend strength
    if trend_gain > 0.30:
        score += 20
    elif trend_gain > 0.20:
        score += 10

    # Base score for valid flag setup
    score += 10

    return min(score, 100.0)


# ========================================================================== #
# Double Bottom (reversal)
# ========================================================================== #


def detect_double_bottom(df: pd.DataFrame, lookback: int = 90) -> float:
    """
    Double Bottom: two lows at similar price separated by an intermediate rally.
    Valid breakout when price exceeds the peak between the two lows.

    Returns score 0-100.
    """
    if len(df) < lookback:
        return 0.0

    recent = df.iloc[-lookback:]
    close = recent["Close"]

    half = len(close) // 2
    first_half = close.iloc[:half]
    second_half = close.iloc[half:]

    first_low = float(first_half.min())
    first_low_idx = first_half.idxmin()
    second_low = float(second_half.min())
    second_low_idx = second_half.idxmin()

    if first_low <= 0:
        return 0.0

    # Peak between the two lows
    between = close.loc[first_low_idx:second_low_idx]
    if len(between) < 10:
        return 0.0
    peak_between = float(between.max())

    score = 0.0

    # Lows within 5% of each other
    low_diff = abs(first_low - second_low) / first_low
    if low_diff < 0.05:
        score += 35
    elif low_diff < 0.10:
        score += 20

    # Peak between should be 10-30% above lows (meaningful rally)
    base_low = min(first_low, second_low)
    if base_low > 0:
        peak_height = (peak_between - base_low) / base_low
        if 0.10 <= peak_height <= 0.30:
            score += 25
        elif 0.07 <= peak_height <= 0.40:
            score += 12

    # Current price breaking above peak_between (confirmation breakout)
    if float(close.iloc[-1]) >= peak_between * 0.98:
        score += 30

    # Lows should be in lower portion of range (true bottom)
    total_high = float(close.max())
    if total_high > 0:
        if first_low < total_high * 0.88 and second_low < total_high * 0.88:
            score += 10

    return min(score, 100.0)


# ========================================================================== #
# Combined scoring
# ========================================================================== #


def compute_pattern_score(df: pd.DataFrame) -> tuple[str, float, dict[str, float]]:
    """
    Run all pattern detectors and return (best_pattern, best_score, all_scores).
    """
    patterns = {
        "VCP": detect_vcp(df),
        "CUP_HANDLE": detect_cup_handle(df),
        "POCKET_PIVOT": detect_pocket_pivot(df),
        "FLAG_BREAKOUT": detect_flag_breakout(df),
        "DOUBLE_BOTTOM": detect_double_bottom(df),
    }
    best_pattern = max(patterns, key=patterns.get)
    best_score = patterns[best_pattern]
    return best_pattern, best_score, patterns
