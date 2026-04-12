"""Tests for dach_momentum.signals signal computation functions."""
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

class TestSMA:
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

    def test_window_larger_than_series(self):
        s = pd.Series([1.0, 2.0])
        result = sma(s, window=5)
        assert all(math.isnan(v) for v in result)

    def test_constant_series(self):
        s = pd.Series([5.0] * 10)
        result = sma(s, window=3)
        # After warm-up, all values should be 5.0
        for i in range(2, 10):
            assert result.iloc[i] == pytest.approx(5.0)


# ========================================================================== #
# atr()
# ========================================================================== #

class TestATR:
    def test_known_ohlc(self):
        """ATR with known constant-range bars."""
        n = 20
        df = pd.DataFrame({
            "Open": [100.0] * n,
            "High": [105.0] * n,
            "Low": [95.0] * n,
            "Close": [100.0] * n,
        })
        result = atr(df, window=14)
        # True range each bar: max(105-95, |105-100|, |95-100|) = 10
        # (prev_close is NaN for bar 0, so bar 0 TR = high - low = 10)
        # ATR(14) = mean of 14 TRs of 10 = 10
        # First 13 values should be NaN (min_periods=14)
        for i in range(13):
            assert math.isnan(result.iloc[i])
        # After 14 bars the rolling mean kicks in
        assert result.iloc[14] == pytest.approx(10.0)
        assert result.iloc[19] == pytest.approx(10.0)

    def test_atr_with_gaps(self):
        """ATR should capture gap moves via prev_close."""
        data = {
            "Open": [100, 110, 120],
            "High": [105, 115, 125],
            "Low":  [95, 105, 115],
            "Close": [100, 110, 120],
        }
        df = pd.DataFrame(data, dtype=float)
        result = atr(df, window=2)
        # Bar 0: TR = max(10, NaN, NaN) = 10 (prev_close NaN)
        # Bar 1: TR = max(115-105, |115-100|, |105-100|) = max(10, 15, 5) = 15
        # Bar 2: TR = max(125-115, |125-110|, |115-110|) = max(10, 15, 5) = 15
        # ATR(2) at bar 2 = mean(15, 15) = 15
        assert result.iloc[2] == pytest.approx(15.0)


# ========================================================================== #
# compute_trend_template()
# ========================================================================== #

class TestComputeTrendTemplate:
    @staticmethod
    def _make_uptrend_df(n=300):
        """Create a synthetic stock in a clear uptrend.

        Price rises steadily so all MAs stack correctly:
        price > sma50 > sma150 > sma200, and 200d SMA is rising.
        """
        # Start at 50, rise to ~200 over 300 days
        close = pd.Series(
            [50 + i * 0.5 for i in range(n)],
            index=pd.bdate_range("2020-01-01", periods=n),
        )
        df = pd.DataFrame({
            "Open": close - 0.1,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": [1000000] * n,
        })
        return df

    @staticmethod
    def _make_downtrend_df(n=300):
        """Create a synthetic stock in a clear downtrend."""
        close = pd.Series(
            [200 - i * 0.5 for i in range(n)],
            index=pd.bdate_range("2020-01-01", periods=n),
        )
        df = pd.DataFrame({
            "Open": close + 0.1,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": [1000000] * n,
        })
        return df

    def test_uptrend_passes(self):
        df = self._make_uptrend_df()
        result = compute_trend_template(df)
        # The last row should pass the trend template
        assert bool(result["trend_template_pass"].iloc[-1]) is True

    def test_downtrend_fails(self):
        df = self._make_downtrend_df()
        result = compute_trend_template(df)
        # The last row should fail the trend template
        assert bool(result["trend_template_pass"].iloc[-1]) is False

    def test_has_all_columns(self):
        df = self._make_uptrend_df()
        result = compute_trend_template(df)
        expected_cols = [
            "tt1_price_above_150", "tt2_price_above_200",
            "tt3_150_above_200", "tt4_200_trending_up",
            "tt5_50_above_150", "tt6_price_above_50",
            "tt7_above_52w_low", "tt8_near_52w_high",
            "trend_template_pass",
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"


# ========================================================================== #
# compute_momentum_signals()
# ========================================================================== #

class TestComputeMomentumSignals:
    def test_mom_12_1_known_prices(self):
        """mom_12_1 = close_1m_ago / close_12m_ago - 1."""
        n = 300
        # Price starts at 100 and increases by 1 each day
        close = pd.Series(
            [100.0 + i for i in range(n)],
            index=pd.bdate_range("2020-01-01", periods=n),
        )
        df = pd.DataFrame({"Close": close})
        result = compute_momentum_signals(df)

        # At the last row (index n-1 = 299):
        # close_12m = close.shift(252) = close[299-252] = close[47] = 147
        # close_1m = close.shift(21)  = close[299-21]  = close[278] = 378
        # mom_12_1 = 378 / 147 - 1
        expected = 378.0 / 147.0 - 1.0
        assert result["mom_12_1"].iloc[-1] == pytest.approx(expected, rel=1e-6)

    def test_has_all_columns(self):
        n = 300
        close = pd.Series(
            [100.0 + i * 0.1 for i in range(n)],
            index=pd.bdate_range("2020-01-01", periods=n),
        )
        df = pd.DataFrame({"Close": close})
        result = compute_momentum_signals(df)
        for col in ["mom_12_1", "mom_6_1", "mom_3_0",
                     "pct_from_52w_high", "pct_from_52w_low"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_early_values_are_nan(self):
        """Before enough history accumulates, values should be NaN."""
        n = 50  # not enough for 252-day lookback
        close = pd.Series(
            [100.0 + i for i in range(n)],
            index=pd.bdate_range("2020-01-01", periods=n),
        )
        df = pd.DataFrame({"Close": close})
        result = compute_momentum_signals(df)
        assert pd.isna(result["mom_12_1"].iloc[-1])


# ========================================================================== #
# rolling_high() and rolling_low()
# ========================================================================== #

class TestRollingHighLow:
    def test_rolling_high(self):
        s = pd.Series([1.0, 5.0, 3.0, 2.0, 4.0])
        result = rolling_high(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(5.0)  # max(1,5,3)
        assert result.iloc[3] == pytest.approx(5.0)  # max(5,3,2)
        assert result.iloc[4] == pytest.approx(4.0)  # max(3,2,4)

    def test_rolling_low(self):
        s = pd.Series([5.0, 1.0, 3.0, 4.0, 2.0])
        result = rolling_low(s, window=3)
        assert math.isnan(result.iloc[0])
        assert math.isnan(result.iloc[1])
        assert result.iloc[2] == pytest.approx(1.0)  # min(5,1,3)
        assert result.iloc[3] == pytest.approx(1.0)  # min(1,3,4)
        assert result.iloc[4] == pytest.approx(2.0)  # min(3,4,2)

    def test_monotone_increasing(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        high = rolling_high(s, window=3)
        low = rolling_low(s, window=3)
        # For monotone increasing, rolling high = last value
        assert high.iloc[4] == pytest.approx(5.0)
        assert high.iloc[3] == pytest.approx(4.0)
        # rolling low = first in window
        assert low.iloc[4] == pytest.approx(3.0)
        assert low.iloc[3] == pytest.approx(2.0)


# ========================================================================== #
# bollinger_bandwidth()
# ========================================================================== #

class TestBollingerBandwidth:
    def test_constant_series_zero_bandwidth(self):
        """Constant prices should have zero (or near-zero) bandwidth."""
        s = pd.Series([100.0] * 30)
        result = bollinger_bandwidth(s, window=20)
        # std = 0, so bandwidth = 0
        assert result.iloc[-1] == pytest.approx(0.0)

    def test_volatile_series_positive_bandwidth(self):
        """Alternating prices should produce positive bandwidth."""
        s = pd.Series([100.0, 110.0] * 15)
        result = bollinger_bandwidth(s, window=20)
        assert result.iloc[-1] > 0

    def test_returns_series_of_same_length(self):
        s = pd.Series([100.0 + i for i in range(30)])
        result = bollinger_bandwidth(s, window=20)
        assert len(result) == len(s)

    def test_nan_before_window(self):
        s = pd.Series([100.0 + i for i in range(30)])
        result = bollinger_bandwidth(s, window=20)
        # First 19 values should be NaN
        for i in range(19):
            assert pd.isna(result.iloc[i])
        # From index 19 onward should be valid
        assert not pd.isna(result.iloc[19])
