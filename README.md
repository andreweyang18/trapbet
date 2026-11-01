# trapbet

Personal research tool testing whether DFS fantasy-score lines (PrizePicks / Underdog) are mispriced
relative to a fair line rebuilt from devigged sportsbook component props. MLB 2025 backtest first;
live capture planned later. Personal use only. No commercialization. Respects operator ToS.
This repo makes no profit claims; it measures hit rates against stated breakevens and reports intervals.

## Status (2026-11-02)

| Component | State |
|---|---|
| Backtest data (Experiment 1) | **Complete.** `data/bet_log.csv`: 261 MLB fantasy-score props from 2025, all dated, 158/261 hit (60.5%, Wilson 95% CI 54–66%). Hitters 112/178 (62.9%), pitchers 46/83 (55.4%). `data/high_stake_slips.csv`: 42 slips with ≥$100 stake. Both regenerate byte-identically from `build_log.py` / `build_high_stake.py`. |
| Beta-binomial analysis | **Runs.** `analysis/beta_binomial.py` prints posteriors by split and saves [a plot](analysis/beta_binomial_posteriors.png). Beta(5.77, 4.23) prior; P(p > 57.7%) = 0.82 for all 261 props, 0.35 for the 83-prop pitcher control. |
| Engines (scoring, devig, fair_line, simulate, trap, sizing) | **Not written.** Spec exists in CLAUDE.md; no code, tests, or examples in the repo. Nothing has been validated on live lines. |
| Ingestion (DFS board + book odds snapshotter) | Not started. |
| Streamlit UI | Not started. |
| S1 / S6 signal reconstruction from game logs | Not started. |

Results and limitations: [RESULTS.md](RESULTS.md). Working rules and task order: [CLAUDE.md](CLAUDE.md).

## Rebuild the data

```
python build_log.py          # data/mlbbets.txt + screenshot rows + data/undated_fills.csv -> data/bet_log.csv
python build_high_stake.py   # -> data/high_stake_slips.csv
python analysis/beta_binomial.py
```

Requires Python 3.10+, pandas, scipy, matplotlib.

## Breakeven convention

`odds_or_payout` is 2.0 in the log (50/50 baseline). Real DFS breakeven on a 3x two-pick is 57.7% per leg.
Every rate is reported against both, next to its n.
