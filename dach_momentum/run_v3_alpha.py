#!/usr/bin/env python3
"""
V3 Alpha-Ensemble — Market-Neutral Long/Short Equity Strategy.

Institutional-grade, fully vectorized daily backtesting pipeline combining:
  A. Microstructure Filter: ADV liquidity gate (bottom 10% excluded)
  B. Alpha Engine: Cross-sectional multi-factor ranking (RSI + RoC + MDD)
  C. Tactical Timing: RSI debouncing (cancel exhausted entries)
  D. Regime Filter: NATR stress indicator with 50% deleveraging

All signals computed at T, execution at T+1. 10 bps round-turn costs.
Newey-West HAC t-statistics with Harvey (2017) threshold check.
"""
import sys
sys.path.insert(0, ".")

import logging
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


# ========================================================================== #
# 1. DataProcessor — Indicators & Microstructure Filter
# ========================================================================== #

class DataProcessor:
    """Computes all raw indicators and the ADV liquidity filter."""

    def __init__(self, close: pd.DataFrame, volume: pd.DataFrame):
        """
        Args:
            close: DataFrame of adjusted close prices (Date x Ticker).
            volume: DataFrame of daily volume (Date x Ticker).
        """
        self.close = close.astype(float)
        self.volume = volume.astype(float)

    def compute_adv_filter(self, window: int = 30, bottom_pct: float = 0.10) -> pd.DataFrame:
        """
        ADV liquidity gate. Returns boolean mask (True = liquid enough).
        Bottom `bottom_pct` of the universe by 30-day ADDV excluded each day.
        """
        addv = (self.close * self.volume).rolling(window, min_periods=window).mean()
        threshold = addv.quantile(bottom_pct, axis=1)
        return addv.ge(threshold, axis=0)

    def compute_rsi(self, window: int = 14) -> pd.DataFrame:
        """Wilder's RSI, fully vectorized across all tickers."""
        delta = self.close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        alpha = 1.0 / window
        avg_gain = gain.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100.0 - 100.0 / (1.0 + rs)

    def compute_roc(self, window: int = 10) -> pd.DataFrame:
        """Rate of Change (%)."""
        return self.close.pct_change(window) * 100.0

    def compute_mdd_252(self) -> pd.DataFrame:
        """Maximum Drawdown over trailing 252 trading days."""
        rolling_max = self.close.rolling(252, min_periods=252).max()
        dd = self.close / rolling_max - 1.0
        return dd.rolling(252, min_periods=252).min()

    def compute_natr(self, high: pd.DataFrame, low: pd.DataFrame,
                     window: int = 14) -> pd.Series:
        """
        Normalized ATR for a single series (market proxy).
        Expects single-column DataFrames or Series for high/low/close.
        Returns Series.
        """
        close = self.close.iloc[:, 0] if isinstance(self.close, pd.DataFrame) and self.close.shape[1] == 1 else self.close
        h = high.iloc[:, 0] if isinstance(high, pd.DataFrame) and high.shape[1] == 1 else high
        l = low.iloc[:, 0] if isinstance(low, pd.DataFrame) and low.shape[1] == 1 else low

        prev_close = close.shift(1)
        tr = pd.concat([
            h - l,
            (h - prev_close).abs(),
            (l - prev_close).abs(),
        ], axis=1).max(axis=1)
        atr_val = tr.ewm(span=window, min_periods=window, adjust=False).mean()
        return atr_val / close

    def build(self, high: pd.DataFrame = None, low: pd.DataFrame = None,
              proxy_ticker: str = "SPY") -> dict:
        """Compute all indicators. Returns dict of DataFrames/Series."""
        logger.info("Computing indicators for %d tickers, %d days...",
                    self.close.shape[1], self.close.shape[0])

        indicators = {
            "close": self.close,
            "adv_mask": self.compute_adv_filter(),
            "rsi_14": self.compute_rsi(14),
            "roc_10": self.compute_roc(10),
            "mdd_252": self.compute_mdd_252(),
        }

        if proxy_ticker in self.close.columns:
            proxy_close = self.close[[proxy_ticker]]
            proxy_high = high[[proxy_ticker]] if high is not None and proxy_ticker in high.columns else proxy_close
            proxy_low = low[[proxy_ticker]] if low is not None and proxy_ticker in low.columns else proxy_close
            dp_proxy = DataProcessor(proxy_close, self.volume[[proxy_ticker]] if proxy_ticker in self.volume.columns else proxy_close * 0 + 1)
            indicators["natr_proxy"] = dp_proxy.compute_natr(proxy_high, proxy_low)
        else:
            logger.warning("Proxy ticker %s not in universe — NATR regime filter disabled.", proxy_ticker)
            indicators["natr_proxy"] = None

        logger.info("Indicators computed.")
        return indicators


# ========================================================================== #
# 2. AlphaEngine — Cross-Sectional Multi-Factor Ranking
# ========================================================================== #

class AlphaEngine:
    """
    Theorem 6: Monthly cross-sectional ranking.
    Composite = 1/3 Rank(RSI) + 1/3 Rank(RoC) + 1/3 Rank(-MDD).
    Long top quartile, short bottom quartile.
    """

    def __init__(self, rebalance_days: int = 20):
        self.rebalance_days = rebalance_days

    def compute_composite(
        self,
        rsi: pd.DataFrame,
        roc: pd.DataFrame,
        mdd: pd.DataFrame,
        adv_mask: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Cross-sectional percentile ranking, masked by ADV liquidity.
        Returns composite score DataFrame (Date x Ticker), NaN where illiquid.
        """
        rsi_m = rsi.where(adv_mask)
        roc_m = roc.where(adv_mask)
        mdd_m = (-mdd).where(adv_mask)  # invert: smaller DD = higher rank

        rank_rsi = rsi_m.rank(axis=1, pct=True)
        rank_roc = roc_m.rank(axis=1, pct=True)
        rank_mdd = mdd_m.rank(axis=1, pct=True)

        return (rank_rsi + rank_roc + rank_mdd) / 3.0

    def generate_raw_weights(self, composite: pd.DataFrame) -> pd.DataFrame:
        """
        Long top 25%, short bottom 25%, equal-weight within legs.
        Rebalance every `rebalance_days` trading days.
        Returns target weight matrix (Date x Ticker).
        """
        n_dates = len(composite)
        rebal_idx = list(range(0, n_dates, self.rebalance_days))

        # Build weight snapshots at each rebalance
        weight_snapshots = {}
        for idx in rebal_idx:
            row = composite.iloc[idx]
            valid = row.dropna()
            snapshot = pd.Series(0.0, index=composite.columns)
            if len(valid) >= 4:
                q25 = valid.quantile(0.25)
                q75 = valid.quantile(0.75)
                longs = valid[valid >= q75].index
                shorts = valid[valid <= q25].index
                if len(longs) > 0:
                    snapshot[longs] = 1.0 / len(longs)
                if len(shorts) > 0:
                    snapshot[shorts] = -1.0 / len(shorts)
            weight_snapshots[composite.index[idx]] = snapshot

        # Build full weight matrix via reindex + ffill
        snap_df = pd.DataFrame(weight_snapshots).T
        weights = snap_df.reindex(composite.index).ffill().fillna(0.0)

        return weights


# ========================================================================== #
# 3. RiskManager — Tactical Timing + Regime Filter
# ========================================================================== #

class RiskManager:
    """
    Theorem 4 (RSI Debouncing) + Theorem 7 (NATR Stress Regime).
    """

    def __init__(
        self,
        rsi_panic: float = 28.0,
        rsi_euphoria: float = 72.0,
        natr_percentile: float = 0.90,
        natr_lookback: int = 252,
        stress_delever: float = 0.50,
    ):
        self.rsi_panic = rsi_panic
        self.rsi_euphoria = rsi_euphoria
        self.natr_percentile = natr_percentile
        self.natr_lookback = natr_lookback
        self.stress_delever = stress_delever

    def apply_rsi_debounce(
        self, weights: pd.DataFrame, rsi: pd.DataFrame,
    ) -> pd.DataFrame:
        """Cancel long if RSI < panic, cancel short if RSI > euphoria."""
        w = weights.copy()
        # Cancel longs in panic
        w[(w > 0) & (rsi < self.rsi_panic)] = 0.0
        # Cancel shorts in euphoria
        w[(w < 0) & (rsi > self.rsi_euphoria)] = 0.0
        return w

    def compute_stress_regime(self, natr: pd.Series) -> pd.Series:
        """Returns boolean Series: True when NATR > rolling 90th percentile."""
        if natr is None:
            return pd.Series(False, index=pd.RangeIndex(0))
        threshold = natr.rolling(self.natr_lookback, min_periods=self.natr_lookback).quantile(self.natr_percentile)
        return natr > threshold

    def apply_regime_filter(
        self, weights: pd.DataFrame, stress: pd.Series,
    ) -> pd.DataFrame:
        """Deleverage by 50% during stress regimes."""
        w = weights.copy()
        stress_aligned = stress.reindex(w.index).fillna(False)
        w.loc[stress_aligned] *= self.stress_delever
        return w


# ========================================================================== #
# 4. BacktestEngine — T+1 Execution, Transaction Costs, Returns
# ========================================================================== #

class BacktestEngine:
    """
    Applies look-ahead bias prevention (T+1 shift), transaction cost
    deduction, and computes daily portfolio returns.
    """

    def __init__(self, cost_bps: float = 10.0):
        self.cost_bps = cost_bps

    def run(
        self,
        close: pd.DataFrame,
        signal_weights: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Args:
            close: Adjusted close prices (Date x Ticker).
            signal_weights: Target weights computed at T (Date x Ticker).

        Returns:
            DataFrame with columns: gross_return, cost, net_return, cumulative.
        """
        # T+1 execution: shift weights forward by 1 day
        exec_weights = signal_weights.shift(1).fillna(0.0)

        # Forward returns: from T to T+1
        fwd_returns = close.pct_change().shift(-1)

        # Gross daily portfolio return
        gross = (exec_weights * fwd_returns).sum(axis=1)

        # Transaction costs: proportional to weight turnover
        turnover = exec_weights.diff().abs().sum(axis=1)
        cost = turnover * (self.cost_bps / 10000.0)

        # Net return
        net = gross - cost

        result = pd.DataFrame({
            "gross_return": gross,
            "cost": cost,
            "net_return": net,
        }, index=close.index)

        result["cumulative"] = (1.0 + result["net_return"]).cumprod()

        return result


# ========================================================================== #
# 5. Econometrics — Newey-West HAC t-statistic
# ========================================================================== #

class Econometrics:
    """Statistical validation with Newey-West HAC standard errors."""

    @staticmethod
    def newey_west_tstat(returns: pd.Series, max_lags: int = None) -> dict:
        """
        Compute Newey-West HAC t-statistic for mean excess return.
        Harvey (2017) threshold: t > 3.0 for new factors.
        """
        try:
            import statsmodels.api as sm
        except ImportError:
            logger.error("statsmodels not installed — skipping econometrics.")
            return {"mean": 0, "tstat": 0, "pvalue": 1, "nw_se": 0, "n_obs": 0}

        clean = returns.dropna()
        if len(clean) < 30:
            return {"mean": 0, "tstat": 0, "pvalue": 1, "nw_se": 0, "n_obs": len(clean)}

        n = len(clean)
        if max_lags is None:
            max_lags = int(np.floor(4 * (n / 100) ** (2 / 9)))

        y = clean.values
        X = np.ones((n, 1))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": max_lags})

        return {
            "mean_daily": model.params[0],
            "mean_annual": model.params[0] * 252,
            "tstat": model.tvalues[0],
            "pvalue": model.pvalues[0],
            "nw_se": model.bse[0],
            "n_obs": n,
            "max_lags": max_lags,
        }


# ========================================================================== #
# Pipeline Orchestrator
# ========================================================================== #

def run_v3_pipeline(
    close: pd.DataFrame,
    volume: pd.DataFrame,
    high: pd.DataFrame = None,
    low: pd.DataFrame = None,
    proxy_ticker: str = "SPY",
) -> dict:
    """
    End-to-end V3 Alpha-Ensemble pipeline.
    Returns dict with results DataFrame, weights, stats, and diagnostics.
    """
    # --- Stage 1: Data Processing ---
    dp = DataProcessor(close, volume)
    indicators = dp.build(high=high, low=low, proxy_ticker=proxy_ticker)

    # --- Stage 2: Alpha Engine ---
    alpha = AlphaEngine(rebalance_days=20)
    composite = alpha.compute_composite(
        indicators["rsi_14"],
        indicators["roc_10"],
        indicators["mdd_252"],
        indicators["adv_mask"],
    )
    raw_weights = alpha.generate_raw_weights(composite)

    # --- Stage 3: Risk Management ---
    rm = RiskManager()
    debounced = rm.apply_rsi_debounce(raw_weights, indicators["rsi_14"])

    natr = indicators.get("natr_proxy")
    stress = rm.compute_stress_regime(natr)
    final_weights = rm.apply_regime_filter(debounced, stress)

    # --- Stage 4: Backtest ---
    engine = BacktestEngine(cost_bps=10.0)
    results = engine.run(close, final_weights)

    # --- Stage 5: Econometrics ---
    econ = Econometrics()
    stats = econ.newey_west_tstat(results["net_return"])

    # --- Diagnostics ---
    net = results["net_return"].dropna()
    ann_ret = net.mean() * 252
    ann_vol = net.std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    cum = results["cumulative"].dropna()
    peak = cum.expanding().max()
    max_dd = ((cum - peak) / peak).min()

    total_cost = results["cost"].sum()
    turnover_avg = final_weights.diff().abs().sum(axis=1).mean()

    n_long = (final_weights > 0).sum(axis=1).mean()
    n_short = (final_weights < 0).sum(axis=1).mean()

    stress_pct = stress.mean() * 100 if isinstance(stress, pd.Series) and len(stress) > 0 else 0

    diagnostics = {
        "ann_return_pct": ann_ret * 100,
        "ann_vol_pct": ann_vol * 100,
        "sharpe": sharpe,
        "max_dd_pct": max_dd * 100,
        "total_cost_pct": total_cost * 100,
        "avg_daily_turnover": turnover_avg,
        "avg_long_positions": n_long,
        "avg_short_positions": n_short,
        "stress_regime_pct": stress_pct,
        "n_obs": len(net),
    }

    return {
        "results": results,
        "weights": final_weights,
        "composite": composite,
        "stress": stress,
        "stats": stats,
        "diagnostics": diagnostics,
    }


def print_v3_report(output: dict) -> None:
    """Print institutional-quality report."""
    d = output["diagnostics"]
    s = output["stats"]

    sep = "=" * 68
    print(f"\n{sep}")
    print("  V3 ALPHA-ENSEMBLE — MARKET-NEUTRAL LONG/SHORT EQUITY")
    print(sep)

    print(f"\n  PERFORMANCE")
    print(f"    Annual Return:      {d['ann_return_pct']:>+10.2f}%")
    print(f"    Annual Volatility:  {d['ann_vol_pct']:>10.2f}%")
    print(f"    Sharpe Ratio:       {d['sharpe']:>10.3f}")
    print(f"    Max Drawdown:       {d['max_dd_pct']:>10.2f}%")

    print(f"\n  PORTFOLIO STRUCTURE")
    print(f"    Avg Long Positions: {d['avg_long_positions']:>10.1f}")
    print(f"    Avg Short Positions:{d['avg_short_positions']:>10.1f}")
    print(f"    Avg Daily Turnover: {d['avg_daily_turnover']:>10.4f}")
    print(f"    Total Friction:     {d['total_cost_pct']:>10.2f}%")

    print(f"\n  REGIME")
    print(f"    Stress Regime:      {d['stress_regime_pct']:>10.1f}% of time")

    print(f"\n  ECONOMETRICS (Newey-West HAC)")
    print(f"    Mean Daily Return:  {s.get('mean_daily', 0)*10000:>+10.2f} bps")
    print(f"    Mean Annual Return: {s.get('mean_annual', 0)*100:>+10.2f}%")
    print(f"    t-statistic:        {s.get('tstat', 0):>10.3f}")
    print(f"    p-value:            {s.get('pvalue', 1):>10.4f}")
    print(f"    NW Std Error:       {s.get('nw_se', 0):>10.6f}")
    print(f"    Observations:       {s.get('n_obs', 0):>10d}")
    print(f"    Max Lags:           {s.get('max_lags', 0):>10d}")

    tstat = s.get("tstat", 0)
    if abs(tstat) >= 3.0:
        print(f"\n  >>> HARVEY THRESHOLD PASSED (|t| = {abs(tstat):.2f} >= 3.0) <<<")
    else:
        print(f"\n  *** WARNING: BELOW HARVEY THRESHOLD (|t| = {abs(tstat):.2f} < 3.0) ***")
        print(f"  *** This factor does NOT survive multiple-testing adjustment. ***")

    print()


# ========================================================================== #
# Main — Download & Run
# ========================================================================== #

def main():
    start = "2010-01-01"
    end = "2024-12-31"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--start" and i + 1 < len(args):
            start = args[i + 1]
        elif a == "--end" and i + 1 < len(args):
            end = args[i + 1]

    print("\n[1/3] Downloading universe data...")
    import yfinance as yf

    # S&P 500 proxy universe: use sector ETFs + liquid large-caps
    tickers = [
        "SPY", "QQQ", "IWM", "DIA",
        "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLU", "XLY", "XLB", "XLRE", "XLC",
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "BRK-B", "JPM",
        "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "ADBE", "CRM", "NFLX",
        "PFE", "KO", "PEP", "MRK", "ABT", "TMO", "COST", "AVGO", "CSCO",
        "ACN", "LLY", "MCD", "WMT", "NKE", "TXN", "QCOM", "LOW", "INTC",
        "AMGN", "IBM", "GS", "CAT", "HON", "BA", "MMM", "GE", "RTX",
        "CVX", "XOM", "COP", "SLB", "EOG",
        "NEE", "DUK", "SO", "D", "AEP",
        "AMT", "PLD", "CCI", "EQIX", "SPG",
    ]

    raw = yf.download(tickers, start="2008-01-01", end=end,
                      auto_adjust=False, progress=True, group_by="ticker")

    # Parse into Close, High, Low, Volume DataFrames
    close_frames = {}
    high_frames = {}
    low_frames = {}
    vol_frames = {}

    for t in tickers:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                sub = raw[t] if t in raw.columns.get_level_values(0) else None
            else:
                sub = raw
            if sub is not None and "Close" in sub.columns:
                close_frames[t] = sub["Close"]
                high_frames[t] = sub["High"]
                low_frames[t] = sub["Low"]
                vol_frames[t] = sub["Volume"]
        except Exception:
            pass

    close = pd.DataFrame(close_frames).dropna(how="all")
    high = pd.DataFrame(high_frames).reindex(close.index)
    low = pd.DataFrame(low_frames).reindex(close.index)
    volume = pd.DataFrame(vol_frames).reindex(close.index).fillna(0)

    close = close.loc[start:]
    high = high.loc[start:]
    low = low.loc[start:]
    volume = volume.loc[start:]

    logger.info("Universe: %d tickers, %d trading days", close.shape[1], close.shape[0])

    print(f"\n[2/3] Running V3 Alpha-Ensemble ({start} to {end})...")
    output = run_v3_pipeline(
        close=close, volume=volume, high=high, low=low, proxy_ticker="SPY",
    )

    print("\n[3/3] Results:")
    print_v3_report(output)

    # Save artifacts
    try:
        from dach_momentum import config
        data_dir = config.DATA_DIR
    except Exception:
        from pathlib import Path
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

    output["results"].to_csv(data_dir / "v3_equity_curve.csv")
    print(f"  Equity curve: {data_dir / 'v3_equity_curve.csv'}")

    output["weights"].to_csv(data_dir / "v3_weights.csv")
    print(f"  Weights: {data_dir / 'v3_weights.csv'}")


if __name__ == "__main__":
    main()
