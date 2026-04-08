"""
Leveraged & Inverse ETFs – Mechanics, Risks, and Compounding
=============================================================

Leveraged and inverse ETFs are designed to deliver multiples (+2x, +3x)
or inverses (-1x, -2x, -3x) of the DAILY return of a benchmark index.

═══════════════════════════════════════════════════════════════════════
HOW THEY WORK
═══════════════════════════════════════════════════════════════════════

Leveraged ETFs use financial derivatives (swaps, futures, options) and
sometimes borrowing to amplify daily returns.

Example: 2x Leveraged S&P 500 ETF (SSO)
    If S&P 500 returns +1% today → SSO targets +2%
    If S&P 500 returns -1% today → SSO targets -2%

Example: -1x Inverse S&P 500 ETF (SH)
    If S&P 500 returns +1% today → SH targets -1%
    If S&P 500 returns -1% today → SH targets +1%

Implementation:
    • Total return swaps with counterparties (banks)
    • Futures contracts (equity index, commodity, VIX)
    • Options strategies
    • The fund must rebalance DAILY to maintain target leverage
    • This daily reset is the source of compounding effects

═══════════════════════════════════════════════════════════════════════
THE COMPOUNDING EFFECT (VOLATILITY DECAY)
═══════════════════════════════════════════════════════════════════════

Over periods longer than one day, leveraged/inverse ETFs can diverge
significantly from the expected multiple of the benchmark's cumulative
return. This is a mathematical certainty, not a flaw.

NUMERICAL EXAMPLE (2x Leveraged):

    Day 1: Index goes from 100 to 110 (+10%)
           2x ETF: +20% → goes from $100 to $120

    Day 2: Index goes from 110 to 100 (-9.09%)
           2x ETF: -18.18% → goes from $120 to $98.18

    Result: Index is flat (100 → 100), but 2x ETF is DOWN $1.82 (-1.82%)

    This "volatility decay" or "beta slippage" worsens with:
    • Higher volatility
    • Longer holding periods
    • Higher leverage multiples

    In a TRENDING market (consistent direction), compounding can HELP:
    If the index rises 1% per day for 5 days:
    Index cumulative: +5.10%
    2x ETF cumulative: > +10.20% (compounding helps)

Mathematical Framework:
    For a 2x leveraged ETF, the n-day return is:
    R_leveraged = ∏(1 + 2 × r_i) - 1  (where r_i is daily index return)

    This is NOT equal to: 2 × [∏(1 + r_i) - 1]  (2× cumulative return)

    The difference is path-dependent and driven by the sequence of returns.

    Approximate decay: For leverage L, daily variance σ², over T days:
    Expected excess return ≈ L × R_index - (L² - L) × σ² × T / 2

═══════════════════════════════════════════════════════════════════════
MAJOR LEVERAGED & INVERSE ETFs
═══════════════════════════════════════════════════════════════════════

Equity – Leveraged:
    ProShares:
    • SSO   – 2x S&P 500 Daily
    • QLD   – 2x Nasdaq-100 Daily
    • UWM   – 2x Russell 2000 Daily
    Direxion:
    • SPXL  – 3x S&P 500 Daily
    • TQQQ  – 3x Nasdaq-100 Daily (one of the most traded ETFs)
    • TNA   – 3x Small Cap Bull Daily
    • SOXL  – 3x Semiconductor Bull Daily
    • FNGU  – 3x FANG+ Bull Daily
    • LABU  – 3x Biotech Bull Daily

Equity – Inverse:
    ProShares:
    • SH    – -1x S&P 500 Daily
    • PSQ   – -1x Nasdaq-100 Daily
    • RWM   – -1x Russell 2000 Daily
    • SDS   – -2x S&P 500 Daily
    • QID   – -2x Nasdaq-100 Daily
    Direxion:
    • SPXS  – -3x S&P 500 Daily
    • SQQQ  – -3x Nasdaq-100 Daily
    • TZA   – -3x Small Cap Bear Daily
    • SOXS  – -3x Semiconductor Bear Daily
    • FNGD  – -3x FANG+ Bear Daily
    • LABD  – -3x Biotech Bear Daily

Sector Leveraged/Inverse:
    • TECL/TECS – 3x/-3x Technology
    • FAS/FAZ   – 3x/-3x Financial
    • NUGT/DUST – 2x/-2x Gold Miners
    • ERX/ERY   – 2x/-2x Energy
    • CURE      – 3x Healthcare

Fixed Income:
    • TBT   – -2x 20+ Year Treasury (bet on rising rates)
    • TMF   – 3x 20+ Year Treasury (bet on falling rates)
    • TBF   – -1x 20+ Year Treasury
    • TMV   – -3x 20+ Year Treasury

Commodity:
    • UCO / SCO  – 2x / -2x Crude Oil
    • BOIL / KOLD – 2x / -2x Natural Gas
    • AGQ / ZSL   – 2x / -2x Silver
    • UGL / GLL   – 2x / -2x Gold

Volatility:
    • UVXY  – 1.5x Short-Term VIX Futures (ProShares)
    • SVXY  – -0.5x Short-Term VIX Futures (betting on volatility decline)
    • UVIX  – 2x Short-Term VIX Futures (Volatility Shares)
    • SVIX  – -1x Short-Term VIX Futures

    VIX products are among the most complex and dangerous leveraged ETPs:
    • VIX futures are almost always in contango → persistent roll cost
    • Long VIX products bleed value over time (UVXY has declined >99.99%
      since inception on a split-adjusted basis)
    • Short VIX strategies can experience catastrophic losses
      (XIV was terminated in Feb 2018 "Volmageddon" event, losing ~96%
      in a single day when VIX spiked)

═══════════════════════════════════════════════════════════════════════
RISKS & REGULATORY CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════

Key Risks:
    1. Compounding / Volatility Decay – Returns diverge from expected
       multiple over periods > 1 day
    2. Amplified Losses – 3x leverage can cause 60%+ single-day losses
    3. Margin / Liquidity Risk – During extreme moves, underlying
       derivatives can become illiquid
    4. Counterparty Risk – Swap agreements with banks
    5. Rebalancing Risk – End-of-day rebalancing can amplify volatility
       ("rebalance effect" creates predictable demand at market close)
    6. Termination Risk – Issuers can terminate products (XIV, TVIX)

Regulatory Stance:
    • FINRA has issued investor alerts about leveraged/inverse ETFs
    • Some brokers require enhanced suitability/options approval
    • SEC proposed rule changes for derivatives-based funds
    • Europe: UCITS cannot offer 3x leverage; limited to 2x
    • Some jurisdictions restrict retail access to leveraged products
    • Complex product governance under MiFID II in Europe

Who Uses Them:
    • Day traders and short-term tactical traders
    • Hedging short-term portfolio risk
    • Market makers and proprietary trading firms
    • NOT recommended for buy-and-hold investors
    • Institutional hedging (for short periods)

═══════════════════════════════════════════════════════════════════════
EXCHANGE-TRADED NOTES (ETNs) – DETAILED
═══════════════════════════════════════════════════════════════════════

ETNs are senior unsecured debt obligations of the issuing bank that
promise to pay the return of a reference index minus fees.

Key Characteristics:
    • NOT funds – do not hold any assets
    • Issuer credit risk (most critical risk)
    • No tracking error (return is contractual, not based on holdings)
    • Tax efficiency: may qualify for long-term capital gains treatment
      even for futures/commodity underlyings
    • Issuer can accelerate (call) the ETN at any time
    • Can trade at premium/discount to indicative value
    • APs can create/redeem with issuer (similar to ETF mechanism)

Notable ETN Issuers:
    • Barclays (iPath)
    • JPMorgan (Elements)
    • Credit Suisse (X-Links) – Many terminated after CS acquisition
    • UBS (E-TRACS)
    • Citigroup (C-Tracks)

Famous ETN Failures:
    • Lehman Brothers ETNs – Went to zero when Lehman filed bankruptcy (2008)
    • Credit Suisse VelocityShares XIV – Terminated after "Volmageddon" (2018)
    • Multiple ETNs suspended/terminated by CS during 2020 volatility

ETN vs. ETF Comparison:
    Feature              ETN                    ETF
    ────────────────     ──────────────────     ──────────────────
    Structure            Debt obligation        Fund (holds assets)
    Credit risk          Yes (issuer default)   No (segregated assets)
    Tracking error       None (contractual)     Yes (can deviate from index)
    Tax efficiency       Potentially better     Very good (in-kind)
    Counterparty risk    High (unsecured debt)  Low
    Maturity             Yes (typically 20-30y)  No (perpetual)
    Transparency         No holdings to disclose Daily holdings
    Regulatory           Securities Act          '40 Act / CFTC
"""
