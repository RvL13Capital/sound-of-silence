"""
External data integrations: SimFin, FRED, FMP (fallback).

SimFin (free tier): historical quarterly income statements, balance sheets,
and cash flows for European stocks — the key missing data source for
real CAN SLIM analysis.

FRED: US and European macro indicators (ECB rate, yields, inflation).

API keys loaded from .env file (gitignored, never committed).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from . import config

logger = logging.getLogger(__name__)

# Load API keys from .env
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass

FMP_KEY = os.getenv("FMP_API_KEY", "")
FRED_KEY = os.getenv("FRED_API_KEY", "")
DBNOMICS_KEY = os.getenv("DBNOMICS_API_KEY", "")

FMP_BASE = "https://financialmodelingprep.com/api/v3"
FRED_BASE = "https://api.stlouisfed.org/fred"

# FMP uses different ticker formats for European exchanges
EXCHANGE_MAP = {
    ".DE": ".DE",   # Xetra — FMP uses .DE
    ".VI": ".VI",   # Vienna
    ".SW": ".SW",   # SIX Swiss
    ".PA": ".PA",   # Euronext Paris
    ".AS": ".AS",   # Euronext Amsterdam
    ".BR": ".BR",   # Euronext Brussels
    ".MI": ".MI",   # Borsa Italiana
    ".MC": ".MC",   # BME Madrid
    ".ST": ".ST",   # Stockholm
    ".CO": ".CO",   # Copenhagen
    ".HE": ".HE",   # Helsinki
    ".OL": ".OL",   # Oslo
    ".LS": ".LS",   # Lisbon
    ".WA": ".WA",   # Warsaw
    ".L": ".L",     # London
    ".AT": ".AT",   # Athens
}


# ========================================================================== #
# SimFin: Historical fundamental data (FREE — the primary source)
# ========================================================================== #

# SimFin market codes for our countries
SIMFIN_MARKETS = {
    ".DE": "de", ".VI": "de", ".SW": "de",  # DACH → German market
    ".PA": "fr", ".AS": "nl", ".BR": "be",
    ".MI": "it", ".MC": "es",
    ".ST": "se", ".CO": "dk", ".HE": "fi", ".OL": "no",
    ".LS": "pt", ".WA": "pl",
    ".L": "gb", ".AT": "gr",
}

# Ticker mapping: yfinance suffix → SimFin ticker (strip suffix)
def _yf_to_simfin_ticker(yf_ticker: str) -> str:
    """Convert yfinance ticker to SimFin format (just the base symbol)."""
    for suffix in EXCHANGE_MAP:
        if yf_ticker.endswith(suffix):
            return yf_ticker[: -len(suffix)]
    return yf_ticker


def _get_simfin_market(yf_ticker: str) -> str:
    """Determine SimFin market code from yfinance ticker suffix."""
    for suffix, market in SIMFIN_MARKETS.items():
        if yf_ticker.endswith(suffix):
            return market
    return "de"  # default


_simfin_cache: dict[str, pd.DataFrame] = {}


def load_simfin_income(market: str = "de") -> pd.DataFrame:
    """
    Load quarterly income statements from SimFin for a market.
    Data is cached in memory and on disk (~/.simfin_data/).
    Free tier: no API key needed, set to 'free'.
    """
    cache_key = f"income_{market}"
    if cache_key in _simfin_cache:
        return _simfin_cache[cache_key]

    try:
        import simfin as sf
        sf.set_api_key("free")

        data_dir = str(config.CACHE_DIR / "simfin")
        sf.set_data_dir(data_dir)

        df = sf.load_income(variant="quarterly", market=market)
        _simfin_cache[cache_key] = df
        logger.info("SimFin income loaded for market=%s: %d rows", market, len(df))
        return df
    except Exception as exc:
        logger.warning("SimFin income load failed for %s: %s", market, exc)
        return pd.DataFrame()


def load_simfin_balance(market: str = "de") -> pd.DataFrame:
    """Load quarterly balance sheets from SimFin."""
    cache_key = f"balance_{market}"
    if cache_key in _simfin_cache:
        return _simfin_cache[cache_key]

    try:
        import simfin as sf
        sf.set_api_key("free")
        sf.set_data_dir(str(config.CACHE_DIR / "simfin"))
        df = sf.load_balance(variant="quarterly", market=market)
        _simfin_cache[cache_key] = df
        return df
    except Exception as exc:
        logger.warning("SimFin balance load failed: %s", exc)
        return pd.DataFrame()


def load_simfin_cashflow(market: str = "de") -> pd.DataFrame:
    """Load quarterly cash flow statements from SimFin."""
    cache_key = f"cashflow_{market}"
    if cache_key in _simfin_cache:
        return _simfin_cache[cache_key]

    try:
        import simfin as sf
        sf.set_api_key("free")
        sf.set_data_dir(str(config.CACHE_DIR / "simfin"))
        df = sf.load_cashflow(variant="quarterly", market=market)
        _simfin_cache[cache_key] = df
        return df
    except Exception as exc:
        logger.warning("SimFin cashflow load failed: %s", exc)
        return pd.DataFrame()


def get_simfin_earnings(yf_ticker: str) -> pd.DataFrame:
    """
    Get quarterly earnings for a stock using SimFin bulk data.
    Returns DataFrame with date, revenue, net_income, eps columns.
    """
    sf_ticker = _yf_to_simfin_ticker(yf_ticker)
    market = _get_simfin_market(yf_ticker)

    income = load_simfin_income(market)
    if income.empty:
        return pd.DataFrame()

    try:
        # SimFin uses MultiIndex: (Ticker, Report Date)
        if sf_ticker in income.index.get_level_values("Ticker"):
            stock = income.loc[sf_ticker].copy()
            stock = stock.reset_index()

            result = pd.DataFrame()
            result["date"] = pd.to_datetime(stock.get("Report Date", stock.get("Fiscal Period", "")))

            # Column names vary by SimFin version
            for col_name, candidates in {
                "revenue": ["Revenue", "Total Revenue"],
                "net_income": ["Net Income", "Net Income (Common)"],
                "gross_profit": ["Gross Profit"],
            }.items():
                for c in candidates:
                    if c in stock.columns:
                        result[col_name] = stock[c].values
                        break

            result = result.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            return result
    except Exception as exc:
        logger.debug("SimFin extraction failed for %s: %s", yf_ticker, exc)

    return pd.DataFrame()


def canslim_score_simfin(yf_ticker: str) -> dict:
    """
    Compute CAN SLIM score using SimFin historical quarterly data.
    This is the REAL fundamental analysis — actual EPS, not proxies.
    """
    result = {
        "ticker": yf_ticker,
        "source": "simfin",
        "C_pass": False, "C_details": "",
        "A_pass": False, "A_details": "",
        "quality_score": 0,
        "earnings_accelerating": False,
        "revenue_accelerating": False,
        "roe": None,
        "fcf_positive": False,
    }

    earnings = get_simfin_earnings(yf_ticker)
    if earnings.empty or len(earnings) < 5:
        result["C_details"] = f"Insufficient SimFin data ({len(earnings)} quarters)"
        return result

    result["source"] = "simfin (real quarterly data)"

    # --- C: Current Quarterly EPS YoY ---
    if "net_income" in earnings.columns and len(earnings) >= 5:
        latest = earnings.iloc[-1]["net_income"]
        prior_yr = earnings.iloc[-5]["net_income"]

        if prior_yr and prior_yr != 0:
            growth = (latest / prior_yr - 1) * 100
            result["C_details"] = f"NI: {latest:,.0f} vs {prior_yr:,.0f} = {growth:+.1f}% YoY"
            result["C_pass"] = growth >= 25

        # Acceleration: compare last 2 YoY growth rates
        if len(earnings) >= 9:
            g1_curr, g1_prev = earnings.iloc[-1]["net_income"], earnings.iloc[-5]["net_income"]
            g2_curr, g2_prev = earnings.iloc[-2]["net_income"], earnings.iloc[-6]["net_income"]
            if g1_prev and g2_prev and g1_prev != 0 and g2_prev != 0:
                rate1 = (g1_curr / g1_prev - 1) * 100
                rate2 = (g2_curr / g2_prev - 1) * 100
                result["earnings_accelerating"] = rate1 > rate2

    # Revenue acceleration
    if "revenue" in earnings.columns and len(earnings) >= 9:
        r1_curr, r1_prev = earnings.iloc[-1]["revenue"], earnings.iloc[-5]["revenue"]
        r2_curr, r2_prev = earnings.iloc[-2]["revenue"], earnings.iloc[-6]["revenue"]
        if r1_prev and r2_prev and r1_prev != 0 and r2_prev != 0:
            rg1 = (r1_curr / r1_prev - 1) * 100
            rg2 = (r2_curr / r2_prev - 1) * 100
            result["revenue_accelerating"] = rg1 > rg2
            result["latest_revenue_growth"] = round(rg1, 1)

    # --- A: Annual trend (use last 4 years of quarterly sums) ---
    if "net_income" in earnings.columns and len(earnings) >= 8:
        # Sum quarters into annual figures
        annual_ni = []
        for i in range(0, min(16, len(earnings)) - 3, 4):
            chunk = earnings.iloc[i:i+4]
            annual_ni.append(chunk["net_income"].sum())

        if len(annual_ni) >= 3:
            growth_years = sum(1 for i in range(1, len(annual_ni)) if annual_ni[i] > annual_ni[i-1])
            result["A_pass"] = growth_years >= 2
            result["A_details"] = f"{growth_years}/{len(annual_ni)-1} years of NI growth"

    # --- FCF check ---
    sf_ticker = _yf_to_simfin_ticker(yf_ticker)
    market = _get_simfin_market(yf_ticker)
    cf = load_simfin_cashflow(market)
    if not cf.empty:
        try:
            if sf_ticker in cf.index.get_level_values("Ticker"):
                stock_cf = cf.loc[sf_ticker]
                for col in ["Free Cash Flow", "Net Cash from Operating Activities"]:
                    if col in stock_cf.columns:
                        ttm = stock_cf[col].tail(4).sum()
                        result["fcf_positive"] = ttm > 0
                        break
        except Exception:
            pass

    # Quality score
    score = 0
    if result["C_pass"]:
        score += 2
    if result["A_pass"]:
        score += 2
    if result["earnings_accelerating"]:
        score += 1
    if result["revenue_accelerating"]:
        score += 1
    if result["fcf_positive"]:
        score += 1
    result["quality_score"] = score

    return result


def _fmp_get(endpoint: str, params: dict = None) -> list | dict:
    """Make a GET request to the FMP API."""
    if not FMP_KEY:
        logger.warning("FMP_API_KEY not set. Add it to .env file.")
        return []
    url = f"{FMP_BASE}/{endpoint}"
    p = {"apikey": FMP_KEY}
    if params:
        p.update(params)
    try:
        r = requests.get(url, params=p, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.debug("FMP request failed: %s", exc)
        return []


# ========================================================================== #
# FMP: Fundamental data
# ========================================================================== #


def get_quarterly_earnings(ticker: str, limit: int = 12) -> pd.DataFrame:
    """
    Get quarterly income statement data from FMP.
    Returns DataFrame with: date, revenue, netIncome, eps, ebitda.
    """
    data = _fmp_get(f"income-statement/{ticker}", {
        "period": "quarter", "limit": str(limit),
    })
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    for q in data:
        rows.append({
            "date": q.get("date"),
            "revenue": q.get("revenue"),
            "gross_profit": q.get("grossProfit"),
            "ebitda": q.get("ebitda"),
            "net_income": q.get("netIncome"),
            "eps": q.get("eps"),
            "eps_diluted": q.get("epsdiluted"),
        })

    df = pd.DataFrame(rows)
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def get_financial_ratios(ticker: str, limit: int = 8) -> pd.DataFrame:
    """Get quarterly financial ratios from FMP."""
    data = _fmp_get(f"ratios/{ticker}", {
        "period": "quarter", "limit": str(limit),
    })
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    for q in data:
        rows.append({
            "date": q.get("date"),
            "pe_ratio": q.get("priceEarningsRatio"),
            "peg_ratio": q.get("priceEarningsToGrowthRatio"),
            "pb_ratio": q.get("priceToBookRatio"),
            "roe": q.get("returnOnEquity"),
            "roa": q.get("returnOnAssets"),
            "current_ratio": q.get("currentRatio"),
            "debt_equity": q.get("debtEquityRatio"),
            "gross_profit_margin": q.get("grossProfitMargin"),
            "net_profit_margin": q.get("netProfitMargin"),
            "operating_margin": q.get("operatingProfitMargin"),
            "fcf_per_share": q.get("freeCashFlowPerShare"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def get_cash_flow(ticker: str, limit: int = 8) -> pd.DataFrame:
    """Get quarterly cash flow statement from FMP."""
    data = _fmp_get(f"cash-flow-statement/{ticker}", {
        "period": "quarter", "limit": str(limit),
    })
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    for q in data:
        rows.append({
            "date": q.get("date"),
            "operating_cf": q.get("operatingCashFlow"),
            "capex": q.get("capitalExpenditure"),
            "fcf": q.get("freeCashFlow"),
            "dividends_paid": q.get("dividendsPaid"),
            "share_buyback": q.get("commonStockRepurchased"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def get_insider_trades(ticker: str) -> pd.DataFrame:
    """Get insider trading activity from FMP."""
    data = _fmp_get(f"insider-trading", {"symbol": ticker, "limit": "20"})
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    for t in data:
        rows.append({
            "date": t.get("transactionDate"),
            "name": t.get("reportingName"),
            "type": t.get("transactionType"),
            "shares": t.get("securitiesTransacted"),
            "price": t.get("price"),
            "value": t.get("securitiesTransacted", 0) * (t.get("price") or 0),
        })

    return pd.DataFrame(rows)


def get_analyst_estimates(ticker: str) -> pd.DataFrame:
    """Get analyst earnings estimates from FMP."""
    data = _fmp_get(f"analyst-estimates/{ticker}", {
        "period": "quarter", "limit": "8",
    })
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    rows = []
    for e in data:
        rows.append({
            "date": e.get("date"),
            "est_revenue_avg": e.get("estimatedRevenueAvg"),
            "est_revenue_low": e.get("estimatedRevenueLow"),
            "est_revenue_high": e.get("estimatedRevenueHigh"),
            "est_eps_avg": e.get("estimatedEpsAvg"),
            "est_eps_low": e.get("estimatedEpsLow"),
            "est_eps_high": e.get("estimatedEpsHigh"),
            "num_analysts_revenue": e.get("numberAnalystsEstimatedRevenue"),
            "num_analysts_eps": e.get("numberAnalystEstimatedEps"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def canslim_score_fmp(ticker: str) -> dict:
    """
    Compute a real CAN SLIM score using FMP fundamental data.

    Returns a dict with:
      C_score, A_score, earnings details, and an overall grade.
    """
    result = {
        "ticker": ticker,
        "C_pass": False, "C_details": "",
        "A_pass": False, "A_details": "",
        "quality_score": 0,
        "earnings_accelerating": False,
        "revenue_accelerating": False,
        "roe": None,
        "fcf_positive": False,
    }

    earnings = get_quarterly_earnings(ticker, limit=12)
    ratios = get_financial_ratios(ticker, limit=8)
    cashflow = get_cash_flow(ticker, limit=8)

    if earnings.empty:
        result["C_details"] = "No earnings data from FMP"
        return result

    # --- C: Current Quarterly Earnings ---
    # Compare each quarter to same quarter prior year
    if len(earnings) >= 5:
        latest = earnings.iloc[-1]
        # Find same quarter last year (4 quarters back)
        prior_year = earnings.iloc[-5] if len(earnings) >= 5 else None

        if prior_year is not None:
            eps_now = latest.get("eps", 0) or 0
            eps_prior = prior_year.get("eps", 0) or 0

            if eps_prior != 0:
                eps_growth = (eps_now / eps_prior - 1) * 100
                result["C_details"] = f"EPS: {eps_now:.2f} vs {eps_prior:.2f} = {eps_growth:+.1f}% YoY"
                result["C_pass"] = eps_growth >= 25
            else:
                result["C_details"] = f"EPS: {eps_now:.2f} (prior year was zero)"

            # Revenue growth
            rev_now = latest.get("revenue", 0) or 0
            rev_prior = prior_year.get("revenue", 0) or 0
            if rev_prior != 0:
                rev_growth = (rev_now / rev_prior - 1) * 100
                result["revenue_growth"] = round(rev_growth, 1)

        # Check acceleration (last 2 quarters vs prior 2)
        if len(earnings) >= 8:
            recent_growth = []
            for i in [-1, -2]:
                curr = earnings.iloc[i].get("eps", 0) or 0
                prev = earnings.iloc[i - 4].get("eps", 0) or 0
                if prev != 0:
                    recent_growth.append((curr / prev - 1) * 100)

            if len(recent_growth) >= 2:
                result["earnings_accelerating"] = recent_growth[0] > recent_growth[1]

    # --- A: Annual Earnings Growth ---
    annual = _fmp_get(f"income-statement/{ticker}", {"period": "annual", "limit": "5"})
    if isinstance(annual, list) and len(annual) >= 3:
        annual_eps = [(a.get("date"), a.get("eps", 0)) for a in annual]
        annual_eps.sort(key=lambda x: x[0])

        # 3-year growth check
        if len(annual_eps) >= 3:
            growth_years = sum(
                1 for i in range(1, len(annual_eps))
                if (annual_eps[i][1] or 0) > (annual_eps[i-1][1] or 0)
            )
            result["A_pass"] = growth_years >= 2
            result["A_details"] = f"{growth_years}/{len(annual_eps)-1} years of EPS growth"

    # --- ROE ---
    if not ratios.empty and "roe" in ratios.columns:
        latest_roe = ratios.iloc[-1].get("roe")
        if latest_roe is not None:
            result["roe"] = round(latest_roe * 100, 1)

    # --- FCF ---
    if not cashflow.empty and "fcf" in cashflow.columns:
        ttm_fcf = cashflow.tail(4)["fcf"].sum()
        result["fcf_positive"] = ttm_fcf > 0

    # --- Overall quality score ---
    score = 0
    if result["C_pass"]:
        score += 2
    if result["A_pass"]:
        score += 2
    if result["earnings_accelerating"]:
        score += 1
    if result.get("roe") and result["roe"] >= 17:
        score += 1
    if result["fcf_positive"]:
        score += 1
    result["quality_score"] = score

    return result


# ========================================================================== #
# FRED: Macro indicators
# ========================================================================== #


def get_fred_series(series_id: str, start: str = "2005-01-01") -> pd.Series:
    """Fetch a FRED time series."""
    if not FRED_KEY:
        logger.warning("FRED_API_KEY not set.")
        return pd.Series(dtype=float)

    try:
        from fredapi import Fred
        fred = Fred(api_key=FRED_KEY)
        return fred.get_series(series_id, observation_start=start)
    except Exception as exc:
        logger.debug("FRED request failed: %s", exc)
        return pd.Series(dtype=float)


def get_euro_yield_curve() -> dict:
    """Get key European interest rate data from FRED."""
    series = {
        "ecb_rate": "ECBDFR",           # ECB deposit facility rate
        "german_10y": "IRLTLT01DEM156N", # German 10Y yield
        "us_10y": "DGS10",              # US 10Y for comparison
        "euro_inflation": "CPALTT01EZM659N",  # Eurozone CPI
    }
    result = {}
    for name, sid in series.items():
        try:
            s = get_fred_series(sid)
            if not s.empty:
                result[name] = {
                    "latest": round(float(s.dropna().iloc[-1]), 2),
                    "date": str(s.dropna().index[-1].date()),
                }
        except Exception:
            pass
    return result


# ========================================================================== #
# Enhanced CAN SLIM dashboard using real data
# ========================================================================== #


def enhanced_canslim(ticker: str) -> dict:
    """
    Run enhanced CAN SLIM analysis combining FMP fundamentals
    with the existing yfinance-based analysis.
    """
    fmp_data = canslim_score_fmp(ticker)
    estimates = get_analyst_estimates(ticker)
    insiders = get_insider_trades(ticker)

    result = {
        "ticker": ticker,
        "fmp": fmp_data,
        "has_fmp_data": fmp_data["C_details"] != "No earnings data from FMP",
    }

    # Analyst revision momentum
    if not estimates.empty and len(estimates) >= 2:
        latest_est = estimates.iloc[-1].get("est_eps_avg")
        prior_est = estimates.iloc[-2].get("est_eps_avg")
        if latest_est and prior_est and prior_est != 0:
            revision = (latest_est / prior_est - 1) * 100
            result["eps_revision_pct"] = round(revision, 1)
            result["revisions_positive"] = revision > 0

    # Insider activity summary
    if not insiders.empty:
        buys = insiders[insiders["type"].str.contains("P-Purchase|Buy|Kauf", case=False, na=False)]
        sells = insiders[insiders["type"].str.contains("S-Sale|Sell|Verkauf", case=False, na=False)]
        result["insider_buys"] = len(buys)
        result["insider_sells"] = len(sells)
        result["insider_signal"] = (
            "BUYING" if len(buys) > len(sells)
            else "SELLING" if len(sells) > len(buys) * 2
            else "neutral"
        )

    return result


def print_enhanced_canslim(data: dict) -> None:
    """Print the enhanced CAN SLIM analysis."""
    fmp = data.get("fmp", {})
    sep = "=" * 60

    print(f"\n{sep}")
    print(f"  ENHANCED CAN SLIM: {data['ticker']}")
    print(f"  Data source: {'FMP (real earnings)' if data.get('has_fmp_data') else 'No FMP data'}")
    print(sep)

    print(f"\n  C — Current Quarterly Earnings: {'PASS' if fmp.get('C_pass') else 'FAIL'}")
    print(f"    {fmp.get('C_details', 'N/A')}")
    if fmp.get("revenue_growth") is not None:
        print(f"    Revenue growth: {fmp['revenue_growth']:+.1f}%")
    print(f"    Earnings accelerating: {'YES' if fmp.get('earnings_accelerating') else 'NO'}")

    print(f"\n  A — Annual Earnings Growth: {'PASS' if fmp.get('A_pass') else 'FAIL'}")
    print(f"    {fmp.get('A_details', 'N/A')}")
    print(f"    ROE: {fmp.get('roe', 'N/A')}%")

    print(f"\n  Cash Flow: {'Positive TTM FCF' if fmp.get('fcf_positive') else 'Negative/Unknown'}")

    if data.get("eps_revision_pct") is not None:
        direction = "UP" if data["revisions_positive"] else "DOWN"
        print(f"\n  Analyst Revisions: {data['eps_revision_pct']:+.1f}% ({direction})")

    if data.get("insider_buys") is not None:
        print(f"\n  Insiders: {data.get('insider_buys', 0)} buys, "
              f"{data.get('insider_sells', 0)} sells — {data.get('insider_signal', '?')}")

    print(f"\n  Quality Score: {fmp.get('quality_score', 0)}/7")
    print()
