"""
Fundamental research dashboard for trend template candidates.

For each stock passing the technical screen, pulls and displays:
- Quarterly earnings history and acceleration
- Valuation metrics (P/E, EV/EBITDA, PEG)
- Cash flow vs earnings quality
- Insider transactions (Directors' Dealings)
- Analyst estimate data (where available)

Run: python run_dashboard.py
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from . import config

logger = logging.getLogger(__name__)


# ========================================================================== #
# Earnings analysis
# ========================================================================== #


def get_earnings_data(ticker_obj: yf.Ticker) -> dict:
    """
    Extract quarterly and annual earnings data.
    Returns a dict with earnings history, growth rates, and acceleration.
    """
    result = {
        "quarterly_eps": [],
        "annual_eps": [],
        "eps_accelerating": False,
        "revenue_accelerating": False,
        "quarters_of_growth": 0,
    }

    try:
        # Quarterly financials
        q_income = ticker_obj.quarterly_income_stmt
        if q_income is not None and not q_income.empty:
            # Get EPS-related data (Net Income as proxy if EPS not directly available)
            for row_name in ["Net Income", "Net Income Common Stockholders",
                             "Diluted EPS", "Basic EPS"]:
                if row_name in q_income.index:
                    eps_series = q_income.loc[row_name].dropna().sort_index()
                    if len(eps_series) >= 2:
                        result["quarterly_eps"] = [
                            {"date": str(d.date()), "value": float(v)}
                            for d, v in eps_series.items()
                        ]
                    break

            # Revenue for acceleration check
            for row_name in ["Total Revenue", "Revenue"]:
                if row_name in q_income.index:
                    rev = q_income.loc[row_name].dropna().sort_index()
                    if len(rev) >= 4:
                        # YoY growth rates for last 4 quarters
                        growths = []
                        vals = rev.values
                        for i in range(len(vals) - 1):
                            if vals[i] != 0:
                                g = (vals[i + 1] / vals[i] - 1) * 100
                                growths.append(g)
                        if len(growths) >= 2:
                            result["revenue_accelerating"] = growths[-1] > growths[-2]
                    break

        # Annual financials for longer-term view
        a_income = ticker_obj.income_stmt
        if a_income is not None and not a_income.empty:
            for row_name in ["Net Income", "Net Income Common Stockholders"]:
                if row_name in a_income.index:
                    annual = a_income.loc[row_name].dropna().sort_index()
                    if len(annual) >= 2:
                        result["annual_eps"] = [
                            {"date": str(d.date()), "value": float(v)}
                            for d, v in annual.items()
                        ]
                        # Count consecutive years of growth
                        vals = annual.values
                        count = 0
                        for i in range(len(vals) - 1, 0, -1):
                            if vals[i] > vals[i - 1]:
                                count += 1
                            else:
                                break
                        result["quarters_of_growth"] = count
                    break

        # EPS acceleration: are recent growth rates > earlier growth rates?
        if len(result["quarterly_eps"]) >= 4:
            vals = [e["value"] for e in result["quarterly_eps"]]
            if len(vals) >= 4 and vals[-4] != 0 and vals[-2] != 0:
                growth_recent = (vals[-1] / vals[-2] - 1) if vals[-2] != 0 else 0
                growth_prior = (vals[-3] / vals[-4] - 1) if vals[-4] != 0 else 0
                result["eps_accelerating"] = growth_recent > growth_prior

    except Exception as exc:
        logger.debug("Earnings data failed for %s: %s",
                     ticker_obj.ticker, exc)

    return result


# ========================================================================== #
# Valuation metrics
# ========================================================================== #


def get_valuation_metrics(ticker_obj: yf.Ticker) -> dict:
    """Extract key valuation ratios."""
    info = ticker_obj.info or {}

    pe_trailing = info.get("trailingPE")
    pe_forward = info.get("forwardPE")
    peg = info.get("pegRatio")
    ev_ebitda = info.get("enterpriseToEbitda")
    pb = info.get("priceToBook")
    ps = info.get("priceToSalesTrailing12Months")
    market_cap = info.get("marketCap")
    ev = info.get("enterpriseValue")

    # Earnings yield = 1/PE (useful for comparison)
    earnings_yield = (1.0 / pe_trailing * 100) if pe_trailing and pe_trailing > 0 else None

    return {
        "pe_trailing": pe_trailing,
        "pe_forward": pe_forward,
        "peg_ratio": peg,
        "ev_ebitda": ev_ebitda,
        "price_to_book": pb,
        "price_to_sales": ps,
        "market_cap": market_cap,
        "enterprise_value": ev,
        "earnings_yield_pct": earnings_yield,
    }


# ========================================================================== #
# Cash flow quality
# ========================================================================== #


def get_cashflow_quality(ticker_obj: yf.Ticker) -> dict:
    """
    Compare operating cash flow to net income.
    Healthy: OCF >= Net Income (cash earnings confirm reported earnings).
    Warning: OCF << Net Income (earnings may be low quality).
    """
    result = {
        "ocf_vs_net_income": None,
        "fcf_yield_pct": None,
        "ocf_trend": None,
        "quality_flag": "unknown",
    }

    try:
        cf = ticker_obj.quarterly_cashflow
        income = ticker_obj.quarterly_income_stmt

        if cf is None or income is None:
            return result

        # Operating Cash Flow
        ocf_row = None
        for name in ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]:
            if name in cf.index:
                ocf_row = cf.loc[name].dropna().sort_index()
                break

        # Net Income
        ni_row = None
        for name in ["Net Income", "Net Income Common Stockholders"]:
            if name in income.index:
                ni_row = income.loc[name].dropna().sort_index()
                break

        if ocf_row is not None and ni_row is not None:
            # Use trailing 4 quarters (TTM)
            ocf_ttm = ocf_row.tail(4).sum()
            ni_ttm = ni_row.tail(4).sum()

            if ni_ttm != 0:
                ratio = ocf_ttm / ni_ttm
                result["ocf_vs_net_income"] = round(float(ratio), 2)

                if ratio >= 1.0:
                    result["quality_flag"] = "GOOD"
                elif ratio >= 0.7:
                    result["quality_flag"] = "OK"
                else:
                    result["quality_flag"] = "WARNING"

            # OCF trend (is it growing?)
            if len(ocf_row) >= 4:
                recent_2q = ocf_row.tail(2).sum()
                prior_2q = ocf_row.tail(4).head(2).sum()
                if prior_2q != 0:
                    result["ocf_trend"] = "growing" if recent_2q > prior_2q else "declining"

        # Free Cash Flow Yield
        info = ticker_obj.info or {}
        fcf = info.get("freeCashflow")
        mcap = info.get("marketCap")
        if fcf and mcap and mcap > 0:
            result["fcf_yield_pct"] = round(fcf / mcap * 100, 2)

    except Exception as exc:
        logger.debug("Cash flow data failed for %s: %s",
                     ticker_obj.ticker, exc)

    return result


# ========================================================================== #
# Insider transactions
# ========================================================================== #


def get_insider_activity(ticker_obj: yf.Ticker) -> dict:
    """
    Get insider buying/selling activity.
    yfinance provides insider_transactions for some stocks.
    """
    result = {
        "recent_buys": 0,
        "recent_sells": 0,
        "net_insider_signal": "neutral",
        "transactions": [],
    }

    try:
        insiders = ticker_obj.insider_transactions
        if insiders is None or insiders.empty:
            return result

        # Filter to last 6 months
        if "Start Date" in insiders.columns:
            date_col = "Start Date"
        elif "startDate" in insiders.columns:
            date_col = "startDate"
        else:
            # Try to find any date column
            date_cols = [c for c in insiders.columns if "date" in c.lower()]
            date_col = date_cols[0] if date_cols else None

        if date_col:
            insiders[date_col] = pd.to_datetime(insiders[date_col], errors="coerce")
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=180)
            recent = insiders[insiders[date_col] >= cutoff]
        else:
            recent = insiders.tail(10)

        # Count buys vs sells
        for _, row in recent.iterrows():
            text = str(row.get("Text", row.get("transaction", ""))).lower()
            shares = row.get("Shares", row.get("shares", 0))

            tx = {
                "text": str(row.get("Text", row.get("transaction", "")))[:60],
                "shares": int(shares) if pd.notna(shares) else 0,
            }
            if date_col and pd.notna(row.get(date_col)):
                tx["date"] = str(row[date_col].date())

            result["transactions"].append(tx)

            if any(w in text for w in ["purchase", "buy", "acquisition", "kauf"]):
                result["recent_buys"] += 1
            elif any(w in text for w in ["sale", "sell", "disposition", "verkauf"]):
                result["recent_sells"] += 1

        if result["recent_buys"] > result["recent_sells"]:
            result["net_insider_signal"] = "BUYING"
        elif result["recent_sells"] > result["recent_buys"] * 2:
            result["net_insider_signal"] = "SELLING"
        else:
            result["net_insider_signal"] = "neutral"

    except Exception as exc:
        logger.debug("Insider data failed for %s: %s",
                     ticker_obj.ticker, exc)

    return result


# ========================================================================== #
# Analyst estimates
# ========================================================================== #


def get_analyst_data(ticker_obj: yf.Ticker) -> dict:
    """Get analyst recommendations and estimate data."""
    result = {
        "analyst_count": None,
        "recommendation": None,
        "target_mean": None,
        "target_vs_current_pct": None,
        "earnings_estimate_next_q": None,
        "revenue_estimate_next_q": None,
    }

    try:
        info = ticker_obj.info or {}

        result["analyst_count"] = info.get("numberOfAnalystOpinions")
        result["recommendation"] = info.get("recommendationKey")
        result["target_mean"] = info.get("targetMeanPrice")

        current = info.get("currentPrice") or info.get("regularMarketPrice")
        if result["target_mean"] and current and current > 0:
            result["target_vs_current_pct"] = round(
                (result["target_mean"] / current - 1) * 100, 1
            )

    except Exception as exc:
        logger.debug("Analyst data failed for %s: %s",
                     ticker_obj.ticker, exc)

    return result


# ========================================================================== #
# Combined dashboard for a single stock
# ========================================================================== #


def research_stock(yf_ticker: str) -> dict:
    """
    Run full fundamental research on a single stock.
    Returns a structured dict with all research data.
    """
    logger.info("Researching %s...", yf_ticker)
    t = yf.Ticker(yf_ticker)

    return {
        "ticker": yf_ticker,
        "name": (t.info or {}).get("shortName", yf_ticker),
        "sector": (t.info or {}).get("sector"),
        "industry": (t.info or {}).get("industry"),
        "earnings": get_earnings_data(t),
        "valuation": get_valuation_metrics(t),
        "cashflow": get_cashflow_quality(t),
        "insiders": get_insider_activity(t),
        "analysts": get_analyst_data(t),
    }


def print_dashboard(data: dict) -> None:
    """Pretty-print the research dashboard for one stock."""
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {data['ticker']}  —  {data['name']}")
    print(f"  {data.get('sector', '?')}  /  {data.get('industry', '?')}")
    print(sep)

    # --- Valuation ---
    v = data["valuation"]
    print("\n  VALUATION")
    print(f"    Market Cap:      {v['market_cap']:>15,.0f}" if v["market_cap"] else "    Market Cap:      N/A")
    print(f"    P/E (trailing):  {v['pe_trailing']:>10.1f}" if v["pe_trailing"] else "    P/E (trailing):  N/A")
    print(f"    P/E (forward):   {v['pe_forward']:>10.1f}" if v["pe_forward"] else "    P/E (forward):   N/A")
    print(f"    PEG Ratio:       {v['peg_ratio']:>10.2f}" if v["peg_ratio"] else "    PEG Ratio:       N/A")
    print(f"    EV/EBITDA:       {v['ev_ebitda']:>10.1f}" if v["ev_ebitda"] else "    EV/EBITDA:       N/A")
    print(f"    P/B:             {v['price_to_book']:>10.2f}" if v["price_to_book"] else "    P/B:             N/A")
    print(f"    Earnings Yield:  {v['earnings_yield_pct']:>9.1f}%" if v["earnings_yield_pct"] else "    Earnings Yield:  N/A")

    # --- Earnings ---
    e = data["earnings"]
    print("\n  EARNINGS")
    if e["quarterly_eps"]:
        print("    Quarterly Net Income (recent):")
        for q in e["quarterly_eps"][-6:]:
            print(f"      {q['date']:>12s}  {q['value']:>15,.0f}")
    print(f"    EPS Accelerating:     {'YES' if e['eps_accelerating'] else 'NO'}")
    print(f"    Revenue Accelerating: {'YES' if e['revenue_accelerating'] else 'NO'}")
    print(f"    Consecutive Growth:   {e['quarters_of_growth']} periods")

    # --- Cash Flow Quality ---
    cf = data["cashflow"]
    print("\n  CASH FLOW QUALITY")
    print(f"    OCF / Net Income:  {cf['ocf_vs_net_income']}" if cf["ocf_vs_net_income"] else "    OCF / Net Income:  N/A")
    print(f"    Quality Flag:      {cf['quality_flag']}")
    print(f"    OCF Trend:         {cf['ocf_trend']}" if cf["ocf_trend"] else "    OCF Trend:         N/A")
    print(f"    FCF Yield:         {cf['fcf_yield_pct']}%" if cf["fcf_yield_pct"] else "    FCF Yield:         N/A")

    # --- Insider Activity ---
    ins = data["insiders"]
    print("\n  INSIDER ACTIVITY (6 months)")
    print(f"    Buys:  {ins['recent_buys']}    Sells:  {ins['recent_sells']}    Signal:  {ins['net_insider_signal']}")
    if ins["transactions"]:
        for tx in ins["transactions"][:5]:
            date_str = tx.get("date", "?")
            print(f"      {date_str}  {tx['text']}")

    # --- Analyst Coverage ---
    a = data["analysts"]
    print("\n  ANALYST COVERAGE")
    print(f"    Analysts:     {a['analyst_count']}" if a["analyst_count"] else "    Analysts:     N/A (uncovered)")
    print(f"    Consensus:    {a['recommendation']}" if a["recommendation"] else "    Consensus:    N/A")
    print(f"    Target Price: {a['target_mean']}" if a["target_mean"] else "    Target Price: N/A")
    print(f"    Upside:       {a['target_vs_current_pct']:+.1f}%" if a["target_vs_current_pct"] is not None else "    Upside:       N/A")

    # --- Summary Assessment ---
    print(f"\n  {'─' * 56}")
    print("  SUMMARY FLAGS")
    flags = []
    if e["eps_accelerating"]:
        flags.append("  [+] Earnings accelerating")
    else:
        flags.append("  [-] Earnings NOT accelerating")

    if e["revenue_accelerating"]:
        flags.append("  [+] Revenue accelerating")
    else:
        flags.append("  [-] Revenue NOT accelerating")

    if cf["quality_flag"] == "GOOD":
        flags.append("  [+] Cash flow confirms earnings (OCF/NI >= 1.0)")
    elif cf["quality_flag"] == "WARNING":
        flags.append("  [!] Cash flow WARNING — OCF << Net Income")

    if ins["net_insider_signal"] == "BUYING":
        flags.append("  [+] Insider BUYING detected")
    elif ins["net_insider_signal"] == "SELLING":
        flags.append("  [!] Insider SELLING detected")

    if v["peg_ratio"] and v["peg_ratio"] < 1.5:
        flags.append(f"  [+] PEG < 1.5 ({v['peg_ratio']:.2f}) — growth reasonably priced")
    elif v["peg_ratio"] and v["peg_ratio"] > 3.0:
        flags.append(f"  [!] PEG > 3.0 ({v['peg_ratio']:.2f}) — growth may be overpriced")

    if a["analyst_count"] and a["analyst_count"] <= 3:
        flags.append(f"  [+] Low coverage ({a['analyst_count']} analysts) — less efficient pricing")

    for flag in flags:
        print(flag)

    print()


# ========================================================================== #
# Run dashboard for all trend template candidates
# ========================================================================== #


def run_dashboard(tickers: Optional[list[str]] = None) -> list[dict]:
    """
    Run the fundamental dashboard for a list of tickers.
    If no tickers provided, uses current trend template passers.
    """
    import time

    results = []
    for i, ticker in enumerate(tickers):
        if i > 0:
            time.sleep(0.5)  # rate limit
        try:
            data = research_stock(ticker)
            results.append(data)
            print_dashboard(data)
        except Exception as exc:
            logger.error("Failed to research %s: %s", ticker, exc)

    return results
