#!/usr/bin/env python3
"""
KnockoutSwing v1.0 — Backtest engine for KO certificate swing trades.

Daily-bar backtest on 4 major indices (DAX, S&P 500, NDX, Euro Stoxx 50).
Simulates KO certificate mechanics: barrier knockout, leverage, financing.
Staged exits (1/3 at 1.5R, 1/3 at 3R, 1/3 trailing).

Usage:
  python run_knockout_backtest.py
  python run_knockout_backtest.py --start 2015-01-01 --end 2024-12-31
"""
import sys
sys.path.insert(0, ".")

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from dach_momentum import config
from dach_momentum.knockout_signals import (
    compute_ko_signals, detect_setup_a, detect_setup_c,
    detect_setup_b_breakout, check_retest,
    SetupSignal, PendingBreakout,
)
from dach_momentum.signals import atr, adx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ========================================================================== #
# Data structures
# ========================================================================== #

@dataclass
class KOTranche:
    tranche_id: int           # 1, 2, or 3
    num_certs: int
    status: str = "OPEN"      # OPEN | CLOSED
    target_r: float = 0.0     # 1.5, 3.0, or 0 (trailing)
    exit_date: str = ""
    exit_index_price: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0


@dataclass
class KOTrade:
    trade_id: int
    index_name: str
    ticker: str
    setup_type: str           # A, B, C
    direction: str            # LONG, SHORT
    entry_date: str
    entry_price: float        # index level at entry
    stop_price: float
    target_price: float
    barrier: float
    leverage: float
    r_value: float            # |entry - stop|
    cert_price_at_entry: float
    tranches: list[KOTranche] = field(default_factory=list)
    financing_accrued: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 999999.0
    days_since_new_extreme: int = 0
    holding_days: int = 0
    exit_date: str = ""
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    total_r_multiple: float = 0.0
    knocked_out: bool = False

    @property
    def is_fully_closed(self) -> bool:
        return all(t.status == "CLOSED" for t in self.tranches)

    @property
    def open_tranches(self) -> list[KOTranche]:
        return [t for t in self.tranches if t.status == "OPEN"]

    @property
    def open_cert_count(self) -> int:
        return sum(t.num_certs for t in self.open_tranches)


@dataclass
class KOState:
    cash: float
    trades: list[KOTrade] = field(default_factory=list)
    closed_trades: list[KOTrade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    monthly_trade_count: dict = field(default_factory=dict)
    regime_ok: bool = True
    next_trade_id: int = 1

    @property
    def open_trades(self) -> list[KOTrade]:
        return [t for t in self.trades if not t.is_fully_closed]

    def total_equity(self, index_prices: dict[str, float]) -> float:
        val = self.cash
        for t in self.open_trades:
            cert_price = _current_cert_price(t, index_prices.get(t.ticker, t.entry_price))
            val += cert_price * t.open_cert_count
        return val

    def total_risk_pct(self, equity: float) -> float:
        risk = sum(
            t.r_value * t.open_cert_count / config.KO_RATIO
            for t in self.open_trades
        )
        return (risk / equity * 100) if equity > 0 else 0.0


# ========================================================================== #
# KO certificate simulation
# ========================================================================== #

def create_ko_certificate(
    direction: str,
    entry_price: float,
    stop_distance: float,
) -> Optional[tuple[float, float, float]]:
    """
    Simulate selecting a KO certificate for a trade.

    Returns (barrier, leverage, cert_price) or None if no valid product.
    """
    barrier_dist = stop_distance * config.KO_BARRIER_TARGET

    if direction == "LONG":
        barrier = entry_price - barrier_dist
        if barrier <= 0:
            return None
        leverage = entry_price / barrier_dist
    else:
        barrier = entry_price + barrier_dist
        leverage = entry_price / barrier_dist

    if leverage < config.KO_LEVERAGE_MIN or leverage > config.KO_LEVERAGE_MAX:
        # Try to adjust barrier to land in valid leverage range
        for target_lev in [7.5, 6.0, 8.0, 5.5, 9.0]:
            adj_dist = entry_price / target_lev
            if direction == "LONG":
                adj_barrier = entry_price - adj_dist
                if adj_barrier <= 0:
                    continue
                # Barrier must be farther than stop
                if adj_dist < stop_distance * config.KO_BARRIER_MULT:
                    continue
            else:
                adj_barrier = entry_price + adj_dist
                if adj_dist < stop_distance * config.KO_BARRIER_MULT:
                    continue
            barrier = adj_barrier
            barrier_dist = adj_dist
            leverage = target_lev
            break
        else:
            return None

    cert_price = barrier_dist / config.KO_RATIO
    return barrier, leverage, cert_price


def _current_cert_price(trade: KOTrade, current_index: float) -> float:
    """Mark-to-market certificate price given current index level."""
    if trade.direction == "LONG":
        raw = (current_index - trade.barrier) / config.KO_RATIO
    else:
        raw = (trade.barrier - current_index) / config.KO_RATIO
    return max(raw, 0.0)


def _check_knockout(trade: KOTrade, day_high: float, day_low: float) -> bool:
    """Check if the KO barrier was breached during the trading day."""
    if trade.direction == "LONG":
        return day_low <= trade.barrier
    else:
        return day_high >= trade.barrier


# ========================================================================== #
# Position sizing
# ========================================================================== #

def size_ko_trade(
    equity: float,
    cert_price: float,
    r_value: float,
    leverage: float,
) -> int:
    """
    Size the trade: total certificates across all 3 tranches.

    Risk per trade = 1% of equity.
    Risk = r_value (index points) * leverage * certs / ratio ... simplified:
    If stop is hit, each cert loses (r_value / ratio) in price.
    Total risk = num_certs * (r_value / ratio).
    """
    risk_per_cert = r_value / config.KO_RATIO
    if risk_per_cert <= 0:
        return 0
    max_risk = equity * (config.KO_RISK_PER_TRADE_PCT / 100)
    total_certs = int(max_risk / risk_per_cert)
    return max(total_certs, 0)


# ========================================================================== #
# Core backtest loop
# ========================================================================== #

def run_knockout_backtest(
    index_prices: dict[str, pd.DataFrame],
    start_date: str = "2010-01-01",
    end_date: str = "2026-12-31",
    initial_capital: float = None,
) -> KOState:
    """Run the daily KO swing backtest across all indices."""
    if initial_capital is None:
        initial_capital = config.KO_INITIAL_CAPITAL

    # Compute signals for each index
    logger.info("Computing KO signals for %d indices...", len(index_prices))
    all_signals: dict[str, pd.DataFrame] = {}
    for ticker, df in index_prices.items():
        if len(df) < 252:
            continue
        all_signals[ticker] = compute_ko_signals(df)
    logger.info("Signals computed for: %s", list(all_signals.keys()))

    # Build unified daily date index
    all_dates = sorted(set().union(*(s.index for s in all_signals.values())))
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    trading_dates = [d for d in all_dates if start_ts <= d <= end_ts]

    state = KOState(cash=initial_capital)
    pending_breakouts: list[PendingBreakout] = []
    last_regime_check = ""

    logger.info("Running KO backtest: %s to %s (%d trading days)",
                start_date, end_date, len(trading_dates))

    for i, date in enumerate(trading_dates):
        if i % 252 == 0:
            logger.info("  %s — %d open trades, equity: %.0f",
                        date.date(), len(state.open_trades),
                        state.total_equity(_day_prices(all_signals, date)))

        month_str = date.strftime("%Y-%m")
        current_prices = _day_prices(all_signals, date)

        # --- Phase 1: Barrier knockout check ---
        for trade in list(state.open_trades):
            sig = all_signals.get(trade.ticker)
            if sig is None or date not in sig.index:
                continue
            row = sig.loc[date]
            if _check_knockout(trade, float(row["high"]), float(row["low"])):
                for tr in trade.open_tranches:
                    tr.status = "CLOSED"
                    tr.exit_date = str(date.date())
                    tr.exit_index_price = float(row["close"])
                    tr.exit_reason = "BARRIER_KO"
                    tr.pnl = -tr.num_certs * trade.cert_price_at_entry
                trade.knocked_out = True
                _finalize_trade(trade, date)
                state.trades.remove(trade)
                state.closed_trades.append(trade)

        # --- Phase 2: Daily financing ---
        for trade in state.open_trades:
            daily_fin = trade.cert_price_at_entry * (config.KO_FINANCING_RATE_ANNUAL / 365)
            trade.financing_accrued += daily_fin * trade.open_cert_count
            trade.holding_days += 1

        # --- Phase 3: Staged exits + hard stop + time stop ---
        for trade in list(state.open_trades):
            sig = all_signals.get(trade.ticker)
            if sig is None or date not in sig.index:
                continue
            row = sig.loc[date]
            price = float(row["close"])
            atr_val = float(row["atr_14"]) if pd.notna(row.get("atr_14")) else 0

            # Update extremes
            new_extreme = False
            if trade.direction == "LONG":
                if price > trade.highest_price:
                    trade.highest_price = price
                    new_extreme = True
                current_r = (price - trade.entry_price) / trade.r_value
            else:
                if price < trade.lowest_price:
                    trade.lowest_price = price
                    new_extreme = True
                current_r = (trade.entry_price - price) / trade.r_value

            if new_extreme:
                trade.days_since_new_extreme = 0
            else:
                trade.days_since_new_extreme += 1

            # Hard stop (Mandate 3)
            hard_stop_hit = False
            if trade.direction == "LONG" and price <= trade.stop_price:
                hard_stop_hit = True
            elif trade.direction == "SHORT" and price >= trade.stop_price:
                hard_stop_hit = True

            if hard_stop_hit:
                cert_px = _current_cert_price(trade, price)
                for tr in trade.open_tranches:
                    tr.status = "CLOSED"
                    tr.exit_date = str(date.date())
                    tr.exit_index_price = price
                    tr.exit_reason = "HARD_STOP"
                    tr.pnl = (cert_px - trade.cert_price_at_entry) * tr.num_certs
                _finalize_trade(trade, date)
                state.trades.remove(trade)
                state.closed_trades.append(trade)
                continue

            # Time stop (Mandate 8)
            if trade.days_since_new_extreme >= config.KO_MAX_HOLD_DAYS:
                cert_px = _current_cert_price(trade, price)
                for tr in trade.open_tranches:
                    tr.status = "CLOSED"
                    tr.exit_date = str(date.date())
                    tr.exit_index_price = price
                    tr.exit_reason = "TIME_STOP"
                    tr.pnl = (cert_px - trade.cert_price_at_entry) * tr.num_certs
                _finalize_trade(trade, date)
                state.trades.remove(trade)
                state.closed_trades.append(trade)
                continue

            # Staged exits per tranche
            cert_px = _current_cert_price(trade, price)
            for tr in trade.open_tranches:
                exit_reason = ""
                if tr.tranche_id == 1 and current_r >= config.KO_EXIT_TRANCHE_1_R:
                    exit_reason = "STAGED_1_5R"
                elif tr.tranche_id == 2 and current_r >= config.KO_EXIT_TRANCHE_2_R:
                    exit_reason = "STAGED_3R"
                elif tr.tranche_id == 3 and atr_val > 0:
                    if trade.direction == "LONG":
                        trail = trade.highest_price - config.KO_TRAILING_ATR_MULT * atr_val
                        if price <= trail:
                            exit_reason = "TRAILING_STOP"
                    else:
                        trail = trade.lowest_price + config.KO_TRAILING_ATR_MULT * atr_val
                        if price >= trail:
                            exit_reason = "TRAILING_STOP"

                if exit_reason:
                    tr.status = "CLOSED"
                    tr.exit_date = str(date.date())
                    tr.exit_index_price = price
                    tr.exit_reason = exit_reason
                    spread_cost = trade.cert_price_at_entry * config.KO_EMITTER_SPREAD_PCT / 2
                    tr.pnl = (cert_px - trade.cert_price_at_entry - spread_cost) * tr.num_certs
                    state.cash += cert_px * tr.num_certs - config.KO_COMMISSION_EUR

            if trade.is_fully_closed:
                _finalize_trade(trade, date)
                state.trades.remove(trade)
                state.closed_trades.append(trade)

        # --- Phase 4: Quarterly regime check (Mandate 12) ---
        quarter_key = f"{date.year}-Q{(date.month - 1) // 3 + 1}"
        if quarter_key != last_regime_check:
            last_regime_check = quarter_key
            adx_ok_count = 0
            for ticker, sig in all_signals.items():
                if date in sig.index:
                    prior = sig.index[sig.index <= date]
                    if len(prior) >= 70:
                        # Compute ADX on weekly-resampled data
                        raw_df = index_prices.get(ticker)
                        if raw_df is not None:
                            weekly = raw_df.loc[raw_df.index <= date].tail(252)
                            weekly_r = weekly.resample("W-FRI").agg({
                                "Open": "first", "High": "max",
                                "Low": "min", "Close": "last",
                            }).dropna()
                            if len(weekly_r) >= 20:
                                adx_val = adx(weekly_r, config.KO_ADX_PERIOD)
                                if len(adx_val) > 0 and pd.notna(adx_val.iloc[-1]):
                                    if float(adx_val.iloc[-1]) >= config.KO_ADX_THRESHOLD:
                                        adx_ok_count += 1
            state.regime_ok = adx_ok_count >= 2  # majority of indices trending

        # --- Phase 5: New entries (Fridays only — Mandate 10) ---
        if date.weekday() == 4 and state.regime_ok:
            if len(state.open_trades) < config.KO_MAX_POSITIONS:
                month_count = state.monthly_trade_count.get(month_str, 0)
                if month_count < config.KO_MAX_TRADES_PER_MONTH:
                    equity = state.total_equity(current_prices)
                    risk_pct = state.total_risk_pct(equity)

                    for ticker, sig in all_signals.items():
                        if date not in sig.index:
                            continue
                        idx_pos = sig.index.get_loc(date)
                        index_name = config.KO_INDICES.get(ticker, ticker)

                        # Check for Setup B breakouts → add to pending
                        bo = detect_setup_b_breakout(sig, idx_pos)
                        if bo is not None:
                            bo.index_name = index_name
                            pending_breakouts.append(bo)

                        # Check Setups A and C
                        setups = []
                        sa = detect_setup_a(sig, idx_pos)
                        if sa:
                            setups.append(sa)
                        sc = detect_setup_c(sig, idx_pos)
                        if sc:
                            setups.append(sc)

                        for setup in setups:
                            if len(state.open_trades) >= config.KO_MAX_POSITIONS:
                                break
                            if month_count >= config.KO_MAX_TRADES_PER_MONTH:
                                break
                            if risk_pct >= config.KO_MAX_TOTAL_RISK_PCT:
                                break
                            # Skip if already have a trade on same index
                            if any(t.ticker == ticker for t in state.open_trades):
                                continue

                            result = create_ko_certificate(
                                setup.direction, setup.entry_price, setup.r_value,
                            )
                            if result is None:
                                continue
                            barrier, leverage, cert_price = result

                            total_certs = size_ko_trade(equity, cert_price, setup.r_value, leverage)
                            if total_certs < 3:
                                continue
                            cost = total_certs * cert_price + config.KO_COMMISSION_EUR
                            cost += total_certs * cert_price * config.KO_EMITTER_SPREAD_PCT / 2
                            if cost > state.cash:
                                total_certs = int((state.cash - config.KO_COMMISSION_EUR) /
                                                  (cert_price * (1 + config.KO_EMITTER_SPREAD_PCT / 2)))
                                if total_certs < 3:
                                    continue
                                cost = total_certs * cert_price + config.KO_COMMISSION_EUR
                                cost += total_certs * cert_price * config.KO_EMITTER_SPREAD_PCT / 2

                            cpt = total_certs // 3
                            remainder = total_certs - 3 * cpt
                            tranches = [
                                KOTranche(1, cpt + (1 if remainder > 0 else 0),
                                          target_r=config.KO_EXIT_TRANCHE_1_R),
                                KOTranche(2, cpt + (1 if remainder > 1 else 0),
                                          target_r=config.KO_EXIT_TRANCHE_2_R),
                                KOTranche(3, cpt, target_r=0.0),
                            ]

                            trade = KOTrade(
                                trade_id=state.next_trade_id,
                                index_name=index_name,
                                ticker=ticker,
                                setup_type=setup.setup_type,
                                direction=setup.direction,
                                entry_date=str(date.date()),
                                entry_price=setup.entry_price,
                                stop_price=setup.stop_price,
                                target_price=setup.target_price,
                                barrier=barrier,
                                leverage=leverage,
                                r_value=setup.r_value,
                                cert_price_at_entry=cert_price,
                                tranches=tranches,
                                highest_price=setup.entry_price,
                                lowest_price=setup.entry_price,
                            )
                            state.trades.append(trade)
                            state.cash -= cost
                            state.next_trade_id += 1
                            month_count += 1
                            state.monthly_trade_count[month_str] = month_count
                            risk_pct = state.total_risk_pct(equity)

        # --- Phase 5b: Check pending breakouts for retest (Setup B) ---
        expired = []
        for pb in pending_breakouts:
            # Find the ticker for this pending breakout
            ticker = None
            for t, name in config.KO_INDICES.items():
                if name == pb.index_name:
                    ticker = t
                    break
            if ticker is None or ticker not in all_signals:
                expired.append(pb)
                continue
            sig = all_signals[ticker]
            if date not in sig.index:
                pb.days_waiting += 1
                if pb.days_waiting > config.KO_RETEST_WINDOW_DAYS:
                    expired.append(pb)
                continue

            idx_pos = sig.index.get_loc(date)
            retest = check_retest(pb, sig, idx_pos)
            pb.days_waiting += 1

            if retest is not None:
                # Same entry logic as A/C
                if (len(state.open_trades) < config.KO_MAX_POSITIONS and
                        state.monthly_trade_count.get(month_str, 0) < config.KO_MAX_TRADES_PER_MONTH and
                        not any(t.ticker == ticker for t in state.open_trades)):
                    equity = state.total_equity(current_prices)
                    result = create_ko_certificate(retest.direction, retest.entry_price, retest.r_value)
                    if result is not None:
                        barrier, leverage, cert_price = result
                        total_certs = size_ko_trade(equity, cert_price, retest.r_value, leverage)
                        if total_certs >= 3:
                            cost = total_certs * cert_price + config.KO_COMMISSION_EUR
                            cost += total_certs * cert_price * config.KO_EMITTER_SPREAD_PCT / 2
                            if cost <= state.cash:
                                cpt = total_certs // 3
                                rem = total_certs - 3 * cpt
                                tranches = [
                                    KOTranche(1, cpt + (1 if rem > 0 else 0),
                                              target_r=config.KO_EXIT_TRANCHE_1_R),
                                    KOTranche(2, cpt + (1 if rem > 1 else 0),
                                              target_r=config.KO_EXIT_TRANCHE_2_R),
                                    KOTranche(3, cpt, target_r=0.0),
                                ]
                                trade = KOTrade(
                                    trade_id=state.next_trade_id,
                                    index_name=pb.index_name,
                                    ticker=ticker,
                                    setup_type="B",
                                    direction=retest.direction,
                                    entry_date=str(date.date()),
                                    entry_price=retest.entry_price,
                                    stop_price=retest.stop_price,
                                    target_price=retest.target_price,
                                    barrier=barrier,
                                    leverage=leverage,
                                    r_value=retest.r_value,
                                    cert_price_at_entry=cert_price,
                                    tranches=tranches,
                                    highest_price=retest.entry_price,
                                    lowest_price=retest.entry_price,
                                )
                                state.trades.append(trade)
                                state.cash -= cost
                                state.next_trade_id += 1
                                mc = state.monthly_trade_count.get(month_str, 0)
                                state.monthly_trade_count[month_str] = mc + 1
                expired.append(pb)
            elif pb.days_waiting > config.KO_RETEST_WINDOW_DAYS:
                expired.append(pb)

        for pb in expired:
            if pb in pending_breakouts:
                pending_breakouts.remove(pb)

        # --- Phase 6: Record equity ---
        eq = state.total_equity(current_prices)
        state.equity_curve.append({
            "date": date,
            "equity": eq,
            "cash": state.cash,
            "open_trades": len(state.open_trades),
            "regime_ok": state.regime_ok,
        })

    # Close remaining at last price
    if trading_dates:
        last_date = trading_dates[-1]
        for trade in list(state.open_trades):
            price = current_prices.get(trade.ticker, trade.entry_price)
            cert_px = _current_cert_price(trade, price)
            for tr in trade.open_tranches:
                tr.status = "CLOSED"
                tr.exit_date = str(last_date.date())
                tr.exit_index_price = price
                tr.exit_reason = "END_OF_BACKTEST"
                tr.pnl = (cert_px - trade.cert_price_at_entry) * tr.num_certs
            _finalize_trade(trade, last_date)
            state.trades.remove(trade)
            state.closed_trades.append(trade)

    return state


# ========================================================================== #
# Helpers
# ========================================================================== #

def _day_prices(all_signals: dict, date: pd.Timestamp) -> dict[str, float]:
    out = {}
    for ticker, sig in all_signals.items():
        if date in sig.index:
            p = sig.loc[date, "close"]
            if pd.notna(p) and p > 0:
                out[ticker] = float(p)
    return out


def _finalize_trade(trade: KOTrade, date: pd.Timestamp) -> None:
    trade.exit_date = str(date.date())
    trade.total_pnl = sum(t.pnl for t in trade.tranches) - trade.financing_accrued
    total_cost = trade.cert_price_at_entry * sum(t.num_certs for t in trade.tranches)
    trade.total_pnl_pct = (trade.total_pnl / total_cost * 100) if total_cost > 0 else 0
    trade.total_r_multiple = trade.total_pnl / (trade.r_value / config.KO_RATIO * sum(t.num_certs for t in trade.tranches)) if trade.r_value > 0 else 0


# ========================================================================== #
# Performance reporting
# ========================================================================== #

def summarize_ko(state: KOState) -> dict:
    eq = pd.DataFrame(state.equity_curve)
    if eq.empty:
        return {}
    eq["date"] = pd.to_datetime(eq["date"])
    eq = eq.set_index("date")
    eq["returns"] = eq["equity"].pct_change()

    initial = eq["equity"].iloc[0]
    final = eq["equity"].iloc[-1]
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = (final / initial) ** (1 / years) - 1 if years > 0 else 0

    ann_vol = eq["returns"].std() * np.sqrt(252)
    sharpe = cagr / ann_vol if ann_vol > 0 else 0
    sortino_denom = eq["returns"][eq["returns"] < 0].std() * np.sqrt(252)
    sortino = cagr / sortino_denom if sortino_denom > 0 else 0
    peak = eq["equity"].expanding().max()
    dd = (eq["equity"] - peak) / peak
    max_dd = dd.min()

    trades = state.closed_trades
    winners = [t for t in trades if t.total_pnl > 0]
    losers = [t for t in trades if t.total_pnl <= 0]
    win_rate = len(winners) / len(trades) * 100 if trades else 0
    avg_r = np.mean([t.total_r_multiple for t in trades]) if trades else 0
    profit_factor = (
        sum(t.total_pnl for t in winners) / abs(sum(t.total_pnl for t in losers))
        if losers and sum(t.total_pnl for t in losers) != 0 else float("inf")
    )

    # Per-setup breakdown
    setup_stats = {}
    for st in ["A", "B", "C"]:
        subset = [t for t in trades if t.setup_type == st]
        if subset:
            w = [t for t in subset if t.total_pnl > 0]
            setup_stats[st] = {
                "count": len(subset),
                "win_rate": len(w) / len(subset) * 100,
                "avg_r": np.mean([t.total_r_multiple for t in subset]),
            }

    # KO-specific
    ko_count = sum(1 for t in trades if t.knocked_out)
    ko_rate = ko_count / len(trades) * 100 if trades else 0
    avg_leverage = np.mean([t.leverage for t in trades]) if trades else 0
    total_financing = sum(t.financing_accrued for t in trades)
    time_stops = sum(1 for t in trades if any(tr.exit_reason == "TIME_STOP" for tr in t.tranches))

    # Exit reason breakdown (tranche level)
    exit_reasons = {}
    for t in trades:
        for tr in t.tranches:
            exit_reasons[tr.exit_reason] = exit_reasons.get(tr.exit_reason, 0) + 1

    return {
        "initial": initial, "final": final,
        "cagr_pct": cagr * 100, "ann_vol_pct": ann_vol * 100,
        "sharpe": sharpe, "sortino": sortino,
        "max_dd_pct": max_dd * 100,
        "total_trades": len(trades), "winners": len(winners), "losers": len(losers),
        "win_rate_pct": win_rate, "avg_r": avg_r, "profit_factor": profit_factor,
        "setup_stats": setup_stats,
        "ko_rate_pct": ko_rate, "avg_leverage": avg_leverage,
        "total_financing": total_financing, "time_stop_count": time_stops,
        "exit_reasons": exit_reasons,
        "regime_on_pct": eq["regime_ok"].mean() * 100,
        "equity_curve": eq,
    }


def print_ko(s: dict) -> None:
    sep = "=" * 64
    print(f"\n{sep}\n  KNOCKOUTSWING v1.0 BACKTEST RESULTS\n{sep}")
    print(f"  Initial:       EUR {s['initial']:>12,.0f}")
    print(f"  Final:         EUR {s['final']:>12,.0f}")
    print(f"  CAGR:          {s['cagr_pct']:>+12.1f}%")
    print(f"  Ann Vol:       {s['ann_vol_pct']:>12.1f}%")
    print(f"  Sharpe:        {s['sharpe']:>12.2f}")
    print(f"  Sortino:       {s['sortino']:>12.2f}")
    print(f"  Max DD:        {s['max_dd_pct']:>12.1f}%")

    print(f"\n  TRADES")
    print(f"    Total:       {s['total_trades']:>8d}")
    print(f"    Winners:     {s['winners']:>8d}")
    print(f"    Losers:      {s['losers']:>8d}")
    print(f"    Win Rate:    {s['win_rate_pct']:>8.1f}%")
    print(f"    Avg R:       {s['avg_r']:>+8.2f}")
    print(f"    Profit Factor: {s['profit_factor']:>6.2f}")

    print(f"\n  SETUP PERFORMANCE")
    for st, stats in sorted(s.get("setup_stats", {}).items()):
        label = {"A": "Pullback", "B": "Breakout", "C": "Higher-Low"}.get(st, st)
        print(f"    Setup {st} ({label:>10}): {stats['count']:>3d} trades, "
              f"{stats['win_rate']:.0f}% win, {stats['avg_r']:>+.2f} avg R")

    print(f"\n  KO CERTIFICATE METRICS")
    print(f"    Knockout rate:   {s['ko_rate_pct']:>8.1f}%")
    print(f"    Avg leverage:    {s['avg_leverage']:>8.1f}x")
    print(f"    Financing drag:  EUR {s['total_financing']:>8.0f}")
    print(f"    Time stops:      {s['time_stop_count']:>8d}")

    print(f"\n  EXIT REASONS (tranche level)")
    for r, n in sorted(s.get("exit_reasons", {}).items(), key=lambda x: -x[1]):
        print(f"    {r:<22s} {n:>5d}")

    print(f"\n  REGIME")
    print(f"    Regime OK:       {s['regime_on_pct']:>8.1f}%")

    # Annual returns
    eq = s.get("equity_curve")
    if eq is not None:
        print(f"\n  ANNUAL RETURNS")
        for year in sorted(eq.index.year.unique()):
            yr = eq[eq.index.year == year]
            if len(yr) >= 2:
                ret = (yr["equity"].iloc[-1] / yr["equity"].iloc[0] - 1) * 100
                print(f"    {year}:  {ret:>+8.1f}%")
    print()


# ========================================================================== #
# Main
# ========================================================================== #

def main():
    start = "2015-01-01"
    end = "2024-12-31"
    capital = config.KO_INITIAL_CAPITAL
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--start" and i + 1 < len(args):
            start = args[i + 1]
        elif a == "--end" and i + 1 < len(args):
            end = args[i + 1]
        elif a == "--capital" and i + 1 < len(args):
            capital = float(args[i + 1])

    print("\n[1/3] Downloading index data...")
    import yfinance as yf
    index_prices = {}
    for ticker, name in config.KO_INDICES.items():
        logger.info("Downloading %s (%s)...", name, ticker)
        df = yf.download(ticker, start=config.KO_DATA_START,
                         auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if len(df) > 0:
            index_prices[ticker] = df
            logger.info("  %s: %d bars", name, len(df))
        else:
            logger.warning("  %s: no data!", name)

    if not index_prices:
        print("ERROR: no index data downloaded.")
        return

    print(f"\n[2/3] Running KO backtest ({start} to {end}, EUR {capital:,.0f})...")
    state = run_knockout_backtest(
        index_prices=index_prices,
        start_date=start,
        end_date=end,
        initial_capital=capital,
    )

    print("\n[3/3] Results:")
    s = summarize_ko(state)
    print_ko(s)

    # Save trade log
    if state.closed_trades:
        rows = []
        for t in state.closed_trades:
            for tr in t.tranches:
                rows.append({
                    "trade_id": t.trade_id,
                    "index": t.index_name,
                    "setup": t.setup_type,
                    "direction": t.direction,
                    "entry_date": t.entry_date,
                    "entry_price": round(t.entry_price, 2),
                    "stop_price": round(t.stop_price, 2),
                    "barrier": round(t.barrier, 2),
                    "leverage": round(t.leverage, 1),
                    "tranche": tr.tranche_id,
                    "certs": tr.num_certs,
                    "exit_date": tr.exit_date,
                    "exit_price": round(tr.exit_index_price, 2),
                    "exit_reason": tr.exit_reason,
                    "pnl": round(tr.pnl, 2),
                    "r_multiple": round(t.total_r_multiple, 2),
                    "knocked_out": t.knocked_out,
                })
        trades_df = pd.DataFrame(rows)
        path = config.DATA_DIR / "ko_backtest_trades.csv"
        trades_df.to_csv(path, index=False)
        print(f"  Trade log: {path}")

    eq = s.get("equity_curve")
    if eq is not None:
        path = config.DATA_DIR / "ko_backtest_equity.csv"
        eq.to_csv(path)
        print(f"  Equity curve: {path}")


if __name__ == "__main__":
    main()
