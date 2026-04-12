"""
Execution Algorithms & Market Impact
=====================================

Execution algorithms are automated strategies designed to execute
large orders while minimising market impact, transaction costs, and
information leakage.  They sit at the intersection of market
microstructure theory and practical trading.

BENCHMARK ALGORITHMS
────────────────────

VWAP (Volume-Weighted Average Price):
    Target: match the day's VWAP.
    Mechanism: slice the order across the trading day proportional
    to the historical intraday volume profile (U-shaped: high at
    open/close, low midday).
    Use case: passive benchmark for portfolio transitions, index
    rebalancing, or when the trader has no urgency.
    Weakness: predictable participation can be detected and
    front-run by informed counterparties.

TWAP (Time-Weighted Average Price):
    Target: execute evenly over a specified time window.
    Mechanism: divide order into equal time-sliced child orders.
    Use case: when volume profile is unavailable, or for illiquid
    names where volume is sporadic.
    Simpler than VWAP; less adaptable.

POV (Percentage of Volume):
    Target: participate at a fixed percentage of real-time volume
    (e.g., "execute at 10% of market volume").
    Mechanism: monitor live volume and adjust order rate.
    Use case: when the trader wants to "go with the flow" and
    avoid outsized footprint.  Adaptive to real conditions.
    Risk: in low-volume periods, execution slows dramatically.

Implementation Shortfall (Arrival Price):
    Target: minimise the difference between the decision price
    (when the PM decided to trade) and the final execution price.
    Mechanism: trades aggressively early (to reduce timing risk)
    then slows down (to reduce impact).  Balances urgency vs cost.
    Framework: Robert Almgren & Neil Chriss (2000).
    Use case: alpha-driven orders where the expected signal decays
    over time.  The urgency parameter controls the speed.

MARKET IMPACT MODELS
────────────────────

Temporary vs. Permanent Impact:
    • Temporary impact: price displacement that reverts after the
      trade completes (due to liquidity demand).
    • Permanent impact: lasting price change reflecting new
      information incorporated by the trade.

Almgren-Chriss Model (2000):
    Optimal execution framework balancing market impact (from
    trading too fast) against timing risk (from trading too slowly).
    • Linear temporary impact: proportional to trading rate.
    • Linear permanent impact: proportional to trade size.
    • Produces an optimal liquidation trajectory given a risk-aversion
      parameter.
    • Foundation of most modern execution algorithms.

Square-Root Law of Market Impact:
    Empirical observation (Bouchaud, Farmer, Lillo 2009):
    Impact ≈ σ × √(Q / V)
    Where σ = daily volatility, Q = order quantity, V = daily volume.
    • Impact grows sub-linearly with order size.
    • Remarkably stable across markets, time periods, and asset classes.
    • Implies: doubling order size increases impact by only ~41%.

Kyle's Lambda (1985):
    In Kyle's model, the market maker's lambda (λ) measures price
    impact per unit of order flow.  Higher λ = less liquid market.
    Empirically, λ is higher for small-cap stocks, illiquid names,
    and during periods of market stress.

Impact Decay and Resilience:
    After a large trade, the temporary impact component decays over
    minutes to hours as the order book refills.  The speed of decay
    depends on market liquidity and the stock's "resilience."

TRANSACTION COST ANALYSIS (TCA)
────────────────────────────────

Explicit Costs:
    • Commissions (broker fees, per-share or per-trade)
    • Exchange fees (maker/taker, clearing fees)
    • Taxes (stamp duty in UK, FTT in France/Italy, Abgeltungsteuer
      effect on holding period decisions in Germany)
    • Clearing and settlement fees

Implicit Costs:
    • Bid-ask spread: cost of immediacy.  Half-spread on entry,
      half-spread on exit.
    • Market impact: additional cost from your order moving the price.
    • Timing cost: adverse price movement between decision and
      execution.
    • Opportunity cost: alpha lost from orders not executed.

Implementation Shortfall Decomposition:
    Total IS = Execution Cost + Opportunity Cost
    Execution Cost = Timing Cost + Market Impact + Commission
    Timing Cost = slippage between decision price and execution start.
    Market Impact = slippage during execution.
    Opportunity Cost = unrealised P&L from unexecuted portion.

Pre-Trade Analysis:
    Estimate expected cost before execution using models based on
    order size, volatility, spread, and ADV.  Used to choose the
    right algorithm and set urgency parameters.

Post-Trade Measurement:
    Compare actual execution against benchmarks (VWAP, arrival price,
    close price) to evaluate broker/algorithm performance.

SMART ORDER ROUTING (SOR)
──────────────────────────

Multi-Venue Landscape:
    Modern equity markets are fragmented across many venues:
    • Primary exchanges (Xetra, NYSE, Nasdaq, LSE)
    • Alternative venues (Chi-X/Cboe Europe, Turquoise, Aquis)
    • Dark pools (Liquidnet, POSIT, UBS MTF, Cboe BIDS)
    • Systematic internalisers (SI, under MiFID II)

    Smart Order Routers scan all available venues to find the best
    execution: best price, deepest liquidity, lowest fees.

Reg NMS (US) – Best Execution:
    Rule 611: orders must be routed to the venue displaying the best
    price (NBBO).  Cannot "trade through" a better price.

MiFID II (EU) – Best Execution:
    Broader obligation: consider price, cost, speed, likelihood of
    execution, size, market impact.  Publish RTS 27/28 reports.
    No strict "trade-through" rule like Reg NMS but similar spirit.

Routing Strategies:
    • Sequential: try venues in priority order.
    • Spray: send to multiple venues simultaneously.
    • Smart: dynamic allocation based on real-time liquidity signals.

MARKET MICROSTRUCTURE
──────────────────────

Bid-Ask Spread Components (Roll, Stoll, Glosten-Harris):
    • Adverse selection: compensation for trading against informed
      counterparties (widest component for small-caps).
    • Inventory risk: cost of holding unwanted positions.
    • Order processing: fixed costs of market making.

Price Discovery:
    The process by which new information is incorporated into prices.
    Occurs primarily at exchanges through order flow; dark pools
    generally free-ride on lit-market price discovery.

Order Book Dynamics:
    • Limit order book (LOB): visible bid/ask levels and sizes.
    • Market orders consume liquidity (remove from LOB).
    • Limit orders provide liquidity (add to LOB).
    • Queue priority: price-time (most exchanges), pro-rata (some
      futures).

Tick Size:
    Minimum price increment.  Affects spread, depth, and market-maker
    economics.
    • US equities: $0.01 for stocks > $1 (SEC Rule 612).
    • EU: MiFID II tick-size regime based on liquidity bands.
    • Smaller tick size → tighter spreads but thinner depth.
    • Larger tick size → wider spreads but deeper order book.

Maker-Taker Model:
    • Makers (limit orders, add liquidity): receive rebate.
    • Takers (market orders, remove liquidity): pay fee.
    • Inverted venues: takers receive rebate, makers pay.
    • Economics influence routing decisions and market structure.

EXECUTION ACROSS ASSET CLASSES
───────────────────────────────

Equities:
    • Most algorithmic, most fragmented, most studied.
    • Central limit order books on lit exchanges + dark venues.

Fixed Income:
    • Primarily OTC, RFQ-based (MarketAxess, Tradeweb).
    • Electronic trading growing but still dealer-intermediated.
    • Portfolio trading: execute entire bond baskets as single package.
    • Algo execution nascent but accelerating.

FX:
    • Fragmented across ECNs (EBS, Reuters Matching), single-dealer
      platforms, multi-dealer platforms (FXall, Currenex).
    • Algos common for large orders: TWAP, VWAP, iceberg.
    • "Last look": controversial practice where dealers can reject
      fills after seeing the order.

Futures:
    • Central limit order book on exchanges (CME Globex, Eurex).
    • Less fragmentation than equities.
    • Spread trading algos (calendar spreads, inter-commodity).

Options:
    • Multi-listed across 16+ US exchanges.
    • Complex order routing due to multi-leg strategies.
    • Market-maker interaction (many exchanges use hybrid models).

REGULATORY FRAMEWORK
─────────────────────
• Reg NMS (US, 2005/2007): order protection, access, sub-penny,
  market data rules.
• MiFID II (EU, 2018): best execution, algo registration, tick
  sizes, transparency, consolidated tape (in progress).
• Market Access Rule (SEC Rule 15c3-5): pre-trade risk controls
  for electronic access.
• CAT (Consolidated Audit Trail): comprehensive US trade tracking.
• ESMA guidelines on algorithmic trading (under MiFID II).
"""
