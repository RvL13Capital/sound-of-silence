#!/usr/bin/env python3
"""
V2 backtest engine: Cross-sectional momentum in high-volatility breakouts.

Architecture differences vs V1 (run_backtest.py):
  - Candidate selection: top-N percentile ranking, not absolute thresholds
  - Regime: multi-layer (CDAX trend + breadth + vol + dispersion)
  - Sizing: inverse-vol weighted (equal risk contribution) + ATR/notional caps
  - Costs: Almgren-Chriss sqrt-impact + half-spread + slippage + commission

V1 remains the benchmark. V2 is a parallel module.

Usage:
  python run_backtest_v2.py
  python run_backtest_v2.py --start 2015-01-01 --end 2025-12-31
"""
import sys
sys.path.insert(0, ".")

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from dach_momentum import config
from dach_momentum.data import load_prices
from dach_momentum.signals import (
    sma, atr, rolling_high, rolling_low, compute_regime,
)

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
class TradeV2:
    ticker: str
    entry_date: str
    entry_price: float
    shares: int
    stop_price: float
    mom_rank: float = 0.0
    hvol_60: float = 0.0
    size_reason: str = ""
    entry_cost_bps: float = 0.0
    exit_cost_bps: float = 0.0
    exit_date: str = ""
    exit_price: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0
    highest_price: float = 0.0
    trailing_active: bool = False


@dataclass
class StateV2:
    cash: float
    positions: list[TradeV2] = field(default_factory=list)
    closed_trades: list[TradeV2] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)

    @property
    def open_positions(self):
        return [p for p in self.positions if not p.exit_date]

    def total_equity(self, prices: dict[str, float]) -> float:
        val = sum(
            p.shares * prices.get(p.ticker, p.entry_price)
            for p in self.open_positions
        )
        return self.cash + val


# ========================================================================== #
# Per-stock signals (minimal set for V2)
# ========================================================================== #

def compute_signals_v2(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the V2 per-stock signal set. Keep it lean."""
    close = df["Close"]
    out = pd.DataFrame(index=df.index)
    out["close"] = close

    # Momentum (12-1)
    out["mom_12_1"] = close.shift(21) / close.shift(252) - 1.0

    # Trend filter (gatekeeper only — ranking does the selection)
    out["sma_200"] = sma(close, 200)
    out["above_200"] = close > out["sma_200"]

    # Breakout: close within N days of a high
    out["high_3m"] = rolling_high(close, config.V2_BREAKOUT_WINDOW_DAYS)
    out["breakout"] = close >= out["high_3m"] * 0.98  # within 2% of 3m high

    # Realized volatility (annualised)
    # hvol_20: responsive — used for per-stock high-vol regime gate
    # hvol_60: stable  — used for position sizing
    log_ret = np.log(close / close.shift(1))
    out["hvol_20"] = log_ret.rolling(20).std() * np.sqrt(252)
    out["hvol_60"] = log_ret.rolling(config.V2_SIZING_VOL_LOOKBACK).std() * np.sqrt(252)

    # ATR for stop sizing
    out["atr_14"] = atr(df, 14)

    # Average daily volume (for market impact model)
    if "Volume" in df.columns:
        vol = df["Volume"]
        out["adv_20"] = vol.rolling(config.V2_ADV_LOOKBACK).mean()
    else:
        out["adv_20"] = np.nan

    # Trailing exit SMA
    out["exit_sma"] = sma(close, config.V2_EXIT_SMA_DAYS)

    return out


# ========================================================================== #
# Cross-sectional ranking
# ========================================================================== #

def compute_xs_mom_rank(
    signals: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Compute cross-sectional percentile rank of mom_12_1 across the universe
    on each date. Returns a DataFrame (dates x tickers) of percentile ranks.
    """
    mom = pd.DataFrame({
        t: s["mom_12_1"] for t, s in signals.items()
        if "mom_12_1" in s.columns
    })
    # Percentile rank per row (date), 0..100
    return mom.rank(axis=1, pct=True) * 100


# ========================================================================== #
# Multi-layer macro regime
# ========================================================================== #

def compute_macro_regime(
    benchmark_close: pd.Series,
    signals: dict[str, pd.DataFrame],
    xs_rank: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute the multi-layer regime gate. Returns a DataFrame indexed by
    benchmark dates with boolean columns per layer plus a combined `regime_on`.

    Layers:
      1) Trend:      CDAX > 40-week SMA (and rising)
      2) Breadth:    % of universe above 200d SMA >= V2_REGIME_BREADTH_MIN_PCT
      3) Volatility: CDAX realized vol (20d) <= V2_REGIME_VOL_MAX_HVOL
      4) Dispersion: mean mom_12_1 of top decile - bottom decile >= threshold
    """
    idx = benchmark_close.index
    out = pd.DataFrame(index=idx)

    # --- Layer 1: trend (reuse V1 logic) ---
    v1_regime = compute_regime(benchmark_close)
    out["l1_trend"] = v1_regime["regime_on"].reindex(idx).fillna(False)

    # --- Layer 2: breadth (% of universe above 200d SMA) ---
    above_200 = pd.DataFrame({
        t: s["above_200"] for t, s in signals.items()
        if "above_200" in s.columns
    })
    breadth_pct = above_200.mean(axis=1) * 100
    breadth_pct = breadth_pct.reindex(idx).ffill()
    out["l2_breadth"] = breadth_pct >= config.V2_REGIME_BREADTH_MIN_PCT

    # --- Layer 3: volatility regime (CDAX realized vol) ---
    bench_ret = np.log(benchmark_close / benchmark_close.shift(1))
    bench_vol = bench_ret.rolling(config.V2_REGIME_VOL_LOOKBACK).std() * np.sqrt(252)
    out["bench_vol"] = bench_vol
    out["l3_vol_ok"] = bench_vol <= config.V2_REGIME_VOL_MAX_HVOL

    # --- Layer 4: cross-sectional dispersion ---
    # Use mom_12_1 level (not rank) to measure spread
    mom = pd.DataFrame({
        t: s["mom_12_1"] for t, s in signals.items()
        if "mom_12_1" in s.columns
    })
    top_decile = mom.quantile(0.9, axis=1)
    bot_decile = mom.quantile(0.1, axis=1)
    dispersion = (top_decile - bot_decile).reindex(idx).ffill()
    out["dispersion"] = dispersion
    out["l4_dispersion"] = dispersion >= config.V2_REGIME_DISPERSION_MIN

    # --- Combined: all four layers must pass ---
    out["regime_on"] = (
        out["l1_trend"] & out["l2_breadth"] & out["l3_vol_ok"] & out["l4_dispersion"]
    )

    return out


# ========================================================================== #
# Volatility-adjusted position sizing
# ========================================================================== #

def vol_adjusted_shares(
    equity: float,
    entry_price: float,
    atr_val: float,
    stock_vol: float,
    available_cash: float,
    commission: float,
) -> tuple[int, float, str]:
    """
    Three-way capped position sizing.

    Constraint 1 — Vol-adjusted (inverse-vol weighting):
        Each position targets equal risk contribution to a portfolio vol goal.
        notional_vol = equity * (target_port_vol / max_positions) / stock_vol
        Higher-vol names get less notional, lower-vol names get more.

    Constraint 2 — ATR risk cap (per-trade loss cap):
        shares_atr = (equity * risk_pct) / (atr_stop_mult * atr)
        Caps maximum loss per trade when the ATR stop triggers.

    Constraint 3 — Notional cap (concentration limit):
        shares_notional = (equity * max_position_pct) / entry_price

    Final shares = min(all three), then floored by cash availability.
    Returns: (shares, stop_price, binding_constraint_name)
    """
    # Clamp vol for sizing (prevent runaway on low-vol names, floor extreme names)
    vol_clamped = max(
        config.V2_SIZING_VOL_FLOOR,
        min(stock_vol, config.V2_SIZING_VOL_CEILING),
    )

    # --- 1) Vol-adjusted notional ---
    vol_budget = config.V2_TARGET_PORTFOLIO_VOL / config.V2_MAX_POSITIONS
    notional_vol = equity * vol_budget / vol_clamped
    shares_vol = int(notional_vol / entry_price)

    # --- 2) ATR risk cap ---
    risk_per_share = config.V2_ATR_STOP_MULT * atr_val
    stop_price = entry_price - risk_per_share
    max_risk_eur = equity * (config.V2_RISK_PER_TRADE_PCT / 100)
    shares_atr = int(max_risk_eur / risk_per_share) if risk_per_share > 0 else 0

    # --- 3) Notional cap ---
    max_notional = equity * (config.V2_MAX_POSITION_PCT / 100)
    shares_notional = int(max_notional / entry_price)

    # Select minimum constraint + remember which one bound
    constraints = {
        "VOL": shares_vol,
        "ATR": shares_atr,
        "NOTIONAL": shares_notional,
    }
    binding, shares = min(constraints.items(), key=lambda kv: kv[1])

    # --- 4) Cash availability ---
    cost_needed = shares * entry_price + commission
    if cost_needed > available_cash:
        shares = int((available_cash - commission) / entry_price)
        binding = "CASH"

    return max(shares, 0), stop_price, binding


# ========================================================================== #
# Transaction cost model
# ========================================================================== #

def compute_trade_cost(
    shares: int,
    price: float,
    stock_vol: float,
    adv: float,
) -> tuple[float, dict]:
    """
    Rigorous per-trade cost model.

    Components (one-way):
      1) Commission:    fixed EUR per trade
      2) Half-spread:   half_spread_bps * notional
      3) Market impact: coeff * stock_vol * sqrt(shares / ADV) * notional
         (Almgren-Chriss square-root model)
      4) Slippage:      fixed bps buffer * notional

    Returns: (total_cost_eur, breakdown_dict)
    """
    notional = shares * price

    # 1) Commission
    comm = config.V2_COMMISSION_EUR

    # 2) Half-spread
    half_spread = notional * (config.V2_HALF_SPREAD_BPS / 10000)

    # 3) Market impact (sqrt model)
    if adv > 0 and stock_vol > 0:
        participation = shares / adv
        if participation > config.V2_MAX_PCT_OF_ADV / 100:
            participation = config.V2_MAX_PCT_OF_ADV / 100
        impact = config.V2_IMPACT_COEFF * stock_vol * np.sqrt(participation) * notional
    else:
        impact = 0.0

    # 4) Slippage
    slippage = notional * (config.V2_SLIPPAGE_BPS / 10000)

    total = comm + half_spread + impact + slippage

    breakdown = {
        "commission": comm,
        "half_spread": half_spread,
        "impact": impact,
        "slippage": slippage,
        "total": total,
        "total_bps": (total / notional * 10000) if notional > 0 else 0,
    }
    return total, breakdown


# ========================================================================== #
# Core backtest loop
# ========================================================================== #

def run_backtest_v2(
    prices: dict[str, pd.DataFrame],
    benchmark_close: pd.Series,
    start_date: str = "2010-01-01",
    end_date: str = "2026-12-31",
    initial_capital: float = 20000.0,
) -> StateV2:
    """Run the V2 backtest."""

    logger.info("Computing V2 signals for %d stocks...", len(prices))
    all_signals: dict[str, pd.DataFrame] = {}
    for ticker, df in prices.items():
        if len(df) < 252:
            continue
        try:
            all_signals[ticker] = compute_signals_v2(df)
        except Exception as e:
            logger.debug("Signal computation failed for %s: %s", ticker, e)
    logger.info("V2 signals computed for %d stocks", len(all_signals))

    logger.info("Computing cross-sectional momentum ranks...")
    xs_rank = compute_xs_mom_rank(all_signals)

    logger.info("Computing multi-layer macro regime...")
    regime = compute_macro_regime(benchmark_close, all_signals, xs_rank)

    # Dates
    all_dates = benchmark_close.index
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    trading_dates = all_dates[(all_dates >= start_ts) & (all_dates <= end_ts)]
    rebal_raw = pd.date_range(start=start_ts, end=end_ts, freq="W-FRI")
    rebal_dates = [
        trading_dates[trading_dates >= d][0]
        for d in rebal_raw
        if (trading_dates >= d).any()
    ]

    max_positions = config.V2_MAX_POSITIONS

    state = StateV2(cash=initial_capital)

    logger.info(
        "Running V2 backtest: %s to %s (%d rebalances)",
        start_date, end_date, len(rebal_dates),
    )

    for i, date in enumerate(rebal_dates):
        if i % 52 == 0:
            logger.info(
                "  %s — %d open, equity: %.0f",
                date.date(), len(state.open_positions),
                state.total_equity(_prices_on(all_signals, date)),
            )

        current_prices = _prices_on(all_signals, date)

        # Regime status
        regime_on = False
        if date in regime.index:
            regime_on = bool(regime.loc[date, "regime_on"])
        else:
            prior = regime.index[regime.index <= date]
            if len(prior) > 0:
                regime_on = bool(regime.loc[prior[-1], "regime_on"])

        # --- Exits ---
        to_close = []
        for pos in state.open_positions:
            if pos.ticker not in all_signals:
                continue
            sig = all_signals[pos.ticker]
            row = _row_on(sig, date)
            if row is None:
                continue
            price = float(row.get("close", 0))
            if price <= 0:
                continue

            if price > pos.highest_price:
                pos.highest_price = price
            gain_pct = (price / pos.entry_price - 1) * 100
            if gain_pct >= config.V2_PROFIT_TRAIL_THRESHOLD:
                pos.trailing_active = True

            exit_reason = ""
            exit_sma = row.get("exit_sma")

            if not pos.trailing_active and price <= pos.stop_price:
                exit_reason = "HARD_STOP"
            elif not regime_on:
                exit_reason = "REGIME_OFF"
            elif pd.notna(exit_sma) and price < float(exit_sma):
                exit_reason = "BELOW_EXIT_SMA"

            if exit_reason:
                adv_exit = row.get("adv_20", 0)
                if pd.isna(adv_exit):
                    adv_exit = 0.0
                hvol_exit = row.get("hvol_60", pos.hvol_60)
                if pd.isna(hvol_exit):
                    hvol_exit = pos.hvol_60
                exit_cost, exit_bd = compute_trade_cost(
                    shares=pos.shares,
                    price=price,
                    stock_vol=hvol_exit,
                    adv=float(adv_exit),
                )
                exit_price = price - exit_cost / pos.shares
                pos.exit_date = str(date.date())
                pos.exit_price = exit_price
                pos.exit_reason = exit_reason
                pos.exit_cost_bps = exit_bd["total_bps"]
                pos.pnl = (exit_price - pos.entry_price) * pos.shares
                pos.pnl_pct = (exit_price / pos.entry_price - 1) * 100
                pos.holding_days = (date - pd.Timestamp(pos.entry_date)).days
                to_close.append(pos)

        for pos in to_close:
            state.cash += pos.shares * pos.exit_price
            state.positions.remove(pos)
            state.closed_trades.append(pos)

        # --- Entries (only when regime is ON) ---
        if regime_on and len(state.open_positions) < max_positions:
            # Cross-sectional rank snapshot for this date
            if date in xs_rank.index:
                ranks_today = xs_rank.loc[date]
            else:
                prior = xs_rank.index[xs_rank.index <= date]
                if len(prior) == 0:
                    continue
                ranks_today = xs_rank.loc[prior[-1]]

            # Select top-N% of universe by momentum rank
            threshold = max(
                100 - config.V2_TOP_N_PCT, config.V2_MIN_MOM_RANK_PCT
            )

            candidates = []
            for ticker, sig in all_signals.items():
                if any(p.ticker == ticker for p in state.open_positions):
                    continue
                rank = ranks_today.get(ticker, np.nan)
                if pd.isna(rank) or rank < threshold:
                    continue
                row = _row_on(sig, date)
                if row is None:
                    continue

                # Gatekeepers (not ranking — selection is by xs-rank only)
                if not bool(row.get("above_200", False)):
                    continue
                if not bool(row.get("breakout", False)):
                    continue
                hvol = row.get("hvol_20", 0)
                if pd.isna(hvol) or hvol < config.V2_MIN_HVOL_PCT:
                    continue  # require high-volatility regime per-stock

                price = float(row.get("close", 0))
                atr_val = row.get("atr_14", 0)
                hvol_60 = row.get("hvol_60", np.nan)
                adv = row.get("adv_20", np.nan)
                if price <= 0 or pd.isna(atr_val) or atr_val <= 0:
                    continue
                if pd.isna(hvol_60) or hvol_60 <= 0:
                    continue
                if pd.isna(adv):
                    adv = 0.0

                candidates.append({
                    "ticker": ticker,
                    "price": price,
                    "atr": float(atr_val),
                    "rank": float(rank),
                    "hvol": float(hvol),
                    "hvol_60": float(hvol_60),
                    "adv": float(adv),
                })

            # Need minimum candidate depth — otherwise signal is too thin
            if len(candidates) < config.V2_MIN_CANDIDATES_PER_DATE:
                pass
            else:
                # Rank purely by cross-sectional momentum percentile
                candidates.sort(key=lambda c: c["rank"], reverse=True)

                slots = max_positions - len(state.open_positions)
                equity = state.total_equity(current_prices)

                for cand in candidates[:slots]:
                    raw_price = cand["price"]
                    atr_val = cand["atr"]

                    # Size first on raw price (conservative — cost comes off cash)
                    shares, stop, size_reason = vol_adjusted_shares(
                        equity=equity,
                        entry_price=raw_price,
                        atr_val=atr_val,
                        stock_vol=cand["hvol_60"],
                        available_cash=state.cash,
                        commission=config.V2_COMMISSION_EUR,
                    )
                    if shares <= 0:
                        continue

                    # Compute realistic entry cost
                    entry_cost, entry_bd = compute_trade_cost(
                        shares=shares,
                        price=raw_price,
                        stock_vol=cand["hvol_60"],
                        adv=cand["adv"],
                    )
                    entry_price = raw_price + entry_cost / shares  # effective entry
                    notional = shares * raw_price
                    if notional < config.V2_MIN_POSITION_EUR:
                        continue
                    total_outlay = notional + entry_cost
                    if total_outlay > state.cash:
                        shares = int((state.cash - entry_cost) / raw_price)
                        if shares <= 0:
                            continue
                        entry_cost, entry_bd = compute_trade_cost(
                            shares, raw_price, cand["hvol_60"], cand["adv"],
                        )
                        entry_price = raw_price + entry_cost / shares
                        total_outlay = shares * raw_price + entry_cost

                    state.cash -= total_outlay
                    trade = TradeV2(
                        ticker=cand["ticker"],
                        entry_date=str(date.date()),
                        entry_price=entry_price,
                        shares=shares,
                        stop_price=stop,
                        mom_rank=cand["rank"],
                        hvol_60=cand["hvol_60"],
                        size_reason=size_reason,
                        entry_cost_bps=entry_bd["total_bps"],
                        highest_price=entry_price,
                    )
                    state.positions.append(trade)

        # Record equity
        eq = state.total_equity(current_prices)
        state.equity_curve.append({
            "date": date,
            "equity": eq,
            "cash": state.cash,
            "positions": len(state.open_positions),
            "regime_on": regime_on,
        })

    # Close remaining positions at last price (with exit costs)
    last_date = trading_dates[-1] if len(trading_dates) > 0 else rebal_dates[-1]
    for pos in list(state.open_positions):
        if pos.ticker not in all_signals:
            continue
        sig = all_signals[pos.ticker]
        prior = sig.index[sig.index <= last_date]
        if len(prior) == 0:
            continue
        row = sig.loc[prior[-1]]
        price = float(row.get("close", pos.entry_price))
        adv_end = row.get("adv_20", 0)
        if pd.isna(adv_end):
            adv_end = 0.0
        exit_cost, exit_bd = compute_trade_cost(
            pos.shares, price, pos.hvol_60, float(adv_end),
        )
        exit_price = price - exit_cost / pos.shares if pos.shares > 0 else price
        pos.exit_date = str(last_date.date())
        pos.exit_price = exit_price
        pos.exit_reason = "END_OF_BACKTEST"
        pos.exit_cost_bps = exit_bd["total_bps"]
        pos.pnl = (exit_price - pos.entry_price) * pos.shares
        pos.pnl_pct = (exit_price / pos.entry_price - 1) * 100
        pos.holding_days = (last_date - pd.Timestamp(pos.entry_date)).days
        state.cash += pos.shares * exit_price
        state.positions.remove(pos)
        state.closed_trades.append(pos)

    return state


# ========================================================================== #
# Helpers
# ========================================================================== #

def _row_on(sig: pd.DataFrame, date: pd.Timestamp):
    if date in sig.index:
        return sig.loc[date]
    prior = sig.index[sig.index <= date]
    if len(prior) == 0:
        return None
    return sig.loc[prior[-1]]


def _prices_on(all_signals: dict, date: pd.Timestamp) -> dict[str, float]:
    out = {}
    for ticker, sig in all_signals.items():
        row = _row_on(sig, date)
        if row is None:
            continue
        p = row.get("close", 0)
        if pd.notna(p) and p > 0:
            out[ticker] = float(p)
    return out


# ========================================================================== #
# Reporting (minimal — same shape as V1 so results are comparable)
# ========================================================================== #

def summarize_v2(state: StateV2) -> dict:
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

    ann_vol = eq["returns"].std() * np.sqrt(52)
    sharpe = cagr / ann_vol if ann_vol > 0 else 0
    peak = eq["equity"].expanding().max()
    dd = (eq["equity"] - peak) / peak
    max_dd = dd.min()

    trades = state.closed_trades
    winners = [t for t in trades if t.pnl > 0]
    win_rate = len(winners) / len(trades) * 100 if trades else 0

    exit_reasons = {}
    size_reasons = {}
    for t in trades:
        exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1
        size_reasons[t.size_reason] = size_reasons.get(t.size_reason, 0) + 1

    avg_hvol = np.mean([t.hvol_60 for t in trades if t.hvol_60 > 0]) if trades else 0
    avg_entry_cost = np.mean([t.entry_cost_bps for t in trades]) if trades else 0
    avg_exit_cost = np.mean([t.exit_cost_bps for t in trades]) if trades else 0
    avg_round_trip = avg_entry_cost + avg_exit_cost

    return {
        "initial": initial,
        "final": final,
        "cagr_pct": cagr * 100,
        "ann_vol_pct": ann_vol * 100,
        "sharpe": sharpe,
        "max_dd_pct": max_dd * 100,
        "total_trades": len(trades),
        "win_rate_pct": win_rate,
        "regime_on_pct": eq["regime_on"].mean() * 100,
        "avg_entry_hvol_pct": avg_hvol * 100,
        "avg_entry_cost_bps": avg_entry_cost,
        "avg_exit_cost_bps": avg_exit_cost,
        "avg_round_trip_bps": avg_round_trip,
        "exit_reasons": exit_reasons,
        "size_reasons": size_reasons,
        "equity_curve": eq,
    }


def print_v2(s: dict) -> None:
    sep = "=" * 60
    print(f"\n{sep}\n  V2 BACKTEST RESULTS\n{sep}")
    print(f"  Initial:       EUR {s['initial']:>10,.0f}")
    print(f"  Final:         EUR {s['final']:>10,.0f}")
    print(f"  CAGR:          {s['cagr_pct']:>+10.1f}%")
    print(f"  Ann Vol:       {s['ann_vol_pct']:>10.1f}%")
    print(f"  Sharpe:        {s['sharpe']:>10.2f}")
    print(f"  Max DD:        {s['max_dd_pct']:>10.1f}%")
    print(f"  Trades:        {s['total_trades']:>10d}")
    print(f"  Win Rate:      {s['win_rate_pct']:>10.1f}%")
    print(f"  Regime ON:     {s['regime_on_pct']:>10.1f}%")
    print(f"  Avg Entry Vol: {s.get('avg_entry_hvol_pct', 0):>10.1f}%")
    print(f"\n  TRANSACTION COSTS (avg per trade)")
    print(f"    Entry:       {s.get('avg_entry_cost_bps', 0):>10.1f} bps")
    print(f"    Exit:        {s.get('avg_exit_cost_bps', 0):>10.1f} bps")
    print(f"    Round-trip:  {s.get('avg_round_trip_bps', 0):>10.1f} bps")
    print("  Exit Reasons:")
    for r, n in sorted(s["exit_reasons"].items(), key=lambda x: -x[1]):
        print(f"    {r:<22s} {n:>5d}")
    print("  Binding Sizing Constraint:")
    for r, n in sorted(s.get("size_reasons", {}).items(), key=lambda x: -x[1]):
        print(f"    {r:<22s} {n:>5d}")
    print()


# ========================================================================== #
# Main
# ========================================================================== #

def main():
    start = "2010-01-01"
    end = "2026-12-31"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--start" and i + 1 < len(args):
            start = args[i + 1]
        elif a == "--end" and i + 1 < len(args):
            end = args[i + 1]

    print("\n[1/3] Loading prices...")
    prices = load_prices()
    if not prices:
        print("ERROR: no price data. Run 'python -m dach_momentum data' first.")
        return
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    print("\n[2/3] Loading benchmark (^GDAXI)...")
    import yfinance as yf
    bench = yf.download("^GDAXI", start="2005-01-01",
                        auto_adjust=False, progress=False)
    if isinstance(bench.columns, pd.MultiIndex):
        bench.columns = bench.columns.get_level_values(0)
    bench_close = bench["Close"]

    print(f"\n[3/3] Running V2 backtest ({start} to {end})...")
    state = run_backtest_v2(
        prices=prices,
        benchmark_close=bench_close,
        start_date=start,
        end_date=end,
        initial_capital=20000.0,
    )
    s = summarize_v2(state)
    print_v2(s)

    if state.closed_trades:
        trades_df = pd.DataFrame([{
            "ticker": t.ticker,
            "entry_date": t.entry_date,
            "entry_price": round(t.entry_price, 2),
            "exit_date": t.exit_date,
            "exit_price": round(t.exit_price, 2),
            "shares": t.shares,
            "mom_rank": round(t.mom_rank, 1),
            "hvol_60": round(t.hvol_60, 3),
            "size_reason": t.size_reason,
            "entry_cost_bps": round(t.entry_cost_bps, 1),
            "exit_cost_bps": round(t.exit_cost_bps, 1),
            "pnl": round(t.pnl, 2),
            "pnl_pct": round(t.pnl_pct, 1),
            "holding_days": t.holding_days,
            "exit_reason": t.exit_reason,
        } for t in state.closed_trades])
        path = config.DATA_DIR / "backtest_v2_trades.csv"
        trades_df.to_csv(path, index=False)
        print(f"  Trade log: {path}")

    eq = s.get("equity_curve")
    if eq is not None:
        path = config.DATA_DIR / "backtest_v2_equity.csv"
        eq.to_csv(path)
        print(f"  Equity curve: {path}")


if __name__ == "__main__":
    main()
