"""
External data integrations: FMP, FRED, DBnomics.

Provides real fundamental data (quarterly earnings, financial ratios)
and macro indicators to replace the price-based quality proxies.

API keys are loaded from .env file (gitignored, never committed).

Usage:
    from dach_momentum.external_data import fmp, fred, macro
    earnings = fmp.get_quarterly_earnings("JEN.DE")
    rates = fred.get_ecb_rate()
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
