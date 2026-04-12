"""
CAN SLIM + Minervini deep-dive analysis.

Comprehensive fundamental research combining O'Neil's CAN SLIM
criteria with Minervini's SEPA methodology for each candidate.

C = Current quarterly earnings (>25% YoY growth)
A = Annual earnings growth (consistent multi-year)
N = New products, management, highs (catalysts)
S = Supply and demand (float, volume patterns)
L = Leader or laggard (relative strength, sector rank)
I = Institutional sponsorship
M = Market direction (regime filter)
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

from . import config

logger = logging.getLogger(__name__)


def _safe_pct(new, old) -> Optional[float]:
    """Calculate percentage change, returning None if division impossible."""
    if old is None or new is None or old == 0:
        return None
    return (new / old - 1) * 100


def _extract_row(df, names: list[str]) -> Optional[pd.Series]:
    """Extract first matching row from a financial statement DataFrame."""
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            return df.loc[name].dropna().sort_index()
    return None


# ========================================================================== #
# C — Current Quarterly Earnings
# ========================================================================== #


def analyze_current_earnings(t: yf.Ticker) -> dict:
    """
    C in CAN SLIM: Current quarterly EPS should be up >=25% YoY.
    Check last 3 quarters for consistency.
    """
    result = {
        "quarterly_yoy": [],
        "sales_yoy": [],
        "passes": False,
        "consecutive_beats": 0,
        "latest_eps_growth": None,
        "latest_sales_growth": None,
        "status": "FAIL",
    }

    q_income = t.quarterly_income_stmt
    if q_income is None or q_income.empty:
        return result

    # Net Income by quarter
    ni = _extract_row(q_income, ["Net Income", "Net Income Common Stockholders"])
    rev = _extract_row(q_income, ["Total Revenue", "Revenue"])

    if ni is not None and len(ni) >= 5:
        # Compare each quarter to same quarter prior year
        vals = list(zip(ni.index, ni.values))
        for i in range(len(vals)):
            # Find the quarter ~4 periods back (same quarter last year)
            if i + 4 < len(vals):
                current_val = vals[i][1]
                prior_val = vals[i + 4][1]
                growth = _safe_pct(current_val, prior_val)
                if growth is not None:
                    result["quarterly_yoy"].append({
                        "quarter": str(vals[i][0].date()),
                        "current": float(current_val),
                        "prior_year": float(prior_val),
                        "growth_pct": round(growth, 1),
                    })

        if result["quarterly_yoy"]:
            result["latest_eps_growth"] = result["quarterly_yoy"][0]["growth_pct"]

            # Count consecutive quarters with >25% growth
            count = 0
            for q in result["quarterly_yoy"]:
                if q["growth_pct"] >= 25:
                    count += 1
                else:
                    break
            result["consecutive_beats"] = count

            if count >= 2:
                result["passes"] = True
                result["status"] = "PASS"
            elif count >= 1:
                result["status"] = "PARTIAL"

    # Sales/Revenue growth
    if rev is not None and len(rev) >= 5:
        vals = list(zip(rev.index, rev.values))
        for i in range(min(3, len(vals) - 4)):
            growth = _safe_pct(vals[i][1], vals[i + 4][1])
            if growth is not None:
                result["sales_yoy"].append({
                    "quarter": str(vals[i][0].date()),
                    "growth_pct": round(growth, 1),
                })
        if result["sales_yoy"]:
            result["latest_sales_growth"] = result["sales_yoy"][0]["growth_pct"]

    return result


# ========================================================================== #
# A — Annual Earnings Growth
# ========================================================================== #


def analyze_annual_earnings(t: yf.Ticker) -> dict:
    """
    A in CAN SLIM: Annual EPS should show consistent growth over 3-5 years.
    Also check ROE (O'Neil wants >17%).
    """
    result = {
        "annual_eps": [],
        "eps_cagr_3y": None,
        "roe": None,
        "roe_passes": False,
        "stability": "unknown",
        "passes": False,
        "status": "FAIL",
    }

    info = t.info or {}
    a_income = t.income_stmt

    # ROE
    roe = info.get("returnOnEquity")
    if roe:
        result["roe"] = round(roe * 100, 1)
        result["roe_passes"] = roe >= 0.17

    if a_income is None or a_income.empty:
        return result

    ni = _extract_row(a_income, ["Net Income", "Net Income Common Stockholders"])
    if ni is not None and len(ni) >= 3:
        vals = list(zip(ni.index, ni.values))
        for d, v in vals:
            result["annual_eps"].append({
                "year": str(d.date()),
                "value": float(v),
            })

        # 3-year CAGR
        if len(vals) >= 4 and vals[-1][1] > 0 and vals[0][1] > 0:
            years = (vals[0][0] - vals[-1][0]).days / 365.25
            if years > 0:
                cagr = (vals[0][1] / vals[-1][1]) ** (1 / years) - 1
                result["eps_cagr_3y"] = round(cagr * 100, 1)

        # Stability: how many years had positive growth?
        growth_years = 0
        decline_years = 0
        for i in range(len(vals) - 1):
            if vals[i][1] > vals[i + 1][1]:
                growth_years += 1
            else:
                decline_years += 1

        if decline_years == 0:
            result["stability"] = "consistent"
        elif decline_years <= 1:
            result["stability"] = "mostly consistent"
        else:
            result["stability"] = "erratic"

        if result["eps_cagr_3y"] and result["eps_cagr_3y"] > 15 and result["stability"] != "erratic":
            result["passes"] = True
            result["status"] = "PASS"
        elif result["eps_cagr_3y"] and result["eps_cagr_3y"] > 10:
            result["status"] = "PARTIAL"

    return result


# ========================================================================== #
# N — New (Catalysts, News, New Highs)
# ========================================================================== #


def analyze_catalysts(t: yf.Ticker, price_data: Optional[pd.DataFrame] = None) -> dict:
    """
    N in CAN SLIM: Look for catalysts — new products, management changes,
    industry shifts, new 52-week highs.
    """
    result = {
        "at_52w_high": False,
        "news_headlines": [],
        "sector_context": None,
        "status": "UNKNOWN",
    }

    info = t.info or {}

    # 52-week high check
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    high_52w = info.get("fiftyTwoWeekHigh")
    if current and high_52w and high_52w > 0:
        pct = (current / high_52w - 1) * 100
        result["at_52w_high"] = pct >= -5  # within 5% counts
        result["pct_from_high"] = round(pct, 1)

    # News headlines
    try:
        news = t.news
        if news:
            for item in news[:8]:
                headline = {
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                }
                # Extract publish time if available
                pub_time = item.get("providerPublishTime")
                if pub_time:
                    headline["date"] = str(pd.Timestamp(pub_time, unit="s").date())
                result["news_headlines"].append(headline)
    except Exception:
        pass

    # Sector/Industry context
    result["sector"] = info.get("sector")
    result["industry"] = info.get("industry")
    result["business_summary"] = (info.get("longBusinessSummary") or "")[:300]

    if result["at_52w_high"] and result["news_headlines"]:
        result["status"] = "STRONG"
    elif result["at_52w_high"]:
        result["status"] = "PASS"
    else:
        result["status"] = "PARTIAL"

    return result


# ========================================================================== #
# S — Supply and Demand
# ========================================================================== #


def analyze_supply_demand(t: yf.Ticker, price_df: Optional[pd.DataFrame] = None) -> dict:
    """
    S in CAN SLIM: Check shares outstanding, float, and volume patterns.
    Smaller float + increasing volume on advances = stronger demand.
    """
    result = {
        "shares_outstanding": None,
        "float_shares": None,
        "float_pct": None,
        "avg_volume_50d": None,
        "avg_volume_10d": None,
        "volume_trend": "unknown",
        "up_down_volume_ratio": None,
        "status": "UNKNOWN",
    }

    info = t.info or {}

    result["shares_outstanding"] = info.get("sharesOutstanding")
    result["float_shares"] = info.get("floatShares")
    result["avg_volume_50d"] = info.get("averageVolume")
    result["avg_volume_10d"] = info.get("averageDailyVolume10Day")

    if result["shares_outstanding"] and result["float_shares"]:
        result["float_pct"] = round(
            result["float_shares"] / result["shares_outstanding"] * 100, 1
        )

    # Volume trend: is recent volume above average?
    if result["avg_volume_10d"] and result["avg_volume_50d"]:
        if result["avg_volume_50d"] > 0:
            vol_ratio = result["avg_volume_10d"] / result["avg_volume_50d"]
            if vol_ratio > 1.2:
                result["volume_trend"] = "INCREASING"
            elif vol_ratio < 0.8:
                result["volume_trend"] = "DECREASING"
            else:
                result["volume_trend"] = "STABLE"

    # Up/Down volume ratio from price data
    if price_df is not None and len(price_df) >= 20:
        close = price_df["Close"]
        volume = price_df["Volume"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        if isinstance(volume, pd.DataFrame):
            volume = volume.iloc[:, 0]

        recent = price_df.tail(20)
        close_r = recent["Close"] if not isinstance(recent["Close"], pd.DataFrame) else recent["Close"].iloc[:, 0]
        vol_r = recent["Volume"] if not isinstance(recent["Volume"], pd.DataFrame) else recent["Volume"].iloc[:, 0]
        changes = close_r.pct_change()

        up_vol = vol_r[changes > 0].sum()
        down_vol = vol_r[changes < 0].sum()
        if down_vol > 0:
            result["up_down_volume_ratio"] = round(float(up_vol / down_vol), 2)

    # Assessment
    good_signs = 0
    if result["volume_trend"] == "INCREASING":
        good_signs += 1
    if result["up_down_volume_ratio"] and result["up_down_volume_ratio"] > 1.2:
        good_signs += 1
    if result["float_pct"] and result["float_pct"] < 70:
        good_signs += 1

    result["status"] = "PASS" if good_signs >= 2 else "PARTIAL" if good_signs >= 1 else "FAIL"

    return result


# ========================================================================== #
# L — Leader or Laggard
# ========================================================================== #


def analyze_leadership(
    ticker: str,
    signals: Optional[dict] = None,
    all_prices: Optional[dict] = None,
) -> dict:
    """
    L in CAN SLIM: Is this stock a leader in its industry group?
    RS rank should be >80 (top 20%).
    """
    result = {
        "rs_rank_pct": None,
        "sector_performance_6m": None,
        "stock_vs_sector": None,
        "is_leader": False,
        "status": "UNKNOWN",
    }

    if signals and ticker in signals:
        df = signals[ticker]
        if not df.empty:
            last = df.iloc[-1]
            result["rs_rank_pct"] = last.get("mom_rank_pct")

            if result["rs_rank_pct"] and result["rs_rank_pct"] >= 80:
                result["is_leader"] = True
                result["status"] = "LEADER"
            elif result["rs_rank_pct"] and result["rs_rank_pct"] >= 60:
                result["status"] = "OK"
            else:
                result["status"] = "LAGGARD"

    return result


# ========================================================================== #
# I — Institutional Sponsorship
# ========================================================================== #


def analyze_institutional(t: yf.Ticker) -> dict:
    """
    I in CAN SLIM: Is institutional ownership present and growing?
    Want to see quality institutional holders, not just any.
    """
    result = {
        "institutional_pct": None,
        "institutional_holders_count": None,
        "top_holders": [],
        "status": "UNKNOWN",
    }

    info = t.info or {}
    result["institutional_pct"] = info.get("heldPercentInstitutions")
    if result["institutional_pct"]:
        result["institutional_pct"] = round(result["institutional_pct"] * 100, 1)

    try:
        holders = t.institutional_holders
        if holders is not None and not holders.empty:
            result["institutional_holders_count"] = len(holders)
            for _, row in holders.head(5).iterrows():
                result["top_holders"].append({
                    "name": str(row.get("Holder", ""))[:40],
                    "shares": int(row.get("Shares", 0)) if pd.notna(row.get("Shares")) else 0,
                    "pct": round(float(row.get("pctHeld", 0)) * 100, 2) if pd.notna(row.get("pctHeld")) else None,
                })
    except Exception:
        pass

    if result["institutional_pct"] and result["institutional_pct"] > 30:
        result["status"] = "PASS"
    elif result["institutional_pct"] and result["institutional_pct"] > 10:
        result["status"] = "PARTIAL"
    else:
        result["status"] = "LOW"

    return result


# ========================================================================== #
# Sector Analysis
# ========================================================================== #


def analyze_sector(
    ticker: str,
    t: yf.Ticker,
    all_prices: Optional[dict] = None,
) -> dict:
    """
    Sector-level analysis: how is the stock's sector performing?
    Are peers trending similarly? What are the macro drivers?
    """
    result = {
        "sector": None,
        "industry": None,
        "peers_trending": 0,
        "peers_total": 0,
        "sector_momentum": None,
        "structural_or_cyclical": "unknown",
    }

    info = t.info or {}
    result["sector"] = info.get("sector")
    result["industry"] = info.get("industry")

    # Find peers in the same sector from our price data
    if all_prices and result["sector"]:
        peer_count = 0
        peer_trending = 0
        for peer_ticker, peer_df in all_prices.items():
            if peer_ticker == ticker:
                continue
            if isinstance(peer_df.columns, pd.MultiIndex):
                peer_df.columns = peer_df.columns.get_level_values(0)
            if "Close" not in peer_df.columns or len(peer_df) < 200:
                continue

            close = peer_df["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

            # Check if peer is in same sector (we'd need metadata for this)
            # For now, just count general trending stats
            sma_200 = close.rolling(200).mean()
            if not sma_200.empty and pd.notna(sma_200.iloc[-1]):
                if close.iloc[-1] > sma_200.iloc[-1]:
                    peer_trending += 1
                peer_count += 1

        result["peers_trending"] = peer_trending
        result["peers_total"] = peer_count
        if peer_count > 0:
            result["sector_momentum"] = round(peer_trending / peer_count * 100, 1)

    return result


# ========================================================================== #
# Combined Deep Dive
# ========================================================================== #


def deep_dive(
    yf_ticker: str,
    signals: Optional[dict] = None,
    all_prices: Optional[dict] = None,
) -> dict:
    """Run full CAN SLIM + sector analysis on a single stock."""
    import time

    logger.info("Deep dive: %s", yf_ticker)
    t = yf.Ticker(yf_ticker)
    info = t.info or {}

    # Get price data for volume analysis
    price_df = None
    if all_prices and yf_ticker in all_prices:
        price_df = all_prices[yf_ticker]
        if isinstance(price_df.columns, pd.MultiIndex):
            price_df.columns = price_df.columns.get_level_values(0)

    time.sleep(0.3)

    return {
        "ticker": yf_ticker,
        "name": info.get("shortName", yf_ticker),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "C": analyze_current_earnings(t),
        "A": analyze_annual_earnings(t),
        "N": analyze_catalysts(t, price_df),
        "S": analyze_supply_demand(t, price_df),
        "L": analyze_leadership(yf_ticker, signals, all_prices),
        "I": analyze_institutional(t),
        "sector_analysis": analyze_sector(yf_ticker, t, all_prices),
    }


def print_deep_dive(data: dict, regime_on: bool = False) -> None:
    """Pretty-print the full CAN SLIM deep dive."""
    sep = "=" * 64
    thin = "─" * 64

    print(f"\n{sep}")
    print(f"  DEEP DIVE: {data['ticker']}  —  {data['name']}")
    print(f"  {data.get('sector', '?')}  /  {data.get('industry', '?')}")
    if data.get("market_cap"):
        print(f"  Market Cap: EUR {data['market_cap']:,.0f}")
    print(sep)

    # --- C: Current Quarterly Earnings ---
    c = data["C"]
    print(f"\n  C — CURRENT QUARTERLY EARNINGS  [{c['status']}]")
    if c["quarterly_yoy"]:
        print(f"    {'Quarter':<14} {'Current':>14} {'Prior Year':>14} {'YoY Growth':>12}")
        for q in c["quarterly_yoy"][:4]:
            marker = " ✓" if q["growth_pct"] >= 25 else " ✗" if q["growth_pct"] < 0 else ""
            print(f"    {q['quarter']:<14} {q['current']:>14,.0f} {q['prior_year']:>14,.0f} {q['growth_pct']:>+10.1f}%{marker}")
        print(f"    Consecutive quarters >25% growth: {c['consecutive_beats']}")
        if c["sales_yoy"]:
            print(f"    Latest quarter sales growth: {c['sales_yoy'][0]['growth_pct']:+.1f}%")
    else:
        print("    No quarterly data available")

    # --- A: Annual Earnings Growth ---
    a = data["A"]
    print(f"\n  A — ANNUAL EARNINGS GROWTH  [{a['status']}]")
    if a["annual_eps"]:
        for yr in a["annual_eps"][:5]:
            print(f"    {yr['year']:<14} {yr['value']:>14,.0f}")
        if a["eps_cagr_3y"] is not None:
            print(f"    3-Year CAGR: {a['eps_cagr_3y']:+.1f}%")
        print(f"    Stability: {a['stability']}")
        print(f"    ROE: {a['roe']:.1f}%" if a["roe"] else "    ROE: N/A")
        if a["roe_passes"]:
            print("    ROE ≥ 17%: ✓")
        elif a["roe"]:
            print("    ROE ≥ 17%: ✗")
    else:
        print("    No annual data available")

    # --- N: New / Catalysts ---
    n = data["N"]
    print(f"\n  N — CATALYSTS & NEWS  [{n['status']}]")
    if n.get("at_52w_high"):
        print(f"    ✓ At or near 52-week high ({n.get('pct_from_high', 0):+.1f}%)")
    else:
        print(f"    ✗ Below 52-week high ({n.get('pct_from_high', 0):+.1f}%)")

    if n["news_headlines"]:
        print("    Recent news:")
        for h in n["news_headlines"][:5]:
            date_str = h.get("date", "")
            title = h["title"][:70]
            print(f"      {date_str:>12}  {title}")
    else:
        print("    No recent news available")

    if n.get("business_summary"):
        print(f"    Business: {n['business_summary'][:200]}...")

    # --- S: Supply and Demand ---
    s = data["S"]
    print(f"\n  S — SUPPLY & DEMAND  [{s['status']}]")
    if s["shares_outstanding"]:
        print(f"    Shares outstanding: {s['shares_outstanding']:>12,.0f}")
    if s["float_pct"]:
        print(f"    Float: {s['float_pct']:.1f}%")
    if s["avg_volume_50d"]:
        print(f"    Avg volume (50d): {s['avg_volume_50d']:>12,.0f}")
    print(f"    Volume trend: {s['volume_trend']}")
    if s["up_down_volume_ratio"]:
        marker = " (accumulation)" if s["up_down_volume_ratio"] > 1.2 else " (distribution)" if s["up_down_volume_ratio"] < 0.8 else ""
        print(f"    Up/Down volume ratio (20d): {s['up_down_volume_ratio']:.2f}{marker}")

    # --- L: Leader or Laggard ---
    l = data["L"]
    print(f"\n  L — LEADER OR LAGGARD  [{l['status']}]")
    if l["rs_rank_pct"] is not None:
        print(f"    Relative Strength rank: {l['rs_rank_pct']:.0f}th percentile")
    print(f"    Leader status: {'YES — top 20%' if l['is_leader'] else 'No'}")

    # --- I: Institutional Sponsorship ---
    inst = data["I"]
    print(f"\n  I — INSTITUTIONAL SPONSORSHIP  [{inst['status']}]")
    if inst["institutional_pct"]:
        print(f"    Institutional ownership: {inst['institutional_pct']:.1f}%")
    if inst["institutional_holders_count"]:
        print(f"    Number of institutional holders: {inst['institutional_holders_count']}")
    if inst["top_holders"]:
        print("    Top holders:")
        for h in inst["top_holders"][:3]:
            pct_str = f"{h['pct']:.1f}%" if h["pct"] else "?"
            print(f"      {h['name']:<40} {pct_str:>6}")

    # --- M: Market Direction ---
    print(f"\n  M — MARKET DIRECTION")
    if regime_on:
        print("    Regime: ON (bullish) ✓")
        print("    Action: ELIGIBLE for entry")
    else:
        print("    Regime: OFF (bearish) ✗")
        print("    Action: WATCHLIST ONLY — do not enter")

    # --- Sector Context ---
    sec = data["sector_analysis"]
    print(f"\n  SECTOR CONTEXT")
    if sec["sector_momentum"] is not None:
        print(f"    Broad market: {sec['peers_trending']}/{sec['peers_total']} stocks above 200-day SMA ({sec['sector_momentum']:.0f}%)")

    # --- Composite Score ---
    print(f"\n  {thin}")
    print("  CAN SLIM SCORECARD")
    print(f"  {thin}")

    score = 0
    total = 7
    criteria = [
        ("C", c["status"], "Current quarterly earnings >25% YoY"),
        ("A", a["status"], "Annual earnings growth consistent"),
        ("N", n["status"], "Catalysts / new highs / news flow"),
        ("S", s["status"], "Supply/demand (volume confirms)"),
        ("L", l["status"], "Leader in sector (RS rank >80)"),
        ("I", inst["status"], "Institutional sponsorship"),
        ("M", "PASS" if regime_on else "FAIL", "Market direction (regime)"),
    ]

    for letter, status, desc in criteria:
        if status in ("PASS", "STRONG", "LEADER"):
            icon = "✓"
            score += 1
        elif status == "PARTIAL":
            icon = "◐"
            score += 0.5
        else:
            icon = "✗"
        print(f"    {icon}  {letter} — {desc} [{status}]")

    print(f"\n    Score: {score:.0f}/{total}")

    if score >= 5.5:
        verdict = "STRONG BUY candidate (when regime turns ON)"
    elif score >= 4:
        verdict = "WATCHLIST — fundamentals mostly support the trend"
    elif score >= 2.5:
        verdict = "WEAK — trend lacks fundamental confirmation"
    else:
        verdict = "AVOID — trend is not supported by fundamentals"

    print(f"    Verdict: {verdict}")
    print()
