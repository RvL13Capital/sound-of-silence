"""
Quantitative & Algorithmic Trading Strategies
==============================================

Quantitative trading uses mathematical models, statistical analysis,
and computational algorithms to identify and exploit market
inefficiencies systematically.

OVERVIEW
────────
Alpha Generation Pipeline:
    1. Idea generation (academic research, market observation, data)
    2. Signal construction (translate idea into measurable signal)
    3. Backtesting (test signal on historical data)
    4. Portfolio construction (combine signals, size positions)
    5. Execution (minimise market impact and transaction costs)
    6. Risk management (monitor, hedge, and control exposure)
    7. Performance attribution (understand what drove returns)

Systematic vs. Discretionary:
    • Systematic: rules-based, codified, repeatable, backtestable.
      Human makes the rules; computer executes.
    • Discretionary: human judgment drives decisions, informed by
      quantitative tools.  Harder to backtest.
    • Hybrid: systematic screening with discretionary overlay.

Notable Quant Firms:
    • Renaissance Technologies (Medallion Fund: ~66% gross CAGR)
    • Two Sigma, D.E. Shaw, Citadel, AQR Capital
    • Man Group (AHL, Numeric), Winton, PDT Partners
    • Millennium, Balyasny (multi-strategy pod shops)
    • Jump Trading, Jane Street (HFT / market making)

STATISTICAL ARBITRAGE
─────────────────────
Pairs Trading:
    • Identify two co-moving stocks (same sector, similar business).
    • Test for cointegration (Engle-Granger, Johansen test).
    • When the spread deviates from equilibrium by > N standard
      deviations, go long the underperformer / short the outperformer.
    • Exit when spread reverts to mean (or at a stop-loss).
    • Risk: structural break (spread diverges permanently, e.g.,
      fundamental change in one company).

Mean Reversion:
    • Ornstein-Uhlenbeck process: dX = θ(μ − X)dt + σdW.
    • Half-life of mean reversion = ln(2) / θ.  Shorter half-life =
      faster reversion = more tradeable.
    • Bollinger Band strategies: buy when price touches lower band,
      sell at upper band.
    • RSI-based: buy when RSI < 30, sell when RSI > 70.

Cross-Sectional Momentum and Reversal:
    • Rank stocks by past returns; buy winners, sell losers
      (Jegadeesh-Titman 1993).
    • Short-term reversal (< 1 month): losers bounce, winners pull back.
    • Intermediate momentum (2-12 months): winners continue winning.
    • Long-term reversal (3-5 years): DeBondt-Thaler.

Sector-Neutral and Market-Neutral Construction:
    • Construct portfolio so that net market exposure (beta) ≈ 0.
    • Dollar-neutral: equal long and short dollar exposure.
    • Beta-neutral: hedge market beta to zero.
    • Sector-neutral: zero net exposure to each GICS sector.
    • Reduces systematic risk, isolates idiosyncratic alpha.

MOMENTUM STRATEGIES
───────────────────
Time-Series Momentum (Trend Following):
    • Go long assets with positive recent returns; short assets with
      negative recent returns (Moskowitz, Ooi, Pedersen 2012).
    • Works across asset classes: equities, bonds, commodities, FX.
    • CTA / Managed Futures industry built on this (~$350B AUM).
    • Key firms: Man AHL, Winton, Aspect Capital, Systematica.

Cross-Sectional Momentum:
    • Rank all stocks (or assets) by past 12-1 month return.
    • Buy top decile, sell bottom decile.
    • Skip most recent month to avoid reversal.
    • Academic backing: Jegadeesh-Titman (1993), Asness-Moskowitz-
      Pedersen (2013).

Momentum Crashes (Daniel-Moskowitz 2016):
    • Momentum strategies experience severe losses during market
      reversals (March 2009, April 2020).
    • Past losers rebound faster than past winners during sharp
      V-recoveries.
    • Mitigation: dynamic hedging, reduced exposure during high
      volatility, market-regime filter.

Dual Momentum (Gary Antonacci):
    • Combines absolute (time-series) and relative (cross-sectional)
      momentum.
    • Hold an asset only if it has positive absolute return AND is the
      strongest in its peer group.

FACTOR INVESTING
────────────────
Fama-French Five-Factor Model (2015):
    R − Rf = α + β₁(MKT) + β₂(SMB) + β₃(HML) + β₄(RMW) + β₅(CMA)
    • MKT: market excess return.
    • SMB: Small Minus Big (size premium).
    • HML: High Minus Low (value premium, book-to-market).
    • RMW: Robust Minus Weak (profitability premium).
    • CMA: Conservative Minus Aggressive (investment premium).

Additional Factors:
    • Momentum (Carhart 1997, Jegadeesh-Titman): UMD factor.
    • Low Volatility / Minimum Variance: Ang et al. (2006, 2009).
    • Quality: Asness-Frazzini-Pedersen (2019) "Quality Minus Junk."
    • Gross profitability: Novy-Marx (2013).
    • 52-week high: George-Hwang (2004).

Factor Timing and Crowding:
    • Factors go through cycles: value underperformed 2010-2020;
      outperformed sharply in 2022.
    • Factor crowding: too much capital chasing the same signals
      compresses the premium.
    • Timing factors is extremely difficult (as hard as timing the
      market).
    • Diversification across factors is more reliable than timing.

Smart Beta Implementation:
    • Use factor-weighted indices instead of market-cap-weighted.
    • Available through ETFs (VLUE, MTUM, QUAL, USMV, etc.).
    • Lower cost than active management but not as cheap as pure
      passive.

MARKET MAKING STRATEGIES
─────────────────────────
Avellaneda-Stoikov Model (2008):
    Optimal bid/ask quotes as a function of inventory, mid-price,
    volatility, and order arrival intensity.
    • Quote wider when inventory is large (protect against adverse moves).
    • Quote tighter when competition is high (capture flow).

Inventory Management:
    Market makers must balance capturing spread revenue against
    accumulating unwanted directional risk.
    • Skew quotes: shade bid/ask to attract flow that reduces
      inventory.
    • Hedge residual delta with correlated instruments or futures.

Adverse Selection:
    When an informed trader trades against a market maker's quote,
    the market maker loses (the "winner's curse" of market making).
    Detecting and avoiding toxic flow is critical.

HIGH-FREQUENCY TRADING (HFT)
──────────────────────────────
(Detailed separately in market_makers_and_hft.py)

Key HFT strategies:
    • Electronic market making (dominant revenue source).
    • Latency arbitrage (cross-venue stale-quote exploitation).
    • Statistical arbitrage at microsecond timescales.
    • Event-driven (react to macro data, earnings in microseconds).

MACHINE LEARNING IN TRADING
─────────────────────────────

Feature Engineering:
    • Price-based: returns, momentum, volatility, relative strength.
    • Fundamental: valuation ratios, earnings growth, quality metrics.
    • Alternative data: satellite imagery, NLP on news/filings/social
      media, credit card data, web traffic, app downloads.
    • Microstructure: order book imbalance, trade flow toxicity.

Supervised Learning:
    • Classification: predict up/down direction.
    • Regression: predict magnitude of return.
    • Algorithms: Random Forest, Gradient Boosting (XGBoost, LightGBM),
      Support Vector Machines, neural networks.

Deep Learning:
    • LSTMs (Long Short-Term Memory): capture temporal dependencies
      in sequential financial data.
    • Transformers: attention-based architectures adapted from NLP to
      time series (growing research area).
    • Autoencoders: dimensionality reduction, anomaly detection.

Reinforcement Learning:
    • Agent learns optimal trading policy through trial and error.
    • Applied to execution (optimal order placement) and portfolio
      management (dynamic allocation).
    • Challenges: non-stationarity, sparse rewards, simulation-to-
      reality gap.

Pitfalls:
    • Overfitting: models memorise noise, not signal.
    • Look-ahead bias: using future information in training.
    • Non-stationarity: market regimes change; past patterns break.
    • Data mining / p-hacking: test enough features and something
      will appear significant by chance.
    • Publication bias: only positive results get published.
    • Low signal-to-noise ratio: financial data is inherently noisy.

BACKTESTING AND STRATEGY DEVELOPMENT
──────────────────────────────────────

Walk-Forward Optimisation:
    • Divide data into sequential in-sample and out-of-sample windows.
    • Optimise on in-sample, test on out-of-sample.
    • Slide the window forward and repeat.
    • Most realistic test of how a strategy would have performed.

Cross-Validation for Time Series:
    • Standard k-fold CV is invalid for time series (leaks future
      into training).
    • Use expanding-window or sliding-window CV.
    • Purge gap between training and test to avoid look-ahead.

Common Pitfalls:
    • Look-ahead bias: using data that wasn't available at decision
      time (e.g., using closing price to decide at close).
    • Survivorship bias: backtesting only on stocks that still exist
      today; delisted losers are missing from the data.
    • Transaction cost underestimation: assuming zero spread, zero
      impact, zero commission.  Realistic costs often eliminate the edge.
    • Overfitting: too many parameters relative to independent
      observations.  Rule of thumb: degrees of freedom ≪ sample size.
    • Selection bias: choosing the backtest window or parameter set
      that looks best.

PORTFOLIO CONSTRUCTION
───────────────────────

Mean-Variance Optimisation (Markowitz 1952):
    Maximise E[R] − λ × Var(R) subject to constraints.
    • Produces the efficient frontier.
    • Highly sensitive to input estimates (especially expected returns).
    • Often produces extreme, unstable weights.

Black-Litterman (1992):
    Combines equilibrium expected returns (from market-cap weights)
    with investor views.  Produces more stable, intuitive weights
    than raw Markowitz.

Risk Parity:
    Allocate so each asset (or factor) contributes equally to
    portfolio risk.  Requires no return forecasts — only covariance.
    Bridgewater, AQR, PanAgora implementations.

Hierarchical Risk Parity (HRP, Lopez de Prado 2016):
    Uses hierarchical clustering on the covariance matrix to build
    a tree-based allocation.  More robust to estimation error than
    traditional mean-variance.

Kelly Criterion for Portfolios:
    Multi-asset extension of Kelly: f = Σ⁻¹ μ.
    Maximises geometric growth rate.  In practice, use fractional
    Kelly (½ or less) for stability.

Constraints:
    • Turnover limits (control transaction costs).
    • Sector / country / factor concentration caps.
    • Position-level limits (min/max weight).
    • Leverage constraints.

STRATEGY PERFORMANCE METRICS
──────────────────────────────
• Annualised return (CAGR).
• Annualised volatility.
• Sharpe ratio (target: > 1.0 for a good strategy, > 2.0 excellent).
• Maximum drawdown and drawdown duration.
• Calmar ratio = CAGR / Max DD.
• Win rate and profit factor (gross wins / gross losses).
• Expectancy = avg win × win rate − avg loss × loss rate.
• Turnover (annual % of portfolio traded).
• Capacity: how much capital can the strategy absorb before
  performance degrades?

Strategy Decay:
    All alpha sources have a half-life.  Crowding, regime changes,
    and regulatory shifts erode edges over time.  Continuous research
    and adaptation are required.
"""
