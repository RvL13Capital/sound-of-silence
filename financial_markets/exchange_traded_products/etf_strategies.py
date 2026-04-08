"""
ETF Investment Strategies & Portfolio Construction
==================================================

═══════════════════════════════════════════════════════════════════════
CORE-SATELLITE APPROACH
═══════════════════════════════════════════════════════════════════════

The most common ETF portfolio construction methodology:

    Core (60-90% of portfolio):
    • Low-cost, broad market ETFs for bulk of allocation
    • Total market or large-cap index funds
    • Example: VTI (US) + VXUS (International) + BND (Bonds)

    Satellite (10-40% of portfolio):
    • Targeted ETFs for specific exposures, tilts, or alpha generation
    • Sector, thematic, factor, or alternative ETFs
    • More active management of satellite positions

═══════════════════════════════════════════════════════════════════════
FACTOR INVESTING (SMART BETA)
═══════════════════════════════════════════════════════════════════════

Academic research has identified persistent return premiums associated
with certain stock characteristics (factors).

Established Factors:
    Value:
    • Stocks with low prices relative to fundamentals outperform over time
    • Metrics: P/E, P/B, P/CF, EV/EBITDA
    • Fama-French value factor (HML – High Minus Low book-to-market)
    • ETFs: VLUE, VTV, IWD, RPV, SPYV

    Size (Small-Cap Premium):
    • Smaller companies tend to outperform larger ones over long periods
    • Fama-French size factor (SMB – Small Minus Big)
    • ETFs: IWM, VB, IJR, SCHA

    Momentum:
    • Stocks with recent strong performance continue to outperform
    • Jegadeesh & Titman (1993)
    • ETFs: MTUM, PDP, DWAS

    Quality:
    • Companies with high profitability, stable earnings, low leverage
    • Metrics: ROE, earnings stability, debt/equity
    • ETFs: QUAL, SPHQ, JQUA, DGRW

    Low Volatility / Minimum Variance:
    • Low-volatility stocks deliver higher risk-adjusted returns
    • "Low volatility anomaly" – contradicts CAPM
    • ETFs: USMV, SPLV, LGLV

    Yield / Income:
    • Stocks with high and growing dividends
    • Related to value factor but distinct
    • ETFs: VYM, SCHD, HDV, DVY, NOBL

Multi-Factor Approaches:
    • Combine factors for diversification of factor risk
    • Integrated: Score stocks on multiple factors simultaneously
    • Sleeve: Allocate separately to single-factor ETFs
    • Sequential: Apply factors as screens in sequence
    • ETFs: GSLC, LRGF, QUS, DEUS, PIE

Factor Cyclicality:
    Factors go through multi-year cycles of outperformance/underperformance:
    • Value vs. Growth cycle is the most watched (growth dominated 2010-2020;
      value outperformed in 2022)
    • Momentum can reverse sharply ("momentum crash")
    • Low volatility underperforms in strong bull markets
    • Factor timing is extremely difficult

═══════════════════════════════════════════════════════════════════════
ASSET ALLOCATION MODELS
═══════════════════════════════════════════════════════════════════════

Classic Models (all implementable with ETFs):

    60/40 Portfolio:
    • 60% equities (VTI or SPY) + 40% bonds (AGG or BND)
    • Historical benchmark for balanced allocation
    • Challenged in 2022 when stocks and bonds fell simultaneously

    Three-Fund Portfolio (Bogleheads):
    • US Total Stock Market (VTI)
    • International Total Stock Market (VXUS)
    • Total Bond Market (BND)

    All-Weather / Risk Parity (Ray Dalio inspired):
    • 30% Stocks (VTI)
    • 40% Long-Term Bonds (TLT)
    • 15% Intermediate Bonds (IEI)
    • 7.5% Gold (GLD)
    • 7.5% Commodities (DBC)
    • Risk parity: equalize risk contribution across asset classes

    Permanent Portfolio (Harry Browne):
    • 25% Stocks, 25% Long-Term Bonds, 25% Gold, 25% Cash

    Endowment Model (Yale/David Swensen):
    • Domestic equity, international equity, real estate, TIPS,
      alternatives (PE, hedge funds – approximated with liquid alts)

    Target-Date / Glide Path:
    • Gradually shift from equities to bonds as retirement approaches
    • ETF model portfolios offered by many providers
    • Automated through robo-advisors (Betterment, Wealthfront, Schwab)

═══════════════════════════════════════════════════════════════════════
TAX-LOSS HARVESTING WITH ETFs
═══════════════════════════════════════════════════════════════════════

Strategy: Sell losing positions to realize losses, then buy a similar
(but not "substantially identical") ETF to maintain market exposure.

    Example:
    • Sell VTI (Vanguard Total Stock Market) at a loss
    • Buy ITOT (iShares Core Total Stock Market) or SCHB (Schwab)
    • Same economic exposure, but realized tax loss offsets gains
    • Must avoid "wash sale" rule (30 days before/after)

    ETFs are ideal for this because:
    • Many similar but not identical ETFs exist for every asset class
    • High liquidity enables efficient switching
    • Low transaction costs
    • Automated by robo-advisors (Betterment, Wealthfront do this daily)

    Wash Sale Rule (IRS):
    • Cannot repurchase "substantially identical" security within 30 days
    • Applies to spouse's accounts and IRAs too
    • Switching between different index providers (Vanguard vs. iShares)
      is generally considered safe
    • ETF vs. mutual fund tracking same index: ambiguous/risky

═══════════════════════════════════════════════════════════════════════
SECTOR ROTATION
═══════════════════════════════════════════════════════════════════════

Using sector ETFs to overweight/underweight sectors based on the
business cycle, momentum, or fundamental analysis.

Business Cycle Framework:
    Early Recovery:  Financials, Consumer Discretionary, Real Estate, Tech
    Mid Cycle:       Technology, Industrials, Materials
    Late Cycle:      Energy, Materials, Healthcare
    Recession:       Utilities, Consumer Staples, Healthcare

    Implementation: Overweight expected outperforming sectors using
    Select Sector SPDR ETFs (XLK, XLF, XLE, etc.) or Vanguard sector ETFs

═══════════════════════════════════════════════════════════════════════
ETF MODEL PORTFOLIOS & ROBO-ADVISORS
═══════════════════════════════════════════════════════════════════════

Robo-Advisors (automated ETF portfolio management):
    • Betterment – Broad market ETFs, tax-loss harvesting, goal-based
    • Wealthfront – Similar, plus direct indexing
    • Schwab Intelligent Portfolios – No advisory fee (monetizes cash)
    • Vanguard Digital Advisor – Low-cost, Vanguard ETFs
    • Fidelity Go – Fidelity Flex ETFs (zero expense ratio)
    • SoFi Automated Investing
    • M1 Finance – Customizable "Pies" (fractional ETF shares)

Model Portfolio Providers:
    • BlackRock (iShares model portfolios)
    • Vanguard Advisor model portfolios
    • WisdomTree model portfolios
    • State Street model portfolios
    • Distributed through financial advisors and platforms

Direct Indexing:
    Owning individual stocks to replicate an index (instead of an ETF).
    Benefits: Enhanced tax-loss harvesting, customization (ESG exclusions).
    Enabled by fractional shares and zero commissions.
    Competing with ETFs for tax-sensitive investors.
    Providers: Parametric (Morgan Stanley), Aperio (BlackRock), Vanguard
    Personalized Indexing, Fidelity Managed FidFolios.

═══════════════════════════════════════════════════════════════════════
INSTITUTIONAL ETF USAGE
═══════════════════════════════════════════════════════════════════════

How institutional investors use ETFs:

    Cash Equitization:
    • Park cash in broad market ETFs instead of holding uninvested cash
    • Maintain market exposure while waiting to deploy into individual positions

    Transition Management:
    • Use ETFs as temporary placeholders during portfolio transitions
    • Changing managers? Buy index ETF, sell gradually into new strategy

    Tactical Allocation:
    • Quickly adjust portfolio tilts using liquid sector/country ETFs
    • Faster and cheaper than trading individual securities

    Hedging:
    • Inverse ETFs for short-term portfolio hedging
    • Options on ETFs (SPY options are the most liquid in the world)

    Liquidity Sleeve:
    • Hold a portion in highly liquid ETFs for cash flow management
    • Bond ETFs provide daily liquidity for otherwise illiquid bond portfolios

    Securities Lending:
    • Lend ETF shares to short sellers and earn income
    • Heavily shorted ETFs command higher lending fees

    Fixed Income Portfolio Management:
    • Bond ETFs for quick exposure adjustments
    • Portfolio trading: trade baskets of bonds via ETF creation/redemption
"""
