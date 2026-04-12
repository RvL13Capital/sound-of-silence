"""Tests for dach_momentum.positions."""
import pytest

from dach_momentum.positions import (
    calculate_stop_price,
    calculate_position_size,
    evaluate_exits,
    Position,
)


# ========================================================================== #
# calculate_stop_price()
# ========================================================================== #


class TestCalculateStopPrice:
    def test_no_atr_uses_10_pct(self):
        """entry=100, no ATR -> stop at 90 (10% below)."""
        stop = calculate_stop_price(100.0, atr=None)
        assert stop == pytest.approx(90.0)

    def test_atr_narrower_than_10_pct_uses_10_pct(self):
        """entry=100, ATR=3 -> 2.5*3=7.5 -> atr_stop=92.5.
        pct_stop=90.  wider stop = min(90, 92.5) = 90.
        floor = 85.  max(90, 85) = 90.
        """
        stop = calculate_stop_price(100.0, atr=3.0)
        assert stop == pytest.approx(90.0)

    def test_atr_wider_but_within_ceiling(self):
        """entry=100, ATR=5 -> 2.5*5=12.5 -> atr_stop=87.5.
        pct_stop=90.  wider stop = min(90, 87.5) = 87.5.
        floor = 85.  max(87.5, 85) = 87.5.
        """
        stop = calculate_stop_price(100.0, atr=5.0)
        assert stop == pytest.approx(87.5)

    def test_atr_exceeds_ceiling_capped(self):
        """entry=100, ATR=7 -> 2.5*7=17.5 -> atr_stop=82.5.
        pct_stop=90.  wider stop = min(90, 82.5) = 82.5.
        floor = 85.  max(82.5, 85) = 85.
        """
        stop = calculate_stop_price(100.0, atr=7.0)
        assert stop == pytest.approx(85.0)


# ========================================================================== #
# calculate_position_size()
# ========================================================================== #


class TestCalculatePositionSize:
    def test_basic_sizing(self):
        """equity=20000, entry=100, stop=90 -> risk_per_share=10,
        max_risk=200 (1% of 20k), shares=20.
        """
        shares = calculate_position_size(
            equity=20000.0,
            entry_price=100.0,
            stop_price=90.0,
        )
        assert shares == 20

    def test_zero_risk_returns_zero(self):
        shares = calculate_position_size(
            equity=20000.0,
            entry_price=100.0,
            stop_price=100.0,
        )
        assert shares == 0

    def test_weight_cap_binding(self):
        """If equity is small and stop is very tight, the 12% weight cap
        should limit the position."""
        # equity=10000, entry=100, stop=99 -> risk/share=1, risk-based=100 shares
        # 12% weight cap = 1200/100 = 12 shares
        shares = calculate_position_size(
            equity=10000.0,
            entry_price=100.0,
            stop_price=99.0,
        )
        assert shares == 12  # min(100, 12, very_large) = 12


# ========================================================================== #
# evaluate_exits()
# ========================================================================== #


class TestEvaluateExits:
    def _make_position(self, entry_price=100.0, stop_price=90.0):
        return Position(
            ticker="TEST.DE",
            entry_date="2023-01-01",
            entry_price=entry_price,
            shares=10,
            stop_price=stop_price,
            risk_per_share=entry_price - stop_price,
        )

    def test_hard_stop_trigger(self):
        pos = self._make_position(entry_price=100.0, stop_price=90.0)
        result = evaluate_exits(
            position=pos,
            current_price=89.0,
            sma_30w=95.0,
            sma_10w=95.0,
            regime_on=True,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "HARD_STOP"
        assert result["urgency"] == "immediate"

    def test_regime_off_below_10w_sma(self):
        pos = self._make_position(entry_price=100.0, stop_price=90.0)
        result = evaluate_exits(
            position=pos,
            current_price=94.0,
            sma_30w=90.0,  # above 30w so that exit is not BELOW_30W_SMA
            sma_10w=95.0,  # price (94) < sma_10w (95)
            regime_on=False,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "REGIME_OFF_BELOW_10W"
        assert result["urgency"] == "within_3_days"

    def test_below_30w_sma(self):
        pos = self._make_position(entry_price=100.0, stop_price=90.0)
        result = evaluate_exits(
            position=pos,
            current_price=94.0,
            sma_30w=95.0,  # price (94) < sma_30w (95)
            sma_10w=93.0,  # above 10w so regime-off exit doesn't fire
            regime_on=True,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "BELOW_30W_SMA"
        assert result["urgency"] == "end_of_week"

    def test_no_exit_when_above_all_smas(self):
        pos = self._make_position(entry_price=100.0, stop_price=90.0)
        result = evaluate_exits(
            position=pos,
            current_price=105.0,
            sma_30w=100.0,
            sma_10w=102.0,
            regime_on=True,
        )
        assert result["exit_triggered"] is False
        assert result["reason"] == ""

    def test_trailing_active_after_20pct_gain(self):
        pos = self._make_position(entry_price=100.0, stop_price=90.0)
        # Price has risen 25% -- should activate trailing
        evaluate_exits(
            position=pos,
            current_price=125.0,
            sma_30w=120.0,
            sma_10w=122.0,
            regime_on=True,
        )
        assert pos.trailing_active is True
