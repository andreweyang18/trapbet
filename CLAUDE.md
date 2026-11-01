# trapbet — project context for Claude Code

My personal research tool testing whether DFS fantasy-score lines (PrizePicks/Underdog)
are mispriced relative to a fair line rebuilt from devigged sportsbook component props.
Personal use only. No commercialization. Respect operator ToS. No profit claims anywhere.

## Status (2026-11-02, v2)
- DONE: Experiment 1 data. `data/bet_log.csv` = 261 unique MLB fantasy-score props from the 2025
  season (every bet placed, incl. losses), deduped per player per game-date, voids dropped. ALL 261 DATED.
  158/261 = 60.5% (Wilson 95% CI 54–66%). Hitters 112/178 (62.9%), pitchers 46/83 (55.4%).
  Hitter unders 89/139 (64.0%). Star-list unders 14/21. ≥$100 stake 123/191 (64.4%) vs <$100 35/70 (50.0%).
  Hitters ≥$100 95/143 (66.4%) vs <$100 17/35 (48.6%). S3 filled; S1/S2/S4/S5/S6/S7 blank.
- DONE: `data/high_stake_slips.csv` — 42 slips with ≥$100 visible stake; fantasy legs 43/62 (69.4%).
- DONE: Engines built and unit-tested (61 tests), pitcher weights verified 2026-11-02, Ohtani example in window; not yet run on live lines.
  `analysis/beta_binomial.py` runs (posteriors by split + plot). Public repo: https://github.com/andreweyang18/trapbet
- NOT STARTED: ingest/ (DFS board + book odds snapshotter), Streamlit page, S1/S6 reconstruction script.

## Data rules (do not change without asking me, the project owner)
- One row per player per game-date. Same-day line movement → one row; if results differ, count as WIN
  and tag `LINE_MOVE_FLIP` in notes (report with and without).
- Fantasy-score markets only (all platforms). MLB only. Pitchers included, tagged `role=pitcher`.
  No partial-game (1–3 inning) fantasy. No tennis/NBA/soccer.
- Voided legs dropped (not the whole slip). `odds_or_payout` = 2.0 by convention (50/50 baseline);
  real DFS breakeven is 57.7%/leg on a 3x 2-pick — always report both.
- `high_conf` = 1 if total real-money stake on that prop that day ≥ $100 (free bets = $0).
- Rows tagged `BOTH_SIDES` (Schwellenbach 5/8, A. Garcia 5/23) and `DATE_TYPO?` are flagged, not resolved.
- Notes-only rows are canonical for result; screenshots are canonical for date/stake/platform.
- Platform codes: prizepicks, underdog, app_A ("Fantasy Points — Full Game"), app_B (fantasy points with American odds). I still need to map app_A/app_B to ParlayPlay/Boom.

## Rebuild
`python build_log.py` regenerates data/bet_log.csv from data/mlbbets.txt (notes), the screenshot rows
hardcoded in the script, and data/undated_fills.csv (my manual date/stake fills keyed by notes line #).
`python build_high_stake.py` regenerates data/high_stake_slips.csv.

## Next tasks, in order
1. `scripts/reconstruct_signals.py`: for all 261 dated rows, pull game logs (pybaseball / MLB stats API) to fill
   S1 (last-5 streak vs line) and S6 (opposing SP quartile by xFIP/K%). Report fill rate with n.
2. `analysis/hierarchical_players.py`: partial pooling of per-player hit rates (empirical Bayes or PyMC).
   Expect Judge 7/8 and Ohtani 4/4 to shrink toward ~70s.
3. `analysis/by_month.py`: hit rate by month on dated rows + sequential posterior plot.
4. `RESULTS.md` two-page note: what was measured, by split, with n and intervals; pitcher control as
   mechanism check; stake split; floor-not-ceiling framing; explicit list of unmeasurable signals.
5. Finish engines + ingest for live NBA run (Dec–Mar), then MLB 2027.

## Style
Honest limitations over encouragement. Every percentage next to its n. Small executable steps.
