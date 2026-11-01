Paste this as your first message in Claude Code, from the repo root:

---
Read CLAUDE.md and RESULTS.md first. This repo is trapbet. Today's job is to get the repo into a
pushable state and verify what actually works — do not add features yet.

1. Run `python build_log.py` and `python build_high_stake.py`; confirm they regenerate data/bet_log.csv
   (267 rows, 163 wins) and data/high_stake_slips.csv (42 rows) without errors.
2. Find the engine code (trapbet/engines/*.py, tests/, examples/). Run the tests and the Ohtani example.
   Report exactly what passes, what fails, and what is missing. Do not fix anything yet — just report.
3. Based on (2), rewrite the README status line so it is true: backtest data complete; engines
   partially built / tested as described; ingestion and UI not started. Link RESULTS.md.
4. Create analysis/beta_binomial.py per CLAUDE.md task 2 and run it on data/bet_log.csv. Print a table.
5. Show me `git status` and a proposed commit message. Do not push until I say so.

Rules: no profit claims, every percentage next to its n, don't describe unbuilt things as built,
ask before changing any data rule in CLAUDE.md.
---
