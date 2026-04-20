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

# --------------------------------------------------------------------------- #
# "Get Rich Quick" strategy parameters
#
# Aggressive concentrated breakout strategy:
# - Fewer positions, larger bets
# - Only top-percentile momentum names
# - Breakout entries: near 52-week highs with volume confirmation
# - Tighter stops, faster trailing
# --------------------------------------------------------------------------- #

RQ_MAX_POSITIONS = 5                   # concentrated: max 5 holdings
RQ_RISK_PER_TRADE_PCT = 2.0           # 2% risk per trade (aggressive)
RQ_MAX_POSITION_PCT = 25.0            # up to 25% in a single name
RQ_MOMENTUM_PERCENTILE = 80           # top 20% momentum only
RQ_HIGH_PROXIMITY_PCT = 0.97          # price within 3% of 52-week high
RQ_VOLUME_SURGE_MULT = 1.5            # 10-day vol >= 1.5x 50-day vol
RQ_INITIAL_HARD_STOP_PCT = 7.0        # tighter 7% hard stop
RQ_HARD_STOP_ATR_MULT = 2.0           # 2x ATR stop (tighter)
RQ_HARD_STOP_CEILING_PCT = 10.0       # never wider than 10%
RQ_PROFIT_THRESHOLD_TO_TRAIL = 15.0   # trail earlier at +15%
RQ_MIN_QUALITY_SCORE = 3              # require decent quality score

# --------------------------------------------------------------------------- #
# "Super Rich" hybrid: pattern recognition + momentum/quality confirmation
#
# Pattern detection identifies the SETUP structure.
# Momentum + quality confirms TIMING and context.
#
# Entry requires ALL of:
#   - Pattern score >= 50 (VCP, Cup&Handle, Pocket Pivot, Flag, Double Bottom)
#   - Momentum rank >= top 30%
#   - Quality score >= 3 (volume/trend-health signals)
#   - Rising relative strength
#
# Ranking: 50% pattern score + 30% momentum + 20% quality
# --------------------------------------------------------------------------- #

SR_MAX_POSITIONS = 5                   # concentrated: max 5 holdings
SR_RISK_PER_TRADE_PCT = 2.0           # 2% risk per trade
SR_MAX_POSITION_PCT = 30.0            # up to 30% in a single name
SR_MIN_PATTERN_SCORE = 50             # pattern bar (slightly relaxed for hybrid)
SR_MIN_MOMENTUM_12_1 = 0.20           # require 20% 12-1 month momentum
SR_MIN_QUALITY_SCORE = 3              # quality score (3/5 signals)
SR_INITIAL_HARD_STOP_PCT = 7.0        # 7% hard stop
SR_HARD_STOP_ATR_MULT = 2.0           # 2x ATR stop
SR_HARD_STOP_CEILING_PCT = 10.0       # never wider than 10%
SR_PROFIT_THRESHOLD_TO_TRAIL = 15.0   # trail at +15%

# Asymmetric stop management (first-principles: convert near-wins into wins)
# +10% gain → stop to breakeven; +20% → lock 5%; +35% → lock 15%

# --------------------------------------------------------------------------- #
# "Cash Machine" high-frequency compounding strategy
#
# Insight: more trades with consistent edge compound faster than few
# concentrated big bets. Maximize trade frequency and win rate.
# - Diversified (15 positions)
# - Short holding period (10-week SMA exit instead of 30-week)
# - Early trailing (+8% instead of +20%) to lock gains quickly
# - Lower quality bar for MORE setups per year
# - Quick turnover = high compounding frequency
# --------------------------------------------------------------------------- #

CM_MAX_POSITIONS = 15                  # diversified: max 15 holdings
CM_RISK_PER_TRADE_PCT = 1.0           # 1% risk per trade (standard)
CM_MAX_POSITION_PCT = 10.0            # up to 10% per position
CM_MIN_QUALITY_SCORE = 2              # lower bar = more setups
CM_INITIAL_HARD_STOP_PCT = 8.0        # moderate stop
CM_HARD_STOP_ATR_MULT = 2.0           # 2x ATR stop
CM_HARD_STOP_CEILING_PCT = 12.0       # never wider than 12%
CM_PROFIT_THRESHOLD_TO_TRAIL = 8.0    # trail very early at +8%
CM_EXIT_SMA_DAYS = 50                 # 10-week SMA exit (faster turnover)

# --------------------------------------------------------------------------- #
# V2 architecture: Cross-sectional momentum in high-volatility breakouts
#
# Design principles (directive from V2 review):
#   1) Stop parameter optimization on narrow bands.
#   2) Replace absolute thresholds with cross-sectional ranking.
#   3) Add multi-layer macro regime gating (not just binary CDAX trend).
#   4) Volatility-adjusted position sizing (equal risk contribution via ATR).
#   5) Rigorous transaction cost model (spread + market impact + slippage).
#
# Goal: prove the Cohen's d = 0.28 edge survives realistic friction.
# --------------------------------------------------------------------------- #

# -- Cross-sectional selection ----------------------------------------------
V2_TOP_N_PCT = 10.0                    # select top 10% of momentum universe
V2_MIN_CANDIDATES_PER_DATE = 5         # need at least 5 names ranked to trade
V2_MIN_MOM_RANK_PCT = 90.0             # fallback absolute floor (percentile)
V2_BREAKOUT_WINDOW_DAYS = 63           # 3-month high breakout requirement
V2_MIN_HVOL_PCT = 0.25                 # min 25% annualised vol (high-vol regime)

# -- Multi-layer macro regime -----------------------------------------------
V2_REGIME_TREND_MA_WEEKS = 40          # layer 1: CDAX > 40w SMA
V2_REGIME_BREADTH_MIN_PCT = 45.0       # layer 2: >=45% of universe above 200d
V2_REGIME_BREADTH_LOOKBACK = 200       # breadth SMA lookback (daily bars)
V2_REGIME_VOL_MAX_HVOL = 0.35          # layer 3: CDAX hvol <= 35% annualised
V2_REGIME_VOL_LOOKBACK = 20            # realized vol window
V2_REGIME_DISPERSION_MIN = 0.15        # layer 4: top10-bot10 mom spread >= 15%

# -- Position sizing (volatility-adjusted / equal risk contribution) --------
# Inverse-vol sizing: notional_i = equity * vol_budget / stock_vol_i
# vol_budget = V2_TARGET_PORTFOLIO_VOL / V2_MAX_POSITIONS
# (conservative — assumes perfectly correlated holdings as upper bound)
# Final shares = min(vol_adjusted, atr_risk_cap, notional_cap)
V2_TARGET_PORTFOLIO_VOL = 0.15         # 15% annualised portfolio vol target
V2_SIZING_VOL_LOOKBACK = 60            # 60-day realized vol for stable sizing
V2_SIZING_VOL_FLOOR = 0.15             # min 15% vol (cap notional on low-vol names)
V2_SIZING_VOL_CEILING = 0.80           # max 80% vol (floor notional on extreme names)
V2_RISK_PER_TRADE_PCT = 1.0            # 1% of equity risked per position (ATR cap)
V2_ATR_STOP_MULT = 2.5                 # stop = 2.5 * ATR_14 below entry
V2_MAX_POSITION_PCT = 15.0             # cap on single-name weight (notional cap)
V2_MAX_POSITIONS = 10                  # max concurrent holdings
V2_MIN_POSITION_EUR = 500.0            # skip dust positions

# -- Transaction cost model -------------------------------------------------
# Total cost = commission + half_spread + market_impact + slippage
V2_COMMISSION_EUR = 10.0               # fixed DKB-style commission
V2_HALF_SPREAD_BPS = 25                # 25 bps half-spread (both sides)
V2_IMPACT_COEFF = 0.10                 # sqrt-model: impact = coeff * σ * sqrt(q/ADV)
V2_SLIPPAGE_BPS = 5                    # fixed slippage buffer
V2_MAX_PCT_OF_ADV = 5.0                # never trade >5% of 20-day ADV
V2_ADV_LOOKBACK = 20                   # 20-day ADV window

# -- Exits ------------------------------------------------------------------
V2_EXIT_SMA_DAYS = 100                 # 20-week SMA trailing exit
V2_PROFIT_TRAIL_THRESHOLD = 20.0       # switch to SMA trailing after +20%
V2_TIME_STOP_DAYS = 180                # exit if no new high in 180 days

# --------------------------------------------------------------------------- #
# KnockoutSwing v1.0 — KO Certificate Swing Trading on Major Indices
#
# Leveraged swing trend-following via knockout certificates.
# Structurally different from DACH momentum: trades 4 indices (not stocks),
# daily bars, both long AND short, KO barrier simulation, staged exits.
#
# Mandate mapping (from roadmap):
#   M1:  Trend filter          M7:  Portfolio cap
#   M2:  Structural stop       M8:  Hold horizon / time stop
#   M3:  3x R:R minimum        M9:  Staged exits (1/3, 1/3, 1/3)
#   M4:  Barrier rule           M10: Weekly rhythm
#   M5:  Leverage cap           M11: Frequency cap
#   M6:  Position sizing        M12: Quarterly regime check
# --------------------------------------------------------------------------- #

# -- Universe (4 indices only) ----------------------------------------------
KO_INDICES = {
    "^GDAXI":   "DAX",
    "^GSPC":    "S&P 500",
    "^NDX":     "Nasdaq 100",
    "^STOXX50E": "Euro Stoxx 50",
}

# -- Trend filter (M1) ------------------------------------------------------
KO_EMA_FAST = 50
KO_EMA_SLOW = 200

# -- Setup A: Trend Pullback (M2) -------------------------------------------
KO_RSI_PERIOD = 14
KO_RSI_OVERSOLD = 40                    # RSI must dip below this
KO_RSI_OVERBOUGHT = 60                  # for short-side pullbacks
KO_PULLBACK_LOOKBACK = 5                # bars to look back for pullback sequence

# -- Setup B: Consolidation Breakout (M2) -----------------------------------
KO_CONSOL_MIN_DAYS = 20                 # ~4 weeks
KO_CONSOL_MAX_DAYS = 40                 # ~8 weeks
KO_ATR_CONTRACTION_PCT = 30.0           # ATR must contract >30%
KO_VOL_SURGE_MULT = 1.5                 # breakout vol > 1.5x 20d avg
KO_RETEST_WINDOW_DAYS = 5               # days to wait for retest
KO_RETEST_TOLERANCE_PCT = 0.3           # how close = "retested" (%)

# -- Setup C: Higher-Low Continuation (M2) ----------------------------------
KO_SWING_BARS = 5                       # N-bar swing point detection
KO_HL_LOOKBACK_DAYS = 60                # window for higher-low search

# -- Structural stop (M2) ---------------------------------------------------
KO_ATR_PERIOD = 14
KO_STOP_ATR_BUFFER = 0.5                # stop = swing low - 0.5 * ATR(14)

# -- R:R minimum (M3) -------------------------------------------------------
KO_MIN_RR_RATIO = 3.0

# -- KO certificate simulation (M4, M5) -------------------------------------
KO_BARRIER_MULT = 2.0                   # barrier >= 2x stop distance
KO_BARRIER_TARGET = 2.5                 # target barrier = 2.5x stop dist
KO_LEVERAGE_MIN = 5.0
KO_LEVERAGE_MAX = 10.0
KO_RATIO = 100                          # 1 cert = 1/100 of index
KO_FINANCING_RATE_ANNUAL = 0.04         # 4% annualized
KO_EMITTER_SPREAD_PCT = 0.003           # 0.3% round-trip
KO_COMMISSION_EUR = 10.0                # fixed commission per side

# -- Position sizing (M6, M7) -----------------------------------------------
KO_RISK_PER_TRADE_PCT = 1.0             # 1% of risk capital per trade
KO_MAX_POSITIONS = 5                    # max concurrent positions
KO_MAX_TOTAL_RISK_PCT = 3.0             # max total portfolio risk

# -- Hold horizon / time stop (M8) ------------------------------------------
KO_MAX_HOLD_DAYS = 30                   # close if no new high in 30 days

# -- Staged exits (M9) ------------------------------------------------------
KO_EXIT_TRANCHE_1_R = 1.5               # 1/3 at +1.5R
KO_EXIT_TRANCHE_2_R = 3.0               # 1/3 at +3.0R
KO_TRAILING_ATR_MULT = 2.0              # 1/3 trailing at 2x ATR

# -- Frequency cap (M11) ----------------------------------------------------
KO_MAX_TRADES_PER_MONTH = 4

# -- Quarterly regime check (M12) -------------------------------------------
KO_ADX_PERIOD = 14
KO_ADX_THRESHOLD = 20.0                 # weekly ADX must be > 20
KO_REGIME_CHECK_WEEKS = 13              # check every quarter

# -- Backtest defaults -------------------------------------------------------
KO_INITIAL_CAPITAL = 20000.0
KO_DATA_START = "2005-01-01"
