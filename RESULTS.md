# Backtest Results & Strategy Analysis

## Strategy Overview

- **Pan-European small/mid-cap momentum + quality strategy**
- **Universe:** 753 stocks across 16 European countries
- **Five strategy modes** (`momentum`, `canslim`, `rich_quick`, `super_rich`, `cash_machine`) sharing the same trend template, regime filter, and execution engine but differing in quality bar, position concentration, exit timing, and entry logic. See [README.md](README.md#strategy-modes) for the comparison table.
- **Funding-stress overlay** (super_rich only, opt-in per mode): blocks new entries when the 14-day mean per-8h BTC perp funding rate exceeds 5 bp. Walk-forward validated 2020-2025.
- **Position sizing:** 1-2% risk per trade depending on mode; per-mode position cap (5-15)
- **Exit:** tiered (hard stop -> regime-off 10w SMA -> 30w SMA trailing for most modes; 10w SMA trail for cash_machine; asymmetric stop ladder for super_rich)

## Backtest Results (2010-2026, EUR 20,000 initial capital)

### All 5 modes side-by-side

| Metric            | Momentum | CAN SLIM | Rich Quick | Super Rich (overlay ON) | Cash Machine |
|-------------------|---------:|---------:|-----------:|------------------------:|-------------:|
| Final equity (EUR)| 372,241  | 422,169  | 360,364    | **~1,005,800**          | 297,687      |
| CAGR              | +19.7%   | +20.6%   | +19.5%     | **+27.2%**              | +18.1%       |
| Max Drawdown      | -31.5%   | -26.5%   | -31.7%     | **-23.9%**              | -26.7%       |
| Sharpe Ratio      | 1.02     | 1.12     | 0.97       | **1.27**                | 0.92         |
| Sortino Ratio     | 1.21     | 1.32     | 1.11       | **1.66**                | 1.02         |
| Calmar Ratio      | 0.63     | 0.78     | 0.61       | **1.14**                | 0.68         |
| Profit Factor     | 2.56     | 4.26     | 2.45       | 3.72                    | 1.85         |
| Total Trades      | 345      | 323      | 155        | 144                     | 1,034        |
| Win Rate          | 39.4%    | 42.7%    | 38.1%      | 39.6%                   | 31.5%        |
| Avg Win           | +44.3%   | +41.4%   | +50.1%     | +50.2%                  | +26.0%       |
| Avg Loss          | -9.3%    | -7.9%    | -8.1%      | -6.0%                   | -5.2%        |

**super_rich without the overlay**: CAGR +20.8%, max DD -27.7%, Sharpe 1.00. The funding-stress overlay (5 bp / 14 d, walk-forward picked) adds +6.4pp CAGR and 3.8pp of drawdown improvement on top of that.

### CAN SLIM Mode — annual returns (baseline reference)

| Year | Return |
|------|-------:|
| 2010 | +16.1% |
| 2011 | -4.3%  |
| 2012 | +7.1%  |
| 2013 | +52.5% |
| 2014 | -13.6% |
| 2015 | +41.1% |
| 2016 | +6.1%  |
| 2017 | +54.9% |
| 2018 | -6.0%  |
| 2019 | +24.5% |
| 2020 | +25.2% |
| 2021 | +49.4% |
| 2022 | -18.9% |
| 2023 | +8.4%  |
| 2024 | +43.1% |
| 2025 | +42.9% |
| 2026 | +9.8%  |

### Exit Reason Breakdown (CAN SLIM)

| Exit Reason | Count |
|---|---:|
| REGIME_OFF_10W | 147 |
| BELOW_30W_SMA | 103 |
| HARD_STOP | 63 |

### Trade Profile (Max Adverse Excursion, CAN SLIM)

- Winners avg max drawdown: -4.3%
- Losers avg max drawdown: -7.3%
- 77% of losers were briefly profitable
- No trade ever drew down more than -25%
- Drawdown distribution: 33% never below -5%, 31% between -5% and -10%, 27% between -10% and -15%

## Funding-Stress Overlay (super_rich)

The dominant alpha source in 2021-2025. Implemented as a binary "block new entries when crypto leverage is overheated" rule using the BTC perpetual funding rate from CoinDesk's CCIX/Binance data.

### Walk-Forward Validation

Anchored at 2020-01-01: train on data through end of (Y-1), pick the best (threshold, window) cell from a 5×3 grid by training-period CAGR uplift, apply to year Y. All 5 folds independently picked the same parameterisation: **5 bp / 14 d**.

| Fold Y | Best params | Train Δ CAGR | Base CAGR (Y) | Overlay CAGR (Y) | Test Δ |
|--------|-------------|-------------:|--------------:|-----------------:|-------:|
| 2021   | 5bp/14d     | +9.02pp      | +38.6%        | +100.3%          | **+61.65pp** |
| 2022   | 5bp/14d     | +31.39pp     | -19.0%        | +6.7%            | +25.71pp |
| 2023   | 5bp/14d     | +28.60pp     | -2.1%         | -0.9%            | +1.20pp  |
| 2024   | 5bp/14d     | +20.98pp     | +24.5%        | +46.0%           | +21.54pp |
| 2025   | 5bp/14d     | +21.11pp     | +18.9%        | +22.8%           | +3.91pp  |

**Aggregate: 5/5 folds positive, mean test Δ CAGR +22.80pp, mean test ΔDD +3.6pp.**

The critical fold is **2021**: training data was 2020 alone (only 12 months, COVID era, no leverage blow-off). Just 3/15 cells helped on training but the algorithm still picked 5 bp / 14 d. That out-of-sample pick delivered +61.65pp uplift on year 2021.

### Per-mode applicability (walk-forward + sweep)

| Mode | Verdict | Default | Reason |
|------|---------|---------|--------|
| `super_rich` | **VALIDATED** | **ON at 5bp/14d** | 5/5 folds positive OOS |
| `rich_quick` | **REFUTED** | OFF | 2/5 folds positive, mean test Δ -2.22pp |
| `canslim`   | not WF-tested | OFF | sweep mean +0.16pp; CAN SLIM quality screen already filters similar entries |
| `momentum`  | not WF-tested | OFF | sweep mean +0.39pp |
| `cash_machine` | not WF-tested | OFF | sweep mean +0.01pp; high frequency washes the signal |

The funding overlay is a super_rich-specific signal because super_rich's pattern-recognition entries (VCP, Cup&Handle, Pocket Pivot) cluster at late-cycle blow-offs — exactly when funding spikes. Other modes have different failure modes that don't align with the funding signal.

### Buy-and-hold sanity check (2021-2025 walk-forward window, annualised)

| Series                          | CAGR    | α vs DAX     |
|---------------------------------|--------:|-------------:|
| DAX (^GDAXI) buy-and-hold       | +12.29% | --           |
| `super_rich` baseline           | +13.00% | +0.71pp/yr   |
| `super_rich` + funding overlay  | **+32.85%** | **+20.56pp/yr** |

The +20pp/yr alpha is genuine, not beta. Cleanest evidence is **2022**: DAX -12.3%, baseline -16.7%, overlay **+7.1%** in the same year — overlay outperformed in a down market, and the gate fired 0% of days that year. The 2022 alpha is the *carryover* effect of having different positions because the gate had blocked late-2021 entries.

**Honest caveat:** super_rich without the overlay only beat DAX by +0.71pp/yr in 2021-2025 — a sharp drop from the 2010-2019 era when super_rich alone crushed DAX in many years (+56pp in 2013, +48pp in 2017, +35pp in 2015). The overlay is the dominant alpha source for the recent half-decade. If the overlay degrades, the strategy's recent track record collapses to roughly DAX-with-extra-volatility.

## Case Study: Rheinmetall (RHM.DE) — CAN SLIM mode

| Trade | Entry | Exit | Result |
|-------|-------|------|--------|
| Trade 1 | May 2024 @ 538 | Stopped Jun 2024 @ 477 | -11.5% |
| Trade 2 | Aug 2024 @ 541 | Exited Sep 2024 @ 485 | -10.3% |
| Trade 3 | Dec 2024 @ 615 | Exited Oct 2025 @ 1,653 | +169.0% |

- **Net P&L on RHM:** +EUR 18,867 from EUR 20,000 initial capital
- **Lesson:** System failed twice before catching the +169% winner

## Known Limitations

- **Survivorship bias:** Tested on stocks existing today; realistic CAGR adjustment -2 to -4pp. The funding overlay's *relative* uplift on super_rich should be more robust to this (the gate acts on entry timing, not stock selection), but absolute CAGR numbers are still inflated.
- **No point-in-time fundamental data** in backtest (CAN SLIM uses price-based quality proxies; SimFin integration in `external_data.py` is available for offline research but not wired into the backtest's quality filter).
- **Currency effects ignored:** GBP, CHF, SEK, NOK, DKK, PLN treated as EUR.
- **Universe constructed from current index constituents** (look-ahead bias).
- **Funding-overlay history is short** — 2019-09 to 2026-05 (~6 years). Walk-forward used 5 folds (2021-2025). Robust enough to pick parameters but not enough to claim regime invariance.
- **Realistic adjusted expectations:** CAGR ~14-17% for momentum/canslim, somewhat lower for the more aggressive modes. The funding overlay's super_rich uplift should survive the bias adjustments but not all of it.

## Disclaimer

This is educational research, not investment advice. Past performance does not guarantee future results. Backtest results are subject to known biases described above.
