"""
Derivatives Markets
===================

Derivatives are financial contracts whose value is derived from the
performance of an underlying asset, index, rate, or event. They serve
two primary purposes: hedging (risk management) and speculation.

MARKET SIZE (approximate)
─────────────────────────
• Global OTC derivatives notional outstanding: ~$600+ trillion
• Global exchange-traded derivatives volume: ~$80+ billion contracts/year
• Interest rate derivatives dominate OTC (~80% of notional)

═══════════════════════════════════════════════════════════════════════
FUTURES
═══════════════════════════════════════════════════════════════════════

A futures contract is a standardized agreement to buy or sell an asset
at a predetermined price on a specific future date. Futures are
exchange-traded, centrally cleared, and marked to market daily.

Key Characteristics:
    • Standardized contracts (size, expiration, tick size)
    • Traded on regulated exchanges
    • Central counterparty clearing (CCP) eliminates counterparty risk
    • Daily mark-to-market with margin requirements
    • Physical delivery or cash settlement at expiration
    • Highly leveraged (initial margin typically 3–12% of notional)

Margin System:
    • Initial margin – Deposit required to open a position
    • Maintenance margin – Minimum equity to keep position open
    • Variation margin – Daily settlement of gains/losses
    • Margin call – Requirement to deposit additional funds if equity
      falls below maintenance level

Major Futures Categories:

    Equity Index Futures:
        • E-mini S&P 500 (ES) – Most traded equity futures globally
        • Micro E-mini S&P 500 (MES) – 1/10th of E-mini
        • E-mini Nasdaq-100 (NQ)
        • E-mini Dow (YM)
        • E-mini Russell 2000 (RTY)
        • Euro Stoxx 50 futures (FESX)
        • FTSE 100 futures
        • Nikkei 225 futures
        • DAX futures (FDAX)
        • Hang Seng futures

    Interest Rate Futures:
        • Treasury Bond futures (ZB) – 30-year
        • 10-Year Treasury Note (ZN) – Most liquid bond future
        • 5-Year Treasury Note (ZF)
        • 2-Year Treasury Note (ZT)
        • Ultra Treasury Bond (UB)
        • Eurodollar futures (expired, replaced by SOFR futures)
        • SOFR futures (SR3, SR1) – Key benchmark rate futures
        • Fed Funds futures (ZQ) – Used to gauge rate expectations
        • Euro-Bund futures (FGBL) – German 10-year
        • Euro-Bobl (FGBM), Euro-Schatz (FGBS)
        • Gilt futures – UK government bonds

    Commodity Futures:
        Energy:
            • Crude Oil – WTI (CL), Brent (BZ/ICE)
            • Natural Gas (NG)
            • RBOB Gasoline (RB)
            • Heating Oil (HO)
        Metals:
            • Gold (GC) – COMEX
            • Silver (SI) – COMEX
            • Copper (HG) – COMEX
            • Platinum (PL), Palladium (PA)
            • Iron Ore – SGX, DCE
            • LME metals: Aluminum, Copper, Zinc, Nickel, Lead, Tin
        Agriculture:
            • Corn (ZC), Soybeans (ZS), Wheat (ZW) – CBOT
            • Live Cattle (LE), Lean Hogs (HE) – CME
            • Coffee (KC), Cocoa (CC), Sugar (SB), Cotton (CT) – ICE
            • Palm Oil – Bursa Malaysia

    Currency Futures:
        • EUR/USD (6E), JPY (6J), GBP (6B), CHF (6S), AUD (6A), CAD (6C)
        • Traded on CME (Chicago Mercantile Exchange)
        • Smaller than OTC FX market but significant for retail/fund use

    Volatility Futures:
        • VIX futures (VX) – Based on CBOE Volatility Index
        • VIX measures 30-day expected volatility of S&P 500 options
        • Typically in contango (futures > spot), creating roll cost

    Cryptocurrency Futures:
        • Bitcoin futures (BTC) – CME
        • Micro Bitcoin (MBT) – CME
        • Ether futures (ETH) – CME

Futures Pricing:
    Cost of carry model:
    F = S × e^((r - y) × t)

    Where:
        F = futures price
        S = spot price
        r = risk-free rate
        y = convenience yield or dividend yield
        t = time to expiration

    • Contango: F > S (normal for most financial futures)
    • Backwardation: F < S (common in commodity markets with supply constraints)

    Basis = Spot price – Futures price
    Basis risk = Risk that basis changes unexpectedly

Rolling Futures:
    Futures contracts expire. Maintaining a continuous position requires
    "rolling" – closing the expiring contract and opening the next one.
    Roll yield can be positive (backwardation) or negative (contango).

Major Futures Exchanges:
    • CME Group (CME, CBOT, NYMEX, COMEX) – Largest derivatives exchange
    • Intercontinental Exchange (ICE) – Energy, agriculture, financial
    • Eurex – European financial derivatives
    • London Metal Exchange (LME) – Base metals
    • Shanghai Futures Exchange (SHFE)
    • Dalian Commodity Exchange (DCE)
    • Zhengzhou Commodity Exchange (ZCE)
    • Multi Commodity Exchange of India (MCX)
    • Japan Exchange Group (JPX) – Osaka Exchange
    • Hong Kong Exchanges (HKEX)
    • Singapore Exchange (SGX)
    • B3 (Brazil)
    • Korea Exchange (KRX)

═══════════════════════════════════════════════════════════════════════
OPTIONS
═══════════════════════════════════════════════════════════════════════

An option gives the holder the right, but not the obligation, to buy
(call) or sell (put) an underlying asset at a specific price (strike)
on or before a specific date (expiration).

Option Types:
    • Call option – Right to buy the underlying
    • Put option  – Right to sell the underlying
    • American – Can be exercised any time before expiration
    • European – Can only be exercised at expiration
    • Bermudan – Can be exercised on specific dates before expiration

Key Terms:
    • Premium – Price paid for the option
    • Strike price – Price at which the underlying can be bought/sold
    • Expiration date – Date the option expires
    • Intrinsic value – max(0, S-K) for calls, max(0, K-S) for puts
    • Time value (extrinsic) – Premium - intrinsic value
    • Moneyness:
      - In-the-money (ITM): Intrinsic value > 0
      - At-the-money (ATM): Strike ≈ underlying price
      - Out-of-the-money (OTM): Intrinsic value = 0

The Greeks (Option Sensitivities):
    • Delta (Δ) – Rate of change of option price per $1 change in underlying
      Calls: 0 to +1; Puts: -1 to 0; ATM ≈ ±0.50
    • Gamma (Γ) – Rate of change of delta per $1 change in underlying
      Highest for ATM options near expiration
    • Theta (Θ) – Time decay; rate of premium erosion per day
      Negative for long options; accelerates near expiration
    • Vega (ν) – Sensitivity to 1% change in implied volatility
      Highest for ATM options with more time to expiration
    • Rho (ρ) – Sensitivity to 1% change in interest rates
      Generally small effect; more significant for long-dated options
    • Vanna – Sensitivity of delta to volatility (cross-Greek: dΔ/dσ)
    • Volga/Vomma – Sensitivity of vega to volatility (d²Price/dσ²)
    • Charm – Decay of delta over time (dΔ/dt)

Option Pricing Models:
    Black-Scholes-Merton (1973):
        Assumptions: European options, lognormal returns, constant
        volatility, no dividends (extended versions handle dividends),
        no transaction costs, continuous trading.

        C = S·N(d1) - K·e^(-rT)·N(d2)
        P = K·e^(-rT)·N(-d2) - S·N(-d1)

        Where:
        d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
        d2 = d1 - σ√T

    Binomial Tree Model (Cox-Ross-Rubinstein):
        Discrete-time model, can handle American options, dividends,
        and varying volatility. Builds a tree of possible price paths.

    Monte Carlo Simulation:
        Simulates many random price paths to estimate option value.
        Useful for complex / path-dependent options.

    Implied Volatility:
        The volatility implied by the market price of an option
        (reverse-engineer BSM). Not directly observable.

    Volatility Smile / Skew:
        • Implied volatility varies by strike price (not constant as BSM assumes)
        • Equity options: "skew" – OTM puts have higher IV than OTM calls
          (demand for downside protection / crash risk premium)
        • FX options: "smile" – Both wings have higher IV
        • Volatility surface: IV plotted across strikes and expirations

Common Option Strategies:
    Directional:
        • Long Call – Bullish, limited risk
        • Long Put – Bearish, limited risk
        • Covered Call – Own stock + sell call (income generation)
        • Protective Put – Own stock + buy put (downside insurance)
        • Married Put – Buy stock + buy put simultaneously
        • Collar – Own stock + buy put + sell call (bounded risk/reward)

    Spreads:
        • Bull Call Spread – Buy lower call + sell higher call
        • Bear Put Spread – Buy higher put + sell lower put
        • Bull Put Spread (credit) – Sell higher put + buy lower put
        • Bear Call Spread (credit) – Sell lower call + buy higher call
        • Calendar Spread – Same strike, different expirations
        • Diagonal Spread – Different strikes and expirations

    Volatility:
        • Long Straddle – Buy call + put at same strike (bet on big move)
        • Long Strangle – Buy OTM call + OTM put (cheaper than straddle)
        • Short Straddle – Sell call + put (bet on low volatility)
        • Iron Condor – Sell strangle + buy further OTM protection
        • Iron Butterfly – Sell straddle + buy strangle protection
        • Ratio spread – Unequal number of long vs short options

    Multi-Leg:
        • Butterfly Spread – 3 strikes (buy-sell-sell-buy pattern)
        • Condor – 4 strikes (similar to butterfly, wider body)
        • Box Spread – Bull call spread + bear put spread (synthetic loan)
        • Jade Lizard – Short put + short call spread (no upside risk)
        • Broken Wing Butterfly – Asymmetric butterfly

Exchange-Traded Options Venues:
    • CBOE (Chicago Board Options Exchange) – Largest US options exchange
    • NYSE Arca Options, NYSE American Options
    • Nasdaq Options Market (NOM), Nasdaq PHLX, Nasdaq ISE, Nasdaq BX, Nasdaq GEMX, Nasdaq MRX
    • MIAX, MIAX Pearl, MIAX Emerald
    • BOX Exchange
    • MEMX Options
    • Eurex (European options)
    • Euronext options markets
    • JSE (Johannesburg)

    US options market has 16+ competing exchanges for equity options.

Options on Futures:
    Options where the underlying is a futures contract.
    Upon exercise, the holder receives a futures position.
    Common for commodities, interest rates, and indices.

LEAPS (Long-Term Equity Anticipation Securities):
    Options with expirations > 1 year (up to ~3 years).
    Available on major stocks and some ETFs.

Weekly Options (Weeklys):
    Options expiring every week (not just monthly).
    Popular for short-term trading and event hedging.

0DTE (Zero Days to Expiration) Options:
    Options traded on their expiration day. Explosive growth since 2022.
    Available daily for SPX, SPY, QQQ. High gamma, rapid time decay.

═══════════════════════════════════════════════════════════════════════
SWAPS (OTC Derivatives)
═══════════════════════════════════════════════════════════════════════

Swaps are OTC agreements to exchange cash flows based on different
financial variables. Since Dodd-Frank, many standardized swaps must
be cleared through CCPs and traded on Swap Execution Facilities (SEFs).

Interest Rate Swaps (IRS):
    Exchange fixed-rate payments for floating-rate payments.
    The most common derivative by notional outstanding.
    • Plain vanilla: Fixed vs. floating (e.g., 5% fixed vs. SOFR + spread)
    • Notional principal is not exchanged
    • Basis swap: Exchange two different floating rates
    • Overnight Index Swap (OIS): Fixed vs. overnight rate (SOFR OIS)
    • Amortizing swap: Notional decreases over time
    • Accreting swap: Notional increases over time
    • Swaption: Option to enter into a swap

Credit Default Swaps (CDS):
    Insurance-like contract on credit risk.
    • Protection buyer pays periodic premium (spread) to protection seller
    • If credit event occurs (default, restructuring), seller compensates buyer
    • Single-name CDS: On a specific issuer
    • CDS Index: On a basket of issuers
      - CDX (North America): CDX.NA.IG, CDX.NA.HY
      - iTraxx (Europe): iTraxx Europe, iTraxx Crossover
    • Played a central role in the 2008 financial crisis (AIG)

Total Return Swaps (TRS):
    One party pays total return of an asset (price change + income);
    the other pays a financing rate (e.g., SOFR + spread).
    Used for synthetic exposure without owning the asset.
    Common in hedge fund prime brokerage (e.g., Archegos Capital collapse).

Equity Swaps:
    Exchange returns of an equity (or basket/index) for a financing rate.
    Similar to TRS but specifically equity-referenced.

Currency Swaps (Cross-Currency Swaps):
    Exchange principal and interest in different currencies.
    Used by corporations and sovereigns for foreign-currency funding.

Commodity Swaps:
    Exchange fixed commodity price for floating market price.
    Used by producers (lock in revenue) and consumers (lock in costs).

Variance Swaps & Volatility Swaps:
    • Variance swap: Pays the difference between realized variance and
      a strike variance. Linear in variance.
    • Volatility swap: Pays the difference between realized volatility
      and a strike volatility. Linear in volatility.
    • Used for pure volatility trading without delta hedging.

═══════════════════════════════════════════════════════════════════════
EXOTIC & STRUCTURED DERIVATIVES
═══════════════════════════════════════════════════════════════════════

Exotic Options:
    • Barrier options: Activate (knock-in) or terminate (knock-out) when
      underlying hits a barrier price
    • Asian options: Payoff based on average price over a period
    • Lookback options: Payoff based on maximum or minimum price during life
    • Digital/Binary options: Fixed payout if condition is met
    • Quanto options: Payoff in a different currency than the underlying
    • Compound options: Options on options
    • Chooser options: Holder chooses call or put at a future date
    • Cliquet/Ratchet options: Series of forward-start options
    • Rainbow options: Based on multiple underlyings (best-of, worst-of)

Structured Products:
    Pre-packaged combinations of derivatives and fixed-income instruments:
    • Autocallable notes – Called early if underlying above barrier
    • Reverse convertibles – High coupon + risk of stock delivery
    • Capital-protected notes – Principal protection + upside participation
    • Range accrual notes – Coupon accrues only when condition is met
    • Snowball/Phoenix notes – Popular in Asian markets
    • Worst-of products – Payoff linked to worst-performing of basket

DERIVATIVES CLEARING
─────────────────────
Post-2008 reforms mandated central clearing for standardized OTC derivatives.

Major CCPs:
    • LCH (London Clearing House) – Largest IRS clearing
    • CME Clearing – Futures and OTC clearing
    • ICE Clear – CDS and other derivatives
    • Eurex Clearing – European derivatives
    • OCC (Options Clearing Corporation) – US equity options
    • JSCC (Japan Securities Clearing Corporation)

Default Waterfall:
    If a clearing member defaults, losses are absorbed in this order:
    1. Defaulter's initial margin
    2. Defaulter's default fund contribution
    3. CCP's own capital (skin-in-the-game)
    4. Non-defaulting members' default fund contributions
    5. CCP's additional resources / recovery mechanisms
"""
