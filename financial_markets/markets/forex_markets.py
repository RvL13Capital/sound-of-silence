"""
Foreign Exchange (FX / Forex) Markets
======================================

The foreign exchange market is the largest and most liquid financial market
in the world. It operates 24 hours a day, 5.5 days a week, across global
time zones.

MARKET SIZE & SCOPE (BIS Triennial Survey)
───────────────────────────────────────────
• Daily turnover: ~$7.5+ trillion (2022 BIS survey)
• Primarily OTC (over-the-counter), decentralized
• No single physical exchange; electronic interbank network
• Spot transactions: ~$2.1 trillion/day
• FX swaps: ~$3.8 trillion/day
• Outright forwards: ~$0.5 trillion/day
• FX options: ~$0.3 trillion/day

CURRENCY PAIRS
──────────────
Notation: BASE/QUOTE (e.g., EUR/USD = 1.10 means 1 EUR = 1.10 USD)

Major Pairs (most liquid, tightest spreads):
    • EUR/USD  – "Euro" (most traded pair globally, ~23% of volume)
    • USD/JPY  – "Dollar Yen" or "Gopher"
    • GBP/USD  – "Cable" (named after transatlantic telegraph cable)
    • USD/CHF  – "Swissy"
    • AUD/USD  – "Aussie"
    • USD/CAD  – "Loonie" (after the loon on the Canadian dollar coin)
    • NZD/USD  – "Kiwi"

Cross Pairs (no USD involvement):
    • EUR/GBP, EUR/JPY, GBP/JPY, EUR/CHF, AUD/NZD, etc.

Emerging Market Pairs:
    • USD/CNH (offshore Chinese yuan), USD/MXN, USD/BRL, USD/ZAR,
      USD/TRY, USD/INR, USD/KRW, USD/THB, etc.

RESERVE CURRENCIES
──────────────────
• USD – Dominant reserve currency (~58% of global reserves)
• EUR – Second (~20%)
• JPY – Third (~5.5%)
• GBP – Fourth (~5%)
• CNY – Growing but still small (~2.5%)
• Others: AUD, CAD, CHF, etc.

FX MARKET STRUCTURE
───────────────────
Participants (layered market):
    1. Interbank Market (Tier 1) – Major global banks trade directly
       (Citi, JPMorgan, UBS, Deutsche Bank, HSBC are top dealers)
    2. Institutional Clients – Asset managers, hedge funds, corporates,
       sovereign wealth funds, central banks
    3. Retail FX – Individual traders via retail brokers
    4. Electronic Communication Networks (ECNs) – e.g., EBS, Reuters
       Matching, Currenex, Hotspot, FXall
    5. Prime Brokerage – Enables non-bank participants to trade on
       bank credit via a prime broker

Trading Sessions (overlap drives highest volume):
    • Sydney:   5:00 PM – 2:00 AM ET
    • Tokyo:    7:00 PM – 4:00 AM ET
    • London:   3:00 AM – 12:00 PM ET
    • New York: 8:00 AM – 5:00 PM ET
    • London-New York overlap (8 AM – 12 PM ET) = peak liquidity

FX INSTRUMENTS
──────────────
Spot:
    Immediate exchange of currencies (settlement T+2 for most pairs,
    T+1 for USD/CAD, T+0 for some).

Forward:
    Agreement to exchange currencies at a future date at a pre-agreed rate.
    The forward rate differs from spot by the "forward points," which
    reflect the interest rate differential between the two currencies
    (covered interest rate parity).

    Forward rate = Spot × (1 + r_quote × t) / (1 + r_base × t)

FX Swap:
    Simultaneous spot purchase and forward sale (or vice versa) of a
    currency. Used for funding and rolling positions. The most traded
    FX instrument by volume.

Currency Swap (Cross-Currency Swap):
    Exchange of principal and interest payments in different currencies
    over a longer term. Unlike an FX swap, involves periodic interest
    exchanges and exchange of principal at both start and end.

FX Options:
    Right (not obligation) to buy or sell a currency pair at a strike price.
    • Vanilla options: European (exercise at expiry) or American (any time)
    • Exotic options:
      - Barrier options (knock-in, knock-out)
      - Digital / Binary options (fixed payout if condition met)
      - Asian options (payoff based on average rate)
      - Basket options (based on a group of currencies)
    • Risk reversals: Long call + short put (or vice versa) at different strikes
    • Straddle: Long call + long put at same strike (bet on volatility)
    • Strangle: Long call + long put at different strikes

Non-Deliverable Forwards (NDFs):
    Forward contracts settled in USD (or other freely traded currency)
    rather than physical delivery of the restricted currency.
    Used for currencies with capital controls (CNY, INR, KRW, BRL, TWD, etc.).

KEY FX CONCEPTS
───────────────
Bid/Ask Spread:
    Bid = price dealer will buy base currency
    Ask = price dealer will sell base currency
    Spread = ask – bid (tighter = more liquid)
    Majors: 0.1–1 pip; EM pairs: 3–50+ pips

Pip:
    Smallest standard price movement. For most pairs, 1 pip = 0.0001
    (4th decimal place). For JPY pairs, 1 pip = 0.01 (2nd decimal).

Lot Sizes:
    Standard lot = 100,000 units of base currency
    Mini lot = 10,000; Micro lot = 1,000; Nano lot = 100

Leverage:
    FX markets offer high leverage. Retail: 50:1 (US), up to 30:1 (EU),
    up to 500:1 (some offshore). Institutional: much higher effective leverage.

Carry Trade:
    Borrow in low-interest-rate currency, invest in high-interest-rate
    currency. Profit = interest rate differential minus any adverse FX movement.
    Risk: sudden unwinding during risk-off events (e.g., JPY carry trade).

Purchasing Power Parity (PPP):
    Long-term FX theory: exchange rates should adjust so that identical
    goods cost the same in different countries.
    Big Mac Index: informal PPP measure published by The Economist.

Interest Rate Parity:
    • Covered Interest Rate Parity (CIP): Forward premium/discount equals
      the interest rate differential (arbitrage-free condition)
    • Uncovered Interest Rate Parity (UIP): Expected spot rate change
      equals the interest rate differential (often violated in practice)

CENTRAL BANK INFLUENCE
──────────────────────
Central banks are the most powerful FX market participants:
    • Monetary policy (interest rate decisions) directly impacts currency value
    • FX intervention: Direct buying/selling of currencies to influence rates
    • Foreign exchange reserves management
    • Forward guidance and verbal intervention ("jawboning")
    • Capital controls and macroprudential policies

Major Central Banks:
    • Federal Reserve (Fed) – USD
    • European Central Bank (ECB) – EUR
    • Bank of Japan (BoJ) – JPY
    • Bank of England (BoE) – GBP
    • Swiss National Bank (SNB) – CHF (known for active intervention)
    • People's Bank of China (PBoC) – CNY (managed float regime)
    • Reserve Bank of Australia (RBA) – AUD
    • Bank of Canada (BoC) – CAD

EXCHANGE RATE REGIMES
─────────────────────
• Free-floating – Market-determined (USD, EUR, GBP, JPY, AUD, CAD)
• Managed float – Authorities intervene to smooth fluctuations (INR, SGD)
• Crawling peg – Fixed rate adjusted gradually (historical examples)
• Fixed peg – Pegged to another currency (HKD pegged to USD; DKK pegged to EUR)
• Currency board – Domestic currency fully backed by foreign reserves
  (Hong Kong, Bulgaria)
• Dollarization – Country uses foreign currency (Ecuador, El Salvador use USD)
• Currency union – Shared currency (Eurozone, CFA franc zones)
"""
