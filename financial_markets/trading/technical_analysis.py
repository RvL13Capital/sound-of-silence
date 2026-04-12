"""
Technical Analysis – Indicators, Chart Patterns, and Volume Analysis
====================================================================

Technical analysis is the study of past market data — primarily price
and volume — to identify patterns and forecast future price movements.
It rests on three axioms: price discounts everything, prices move in
trends, and history tends to repeat itself.

FOUNDATIONS
──────────
Dow Theory (Charles Dow, late 1800s):
    • The market has three trends: primary (months–years), secondary
      (weeks–months), and minor (days–weeks).
    • Trends persist until a definitive reversal signal appears.
    • Volume must confirm the trend.
    • The industrials and transports must confirm each other.

Efficient Market Hypothesis (EMH) debate:
    • Weak-form EMH: Past prices contain no predictive information.
      Technical analysis should not work.
    • Practitioners argue: markets are not perfectly efficient at all
      times, especially in less-covered or less-liquid names.  Behavioral
      biases (anchoring, herding, disposition effect) create exploitable
      patterns.  The Hong-Stein (1999) model provides a theoretical
      framework for why trend-following works in low-coverage stocks.

CHART TYPES
───────────
• Candlestick – Body (open→close) + wicks (high/low).  Japanese origin.
  Most widely used chart type for technical analysis.
• Bar chart (OHLC) – Vertical line (low→high), left tick (open),
  right tick (close).
• Line chart – Closing prices connected.  Simple trend identification.
• Point-and-Figure – Columns of X (rising) and O (falling), ignores
  time, focuses on price reversals of a fixed box size.
• Renko – Bricks of fixed size; new brick only when price moves by
  the brick amount.  Filters noise.
• Heikin-Ashi – Modified candlesticks using averaged OHLC values.
  Smooths trends, easier to read trend direction.
• Kagi – Vertical lines that reverse direction when price moves by a
  specified amount.  Originated in Japan.

TREND ANALYSIS
──────────────
Support and Resistance:
    • Support: price level where buying pressure consistently exceeds
      selling pressure (price "bounces").
    • Resistance: price level where selling pressure exceeds buying
      pressure (price "reverses").
    • Broken resistance becomes support and vice versa (polarity).
    • Strength increases with number of touches and volume at the level.

Trendlines and Channels:
    • Uptrend line: drawn along rising lows (support).
    • Downtrend line: drawn along falling highs (resistance).
    • Channel: parallel lines encompassing price action.
    • Steeper trendlines break more easily; shallow trends are more
      sustainable.

Moving Averages:
    • Simple Moving Average (SMA): arithmetic mean of last N closes.
    • Exponential Moving Average (EMA): weights recent prices more
      heavily; reacts faster to new data.
    • Weighted Moving Average (WMA): linear weighting (most recent
      highest).
    • Double EMA (DEMA) / Triple EMA (TEMA): reduce lag further.
    • Hull Moving Average (HMA): uses WMA of WMA to reduce lag while
      maintaining smoothness.

    Key periods:
    • 50-day SMA – intermediate-term trend
    • 150-day SMA – Minervini trend template component
    • 200-day SMA – long-term trend, institutional benchmark
    • 30-week SMA (≈150-day) – Weinstein Stage Analysis

    Crossovers:
    • Golden Cross: 50-day SMA crosses above 200-day SMA (bullish).
    • Death Cross: 50-day SMA crosses below 200-day SMA (bearish).
    • Reliability: works best in trending markets; produces whipsaws
      in ranges.

Average Directional Index (ADX):
    • Measures trend strength (not direction), scale 0–100.
    • ADX > 25: strong trend.  ADX < 20: weak/no trend.
    • +DI / -DI: directional indicators (bullish/bearish pressure).
    • Developed by Welles Wilder (1978).

CHART PATTERNS
──────────────
Reversal Patterns:
    • Head and Shoulders: left shoulder, head (higher high), right
      shoulder.  Neckline break confirms reversal.  Inverse H&S is
      bullish.  Most statistically studied pattern.
    • Double Top / Double Bottom: two peaks/troughs at similar level.
      Break of the intervening low/high confirms.
    • Triple Top / Triple Bottom: three tests of a level.
    • Rounding Bottom (Saucer): gradual shift from selling to buying.
    • Wedge (Rising/Falling): converging trendlines with both sloping
      in the same direction.  Rising wedge is bearish; falling wedge
      is bullish.

Continuation Patterns:
    • Flag: small rectangle sloping against the prior trend.
    • Pennant: small symmetrical triangle after a sharp move.
    • Rectangle: horizontal consolidation between support/resistance.
    • Cup and Handle: U-shaped cup followed by a small downward drift
      (handle), then breakout.  William O'Neil pattern.
    • Triangles: ascending (flat top, rising bottom), descending
      (flat bottom, falling top), symmetric (converging).

Candlestick Patterns:
    Single-candle:
    • Doji – Open ≈ Close, indecision.
    • Hammer – Small body at top, long lower wick (bullish reversal
      after downtrend).
    • Inverted Hammer – Small body at bottom, long upper wick.
    • Shooting Star – Hammer shape at top of uptrend (bearish).
    • Spinning Top – Small body, wicks on both sides (indecision).

    Multi-candle:
    • Engulfing (bullish/bearish) – Second candle's body fully engulfs
      the first.
    • Morning Star – Three-candle bullish reversal (down, small body,
      up).
    • Evening Star – Three-candle bearish reversal (up, small body,
      down).
    • Harami – Small body contained within prior candle's body.
    • Three White Soldiers – Three consecutive large up-candles
      (strong bullish).
    • Three Black Crows – Three consecutive large down-candles
      (strong bearish).
    • Piercing Line / Dark Cloud Cover – Partial engulfing patterns.

MOMENTUM INDICATORS
───────────────────
Relative Strength Index (RSI):
    • RSI = 100 − 100 / (1 + RS), where RS = avg gain / avg loss
      over N periods (typically 14).
    • Overbought: RSI > 70.  Oversold: RSI < 30.
    • Divergence: price makes new high but RSI doesn't → potential
      reversal.
    • Developed by Welles Wilder (1978).

Stochastic Oscillator:
    • %K = (Close − Low_N) / (High_N − Low_N) × 100 (typically N=14).
    • %D = SMA(%K, 3).  Signal line.
    • Overbought: > 80.  Oversold: < 20.
    • Crossovers of %K and %D generate signals.

MACD (Moving Average Convergence Divergence):
    • MACD Line = EMA(12) − EMA(26).
    • Signal Line = EMA(9) of MACD Line.
    • Histogram = MACD − Signal.
    • Crossovers, zero-line crossings, and divergences are signals.
    • Developed by Gerald Appel (1979).

Williams %R:
    • Similar to stochastic, scale −100 to 0.
    • %R = (Highest_N − Close) / (Highest_N − Lowest_N) × (−100).
    • Overbought: > −20.  Oversold: < −80.

Rate of Change (ROC):
    • ROC = (Close − Close_N) / Close_N × 100.
    • Measures percentage change over N periods.
    • Simple momentum measure.

Commodity Channel Index (CCI):
    • CCI = (Typical Price − SMA) / (0.015 × Mean Deviation).
    • Developed by Donald Lambert.  +100/−100 thresholds.

Money Flow Index (MFI):
    • Volume-weighted RSI.  Incorporates both price and volume.
    • Overbought > 80, oversold < 20.

VOLATILITY INDICATORS
─────────────────────
Bollinger Bands (John Bollinger):
    • Middle band = SMA(20).
    • Upper band = SMA(20) + 2 × StdDev(20).
    • Lower band = SMA(20) − 2 × StdDev(20).
    • Band squeeze (narrowing) signals low volatility → potential
      breakout.  This is the basis of the Volatility Contraction
      Pattern (Minervini).
    • ~95% of price action falls within the bands.

Average True Range (ATR):
    • ATR = SMA of True Range over N periods (typically 14).
    • True Range = max(High−Low, |High−PrevClose|, |Low−PrevClose|).
    • Measures volatility in absolute price terms.
    • Used for stop-loss placement, position sizing, and breakout
      confirmation.

Keltner Channels:
    • Similar to Bollinger Bands but uses ATR instead of standard
      deviation.
    • Middle = EMA(20).  Upper/Lower = EMA ± 2 × ATR.
    • Squeeze: Bollinger Bands inside Keltner Channels = very low vol.

Donchian Channels:
    • Upper = highest high over N periods.
    • Lower = lowest low over N periods.
    • Breakout above upper channel = buy signal (turtle trading).
    • Developed by Richard Donchian (1960s).

VOLUME ANALYSIS
───────────────
On-Balance Volume (OBV):
    • Cumulative: add volume on up days, subtract on down days.
    • Divergence between OBV trend and price trend signals potential
      reversal.  Developed by Joe Granville (1963).

Volume-Weighted Average Price (VWAP):
    • VWAP = Σ(Price × Volume) / Σ(Volume) over a session.
    • Institutional benchmark for execution quality.
    • Price above VWAP = bullish; below = bearish intraday.

Accumulation/Distribution Line:
    • Weights volume by where the close falls within the day's range.
    • CLV = [(Close − Low) − (High − Close)] / (High − Low).
    • A/D = Σ(CLV × Volume).

Chaikin Money Flow (CMF):
    • Sum of A/D values over N periods / sum of volume over N periods.
    • Positive = accumulation; negative = distribution.

Volume Profile / Market Profile:
    • Horizontal histogram showing volume traded at each price level.
    • Point of Control (POC): price with highest volume.
    • Value Area: price range containing 70% of volume.
    • Identifies support/resistance from volume, not just price.

FIBONACCI ANALYSIS
──────────────────
Based on the Fibonacci sequence (1, 1, 2, 3, 5, 8, 13, 21, 34…) and
the golden ratio (≈ 1.618, φ).

    Retracement Levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
    • Measure how far a pullback retraces the prior move.
    • 61.8% and 38.2% are the most commonly watched levels.

    Extension Levels: 127.2%, 161.8%, 261.8%
    • Project targets beyond the prior high/low.

    Fibonacci Fans, Arcs, Time Zones: Less commonly used variants
    applying Fibonacci ratios to angles, curves, and time intervals.

ELLIOTT WAVE THEORY
───────────────────
Developed by Ralph Nelson Elliott (1930s).  Markets move in
recognisable wave patterns driven by investor psychology.

    Impulse Waves (5 waves in the direction of the trend):
    Wave 1: Initial move up.
    Wave 2: Pullback (does not retrace beyond Wave 1 start).
    Wave 3: Strongest and longest wave (typically 1.618× Wave 1).
    Wave 4: Corrective pullback (does not overlap Wave 1 territory).
    Wave 5: Final push (often with divergence on momentum indicators).

    Corrective Waves (3 waves against the trend): A-B-C.
    Multiple correction forms: zigzags, flats, triangles, combinations.

    Waves nest within larger waves (fractal structure).
    Wave degrees: Grand Supercycle down to Subminuette.

    Criticism: highly subjective wave counting; multiple valid
    interpretations at any point in time.  Rarely used in systematic
    trading due to ambiguity.

ICHIMOKU CLOUD (Ichimoku Kinko Hyo)
─────────────────────────────────────
Japanese charting system developed by Goichi Hosoda (1960s).
Five components:

    Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2.
    Kijun-sen (Base Line): (26-period high + 26-period low) / 2.
    Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, plotted 26
      periods ahead.
    Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2,
      plotted 26 periods ahead.
    Chikou Span (Lagging Span): Current close plotted 26 periods behind.

    The "cloud" (kumo) is the area between Senkou Span A and B.
    • Price above cloud = bullish.  Below = bearish.  Inside = neutral.
    • Cloud colour (A > B vs B > A) indicates trend direction.
    • Tenkan-Kijun crossovers generate trade signals.
    • Cloud thickness represents support/resistance strength.

MARKET BREADTH INDICATORS
──────────────────────────
Advance/Decline Line:
    • Cumulative: advances minus declines each day.
    • Divergence from index = weakening internal market structure.

McClellan Oscillator:
    • Difference between 19-day and 39-day EMA of daily advances
      minus declines.
    • Measures momentum of market breadth.

New Highs vs. New Lows:
    • Net new highs = new 52-week highs minus new 52-week lows.
    • Falling new highs during rising index = bearish divergence.

Arms Index (TRIN):
    • TRIN = (Advancing Issues / Declining Issues) /
      (Advancing Volume / Declining Volume).
    • TRIN < 1.0 = bullish (more volume in advancing stocks).
    • TRIN > 1.0 = bearish.

Percentage of Stocks Above Moving Average:
    • % of index members above their 50-day or 200-day SMA.
    • <20% = oversold market.  >80% = overbought.

INTERMARKET ANALYSIS
────────────────────
Asset class relationships that provide context:
    • Bond prices ↑ → yields ↓ → often precedes equity weakness
      (flight to safety) or supports rate-sensitive sectors.
    • Strong USD typically pressures EM equities and commodities.
    • Copper/gold ratio: rising = growth expectations; falling = fear.
    • Commodity prices and inflation-linked equities tend to correlate.
    • VIX (equity fear gauge) spikes during equity sell-offs;
      persistently high VIX = ongoing uncertainty.

LIMITATIONS AND CRITICISMS
───────────────────────────
• Academic scepticism: weak-form EMH suggests past prices carry no
  predictive information beyond what's in the current price.
• Survivorship bias in pattern studies: patterns that "worked" are
  published; those that didn't are forgotten.
• Curve fitting / data mining: with enough parameters, any historical
  data can be fit.  Out-of-sample validation is essential.
• Confirmation bias: traders see patterns they're looking for.
• Self-fulfilling prophecy argument: some patterns work because
  enough participants believe in them (support at round numbers,
  Fibonacci levels).
• In highly efficient, well-covered markets (US large-cap),
  technical edge is largely arbitraged.  Works better in less
  efficient markets (small-caps, emerging markets, crypto).
"""
