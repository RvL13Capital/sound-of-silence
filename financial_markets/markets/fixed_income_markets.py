"""
Fixed-Income / Debt Markets (Bond Markets)
==========================================

Fixed-income markets facilitate the issuance and trading of debt securities.
Issuers borrow capital from investors and promise to pay periodic interest
(coupons) and return principal at maturity. The global bond market is larger
than the equity market by outstanding value.

MARKET SIZE & SCOPE (approximate as of mid-2020s)
──────────────────────────────────────────────────
• Global bond market outstanding: ~$140+ trillion
• US bond market: ~$55+ trillion
• Daily US bond trading volume: ~$1+ trillion
• Predominantly OTC (over-the-counter) trading

BOND FUNDAMENTALS
─────────────────
Key Terms:
    • Par / Face value   – Nominal amount paid at maturity (typically $1,000)
    • Coupon rate         – Annual interest rate as % of par
    • Coupon frequency    – Semi-annual (US), annual (Europe), quarterly, etc.
    • Maturity date       – Date when principal is repaid
    • Issue price         – Price at which bond is initially sold
    • Yield to Maturity (YTM) – Total return if held to maturity
    • Current yield       – Annual coupon ÷ current market price
    • Yield to Call (YTC) – Yield assuming bond is called at earliest date
    • Yield to Worst (YTW) – Lowest of YTM, YTC across all call dates
    • Accrued interest    – Interest earned since last coupon payment
    • Clean price         – Quoted price without accrued interest
    • Dirty / Full price  – Clean price + accrued interest (actual settlement)

Price-Yield Relationship:
    Bond prices and yields move inversely.
    • When interest rates rise → bond prices fall
    • When interest rates fall → bond prices rise
    • This is the fundamental interest rate risk of bonds

TYPES OF BONDS
──────────────

Government Bonds:
    US Treasury Securities:
        • Treasury Bills (T-Bills)  – Maturity ≤ 1 year, zero-coupon (discount)
        • Treasury Notes (T-Notes)  – Maturity 2–10 years, semi-annual coupon
        • Treasury Bonds (T-Bonds)  – Maturity 20–30 years, semi-annual coupon
        • TIPS (Treasury Inflation-Protected Securities) – Principal adjusts
          with CPI; pays real coupon rate on adjusted principal
        • FRNs (Floating Rate Notes) – 2-year maturity, coupon floats with
          13-week T-bill rate
        • STRIPS – Separately traded components of Treasury coupon securities
          (zero-coupon instruments)
        • I-Bonds (Series I Savings Bonds) – Retail savings bonds with
          inflation adjustment

    Sovereign Bonds (Other Countries):
        • Gilts (UK)
        • Bunds (Germany)
        • OATs (France – Obligations Assimilables du Trésor)
        • JGBs (Japan – Japanese Government Bonds)
        • BTPs (Italy)
        • Bonos (Spain)

    Supranational Bonds:
        • World Bank, European Investment Bank (EIB), Asian Development Bank

Agency Bonds (US):
    Government-Sponsored Enterprise (GSE) debt:
        • Fannie Mae (FNMA)
        • Freddie Mac (FHLMC)
        • Federal Home Loan Banks (FHLB)
        • Ginnie Mae (GNMA) – explicitly government-backed

Municipal Bonds (Munis):
    Issued by US state and local governments.
    • General Obligation (GO) bonds – Backed by taxing power of issuer
    • Revenue bonds – Backed by specific revenue stream (tolls, utilities)
    • Tax-exempt: Interest generally exempt from federal income tax,
      and often state/local tax if investor resides in issuing state
    • Taxable munis: Some municipal bonds are taxable (Build America Bonds)
    • Private activity bonds – Fund private projects with public benefit

Corporate Bonds:
    • Investment-grade (IG): Rated BBB-/Baa3 or higher
    • High-yield (HY) / "junk bonds": Rated BB+/Ba1 or lower
    • Senior secured – Backed by specific collateral
    • Senior unsecured – Backed by general creditworthiness
    • Subordinated / Junior – Lower priority in bankruptcy
    • Convertible bonds – Can be converted to equity shares
    • Callable bonds – Issuer can redeem early at call price
    • Putable bonds – Holder can demand early redemption
    • Zero-coupon bonds – No periodic coupons, issued at deep discount
    • Floating-rate notes (FRNs) – Coupon resets periodically (e.g., SOFR + spread)
    • Payment-in-Kind (PIK) – Interest paid with additional bonds, not cash
    • CoCo bonds (Contingent Convertible) – Convert to equity under stress triggers

Mortgage-Backed Securities (MBS):
    • Agency MBS – Issued/guaranteed by Ginnie Mae, Fannie Mae, Freddie Mac
    • Non-agency / Private-label MBS – No government guarantee
    • Pass-through securities – Principal & interest passed to investors
    • CMOs (Collateralized Mortgage Obligations) – Tranched MBS with
      different risk/return profiles (sequential, PAC, companion tranches)

Asset-Backed Securities (ABS):
    Securities backed by pools of receivables:
    • Auto loan ABS
    • Credit card ABS
    • Student loan ABS (SLABS)
    • Equipment lease ABS
    • CLOs (Collateralized Loan Obligations) – Backed by leveraged loans

CREDIT RATINGS
──────────────
Major Rating Agencies:
    • S&P Global Ratings
    • Moody's Investors Service
    • Fitch Ratings
    (Plus regional agencies: DBRS Morningstar, Japan Credit Rating Agency, etc.)

Rating Scales:
    Investment Grade:
        S&P/Fitch    Moody's     Description
        ─────────    ───────     ───────────
        AAA          Aaa         Highest quality
        AA+/AA/AA-   Aa1/Aa2/Aa3 High quality
        A+/A/A-      A1/A2/A3    Upper medium
        BBB+/BBB/BBB- Baa1/Baa2/Baa3 Medium (lowest IG)

    Below Investment Grade (High Yield / Speculative):
        BB+/BB/BB-   Ba1/Ba2/Ba3  Speculative
        B+/B/B-      B1/B2/B3     Highly speculative
        CCC+/CCC/CCC- Caa1/Caa2/Caa3 Substantial risk
        CC           Ca           Very high risk
        C            C            Imminent default
        D            –            Default

YIELD CURVE
───────────
The yield curve plots yields of bonds with the same credit quality but
different maturities. The Treasury yield curve is the most watched.

Shapes:
    • Normal (upward sloping) – Long-term yields > short-term yields
      (most common; reflects term premium and growth expectations)
    • Flat – Similar yields across maturities (often transitional)
    • Inverted – Short-term yields > long-term yields
      (historically a recession predictor)
    • Humped – Medium-term yields highest (relatively rare)

Key Yield Curve Metrics:
    • 2s10s spread – Difference between 10-year and 2-year Treasury yields
    • 3-month/10-year spread – Fed's preferred recession indicator
    • Term premium – Extra yield for holding longer-duration bonds

Yield Curve Movements:
    • Parallel shift – All maturities move by similar amount
    • Steepening – Long end rises more (or short end falls more)
    • Flattening – Long end falls more (or short end rises more)
    • Twist – Short and long ends move in opposite directions
    • Butterfly – Changes in curvature (belly vs. wings)

BOND RISK MEASURES
──────────────────
Duration:
    Measures sensitivity of bond price to interest rate changes.

    • Macaulay Duration – Weighted average time to receive cash flows
    • Modified Duration – % price change for 1% change in yield
      Modified Duration = Macaulay Duration / (1 + yield/n)
    • Effective Duration – Used for bonds with embedded options;
      measures price sensitivity using actual price changes for
      parallel yield curve shifts
    • Key Rate Duration – Sensitivity to changes at specific maturity
      points on the yield curve
    • Dollar Duration (DV01) – Dollar change in price for 1 basis
      point change in yield

    Rule of thumb: A bond with duration of 5 years will lose ~5% in
    value for every 1% rise in interest rates.

Convexity:
    Measures curvature of the price-yield relationship.
    Duration gives a linear approximation; convexity corrects for the
    curve. Positive convexity is beneficial (prices rise more than
    duration predicts when yields fall, fall less when yields rise).

    • Callable bonds have negative convexity at low yields (price
      appreciation is capped by the call price)
    • MBS also exhibit negative convexity due to prepayment risk

Credit Spread:
    Difference in yield between a bond and a comparable-maturity
    risk-free benchmark (usually Treasury yield).

    • Option-Adjusted Spread (OAS) – Spread adjusted for embedded options
    • Z-spread (zero-volatility spread) – Constant spread over the
      entire Treasury spot curve
    • G-spread – Spread over the interpolated government bond yield
    • I-spread – Spread over the swap curve (SOFR or equivalent)

BOND MARKET BENCHMARKS & INDICES
──────────────────────────────────
• Bloomberg US Aggregate Bond Index ("the Agg") – Broadest US IG bond index
• Bloomberg Global Aggregate – Global IG bonds
• ICE BofA US High Yield Index – US high-yield corporate bonds
• Bloomberg US Treasury Index – US government bonds only
• Bloomberg US Corporate Bond Index – US IG corporate bonds
• JPMorgan EMBI (Emerging Markets Bond Index) – EM sovereign debt
• JPMorgan GBI-EM – EM local-currency government bonds
• S&P/LSTA Leveraged Loan Index – US leveraged loans
• iBoxx indices – Widely used in Europe for corporate and government bonds

BOND TRADING & MARKET STRUCTURE
────────────────────────────────
• Bonds primarily trade OTC (not on centralized exchanges)
• Dealer-based market: investors trade through broker-dealers
• Electronic platforms: MarketAxess, Tradeweb, Bloomberg, ICE BondPoint
• TRACE (Trade Reporting and Compliance Engine) – FINRA system requiring
  post-trade reporting of US corporate and agency bond transactions
• EMMA (Electronic Municipal Market Access) – MSRB system for muni data
• Request-for-Quote (RFQ) – Dominant protocol for electronic bond trading
• All-to-all trading – Growing trend enabling direct investor-to-investor trades
• Portfolio trading – Trading baskets of bonds as a single package (growing rapidly)

MONEY MARKET INSTRUMENTS
─────────────────────────
Short-term debt (maturity ≤ 1 year), highly liquid, low risk:

    • Treasury Bills (T-Bills) – US government, 4-week to 52-week maturities
    • Commercial Paper (CP) – Short-term unsecured corporate debt (1–270 days)
    • Certificates of Deposit (CDs) – Time deposits at banks
    • Bankers' Acceptances (BAs) – Bank-guaranteed trade finance instruments
    • Repurchase Agreements (Repos) – Short-term collateralized lending
      - Repo: sell security + agree to repurchase at higher price
      - Reverse repo: buy security + agree to resell
      - Overnight, term, and open repos
      - Tri-party repo: settled through clearing bank (BNY Mellon, JPMorgan)
    • Federal Funds – Overnight interbank lending of reserves at the Fed
    • Eurodollars – US dollar deposits held in banks outside the US
    • SOFR (Secured Overnight Financing Rate) – Benchmark rate based on
      Treasury repo transactions (replaced LIBOR)

REFERENCE RATES
───────────────
The transition away from LIBOR (completed mid-2023):
    • SOFR (US) – Secured, based on overnight Treasury repo market
    • SONIA (UK) – Sterling Overnight Index Average (unsecured)
    • €STR (Eurozone) – Euro Short-Term Rate (replaced EONIA)
    • TONA (Japan) – Tokyo Overnight Average Rate
    • SARON (Switzerland) – Swiss Average Rate Overnight (secured)
    • CORRA (Canada) – Canadian Overnight Repo Rate Average
"""
