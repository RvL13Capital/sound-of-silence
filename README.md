# sound-of-silence

A comprehensive knowledge base covering global financial markets and exchange-traded financial products.

## Structure

```
financial_markets/
├── markets/                          # Market types and structures
│   ├── equity_markets.py             # Stock markets, IPOs, indices, trading mechanics
│   ├── fixed_income_markets.py       # Bonds, yield curves, credit ratings, money markets
│   ├── forex_markets.py              # FX markets, currency pairs, central banks
│   ├── derivatives_markets.py        # Futures, options, swaps, exotic derivatives
│   └── commodity_markets.py          # Energy, metals, agriculture, commodity pricing
│
├── instruments/                      # Financial instrument taxonomy
│   ├── equity_instruments.py         # Stocks, preferred, ADRs, REITs, MLPs, BDCs, SPACs
│   └── structured_products.py        # Structured notes, securitization, CLOs, CDOs
│
├── exchange_traded_products/         # Deep dive into ETPs
│   ├── etf_mechanics.py              # Creation/redemption, arbitrage, tax efficiency, pricing
│   ├── etf_categories.py             # Equity, fixed-income, commodity, currency, crypto ETFs
│   ├── leveraged_inverse_etfs.py     # Leveraged/inverse mechanics, compounding, ETNs
│   └── etf_strategies.py             # Factor investing, asset allocation, tax-loss harvesting
│
├── infrastructure/                   # Market plumbing
│   ├── exchanges.py                  # Global exchanges, technology, order routing, dark pools
│   └── clearing_settlement.py        # CCPs, settlement, CSDs, securities lending, DLT
│
├── participants/                     # Who operates in markets
│   ├── institutional_investors.py    # Asset managers, pensions, SWFs, hedge funds, PE/VC
│   └── market_makers_and_hft.py      # Market makers, HFT, investment banks, retail, custodians
│
├── regulation/                       # Regulatory frameworks
│   ├── us_regulation.py              # SEC, CFTC, Dodd-Frank, Basel, securities laws
│   └── global_regulation.py          # MiFID II, UCITS, EMIR, AIFMD, Asian regulation, crypto
│
└── trading/                          # Trading strategies and analytics
    ├── technical_analysis.py         # Indicators, chart patterns, volume analysis
    ├── execution_algorithms.py       # VWAP, TWAP, market impact, slippage, best execution
    ├── risk_management.py            # VaR, position sizing, stress testing, drawdown control
    ├── quantitative_strategies.py    # Systematic, stat-arb, mean reversion, ML approaches
    └── advanced_derivatives.py       # Greeks hedging, volatility trading, curve strategies

dach_momentum/                        # DACH small/mid-cap momentum strategy (Python)
├── dach_momentum/
│   ├── config.py                     # Strategy parameters and project configuration
│   └── universe.py                   # DACH index universe construction
├── data/
│   ├── seed_universe.csv             # Seed ticker list (fallback for Wikipedia scraping)
│   └── universe.csv                  # Generated universe output
└── requirements.txt                  # Python dependencies
```

## Topics Covered

- **Market Structure**: Equity, fixed-income, FX, derivatives, and commodity markets
- **Financial Instruments**: Stocks, bonds, options, futures, swaps, structured products
- **Exchange-Traded Products**: ETFs, ETNs, ETCs — mechanics, categories, strategies
- **Market Infrastructure**: Exchanges, clearinghouses, settlement systems, securities lending
- **Market Participants**: Institutional investors, hedge funds, market makers, HFT, retail
- **Regulation**: US securities law, Dodd-Frank, Basel III, MiFID II, global frameworks
- **Trading**: Technical analysis, execution algorithms, risk management, quant strategies, derivatives
- **DACH Momentum Strategy**: Systematic momentum + quality strategy for German/Austrian/Swiss small/mid-caps
