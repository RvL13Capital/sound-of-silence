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
python run_backtest.py --mode momentum     # trend template + momentum baseline
python run_backtest.py --mode canslim      # adds CAN SLIM quality filters
python run_backtest.py --mode rich_quick   # 5-position concentrated breakout
python run_backtest.py --mode super_rich   # pattern + momentum + quality, 5-position; funding-stress overlay enabled by default
python run_backtest.py --mode cash_machine # high-frequency, 15-position, 10w-SMA exits
python run_backtest.py --mode all          # run all 5 and print side-by-side comparison
python run_backtest.py --start 2015-01-01 --end 2025-12-31
```

### Funding-stress overlay sweeps

Sensitivity sweep and walk-forward validation of the BTC perp funding-rate gate that's wired into super_rich. Refresh the cache via `python -m dach_momentum.btc_data` first.

```bash
cd dach_momentum
python run_funding_sweep.py --modes super_rich          # 5x3 threshold/window grid
python run_walkforward_funding.py --mode super_rich     # anchored 2020-2025 walk-forward
python run_overlay_sanity.py                            # buy-and-hold benchmark sanity check
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

## Strategy Overview

The strategy stack has five optional layers; each `--mode` enables a different combination.

1. **Minervini Trend Template** -- price must be above the 50-day, 150-day, and 200-day SMAs in the correct stacking order; the 200-day SMA must be rising for at least 1 month; price must be within 25% of its 52-week high and at least 30% above its 52-week low.

2. **CAN SLIM Quality Filters** -- gross profitability above universe median, net debt/EBITDA below 3.0x, volume confirmation, Bollinger bandwidth trend health, and extension guards.

3. **CDAX Regime Filter** -- the CDAX Composite index must be above its 40-week SMA to allow new entries. When the regime is off, no new positions are opened and existing positions use a tighter 10-week SMA exit.

4. **Pattern recognition (super_rich only)** -- VCP, Cup & Handle, Pocket Pivot, Flag, Double Bottom, plus Japanese candlestick patterns (Homma/Nison) used as confirmation. Implemented in `dach_momentum/patterns.py`.

5. **Crypto-leverage stress overlay (super_rich only, opt-in per mode)** -- BTC perpetual funding rate from CoinDesk's CCIX/Binance data. Blocks new entries when the 14-day mean per-8h funding rate exceeds 5 bp (~p95 historically). Walk-forward validated 2020-2025 (5/5 test folds positive, +22.8pp mean test Δ CAGR). Configured via `FUNDING_OVERLAY_BY_MODE` in [config.py](dach_momentum/dach_momentum/config.py); other modes are intentionally OFF (rich_quick was walk-forward refuted; canslim/momentum/cash_machine showed no in-sample signal worth testing).

### Strategy Modes

| Mode | Filters | Sizing | Funding overlay |
|------|---------|--------|-----------------|
| `momentum` | Trend template + momentum | 1% risk, 10-position cap | OFF |
| `canslim` | + CAN SLIM quality (score ≥ 3) | 1% risk, 10-position cap | OFF |
| `rich_quick` | Trend + 80th-percentile momentum, near 52w high, volume surge | 2% risk, 5-position cap, up to 25% per name | OFF |
| `super_rich` | Pattern score ≥ 50 + momentum ≥ 20% + quality ≥ 3 + asymmetric stops (BE @ +10%, +5% @ +20%, +15% @ +35%) | 2% risk, 5-position cap, up to 30% per name | **ON (5 bp / 14 d)** |
| `cash_machine` | Trend + lower quality bar; 10-week SMA exit (faster turnover) | 1% risk, 15-position cap | OFF |

**Default position sizing (momentum/canslim):** risk-per-trade targeting (1% of equity per trade), 12% single-position cap, 30% single-sector cap, 15-position maximum. Initial stops are 10% or 2.5x ATR (whichever is wider, capped at 15%). After +20% profit, the stop switches to a trailing 30-week SMA.

**Transaction costs:** EUR 10 per trade (DKB) plus an estimated 50 bps one-way spread.

## Backtest Results Summary

Results from the full backtest over the period **2010--2026**, covering **16 countries** and **753 stocks**, starting with an initial portfolio of **EUR 20,000**.

### Side-by-side comparison (all 5 modes)

| Metric            | Momentum | CAN SLIM | Rich Quick | Super Rich (overlay) | Cash Machine |
|-------------------|---------:|---------:|-----------:|---------------------:|-------------:|
| CAGR              | +19.7%   | +20.6%   | +19.5%     | **+27.2%**           | +18.1%       |
| Max Drawdown      | -31.5%   | -26.5%   | -31.7%     | **-23.9%**           | -26.7%       |
| Sharpe Ratio      | 1.02     | 1.12     | 0.97       | **1.27**             | 0.92         |
| Sortino Ratio     | 1.21     | 1.32     | 1.11       | **1.66**             | 1.02         |
| Calmar Ratio      | 0.63     | 0.78     | 0.61       | **1.14**             | 0.68         |
| Profit Factor     | 2.56     | 4.26     | 2.45       | 3.72                 | 1.85         |
| Total Trades      | 345      | 323      | 155        | 144                  | 1,034        |
| Win Rate          | 39.4%    | 42.7%    | 38.1%      | 39.6%                | 31.5%        |
| Avg Win           | +44.3%   | +41.4%   | +50.1%     | +50.2%               | +26.0%       |
| Avg Loss          | -9.3%    | -7.9%    | -8.1%      | -6.0%                | -5.2%        |

**`super_rich` numbers above include the BTC funding-stress overlay (5 bp / 14 d) which is enabled by default for that mode.** Without the overlay, `super_rich` baseline CAGR is +20.8%, max DD -27.7%, Sharpe 1.00. The overlay adds the rest.

### Walk-forward validation of the funding overlay (super_rich)

Anchored at 2020-01-01: train on data through end of (Y-1), pick the best (threshold, window) cell, apply to year Y. All 5 folds picked the same parameterisation (5 bp / 14 d).

| Fold Y | Best params | Train Δ CAGR | Base CAGR (Y) | Overlay CAGR (Y) | Test Δ |
|--------|-------------|-------------:|--------------:|-----------------:|-------:|
| 2021   | 5bp/14d     | +9.02pp      | +38.6%        | +100.3%          | **+61.65pp** |
| 2022   | 5bp/14d     | +31.39pp     | -19.0%        | +6.7%            | +25.71pp |
| 2023   | 5bp/14d     | +28.60pp     | -2.1%         | -0.9%            | +1.20pp  |
| 2024   | 5bp/14d     | +20.98pp     | +24.5%        | +46.0%           | +21.54pp |
| 2025   | 5bp/14d     | +21.11pp     | +18.9%        | +22.8%           | +3.91pp  |

**Aggregate: 5/5 folds positive, mean test Δ CAGR +22.80pp.** The critical fold is 2021: trained on 2020 alone (with 2021's leverage blow-off entirely out-of-sample), the algorithm picked 5 bp / 14 d and that pick delivered +61.65pp on the held-out 2021 test year.

### Buy-and-hold sanity check (2021-2025 walk-forward window, annualised)

| Series                | CAGR    | α vs DAX |
|-----------------------|--------:|---------:|
| DAX (^GDAXI) buy-and-hold | +12.29% | --       |
| `super_rich` baseline | +13.00% | +0.71pp/yr |
| `super_rich` + overlay | **+32.85%** | **+20.56pp/yr** |

The +20pp/yr alpha vs DAX is genuine, not beta exposure. Cleanest evidence is **2022**: DAX -12.3%, baseline -16.7%, overlay **+7.1%** — overlay outperformed in a down market, and the gate fired 0% of days that year (alpha came from the *carryover* effect of having different positions because the gate blocked late-2021 entries).

**Honest caveat:** in the 2021-2025 window, `super_rich` *baseline* (without the overlay) only beat DAX by +0.71pp/yr — a sharp drop from the 2010-2019 era when it crushed DAX in many years (+56pp in 2013, +48pp in 2017). The overlay is the dominant alpha source for the recent half-decade.

### Survivorship Bias Note

These results use the current index constituents and do not account for stocks that were delisted or dropped from indices over the backtest period. A realistic survivorship-bias-adjusted CAGR estimate is **~14--17%** for `momentum`/`canslim` and proportionally lower for the more aggressive modes. The funding overlay's relative uplift on `super_rich` should be more robust to survivorship bias (since it acts on entry timing, not stock selection), but absolute CAGR numbers are still inflated.

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
    │   ├── __main__.py                   #   CLI entry point (universe | data | signals | btc_data)
    │   ├── config.py                     #   All strategy parameters incl. FUNDING_OVERLAY_BY_MODE
    │   ├── universe.py                   #   Wikipedia scraper + universe construction
    │   ├── data.py                       #   yfinance price download + caching
    │   ├── signals.py                    #   Trend, momentum, regime, BTC regime, funding stress
    │   ├── canslim.py                    #   CAN SLIM quality scoring + deep dive
    │   ├── patterns.py                   #   Chart patterns (VCP, Cup&Handle, Pocket Pivot, …) + candlesticks
    │   ├── positions.py                  #   Position sizing, stop logic, exit scanner
    │   ├── btc_data.py                   #   CoinDesk BTC index + perp funding-rate fetcher
    │   ├── external_data.py              #   SimFin/FMP/FRED for fundamentals + macro
    │   └── dashboard.py                  #   Fundamental research dashboard
    │
    ├── data/                             # Data files (generated + seed)
    │   ├── seed_universe.csv             #   Fallback ticker list for Wikipedia scraping gaps
    │   ├── universe.csv                  #   Generated universe output
    │   ├── btc_daily.csv                 #   CoinDesk CCIX BTC-USD daily history (2010-07-)
    │   ├── btc_funding.csv               #   Binance BTC-USDT-PERP funding rate (2019-09-)
    │   └── prices/                       #   Per-ticker parquet OHLCV cache
    │
    ├── run_backtest.py                   # Full historical backtest simulation (5 modes)
    ├── run_funding_sweep.py              # 5x3 threshold/window sensitivity sweep on the funding overlay
    ├── run_walkforward_funding.py        # Anchored walk-forward validation of the overlay
    ├── run_overlay_sanity.py             # Buy-and-hold benchmark sanity check vs DAX
    ├── run_canslim.py                    # CAN SLIM deep dive on candidates
    ├── run_exits.py                      # Exit signal scanner
    ├── run_top_gains.py                  # Top historical gain finder
    ├── run_mae.py                        # Max adverse excursion analysis
    ├── run_walkforward.py                # General walk-forward harness (mode-level OOS testing)
    ├── run_enhanced.py                   # Fundamental + macro enhanced research view
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
