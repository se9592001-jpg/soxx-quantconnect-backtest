# SMA Golden/Dead-Cross Strategy: QuantConnect Backtest Validation

## Problem Statement

A prior pandas-based analysis found that a 20/60-day SMA golden-cross signal on SOXX showed no statistically significant edge over baseline returns (t-test, p > 0.05). This project ports that signal into a QuantConnect (LEAN) algorithm to test it under realistic backtesting conditions — capital allocation, automatic slippage/commission modeling, and full equity-curve simulation — rather than the simplified return-averaging approach used in the original pandas study.

The goal isn't to prove the strategy works, but to rigorously test whether it holds up under (1) different parameter choices, (2) a different underlying asset, and (3) distinct market regimes (uptrend vs. corrections), and to report what actually happened.

## Data Source

- **Instruments:** SOXX (iShares Semiconductor ETF), QQQ (Invesco NASDAQ-100 ETF)
- **Resolution:** Daily
- **Platform:** QuantConnect LEAN Engine (cloud backtesting), USD, $100,000 starting capital
- **Full-period range:** 2021-08-02 to 2026-05-18 (~5 years)
- **Regime sub-periods:** selected from SOXX's price chart based on visually identified drawdown/recovery cycles (see Limitations)

Note on the end date: `main.py` requests an end date of 2026-07-30, but the account's organization settings reserve the most recent 90 days from the actual run date as an out-of-sample holdout (a QuantConnect anti-overfitting feature), so every backtest here was automatically capped at 2026-05-18. This also means the QuantConnect results cover a slightly shorter window than the original pandas study, which ran through 2026-07-30 — see Limitations for why this doesn't change the conclusions.

## Methodology

**Signal:** Classic golden-cross / dead-cross on two SMAs (`fast_period`, `slow_period`, exposed as QuantConnect parameters). A position is opened at 100% of equity when the fast SMA crosses above the slow SMA, and fully liquidated when it crosses back below. Cross detection uses a state-gate (`is_holding`) comparing the current fast-vs-slow relationship against the prior bar, so only genuine crossovers trigger trades, not every bar where fast > slow.

**Baseline:** A custom "Buy & Hold" equity curve is computed and plotted alongside the strategy (`initial_price` captured on the first valid bar, then `100,000 × current_price / initial_price`), rather than relying on QuantConnect's default price-only benchmark chart. This baseline is price-return only and doesn't add back dividends (see Limitations).

**Costs:** No explicit brokerage/fee model was configured. LEAN's default fee and slippage models (including `VolumeShareSlippageModel`) are applied automatically to every order, so trading costs are reflected in net results even without manual configuration. Total fees ranged from $10.89 (DeepSeek period, 5 orders) to $131.00 (SOXX 10/30, 43 orders) across the seven runs.

**Validation axes tested:**
1. **Parameter robustness** — same SOXX signal at (20,60), (10,30), (50,200)
2. **Asset generalization** — same (20,60) signal applied to QQQ
3. **Regime robustness** — same SOXX (20,60) signal isolated to three distinct market conditions: the 2022 rate-hike correction, a 2024–2025 semiconductor-sector correction, and the January–May 2025 DeepSeek-driven selloff/recovery

## Results

| Run | Period | Return | Baseline (Buy&Hold) Return | Sharpe | PSR | Max Drawdown | Win Rate | Orders |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| SOXX 20/60 (base case) | 2021-08 – 2026-05 | 72.38% | 236.50% | 0.302 | 2.88% | 36.8% | 40% | 21 |
| SOXX 10/30 | 2021-08 – 2026-05 | 90.54% | 236.50% | 0.378 | 4.21% | 36.4% | 43% | 43 |
| SOXX 50/200 | 2021-08 – 2026-05 | **257.56%** | 236.50% | **0.844** | **24.68%** | 24.7% | 100% | 7 |
| QQQ 20/60 | 2021-08 – 2026-05 | 19.50% | 99.27% | −0.069 | 0.23% | 31.5% | 36% | 23 |
| SOXX 20/60, 2022 correction | 2021-12 – 2023-07 | 1.18% | 3.75% | −0.019 | 5.68% | 32.4% | 33% | 7 |
| SOXX 20/60, 2024–25 correction | 2024-06 – 2025-08 | −10.61% | 5.58% | −0.491 | 2.03% | 36.3% | 0% | 7 |
| SOXX 20/60, DeepSeek period | 2024-11 – 2025-05 | −7.46% | −3.82% | −1.06 | 1.52% | 18.1% | 0% | 5 |

**Key observations:**

- **Baseline (buy-and-hold) beat the strategy in 6 of 7 runs.** Only the (50,200) parameter combination outperformed its own baseline, and it did so on a sample of just 7 trades — this looks more like a single fortunate combination on this specific window than a robust edge (see Limitations).
- **Strategy underperformed baseline in every isolated correction/drawdown window**, including the shortest, sharpest one (DeepSeek). This directly contradicts the intuitive expectation that a trend-following exit should provide downside protection: the strategy didn't merely under-earn relative to baseline during recoveries, it actively lost more than a passive holder in two of three regime tests.
- **Win rate collapsed to 0% in both recent correction windows** (2024–25 correction and DeepSeek) — every trade taken in those windows was a loser.
- **QQQ produced a negative Sharpe and Alpha**, a more clearly negative result than SOXX's base case, reinforcing that the signal's weak performance isn't SOXX-specific.

**On PSR (Probabilistic Sharpe Ratio):** even the strongest-looking base case (SOXX 20/60, Sharpe 0.302) has a PSR of only 2.88% — analogous to a p-value, this means there's very little statistical confidence that this Sharpe Ratio reflects a real, repeatable edge rather than chance. This lines up with the original pandas study's t-test finding (p > 0.05, no significant edge): both the significance test on raw returns and the confidence measure on the risk-adjusted return arrive at the same conclusion through independent methods.

## Interpretation

Consistent with the theoretical property of SMA crossovers as **lagging indicators** — they buy after an uptrend is already established and sell after a decline has already occurred — the strategy structurally struggles to outperform buy-and-hold on assets with strong secular uptrends (both SOXX and QQQ over this window). It also failed to provide the downside protection it's often assumed to offer: in isolated correction windows, the strategy didn't simply forgo gains relative to baseline, it lost more.

This is consistent with, and extends, the original pandas finding: the earlier analysis found no statistically significant return edge over a random-holding-period baseline (p > 0.05); this QuantConnect analysis shows that even a full portfolio simulation, with position sizing, compounding, and automatic transaction costs, doesn't surface a practical edge either, and additionally shows the strategy underperforming a naive buy-and-hold baseline specifically during the periods where a trend-following exit is theoretically supposed to help most.

## Limitations

1. **Two different "baseline" definitions across the two projects.** The original pandas study's baseline was the *average return from holding a random N-day window*, not a full buy-and-hold. This QuantConnect baseline is a true buy-and-hold equity curve. The two aren't directly comparable numbers; they answer different questions ("is the signal better than typical short-term holding periods?" vs. "would you have been better off never touching your position?"), and this project treats them as complementary rather than equivalent evidence.
2. **Pandas and QuantConnect studies don't cover identical end dates.** The pandas project's data runs through 2026-07-30, while every QuantConnect result here is capped at 2026-05-18. This isn't a coding choice: `main.py` requests 2026-07-30 as the end date, but the account's organization settings reserve the most recent 90 days (from whenever the backtest is actually run) as an out-of-sample holdout, so QuantConnect silently truncates the backtest before it ever reaches that date. Re-running with "No Holdout Period" enabled would close this gap, but that setting isn't available on this account tier. The ~2-month difference falls entirely within the already-included 2024–25 correction and DeepSeek windows, both of which the strategy already loses in, so it's unlikely that the missing 10 weeks would flip the overall conclusion.
3. **Baseline excludes dividends.** The manually-computed Buy & Hold curve is price-return only; SOXX/QQQ dividend yields (~0.5–1%/yr) aren't added back, so the reported baseline slightly understates true buy-and-hold performance.
4. **Small sample sizes in regime tests.** The three isolated regime windows produced only 5–7 trades each. This is too few for a statistically meaningful significance test (a formal t-test on n=5–7 has essentially no power), so no p-value is reported for these sub-windows — the low PSR values (1.5–5.7%) are used instead as a rough indicator that these Sharpe Ratios shouldn't be treated as reliable estimates, only as directional evidence.
5. **Regime windows were chosen by visual inspection** of SOXX's price chart (identifying drawdown start/trough/recovery points), not by an objective, pre-specified rule. This introduces a mild risk of hindsight bias in window selection, even though the *conclusion* (strategy underperforms in corrections) went against what a "cherry-picked to look good" selection would have shown.
6. **No formal walk-forward validation.** Parameters weren't optimized in-sample and tested out-of-sample; the (20,60) default was chosen a priori as a market convention, and (10,30)/(50,200) were added post hoc as robustness checks, not derived from an optimization procedure. The strong (50,200) result in particular hasn't been validated out-of-sample and shouldn't be treated as a discovered "better" parameter set without further testing on unseen data.
7. **Two-asset, single-window evidence.** SOXX and QQQ share meaningful sector overlap (both tech-heavy) and were tested over the same secular-uptrend window. The conclusion that "trend-following underperforms buy-and-hold in strong uptrends" is theoretically well-supported and observed consistently here, but generalizing it beyond these two correlated assets and this specific five-year period would require testing on a wider, more independent set of instruments and time periods.

## Running This Code

This algorithm is written for QuantConnect's LEAN engine (`from AlgorithmImports import *`) and can't be run as a standalone Python script — `AlgorithmImports` is provided by the LEAN runtime, not by a pip-installable package. To run it, use either:
- A [QuantConnect](https://www.quantconnect.com) account (free tier supports cloud backtesting), or
- [LEAN CLI](https://www.quantconnect.com/docs/v2/lean-cli) with Docker for local execution

Parameters (`fast_period`, `slow_period`) and the backtest date range (`set_start_date`/`set_end_date`) can be changed directly in `main.py`, or `fast_period`/`slow_period` overridden via QuantConnect's Parameters panel without editing code. Note that the actual end date used will still depend on the account's out-of-sample holdout setting (see Limitations #2).

## Repository

```
├── main.py              # strategy source (base case: SOXX, 20/60, requested range 2021-08–2026-07)
├── README.md
├── results/              # raw JSON backtest output for all 7 runs
└── reports/              # full QuantConnect PDF strategy reports for the two most illustrative runs (QQQ base case, SOXX DeepSeek period)
```