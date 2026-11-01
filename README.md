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
| Engines (scoring, devig, fair_line, simulate, trap, sizing) | **Built and unit-tested; worked example reproduces the hand calculation; not yet run on live lines.** `trapbet/engines/`, 61 tests in `tests/`. All four scoring tables verified 2026-11-02. |
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

Run the tests and the worked example:

```
python -m pytest -q
python examples/ohtani_example.py   # PrizePicks 9.5 from three book markets: fair FS 7.66, P(under) 0.68, 3 units (illustrative inputs)
```

Requires Python 3.10+; `pip install -r requirements.txt` (numpy, scipy, pandas, matplotlib, pytest).

## Assumptions

- **One-sided devig.** When a book offers only one side of a component market, the engine devigs it
  as fair = implied / (1 + hold) with an assumed hold (multiplicative). The additive alternative,
  fair = implied − hold / 2, gives a lower fair line (about 7.4 vs 7.66 in the Ohtani example) and
  is available as `devig_one_sided(..., method="additive")`. This choice matters only when one side
  of a market is available; with real two-way prices the conventions mostly cancel, and the live
  snapshotter will capture both sides.
- **The Ohtani example is a regression test, not a validation.** Its acceptance window was set from
  a hand calculation that uses the same devig convention, so passing it shows the code reproduces
  the arithmetic, not that the method prices lines correctly. Validation needs live lines and
  settled results.
- **Scoring tables** were verified on 2026-11-02 against the platform scoring pages. Both platforms
  have changed scoring before; re-check every table at the start of each season.

## Breakeven convention

`odds_or_payout` is 2.0 in the log (50/50 baseline). Real DFS breakeven on a 3x two-pick is 57.7% per leg.
Every rate is reported against both, next to its n.
