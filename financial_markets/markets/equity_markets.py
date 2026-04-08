"""
Equity Markets (Stock Markets)
==============================

Equity markets facilitate the issuance and trading of ownership shares in
publicly listed companies. They are the most visible segment of global
capital markets.

MARKET SIZE & SCOPE (approximate as of mid-2020s)
──────────────────────────────────────────────────
• Global equity market capitalization: ~$110+ trillion
• Number of listed companies worldwide: ~58,000+
• Major indices track hundreds to thousands of securities

PRIMARY MARKET (Issuance)
─────────────────────────
Securities are created and sold to investors for the first time.

IPO (Initial Public Offering)
    The process by which a private company first sells shares to the public.

    Steps:
    1. Selection of underwriters (investment banks)
    2. Due diligence and SEC registration (Form S-1 in the US)
    3. Roadshow – management presents to institutional investors
    4. Book building – underwriters gauge demand and set price range
    5. Pricing – final offer price determined night before trading
    6. Allocation – shares distributed to institutional and retail investors
    7. First day of trading on the exchange

    Key Terms:
    • Underwriter: Investment bank managing the offering
    • Greenshoe option: Over-allotment option (typically 15% extra shares)
    • Lock-up period: Insiders restricted from selling (usually 90–180 days)
    • Quiet period: Restrictions on promotional communications

Direct Listing (DPO – Direct Public Offering)
    Company lists existing shares without issuing new ones or using
    underwriters. No capital is raised; existing shareholders can sell.
    Examples: Spotify (2018), Slack (2019), Coinbase (2021).

SPAC (Special Purpose Acquisition Company)
    A shell company raises capital through an IPO, then merges with a
    private target company within a deadline (typically 18–24 months).
    The target becomes public through the merger ("de-SPAC").
    SPACs surged in 2020–2021, then declined under regulatory scrutiny.

Follow-On / Secondary Offering
    Additional shares issued by an already-public company.
    • Dilutive: New shares created, diluting existing shareholders.
    • Non-dilutive: Existing shareholders sell their shares.

Rights Offering
    Existing shareholders given the right (but not obligation) to buy
    additional shares at a discount, in proportion to their holdings.

SECONDARY MARKET (Trading)
──────────────────────────
Existing securities traded among investors. The issuing company does not
receive proceeds from secondary market trades.

Market Structures:
    • Auction Market – Buyers and sellers submit orders; trades executed
      at a single clearing price (e.g., NYSE opening/closing auctions).
    • Continuous Market – Trades execute throughout the day as orders match.
    • Dealer / Market-Maker Market – Dealers quote bid/ask prices and trade
      from their own inventory (e.g., Nasdaq's historical structure).
    • Hybrid – Combination of auction and dealer models (modern NYSE).

EQUITY MARKET SEGMENTS
──────────────────────
By Market Capitalization:
    • Mega-cap:  > $200 billion
    • Large-cap: $10 billion – $200 billion
    • Mid-cap:   $2 billion – $10 billion
    • Small-cap: $300 million – $2 billion
    • Micro-cap: $50 million – $300 million
    • Nano-cap:  < $50 million

By Style:
    • Growth stocks – High revenue/earnings growth expectations, higher P/E
    • Value stocks  – Trading below intrinsic value estimates, lower P/E
    • Blend/Core    – Characteristics of both growth and value

By Sector (GICS – Global Industry Classification Standard):
    1. Energy
    2. Materials
    3. Industrials
    4. Consumer Discretionary
    5. Consumer Staples
    6. Health Care
    7. Financials
    8. Information Technology
    9. Communication Services
    10. Utilities
    11. Real Estate

MAJOR GLOBAL EQUITY EXCHANGES
──────────────────────────────
Americas:
    • NYSE (New York Stock Exchange) – Largest by market cap
    • Nasdaq – Second largest, tech-heavy
    • TMX Group (Toronto Stock Exchange) – Canada
    • B3 (Brasil Bolsa Balcão) – Brazil

Europe:
    • Euronext (Amsterdam, Paris, Brussels, Lisbon, Dublin, Oslo, Milan)
    • London Stock Exchange (LSE)
    • Deutsche Börse (Xetra / Frankfurt)
    • SIX Swiss Exchange (Zurich)
    • Nasdaq Nordic & Baltic (Stockholm, Helsinki, Copenhagen)
    • Moscow Exchange (MOEX)

Asia-Pacific:
    • Tokyo Stock Exchange (JPX – Japan Exchange Group)
    • Shanghai Stock Exchange (SSE)
    • Shenzhen Stock Exchange (SZSE)
    • Hong Kong Exchanges (HKEX)
    • National Stock Exchange of India (NSE)
    • BSE (formerly Bombay Stock Exchange)
    • Korea Exchange (KRX)
    • ASX (Australian Securities Exchange)
    • Singapore Exchange (SGX)

Middle East & Africa:
    • Saudi Exchange (Tadawul)
    • Johannesburg Stock Exchange (JSE)
    • Tel Aviv Stock Exchange (TASE)

MAJOR EQUITY INDICES
────────────────────
US:
    • S&P 500       – 500 large-cap US stocks (market-cap weighted)
    • Dow Jones Industrial Average (DJIA) – 30 blue-chip stocks (price-weighted)
    • Nasdaq Composite – All Nasdaq-listed stocks (~3,000+)
    • Nasdaq-100     – 100 largest non-financial Nasdaq stocks
    • Russell 2000   – 2,000 small-cap US stocks
    • Russell 3000   – Broad US market (top 3,000)
    • S&P 400 MidCap – 400 mid-cap stocks
    • Wilshire 5000  – Total US equity market

International:
    • FTSE 100       – 100 largest UK-listed companies
    • DAX 40         – 40 largest German companies
    • CAC 40         – 40 largest French companies
    • Nikkei 225     – 225 Japanese stocks (price-weighted)
    • TOPIX          – All Tokyo Stock Exchange First Section stocks
    • Hang Seng      – Leading Hong Kong stocks
    • CSI 300        – 300 largest Chinese A-shares (Shanghai + Shenzhen)
    • KOSPI          – Korean composite index
    • S&P/ASX 200    – 200 largest Australian stocks
    • BSE Sensex     – 30 largest Indian stocks
    • Nifty 50       – 50 largest Indian stocks

Global / Regional:
    • MSCI World       – ~1,500 stocks across 23 developed markets
    • MSCI ACWI        – All Country World Index (developed + emerging)
    • MSCI Emerging Markets – ~1,400 stocks across 24 emerging markets
    • FTSE All-World    – ~4,000 stocks across 49 countries
    • S&P Global 1200   – Composite of 7 regional indices

INDEX CONSTRUCTION METHODOLOGIES
─────────────────────────────────
Price-Weighted:
    Sum of member stock prices ÷ divisor. Higher-priced stocks have more
    influence regardless of company size. Example: DJIA, Nikkei 225.

Market-Cap Weighted (Capitalization-Weighted):
    Each stock's weight = its market cap ÷ total index market cap.
    Larger companies dominate. Example: S&P 500, MSCI indices.

    Variant – Float-Adjusted: Only free-float shares counted (excluding
    insider/government holdings). Most modern indices use this.

Equal-Weighted:
    Every stock has the same weight (e.g., 1/500 for a 500-stock index).
    Rebalanced periodically. Gives more weight to smaller constituents.

Fundamentally-Weighted:
    Weighted by fundamental factors (revenue, dividends, book value)
    rather than market cap. Example: FTSE RAFI indices.

EQUITY VALUATION METRICS
─────────────────────────
• P/E Ratio (Price/Earnings)         – Price per share ÷ EPS
• Forward P/E                        – Price ÷ estimated future EPS
• PEG Ratio                          – P/E ÷ earnings growth rate
• P/B Ratio (Price/Book)             – Price ÷ book value per share
• P/S Ratio (Price/Sales)            – Market cap ÷ total revenue
• EV/EBITDA                          – Enterprise value ÷ EBITDA
• Dividend Yield                     – Annual dividends per share ÷ price
• Free Cash Flow Yield               – FCF per share ÷ price
• ROE (Return on Equity)             – Net income ÷ shareholders' equity
• ROIC (Return on Invested Capital)  – NOPAT ÷ invested capital

CORPORATE ACTIONS AFFECTING EQUITY
────────────────────────────────────
• Dividends       – Cash or stock distributions to shareholders
• Stock splits    – Increase shares outstanding, reduce price proportionally
• Reverse splits  – Decrease shares, increase price
• Buybacks        – Company repurchases its own shares
• Mergers & Acquisitions (M&A) – Consolidation of companies
• Spin-offs       – Separation of a division into a new public company
• Tender offers   – Public offer to buy shares at a premium
• Delisting       – Removal from exchange (voluntary or involuntary)

TRADING MECHANICS
─────────────────
Order Types:
    • Market order     – Execute immediately at best available price
    • Limit order      – Execute at specified price or better
    • Stop order       – Triggered when price reaches stop level
    • Stop-limit order – Stop trigger + limit price constraint
    • Iceberg order    – Large order with only small portion visible
    • Fill-or-Kill     – Execute entire order immediately or cancel
    • Immediate-or-Cancel – Fill what's possible, cancel remainder
    • Good-Till-Cancelled (GTC) – Remains active until filled or cancelled
    • Market-on-Close (MOC) – Execute at closing auction price
    • Market-on-Open (MOO)  – Execute at opening auction price
    • VWAP order       – Target volume-weighted average price
    • TWAP order       – Target time-weighted average price

Trading Sessions (US):
    • Pre-market:   4:00 AM – 9:30 AM ET
    • Regular:      9:30 AM – 4:00 PM ET
    • After-hours:  4:00 PM – 8:00 PM ET
    • Opening Auction: ~9:28–9:30 AM ET
    • Closing Auction: ~3:50–4:00 PM ET (highest volume period)

Settlement:
    • US equities settle T+1 (trade date + 1 business day) as of May 2024
    • Previously T+2, and before that T+3
    • Europe transitioning to T+1 (targeted for 2027)

SHORT SELLING
─────────────
Selling borrowed shares with the expectation of buying them back at a
lower price.

Mechanics:
    1. Borrow shares from a broker (who sources from client accounts)
    2. Sell borrowed shares on the open market
    3. Buy shares back later ("cover" the short position)
    4. Return shares to the lender
    5. Profit/loss = sell price – buy price – borrowing costs

Key Concepts:
    • Short interest – Total shares sold short for a stock
    • Short interest ratio (days to cover) – Short interest ÷ avg daily volume
    • Borrow rate / lending fee – Cost to borrow shares (annualized)
    • Hard-to-borrow list – Stocks with limited shares available to short
    • Short squeeze – Rapid price increase forcing short sellers to cover
    • Regulation SHO – SEC rules requiring locate and close-out of fails
    • Uptick rule (alternative) – Restriction on shorting during declines
    • Naked short selling – Selling short without borrowing (largely prohibited)

MARGIN TRADING
──────────────
Buying securities with borrowed money from a broker.

Regulation T (US):
    • Initial margin: 50% of purchase price
    • Maintenance margin: 25% minimum (many brokers require 30–40%)
    • Margin call: Triggered when equity falls below maintenance level
    • Forced liquidation: Broker sells positions if margin call not met

Portfolio Margin:
    • Risk-based margin calculation (TIMS model)
    • Available to qualified accounts (typically $100k+ minimum)
    • Can provide significantly lower margin requirements for hedged positions

DARK POOLS & ALTERNATIVE VENUES
─────────────────────────────────
Dark pools are private trading venues where orders are not displayed
publicly before execution. They provide anonymity and reduce market impact
for large institutional orders.

Types:
    • Broker-dealer owned (e.g., Goldman Sachs Sigma X, Morgan Stanley MS Pool)
    • Exchange-owned (e.g., Cboe BIDS)
    • Independent / electronic market maker operated
    • Consortium-owned (e.g., Luminex, now part of Cowen)

Regulation:
    • Regulated as Alternative Trading Systems (ATS) by the SEC
    • Must file Form ATS and report trading data
    • Subject to Regulation ATS and Regulation NMS
    • Dark pool volume is ~40–45% of US equity trading (2024)
"""
