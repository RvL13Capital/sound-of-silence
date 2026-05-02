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
# Japanese Candlestick Patterns (Homma / Nison)
# ========================================================================== #


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _upper_shadow(h: float, o: float, c: float) -> float:
    return h - max(o, c)


def _lower_shadow(o: float, c: float, l: float) -> float:
    return min(o, c) - l


def _is_bullish(o: float, c: float) -> bool:
    return c > o


def _is_bearish(o: float, c: float) -> bool:
    return o > c


def _avg_body(df: pd.DataFrame, n: int = 14) -> float:
    """Average candle body size over last n bars."""
    opens = df["Open"].iloc[-n:]
    closes = df["Close"].iloc[-n:]
    return float((closes - opens).abs().mean())


def detect_bullish_engulfing(df: pd.DataFrame) -> float:
    """
    Bullish Engulfing (tsutsumi): bearish candle fully engulfed by
    larger bullish candle. Reversal signal at support.
    """
    if len(df) < 16:
        return 0.0
    o1, h1, l1, c1 = [float(df[c].iloc[-2]) for c in ("Open", "High", "Low", "Close")]
    o2, h2, l2, c2 = [float(df[c].iloc[-1]) for c in ("Open", "High", "Low", "Close")]
    if not (_is_bearish(o1, c1) and _is_bullish(o2, c2)):
        return 0.0
    if not (o2 <= c1 and c2 >= o1):
        return 0.0
    score = 50.0
    avg = _avg_body(df)
    if avg > 0 and _body(o2, c2) > avg * 1.5:
        score += 25
    if l2 < l1:
        score += 15
    if _lower_shadow(o2, c2, l2) < _body(o2, c2) * 0.3:
        score += 10
    return min(score, 100.0)


def detect_morning_star(df: pd.DataFrame) -> float:
    """
    Morning Star (sansei boshi): 3-candle reversal.
    Day1=long bearish, Day2=small body (star), Day3=long bullish.
    """
    if len(df) < 16:
        return 0.0
    rows = [(float(df[c].iloc[-3+i]) for c in ("Open", "High", "Low", "Close")) for i in range(3)]
    o1, h1, l1, c1 = rows[0]
    o2, h2, l2, c2 = rows[1]
    o3, h3, l3, c3 = rows[2]
    avg = _avg_body(df, 14)
    if avg <= 0:
        return 0.0
    if not (_is_bearish(o1, c1) and _body(o1, c1) > avg):
        return 0.0
    if _body(o2, c2) > avg * 0.5:
        return 0.0
    if not (_is_bullish(o3, c3) and _body(o3, c3) > avg):
        return 0.0
    score = 55.0
    if c3 > (o1 + c1) / 2:
        score += 25
    if l2 < min(l1, l3):
        score += 10
    if _body(o3, c3) > avg * 1.5:
        score += 10
    return min(score, 100.0)


def detect_hammer(df: pd.DataFrame) -> float:
    """
    Hammer (takuri): small body at top, long lower shadow (>= 2x body).
    Bullish reversal at support after downtrend.
    """
    if len(df) < 16:
        return 0.0
    o, h, l, c = [float(df[col].iloc[-1]) for col in ("Open", "High", "Low", "Close")]
    body = _body(o, c)
    lower = _lower_shadow(o, c, l)
    upper = _upper_shadow(h, o, c)
    if body <= 0 or lower < body * 2:
        return 0.0
    if upper > body * 0.5:
        return 0.0
    score = 50.0
    prior_5 = df["Close"].iloc[-6:-1]
    if float(prior_5.iloc[-1]) < float(prior_5.iloc[0]):
        score += 20
    if lower > body * 3:
        score += 15
    if _is_bullish(o, c):
        score += 15
    return min(score, 100.0)


def detect_three_white_soldiers(df: pd.DataFrame) -> float:
    """
    Three White Soldiers (sanpei): 3 consecutive long bullish candles,
    each closing higher. Strong bullish continuation.
    """
    if len(df) < 16:
        return 0.0
    avg = _avg_body(df, 14)
    if avg <= 0:
        return 0.0
    score = 0.0
    for i in range(-3, 0):
        o_i = float(df["Open"].iloc[i])
        c_i = float(df["Close"].iloc[i])
        if not _is_bullish(o_i, c_i):
            return 0.0
        if _body(o_i, c_i) < avg * 0.8:
            return 0.0
    score = 50.0
    c1 = float(df["Close"].iloc[-3])
    c2 = float(df["Close"].iloc[-2])
    c3 = float(df["Close"].iloc[-1])
    if c3 > c2 > c1:
        score += 25
    o2 = float(df["Open"].iloc[-2])
    o3 = float(df["Open"].iloc[-1])
    if o2 > c1 * 0.95 and o3 > c2 * 0.95:
        score += 15
    for i in range(-3, 0):
        o_i = float(df["Open"].iloc[i])
        h_i = float(df["High"].iloc[i])
        c_i = float(df["Close"].iloc[i])
        if _upper_shadow(h_i, o_i, c_i) < _body(o_i, c_i) * 0.3:
            score += 3
    return min(score, 100.0)


def detect_piercing_line(df: pd.DataFrame) -> float:
    """
    Piercing Line (kirikomi): bearish candle + bullish candle that opens
    below prior low and closes above 50% of prior body.
    """
    if len(df) < 16:
        return 0.0
    o1, c1 = float(df["Open"].iloc[-2]), float(df["Close"].iloc[-2])
    o2, c2 = float(df["Open"].iloc[-1]), float(df["Close"].iloc[-1])
    l1 = float(df["Low"].iloc[-2])
    if not (_is_bearish(o1, c1) and _is_bullish(o2, c2)):
        return 0.0
    if o2 > c1:
        return 0.0
    midpoint = (o1 + c1) / 2
    if c2 < midpoint:
        return 0.0
    score = 55.0
    avg = _avg_body(df, 14)
    if avg > 0 and _body(o1, c1) > avg * 1.2:
        score += 15
    if o2 < l1:
        score += 15
    if c2 > o1 * 0.95:
        score += 15
    return min(score, 100.0)


def detect_doji_star(df: pd.DataFrame) -> float:
    """
    Bullish Doji Star: bearish candle + doji (open≈close), signaling
    seller exhaustion. Needs bullish confirmation on day 3.
    """
    if len(df) < 16:
        return 0.0
    o1, c1 = float(df["Open"].iloc[-2]), float(df["Close"].iloc[-2])
    o2, h2, l2, c2 = [float(df[c].iloc[-1]) for c in ("Open", "High", "Low", "Close")]
    avg = _avg_body(df, 14)
    if avg <= 0:
        return 0.0
    if not _is_bearish(o1, c1):
        return 0.0
    if _body(o1, c1) < avg:
        return 0.0
    doji_body = _body(o2, c2)
    doji_range = h2 - l2
    if doji_range <= 0 or doji_body > doji_range * 0.15:
        return 0.0
    score = 50.0
    if max(o2, c2) < c1:
        score += 20
    if doji_range > avg * 0.5:
        score += 10
    prior_5 = df["Close"].iloc[-7:-2]
    if float(prior_5.iloc[-1]) < float(prior_5.iloc[0]):
        score += 20
    return min(score, 100.0)


def detect_bullish_harami(df: pd.DataFrame) -> float:
    """
    Bullish Harami (harami): large bearish candle + small bullish candle
    contained within prior body. Reversal at support.
    """
    if len(df) < 16:
        return 0.0
    o1, c1 = float(df["Open"].iloc[-2]), float(df["Close"].iloc[-2])
    o2, c2 = float(df["Open"].iloc[-1]), float(df["Close"].iloc[-1])
    if not (_is_bearish(o1, c1) and _is_bullish(o2, c2)):
        return 0.0
    if not (o2 >= c1 and c2 <= o1):
        return 0.0
    avg = _avg_body(df, 14)
    if avg <= 0:
        return 0.0
    score = 45.0
    if _body(o1, c1) > avg * 1.3:
        score += 20
    if _body(o2, c2) < _body(o1, c1) * 0.5:
        score += 20
    prior_5 = df["Close"].iloc[-7:-2]
    if float(prior_5.iloc[-1]) < float(prior_5.iloc[0]):
        score += 15
    return min(score, 100.0)


def detect_marubozu(df: pd.DataFrame) -> float:
    """
    Bullish Marubozu: long body, no (or tiny) shadows.
    Maximum conviction candle.
    """
    if len(df) < 16:
        return 0.0
    o, h, l, c = [float(df[col].iloc[-1]) for col in ("Open", "High", "Low", "Close")]
    if not _is_bullish(o, c):
        return 0.0
    body = _body(o, c)
    upper = _upper_shadow(h, o, c)
    lower = _lower_shadow(o, c, l)
    if body <= 0:
        return 0.0
    if upper > body * 0.05 or lower > body * 0.05:
        if upper > body * 0.15 or lower > body * 0.15:
            return 0.0
        score = 40.0
    else:
        score = 60.0
    avg = _avg_body(df, 14)
    if avg > 0 and body > avg * 2:
        score += 25
    elif avg > 0 and body > avg * 1.5:
        score += 15
    vol = df["Volume"] if "Volume" in df.columns else None
    if vol is not None and len(vol) >= 10:
        if float(vol.iloc[-1]) > float(vol.iloc[-10:].mean()) * 1.5:
            score += 15
    return min(score, 100.0)


# ========================================================================== #
# Combined scoring (chart + candlestick)
# ========================================================================== #


def compute_pattern_score(df: pd.DataFrame) -> tuple[str, float, dict[str, float]]:
    """
    Run all pattern detectors and return (best_pattern, best_score, all_scores).

    Chart patterns (multi-week structure) are the PRIMARY trigger.
    Candlestick patterns (1-3 day Homma/Nison signals) act as CONFIRMATION
    bonus (max +15 pts) — they are not strong enough to trigger entries alone
    in a momentum-filtered universe (most reversal candles fire too early).

    Final score = best_chart_score + candlestick_confirmation_bonus.
    """
    has_ohlc = all(c in df.columns for c in ("Open", "High", "Low", "Close"))

    # Chart patterns (multi-week structure) — primary
    chart = {
        "VCP": detect_vcp(df),
        "CUP_HANDLE": detect_cup_handle(df),
        "POCKET_PIVOT": detect_pocket_pivot(df),
        "FLAG_BREAKOUT": detect_flag_breakout(df),
        "DOUBLE_BOTTOM": detect_double_bottom(df),
    }

    # Continuation candlesticks (match momentum context)
    continuation: dict[str, float] = {}
    # Reversal candlesticks (confirmation only)
    reversal: dict[str, float] = {}
    if has_ohlc and len(df) >= 16:
        continuation = {
            "THREE_SOLDIERS": detect_three_white_soldiers(df),
            "MARUBOZU": detect_marubozu(df),
        }
        reversal = {
            "ENGULFING": detect_bullish_engulfing(df),
            "MORNING_STAR": detect_morning_star(df),
            "HAMMER": detect_hammer(df),
            "PIERCING_LINE": detect_piercing_line(df),
            "DOJI_STAR": detect_doji_star(df),
            "HARAMI": detect_bullish_harami(df),
        }

    # Best chart pattern = primary score
    best_chart_name = max(chart, key=chart.get) if chart else ""
    best_chart_score = chart[best_chart_name] if chart else 0.0

    # Candlestick confirmation bonus (chart pattern must be active)
    bonus = 0.0
    bonus_source = ""
    if best_chart_score >= 30:
        # Continuation candles — stronger bonus (context aligned)
        if continuation:
            best_cont = max(continuation, key=continuation.get)
            if continuation[best_cont] >= 50:
                bonus = min(continuation[best_cont] / 100 * 15, 15)
                bonus_source = best_cont
        # Reversal candles — weaker bonus (only counts if nothing else)
        if bonus == 0 and reversal:
            best_rev = max(reversal, key=reversal.get)
            if reversal[best_rev] >= 60:
                bonus = min(reversal[best_rev] / 100 * 8, 8)
                bonus_source = best_rev

    # Final combined score
    final_score = min(best_chart_score + bonus, 100.0)
    best_pattern = (
        f"{best_chart_name}+{bonus_source}" if bonus_source else best_chart_name
    )

    # All candidate scores for diagnostics (not for max-selection)
    diag = {**chart, **continuation, **reversal}
    return best_pattern, final_score, diag
