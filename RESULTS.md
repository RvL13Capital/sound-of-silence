# Backtest Results & Strategy Analysis

## Strategy Overview

- **Pan-European small/mid-cap momentum + quality strategy**
- **Universe:** 753 stocks across 16 European countries
- **Entry:** Minervini 8-criteria trend template + CAN SLIM quality filter + regime filter
- **Exit:** Tiered (hard stop 10% -> regime-off 10w SMA -> 30w SMA trailing)
- **Position sizing:** 1% risk per trade, max 10 positions

## Backtest Results (2010-2026)

### CAN SLIM Mode (recommended)

| Metric | Value |
|---|---|
| Initial Capital | EUR 20,000 |
| Final Equity | EUR 423,729 |
| Total Return | +2,039.6% |
| CAGR | +20.7% |
| Annual Volatility | 18.5% |
| Max Drawdown | -26.5% |
| Sharpe Ratio | 1.12 |
| Sortino Ratio | 1.33 |
| Calmar Ratio | 0.78 |
| Total Trades | 315 |
| Win Rate | 43.8% |
| Avg Win | +41.4% |
| Avg Loss | -8.2% |
| Profit Factor | 4.32 |
| Avg Holding | 139 days |

### Momentum Mode (baseline)

| Metric | Value |
|---|---|
| Initial Capital | EUR 20,000 |
| CAGR | +19.8% |
| Sharpe Ratio | 1.02 |
| Max Drawdown | -31.5% |
| Win Rate | 40.2% |
| Profit Factor | 2.58 |
| Total Trades | 338 |

### Annual Returns

| Year | CAN SLIM | Momentum |
|---|---|---|
| 2010 | +16.1% | +8.2% |
| 2011 | -4.3% | -6.7% |
| 2012 | +7.1% | +7.4% |
| 2013 | +52.5% | +69.4% |
| 2014 | -13.6% | +1.2% |
| 2015 | +41.1% | +49.6% |
| 2016 | +6.1% | -1.1% |
| 2017 | +54.9% | +67.2% |
| 2018 | -6.0% | +2.6% |
| 2019 | +24.5% | +26.6% |
| 2020 | +25.2% | +23.6% |
| 2021 | +49.4% | +34.2% |
| 2022 | -18.9% | -21.2% |
| 2023 | +8.4% | -2.7% |
| 2024 | +43.1% | +27.7% |
| 2025 | +42.9% | +26.7% |
| 2026 | +9.8% | +10.1% |

### Exit Reason Breakdown

| Exit Reason | CAN SLIM | Momentum |
|---|---|---|
| REGIME_OFF_10W | 147 | 146 |
| BELOW_30W_SMA | 103 | 100 |
| HARD_STOP | 63 | 89 |

### Trade Profile (Max Adverse Excursion)

- Winners avg max drawdown: -4.3%
- Losers avg max drawdown: -7.3%
- 77% of losers were briefly profitable
- No trade ever drew down more than -25%
- Drawdown distribution:
  - 33% never below -5%
  - 31% between -5% and -10%
  - 27% between -10% and -15%

## Case Study: Rheinmetall (RHM.DE)

| Trade | Entry | Exit | Result |
|---|---|---|---|
| Trade 1 | May 2024 @ 538 | Stopped Jun 2024 @ 477 | -11.5% |
| Trade 2 | Aug 2024 @ 541 | Exited Sep 2024 @ 485 | -10.3% |
| Trade 3 | Dec 2024 @ 615 | Exited Oct 2025 @ 1,653 | +169.0% |

- **Net P&L on RHM:** +EUR 18,867 from EUR 20,000 initial capital
- **Lesson:** System failed twice before catching the +169% winner

## Known Limitations

- **Survivorship bias:** Tested on stocks existing today; realistic CAGR adjustment -2 to -4%
- **No point-in-time fundamental data** in backtest (CAN SLIM uses price-based quality proxies)
- **Currency effects ignored:** GBP, CHF, SEK, NOK, DKK, PLN treated as EUR
- **Universe constructed from current index constituents** (look-ahead bias)
- **Realistic adjusted expectations:** CAGR ~14-17%, Sharpe ~0.8-1.0

## Disclaimer

This is educational research, not investment advice. Past performance does not guarantee future results. Backtest results are subject to known biases described above.
