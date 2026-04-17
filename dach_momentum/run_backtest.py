#!/usr/bin/env python3
"""
Backtest engine for the DACH momentum + quality strategy.

Simulates the full strategy historically:
- Weekly screening for trend template + momentum candidates
- Regime filter gates new entries
- Tiered exit logic (hard stop, regime-off 10w SMA, 30w SMA trailing)
- Position sizing with risk-per-trade targeting
- Transaction costs (DKB EUR 10/trade + spread estimate)
- Outputs equity curve, drawdown, trade log, and performance stats

Modes:
  --mode momentum     : trend template + momentum only (original)
  --mode canslim      : adds quality filters (volume, trend health, extension)
  --mode rich_quick   : aggressive concentrated breakout strategy
  --mode super_rich   : MAXIMUM AGGRESSION - 3 positions, strongest breakouts only
  --mode cash_machine : HIGH FREQUENCY - many trades, early profit-taking

Usage: python run_backtest.py
       python run_backtest.py --mode canslim
       python run_backtest.py --mode rich_quick
       python run_backtest.py --mode super_rich
       python run_backtest.py --mode cash_machine
       python run_backtest.py --mode all
       python run_backtest.py --start 2015-01-01 --end 2025-12-31
"""
import sys
sys.path.insert(0, ".")

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from dach_momentum import config
from dach_momentum.data import load_prices, print_data_freshness
from dach_momentum.signals import (
    sma, atr, rolling_high, rolling_low, bollinger_bandwidth,
    compute_regime, compute_breakout_signals,
)
from dach_momentum.patterns import compute_pattern_score

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ========================================================================== #
# Backtest data structures
# ========================================================================== #

@dataclass
class Trade:
    ticker: str
    entry_date: str
    entry_price: float
    shares: int
    stop_price: float
    exit_date: str = ""
    exit_price: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_days: int = 0
    highest_price: float = 0.0
    trailing_active: bool = False


@dataclass
class BacktestState:
    cash: float
    positions: list[Trade] = field(default_factory=list)
    closed_trades: list[Trade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)

    @property
    def open_positions(self):
        return [p for p in self.positions if not p.exit_date]

    def total_equity(self, prices: dict[str, float]) -> float:
        pos_value = sum(
            p.shares * prices.get(p.ticker, p.entry_price)
            for p in self.open_positions
        )
        return self.cash + pos_value


# ========================================================================== #
# Signal computation (inline, no dependency on saved signals)
# ========================================================================== #

def compute_stock_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all needed signals for one stock inline."""
    close = df["Close"]

    signals = pd.DataFrame(index=df.index)
    signals["close"] = close

    # Moving averages
    signals["sma_50"] = sma(close, 50)
    signals["sma_150"] = sma(close, 150)
    signals["sma_200"] = sma(close, 200)
    signals["sma_200_1m"] = signals["sma_200"].shift(21)

    # 52-week high/low
    signals["high_52w"] = rolling_high(close, 252)
    signals["low_52w"] = rolling_low(close, 252)

    # Trend template
    signals["tt_pass"] = (
        (close > signals["sma_150"]) &
        (close > signals["sma_200"]) &
        (signals["sma_150"] > signals["sma_200"]) &
        (signals["sma_200"] > signals["sma_200_1m"]) &
        (signals["sma_50"] > signals["sma_150"]) &
        (close > signals["sma_50"]) &
        (close >= signals["low_52w"] * config.TREND_52W_LOW_DISTANCE) &
        (close >= signals["high_52w"] * config.TREND_52W_HIGH_PROXIMITY)
    )

    # Momentum (12-1 month)
    close_12m = close.shift(252)
    close_1m = close.shift(21)
    signals["mom_12_1"] = close_1m / close_12m - 1.0

    # ATR for stop calculation
    signals["atr_14"] = atr(df, 14)

    # Exit SMAs
    signals["sma_30w"] = sma(close, 150)  # 30 weeks * 5 days
    signals["sma_10w"] = sma(close, 50)   # 10 weeks * 5 days

    # Volume analysis (S in CAN SLIM — supply/demand)
    if "Volume" in df.columns:
        vol = df["Volume"]
        signals["vol_50d"] = vol.rolling(50).mean()
        signals["vol_10d"] = vol.rolling(10).mean()

        # Volume trend: is recent volume above average?
        signals["vol_increasing"] = signals["vol_10d"] > signals["vol_50d"]

        # Up/Down volume ratio (20-day rolling)
        daily_return = close.pct_change()
        up_vol = vol.where(daily_return > 0, 0).rolling(20).sum()
        down_vol = vol.where(daily_return < 0, 0).rolling(20).sum()
        signals["up_down_vol_ratio"] = up_vol / down_vol.replace(0, np.nan)

        # Accumulation: up/down ratio > 1.2
        signals["accumulation"] = signals["up_down_vol_ratio"] > 1.2

    # Trend health signals (proxies for CAN SLIM quality)
    # These use only price data, so they're backtestable without fundamentals

    # 1. Price acceleration: is the rate of rise increasing?
    mom_3m = close / close.shift(63) - 1
    mom_6m = close / close.shift(126) - 1
    signals["price_accelerating"] = mom_3m > (mom_6m / 2)

    # 2. SMA spacing: healthy trends have well-separated SMAs
    #    (50 > 150 > 200 with gaps, not clustered together)
    if "sma_50" in signals.columns and "sma_200" in signals.columns:
        sma_spread = (signals["sma_50"] / signals["sma_200"] - 1) * 100
        signals["sma_spread_pct"] = sma_spread
        signals["healthy_spread"] = (sma_spread > 2) & (sma_spread < 30)

    # 3. Not over-extended: price shouldn't be too far above 200d SMA
    extension = (close / signals["sma_200"] - 1) * 100
    signals["extension_pct"] = extension
    signals["not_overextended"] = extension < 60  # <60% above 200d SMA

    # 4. Volatility contraction: Bollinger bandwidth declining
    signals["bb_width"] = bollinger_bandwidth(close, 20)
    bb_avg = signals["bb_width"].rolling(50).mean()
    signals["vol_contracting"] = signals["bb_width"] < bb_avg

    # Combined quality score (0-5 points, backtestable)
    quality_score = pd.Series(0, index=df.index, dtype=float)
    if "accumulation" in signals.columns:
        quality_score += signals["accumulation"].astype(float)
    quality_score += signals["price_accelerating"].astype(float)
    if "healthy_spread" in signals.columns:
        quality_score += signals["healthy_spread"].astype(float)
    quality_score += signals["not_overextended"].astype(float)
    quality_score += signals["vol_contracting"].astype(float)
    signals["quality_score"] = quality_score

    # Breakout signals (for "Get Rich Quick" strategy)
    breakout = compute_breakout_signals(df)
    for col in breakout.columns:
        if col not in signals.columns:
            signals[col] = breakout[col]

    return signals


# ========================================================================== #
# Core backtest logic
# ========================================================================== #

def run_backtest(
    prices: dict[str, pd.DataFrame],
    benchmark_close: pd.Series,
    start_date: str = "2010-01-01",
    end_date: str = "2026-12-31",
    initial_capital: float = 20000.0,
    max_positions: int = 10,
    rebalance_freq: str = "W-FRI",  # weekly on Fridays
    mode: str = "momentum",  # "momentum", "canslim", "rich_quick", "super_rich", "cash_machine"
) -> BacktestState:
    """Run the full backtest."""

    # Override position count per mode
    if mode == "rich_quick":
        max_positions = config.RQ_MAX_POSITIONS
    elif mode == "super_rich":
        max_positions = config.SR_MAX_POSITIONS
    elif mode == "cash_machine":
        max_positions = config.CM_MAX_POSITIONS

    # Compute signals for all stocks
    logger.info("Computing signals for %d stocks...", len(prices))
    all_signals: dict[str, pd.DataFrame] = {}
    for ticker, df in prices.items():
        if len(df) < 252:  # need at least 1 year
            continue
        try:
            all_signals[ticker] = compute_stock_signals(df)
        except Exception as e:
            logger.debug("Signal computation failed for %s: %s", ticker, e)

    logger.info("Signals computed for %d stocks", len(all_signals))

    # Compute regime
    regime = compute_regime(benchmark_close)

    # Get all rebalance dates
    all_dates = benchmark_close.index
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    mask = (all_dates >= start_ts) & (all_dates <= end_ts)
    trading_dates = all_dates[mask]

    # Weekly rebalance dates
    rebal_dates = pd.date_range(
        start=start_ts, end=end_ts, freq=rebalance_freq
    )
    # Snap to actual trading days
    rebal_dates = [
        trading_dates[trading_dates >= d][0]
        for d in rebal_dates
        if any(trading_dates >= d)
    ]

    state = BacktestState(cash=initial_capital)
    commission = config.COMMISSION_PER_TRADE_EUR
    spread_bps = config.ESTIMATED_SPREAD_BPS

    logger.info(
        "Running backtest: %s to %s (%d rebalance dates)",
        start_date, end_date, len(rebal_dates),
    )

    for i, date in enumerate(rebal_dates):
        if i % 52 == 0:  # log yearly
            logger.info("  %s — %d open positions, equity: %.0f",
                        date.date(), len(state.open_positions),
                        state.total_equity(_get_prices(all_signals, date)))

        # Get current prices
        current_prices = _get_prices(all_signals, date)

        # Get regime status
        regime_on = False
        if date in regime.index:
            regime_on = bool(regime.loc[date].get("regime_on", False))
        else:
            # Find nearest prior date
            prior = regime.index[regime.index <= date]
            if len(prior) > 0:
                regime_on = bool(regime.loc[prior[-1]].get("regime_on", False))

        # --- STEP 1: Check exits on existing positions ---
        positions_to_close = []
        for pos in state.open_positions:
            if pos.ticker not in all_signals:
                continue

            sig = all_signals[pos.ticker]
            if date not in sig.index:
                prior_dates = sig.index[sig.index <= date]
                if len(prior_dates) == 0:
                    continue
                row = sig.loc[prior_dates[-1]]
            else:
                row = sig.loc[date]

            price = float(row.get("close", 0))
            if price <= 0:
                continue

            # Update tracking
            if price > pos.highest_price:
                pos.highest_price = price
            gain_pct = (price / pos.entry_price - 1) * 100
            if mode == "super_rich":
                trail_threshold = config.SR_PROFIT_THRESHOLD_TO_TRAIL
            elif mode == "rich_quick":
                trail_threshold = config.RQ_PROFIT_THRESHOLD_TO_TRAIL
            elif mode == "cash_machine":
                trail_threshold = config.CM_PROFIT_THRESHOLD_TO_TRAIL
            else:
                trail_threshold = config.PROFIT_THRESHOLD_TO_TRAIL
            if gain_pct >= trail_threshold:
                pos.trailing_active = True

            sma_30w = row.get("sma_30w")
            sma_10w = row.get("sma_10w")

            exit_reason = ""

            # Exit 1: Hard stop
            if not pos.trailing_active and price <= pos.stop_price:
                exit_reason = "HARD_STOP"

            # Exit 2: Regime OFF + below 10w SMA
            elif not regime_on and pd.notna(sma_10w) and price < float(sma_10w):
                exit_reason = "REGIME_OFF_10W"

            # Exit 3: Trend exit — 10w SMA for cash_machine, 30w SMA for others
            elif mode == "cash_machine" and pd.notna(sma_10w) and price < float(sma_10w):
                exit_reason = "BELOW_10W_SMA"
            elif mode != "cash_machine" and pd.notna(sma_30w) and price < float(sma_30w):
                exit_reason = "BELOW_30W_SMA"

            if exit_reason:
                # Apply spread cost on exit
                exit_price = price * (1 - spread_bps / 10000)
                pos.exit_date = str(date.date())
                pos.exit_price = exit_price
                pos.exit_reason = exit_reason
                pos.pnl = (exit_price - pos.entry_price) * pos.shares - 2 * commission
                pos.pnl_pct = (exit_price / pos.entry_price - 1) * 100
                pos.holding_days = (date - pd.Timestamp(pos.entry_date)).days
                positions_to_close.append(pos)

        # Close positions
        for pos in positions_to_close:
            state.cash += pos.shares * pos.exit_price - commission
            state.positions.remove(pos)
            state.closed_trades.append(pos)

        # --- DRAWDOWN CIRCUIT BREAKER ---
        # If trailing 60-day portfolio return < -15%, pause new entries
        current_equity = state.total_equity(current_prices)
        circuit_breaker_active = False
        if len(state.equity_curve) >= config.DRAWDOWN_LOOKBACK_DAYS // 5:
            lookback_idx = min(
                config.DRAWDOWN_LOOKBACK_DAYS // 5,
                len(state.equity_curve),
            )
            past_equity = state.equity_curve[-lookback_idx]["equity"]
            if past_equity > 0:
                trailing_dd = (current_equity / past_equity - 1) * 100
                if trailing_dd < -config.DRAWDOWN_CIRCUIT_BREAKER_PCT:
                    circuit_breaker_active = True

        # --- STEP 2: Screen for new entries (only if regime ON + no circuit breaker) ---
        if regime_on and not circuit_breaker_active and len(state.open_positions) < max_positions:
            candidates = []
            for ticker, sig in all_signals.items():
                # Skip if already holding
                if any(p.ticker == ticker for p in state.open_positions):
                    continue

                if date not in sig.index:
                    prior_dates = sig.index[sig.index <= date]
                    if len(prior_dates) == 0:
                        continue
                    row = sig.loc[prior_dates[-1]]
                else:
                    row = sig.loc[date]

                if not row.get("tt_pass", False):
                    continue

                mom = row.get("mom_12_1", 0)
                if pd.isna(mom) or mom <= 0:
                    continue

                price = float(row.get("close", 0))
                atr_val = row.get("atr_14", 0)

                if price <= 0:
                    continue

                # Quality filter (CAN SLIM mode)
                quality = row.get("quality_score", 0)
                if pd.isna(quality):
                    quality = 0

                if mode == "canslim" and quality < 3:
                    continue  # reject low-quality candidates

                if mode == "cash_machine" and quality < config.CM_MIN_QUALITY_SCORE:
                    continue  # moderate quality bar for high-frequency mode

                # Rich Quick & Super Rich: aggressive breakout filters
                breakout_score = row.get("breakout_score", 0)
                if pd.isna(breakout_score):
                    breakout_score = 0
                near_high = bool(row.get("near_52w_high", False))
                vol_surge = bool(row.get("volume_surge", False))
                price_accel = bool(row.get("price_accelerating", False))
                rs_rising = bool(row.get("rs_rising", False))
                mom_rank = row.get("mom_rank_pct", 0)
                if pd.isna(mom_rank):
                    mom_rank = 0

                if mode == "rich_quick":
                    if not near_high:
                        continue  # must be near 52-week high
                    if not vol_surge:
                        continue  # must have volume confirmation
                    if quality < config.RQ_MIN_QUALITY_SCORE:
                        continue  # need decent trend quality

                # Super Rich: pure pattern recognition
                pattern_name = ""
                pattern_score = 0.0
                if mode == "super_rich":
                    # Need raw OHLCV up to current date for pattern detection
                    raw_df = prices.get(ticker)
                    if raw_df is None or len(raw_df) < 60:
                        continue
                    # Slice to current date
                    raw_df_as_of = raw_df.loc[raw_df.index <= date]
                    if len(raw_df_as_of) < 60:
                        continue
                    pattern_name, pattern_score, _ = compute_pattern_score(
                        raw_df_as_of.tail(200)
                    )
                    if pattern_score < config.SR_MIN_PATTERN_SCORE:
                        continue

                candidates.append({
                    "ticker": ticker,
                    "price": price,
                    "mom": mom,
                    "atr": float(atr_val) if pd.notna(atr_val) else None,
                    "quality": float(quality),
                    "breakout_score": float(breakout_score),
                    "pattern_name": pattern_name,
                    "pattern_score": float(pattern_score),
                })

            # Rank candidates
            if mode == "super_rich":
                # Rank by pattern score (pure technical pattern detection)
                candidates.sort(
                    key=lambda x: x.get("pattern_score", 0),
                    reverse=True,
                )
            elif mode == "rich_quick":
                # Rank by breakout score (composite of proximity, volume, accel)
                candidates.sort(
                    key=lambda x: x.get("breakout_score", 0),
                    reverse=True,
                )
            elif mode == "canslim":
                # Weight: 60% momentum + 40% quality
                candidates.sort(
                    key=lambda x: x["mom"] * 0.6 + x.get("quality", 0) / 5 * 0.4,
                    reverse=True,
                )
            else:
                candidates.sort(key=lambda x: x["mom"], reverse=True)
            slots = max_positions - len(state.open_positions)

            for cand in candidates[:slots]:
                entry_price = cand["price"] * (1 + spread_bps / 10000)  # spread cost

                # Calculate stop — tighter for aggressive modes
                atr_val = cand["atr"]
                if mode == "super_rich":
                    pct_stop = entry_price * (1 - config.SR_INITIAL_HARD_STOP_PCT / 100)
                    if atr_val and atr_val > 0:
                        atr_stop = entry_price - config.SR_HARD_STOP_ATR_MULT * atr_val
                        floor = entry_price * (1 - config.SR_HARD_STOP_CEILING_PCT / 100)
                        stop = max(min(pct_stop, atr_stop), floor)
                    else:
                        stop = pct_stop
                elif mode == "rich_quick":
                    pct_stop = entry_price * (1 - config.RQ_INITIAL_HARD_STOP_PCT / 100)
                    if atr_val and atr_val > 0:
                        atr_stop = entry_price - config.RQ_HARD_STOP_ATR_MULT * atr_val
                        floor = entry_price * (1 - config.RQ_HARD_STOP_CEILING_PCT / 100)
                        stop = max(min(pct_stop, atr_stop), floor)
                    else:
                        stop = pct_stop
                elif mode == "cash_machine":
                    pct_stop = entry_price * (1 - config.CM_INITIAL_HARD_STOP_PCT / 100)
                    if atr_val and atr_val > 0:
                        atr_stop = entry_price - config.CM_HARD_STOP_ATR_MULT * atr_val
                        floor = entry_price * (1 - config.CM_HARD_STOP_CEILING_PCT / 100)
                        stop = max(min(pct_stop, atr_stop), floor)
                    else:
                        stop = pct_stop
                else:
                    pct_stop = entry_price * (1 - config.INITIAL_HARD_STOP_PCT / 100)
                    if atr_val and atr_val > 0:
                        atr_stop = entry_price - config.INITIAL_HARD_STOP_ATR_MULT * atr_val
                        floor = entry_price * (1 - config.HARD_STOP_CEILING_PCT / 100)
                        stop = max(min(pct_stop, atr_stop), floor)
                    else:
                        stop = pct_stop

                # Position sizing — more aggressive for rich_quick / super_rich
                risk_per_share = entry_price - stop
                if risk_per_share <= 0:
                    continue

                equity = state.total_equity(current_prices)
                if mode == "super_rich":
                    max_risk = equity * (config.SR_RISK_PER_TRADE_PCT / 100)
                    shares = int(max_risk / risk_per_share)
                    max_pos_value = equity * (config.SR_MAX_POSITION_PCT / 100)
                elif mode == "rich_quick":
                    max_risk = equity * (config.RQ_RISK_PER_TRADE_PCT / 100)
                    shares = int(max_risk / risk_per_share)
                    max_pos_value = equity * (config.RQ_MAX_POSITION_PCT / 100)
                elif mode == "cash_machine":
                    max_risk = equity * (config.CM_RISK_PER_TRADE_PCT / 100)
                    shares = int(max_risk / risk_per_share)
                    max_pos_value = equity * (config.CM_MAX_POSITION_PCT / 100)
                else:
                    max_risk = equity * (config.RISK_PER_TRADE_PCT / 100)
                    shares = int(max_risk / risk_per_share)
                    max_pos_value = equity * (config.MAX_POSITION_PCT / 100)
                shares = min(shares, int(max_pos_value / entry_price))

                if shares <= 0:
                    continue

                cost = shares * entry_price + commission
                if cost > state.cash:
                    shares = int((state.cash - commission) / entry_price)
                    if shares <= 0:
                        continue

                # Execute entry
                state.cash -= shares * entry_price + commission
                trade = Trade(
                    ticker=cand["ticker"],
                    entry_date=str(date.date()),
                    entry_price=entry_price,
                    shares=shares,
                    stop_price=stop,
                    highest_price=entry_price,
                )
                state.positions.append(trade)

        # --- Record equity ---
        eq = state.total_equity(current_prices)
        state.equity_curve.append({
            "date": date,
            "equity": eq,
            "cash": state.cash,
            "positions": len(state.open_positions),
            "regime_on": regime_on,
            "circuit_breaker": circuit_breaker_active,
        })

    # Close any remaining positions at last price
    last_date = trading_dates[-1] if len(trading_dates) > 0 else rebal_dates[-1]
    for pos in list(state.open_positions):
        if pos.ticker in all_signals:
            sig = all_signals[pos.ticker]
            prior = sig.index[sig.index <= last_date]
            if len(prior) > 0:
                price = float(sig.loc[prior[-1]].get("close", pos.entry_price))
                pos.exit_date = str(last_date.date())
                pos.exit_price = price
                pos.exit_reason = "END_OF_BACKTEST"
                pos.pnl = (price - pos.entry_price) * pos.shares - 2 * commission
                pos.pnl_pct = (price / pos.entry_price - 1) * 100
                pos.holding_days = (last_date - pd.Timestamp(pos.entry_date)).days
                state.cash += pos.shares * price
                state.positions.remove(pos)
                state.closed_trades.append(pos)

    return state


def _get_prices(all_signals: dict, date: pd.Timestamp) -> dict[str, float]:
    """Get current prices for all stocks on a given date."""
    prices = {}
    for ticker, sig in all_signals.items():
        if date in sig.index:
            p = sig.loc[date].get("close", 0)
        else:
            prior = sig.index[sig.index <= date]
            if len(prior) > 0:
                p = sig.loc[prior[-1]].get("close", 0)
            else:
                continue
        if pd.notna(p) and p > 0:
            prices[ticker] = float(p)
    return prices


# ========================================================================== #
# Performance analytics
# ========================================================================== #

def compute_performance(state: BacktestState) -> dict:
    """Compute comprehensive performance metrics."""
    eq = pd.DataFrame(state.equity_curve)
    if eq.empty:
        return {}

    eq["date"] = pd.to_datetime(eq["date"])
    eq = eq.set_index("date")
    eq["returns"] = eq["equity"].pct_change()

    # Basic metrics
    initial = eq["equity"].iloc[0]
    final = eq["equity"].iloc[-1]
    years = (eq.index[-1] - eq.index[0]).days / 365.25

    cagr = (final / initial) ** (1 / years) - 1 if years > 0 else 0
    total_return = final / initial - 1

    # Volatility and Sharpe
    ann_vol = eq["returns"].std() * np.sqrt(52)  # weekly data
    sharpe = cagr / ann_vol if ann_vol > 0 else 0
    sortino_denom = eq["returns"][eq["returns"] < 0].std() * np.sqrt(52)
    sortino = cagr / sortino_denom if sortino_denom > 0 else 0

    # Drawdown
    peak = eq["equity"].expanding().max()
    drawdown = (eq["equity"] - peak) / peak
    max_dd = drawdown.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    # Trade statistics
    trades = state.closed_trades
    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]

    win_rate = len(winners) / len(trades) * 100 if trades else 0
    avg_win = np.mean([t.pnl_pct for t in winners]) if winners else 0
    avg_loss = np.mean([t.pnl_pct for t in losers]) if losers else 0
    profit_factor = (
        sum(t.pnl for t in winners) / abs(sum(t.pnl for t in losers))
        if losers and sum(t.pnl for t in losers) != 0 else float("inf")
    )
    avg_hold = np.mean([t.holding_days for t in trades]) if trades else 0

    # Exit reason breakdown
    exit_reasons = {}
    for t in trades:
        exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

    # Regime and circuit breaker statistics
    regime_on_pct = eq["regime_on"].mean() * 100
    cb_pct = eq["circuit_breaker"].mean() * 100 if "circuit_breaker" in eq.columns else 0.0
    cb_weeks = int(eq["circuit_breaker"].sum()) if "circuit_breaker" in eq.columns else 0

    return {
        "initial_capital": initial,
        "final_equity": final,
        "total_return_pct": total_return * 100,
        "cagr_pct": cagr * 100,
        "ann_volatility_pct": ann_vol * 100,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown_pct": max_dd * 100,
        "calmar_ratio": calmar,
        "total_trades": len(trades),
        "winners": len(winners),
        "losers": len(losers),
        "win_rate_pct": win_rate,
        "avg_win_pct": avg_win,
        "avg_loss_pct": avg_loss,
        "profit_factor": profit_factor,
        "avg_holding_days": avg_hold,
        "exit_reasons": exit_reasons,
        "regime_on_pct": regime_on_pct,
        "circuit_breaker_pct": cb_pct,
        "circuit_breaker_weeks": cb_weeks,
        "equity_curve": eq,
    }


def print_performance(perf: dict) -> None:
    """Print backtest results."""
    sep = "=" * 60
    print(f"\n{sep}")
    print("  BACKTEST RESULTS")
    print(sep)

    print(f"\n  RETURNS")
    print(f"    Initial Capital:   EUR {perf['initial_capital']:>10,.0f}")
    print(f"    Final Equity:      EUR {perf['final_equity']:>10,.0f}")
    print(f"    Total Return:      {perf['total_return_pct']:>+10.1f}%")
    print(f"    CAGR:              {perf['cagr_pct']:>+10.1f}%")

    print(f"\n  RISK")
    print(f"    Annual Volatility: {perf['ann_volatility_pct']:>10.1f}%")
    print(f"    Max Drawdown:      {perf['max_drawdown_pct']:>10.1f}%")
    print(f"    Sharpe Ratio:      {perf['sharpe_ratio']:>10.2f}")
    print(f"    Sortino Ratio:     {perf['sortino_ratio']:>10.2f}")
    print(f"    Calmar Ratio:      {perf['calmar_ratio']:>10.2f}")

    print(f"\n  TRADES")
    print(f"    Total Trades:      {perf['total_trades']:>10d}")
    print(f"    Winners:           {perf['winners']:>10d}")
    print(f"    Losers:            {perf['losers']:>10d}")
    print(f"    Win Rate:          {perf['win_rate_pct']:>10.1f}%")
    print(f"    Avg Win:           {perf['avg_win_pct']:>+10.1f}%")
    print(f"    Avg Loss:          {perf['avg_loss_pct']:>+10.1f}%")
    print(f"    Profit Factor:     {perf['profit_factor']:>10.2f}")
    print(f"    Avg Holding:       {perf['avg_holding_days']:>10.0f} days")

    print(f"\n  EXIT REASONS")
    for reason, count in sorted(perf["exit_reasons"].items(),
                                 key=lambda x: -x[1]):
        print(f"    {reason:<25s} {count:>5d}")

    print(f"\n  REGIME")
    print(f"    Time in bullish regime: {perf['regime_on_pct']:.1f}%")
    print(f"    Circuit breaker active: {perf['circuit_breaker_pct']:.1f}% "
          f"({perf['circuit_breaker_weeks']} weeks)")

    # Annual returns
    eq = perf["equity_curve"]
    print(f"\n  ANNUAL RETURNS")
    for year in sorted(eq.index.year.unique()):
        year_data = eq[eq.index.year == year]
        if len(year_data) >= 2:
            yr_ret = (year_data["equity"].iloc[-1] /
                      year_data["equity"].iloc[0] - 1) * 100
            print(f"    {year}:  {yr_ret:>+8.1f}%")

    print()


# ========================================================================== #
# Main
# ========================================================================== #

def main():
    print_data_freshness()

    # Parse args
    start = "2010-01-01"
    end = "2026-12-31"
    mode = "both"  # default: run both and compare
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--start" and i + 1 < len(args):
            start = args[i + 1]
        elif arg == "--end" and i + 1 < len(args):
            end = args[i + 1]
        elif arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]

    # Load prices
    print("\n[1/3] Loading price data...")
    prices = load_prices()
    if not prices:
        print("ERROR: No price data. Run 'python -m dach_momentum data' first.")
        return

    # Flatten MultiIndex
    for t in prices:
        if isinstance(prices[t].columns, pd.MultiIndex):
            prices[t].columns = prices[t].columns.get_level_values(0)

    logger.info("Loaded %d tickers", len(prices))

    # Load benchmark
    print("\n[2/3] Loading benchmark...")
    import yfinance as yf
    bench = yf.download("^GDAXI", start="2005-01-01",
                        auto_adjust=False, progress=False)
    if isinstance(bench.columns, pd.MultiIndex):
        bench.columns = bench.columns.get_level_values(0)
    bench_close = bench["Close"]
    logger.info("Benchmark: %d rows", len(bench_close))

    # Run backtest(s)
    if mode == "both":
        modes_to_run = ["momentum", "canslim"]
    elif mode == "all":
        modes_to_run = ["momentum", "canslim", "rich_quick", "super_rich", "cash_machine"]
    else:
        modes_to_run = [mode]
    all_results = {}

    for run_mode in modes_to_run:
        print(f"\n[3/3] Running backtest: {run_mode.upper()} mode ({start} to {end})...")
        state = run_backtest(
            prices=prices,
            benchmark_close=bench_close,
            start_date=start,
            end_date=end,
            initial_capital=20000.0,
            max_positions=10,
            mode=run_mode,
        )

        perf = compute_performance(state)
        all_results[run_mode] = perf
        print_performance(perf)

        # Save trade log
        suffix = f"_{run_mode}" if len(modes_to_run) > 1 else ""
        if state.closed_trades:
            trades_df = pd.DataFrame([{
                "ticker": t.ticker,
                "entry_date": t.entry_date,
                "entry_price": round(t.entry_price, 2),
                "exit_date": t.exit_date,
                "exit_price": round(t.exit_price, 2),
                "shares": t.shares,
                "pnl": round(t.pnl, 2),
                "pnl_pct": round(t.pnl_pct, 1),
                "holding_days": t.holding_days,
                "exit_reason": t.exit_reason,
            } for t in state.closed_trades])
            trades_path = config.DATA_DIR / f"backtest_trades{suffix}.csv"
            trades_df.to_csv(trades_path, index=False)
            print(f"  Trade log saved to: {trades_path}")

        eq = perf.get("equity_curve")
        if eq is not None:
            eq_path = config.DATA_DIR / f"backtest_equity{suffix}.csv"
            eq.to_csv(eq_path)
            print(f"  Equity curve saved to: {eq_path}")

    # Side-by-side comparison if multiple modes ran
    if len(all_results) >= 2:
        sep = "=" * 76
        print(f"\n{sep}")
        print("  STRATEGY COMPARISON")
        print(sep)

        mode_names = list(all_results.keys())
        mode_labels = {
            "momentum": "Momentum",
            "canslim": "CAN SLIM",
            "rich_quick": "Rich Quick",
            "super_rich": "Super Rich",
            "cash_machine": "Cash Machine",
        }

        metrics = [
            ("CAGR", "cagr_pct", True),
            ("Max Drawdown", "max_drawdown_pct", False),
            ("Sharpe", "sharpe_ratio", True),
            ("Sortino", "sortino_ratio", True),
            ("Total Trades", "total_trades", None),
            ("Win Rate", "win_rate_pct", True),
            ("Avg Win", "avg_win_pct", True),
            ("Avg Loss", "avg_loss_pct", False),
            ("Profit Factor", "profit_factor", True),
            ("Calmar", "calmar_ratio", True),
        ]

        # Print header
        header = f"  {'Metric':<20}"
        divider = f"  {'─'*20}"
        for mn in mode_names:
            header += f" {mode_labels.get(mn, mn):>12}"
            divider += f" {'─'*12}"
        header += f"  {'Best':>12}"
        divider += f"  {'─'*12}"
        print(f"\n{header}")
        print(divider)

        for label, key, higher_is_better in metrics:
            vals = {}
            line = f"  {label:<20}"
            for mn in mode_names:
                v = all_results[mn].get(key, 0)
                vals[mn] = v
                if key in ("total_trades", ):
                    line += f" {v:>12d}" if isinstance(v, int) else f" {v:>12.0f}"
                elif key in ("sharpe_ratio", "sortino_ratio", "profit_factor", "calmar_ratio"):
                    line += f" {v:>12.2f}"
                else:
                    line += f" {v:>+11.1f}%"

            # Determine best
            if higher_is_better is None:
                best = "---"
            elif higher_is_better:
                best_mn = max(vals, key=vals.get)
                best = mode_labels.get(best_mn, best_mn)
            else:
                # For drawdown/loss: less negative is better (higher value)
                best_mn = max(vals, key=vals.get)
                best = mode_labels.get(best_mn, best_mn)

            line += f"  {best:>12}"
            print(line)

        print()


if __name__ == "__main__":
    main()
