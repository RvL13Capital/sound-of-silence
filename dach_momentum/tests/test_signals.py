"""Tests for dach_momentum.signals."""
import math

import numpy as np
import pandas as pd
import pytest

from dach_momentum.signals import (
    sma,
    atr,
    compute_trend_template,
    compute_momentum_signals,
    rolling_high,
    rolling_low,
    bollinger_bandwidth,
)


# ========================================================================== #
# sma()
# ========================================================================== #


class TestSma:
    def test_simple_known_series(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sma(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(2.0)
        assert result.iloc[3] == pytest.approx(3.0)
        assert result.iloc[4] == pytest.approx(4.0)

    def test_window_equals_length(self):
        s = pd.Series([10.0, 20.0, 30.0])
        result = sma(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(20.0)

    def test_window_larger_than_length(self):
        s = pd.Series([1.0, 2.0])
        result = sma(s, window=5)
        assert all(math.isnan(v) for v in result)


# ========================================================================== #
# atr()
# ========================================================================== #


class TestAtr:
    def test_with_known_ohlc(self):
        """Build a 20-row OHLC DataFrame with constant ranges so ATR is predictable."""
        n = 20
        dates = pd.date_range("2020-01-01", periods=n, freq="B")
        # Prices climb steadily; High-Low always = 2
        closes = [100.0 + i for i in range(n)]
        highs = [c + 1.0 for c in closes]
        lows = [c - 1.0 for c in closes]
        opens = closes[:]

        df = pd.DataFrame(
            {"Open": opens, "High": highs, "Low": lows, "Close": closes},
            index=dates,
        )

        result = atr(df, window=14)
        # True Range should be 2.0 for every row (High-Low = 2, and the
        # previous-close based components are smaller because price moves by 1/day).
        # First row has no prev_close so |High - NaN| = NaN, but max ignores NaN.
        # For rows 1+, TR = max(2, |high - prev_close|, |low - prev_close|) = 2.
        # ATR(14) should therefore be 2.0 once we have 14 valid TR values.
        assert math.isnan(result.iloc[0])  # first TR is NaN-based
        # After 14 valid periods the ATR should stabilise at 2.0
        assert result.iloc[14] == pytest.approx(2.0, abs=0.01)
        assert result.iloc[-1] == pytest.approx(2.0, abs=0.01)


# ========================================================================== #
# compute_trend_template()
# ========================================================================== #


def _make_uptrend_df(n=400, start_price=50.0, daily_gain=0.002):
    """Create a synthetic stock in a clear uptrend (all MAs stacked correctly)."""
    dates = pd.date_range("2018-01-01", periods=n, freq="B")
    prices = [start_price * (1 + daily_gain) ** i for i in range(n)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.005 for p in prices],
            "Low": [p * 0.995 for p in prices],
            "Close": prices,
            "Volume": [100000] * n,
        },
        index=dates,
    )


def _make_downtrend_df(n=400, start_price=200.0, daily_loss=0.002):
    """Create a synthetic stock in a clear downtrend."""
    dates = pd.date_range("2018-01-01", periods=n, freq="B")
    prices = [start_price * (1 - daily_loss) ** i for i in range(n)]
    return pd.DataFrame(
        {
            "Open": prices,
            "High": [p * 1.005 for p in prices],
            "Low": [p * 0.995 for p in prices],
            "Close": prices,
            "Volume": [100000] * n,
        },
        index=dates,
    )


class TestComputeTrendTemplate:
    def test_uptrend_passes(self):
        df = _make_uptrend_df()
        result = compute_trend_template(df)
        # The last row should pass because all MAs are stacked correctly
        assert result["trend_template_pass"].iloc[-1] is True or result["trend_template_pass"].iloc[-1] == True

    def test_downtrend_fails(self):
        df = _make_downtrend_df()
        result = compute_trend_template(df)
        assert result["trend_template_pass"].iloc[-1] == False


# ========================================================================== #
# compute_momentum_signals()
# ========================================================================== #


class TestComputeMomentumSignals:
    def test_mom_12_1_known_values(self):
        """Price doubles over 252 days, then stays flat for 21 days.
        mom_12_1 = close_1m_ago / close_12m_ago - 1 = 2.0 / 1.0 - 1 = 1.0 (100%)
        """
        n = 300
        dates = pd.date_range("2018-01-01", periods=n, freq="B")
        prices = []
        for i in range(n):
            if i < 252:
                # linear ramp from 100 to 200
                prices.append(100.0 + (100.0 * i / 251))
            else:
                prices.append(200.0)

        df = pd.DataFrame(
            {
                "Open": prices,
                "High": prices,
                "Low": prices,
                "Close": prices,
            },
            index=dates,
        )

        result = compute_momentum_signals(df)
        # At index 273 (252 + 21), mom_12_1 should be defined
        # close_1m = close[273-21] = close[252] = 200
        # close_12m = close[273-252] = close[21] ~ 100 + 100*21/251
        # Let's just check the last row where we have enough data
        last_mom = result["mom_12_1"].dropna().iloc[-1]
        # Should be a large positive number (roughly 100% gain)
        assert last_mom > 0.5


# ========================================================================== #
# rolling_high() / rolling_low()
# ========================================================================== #


class TestRollingHighLow:
    def test_rolling_high(self):
        s = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0])
        result = rolling_high(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == 3.0
        assert result.iloc[3] == 5.0
        assert result.iloc[4] == 5.0

    def test_rolling_low(self):
        s = pd.Series([5.0, 3.0, 4.0, 1.0, 2.0])
        result = rolling_low(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == 3.0
        assert result.iloc[3] == 1.0
        assert result.iloc[4] == 1.0


# ========================================================================== #
# bollinger_bandwidth()
# ========================================================================== #


class TestBollingerBandwidth:
    def test_constant_series_zero_bandwidth(self):
        """A constant series has zero std, so bandwidth should be 0."""
        s = pd.Series([100.0] * 30)
        result = bollinger_bandwidth(s, window=20)
        assert result.iloc[-1] == pytest.approx(0.0)

    def test_volatile_series_positive_bandwidth(self):
        """An alternating series should produce positive bandwidth."""
        s = pd.Series([100.0 + ((-1) ** i) * 5.0 for i in range(30)])
        result = bollinger_bandwidth(s, window=20)
        last_val = result.iloc[-1]
        assert last_val > 0
