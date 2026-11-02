"""Results page: filtered backtest headline, split table and the four figures."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.backtest_lib import (BREAKEVEN_REAL, DEFAULT_LOG, load, rate_row,  # noqa: E402
                                   summarise)
from analysis.figures_lib import fig_by_month, fig_by_split, fig_by_stake, fig_posteriors  # noqa: E402

WHAT_IT_SHOWS = """
- **Floor, not ceiling.** The sample is every bet I placed, including action I knew was low-edge.
  It is not a curated subset.
- **Pitcher control.** Pitcher props sit closer to breakeven (46/83) than hitter props (112/178),
  consistent with the mechanism I am testing: pitcher component markets are priced tighter, so a
  rebuilt fair line should disagree with the DFS line less often. One season is not proof of that.
- **Sizing tracked results.** My ≥ $100 tier beat my < $100 tier by 14 points overall
  (123/191 vs 35/70). I set stakes before results were known, but the sample is small and I did not
  pre-register the split.
- **Signals not yet measured.** Of the seven trap signals, only S3 (household stars: Ohtani, Judge)
  is filled for the backtest. S1 (recent streak) and S6 (opposing pitcher) await game-log
  reconstruction. S2, S4, S5 and S7 need line captures that do not exist for 2025.
- **S3 was redefined after the results were known.** On 2026-11-02 I narrowed the star list from nine
  players to the two household names. The v1 numbers are reported alongside v2 so the effect of the
  redefinition is visible.
- **The engine is unvalidated.** Its worked example is a regression test against my hand calculation,
  which uses the same devig convention. Passing it shows the arithmetic is reproduced, not that the
  method prices lines correctly. That needs live lines and settled results.
"""


@st.cache_data
def _load() -> pd.DataFrame:
    return load(DEFAULT_LOG)


d = _load()
months = sorted(str(m) for m in d["month"].unique())

st.title("Results — 2025 MLB fantasy-score backtest")
st.caption("261 props, all dated. Numbers frozen 2026-11-02. Every rate is shown next to its n.")

with st.sidebar:
    st.header("Filters")
    role = st.radio("Role", ["all", "hitter", "pitcher"], horizontal=True)
    side = st.radio("Side", ["all", "under", "over"], horizontal=True)
    tier = st.radio("Stake tier", ["all", "≥ $100", "< $100"], horizontal=True)
    m_lo, m_hi = st.select_slider("Month range", options=months, value=(months[0], months[-1]))
    star = st.radio("Star list", ["none", "v2 (Ohtani, Judge)", "v1 (9 players)"],
                    help="v2 and v1 restrict to props on that star list; none applies no star filter.")

mask = pd.Series(True, index=d.index)
if role != "all":
    mask &= d["role"] == role
if side != "all":
    mask &= d["side"] == side
if tier != "all":
    mask &= d["high_conf"] == (1 if tier.startswith("≥") else 0)
mask &= d["month"].astype(str).between(m_lo, m_hi)
if star.startswith("v2"):
    mask &= d["S3_star"] == 1
elif star.startswith("v1"):
    mask &= d["S3_star_v1"] == 1
f = d[mask]

if len(f) == 0:
    st.warning("No rows match these filters.")
    st.stop()

r = rate_row(f, pd.Series(True, index=f.index))
c1, c2, c3, c4 = st.columns(4)
c1.metric("W / N", f"{r['wins']} / {r['n']}")
c2.metric("Hit rate", f"{r['rate']:.1%}")
c3.metric("Wilson 95% CI", f"{r['wilson_lo']:.0%} – {r['wilson_hi']:.0%}")
c4.metric(f"P(p > {BREAKEVEN_REAL:.1%})", f"{r['p_gt_577']:.2f}",
          help="Posterior under a Beta(5.77, 4.23) prior centred on the 3x two-pick breakeven.")

st.subheader("Splits on the filtered rows")
t = summarise(f)
t = t[t["n"] > 0]
show = pd.DataFrame({
    "Split": t["split"],
    "W/N": [f"{w}/{n}" for w, n in zip(t["wins"], t["n"])],
    "Rate": t["rate"].map("{:.1%}".format),
    "Wilson 95%": [f"{lo:.1%} – {hi:.1%}" for lo, hi in zip(t["wilson_lo"], t["wilson_hi"])],
    "Post. mean": t["post_mean"].map("{:.1%}".format),
    "95% credible": [f"{lo:.1%} – {hi:.1%}" for lo, hi in zip(t["cred_lo"], t["cred_hi"])],
    "P(p > 57.7%)": t["p_gt_577"].map("{:.2f}".format),
})
st.dataframe(show, hide_index=True, width="stretch")
st.caption("Splits overlap; they are not independent samples. Breakevens: 50% by the log convention, "
           "57.7% per leg on a 3x two-pick.")

st.subheader("Figures (live, on the filtered rows)")
left, right = st.columns(2)
with left:
    st.pyplot(fig_by_split(f), clear_figure=True)
    st.pyplot(fig_by_month(f), clear_figure=True)
with right:
    st.pyplot(fig_by_stake(f), clear_figure=True)
    st.pyplot(fig_posteriors(summarise(f), len(f)), clear_figure=True)

st.subheader("What this does and doesn't show")
st.markdown(WHAT_IT_SHOWS)
st.divider()
st.caption("Every bet I placed in 2025, including losers. No profit claim.")
