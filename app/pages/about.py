"""About page: the question, how the engine works, links."""
import streamlit as st

st.title("About")

st.markdown("""
**The question.** Are DFS fantasy-score lines (PrizePicks, Underdog) mispriced relative to a fair line
rebuilt from devigged sportsbook component props? This project holds a 2025 MLB backtest of every
fantasy-score prop I placed that season, plus the engines I am building to rebuild fair lines for a
live test. It is personal research, not a commercial product and not betting advice, and I make no
profit claim.

**How it works.** Pull the component markets a book offers for the player (hits, H+R+RBI, walks,
stolen bases). Devig each market and invert a Poisson tail to get an expected count per game. Fill
any missing component from composite shares or season rates, then recombine with the platform's
scoring weights into a fair fantasy score. Simulate plate appearances to turn expected components
into a score distribution and P(over / under the DFS line). Score the seven trap signals, flag
candidates, and size with capped fractional Kelly.

- Code and data: [github.com/andreweyang18/trapbet](https://github.com/andreweyang18/trapbet)
- Full results, definition changes and data flags:
  [RESULTS.md](https://github.com/andreweyang18/trapbet/blob/main/RESULTS.md)

Built by Andrew Yang — Applied Mathematics, UCLA (Statistics & Data Science minor).
[LinkedIn](https://www.linkedin.com/in/andreweyang)
""")
