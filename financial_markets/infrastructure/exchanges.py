"""
Exchanges – Trading Venues and Market Structure
================================================

═══════════════════════════════════════════════════════════════════════
EXCHANGE BUSINESS MODEL
═══════════════════════════════════════════════════════════════════════

Modern exchanges are typically publicly traded, for-profit corporations
(demutualized from their original member-owned structures).

Revenue Streams:
    • Transaction fees (trading commissions, clearing fees)
    • Market data sales (real-time quotes, historical data)
    • Listing fees (IPO and annual listing fees)
    • Technology services (co-location, connectivity)
    • Index licensing (S&P, FTSE Russell, MSCI license fees)
    • Derivatives trading and clearing
    • Information services and analytics
    • Regulatory services

MAJOR GLOBAL EXCHANGE GROUPS
──────────────────────────────

CME Group (Chicago):
    • CME (Chicago Mercantile Exchange) – Equity index, FX, interest rate futures
    • CBOT (Chicago Board of Trade) – Treasury, grain, agricultural futures
    • NYMEX (New York Mercantile Exchange) – Energy futures
    • COMEX (Commodity Exchange) – Metals futures
    • CME Clearing – One of world's largest CCPs
    • BrokerTec – Fixed income electronic trading
    • EBS – FX electronic trading
    • Largest derivatives exchange globally by volume

Intercontinental Exchange (ICE):
    • NYSE (New York Stock Exchange) – Largest equity exchange by market cap
    • NYSE Arca – ETF and equity trading
    • NYSE American – Small-cap equities
    • ICE Futures US – Soft commodities (coffee, sugar, cotton, cocoa)
    • ICE Futures Europe – Brent crude, European energy
    • ICE Clear Credit – CDS clearing
    • ICE Data Services – Pricing and reference data
    • Mortgage Technology (Ellie Mae) – Mortgage origination

Nasdaq Inc.:
    • Nasdaq Stock Market – Tech-heavy equity exchange
    • Nasdaq Nordic (formerly OMX) – Stockholm, Helsinki, Copenhagen, Iceland
    • Nasdaq Baltic – Riga, Tallinn, Vilnius
    • Nasdaq Futures (NFX) – Energy derivatives
    • Market technology (sold to 130+ exchanges globally)
    • Index business (Nasdaq-100, etc.)
    • Anti-financial crime technology (Verafin)

Cboe Global Markets:
    • Cboe Options Exchange – Largest US options exchange
    • Cboe BZX, BYX, EDGX, EDGA – Four US equity exchanges
    • Cboe Futures Exchange (CFE) – VIX futures
    • Cboe Europe – Pan-European equities
    • Cboe Australia, Cboe Japan, Cboe Canada
    • VIX index (Cboe Volatility Index) – "Fear gauge"
    • SPX options – Most traded index options in the world

London Stock Exchange Group (LSEG):
    • London Stock Exchange – UK/European equities
    • Borsa Italiana (Milan) – Italian market
    • LCH (London Clearing House) – Major CCP for IRS and other derivatives
    • FTSE Russell – Index provider (FTSE 100, Russell 2000, etc.)
    • Refinitiv – Data and analytics (acquired 2021)
    • Tradeweb (partial ownership) – Electronic bond trading

Euronext:
    • Amsterdam, Brussels, Dublin, Lisbon, Milan, Oslo, Paris
    • Pan-European exchange operator
    • Borsa Italiana acquired from LSEG (2021)
    • MTS – European government bond trading platform
    • Euronext Clearing, Euronext Securities

Deutsche Börse Group:
    • Xetra – German electronic equity trading
    • Frankfurt Stock Exchange
    • Eurex – Largest European derivatives exchange
    • Clearstream – CSD and settlement
    • 360T – FX trading platform
    • ISS (Institutional Shareholder Services) – Governance advisory

Japan Exchange Group (JPX):
    • Tokyo Stock Exchange (TSE) – Third largest globally by market cap
    • Osaka Exchange (OSE) – Derivatives
    • Japan Securities Clearing Corporation (JSCC)
    • TOPIX, Nikkei 225 (licensed from Nikkei)

Hong Kong Exchanges (HKEX):
    • Stock Exchange of Hong Kong – Gateway to China
    • Hong Kong Futures Exchange
    • London Metal Exchange (LME) – Acquired 2012
    • Stock Connect (Shanghai-Hong Kong, Shenzhen-Hong Kong)
    • Bond Connect – Access to China Interbank Bond Market

Singapore Exchange (SGX):
    • Equities, fixed income, derivatives
    • SGX Nifty (Indian index futures)
    • Iron ore futures
    • Asian FX derivatives
    • Gateway to ASEAN markets

Other Notable Exchanges:
    • B3 (Brazil) – Brazilian exchange, clearinghouse, and depository
    • Korea Exchange (KRX) – One of world's most active derivatives markets
      (KOSPI 200 options historically most traded by volume)
    • Taiwan Stock Exchange (TWSE)
    • National Stock Exchange of India (NSE) – Largest by equity derivatives volume
    • BSE (formerly Bombay Stock Exchange)
    • Saudi Exchange (Tadawul) – Largest in Middle East
    • Johannesburg Stock Exchange (JSE) – Largest in Africa
    • Australian Securities Exchange (ASX)
    • TMX Group (Toronto Stock Exchange, TSX Venture) – Canada
    • Moscow Exchange (MOEX) – Russia (sanctions-affected since 2022)

═══════════════════════════════════════════════════════════════════════
EXCHANGE TECHNOLOGY
═══════════════════════════════════════════════════════════════════════

Matching Engines:
    Core technology that matches buy and sell orders.
    • Price-time priority (most common): Best price first, then earliest order
    • Pro-rata matching: Fills distributed proportionally (some futures)
    • Latency: Modern matching engines operate in microseconds
    • Throughput: Millions of messages per second

    Key platforms:
    • Nasdaq INET – Used by Nasdaq exchanges
    • NYSE Pillar – NYSE's unified trading platform
    • CME Globex – Derivatives trading platform
    • Eurex T7 – Derivatives matching engine
    • ICE's trading platform
    • LSEG Millennium Exchange

Co-Location:
    Exchange data centers offer rack space adjacent to matching engines.
    • Reduces latency to microseconds
    • Critical for HFT firms
    • Revenue source for exchanges
    • Major data centers: Equinix NY5 (NYSE), Equinix NJ2 (Nasdaq),
      CME Aurora (Illinois)

Market Data:
    • Level 1: Best bid/ask price and size (top of book)
    • Level 2: Multiple levels of bid/ask (depth of book)
    • Level 3: Full order book (individual orders)
    • SIP (Securities Information Processor) – Consolidated US market data
      (CTA/CQS for NYSE-listed, UTP for Nasdaq-listed)
    • Proprietary data feeds – Direct from exchange (faster than SIP)
    • Tick data, historical data, reference data

═══════════════════════════════════════════════════════════════════════
ORDER ROUTING & MARKET ACCESS
═══════════════════════════════════════════════════════════════════════

Regulation NMS (US):
    National Market System rules (SEC, 2005/2007):
    • Order Protection Rule (Rule 611) – Must route to best price
    • Access Rule (Rule 610) – Limits access fees, requires connectivity
    • Sub-Penny Rule (Rule 612) – Minimum pricing increments
    • Market Data Rules – Consolidated data requirements

    Key concepts:
    • NBBO (National Best Bid and Offer) – Best available prices across
      all exchanges
    • Protected quote – Automated quote at NBBO that must be respected
    • Trade-through: Executing at inferior price when better price exists
      (prohibited)
    • Locked/crossed markets: Situations where bid ≥ ask across venues

Smart Order Routing (SOR):
    Algorithms that determine optimal venue for order execution.
    Consider: price, liquidity, fees/rebates, speed, fill probability.
    Route across lit exchanges, dark pools, and dealer internalization.

Payment for Order Flow (PFOF):
    Wholesale market makers (Citadel Securities, Virtu) pay retail
    brokers for their order flow. Execute at or better than NBBO.
    • Revenue model for zero-commission brokers (Robinhood, etc.)
    • Controversial: potential conflict of interest
    • Banned in UK, Canada; restricted in EU under MiFID II
    • SEC has considered restrictions/bans in US

Maker-Taker Fee Model:
    • Makers (provide liquidity via limit orders): Receive rebate
    • Takers (remove liquidity via market orders): Pay fee
    • Typical: -$0.0020 to -$0.0035 rebate / $0.0025 to $0.0035 fee per share
    • Inverted venues: Takers get rebate, makers pay (EDGA, BYX)
    • Incentivizes limit order placement and liquidity provision

═══════════════════════════════════════════════════════════════════════
ALTERNATIVE TRADING SYSTEMS
═══════════════════════════════════════════════════════════════════════

Dark Pools:
    (Detailed in equity_markets.py)
    Private venues with no pre-trade transparency.
    ~40-45% of US equity volume.

Systematic Internalizers (SI) – European:
    Investment firms that execute client orders against own capital
    on an organized, systematic basis outside a regulated market.
    Subject to MiFID II transparency requirements.

Electronic Communication Networks (ECNs):
    Electronic systems that automatically match buy and sell orders.
    Largely absorbed into exchange groups or evolved into exchanges.

Crossing Networks:
    Match large institutional orders at a reference price (e.g., midpoint
    of NBBO). Lower market impact for block trades.

Periodic Auctions:
    Frequent batch auctions (e.g., every 100ms) as an alternative to
    continuous trading. Cboe Europe Periodic Auctions is a major venue.
    Aggregates orders and executes at a single price.

Request-for-Quote (RFQ) Platforms:
    Investors request quotes from multiple dealers simultaneously.
    Dominant in fixed income (MarketAxess, Tradeweb) and ETF block trading.
"""
