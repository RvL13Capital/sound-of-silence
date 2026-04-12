# sound-of-silence

A comprehensive financial markets knowledge base paired with a systematic European equity momentum strategy engine.

## Project Overview

This repository contains two main components:

1. **Financial Markets Knowledge Base** (`financial_markets/`) -- a structured Python reference covering global market structure, instruments, trading strategies, regulation, and infrastructure.
2. **DACH Momentum Strategy** (`dach_momentum/`) -- a fully backtestable momentum + quality strategy targeting European small/mid-cap equities across 16 countries, implementing Minervini's trend template, CAN SLIM quality filters, and a market regime filter.

## Installation

**Requirements:** Python 3.11+

### Using pip

```bash
git clone https://github.com/your-org/sound-of-silence.git
cd sound-of-silence
pip install -r dach_momentum/requirements.txt
```

### Using Poetry

```bash
git clone https://github.com/your-org/sound-of-silence.git
cd sound-of-silence
poetry install
```

### Dependencies

- `pandas >= 2.1`
- `numpy >= 1.26`
- `requests >= 2.31`
- `lxml >= 4.9`
- `html5lib >= 1.1`
- `yfinance >= 0.2.40`
- `beautifulsoup4 >= 4.12`

## Quick Start

```bash
# 1. Build the stock universe (scrapes Wikipedia index pages for 16 countries)
python -m dach_momentum universe

# 2. Download historical price data via yfinance
python -m dach_momentum data

# 3. Generate momentum + trend template signals
python -m dach_momentum signals

# 4. Run a backtest (CAN SLIM mode recommended)
cd dach_momentum
python run_backtest.py --mode canslim
```

## Usage

All `run_*.py` scripts should be executed from inside the `dach_momentum/` directory.

### Universe Construction

Scrape index constituents from Wikipedia for DAX, MDAX, SDAX, TecDAX, ATX, SMI, SMIM, and indices across France, Netherlands, Belgium, Italy, Spain, Scandinavia, UK, Poland, Portugal, and Greece. Applies market-cap, volume, free-float, listing-age, and sector filters.

```bash
python -m dach_momentum universe
```

### Price Data Download

Download and cache daily OHLCV data for the filtered universe via yfinance.

```bash
python -m dach_momentum data
```

### Signal Generation

Compute momentum scores, trend template compliance (Minervini), and regime filter state.

```bash
python -m dach_momentum signals
```

### CAN SLIM Deep Dive

Run earnings quality, valuation, cash flow, insider activity, and analyst coverage analysis on trend template candidates.

```bash
cd dach_momentum
python run_canslim.py                     # analyze all candidates
python run_canslim.py JEN.DE DRW3.DE      # analyze specific tickers
```

### Exit Scan

Evaluate exit signals (hard stops, trailing SMA exits, regime-off exits) on current or simulated positions.

```bash
cd dach_momentum
python run_exits.py                       # simulate positions entered 30 days ago
python run_exits.py --days 60             # simulate positions entered 60 days ago
python run_exits.py --manual              # enter positions manually
```

### Backtest

Full historical simulation with weekly screening, position sizing, tiered exits, and transaction costs.

```bash
cd dach_momentum
python run_backtest.py --mode canslim     # momentum + CAN SLIM quality filters
python run_backtest.py --mode momentum    # momentum + trend template only
python run_backtest.py --start 2015-01-01 --end 2025-12-31
```

### Top Gains Analysis

Find the 50 highest percentage gains within any 6-month window across the entire universe.

```bash
cd dach_momentum
python run_top_gains.py
```

### Max Adverse Excursion (MAE)

Analyze how far underwater each backtest trade went before recovering or being stopped out.

```bash
cd dach_momentum
python run_mae.py
```

### Fundamental Research Dashboard

Pull fundamental data for all stocks passing the technical screen and display a research dashboard covering earnings quality, valuation, cash flow, insider activity, and analyst coverage.

```bash
cd dach_momentum
python run_dashboard.py
```

## Strategy Overview (v3 Spec)

The strategy combines three layers:

1. **Minervini Trend Template** -- price must be above the 50-day, 150-day, and 200-day SMAs in the correct stacking order; the 200-day SMA must be rising for at least 1 month; price must be within 25% of its 52-week high and at least 30% above its 52-week low.

2. **CAN SLIM Quality Filters** -- gross profitability above universe median, net debt/EBITDA below 3.0x, volume confirmation, Bollinger bandwidth trend health, and extension guards.

3. **Regime Filter** -- the CDAX Composite index must be above its 40-week SMA to allow new entries. When the regime is off, no new positions are opened and existing positions use a tighter 10-week SMA exit.

**Position sizing:** risk-per-trade targeting (1% of equity per trade), with a 12% single-position cap, 30% single-sector cap, and a 15-position maximum. Initial stops are set at 10% or 2.5x ATR (whichever is wider, capped at 15%). After +20% profit, the stop switches to a trailing 30-week SMA.

**Transaction costs:** EUR 10 per trade (DKB) plus an estimated 50 bps one-way spread.

## Backtest Results Summary

Results from the full backtest over the period **2010--2026**, covering **16 countries** and **753 stocks**, starting with an initial portfolio of **EUR 20,000**.

### CAN SLIM Mode

| Metric           | Value        |
|------------------|--------------|
| CAGR             | +20.7%       |
| Sharpe Ratio     | 1.12         |
| Sortino Ratio    | 1.33         |
| Max Drawdown     | -26.5%       |
| Win Rate         | 43.8%        |
| Profit Factor    | 4.32         |
| Total Trades     | 315          |
| Avg Holding      | 139 days     |
| Final Equity     | EUR 423,729  |

### Momentum Mode

| Metric           | Value        |
|------------------|--------------|
| CAGR             | +19.8%       |
| Sharpe Ratio     | 1.02         |
| Sortino Ratio    | 1.21         |
| Max Drawdown     | -31.5%       |
| Win Rate         | 40.2%        |
| Profit Factor    | 2.58         |

### Survivorship Bias Note

These results use the current index constituents and do not account for stocks that were delisted or dropped from indices over the backtest period. A realistic survivorship-bias-adjusted CAGR estimate is **~14--17%**, which still represents strong performance for a systematic European small/mid-cap strategy.

## Directory Structure

```
sound-of-silence/
├── README.md
├── LICENSE                               # MIT License
├── pyproject.toml                        # Project metadata (Poetry)
│
├── financial_markets/                    # Financial markets knowledge base
│   ├── __init__.py
│   ├── markets/                          # Market types and structures
│   │   ├── equity_markets.py             #   Stock markets, IPOs, indices, trading mechanics
│   │   ├── fixed_income_markets.py       #   Bonds, yield curves, credit ratings, money markets
│   │   ├── forex_markets.py              #   FX markets, currency pairs, central banks
│   │   ├── derivatives_markets.py        #   Futures, options, swaps, exotic derivatives
│   │   └── commodity_markets.py          #   Energy, metals, agriculture, commodity pricing
│   │
│   ├── instruments/                      # Financial instrument taxonomy
│   │   ├── equity_instruments.py         #   Stocks, preferred, ADRs, REITs, MLPs, BDCs, SPACs
│   │   └── structured_products.py        #   Structured notes, securitization, CLOs, CDOs
│   │
│   ├── exchange_traded_products/         # Deep dive into ETPs
│   │   ├── etf_mechanics.py              #   Creation/redemption, arbitrage, tax efficiency
│   │   ├── etf_categories.py             #   Equity, fixed-income, commodity, currency, crypto ETFs
│   │   ├── leveraged_inverse_etfs.py     #   Leveraged/inverse mechanics, compounding, ETNs
│   │   └── etf_strategies.py             #   Factor investing, asset allocation, tax-loss harvesting
│   │
│   ├── infrastructure/                   # Market plumbing
│   │   ├── exchanges.py                  #   Global exchanges, technology, order routing, dark pools
│   │   └── clearing_settlement.py        #   CCPs, settlement, CSDs, securities lending, DLT
│   │
│   ├── participants/                     # Who operates in markets
│   │   ├── institutional_investors.py    #   Asset managers, pensions, SWFs, hedge funds, PE/VC
│   │   └── market_makers_and_hft.py      #   Market makers, HFT, investment banks, retail
│   │
│   ├── regulation/                       # Regulatory frameworks
│   │   ├── us_regulation.py              #   SEC, CFTC, Dodd-Frank, Basel, securities laws
│   │   └── global_regulation.py          #   MiFID II, UCITS, EMIR, AIFMD, Asian regulation
│   │
│   └── trading/                          # Trading strategies and analytics
│       ├── technical_analysis.py         #   Indicators, chart patterns, volume analysis
│       ├── execution_algorithms.py       #   VWAP, TWAP, market impact, slippage
│       ├── risk_management.py            #   VaR, position sizing, stress testing, drawdown control
│       ├── quantitative_strategies.py    #   Systematic, stat-arb, mean reversion, ML approaches
│       └── advanced_derivatives.py       #   Greeks hedging, volatility trading, curve strategies
│
└── dach_momentum/                        # DACH momentum strategy engine
    ├── dach_momentum/                    # Core package
    │   ├── __init__.py
    │   ├── __main__.py                   #   CLI entry point (universe | data | signals)
    │   ├── config.py                     #   All strategy parameters and paths
    │   ├── universe.py                   #   Wikipedia scraper + universe construction
    │   ├── data.py                       #   yfinance price download + caching
    │   ├── signals.py                    #   Trend template, momentum, regime filter
    │   ├── canslim.py                    #   CAN SLIM quality scoring + deep dive
    │   ├── positions.py                  #   Position sizing, stop logic, exit scanner
    │   └── dashboard.py                  #   Fundamental research dashboard
    │
    ├── data/                             # Data files (generated + seed)
    │   ├── seed_universe.csv             #   Fallback ticker list for Wikipedia scraping gaps
    │   └── universe.csv                  #   Generated universe output
    │
    ├── run_backtest.py                   # Full historical backtest simulation
    ├── run_canslim.py                    # CAN SLIM deep dive on candidates
    ├── run_exits.py                      # Exit signal scanner
    ├── run_top_gains.py                  # Top historical gain finder
    ├── run_mae.py                        # Max adverse excursion analysis
    ├── run_dashboard.py                  # Fundamental research dashboard runner
    └── requirements.txt                  # Python dependencies
```

## Knowledge Base Topics

The `financial_markets/` package serves as a structured reference covering:

- **Market Structure** -- equity, fixed-income, FX, derivatives, and commodity markets
- **Financial Instruments** -- stocks, bonds, options, futures, swaps, structured products
- **Exchange-Traded Products** -- ETFs, ETNs, ETCs: mechanics, categories, and strategies
- **Market Infrastructure** -- exchanges, clearinghouses, settlement systems, securities lending
- **Market Participants** -- institutional investors, hedge funds, market makers, HFT, retail
- **Regulation** -- US securities law, Dodd-Frank, Basel III, MiFID II, global frameworks
- **Trading** -- technical analysis, execution algorithms, risk management, quant strategies, derivatives

## Known Limitations

- **Survivorship bias** -- the universe is built from current index constituents. Stocks that were delisted, acquired, or dropped from indices during the backtest period are missing, which inflates historical returns.
- **No point-in-time fundamentals** -- CAN SLIM quality metrics use the latest available data from yfinance, not what was actually available at each historical decision point.
- **Currency effects** -- all stocks are priced in their local currency (EUR, CHF, SEK, GBP, NOK, DKK, PLN, etc.) but portfolio-level metrics are reported in EUR without explicit FX hedging or conversion adjustments.
- **Wikipedia scraping gaps** -- universe construction relies on Wikipedia constituent tables, which may be incomplete, outdated, or restructured without notice. A seed CSV is included as a fallback.
- **Free data limitations** -- yfinance data may have gaps, splits not properly adjusted, or missing tickers for smaller European stocks.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 RvL13Capital
