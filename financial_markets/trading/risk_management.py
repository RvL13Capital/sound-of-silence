"""
Risk Management & Portfolio Analytics
======================================

Risk management is the identification, measurement, monitoring, and
control of potential losses across all dimensions of a trading or
investment operation.

TYPES OF RISK
─────────────
• Market risk – Adverse price movements in equities, rates, FX,
  commodities, or volatility.
• Credit risk – Counterparty fails to meet obligations.
• Liquidity risk – Cannot exit a position at a reasonable price.
• Operational risk – Systems failures, human error, fraud.
• Model risk – Models produce incorrect outputs due to bad
  assumptions, implementation errors, or regime changes.
• Systemic risk – Cascading failures across the financial system.
• Concentration risk – Excessive exposure to a single name, sector,
  factor, or geography.
• Regulatory / legal risk – Changes in law, enforcement actions.

VALUE AT RISK (VaR)
───────────────────
VaR answers: "What is the maximum expected loss over a given horizon
at a specified confidence level?"

Example: 1-day 95% VaR of EUR 100k means there is a 5% chance of
losing more than EUR 100k in a single day.

Methods:

    Historical Simulation:
    • Use actual historical returns (e.g., last 500 days).
    • Sort returns, pick the Nth percentile.
    • Pros: no distributional assumption, captures fat tails.
    • Cons: limited by historical sample, slow to react to regime
      changes, assumes the future resembles the past.

    Variance-Covariance (Parametric):
    • Assume returns are normally distributed.
    • VaR = μ − z × σ × √t (where z = 1.645 for 95%, 2.326 for 99%).
    • Pros: fast, analytical, easy to decompose.
    • Cons: normality assumption is wrong (fat tails), underestimates
      tail risk.  Delta-normal VaR for derivatives further compounds
      the problem.

    Monte Carlo Simulation:
    • Simulate thousands of random return paths from a fitted model.
    • Compute portfolio value under each path; derive loss distribution.
    • Pros: flexible, handles non-linear instruments, allows complex
      correlation structures.
    • Cons: computationally expensive, dependent on model assumptions.

Conditional VaR (CVaR / Expected Shortfall):
    • Average loss in the worst X% of cases (beyond the VaR threshold).
    • Better captures tail risk than VaR.
    • Basel III / FRTB requires Expected Shortfall (97.5%, 10-day)
      instead of VaR for market risk capital.

VaR Limitations:
    • VaR says nothing about the magnitude of losses beyond the
      threshold ("it could be EUR 100k or EUR 1B — VaR doesn't tell").
    • Not sub-additive: portfolio VaR can exceed sum of component VaRs.
    • CVaR fixes sub-additivity but shares other limitations.

Backtesting VaR:
    • Kupiec test (proportion of failures): did VaR breaches occur at
      the expected frequency?
    • Christoffersen test: are breaches independent (no clustering)?
    • Traffic-light approach (Basel): green/yellow/red zones based on
      breach count.

POSITION SIZING
───────────────
Fixed Fractional:
    • Risk a fixed percentage of equity per trade (e.g., 1%).
    • Position size = (Equity × Risk%) / (Entry − Stop).
    • Self-correcting: sizes shrink after losses, grow after gains.

Kelly Criterion:
    • f* = (bp − q) / b, where b = win/loss ratio, p = win
      probability, q = 1 − p.
    • Maximises long-run geometric growth rate of capital.
    • In practice, full Kelly is too aggressive; use fractional Kelly
      (½ Kelly or ¼ Kelly) to reduce variance and drawdown.
    • Assumes known probabilities and independent bets — rarely true
      in practice.

Volatility-Based Sizing:
    • Size inversely proportional to asset volatility.
    • Position size = Target Risk / (ATR × Multiplier) or
      = Target Vol / Asset Vol.
    • Equalises risk contribution across positions regardless of
      their individual volatility.

Risk Parity:
    • Allocate so that each asset contributes equally to total
      portfolio risk.
    • Requires a covariance matrix estimate.
    • Bridgewater's All-Weather popularised this concept.
    • Tends to overweight bonds and underweight equities relative
      to traditional 60/40.

PORTFOLIO RISK ANALYTICS
─────────────────────────
Portfolio Variance:
    σ²_p = Σ Σ w_i w_j σ_i σ_j ρ_ij
    Diversification reduces portfolio variance when correlations < 1.

Beta and Systematic Risk:
    β = Cov(R_asset, R_market) / Var(R_market).
    Measures sensitivity to the market factor.  β > 1 = amplifies
    market moves; β < 1 = dampens.

Tracking Error:
    Standard deviation of the difference between portfolio and
    benchmark returns.  TE = σ(R_p − R_b).

Risk-Adjusted Return Measures:
    • Sharpe Ratio = (R_p − R_f) / σ_p.  Risk-adjusted excess return.
    • Sortino Ratio = (R_p − R_f) / σ_downside.  Penalises only
      downside volatility.
    • Calmar Ratio = Annualised Return / Max Drawdown.
    • Information Ratio = (R_p − R_b) / TE.  Active return per unit
      of active risk.
    • Treynor Ratio = (R_p − R_f) / β.  Excess return per unit of
      systematic risk.

Maximum Drawdown:
    Largest peak-to-trough decline in portfolio value.
    MDD = (Trough − Peak) / Peak.
    Drawdown duration: time from peak to recovery to a new high.
    Institutional target: MDD < 20-25% for long-only equity.

STRESS TESTING & SCENARIO ANALYSIS
────────────────────────────────────

Historical Scenarios:
    Replay known crises through the portfolio:
    • 2000–2002 Dot-com crash
    • 2007–2009 Global Financial Crisis
    • 2010 Flash Crash (May 6)
    • 2011 Eurozone sovereign debt crisis
    • 2015 CNY devaluation / Aug flash crash
    • 2018 Feb Volmageddon + Q4 sell-off
    • 2020 COVID-19 crash (Feb–Mar)
    • 2022 Rate shock (growth/tech collapse)
    • 2024 Aug yen carry unwind
    • 2025 Apr Liberation Day tariffs

Hypothetical Scenarios:
    Construct "what if" shocks:
    • Interest rates +200 bps overnight.
    • EUR/USD ±10%.
    • Equity markets −30% in 5 days.
    • Oil ±50%.
    • Simultaneous moves (correlated stress).

Reverse Stress Testing:
    Start from the outcome (e.g., "portfolio loses 50%") and work
    backwards to identify which scenarios would produce that loss.
    Required by some regulators.

Regulatory Stress Tests:
    • CCAR / DFAST (US) – Fed stress tests for large banks.
    • EBA Stress Test (EU) – European Banking Authority.
    • Bank of England Stress Test.
    • Insurance stress tests (Solvency II SCR).

HEDGING STRATEGIES
──────────────────
Delta Hedging:
    Offset directional risk using futures, options, or correlated
    instruments.  Continuously adjust as delta changes (dynamic
    hedging).

Cross-Hedging:
    Hedge with a correlated but different instrument when a direct
    hedge isn't available (e.g., hedge a MDAX portfolio with DAX
    futures).  Basis risk exists.

Tail Risk Hedging:
    • Buy deep OTM put options on the index.
    • VIX call options (protect against volatility spikes).
    • Tail-risk funds: dedicated strategies (Universa, Cambria TAIL).
    • Cost: ongoing premium bleed (1-3% annually in normal markets).

Currency Hedging:
    • FX forwards to offset foreign-currency exposure.
    • Important for international small-cap strategies where FX moves
      can dominate stock returns.

Interest Rate Hedging:
    • Interest rate swaps, futures, swaptions.
    • Duration hedging for bond portfolios.
    • Relevant for fixed-income strategies and balance-sheet risk.

DRAWDOWN MANAGEMENT
───────────────────
Stop-Loss Strategies:
    • Fixed stop: exit at −X% from entry.
    • Trailing stop: exit at −X% from highest point since entry.
    • Volatility-adjusted: stop at N × ATR below entry or high.
    • Time stop: exit if position hasn't moved in N days.

Dynamic Position Reduction:
    • Reduce gross exposure when portfolio drawdown exceeds a
      threshold (e.g., cut to 50% exposure if DD > 10%).
    • Regime filter: pause new entries when the market trend turns
      bearish (index below long-term MA).

Circuit Breakers:
    • Portfolio level: stop all new trading if 60-day DD > 15%.
    • Strategy level: if a specific strategy underperforms by 2σ,
      pause and review.
    • Exchange level: LULD (Limit Up/Limit Down) halts on individual
      stocks; market-wide circuit breakers at 7/13/20%.

COUNTERPARTY AND CREDIT RISK
──────────────────────────────
• Counterparty credit exposure: mark-to-market value of outstanding
  derivative positions.
• Credit Value Adjustment (CVA): price of counterparty default risk
  embedded in derivative valuations.
• Netting agreements (ISDA Master Agreement): offset positive and
  negative exposures with the same counterparty.
• Collateral management: daily margin calls, eligible collateral,
  haircuts.
• Central clearing (CCP): eliminates bilateral counterparty risk
  for cleared derivatives but concentrates risk at the CCP.

LIQUIDITY RISK
──────────────
• Funding liquidity: ability to meet cash obligations.
• Market liquidity: ability to trade without significant price impact.
• Bid-ask spread as a real-time liquidity measure.
• Liquidity-adjusted VaR: extends VaR to account for the time
  needed to liquidate positions.
• Redemption risk: investors withdrawing capital during stress
  (hedge fund gates, mutual fund outflows).

OPERATIONAL RISK
────────────────
Historical incidents:
    • Barings Bank (1995): Nick Leeson, rogue trading, £827M loss.
    • Société Générale (2008): Jérôme Kerviel, EUR 4.9B loss.
    • Knight Capital (2012): algorithm malfunction, $440M loss in
      45 minutes.
    • JPMorgan "London Whale" (2012): CDS trading, $6.2B loss.
    • Archegos Capital (2021): TRS concentration, $10B+ losses across
      prime brokers.

Controls:
    • Segregation of duties (front/middle/back office).
    • Real-time position monitoring and limit enforcement.
    • Model validation and independent review.
    • Disaster recovery and business continuity planning.
    • Cybersecurity (a growing operational risk vector).

REGULATORY RISK FRAMEWORKS
───────────────────────────
Basel III / IV:
    • Minimum capital requirements (CET1, Tier 1, Total Capital).
    • Capital buffers (conservation, countercyclical, G-SIB surcharge).
    • Leverage ratio (minimum 3%).
    • Liquidity ratios (LCR, NSFR).

FRTB (Fundamental Review of the Trading Book):
    • Replaces VaR with Expected Shortfall (97.5%, 10-day).
    • Standardised Approach (SA) and Internal Models Approach (IMA).
    • Stricter boundary between trading book and banking book.
    • Non-modellable risk factors (NMRF) add capital charges.

Margin Requirements:
    • Initial margin for cleared derivatives (SPAN, PRISMA models).
    • Variation margin (daily mark-to-market).
    • Uncleared margin rules (UMR): bilateral initial margin for
      non-cleared OTC derivatives (phase 6 complete as of Sept 2022).
"""
