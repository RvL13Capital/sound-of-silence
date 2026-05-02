"""Tests for backtest engine: signal computation and performance analytics."""
import numpy as np
import pandas as pd
import pytest

import sys
sys.path.insert(0, "/home/user/sound-of-silence/dach_momentum")

from run_backtest import compute_stock_signals, compute_performance, BacktestState, Trade


# ========================================================================== #
# compute_stock_signals()
# ========================================================================== #

class TestComputeStockSignals:
    @staticmethod
    def _make_synthetic_df(n=500, seed=42):
        """Create a realistic synthetic OHLCV DataFrame.

        Uses a deterministic random walk so results are reproducible.
        """
        rng = np.random.RandomState(seed)
        dates = pd.bdate_range("2018-01-01", periods=n)

        # Random walk for close prices starting at 100
        log_returns = rng.normal(0.0003, 0.015, size=n)
        close = 100 * np.exp(np.cumsum(log_returns))

        # Construct OHLC from close
        high = close * (1 + rng.uniform(0, 0.02, size=n))
        low = close * (1 - rng.uniform(0, 0.02, size=n))
        open_ = close * (1 + rng.normal(0, 0.005, size=n))
        volume = rng.randint(100000, 1000000, size=n).astype(float)

        df = pd.DataFrame({
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }, index=dates)
        return df

    def test_returns_expected_columns(self):
        df = self._make_synthetic_df()
        signals = compute_stock_signals(df)
        expected_cols = [
            "close", "sma_50", "sma_150", "sma_200", "sma_200_1m",
            "high_52w", "low_52w", "tt_pass", "mom_12_1",
            "atr_14", "sma_30w", "sma_10w",
        ]
        for col in expected_cols:
            assert col in signals.columns, f"Missing column: {col}"

    def test_no_errors_with_volume(self):
        """Verify that volume-dependent columns are computed."""
        df = self._make_synthetic_df()
        signals = compute_stock_signals(df)
        assert "vol_50d" in signals.columns
        assert "vol_10d" in signals.columns
        assert "up_down_vol_ratio" in signals.columns
        assert "accumulation" in signals.columns

    def test_quality_score_range(self):
        """Quality score should be between 0 and 5."""
        df = self._make_synthetic_df()
        signals = compute_stock_signals(df)
        valid = signals["quality_score"].dropna()
        assert valid.min() >= 0
        assert valid.max() <= 5

    def test_index_preserved(self):
        df = self._make_synthetic_df()
        signals = compute_stock_signals(df)
        assert len(signals) == len(df)
        assert (signals.index == df.index).all()

    def test_tt_pass_is_boolean(self):
        df = self._make_synthetic_df()
        signals = compute_stock_signals(df)
        # tt_pass should contain only True/False (possibly with NaN)
        valid = signals["tt_pass"].dropna()
        assert set(valid.unique()).issubset({True, False})


# ========================================================================== #
# compute_performance()
# ========================================================================== #

class TestComputePerformance:
    @staticmethod
    def _make_state_with_known_equity():
        """Build a BacktestState with a known equity curve.

        Equity grows from 20000 to 30000 over 104 weeks (~2 years)
        with one drawdown episode.
        """
        state = BacktestState(cash=20000.0)

        dates = pd.date_range("2020-01-03", periods=104, freq="W-FRI")
        equity_values = []

        # Phase 1 (weeks 0-51): grow from 20000 to 26000
        for i in range(52):
            equity_values.append(20000 + i * (6000 / 52))

        # Phase 2 (weeks 52-61): drawdown from 26000 to 22000
        for i in range(10):
            equity_values.append(26000 - i * (4000 / 10))

        # Phase 3 (weeks 62-103): recover from 22000 to 30000
        for i in range(42):
            equity_values.append(22000 + i * (8000 / 42))

        for date, eq in zip(dates, equity_values):
            state.equity_curve.append({
                "date": date,
                "equity": eq,
                "cash": eq * 0.3,
                "positions": 5,
                "regime_on": True,
            })

        # Add some closed trades for trade statistics
        state.closed_trades = [
            Trade(ticker="A.DE", entry_date="2020-01-10",
                  entry_price=50.0, shares=10, stop_price=45.0,
                  exit_date="2020-06-10", exit_price=60.0,
                  exit_reason="BELOW_30W_SMA",
                  pnl=80.0, pnl_pct=20.0, holding_days=152),
            Trade(ticker="B.DE", entry_date="2020-03-01",
                  entry_price=100.0, shares=5, stop_price=90.0,
                  exit_date="2020-09-01", exit_price=90.0,
                  exit_reason="HARD_STOP",
                  pnl=-70.0, pnl_pct=-10.0, holding_days=184),
            Trade(ticker="C.DE", entry_date="2020-07-01",
                  entry_price=30.0, shares=20, stop_price=27.0,
                  exit_date="2021-01-01", exit_price=40.0,
                  exit_reason="REGIME_OFF_10W",
                  pnl=180.0, pnl_pct=33.3, holding_days=184),
        ]

        return state

    def test_cagr_positive(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        # Equity went from 20000 to ~30000, CAGR should be positive
        assert perf["cagr_pct"] > 0

    def test_cagr_approximately_correct(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        # ~2 years, 20000 -> ~30000 => CAGR ~ 22% (sqrt(1.5)-1 ~ 22.5%)
        assert 15 < perf["cagr_pct"] < 35

    def test_max_drawdown_negative(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        assert perf["max_drawdown_pct"] < 0

    def test_max_drawdown_magnitude(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        # Drawdown from 26000 to ~22000 = ~15.4%
        assert -20 < perf["max_drawdown_pct"] < -10

    def test_sharpe_positive(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        assert perf["sharpe_ratio"] > 0

    def test_trade_stats(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        assert perf["total_trades"] == 3
        assert perf["winners"] == 2
        assert perf["losers"] == 1
        assert 60 < perf["win_rate_pct"] < 70  # 2/3 = 66.7%

    def test_profit_factor(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        # winners pnl = 80 + 180 = 260; losers pnl = 70
        # profit_factor = 260 / 70 ~ 3.71
        assert perf["profit_factor"] == pytest.approx(260.0 / 70.0, rel=0.01)

    def test_exit_reasons_counted(self):
        state = self._make_state_with_known_equity()
        perf = compute_performance(state)
        assert perf["exit_reasons"]["HARD_STOP"] == 1
        assert perf["exit_reasons"]["BELOW_30W_SMA"] == 1
        assert perf["exit_reasons"]["REGIME_OFF_10W"] == 1

    def test_empty_state(self):
        state = BacktestState(cash=20000.0)
        perf = compute_performance(state)
        assert perf == {}
