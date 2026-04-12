"""Tests for position sizing, stop-loss calculation, and exit logic."""
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
    def test_no_atr_10pct_stop(self):
        """No ATR provided -> stop at 10% below entry."""
        stop = calculate_stop_price(entry_price=100.0, atr=None)
        assert stop == pytest.approx(90.0)

    def test_atr_narrower_than_10pct(self):
        """ATR=3 -> 2.5*3=7.5 stop distance, but 10% = 10 is wider.
        min(90, 92.5) = 90 (wider), max(90, 85) = 90 (above floor).
        """
        stop = calculate_stop_price(entry_price=100.0, atr=3.0)
        assert stop == pytest.approx(90.0)

    def test_atr_wider_than_10pct_below_ceiling(self):
        """ATR=5 -> 2.5*5=12.5 stop distance.
        pct_stop = 90, atr_stop = 87.5, floor = 85.
        wider_stop = min(90, 87.5) = 87.5.
        stop = max(87.5, 85) = 87.5.
        """
        stop = calculate_stop_price(entry_price=100.0, atr=5.0)
        assert stop == pytest.approx(87.5)

    def test_atr_exceeds_ceiling_capped_at_15pct(self):
        """ATR=7 -> 2.5*7=17.5 stop distance.
        pct_stop = 90, atr_stop = 82.5, floor = 85.
        wider_stop = min(90, 82.5) = 82.5.
        stop = max(82.5, 85) = 85 (capped at 15%).
        """
        stop = calculate_stop_price(entry_price=100.0, atr=7.0)
        assert stop == pytest.approx(85.0)

    def test_zero_atr_treated_as_no_atr(self):
        """ATR=0 should behave like no ATR."""
        stop = calculate_stop_price(entry_price=100.0, atr=0.0)
        assert stop == pytest.approx(90.0)

    def test_result_is_rounded(self):
        """Stop price should be rounded to 4 decimal places."""
        stop = calculate_stop_price(entry_price=99.99, atr=None)
        # 99.99 * 0.9 = 89.991
        assert stop == pytest.approx(89.991, abs=1e-4)


# ========================================================================== #
# calculate_position_size()
# ========================================================================== #

class TestCalculatePositionSize:
    def test_basic_sizing(self):
        """equity=20000, entry=100, stop=90 -> risk_per_share=10,
        max_risk=200 (1% of 20000), shares=200/10=20."""
        shares = calculate_position_size(
            equity=20000.0,
            entry_price=100.0,
            stop_price=90.0,
        )
        assert shares == 20

    def test_zero_risk_per_share(self):
        """If stop >= entry, return 0 shares."""
        shares = calculate_position_size(
            equity=20000.0,
            entry_price=100.0,
            stop_price=100.0,
        )
        assert shares == 0

    def test_capped_by_max_position_weight(self):
        """With very tight stop (high risk shares), position weight cap kicks in.
        equity=10000, entry=100, stop=99.5 -> risk_per_share=0.5.
        shares_by_risk = 100 / 0.5 = 200 (value = 20000 > 12% of 10000).
        shares_by_weight = 1200 / 100 = 12.
        Result capped at 12.
        """
        shares = calculate_position_size(
            equity=10000.0,
            entry_price=100.0,
            stop_price=99.5,
        )
        # shares_by_risk = int(100 / 0.5) = 200
        # shares_by_weight = int(1200 / 100) = 12
        # shares_by_adv with default 1e9 is huge
        assert shares == 12

    def test_negative_risk_returns_zero(self):
        shares = calculate_position_size(
            equity=20000.0,
            entry_price=100.0,
            stop_price=110.0,  # stop above entry
        )
        assert shares == 0


# ========================================================================== #
# evaluate_exits()
# ========================================================================== #

class TestEvaluateExits:
    @staticmethod
    def _make_position(**kwargs):
        defaults = dict(
            ticker="TEST.DE",
            entry_date="2023-01-01",
            entry_price=100.0,
            shares=20,
            stop_price=90.0,
            risk_per_share=10.0,
        )
        defaults.update(kwargs)
        return Position(**defaults)

    def test_hard_stop_trigger(self):
        pos = self._make_position()
        result = evaluate_exits(
            position=pos,
            current_price=89.0,
            sma_30w=95.0,
            sma_10w=97.0,
            regime_on=True,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "HARD_STOP"
        assert result["urgency"] == "immediate"

    def test_regime_off_below_10w_sma(self):
        pos = self._make_position()
        result = evaluate_exits(
            position=pos,
            current_price=95.0,  # above stop (90) but below 10w SMA
            sma_30w=110.0,       # above 30w too (we test 10w first)
            sma_10w=98.0,
            regime_on=False,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "REGIME_OFF_BELOW_10W"
        assert result["urgency"] == "within_3_days"

    def test_below_30w_sma_trigger(self):
        pos = self._make_position()
        result = evaluate_exits(
            position=pos,
            current_price=94.0,  # above stop (90), above 10w, but below 30w
            sma_30w=96.0,
            sma_10w=93.0,        # price is above 10w, so exit 2 doesn't fire
            regime_on=True,       # regime on, so exit 2 doesn't apply
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "BELOW_30W_SMA"

    def test_no_exit_above_all_smas(self):
        pos = self._make_position()
        result = evaluate_exits(
            position=pos,
            current_price=105.0,
            sma_30w=95.0,
            sma_10w=100.0,
            regime_on=True,
        )
        assert result["exit_triggered"] is False
        assert result["reason"] == ""

    def test_trailing_activation_at_20pct_gain(self):
        pos = self._make_position()
        # Price at +20% from entry (100 -> 120)
        evaluate_exits(
            position=pos,
            current_price=120.01,  # slightly above +20% to avoid float rounding
            sma_30w=110.0,
            sma_10w=115.0,
            regime_on=True,
        )
        assert pos.trailing_active is True

    def test_highest_price_tracking(self):
        pos = self._make_position()
        assert pos.highest_since_entry == 100.0
        evaluate_exits(
            position=pos,
            current_price=115.0,
            sma_30w=100.0,
            sma_10w=105.0,
            regime_on=True,
        )
        assert pos.highest_since_entry == 115.0

    def test_hard_stop_takes_priority_over_regime_exit(self):
        """When price is below both hard stop and 10w SMA with regime off,
        the hard stop should fire first."""
        pos = self._make_position()
        result = evaluate_exits(
            position=pos,
            current_price=85.0,
            sma_30w=95.0,
            sma_10w=97.0,
            regime_on=False,
        )
        assert result["exit_triggered"] is True
        assert result["reason"] == "HARD_STOP"
