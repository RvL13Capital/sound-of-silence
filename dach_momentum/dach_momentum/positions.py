"""
Position management and exit logic.

Tracks open positions, applies the tiered exit rules based on
regime status, and generates exit signals with specific reasons.

Exit hierarchy:
1. Hard stop (10% or 2.5x ATR from entry) — ALWAYS applies
2. Regime OFF + below 10-week SMA — exit within 3 days
3. Weekly close below 30-week SMA — primary trend exit
4. Profit threshold (+20%) reached — switch to MA-only exit
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from . import config

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position with entry details and tracking state."""
    ticker: str
    entry_date: str
    entry_price: float
    shares: int
    stop_price: float
    risk_per_share: float
    trailing_active: bool = False    # True once +20% reached
    highest_since_entry: float = 0.0
    status: str = "OPEN"             # OPEN, EXIT_TRIGGERED, CLOSED
    exit_reason: str = ""
    exit_date: str = ""
    exit_price: float = 0.0

    def __post_init__(self):
        if self.highest_since_entry == 0:
            self.highest_since_entry = self.entry_price


@dataclass
class PortfolioState:
    """Tracks all positions and portfolio-level metrics."""
    positions: list[Position] = field(default_factory=list)
    cash: float = 20000.0
    initial_equity: float = 20000.0
    trade_log: list[dict] = field(default_factory=list)

    @property
    def open_positions(self) -> list[Position]:
        return [p for p in self.positions if p.status == "OPEN"]

    @property
    def position_count(self) -> int:
        return len(self.open_positions)

    @property
    def total_equity(self) -> float:
        return self.cash + sum(
            p.shares * p.entry_price for p in self.open_positions
        )


def calculate_stop_price(
    entry_price: float,
    atr: Optional[float] = None,
) -> float:
    """
    Calculate initial hard stop: max(10%, 2.5 * ATR), capped at 15%.
    """
    pct_stop = entry_price * (1 - config.INITIAL_HARD_STOP_PCT / 100)

    if atr and atr > 0:
        atr_stop = entry_price - config.INITIAL_HARD_STOP_ATR_MULT * atr
        # Use the WIDER stop (more room), but cap at 15%
        floor = entry_price * (1 - config.HARD_STOP_CEILING_PCT / 100)
        stop = max(min(pct_stop, atr_stop), floor)
    else:
        stop = pct_stop

    return round(stop, 4)


def calculate_position_size(
    equity: float,
    entry_price: float,
    stop_price: float,
    avg_daily_volume_eur: float = 1e9,
) -> int:
    """
    Calculate position size based on risk-per-trade and constraints.

    Risk: 1% of portfolio equity per trade.
    Constraints: max 12% of equity, max 5% of ADV.
    """
    risk_per_share = entry_price - stop_price
    if risk_per_share <= 0:
        return 0

    # Risk-based sizing
    max_risk = equity * (config.RISK_PER_TRADE_PCT / 100)
    shares_by_risk = int(max_risk / risk_per_share)

    # Max position weight
    max_position_value = equity * (config.MAX_POSITION_PCT / 100)
    shares_by_weight = int(max_position_value / entry_price)

    # Max % of ADV
    max_adv_value = avg_daily_volume_eur * (config.MAX_PCT_OF_ADV / 100)
    shares_by_adv = int(max_adv_value / entry_price)

    shares = min(shares_by_risk, shares_by_weight, shares_by_adv)
    return max(shares, 0)


# ========================================================================== #
# Exit signal evaluation
# ========================================================================== #


def evaluate_exits(
    position: Position,
    current_price: float,
    sma_30w: Optional[float],
    sma_10w: Optional[float],
    regime_on: bool,
    current_date: str = "",
) -> dict:
    """
    Evaluate all exit conditions for a single position.

    Returns a dict with:
      - exit_triggered: bool
      - reason: str
      - urgency: "immediate" | "within_3_days" | "end_of_week"
      - details: str
    """
    result = {
        "exit_triggered": False,
        "reason": "",
        "urgency": "",
        "details": "",
        "warnings": [],
    }

    # Track highest price since entry
    if current_price > position.highest_since_entry:
        position.highest_since_entry = current_price

    # Check if +20% threshold reached (activate trailing)
    gain_pct = (current_price / position.entry_price - 1) * 100
    if gain_pct >= config.PROFIT_THRESHOLD_TO_TRAIL:
        position.trailing_active = True

    # --- EXIT 1: Hard stop (absolute, always applies) ---
    if current_price <= position.stop_price:
        result["exit_triggered"] = True
        result["reason"] = "HARD_STOP"
        result["urgency"] = "immediate"
        loss_pct = (current_price / position.entry_price - 1) * 100
        result["details"] = (
            f"Price {current_price:.2f} hit stop {position.stop_price:.2f} "
            f"({loss_pct:+.1f}% from entry {position.entry_price:.2f})"
        )
        return result

    # --- EXIT 2: Regime OFF + below 10-week SMA ---
    if not regime_on and sma_10w is not None:
        if current_price < sma_10w:
            result["exit_triggered"] = True
            result["reason"] = "REGIME_OFF_BELOW_10W"
            result["urgency"] = "within_3_days"
            result["details"] = (
                f"Regime OFF + price {current_price:.2f} below "
                f"10-week SMA {sma_10w:.2f}"
            )
            return result

    # --- EXIT 3: Weekly close below 30-week SMA ---
    if sma_30w is not None and position.trailing_active:
        # After +20%, the 30-week SMA is the ONLY exit (hard stop removed)
        if current_price < sma_30w:
            result["exit_triggered"] = True
            result["reason"] = "BELOW_30W_SMA"
            result["urgency"] = "end_of_week"
            result["details"] = (
                f"Price {current_price:.2f} below 30-week SMA "
                f"{sma_30w:.2f} (trailing mode active, +{gain_pct:.1f}%)"
            )
            return result
    elif sma_30w is not None:
        # Before +20%, 30-week SMA break is also an exit
        if current_price < sma_30w:
            result["exit_triggered"] = True
            result["reason"] = "BELOW_30W_SMA"
            result["urgency"] = "end_of_week"
            result["details"] = (
                f"Price {current_price:.2f} below 30-week SMA "
                f"{sma_30w:.2f} ({gain_pct:+.1f}% from entry)"
            )
            return result

    # --- WARNINGS (not exits, but flags) ---
    if not regime_on:
        result["warnings"].append("Regime OFF — no new entries, exits tightened")

    if not regime_on and sma_10w and current_price < sma_10w * 1.03:
        result["warnings"].append(
            f"CLOSE to 10w SMA ({current_price:.2f} vs {sma_10w:.2f}) — "
            f"regime-off exit may trigger soon"
        )

    if sma_30w and current_price < sma_30w * 1.05:
        result["warnings"].append(
            f"Approaching 30w SMA ({current_price:.2f} vs {sma_30w:.2f})"
        )

    drawdown_from_high = (
        (current_price / position.highest_since_entry - 1) * 100
        if position.highest_since_entry > 0 else 0
    )
    if drawdown_from_high < -15:
        result["warnings"].append(
            f"Drawdown from high: {drawdown_from_high:.1f}%"
        )

    return result


# ========================================================================== #
# Portfolio-level exit scan
# ========================================================================== #


def scan_all_exits(
    portfolio: PortfolioState,
    signals: dict[str, pd.DataFrame],
    as_of: Optional[str] = None,
) -> list[dict]:
    """
    Scan all open positions for exit signals.

    Returns a list of exit reports, one per position.
    """
    reports = []

    for pos in portfolio.open_positions:
        if pos.ticker not in signals:
            reports.append({
                "ticker": pos.ticker,
                "status": "NO_DATA",
                "details": "No signal data available",
            })
            continue

        df = signals[pos.ticker]
        if df.empty:
            continue

        if as_of:
            mask = df.index <= pd.Timestamp(as_of)
            if not mask.any():
                continue
            row = df.loc[mask].iloc[-1]
        else:
            row = df.iloc[-1]

        current_price = row.get("Close", 0)
        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[0]

        sma_30w = row.get("exit_sma_30w")
        sma_10w = row.get("exit_sma_10w")
        regime_on = bool(row.get("regime_on", False))

        exit_eval = evaluate_exits(
            position=pos,
            current_price=float(current_price),
            sma_30w=float(sma_30w) if pd.notna(sma_30w) else None,
            sma_10w=float(sma_10w) if pd.notna(sma_10w) else None,
            regime_on=regime_on,
        )

        gain_pct = (current_price / pos.entry_price - 1) * 100

        report = {
            "ticker": pos.ticker,
            "entry_date": pos.entry_date,
            "entry_price": pos.entry_price,
            "current_price": float(current_price),
            "gain_pct": round(gain_pct, 1),
            "stop_price": pos.stop_price,
            "trailing_active": pos.trailing_active,
            "highest_since_entry": pos.highest_since_entry,
            "regime_on": regime_on,
            "sma_30w": float(sma_30w) if pd.notna(sma_30w) else None,
            "sma_10w": float(sma_10w) if pd.notna(sma_10w) else None,
            **exit_eval,
        }
        reports.append(report)

    return reports


def print_exit_scan(reports: list[dict]) -> None:
    """Pretty-print the exit scan results."""
    sep = "=" * 70
    print(f"\n{sep}")
    print("  POSITION EXIT SCAN")
    print(sep)

    exits = [r for r in reports if r.get("exit_triggered")]
    holds = [r for r in reports if not r.get("exit_triggered") and r.get("current_price")]
    warnings = [r for r in holds if r.get("warnings")]

    if exits:
        print(f"\n  EXIT TRIGGERED ({len(exits)}):")
        print(f"  {'─' * 66}")
        for r in exits:
            print(f"\n  {r['ticker']}")
            print(f"    Reason:   {r['reason']}")
            print(f"    Urgency:  {r['urgency']}")
            print(f"    Details:  {r['details']}")
            print(f"    P&L:      {r['gain_pct']:+.1f}%")

    if holds:
        print(f"\n  HOLD ({len(holds)}):")
        print(f"  {'─' * 66}")
        print(f"  {'Ticker':<12} {'Entry':>8} {'Current':>8} {'P&L':>8} "
              f"{'Stop':>8} {'30w SMA':>8} {'10w SMA':>8} {'Trail':>6}")
        print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
        for r in holds:
            trail = "YES" if r.get("trailing_active") else "no"
            sma30 = f"{r['sma_30w']:.2f}" if r.get("sma_30w") else "N/A"
            sma10 = f"{r['sma_10w']:.2f}" if r.get("sma_10w") else "N/A"
            print(
                f"  {r['ticker']:<12} {r['entry_price']:>8.2f} "
                f"{r['current_price']:>8.2f} {r['gain_pct']:>+7.1f}% "
                f"{r['stop_price']:>8.2f} {sma30:>8} {sma10:>8} {trail:>6}"
            )

    if warnings:
        print(f"\n  WARNINGS:")
        print(f"  {'─' * 66}")
        for r in warnings:
            for w in r["warnings"]:
                print(f"  {r['ticker']:<12} {w}")

    if not exits and not warnings:
        print("\n  All positions healthy. No exits or warnings.")

    print()


# ========================================================================== #
# Simulate hypothetical positions for current candidates
# ========================================================================== #


def simulate_watchlist_positions(
    signals: dict[str, pd.DataFrame],
    entry_offset_days: int = 30,
) -> PortfolioState:
    """
    Create hypothetical positions for trend template candidates
    as if they were entered N days ago. Useful for demonstrating
    how the exit logic works on current market data.
    """
    portfolio = PortfolioState()

    for ticker, df in signals.items():
        if df.empty:
            continue

        last = df.iloc[-1]
        if not last.get("trend_template_pass", False):
            continue

        # Simulate entry at the price N days ago
        if len(df) <= entry_offset_days:
            continue

        entry_row = df.iloc[-(entry_offset_days + 1)]
        entry_price = entry_row.get("Close", 0)
        if isinstance(entry_price, pd.Series):
            entry_price = entry_price.iloc[0]
        if entry_price <= 0:
            continue

        entry_date = str(df.index[-(entry_offset_days + 1)].date())

        atr = entry_row.get("atr_14")
        if isinstance(atr, pd.Series):
            atr = atr.iloc[0]

        stop = calculate_stop_price(
            entry_price,
            float(atr) if pd.notna(atr) else None,
        )

        pos = Position(
            ticker=ticker,
            entry_date=entry_date,
            entry_price=float(entry_price),
            shares=100,  # placeholder
            stop_price=stop,
            risk_per_share=float(entry_price) - stop,
        )

        # Track highest price during the holding period
        holding_data = df.iloc[-(entry_offset_days + 1):]
        for _, row in holding_data.iterrows():
            p = row.get("Close", 0)
            if isinstance(p, pd.Series):
                p = p.iloc[0]
            if p > pos.highest_since_entry:
                pos.highest_since_entry = float(p)

        # Check if +20% threshold was reached
        if pos.highest_since_entry >= entry_price * 1.2:
            pos.trailing_active = True

        portfolio.positions.append(pos)

    return portfolio
