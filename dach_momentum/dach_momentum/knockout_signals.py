"""
KnockoutSwing v1.0 — Setup detection for KO certificate swing trades.

Three A+ setups on 4 major indices (DAX, S&P 500, NDX, Euro Stoxx 50):
  A: Trend Pullback to EMA(50) with RSI confirmation
  B: Consolidation Breakout with volume + retest
  C: Higher-Low / Lower-High Continuation

Only trades WITH the dominant trend. No counter-trend.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from . import config
from .signals import ema, atr, rsi, adx, rolling_high, rolling_low, bollinger_bandwidth


# ========================================================================== #
# Trend filter (Mandate 1)
# ========================================================================== #

def compute_ko_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute EMA-based trend direction for KO trading.

    Long:  Close > EMA(50) > EMA(200), both rising
    Short: Close < EMA(50) < EMA(200), both falling
    """
    close = df["Close"]
    out = pd.DataFrame(index=df.index)

    out["ema_50"] = ema(close, config.KO_EMA_FAST)
    out["ema_200"] = ema(close, config.KO_EMA_SLOW)
    out["ema_50_prev"] = out["ema_50"].shift(1)
    out["ema_200_prev"] = out["ema_200"].shift(1)

    out["trend_long"] = (
        (close > out["ema_50"]) &
        (out["ema_50"] > out["ema_200"]) &
        (out["ema_50"] > out["ema_50_prev"]) &
        (out["ema_200"] > out["ema_200_prev"])
    )
    out["trend_short"] = (
        (close < out["ema_50"]) &
        (out["ema_50"] < out["ema_200"]) &
        (out["ema_50"] < out["ema_50_prev"]) &
        (out["ema_200"] < out["ema_200_prev"])
    )
    return out


# ========================================================================== #
# Per-index signal computation
# ========================================================================== #

def compute_ko_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all signals needed for KO setup detection on one index."""
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    out = pd.DataFrame(index=df.index)

    out["close"] = close
    out["high"] = high
    out["low"] = low
    out["open"] = df["Open"]

    # Trend
    trend = compute_ko_trend(df)
    for col in trend.columns:
        out[col] = trend[col]

    # RSI
    out["rsi_14"] = rsi(close, config.KO_RSI_PERIOD)

    # ATR
    out["atr_14"] = atr(df, config.KO_ATR_PERIOD)

    # BB width for consolidation detection
    out["bb_width"] = bollinger_bandwidth(close, 20)
    out["bb_width_avg"] = out["bb_width"].rolling(50).mean()

    # Volume
    if "Volume" in df.columns:
        vol = df["Volume"]
        out["vol_20d"] = vol.rolling(20).mean()
        out["vol_ratio"] = vol / out["vol_20d"].replace(0, np.nan)
    else:
        out["vol_20d"] = np.nan
        out["vol_ratio"] = 1.0

    # Swing points (N-bar method)
    n = config.KO_SWING_BARS
    out["swing_low"] = _detect_swing_lows(low, n)
    out["swing_high"] = _detect_swing_highs(high, n)

    # Rolling range for consolidation detection
    out["range_high"] = rolling_high(high, config.KO_CONSOL_MIN_DAYS)
    out["range_low"] = rolling_low(low, config.KO_CONSOL_MIN_DAYS)

    # ATR contraction ratio
    atr_long = atr(df, config.KO_CONSOL_MIN_DAYS)
    out["atr_contraction"] = (1 - out["atr_14"] / atr_long.replace(0, np.nan)) * 100

    return out


def _detect_swing_lows(low: pd.Series, n: int) -> pd.Series:
    """True where low[i] < low of the N bars before and N bars after."""
    result = pd.Series(False, index=low.index)
    vals = low.values
    for i in range(n, len(vals) - n):
        window_before = vals[i - n:i]
        window_after = vals[i + 1:i + n + 1]
        if vals[i] < window_before.min() and vals[i] < window_after.min():
            result.iloc[i] = True
    return result


def _detect_swing_highs(high: pd.Series, n: int) -> pd.Series:
    """True where high[i] > high of the N bars before and N bars after."""
    result = pd.Series(False, index=high.index)
    vals = high.values
    for i in range(n, len(vals) - n):
        window_before = vals[i - n:i]
        window_after = vals[i + 1:i + n + 1]
        if vals[i] > window_before.max() and vals[i] > window_after.max():
            result.iloc[i] = True
    return result


# ========================================================================== #
# Setup A — Trend Pullback to EMA(50)
# ========================================================================== #

@dataclass
class SetupSignal:
    setup_type: str       # "A", "B", "C"
    direction: str        # "LONG" or "SHORT"
    date: str
    entry_price: float    # next-bar open
    stop_price: float
    target_price: float
    r_value: float        # |entry - stop|
    r_multiple: float     # target / r_value


def detect_setup_a(sig: pd.DataFrame, idx: int) -> Optional[SetupSignal]:
    """
    Trend Pullback to EMA(50).

    Long: price pulled back to EMA50, RSI < 40, then closed back above EMA50.
    Short: mirror.
    """
    if idx < config.KO_PULLBACK_LOOKBACK + 1 or idx >= len(sig) - 1:
        return None

    row = sig.iloc[idx]
    trend_long = bool(row.get("trend_long", False))
    trend_short = bool(row.get("trend_short", False))
    if not trend_long and not trend_short:
        return None

    close = row["close"]
    ema50 = row["ema_50"]
    atr_val = row["atr_14"]
    if pd.isna(ema50) or pd.isna(atr_val) or atr_val <= 0:
        return None

    lb = config.KO_PULLBACK_LOOKBACK

    if trend_long:
        # Check pullback sequence in the lookback window
        window = sig.iloc[idx - lb:idx + 1]
        rsi_dipped = (window["rsi_14"] < config.KO_RSI_OVERSOLD).any()
        touched_ema = (window["low"] <= window["ema_50"]).any()
        confirmed = close > ema50  # confirmation candle: back above EMA50

        if not (rsi_dipped and touched_ema and confirmed):
            return None

        pullback_low = float(window["low"].min())
        stop = pullback_low - config.KO_STOP_ATR_BUFFER * atr_val
        entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else close
        r_val = entry - stop
        if r_val <= 0:
            return None

        # Target: recent swing high above entry + measured move
        recent_highs = sig["high"].iloc[max(0, idx - 60):idx + 1]
        swing_target = float(recent_highs.max())
        target = swing_target + r_val  # measured move extension
        r_mult = (target - entry) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None

        return SetupSignal("A", "LONG", str(sig.index[idx].date()),
                           entry, stop, target, r_val, r_mult)

    if trend_short:
        window = sig.iloc[idx - lb:idx + 1]
        rsi_spiked = (window["rsi_14"] > config.KO_RSI_OVERBOUGHT).any()
        touched_ema = (window["high"] >= window["ema_50"]).any()
        confirmed = close < ema50

        if not (rsi_spiked and touched_ema and confirmed):
            return None

        pullback_high = float(window["high"].max())
        stop = pullback_high + config.KO_STOP_ATR_BUFFER * atr_val
        entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else close
        r_val = stop - entry
        if r_val <= 0:
            return None

        recent_lows = sig["low"].iloc[max(0, idx - 60):idx + 1]
        swing_target = float(recent_lows.min())
        target = swing_target - r_val
        r_mult = (entry - target) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None

        return SetupSignal("A", "SHORT", str(sig.index[idx].date()),
                           entry, stop, target, r_val, r_mult)

    return None


# ========================================================================== #
# Setup B — Consolidation Breakout
# ========================================================================== #

@dataclass
class PendingBreakout:
    index_name: str
    direction: str
    breakout_date: str
    breakout_level: float
    range_high: float
    range_low: float
    stop_price: float
    target_price: float
    r_value: float
    r_multiple: float
    days_waiting: int = 0


def detect_setup_b_breakout(sig: pd.DataFrame, idx: int) -> Optional[PendingBreakout]:
    """
    Detect a consolidation breakout (first step of Setup B).
    Returns a PendingBreakout that waits for retest confirmation.
    """
    if idx < config.KO_CONSOL_MAX_DAYS + 10 or idx >= len(sig) - 1:
        return None

    row = sig.iloc[idx]
    trend_long = bool(row.get("trend_long", False))
    trend_short = bool(row.get("trend_short", False))
    if not trend_long and not trend_short:
        return None

    atr_val = row["atr_14"]
    if pd.isna(atr_val) or atr_val <= 0:
        return None

    # Check ATR contraction
    contraction = row.get("atr_contraction", 0)
    if pd.isna(contraction) or contraction < config.KO_ATR_CONTRACTION_PCT:
        return None

    # Check BB squeeze
    bb_w = row.get("bb_width", np.nan)
    bb_avg = row.get("bb_width_avg", np.nan)
    if pd.isna(bb_w) or pd.isna(bb_avg) or bb_w >= bb_avg:
        return None

    # Check volume surge
    vol_ratio = row.get("vol_ratio", 0)
    if pd.isna(vol_ratio) or vol_ratio < config.KO_VOL_SURGE_MULT:
        return None

    # Compute consolidation range
    close = row["close"]
    consol_window = sig.iloc[idx - config.KO_CONSOL_MIN_DAYS:idx]
    rng_high = float(consol_window["high"].max())
    rng_low = float(consol_window["low"].min())
    rng_height = rng_high - rng_low

    if trend_long and close > rng_high:
        stop = rng_low - config.KO_STOP_ATR_BUFFER * atr_val
        entry_est = rng_high  # retest level = breakout level
        r_val = entry_est - stop
        if r_val <= 0:
            return None
        target = entry_est + rng_height
        r_mult = (target - entry_est) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None
        return PendingBreakout(
            "", "LONG", str(sig.index[idx].date()),
            rng_high, rng_high, rng_low,
            stop, target, r_val, r_mult,
        )

    if trend_short and close < rng_low:
        stop = rng_high + config.KO_STOP_ATR_BUFFER * atr_val
        entry_est = rng_low
        r_val = stop - entry_est
        if r_val <= 0:
            return None
        target = entry_est - rng_height
        r_mult = (entry_est - target) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None
        return PendingBreakout(
            "", "SHORT", str(sig.index[idx].date()),
            rng_low, rng_high, rng_low,
            stop, target, r_val, r_mult,
        )

    return None


def check_retest(pending: PendingBreakout, sig: pd.DataFrame, idx: int) -> Optional[SetupSignal]:
    """Check if a pending breakout gets retested at the breakout level."""
    row = sig.iloc[idx]
    tol = config.KO_RETEST_TOLERANCE_PCT / 100 * pending.breakout_level

    if pending.direction == "LONG":
        if row["low"] <= pending.breakout_level + tol and row["close"] > pending.breakout_level:
            entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else float(row["close"])
            r_val = entry - pending.stop_price
            if r_val <= 0:
                return None
            r_mult = (pending.target_price - entry) / r_val
            return SetupSignal("B", "LONG", str(sig.index[idx].date()),
                               entry, pending.stop_price, pending.target_price,
                               r_val, r_mult)
    else:
        if row["high"] >= pending.breakout_level - tol and row["close"] < pending.breakout_level:
            entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else float(row["close"])
            r_val = pending.stop_price - entry
            if r_val <= 0:
                return None
            r_mult = (entry - pending.target_price) / r_val
            return SetupSignal("B", "SHORT", str(sig.index[idx].date()),
                               entry, pending.stop_price, pending.target_price,
                               r_val, r_mult)
    return None


# ========================================================================== #
# Setup C — Higher-Low / Lower-High Continuation
# ========================================================================== #

def detect_setup_c(sig: pd.DataFrame, idx: int) -> Optional[SetupSignal]:
    """
    Higher-Low (long) or Lower-High (short) continuation.

    Identifies two consecutive swing lows where the second is higher than the
    first (or two swing highs with the second lower), plus a reversal candle
    confirmation.
    """
    if idx < config.KO_HL_LOOKBACK_DAYS or idx >= len(sig) - 1:
        return None

    row = sig.iloc[idx]
    trend_long = bool(row.get("trend_long", False))
    trend_short = bool(row.get("trend_short", False))
    if not trend_long and not trend_short:
        return None

    atr_val = row["atr_14"]
    if pd.isna(atr_val) or atr_val <= 0:
        return None

    lookback = config.KO_HL_LOOKBACK_DAYS
    window = sig.iloc[max(0, idx - lookback):idx + 1]

    if trend_long:
        # Find swing lows in the lookback
        swing_idx = window.index[window["swing_low"]]
        if len(swing_idx) < 2:
            return None

        last_two = swing_idx[-2:]
        sl1 = float(window.loc[last_two[0], "low"])
        sl2 = float(window.loc[last_two[1], "low"])
        if sl2 <= sl1:
            return None  # not a higher low
        ema50 = row["ema_50"]
        if pd.isna(ema50) or sl2 < ema50:
            return None  # higher low must be above EMA50

        # Reversal candle: close > open on the current bar
        if row["close"] <= row["open"]:
            return None

        # Entry: break of the minor high between the two swing lows
        between = window.loc[last_two[0]:last_two[1]]
        if between.empty:
            return None
        minor_high = float(between["high"].max())
        if row["close"] <= minor_high:
            return None  # hasn't broken the minor high yet

        entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else float(row["close"])
        stop = sl2 - config.KO_STOP_ATR_BUFFER * atr_val
        r_val = entry - stop
        if r_val <= 0:
            return None

        # Target: previous swing high + measured leg
        swing_high_idx = window.index[window["swing_high"]]
        if len(swing_high_idx) > 0:
            prev_swing_high = float(window.loc[swing_high_idx[-1], "high"])
        else:
            prev_swing_high = float(window["high"].max())
        leg = prev_swing_high - sl2
        target = prev_swing_high + 0.5 * leg
        r_mult = (target - entry) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None

        return SetupSignal("C", "LONG", str(sig.index[idx].date()),
                           entry, stop, target, r_val, r_mult)

    if trend_short:
        swing_idx = window.index[window["swing_high"]]
        if len(swing_idx) < 2:
            return None

        last_two = swing_idx[-2:]
        sh1 = float(window.loc[last_two[0], "high"])
        sh2 = float(window.loc[last_two[1], "high"])
        if sh2 >= sh1:
            return None  # not a lower high
        ema50 = row["ema_50"]
        if pd.isna(ema50) or sh2 > ema50:
            return None

        if row["close"] >= row["open"]:
            return None  # need bearish candle

        between = window.loc[last_two[0]:last_two[1]]
        if between.empty:
            return None
        minor_low = float(between["low"].min())
        if row["close"] >= minor_low:
            return None

        entry = float(sig.iloc[idx + 1]["open"]) if idx + 1 < len(sig) else float(row["close"])
        stop = sh2 + config.KO_STOP_ATR_BUFFER * atr_val
        r_val = stop - entry
        if r_val <= 0:
            return None

        swing_low_idx = window.index[window["swing_low"]]
        if len(swing_low_idx) > 0:
            prev_swing_low = float(window.loc[swing_low_idx[-1], "low"])
        else:
            prev_swing_low = float(window["low"].min())
        leg = sh2 - prev_swing_low
        target = prev_swing_low - 0.5 * leg
        r_mult = (entry - target) / r_val
        if r_mult < config.KO_MIN_RR_RATIO:
            return None

        return SetupSignal("C", "SHORT", str(sig.index[idx].date()),
                           entry, stop, target, r_val, r_mult)

    return None


# ========================================================================== #
# Combined scanner
# ========================================================================== #

def scan_setups(sig: pd.DataFrame, idx: int) -> list[SetupSignal]:
    """Scan for all 3 setups at a given bar. Returns triggered signals."""
    results = []
    for detector in [detect_setup_a, detect_setup_c]:
        s = detector(sig, idx)
        if s is not None:
            results.append(s)
    # Setup B handled separately via PendingBreakout state machine
    return results
