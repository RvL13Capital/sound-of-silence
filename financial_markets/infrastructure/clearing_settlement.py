"""
Clearing, Settlement, and Post-Trade Infrastructure
=====================================================

═══════════════════════════════════════════════════════════════════════
THE TRADE LIFECYCLE
═══════════════════════════════════════════════════════════════════════

    1. Pre-Trade → Order creation, risk checks, routing
    2. Execution → Order matched on exchange or OTC
    3. Clearing  → Trade validated, novated to CCP, margin calculated
    4. Settlement → Actual exchange of securities and cash (delivery vs. payment)
    5. Post-Settlement → Corporate actions, income processing, reconciliation

═══════════════════════════════════════════════════════════════════════
CLEARING (Central Counterparty Clearing – CCP)
═══════════════════════════════════════════════════════════════════════

After a trade is executed, the CCP interposes itself between buyer and
seller through "novation":
    Original: Buyer ↔ Seller
    After:    Buyer ↔ CCP ↔ Seller

The CCP becomes the buyer to every seller and the seller to every buyer,
guaranteeing performance of the trade.

Functions of a CCP:
    • Novation – Assumption of counterparty risk
    • Netting – Offset obligations to reduce settlement volumes
      (multilateral netting can reduce settlement obligations by 95%+)
    • Margin collection – Initial and variation margin
    • Risk management – Position limits, stress testing, default management
    • Default management – Procedures if a clearing member fails

Major CCPs:
    Equities:
    • NSCC (National Securities Clearing Corporation) – US equities
      (subsidiary of DTCC)
    • Euroclear / Clearstream – European securities
    • LCH EquityClear – European equities

    Derivatives:
    • OCC (Options Clearing Corporation) – US equity options
    • CME Clearing – CME Group derivatives
    • ICE Clear US / ICE Clear Europe – ICE products
    • LCH SwapClear – Largest IRS clearing (>$350 trillion notional)
    • Eurex Clearing – European derivatives
    • JSCC – Japanese derivatives and JGB clearing

    Fixed Income:
    • FICC (Fixed Income Clearing Corporation) – US Treasuries, MBS, repos
      (subsidiary of DTCC)

CCP Margin System:
    Initial Margin (IM):
    • Collateral deposited upfront to cover potential losses
    • Calculated using models: SPAN, PRISMA, VaR-based
    • Typically covers 99%+ of potential 1-5 day price moves
    • Can increase dramatically during volatility (procyclical risk)

    Variation Margin (VM):
    • Daily (or intraday) cash flows reflecting mark-to-market gains/losses
    • Losing positions pay; winning positions receive
    • Ensures losses don't accumulate

    Additional Margin:
    • Concentration charges (large positions)
    • Liquidity charges (hard-to-liquidate portfolios)
    • Wrong-way risk charges
    • Discretionary add-ons during stress

CCP Default Waterfall:
    If a clearing member defaults, losses absorbed sequentially:
    1. Defaulter's initial margin
    2. Defaulter's default fund contribution
    3. CCP's own capital (skin-in-the-game, typically small)
    4. Non-defaulting members' default fund contributions
    5. CCP's additional capital / assessment rights
    6. Recovery tools (variation margin haircutting, partial tear-up)
    7. Resolution (if CCP itself fails – regulatory resolution authority)

    G20 reforms post-2008 mandated centralized clearing for standardized
    OTC derivatives (primarily interest rate swaps and CDS indices).

CCP Risk Concerns:
    • "Too big to fail" concentration of risk
    • Procyclicality (margin increases during crises exacerbate stress)
    • Interconnectedness (members belong to multiple CCPs)
    • CCP-to-CCP risk (limited but growing)
    • Operational risk (cyber attacks, system failures)
    • Adequacy of loss-absorbing resources under extreme scenarios

═══════════════════════════════════════════════════════════════════════
SETTLEMENT
═══════════════════════════════════════════════════════════════════════

Settlement is the actual transfer of securities from seller to buyer
and cash from buyer to seller.

Settlement Cycles:
    • T+0 (same day): Some government bond repos, crypto
    • T+1 (trade date + 1 day): US equities (since May 2024), Canada, Mexico
    • T+2 (trade date + 2 days): Most of Europe, Asia-Pacific (transitioning)
    • T+3: Historical US standard (until 2017)

    Benefits of shorter settlement:
    • Reduced counterparty risk (less time for defaults)
    • Lower margin requirements
    • Reduced operational risk

    Challenges:
    • FX funding for cross-border trades (CLS settlement)
    • Securities lending recall timing
    • Affirmation and allocation processes must be faster
    • Different time zones complicate cross-border settlement

Delivery vs. Payment (DvP):
    Simultaneous exchange of securities and cash, eliminating principal risk.
    Three models:
    • DvP Model 1: Gross securities, gross cash (instruction by instruction)
    • DvP Model 2: Gross securities, net cash
    • DvP Model 3: Net securities, net cash (most efficient)

Central Securities Depositories (CSDs):
    Institutions that hold securities in dematerialized (book-entry) form
    and facilitate settlement.

    Major CSDs:
    • DTCC / DTC (Depository Trust Company) – US securities
    • Euroclear – International/European CSD (Brussels)
    • Clearstream – International/European CSD (Luxembourg, Deutsche Börse)
    • CREST (now part of Euroclear) – UK/Irish securities
    • JASDEC – Japan
    • CDS Clearing (now CDCC) – Canada
    • CCDC / SHCH – China

DTCC (Depository Trust & Clearing Corporation):
    The backbone of US capital markets post-trade infrastructure.
    • DTC – Custody and settlement of US securities
    • NSCC – Equity clearing and netting
    • FICC – Treasury, agency, and MBS clearing
    • Processes ~$2.5+ quadrillion in securities transactions annually
    • Holds ~$87+ trillion in securities in custody
    • Industry-owned (by its member banks, broker-dealers)

═══════════════════════════════════════════════════════════════════════
SECURITIES LENDING
═══════════════════════════════════════════════════════════════════════

The temporary transfer of securities from a lender to a borrower in
exchange for collateral and a lending fee.

Why Borrow Securities?
    • Short selling (must deliver borrowed shares)
    • Settlement fails (borrow to make delivery)
    • Hedging and market making
    • Collateral transformation (swap lower-quality collateral for
      high-quality securities)

Market Size:
    • ~$30+ trillion in securities available to lend globally
    • ~$3+ trillion on loan at any given time

Key Participants:
    • Lenders: Pension funds, mutual funds, ETFs, sovereign wealth funds,
      insurance companies (beneficial owners)
    • Borrowers: Hedge funds, proprietary trading firms, broker-dealers
    • Intermediaries: Agent lenders (custody banks: BNY Mellon, State Street,
      JPMorgan), prime brokers

Economics:
    • General collateral (GC): Easy-to-borrow securities, low fees (5-25 bps)
    • Specials: Hard-to-borrow securities, higher fees (1-50%+ annualized)
    • Collateral: Cash or non-cash (Treasuries, letters of credit)
    • Cash collateral reinvested for additional return

Risks:
    • Counterparty default (borrower fails to return securities)
    • Collateral reinvestment risk (cash collateral losses)
    • Recall risk (lender recalls securities during high demand)
    • Operational risk

═══════════════════════════════════════════════════════════════════════
TRADE REPORTING & TRANSPARENCY
═══════════════════════════════════════════════════════════════════════

US:
    • TRACE – Post-trade reporting for corporate and agency bonds (FINRA)
    • EMMA – Municipal bond transparency (MSRB)
    • CAT (Consolidated Audit Trail) – Comprehensive equity/options trade
      tracking system (SEC/FINRA)
    • Form 13F – Quarterly institutional holdings reports (>$100M AUM)
    • Swap Data Repositories (SDRs) – OTC derivative trade reporting
      (ICE Trade Vault, DTCC Data Repository, CME SDR)

Europe:
    • MiFID II/MiFIR transaction reporting – Comprehensive trade reporting
    • EMIR trade reporting – OTC derivatives to trade repositories
    • SFTR – Securities Financing Transactions Regulation (repo reporting)
    • Pre- and post-trade transparency requirements for all asset classes

═══════════════════════════════════════════════════════════════════════
EMERGING INFRASTRUCTURE: BLOCKCHAIN / DLT
═══════════════════════════════════════════════════════════════════════

Distributed Ledger Technology (DLT) for financial market infrastructure:

Potential Benefits:
    • Atomic settlement (DvP in real-time, T+0)
    • Shared golden source of truth (reduced reconciliation)
    • 24/7 operation
    • Programmable securities (smart contracts for corporate actions)
    • Fractional ownership of traditionally illiquid assets

Current Initiatives:
    • DTCC Digital Securities Management (DSM)
    • HQLAx – Blockchain-based collateral management
    • JPMorgan Onyx – Digital assets and payments
    • Canton Network – Institutional blockchain (Digital Asset)
    • Singapore's Project Guardian – Tokenized assets
    • SIX Digital Exchange (SDX) – Fully regulated DLT-based exchange
    • ASX CHESS replacement (attempted, then cancelled; lessons learned)
    • European Central Bank – DLT settlement trials

Challenges:
    • Regulatory uncertainty
    • Interoperability between DLT and legacy systems
    • Scalability and performance
    • Legal frameworks for digital securities
    • Privacy vs. transparency trade-offs
    • Industry coordination and standards
"""
