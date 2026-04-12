"""Tests for run_backtest: compute_stock_signals and compute_performance."""
import sys
import os

# Ensure project root is on sys.path so run_backtest can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import pytest

from run_backtest import compute_stock_signals, compute_performance, BacktestState, Trade


# ========================================================================== #
# compute_stock_signals()
# ========================================================================== #


def _make_synthetic_ohlcv(n=500, start_price=100.0, seed=42):
    """Deterministic synthetic OHLCV data (random-walk-like but seeded)."""
    rng = np.random.RandomState(seed)
    dates = pd.date_range("2017-01-01", periods=n, freq="B")
    log_returns = rng.normal(0.0003, 0.015, size=n)
    log_returns[0] = 0.0
    prices = start_price * np.exp(np.cumsum(log_returns))

    df = pd.DataFrame(
        {
            "Open": prices * (1 + rng.uniform(-0.005, 0.005, n)),
            "High": prices * (1 + rng.uniform(0.001, 0.02, n)),
            "Low": prices * (1 - rng.uniform(0.001, 0.02, n)),
            "Close": prices,
            "Volume": rng.randint(50000, 500000, size=n).astype(float),
        },
        index=dates,
    )
    return df


class TestComputeStockSignals:
    def test_returns_all_expected_columns(self):
        df = _make_synthetic_ohlcv()
        result = compute_stock_signals(df)

        expected_cols = [
            "close",
            "sma_50",
            "sma_150",
            "sma_200",
            "high_52w",
            "low_52w",
            "tt_pass",
            "mom_12_1",
            "atr_14",
            "sma_30w",
            "sma_10w",
            "bb_width",
            "quality_score",
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_no_error_on_short_data(self):
        """Even with only 252 rows (minimum for backtest), should not raise."""
        df = _make_synthetic_ohlcv(n=260)
        result = compute_stock_signals(df)
        assert len(result) == 260

    def test_tt_pass_is_boolean(self):
        df = _make_synthetic_ohlcv()
        result = compute_stock_signals(df)
        assert result["tt_pass"].dtype == bool


# ========================================================================== #
# compute_performance()
# ========================================================================== #


class TestComputePerformance:
    def _make_state_with_equity_curve(
        self,
        initial=10000.0,
        final=15000.0,
        n_weeks=104,
    ):
        """Build a BacktestState with a linearly growing equity curve."""
        dates = pd.date_range("2020-01-03", periods=n_weeks, freq="W-FRI")
        equities = np.linspace(initial, final, n_weeks)

        state = BacktestState(cash=final)
        state.equity_curve = [
            {
                "date": d,
                "equity": eq,
                "cash": eq,
                "positions": 0,
                "regime_on": True,
            }
            for d, eq in zip(dates, equities)
        ]

        # Add some closed trades so win/loss stats work
        state.closed_trades = [
            Trade(
                ticker="A.DE",
                entry_date="2020-01-10",
                entry_price=100.0,
                shares=10,
                stop_price=90.0,
                exit_date="2020-03-10",
                exit_price=120.0,
                exit_reason="BELOW_30W_SMA",
                pnl=190.0,
                pnl_pct=20.0,
                holding_days=60,
            ),
            Trade(
                ticker="B.DE",
                entry_date="2020-02-01",
                entry_price=50.0,
                shares=20,
                stop_price=45.0,
                exit_date="2020-04-01",
                exit_price=45.0,
                exit_reason="HARD_STOP",
                pnl=-120.0,
                pnl_pct=-10.0,
                holding_days=59,
            ),
        ]
        return state

    def test_cagr_positive_for_growing_equity(self):
        state = self._make_state_with_equity_curve(
            initial=10000.0, final=15000.0, n_weeks=104,
        )
        perf = compute_performance(state)
        assert perf["cagr_pct"] > 0

    def test_cagr_approximate_value(self):
        """10000 -> 15000 over ~2 years => CAGR ~ 22.5%"""
        state = self._make_state_with_equity_curve(
            initial=10000.0, final=15000.0, n_weeks=104,
        )
        perf = compute_performance(state)
        assert 15 < perf["cagr_pct"] < 30

    def test_max_drawdown_for_monotonic_curve(self):
        """A monotonically increasing equity curve has zero drawdown."""
        state = self._make_state_with_equity_curve(
            initial=10000.0, final=15000.0, n_weeks=104,
        )
        perf = compute_performance(state)
        # The linearly growing curve is monotonic, so max DD should be ~0
        assert perf["max_drawdown_pct"] >= -1.0  # allow tiny floating-point noise

    def test_sharpe_positive(self):
        state = self._make_state_with_equity_curve(
            initial=10000.0, final=15000.0, n_weeks=104,
        )
        perf = compute_performance(state)
        assert perf["sharpe_ratio"] > 0

    def test_win_rate_50_pct(self):
        """Two trades: one winner, one loser -> 50% win rate."""
        state = self._make_state_with_equity_curve()
        perf = compute_performance(state)
        assert perf["win_rate_pct"] == pytest.approx(50.0)

    def test_profit_factor(self):
        """Winners: 190, Losers: 120 -> PF = 190/120 ~ 1.58"""
        state = self._make_state_with_equity_curve()
        perf = compute_performance(state)
        assert perf["profit_factor"] == pytest.approx(190.0 / 120.0, rel=0.01)

    def test_total_trades(self):
        state = self._make_state_with_equity_curve()
        perf = compute_performance(state)
        assert perf["total_trades"] == 2
