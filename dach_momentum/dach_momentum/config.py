"""
Project configuration: paths, constants, and index source definitions.

All tunable parameters for the strategy live here so that we have
one place to look when we need to change something.
"""
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
UNIVERSE_CSV = DATA_DIR / "universe.csv"
PRICES_DIR = DATA_DIR / "prices"

for _d in (DATA_DIR, CACHE_DIR, PRICES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Index sources
#
# URL points to the English Wikipedia page with a constituent table.
# `suffix` is the ticker suffix yfinance expects for that exchange.
# `country` is a free-text label used in the output universe CSV.
#
# Note: Some URLs may break if Wikipedia restructures the page.
# If a scrape fails, the error is logged and the index is skipped.
# --------------------------------------------------------------------------- #

INDEX_SOURCES = {
    # --- Germany ---
    "DAX": {
        "url": "https://en.wikipedia.org/wiki/DAX",
        "country": "Germany",
        "suffix": ".DE",
    },
    "MDAX": {
        "url": "https://en.wikipedia.org/wiki/MDAX",
        "country": "Germany",
        "suffix": ".DE",
    },
    "SDAX": {
        "url": "https://en.wikipedia.org/wiki/SDAX",
        "country": "Germany",
        "suffix": ".DE",
    },
    "TecDAX": {
        "url": "https://en.wikipedia.org/wiki/TecDAX",
        "country": "Germany",
        "suffix": ".DE",
    },
    "ATX": {
        "url": "https://en.wikipedia.org/wiki/Austrian_Traded_Index",
        "country": "Austria",
        "suffix": ".VI",
    },
    "SMI": {
        "url": "https://en.wikipedia.org/wiki/Swiss_Market_Index",
        "country": "Switzerland",
        "suffix": ".SW",
    },
    "SMIM": {
        "url": "https://en.wikipedia.org/wiki/SMI_MID",
        "country": "Switzerland",
        "suffix": ".SW",
    },
    # --- France ---
    "CAC_Mid_60": {
        "url": "https://en.wikipedia.org/wiki/CAC_Mid_60",
        "country": "France",
        "suffix": ".PA",
    },
    "SBF_120": {
        "url": "https://en.wikipedia.org/wiki/SBF_120",
        "country": "France",
        "suffix": ".PA",
    },
    # --- Netherlands ---
    "AEX": {
        "url": "https://en.wikipedia.org/wiki/AEX_index",
        "country": "Netherlands",
        "suffix": ".AS",
    },
    "AMX": {
        "url": "https://en.wikipedia.org/wiki/AMX_index",
        "country": "Netherlands",
        "suffix": ".AS",
    },
    # --- Belgium ---
    "BEL_20": {
        "url": "https://en.wikipedia.org/wiki/BEL_20",
        "country": "Belgium",
        "suffix": ".BR",
    },
    # --- Italy ---
    "FTSE_MIB": {
        "url": "https://en.wikipedia.org/wiki/FTSE_MIB",
        "country": "Italy",
        "suffix": ".MI",
    },
    "FTSE_Italia_Mid": {
        "url": "https://en.wikipedia.org/wiki/FTSE_Italia_Mid_Cap",
        "country": "Italy",
        "suffix": ".MI",
    },
    # --- Spain ---
    "IBEX_35": {
        "url": "https://en.wikipedia.org/wiki/IBEX_35",
        "country": "Spain",
        "suffix": ".MC",
    },
    # --- Sweden ---
    "OMX_30": {
        "url": "https://en.wikipedia.org/wiki/OMX_Stockholm_30",
        "country": "Sweden",
        "suffix": ".ST",
    },
    "OMX_Mid_SE": {
        "url": "https://en.wikipedia.org/wiki/OMX_Stockholm_Mid_Cap",
        "country": "Sweden",
        "suffix": ".ST",
    },
    "OMX_Small_SE": {
        "url": "https://en.wikipedia.org/wiki/OMX_Stockholm_Small_Cap",
        "country": "Sweden",
        "suffix": ".ST",
    },
    # --- Denmark ---
    "C25": {
        "url": "https://en.wikipedia.org/wiki/OMX_Copenhagen_25",
        "country": "Denmark",
        "suffix": ".CO",
    },
    # --- Finland ---
    "OMX_H25": {
        "url": "https://en.wikipedia.org/wiki/OMX_Helsinki_25",
        "country": "Finland",
        "suffix": ".HE",
    },
    # --- Norway ---
    "OBX": {
        "url": "https://en.wikipedia.org/wiki/OBX_Index",
        "country": "Norway",
        "suffix": ".OL",
    },
    # --- Portugal ---
    "PSI": {
        "url": "https://en.wikipedia.org/wiki/PSI-20",
        "country": "Portugal",
        "suffix": ".LS",
    },
    # --- Poland ---
    "WIG20": {
        "url": "https://en.wikipedia.org/wiki/WIG20",
        "country": "Poland",
        "suffix": ".WA",
    },
    "mWIG40": {
        "url": "https://en.wikipedia.org/wiki/MWIG40",
        "country": "Poland",
        "suffix": ".WA",
    },
    # --- Netherlands small ---
    "AScX": {
        "url": "https://en.wikipedia.org/wiki/AScX",
        "country": "Netherlands",
        "suffix": ".AS",
    },
    # --- UK ---
    "FTSE_250": {
        "url": "https://en.wikipedia.org/wiki/FTSE_250_Index",
        "country": "UK",
        "suffix": ".L",
    },
    # --- Greece ---
    "ATHEX": {
        "url": "https://en.wikipedia.org/wiki/FTSE/Athex_Large_Cap",
        "country": "Greece",
        "suffix": ".AT",
    },
}

# --------------------------------------------------------------------------- #
# Universe filter parameters
# (Applied at Step 2 when we have market-cap / volume data.)
# --------------------------------------------------------------------------- #

MIN_MARKET_CAP_EUR = 100_000_000       # EUR 100M floor
MAX_MARKET_CAP_EUR = 2_000_000_000     # EUR 2B ceiling
MIN_AVG_DAILY_VOLUME_EUR = 150_000     # EUR 150k ADV floor (60-day)
MIN_FREE_FLOAT_PCT = 25.0              # 25% minimum free float
MIN_LISTING_AGE_DAYS = 365             # 1 year minimum listing history

# Sectors to exclude.  Financials have different quality metrics
# (Novy-Marx gross profitability doesn't apply to banks/insurers).
# Real estate excluded because it is interest-rate driven rather
# than trend-driven in the sense our strategy targets.
EXCLUDED_SECTORS = {
    "Financial Services",
    "Financials",
    "Banks",
    "Insurance",
    "Real Estate",
    "Immobilien",
    "Finanzdienstleister",
}

# --------------------------------------------------------------------------- #
# Strategy parameters  (v3 spec)
# --------------------------------------------------------------------------- #

# -- Regime filter -----------------------------------------------------------
REGIME_INDEX_TICKER = "^CDAXI"        # CDAX Composite (yfinance symbol)
REGIME_MA_WEEKS = 40                   # 40-week SMA for regime filter

# -- Momentum ----------------------------------------------------------------
MOMENTUM_LOOKBACK_DAYS = 252           # ~12 months of trading days
MOMENTUM_SKIP_DAYS = 21               # skip most recent month (reversal)

# -- Trend Template (Minervini) ---------------------------------------------
TREND_SMA_SHORT = 50                   # 50-day SMA
TREND_SMA_MED = 150                    # 150-day SMA
TREND_SMA_LONG = 200                   # 200-day SMA
TREND_52W_HIGH_PROXIMITY = 0.90        # price >= 90% of 52-week high
TREND_52W_LOW_DISTANCE = 1.30          # price >= 130% of 52-week low

# -- Quality -----------------------------------------------------------------
QUALITY_GROSS_PROF_PERCENTILE = 50     # above universe median
QUALITY_MAX_NET_DEBT_EBITDA = 3.0      # net debt / EBITDA cap

# -- Position sizing ---------------------------------------------------------
MAX_POSITIONS = 15
MIN_POSITIONS = 8
RISK_PER_TRADE_PCT = 1.0              # 1% of portfolio equity risked per trade
MAX_POSITION_PCT = 12.0               # hard cap on single position weight
MAX_SECTOR_PCT = 30.0                 # max single sector weight
MAX_TOP3_SECTOR_PCT = 60.0            # max top-3 sector concentration
MAX_PCT_OF_ADV = 5.0                  # position <= 5% of 20-day ADV

# -- Exits -------------------------------------------------------------------
INITIAL_HARD_STOP_PCT = 10.0          # 10% initial hard stop
INITIAL_HARD_STOP_ATR_MULT = 2.5      # or 2.5x ATR, whichever is wider
HARD_STOP_CEILING_PCT = 15.0          # never wider than 15%
PROFIT_THRESHOLD_TO_TRAIL = 20.0      # switch to MA-only exit after +20%
EXIT_MA_WEEKS = 30                     # 30-week SMA for individual exits

# -- Risk management ---------------------------------------------------------
DRAWDOWN_CIRCUIT_BREAKER_PCT = 15.0   # pause new entries if 60-day DD > 15%
DRAWDOWN_LOOKBACK_DAYS = 60

# -- Transaction costs (DKB) ------------------------------------------------
COMMISSION_PER_TRADE_EUR = 10.0
ESTIMATED_SPREAD_BPS = 50             # 50 bps one-way spread estimate
