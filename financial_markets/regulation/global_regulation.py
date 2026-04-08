"""
Global Financial Market Regulation
===================================

═══════════════════════════════════════════════════════════════════════
EUROPEAN UNION REGULATION
═══════════════════════════════════════════════════════════════════════

MiFID II / MiFIR (Markets in Financial Instruments Directive/Regulation):
    Comprehensive European financial market regulation (effective 2018).

    Key Provisions:
    • Market structure:
      - Regulated Markets (RMs), Multilateral Trading Facilities (MTFs),
        Organized Trading Facilities (OTFs), Systematic Internalisers (SIs)
      - Mandatory trading on-venue for shares and derivatives
      - Double volume caps on dark pool trading (4% per venue, 8% total)
    • Transparency:
      - Pre-trade transparency for equities and non-equities
      - Post-trade transparency requirements
      - Transaction reporting to regulators (65+ data fields)
    • Best execution: Enhanced requirements and reporting (RTS 28)
    • Research unbundling: Research payments separated from execution
      (dramatically changed sell-side research economics)
    • Investor protection:
      - Product governance requirements
      - Appropriateness and suitability assessments
      - Cost and charges disclosure
      - Product intervention powers for ESMA and NCAs
    • Algorithmic trading regulation:
      - Algo registration and testing requirements
      - HFT-specific rules (tick sizes, market-making obligations)
      - Kill switch requirements
    • Position limits for commodity derivatives
    • Consolidated tape (still being implemented)

EMIR (European Market Infrastructure Regulation):
    EU equivalent of Dodd-Frank Title VII for derivatives:
    • Central clearing obligation for standardized OTC derivatives
    • Reporting of all derivatives to trade repositories
    • Risk mitigation for non-centrally cleared derivatives
      (bilateral margin, portfolio reconciliation, dispute resolution)
    • EMIR Refit (2019) simplified requirements for smaller counterparties

UCITS (Undertakings for Collective Investment in Transferable Securities):
    Harmonized EU fund regulation:
    • UCITS V and VI – Current framework
    • Passporting: UCITS fund authorized in one EU state can be
      distributed across all EU member states
    • Diversification: 5/10/40 rule (max 5% per issuer normally;
      can go to 10% for up to 40% of portfolio)
    • Leverage limits: Limited use of derivatives (commitment approach)
    • Custodian/depositary requirements
    • KIID (Key Investor Information Document) → replaced by KID under PRIIPs
    • ~$14+ trillion in UCITS assets

AIFMD (Alternative Investment Fund Managers Directive):
    Regulates non-UCITS fund managers:
    • Hedge funds, PE funds, real estate funds, other alternatives
    • Reporting and transparency requirements
    • Remuneration rules for managers
    • Depositary requirements
    • Marketing passport within EU
    • Leverage monitoring and systemic risk reporting

PRIIPs Regulation:
    Key Information Documents (KIDs) for packaged retail investment
    and insurance-based investment products:
    • Standardized 3-page disclosure document
    • Risk indicator (1-7 scale)
    • Performance scenarios
    • Cost disclosure
    • Applies to: structured products, ETFs, funds, insurance products

SFDR (Sustainable Finance Disclosure Regulation):
    ESG disclosure requirements for financial products:
    • Article 6: No specific ESG integration
    • Article 8: Promotes environmental/social characteristics ("light green")
    • Article 9: Sustainable investment objective ("dark green")
    • Principal Adverse Impacts (PAI) reporting
    • Part of EU's sustainable finance framework (EU Taxonomy, CSRD)

EU Taxonomy:
    Classification system for environmentally sustainable activities:
    • Six environmental objectives (climate mitigation, adaptation, water,
      circular economy, pollution, biodiversity)
    • Technical screening criteria for each activity
    • Do No Significant Harm (DNSH) principle
    • Minimum social safeguards

CSRD (Corporate Sustainability Reporting Directive):
    Enhanced non-financial reporting for EU companies:
    • European Sustainability Reporting Standards (ESRS)
    • Double materiality (financial + impact materiality)
    • Phased implementation starting 2024-2026
    • Applies to large companies, listed SMEs

Bank Resolution (BRRD):
    EU framework for bank resolution:
    • Bail-in tool (convert creditors' claims to equity)
    • MREL (Minimum Requirement for Own Funds and Eligible Liabilities)
    • Single Resolution Mechanism (SRM) for Banking Union countries
    • Single Resolution Fund (SRF)

═══════════════════════════════════════════════════════════════════════
UK REGULATION (Post-Brexit)
═══════════════════════════════════════════════════════════════════════

    • FCA (Financial Conduct Authority) – Conduct regulation
    • PRA (Prudential Regulation Authority, Bank of England) – Prudential
    • UK retained EU law but diverging (UK MiFID, UK EMIR, UK PRIIPs)
    • Edinburgh Reforms (2022) – Package of deregulatory measures
    • Wholesale Markets Review – Simplifying UK market regulation
    • Consumer Duty (2023) – New consumer protection standard
    • UK Listing Rules reform – Making London more competitive for IPOs

═══════════════════════════════════════════════════════════════════════
ASIAN REGULATION
═══════════════════════════════════════════════════════════════════════

Japan (JFSA / FSA):
    • Financial Instruments and Exchange Act (FIEA)
    • Corporate Governance Code and Stewardship Code
    • TSE market restructure (2022): Prime, Standard, Growth segments
    • Increasing focus on shareholder activism and corporate reform

China (CSRC / PBoC / CBIRC):
    • QFII / RQFII: Programs for foreign investment in A-shares
    • Stock Connect (Shanghai-Hong Kong, Shenzhen-Hong Kong)
    • Bond Connect: Access to Chinese interbank bond market
    • A-share inclusion in MSCI indices (partial, with inclusion factors)
    • Capital controls and FX management
    • STAR Market (SSE) – China's Nasdaq-equivalent, registration-based IPO
    • Common Prosperity policies affecting tech/education/real estate sectors
    • Evolving regulatory framework with periodic market interventions

Hong Kong (SFC):
    • Dual regulator: SFC (securities) + HKMA (banking/monetary)
    • Gateway to mainland China via Stock/Bond Connect
    • Listing rules (dual-class shares permitted since 2018)
    • Virtual asset service provider (VASP) licensing regime

Singapore (MAS):
    • Single integrated regulator (central bank + financial regulator)
    • Securities and Futures Act
    • Progressive approach to fintech and digital assets
    • Payment Services Act (crypto regulation)
    • Variable Capital Company (VCC) framework for funds

India (SEBI):
    • Securities and Exchange Board of India
    • FPI (Foreign Portfolio Investor) framework
    • Strict derivative regulations (limited single-stock futures access)
    • Mutual fund regulation (direct plans vs. regular plans)
    • Growing equity culture; massive retail participation growth
    • UPI-based instant settlement initiatives

Australia (ASIC):
    • Corporations Act 2001
    • Market integrity rules
    • Design and distribution obligations (DDO) for financial products
    • CHESS replacement project (ASX settlement infrastructure)

═══════════════════════════════════════════════════════════════════════
INTERNATIONAL REGULATORY COORDINATION
═══════════════════════════════════════════════════════════════════════

Financial Stability Board (FSB):
    • G20 body coordinating international financial regulation
    • Monitors systemic risk
    • Coordinates reform implementation
    • Designates Global Systemically Important Banks (G-SIBs) and
      Insurers (G-SIIs)
    • Crypto-asset regulatory framework recommendations

Basel Committee on Banking Supervision (BCBS):
    • Sets global banking standards (Basel III)
    • Hosted by BIS in Basel, Switzerland
    • Members: Central banks and regulators from 28 jurisdictions

IOSCO (International Organization of Securities Commissions):
    • Sets standards for securities regulation
    • 130+ member jurisdictions
    • Principles for financial benchmarks (post-LIBOR scandal)
    • MMoU (Multilateral Memorandum of Understanding) for enforcement cooperation
    • Standards for ETFs, HFT, dark pools, CRAs

CPMI-IOSCO:
    • Standards for financial market infrastructures (PFMI)
    • 24 principles covering CCPs, CSDs, trade repositories, payment systems

FATF (Financial Action Task Force):
    • Global AML/CFT (combating the financing of terrorism) standards
    • 40 Recommendations
    • Grey list / black list for non-compliant jurisdictions
    • Travel Rule for crypto (VASP-to-VASP information sharing)
    • Mutual evaluations of member jurisdictions

═══════════════════════════════════════════════════════════════════════
CRYPTO / DIGITAL ASSET REGULATION
═══════════════════════════════════════════════════════════════════════

US Approach:
    • SEC: Securities-based approach (Howey test); enforcement actions
    • CFTC: Regulates crypto derivatives; considers Bitcoin a commodity
    • No comprehensive federal crypto legislation yet (multiple proposals)
    • State-level: New York BitLicense, Wyoming DAO/digital asset laws
    • Spot Bitcoin and Ether ETFs approved (2024) – SEC oversight
    • Stablecoin regulation actively debated

EU (MiCA – Markets in Crypto-Assets):
    • Comprehensive crypto regulation (effective 2024-2025)
    • Licensing for crypto-asset service providers (CASPs)
    • Stablecoin requirements (e-money tokens, asset-referenced tokens)
    • Market abuse provisions for crypto
    • Most advanced comprehensive crypto regulatory framework globally

UK:
    • FCA registration for crypto businesses
    • Financial promotions regime extended to crypto (2023)
    • Phased approach to comprehensive regulation

Asia:
    • Japan: Licensed virtual asset exchanges (JFSA), stablecoin framework
    • Singapore: Payment Services Act, MAS licensing
    • Hong Kong: VASP licensing regime (SFC)
    • South Korea: Virtual Asset User Protection Act
    • China: Comprehensive ban on crypto trading (2021)

International:
    • FSB global crypto framework recommendations
    • FATF Travel Rule (information sharing between VASPs)
    • BIS/CPMI work on CBDCs (Central Bank Digital Currencies)
    • IOSCO crypto policy recommendations
"""
