"""
Structured Products & Alternative Instruments
==============================================

Structured products are pre-packaged investment strategies combining
derivatives with traditional instruments to create customized
risk/return profiles.

═══════════════════════════════════════════════════════════════════════
STRUCTURED NOTES
═══════════════════════════════════════════════════════════════════════

Debt obligations of an issuer (typically a bank) where the return is
linked to the performance of an underlying asset, index, or rate.

Key Components:
    • Bond component (zero-coupon or coupon-bearing) – provides structure
    • Derivative component (embedded option) – provides linked return
    • Issuer credit risk – investor bears default risk of the issuing bank

Common Types:

    Principal-Protected Notes (PPNs):
        • Guarantee return of principal at maturity (subject to issuer credit)
        • Upside linked to equity index, commodity, or other reference
        • Participation rate: fraction of upside captured (e.g., 80%)
        • Cap: maximum return may be limited
        • Trade-off: lower participation for full principal protection

    Reverse Convertibles:
        • High coupon (e.g., 8-15% annualized)
        • If underlying falls below barrier ("knock-in"), investor
          receives shares instead of par at maturity
        • Popular on individual stocks or baskets
        • Essentially: investor sells a put option (receives premium as coupon)

    Autocallable Notes:
        • Periodically observed (e.g., quarterly)
        • If underlying above autocall level, note is called early with coupon
        • If underlying falls below barrier at maturity, investor takes loss
        • "Snowball" variant: missed coupons accumulate and paid at autocall
        • Very popular in Asia and Europe

    Buffer / Barrier Notes:
        • Provide downside protection (buffer) up to a certain level
        • Beyond the buffer, investor bears losses
        • Upside may be capped or uncapped
        • "Accelerated return" variants provide leveraged upside to a cap

    Range Accrual Notes:
        • Coupon accrues only on days when a reference rate or index
          falls within a specified range
        • Linked to interest rates, FX rates, or equity indices

    Worst-of Notes:
        • Payoff linked to the worst-performing asset in a basket
        • Higher coupon due to correlation risk and multiple risk exposures
        • Popular on baskets of 2-4 stocks or indices

    Digital / Binary Notes:
        • Fixed coupon if underlying meets condition; zero if not
        • Simple payout structure

═══════════════════════════════════════════════════════════════════════
SECURITIZED PRODUCTS
═══════════════════════════════════════════════════════════════════════

Financial instruments created by pooling cash-flow-generating assets
and issuing securities backed by those pools.

Collateralized Debt Obligations (CDOs):
    Structured product backed by a diversified pool of debt.
    Tranches: Senior (AAA), Mezzanine (BBB-A), Equity (unrated, first loss).

    Types:
    • CLOs (Collateralized Loan Obligations) – Backed by leveraged loans
      (most common surviving CDO type, ~$1 trillion market)
    • CBO (Collateralized Bond Obligations) – Backed by bonds
    • Synthetic CDOs – Backed by CDS rather than actual bonds/loans
    • CDO² (CDO-squared) – CDO of CDO tranches (extremely complex, largely
      discredited after 2008)
    • Bespoke CDOs – Customized for specific investors

    CLO Mechanics:
        • Manager actively manages the loan portfolio (5-year reinvestment period)
        • Equity tranche gets residual cash flows (target 12-20% returns)
        • Senior tranches rated AAA, backed by subordination and overcollateralization
        • Waterfall: interest and principal paid sequentially from senior to equity
        • Tests: overcollateralization (OC) and interest coverage (IC) tests
          determine if cash flows are diverted from junior to senior tranches

Mortgage-Backed Securities (MBS):
    (Detailed in fixed_income_markets.py)
    • Agency pass-throughs, CMOs, non-agency RMBS, CMBS

Asset-Backed Securities (ABS):
    • Auto loans, credit cards, student loans, equipment leases
    • Structured in tranches with credit enhancement
    • Revolving vs. amortizing structures
    • Credit enhancement: subordination, excess spread, reserve accounts,
      overcollateralization, surety bonds, letters of credit

Commercial Mortgage-Backed Securities (CMBS):
    • Backed by commercial property loans (office, retail, hotel, multifamily)
    • Conduit/fusion CMBS: diversified pool of loans
    • Single-asset/single-borrower (SASB) CMBS
    • CRE CLOs: Managed pools of transitional commercial real estate loans

═══════════════════════════════════════════════════════════════════════
CREDIT-LINKED INSTRUMENTS
═══════════════════════════════════════════════════════════════════════

Credit-Linked Notes (CLNs):
    Debt instruments where the coupon and/or principal repayment is
    linked to the credit performance of a reference entity.
    Essentially a funded credit default swap.

Catastrophe Bonds (Cat Bonds):
    Insurance-linked securities. If a specified catastrophic event
    occurs (hurricane, earthquake), investors lose principal (transferred
    to the insurer). High yield compensates for this risk.
    ~$45+ billion market, growing rapidly.

Insurance-Linked Securities (ILS):
    Broader category including cat bonds, industry loss warranties,
    sidecars, and quota share arrangements.

Weather Derivatives:
    Derivatives based on weather outcomes (temperature, rainfall,
    snowfall). Used by utilities, agriculture, tourism.
    • Heating Degree Days (HDD) and Cooling Degree Days (CDD) contracts
    • Traded on CME

═══════════════════════════════════════════════════════════════════════
ALTERNATIVE INVESTMENT VEHICLES
═══════════════════════════════════════════════════════════════════════

Interval Funds:
    Registered closed-end funds that periodically offer to repurchase
    shares (quarterly). Access to illiquid strategies (private credit,
    real estate) for retail investors. Growing rapidly.

Tender Offer Funds:
    Similar to interval funds but repurchases at board's discretion.
    Less frequent liquidity than interval funds.

Non-Traded REITs / BDCs:
    Registered with SEC but not listed on an exchange.
    • NAV calculated periodically (monthly or quarterly)
    • Limited liquidity (periodic redemption programs)
    • Higher fees than traded equivalents
    • Growing institutional-quality product category

Private Credit Funds (Direct Lending):
    Vehicles providing loans directly to companies, bypassing banks.
    Explosive growth post-2010s. Now competing with syndicated loan market.

Digital Securities / Security Tokens:
    Traditional financial instruments issued and traded on blockchain.
    • Tokenized equities, bonds, real estate, fund interests
    • Regulated under existing securities laws
    • Potential for 24/7 trading, fractional ownership, faster settlement
    • Still nascent but growing regulatory framework
"""
