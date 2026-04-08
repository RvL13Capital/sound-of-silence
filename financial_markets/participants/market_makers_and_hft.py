"""
Market Makers, High-Frequency Trading, and Sell-Side Participants
=================================================================

═══════════════════════════════════════════════════════════════════════
MARKET MAKERS
═══════════════════════════════════════════════════════════════════════

Market makers provide liquidity by continuously quoting bid and ask
prices and standing ready to buy or sell. They profit from the
bid-ask spread and manage inventory risk.

Types of Market Makers:

    Designated Market Makers (DMMs):
    • Assigned to specific securities on an exchange
    • Obligations: Maintain fair and orderly markets, provide quotes
    • NYSE DMMs: Citadel Securities, GTS, Virtu Financial
    • Have informational advantages (see order flow)
    • Obligations include: minimum quote size, maximum spread width,
      participation in opening/closing auctions

    Registered / Competitive Market Makers:
    • Compete to provide liquidity alongside DMMs
    • Less stringent obligations but incentivized by exchange rebates

    OTC / Wholesale Market Makers:
    • Execute retail order flow off-exchange
    • Citadel Securities, Virtu Financial, Jane Street, UBS, G1X
    • Pay for order flow (PFOF) to retail brokers
    • Provide price improvement over NBBO
    • Handle ~40%+ of US retail equity order flow

    ETF Market Makers / Authorized Participants:
    • Create/redeem ETF shares to maintain price-NAV alignment
    • Major players: Jane Street, Flow Traders, Citadel, Virtu, Optiver,
      Susquehanna (SIG), Jump Trading
    • Provide tight bid-ask spreads for ETFs
    • Critical for less liquid / niche ETFs where market making is harder

    Options Market Makers:
    • Provide liquidity across the options chain (all strikes, all expirations)
    • Must manage Greek risk (delta, gamma, vega, theta)
    • Major: Citadel Securities, Susquehanna (SIG), Wolverine,
      IMC, Optiver, Jane Street

    Fixed-Income Market Makers:
    • Banks traditionally dominated: JPMorgan, Goldman Sachs, BofA,
      Citi, Barclays, Morgan Stanley
    • Electronic market makers expanding: Jane Street, Citadel, Jump
    • Post-2008 regulation (Volcker Rule) reduced bank market-making capacity

Economics of Market Making:
    Revenue:
    • Bid-ask spread capture
    • Rebates from exchanges (maker-taker model)
    • Information from order flow
    • Securities lending income
    Costs:
    • Adverse selection (trading against informed counterparties)
    • Inventory risk (holding positions that move against you)
    • Technology infrastructure
    • Regulatory compliance

═══════════════════════════════════════════════════════════════════════
HIGH-FREQUENCY TRADING (HFT)
═══════════════════════════════════════════════════════════════════════

Automated trading characterized by:
    • Extremely low latency (microseconds to nanoseconds)
    • High message rates (thousands to millions of orders per day)
    • Very short holding periods (seconds to minutes, rarely overnight)
    • Significant technology investment in speed
    • Statistical/quantitative strategies

HFT share of US equity volume: ~50-60% of trades, ~20-25% of dollar volume

HFT Strategies:

    Market Making / Liquidity Provision:
    • Continuously quote bid/ask prices across many securities
    • Earn the spread; manage inventory risk electronically
    • Cancel and replace quotes rapidly as conditions change
    • Dominant source of revenue for most HFT firms

    Statistical Arbitrage:
    • Exploit short-term pricing inefficiencies between related securities
    • Pairs trading, index arbitrage, ETF arbitrage
    • Mean-reversion strategies on micro timescales
    • Cross-asset correlations

    Latency Arbitrage:
    • Exploit speed advantages to trade on stale quotes
    • Price discrepancies between exchanges (SIP latency)
    • Cross-venue arbitrage (trade at faster venue, capture slow one)
    • Most controversial HFT strategy (seen as "picking off" slow quotes)

    Event Trading:
    • Ultra-fast reaction to news, economic data releases
    • Natural language processing of news feeds
    • Macroeconomic data (FOMC, NFP, CPI)
    • Earnings announcements, corporate actions

    Structural Strategies:
    • Exploit market microstructure features
    • Opening/closing auction strategies
    • End-of-day rebalancing (anticipate index fund flows)
    • Options expiration strategies (gamma hedging flows)

Major HFT / Electronic Trading Firms:
    • Citadel Securities – Largest US equity wholesaler and market maker
    • Virtu Financial – Publicly traded, market making across asset classes
    • Jane Street – Major in ETFs, options, and crypto
    • Jump Trading – Multi-asset, global
    • Tower Research Capital
    • Hudson River Trading (HRT)
    • DRW Holdings
    • IMC Trading
    • Optiver – Dutch-origin, options and ETF specialist
    • Flow Traders – Dutch, ETF market making globally
    • Susquehanna International Group (SIG) – Options, ETFs, quantitative
    • Two Sigma Securities
    • XTX Markets – London-based, FX and equities
    • GTS (Global Trading Systems) – NYSE DMM

Technology Infrastructure:
    • Co-location at exchange data centers
    • Microwave / millimeter-wave towers (Chicago-NJ, London-Frankfurt)
    • FPGA (Field-Programmable Gate Arrays) for hardware-level speed
    • Kernel bypass networking (DPDK, Solarflare/Xilinx)
    • Custom network switches and routers
    • Specialized CPU optimization (tick-to-trade < 1 microsecond)
    • Cross-connects and dark fiber

Controversies and Regulation:
    • Flash Crash (May 6, 2010) – DJIA dropped ~1,000 points in minutes
    • "Arms race" in speed (socially wasteful investment?)
    • Market complexity and fragmentation
    • Quote stuffing and layering (illegal manipulation)
    • Spoofing (placing orders intended to be cancelled to manipulate)
      – Now explicitly illegal under Dodd-Frank
    • IEX "speed bump" (350 microsecond delay to reduce latency advantage)
    • SEC Market Structure reforms (proposed changes to PFOF, tick sizes)
    • MiFID II – HFT firms must register, risk controls, algo testing
    • Circuit breakers (LULD – Limit Up/Limit Down) to prevent flash crashes

═══════════════════════════════════════════════════════════════════════
INVESTMENT BANKS / BROKER-DEALERS
═══════════════════════════════════════════════════════════════════════

Full-service intermediaries connecting capital seekers with capital
providers. Post-2008, most major investment banks became bank holding
companies regulated by the Federal Reserve.

Functions:
    • Underwriting (equity IPOs, bond issuances)
    • Sales & Trading (market making, execution services)
    • M&A Advisory
    • Securities Research
    • Prime Brokerage (hedge fund services)
    • Structured Products / Financial Engineering
    • Asset Management (many have asset management divisions)
    • Wealth Management

Major Global Investment Banks (Bulge Bracket):
    • JPMorgan Chase
    • Goldman Sachs
    • Morgan Stanley
    • Bank of America Securities
    • Citigroup
    • Barclays
    • Deutsche Bank
    • UBS
    • Credit Suisse (acquired by UBS, 2023)
    • HSBC

═══════════════════════════════════════════════════════════════════════
PRIME BROKERAGE
═══════════════════════════════════════════════════════════════════════

Suite of services provided by major banks to hedge funds and other
institutional investors:

    • Custody of assets
    • Securities lending (for short selling)
    • Margin financing (leverage)
    • Trade execution
    • Capital introduction (connecting funds with investors)
    • Risk analytics and reporting
    • Cash management
    • Synthetic prime brokerage (via swaps/TRS)

Major Prime Brokers:
    JPMorgan, Goldman Sachs, Morgan Stanley, BofA, Barclays, UBS

Multi-prime model: Most large hedge funds use multiple prime brokers
to diversify counterparty risk (accelerated after Lehman collapse).

═══════════════════════════════════════════════════════════════════════
RETAIL INVESTORS
═══════════════════════════════════════════════════════════════════════

Individual investors trading for their own accounts.

Evolution:
    • Traditional: Full-service brokers, phone orders, high commissions
    • Discount brokers (1990s): Charles Schwab, TD Ameritrade, E*Trade
    • Online trading (2000s): Lower costs, electronic execution
    • Commission-free era (2019+): Schwab, Fidelity, Robinhood → zero commissions
    • Meme stock era (2021): GameStop, AMC, coordinated retail trading (WallStreetBets)
    • Current: Fractional shares, crypto, options trading widely accessible

Major Retail Platforms (US):
    • Fidelity – Largest by client assets
    • Charles Schwab (merged with TD Ameritrade) – Largest by number of accounts
    • Vanguard – Primarily funds, growing brokerage
    • Robinhood – Mobile-first, popularized zero-commission trading
    • Interactive Brokers – Favored by active traders, global market access
    • E*Trade (Morgan Stanley)
    • Webull, SoFi, Public, Tastytrade

Retail Trading Characteristics:
    • Growing share of equity market volume (~20-25% of US equity volume)
    • Significant options trading (especially short-dated/0DTE)
    • ETFs are primary investment vehicle for many retail investors
    • Increasing use of fractional shares
    • Social media influence on investment decisions
    • PFOF-driven execution (orders routed to wholesale market makers)

═══════════════════════════════════════════════════════════════════════
INDEX PROVIDERS
═══════════════════════════════════════════════════════════════════════

Companies that design, calculate, and maintain financial indices.
Their methodological decisions determine trillions of dollars in
index-tracking investments.

Major Providers:
    • S&P Dow Jones Indices (S&P Global) – S&P 500, DJIA
    • MSCI – MSCI World, ACWI, Emerging Markets, ESG indices
    • FTSE Russell (LSEG) – FTSE 100, Russell 2000, FTSE All-World
    • Bloomberg – Bloomberg Barclays bond indices
    • ICE (Intercontinental Exchange) – BofA bond indices
    • Nasdaq – Nasdaq-100, Nasdaq Composite
    • Solactive – Fast-growing, lower-cost alternative (used by many ETFs)
    • Morningstar – Morningstar indices, fund ratings

Revenue model: Licensing fees from ETF issuers, futures exchanges,
and structured product issuers (basis point fee on AUM tracking the index).

═══════════════════════════════════════════════════════════════════════
CUSTODIAN BANKS
═══════════════════════════════════════════════════════════════════════

Banks that hold and safeguard financial assets for institutional investors.

Functions:
    • Safekeeping of securities (global custody)
    • Settlement of trades
    • Corporate actions processing
    • Income collection (dividends, coupons)
    • FX execution for cross-border investments
    • Fund accounting and NAV calculation
    • Transfer agency (mutual fund/ETF share recordkeeping)
    • Securities lending
    • Compliance reporting

Major Custodians:
    • BNY Mellon – ~$47+ trillion in assets under custody
    • State Street – ~$40+ trillion
    • JPMorgan – ~$30+ trillion
    • Citibank – ~$25+ trillion
    • Northern Trust – ~$15+ trillion
    • HSBC Securities Services
    • BNP Paribas Securities Services
"""
