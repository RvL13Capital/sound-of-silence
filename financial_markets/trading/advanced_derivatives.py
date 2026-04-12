"""
Advanced Derivatives Trading
=============================

Professional-level derivatives trading: deep Greeks analysis,
volatility trading, yield curve strategies, exotic instruments,
and cross-asset derivative structures.

OPTIONS GREEKS – DEEP DIVE
───────────────────────────

Delta (Δ):
    • Rate of change of option price per $1 move in the underlying.
    • Calls: 0 to +1.  Puts: −1 to 0.  ATM ≈ ±0.50.
    • Interpretation: approximate probability of finishing ITM
      (rough proxy, not exact).
    • Delta hedging: hold Δ × 100 shares of underlying per contract
      to create a delta-neutral position.  Must be continuously
      rebalanced as delta changes with price, time, and vol.

Gamma (Γ):
    • Rate of change of delta per $1 move in the underlying.
    • Always positive for long options (calls and puts).
    • Highest for ATM options near expiration.
    • Gamma risk: short-gamma positions (short options) face
      accelerating losses during large moves.  Long-gamma positions
      benefit from large moves.
    • Gamma scalping: delta-hedge a long-gamma position; profit from
      realised volatility exceeding implied volatility.

Theta (Θ):
    • Time decay: rate of premium erosion per day (all else equal).
    • Negative for long options; positive for short options.
    • Accelerates near expiration (non-linear decay curve).
    • "Theta is the rent you pay for gamma."

Vega (ν):
    • Sensitivity of option price to a 1-percentage-point change
      in implied volatility.
    • Highest for ATM, long-dated options.
    • Long vega: profit when IV rises.  Short vega: profit when
      IV falls.
    • Vega is the core exposure in volatility trading.

Rho (ρ):
    • Sensitivity to a 1-percentage-point change in the risk-free rate.
    • Generally small for short-dated options; significant for LEAPS
      and deep ITM options.
    • Calls have positive rho; puts have negative rho.

Higher-Order Greeks:
    Vanna:  ∂Δ/∂σ (or equivalently ∂ν/∂S).
            Measures how delta changes with volatility.
            Important for risk-reversal and skew trading.

    Volga (Vomma):  ∂²Price/∂σ² = ∂ν/∂σ.
            Sensitivity of vega to volatility.  Relevant for
            pricing far-OTM options and managing convexity in vol.

    Charm:  ∂Δ/∂t.  Delta decay — how delta changes over time
            even without price movement.  Critical for managing
            delta hedges near expiration.

    Color:  ∂Γ/∂t.  Rate of change of gamma over time.

    Speed:  ∂Γ/∂S.  Rate of change of gamma with price.
            Third-order: relevant for very large positions.

    Greeks Aggregation:
    Portfolio-level Greeks are the sum of individual position Greeks.
    A derivatives desk manages portfolio delta, gamma, vega, and
    theta as aggregated risk metrics, hedging where necessary.

VOLATILITY TRADING
──────────────────

Implied vs. Realised Volatility:
    • Implied volatility (IV): volatility priced into options by the
      market (forward-looking).
    • Realised (historical) volatility: actual observed volatility of
      the underlying over a past period.
    • Volatility Risk Premium (VRP): IV typically exceeds realised
      vol.  This premium compensates option sellers for bearing tail
      risk.  Harvesting the VRP is a core strategy for many funds.

Volatility Smile and Skew:
    • Black-Scholes assumes constant volatility; in reality, IV
      varies by strike and expiration.
    • Equity skew: OTM puts have higher IV than OTM calls (demand
      for downside protection, crash risk premium).
    • FX smile: both wings (OTM calls and puts) have elevated IV.
    • Commodity: term structure of vol varies with contango/backwdn.
    • Volatility surface: 3D plot of IV across strikes and expiries.

Variance Swaps:
    • Payoff = Notional × (Realised Variance − Strike Variance).
    • Linear in variance (not volatility).
    • Pure exposure to realised volatility with no path dependency.
    • Can be replicated by a continuum of options across all strikes.
    • Very popular with institutional vol traders.

Volatility Swaps:
    • Payoff = Notional × (Realised Vol − Strike Vol).
    • Linear in volatility.
    • Harder to hedge than variance swaps due to convexity adjustment.

VIX and VIX Derivatives:
    • VIX = 30-day implied volatility of S&P 500 options.
    • VIX futures: typically in contango (futures > spot VIX).
    • VIX options: options on VIX futures (not on spot VIX directly).
    • Long VIX products (UVXY, VXX) bleed value due to contango roll.
    • Short VIX strategies profit from roll yield but carry
      catastrophic tail risk (XIV / Volmageddon Feb 2018).

Dispersion Trading:
    • Trade the difference between index implied vol and the implied
      vol of individual constituents.
    • Sell index volatility (straddles), buy single-stock volatility.
    • Profits when realised correlation is lower than implied.
    • Correlation is typically overpriced in index options.

Straddles and Strangles as Volatility Plays:
    • Long straddle: buy ATM call + ATM put.  Profit from large move
      in either direction (long gamma, long vega).
    • Long strangle: buy OTM call + OTM put.  Cheaper but needs
      bigger move.
    • Short straddle/strangle: collect premium, profit from low
      realised vol.  Unlimited risk on the wings.

ADVANCED OPTIONS STRATEGIES
────────────────────────────

Vertical Spreads:
    • Bull call spread: buy lower call, sell higher call (debit).
    • Bear put spread: buy higher put, sell lower put (debit).
    • Credit spreads: sell the more expensive option, buy protection.
    • Risk/reward is defined and capped.

Iron Condors and Iron Butterflies:
    • Iron condor: sell OTM put + sell OTM call, buy further OTM
      protection on both sides.  Profits from low realised vol.
    • Iron butterfly: sell ATM straddle, buy OTM strangle protection.
      Tighter range, higher premium.

Calendar (Time) Spreads and Diagonals:
    • Calendar: same strike, different expirations.  Profits from
      time decay differential and vol term structure.
    • Diagonal: different strike AND different expiration.

Ratio Spreads and Backspreads:
    • Ratio spread: buy 1, sell 2 (or other ratio) at different
      strikes.  Creates uneven exposure.
    • Backspread: buy more options than you sell (long gamma, short
      theta).

Conversion and Reversal (Synthetic Positions):
    • Conversion: long stock + long put + short call (same strike) =
      risk-free position (or synthetic bond).
    • Reversal: short stock + short put + long call = opposite.
    • Used for arbitrage and financing.

Box Spread:
    • Bull call spread + bear put spread at same strikes = synthetic
      zero-coupon bond.  Used as lending/borrowing instrument.

DELTA HEDGING AND DYNAMIC REPLICATION
──────────────────────────────────────

Continuous vs. Discrete Hedging:
    BSM assumes continuous hedging (infinite rebalancing).  In
    practice, hedging is discrete (daily, hourly, or on threshold).
    Hedging frequency trades off: more frequent = lower hedge error
    but higher transaction costs.

Hedging P&L:
    For a delta-hedged long option position:
    P&L ≈ ½ Γ S² (σ²_realised − σ²_implied) × dt
    • If realised vol > implied vol: long gamma profits.
    • If realised vol < implied vol: long gamma loses.
    • This is the fundamental equation of volatility trading.

Pin Risk:
    Near expiration, ATM options have very high gamma.  Small price
    moves cause large delta swings, making hedging difficult.
    Particularly dangerous at option expiration for market makers.

YIELD CURVE STRATEGIES (RATES DERIVATIVES)
───────────────────────────────────────────

Interest Rate Swaps:
    • Plain vanilla: fixed vs. floating (e.g., 5% fixed vs. SOFR).
    • Basis swaps: two floating rates (e.g., 1-month vs. 3-month).
    • OIS (Overnight Index Swap): fixed vs. overnight rate.

Swap Curve Trading:
    • Flattener: short short-end, long long-end (profit if curve
      flattens).
    • Steepener: long short-end, short long-end.
    • Butterfly: trade the curvature (2s/5s/10s, 5s/10s/30s).
    • DV01 weighted to be duration-neutral.

Swaptions:
    • Options on interest rate swaps.
    • Payer swaption: right to enter a swap paying fixed (bearish
      rates / bullish yields).
    • Receiver swaption: right to enter a swap receiving fixed
      (bullish rates / bearish yields).
    • Volatility cube: IV across strike, expiry, and tenor.

Caps, Floors, and Collars:
    • Cap: series of caplets; each is a call on a reference rate.
    • Floor: series of floorlets; each is a put on a reference rate.
    • Collar: long cap + short floor (or vice versa).  Bounds rate
      exposure to a range.

CREDIT DERIVATIVES
──────────────────

Credit Default Swaps (CDS):
    • Protection buyer pays periodic premium (spread) to seller.
    • If credit event occurs, seller compensates for loss.
    • Single-name CDS: on one issuer.
    • CDS Index: CDX (N. America), iTraxx (Europe).
    • CDS curve trading: steepeners, flatteners on the term structure
      of credit spreads.
    • Basis trade: CDS spread vs. cash bond spread; exploit
      divergences.

Tranched Products:
    • Synthetic CDOs: reference portfolio of CDS, sliced into
      tranches (equity, mezzanine, senior).
    • Equity tranche: first loss, highest yield, most risk.
    • Super-senior: last loss, lowest yield, minimal risk in normal
      conditions (but concentrated tail risk).
    • Bespoke tranches: customised for specific investors.

EXOTIC DERIVATIVES
──────────────────

Barrier Options:
    • Knock-in: activated when underlying hits a barrier.
    • Knock-out: terminated when underlying hits a barrier.
    • Single barrier (up-and-in, up-and-out, down-and-in, down-and-out).
    • Double barrier: bounded by upper and lower barriers.
    • Cheaper than vanilla options; carry discontinuity risk at
      the barrier.

Asian Options:
    • Payoff based on the average price over a period.
    • Arithmetic average (most common, harder to price analytically).
    • Geometric average (closed-form solution exists).
    • Lower premium than vanilla (averaging reduces payoff volatility).
    • Common in commodity and FX markets.

Lookback Options:
    • Fixed-strike lookback: payoff = max(S_max − K, 0) for calls.
    • Floating-strike lookback: payoff based on max/min during life.
    • Very expensive; effectively eliminate timing risk.

Digital / Binary Options:
    • Fixed payout if condition is met at expiration.
    • Cash-or-nothing: pays fixed cash if ITM.
    • Asset-or-nothing: pays the asset value if ITM.
    • Discontinuous payoff creates hedging challenges (high gamma
      near the strike at expiry).

Quanto Options:
    • Payoff in a different currency than the underlying, at a
      fixed exchange rate.  Eliminates FX risk for the buyer.
    • Pricing requires correlation between underlying and FX rate.

Autocallable Notes:
    • Periodically observed (quarterly or semi-annually).
    • If underlying above autocall barrier, note is called early
      with a coupon.
    • If not called and underlying below barrier at maturity,
      investor takes equity-linked loss.
    • Very popular structured product in Europe and Asia.

Pricing Methods for Exotics:
    • Closed-form: available for some (barrier with log-normal, Asian
      geometric, European digitals).
    • Monte Carlo simulation: most flexible, handles path dependency.
    • Finite difference methods (PDE solving): efficient for 1-2
      factor models.
    • Binomial / trinomial trees: intuitive, handle American exercise.

MODEL RISK IN DERIVATIVES
──────────────────────────

Black-Scholes-Merton Limitations:
    • Assumes constant volatility (volatility smile contradicts this).
    • Assumes continuous hedging (impossible in practice).
    • Assumes log-normal returns (real returns have fat tails).
    • No jumps, no transaction costs, no market microstructure.

Local Volatility (Dupire 1994):
    Calibrate a deterministic volatility surface σ(S,t) that exactly
    reproduces all observed option prices.  Widely used for pricing
    exotics but produces unrealistic forward volatility dynamics.

Stochastic Volatility Models:
    • Heston (1993): volatility follows a mean-reverting
      square-root diffusion.  dv = κ(θ−v)dt + ξ√v dW.
      Semi-closed-form for European options.
    • SABR (Hagan et al. 2002): Stochastic Alpha Beta Rho.
      Standard for interest rate options and swaptions.
      Calibrates well to the smile.
    • Bergomi variance-curve models (for VIX and vol surface
      dynamics).

Jump-Diffusion Models:
    • Merton (1976): adds Poisson jumps to GBM.
    • Captures sudden large moves (earnings, events).
    • Produces more realistic short-dated smiles.

RISK MANAGEMENT FOR DERIVATIVES PORTFOLIOS
────────────────────────────────────────────

Greeks-Based Risk:
    Monitor and limit portfolio delta, gamma, vega, and theta.
    Set notional and Greek limits per trader, desk, and firm.

Scenario Analysis:
    Shock the underlying by ±X%, volatility by ±Y%, rates by ±Z bps.
    Compute portfolio P&L under each scenario (stress matrix).

CVA / DVA:
    Credit Value Adjustment: price of counterparty default risk.
    Debit Value Adjustment: benefit from own default risk.
    Post-2008, CVA desks became standard at major banks.

Margin Requirements:
    Initial margin (IM): covers potential future exposure.
    Variation margin (VM): daily mark-to-market settlement.
    Models: CME SPAN, Eurex PRISMA, OCC TIMS.
"""
