"""
ETF Mechanics – Creation, Redemption, and Market Microstructure
===============================================================

The creation/redemption mechanism is the defining innovation of ETFs.
It is what keeps ETF market prices aligned with Net Asset Value (NAV)
and differentiates ETFs from closed-end funds.

═══════════════════════════════════════════════════════════════════════
CREATION / REDEMPTION PROCESS
═══════════════════════════════════════════════════════════════════════

Key Participants:
    • ETF Sponsor / Issuer – Creates and manages the ETF (e.g., BlackRock)
    • Authorized Participants (APs) – Large financial institutions with
      agreements to create/redeem ETF shares directly with the sponsor.
      Typically major banks and market makers (e.g., Jane Street, Citadel
      Securities, Virtu, Goldman Sachs, JPMorgan).
    • Market Makers – Provide liquidity on the exchange by quoting
      bid/ask prices. APs often also serve as market makers.
    • Transfer Agent – Processes creation/redemption orders
    • Custodian – Holds the ETF's underlying securities

The Creation Process (New ETF shares enter the market):
    1. AP assembles a "creation basket" – the specific securities (or cash)
       that match the ETF's portfolio composition
    2. AP delivers the creation basket to the ETF sponsor/custodian
    3. ETF sponsor issues new ETF shares to the AP (in large blocks
       called "creation units," typically 25,000 or 50,000 shares)
    4. AP sells the newly created ETF shares on the exchange to investors
       (or holds them in inventory)

The Redemption Process (ETF shares removed from the market):
    1. AP accumulates ETF shares on the secondary market
    2. AP delivers creation unit blocks of ETF shares to the ETF sponsor
    3. ETF sponsor returns the underlying securities (or cash) to the AP
    4. The redeemed ETF shares are cancelled (destroyed)

    In-Kind vs. Cash Creation/Redemption:
    • In-Kind: Securities delivered/received (tax-efficient, most common
      for equity ETFs). The ETF avoids realizing capital gains.
    • Cash: AP delivers cash instead of securities. Used for:
      - International ETFs (time zone/settlement differences)
      - Fixed-income ETFs (bond illiquidity)
      - Commodity ETFs (don't hold securities)
      - Some actively managed ETFs (to protect strategy)
    • Custom baskets: Post-2019 ETF Rule allows flexible baskets that
      differ from pro-rata portfolio slices

═══════════════════════════════════════════════════════════════════════
ARBITRAGE MECHANISM
═══════════════════════════════════════════════════════════════════════

The creation/redemption mechanism creates an arbitrage loop that keeps
the ETF's market price close to its NAV.

When ETF trades at a PREMIUM (market price > NAV):
    1. AP buys underlying securities in the open market
    2. AP delivers securities to ETF sponsor → receives new ETF shares
    3. AP sells ETF shares on the exchange at the premium price
    4. AP profits from the difference
    5. Selling pressure on ETF + buying pressure on underlyings → price converges

When ETF trades at a DISCOUNT (market price < NAV):
    1. AP buys cheap ETF shares on the exchange
    2. AP redeems ETF shares with sponsor → receives underlying securities
    3. AP sells underlying securities in the open market
    4. AP profits from the difference
    5. Buying pressure on ETF + selling pressure on underlyings → price converges

This process typically keeps premiums/discounts within basis points for
liquid equity ETFs. Less liquid underlyings (bonds, international stocks)
may see wider premiums/discounts.

═══════════════════════════════════════════════════════════════════════
TAX EFFICIENCY
═══════════════════════════════════════════════════════════════════════

ETFs are more tax-efficient than mutual funds due to in-kind redemptions:

    • When investors sell mutual fund shares, the fund may need to sell
      securities → realizes capital gains → distributed to all holders
    • When ETF investors sell, they sell on the exchange (no fund-level
      transaction). AP redemptions use in-kind transfers.
    • In-kind redemptions: ETF delivers low-cost-basis shares to the AP,
      flushing embedded gains out of the fund without triggering taxable
      events for remaining shareholders ("tax loss harvesting in reverse")
    • Result: Many equity ETFs have never distributed a capital gain
      despite decades of operation (SPY being a notable exception due to
      its older Unit Investment Trust structure)

    Exceptions to ETF Tax Efficiency:
    • Bond ETFs (some in-kind, some cash, less tax efficient)
    • International ETFs with cash creations
    • Commodity ETFs structured as limited partnerships (K-1 tax form)
    • Currency ETFs (may generate ordinary income)
    • Actively managed ETFs with high turnover

═══════════════════════════════════════════════════════════════════════
ETF PRICING & TRADING
═══════════════════════════════════════════════════════════════════════

Key Price Measures:
    • Market Price – Real-time trading price on the exchange
    • NAV (Net Asset Value) – Per-share value of underlying holdings,
      calculated at end of day (4:00 PM ET for US ETFs)
    • iNAV / IIV (Intraday Indicative Value) – Estimated NAV updated
      every 15 seconds during trading. Published by exchange.
      Note: Can be stale for international or bond ETFs.
    • Premium/Discount = (Market Price - NAV) / NAV

Trading Costs:
    • Bid-Ask Spread – Primary cost for short-term traders
      - Tight for liquid ETFs (SPY: ~$0.01, or ~0.002%)
      - Wider for less liquid / niche ETFs (1-50+ bps)
    • Commission – Most major brokers now offer commission-free ETF trading
    • Market Impact – Large orders can move the market price
    • Tracking Difference (ongoing) – Deviation from index return

Factors Affecting ETF Spreads:
    • Liquidity of underlying securities
    • ETF's own trading volume (secondary factor; underlying matters more)
    • Number of active market makers
    • Time of day (wider at open, narrower midday)
    • Volatility (spreads widen in volatile markets)
    • Creation/redemption efficiency

Best Practices for ETF Trading:
    • Use limit orders (avoid market orders, especially for less liquid ETFs)
    • Avoid trading in the first and last 15 minutes of the session
    • Check iNAV and premium/discount before trading
    • For large orders, contact the ETF's capital markets desk
    • Be cautious trading during market stress (premiums/discounts can widen)
    • For international ETFs, trade when underlying markets are open

═══════════════════════════════════════════════════════════════════════
ETF LEGAL STRUCTURES
═══════════════════════════════════════════════════════════════════════

US Structures:
    Open-End Fund (Investment Company Act of 1940):
        • Most common structure for modern ETFs
        • Governed by SEC under '40 Act
        • Must diversify (no single security >25% of assets; all positions
          >5% cannot collectively exceed 75% of assets) for "diversified" funds
        • Can reinvest dividends (no cash drag)
        • Flexible creation baskets allowed under Rule 6c-11
        • Can lend securities

    Unit Investment Trust (UIT):
        • Oldest ETF structure (SPY, DIA, QQQ originally)
        • Cannot reinvest dividends (creates cash drag)
        • Must fully replicate the index (no sampling)
        • Cannot lend securities
        • Cannot use derivatives
        • Fixed trust structure; less flexible

    Grantor Trust:
        • Used for physically-backed commodity ETFs (GLD, SLV, IAU)
        • Investors own a fractional interest in the trust's holdings
        • Trust holds the physical commodity
        • Taxed as collectibles (28% max long-term rate for gold/silver)
        • No active management; purely custodial
        • Limited partnership variant used for futures-based products

    Exchange-Traded Note (ETN):
        • Senior unsecured debt obligation of the issuer
        • NOT a fund; does not hold assets
        • Issuer promises to pay the return of a reference index minus fees
        • Carries issuer credit risk (Lehman Brothers ETNs went to zero in 2008)
        • Perfect tracking (no tracking error; return is contractual)
        • Tax treatment can be favorable (may defer capital gains)
        • Must meet SEC registration requirements
        • Market has shrunk significantly due to credit risk concerns

    Commodity Pool (under CFTC):
        • Used for futures-based commodity and volatility ETFs
        • Registered with CFTC and NFA (not primarily SEC)
        • Issues K-1 tax forms (complex for investors)
        • Examples: USO (oil), UNG (natural gas), VXX (VIX)
        • Subject to position limits and CFTC reporting requirements

European Structures:
    UCITS (Undertakings for Collective Investment in Transferable Securities):
        • Dominant ETF structure in Europe
        • Harmonized EU regulatory framework
        • Strict diversification rules (5/10/40 rule)
        • Can be distributed across EU member states (passporting)
        • Can be physical (full replication) or synthetic (swap-based)
        • Most European ETFs are domiciled in Ireland or Luxembourg
          (favorable tax treaty networks)

    Synthetic Replication (Swap-Based):
        • ETF enters into a swap agreement with a counterparty
        • Counterparty promises to deliver the index return
        • ETF holds collateral basket (may differ from index)
        • Counterparty risk managed through overcollateralization
        • Can be "funded" or "unfunded" model
        • Advantages: can replicate indices that are hard to hold
          physically (e.g., emerging markets, commodity)
        • Risks: counterparty default, collateral quality

═══════════════════════════════════════════════════════════════════════
ETF COSTS & FEES
═══════════════════════════════════════════════════════════════════════

Expense Ratio:
    Annual management fee charged as a percentage of AUM.
    Deducted daily from NAV (not billed separately).

    Ranges:
    • Ultra-low-cost core ETFs: 0.00% – 0.05% (Schwab, Vanguard, BlackRock)
    • Broad index ETFs: 0.03% – 0.20%
    • Smart beta / Factor ETFs: 0.10% – 0.50%
    • Actively managed ETFs: 0.20% – 1.00%
    • Thematic / Niche ETFs: 0.40% – 0.85%
    • Leveraged / Inverse ETFs: 0.75% – 1.00%
    • Crypto ETFs: 0.20% – 0.95% (introductory fee waivers common)

    Fee war has compressed costs dramatically. The zero-fee ETF exists
    (SoFi, BNY Mellon offered 0.00% expense ratios to attract assets).

Tracking Difference:
    Actual divergence of ETF return from its benchmark.
    Can be positive (outperform) or negative (underperform).
    Caused by:
    • Expense ratio (largest component)
    • Securities lending income (can offset expenses)
    • Cash drag (uninvested cash)
    • Sampling methodology (not holding all index constituents)
    • Rebalancing costs and timing
    • Tax withholding on foreign dividends
    • Fair value pricing adjustments

Tracking Error:
    Standard deviation of tracking differences over time.
    Measures consistency of tracking.

Securities Lending Revenue:
    ETFs can lend their holdings to short sellers and earn fees.
    Revenue is typically split between the fund and the lending agent.
    Can significantly offset expenses (some ETFs earn more from lending
    than they charge in fees).

Total Cost of Ownership (TCO):
    TCO = Expense Ratio + Trading Costs (spread) + Tracking Difference
    + Tax Drag (for taxable accounts)
"""
