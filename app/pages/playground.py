"""Playground page: rebuild a fair fantasy-score line from component markets and simulate it."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.figures_lib import fig_histogram  # noqa: E402
from app.playground_lib import (DEFAULT_HOLD, DEFAULT_HOLD_OTHER, N_LEGS, OHTANI_EXAMPLE,  # noqa: E402
                                PAYOUT, STATS, MarketInput, run_playground)

st.title("Playground — rebuild a fair line")
st.error("Illustrative inputs. Not run on live lines. Not betting advice.")

EMPTY_MARKETS = pd.DataFrame({"stat": pd.Series([], dtype=str), "threshold": pd.Series([], dtype=float),
                              "side": pd.Series([], dtype=str), "american": pd.Series([], dtype=float),
                              "other_side": pd.Series([], dtype=float), "hold": pd.Series([], dtype=float)})
DEFAULTS = dict(platform="prizepicks", line=9.5, side="under", mix_1b=0.45, mix_2b=0.15, mix_3b=0.05,
                mix_hr=0.35, share_h=0.40, share_r=0.31, share_rbi=0.29, fb_hbp=0.05, fb_h=0.0,
                fb_r=0.0, fb_rbi=0.0, fb_bb=0.0, fb_sb=0.0, pa_mean=4.3, n_sims=200_000, seed=7)


def _init_state() -> None:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    st.session_state.setdefault("markets_df", EMPTY_MARKETS.copy())
    st.session_state.setdefault("editor_version", 0)


def _load_ohtani() -> None:
    ex = OHTANI_EXAMPLE
    st.session_state.update(platform=ex["platform"], line=ex["line"], side=ex["side"],
                            mix_1b=ex["hit_mix"][0], mix_2b=ex["hit_mix"][1], mix_3b=ex["hit_mix"][2],
                            mix_hr=ex["hit_mix"][3], share_h=ex["shares"]["H"], share_r=ex["shares"]["R"],
                            share_rbi=ex["shares"]["RBI"], fb_hbp=ex["fallbacks"]["HBP"],
                            pa_mean=ex["pa_mean"], n_sims=ex["n_sims"], seed=ex["seed"])
    st.session_state["markets_df"] = pd.DataFrame(
        [dict(stat=m.stat, threshold=m.threshold, side=m.side, american=float(m.american),
              other_side=None, hold=m.hold) for m in ex["markets"]])
    st.session_state["editor_version"] += 1


_init_state()
st.button("Load Ohtani example (PrizePicks 9.5 from three book markets)", on_click=_load_ohtani)

with st.form("playground"):
    c1, c2, c3, c4 = st.columns(4)
    platform = c1.selectbox("Platform", ["prizepicks", "underdog"], key="platform")
    c2.selectbox("Role", ["hitter"], help="Hitters only in v1; pitcher components are not modelled yet.")
    line = c3.number_input("DFS line", min_value=0.5, max_value=60.0, step=0.5, key="line")
    side = c4.selectbox("Side", ["under", "over"], key="side")

    st.markdown("**Component markets** (up to 5). Other-side odds are optional; the assumed hold is used "
                f"only when they are blank (default {DEFAULT_HOLD_OTHER}, {DEFAULT_HOLD['SB']} for SB).")
    markets_df = st.data_editor(
        st.session_state["markets_df"], num_rows="dynamic", hide_index=True, width="stretch",
        key=f"markets_editor_{st.session_state['editor_version']}",
        column_config={
            "stat": st.column_config.SelectboxColumn("stat", options=list(STATS), required=True),
            "threshold": st.column_config.NumberColumn("threshold", step=0.5, required=True),
            "side": st.column_config.SelectboxColumn("side", options=["over", "under"], required=True),
            "american": st.column_config.NumberColumn("American odds", step=5, required=True),
            "other_side": st.column_config.NumberColumn("other-side odds (optional)", step=5),
            "hold": st.column_config.NumberColumn("assumed hold", step=0.01, min_value=0.0, max_value=0.5),
        })

    st.markdown("**Hit mix** (fractions of hits; must sum to 1)")
    m1, m2, m3, m4 = st.columns(4)
    mix = (m1.slider("1B", 0.0, 1.0, step=0.01, key="mix_1b"), m2.slider("2B", 0.0, 1.0, step=0.01, key="mix_2b"),
           m3.slider("3B", 0.0, 1.0, step=0.01, key="mix_3b"), m4.slider("HR", 0.0, 1.0, step=0.01, key="mix_hr"))
    st.caption(f"Hit-mix sum: {sum(mix):.2f}")

    st.markdown("**Composite shares** (used when only an H+R+RBI market exists)")
    s1, s2, s3 = st.columns(3)
    shares = {"H": s1.number_input("H share", 0.0, 1.0, step=0.01, key="share_h"),
              "R": s2.number_input("R share", 0.0, 1.0, step=0.01, key="share_r"),
              "RBI": s3.number_input("RBI share", 0.0, 1.0, step=0.01, key="share_rbi")}

    with st.expander("Season fallbacks (per-game rates used when a stat has no market; 0 = none)"):
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        fb_inputs = {"H": f1.number_input("H", 0.0, 5.0, step=0.01, key="fb_h"),
                     "R": f2.number_input("R", 0.0, 3.0, step=0.01, key="fb_r"),
                     "RBI": f3.number_input("RBI", 0.0, 3.0, step=0.01, key="fb_rbi"),
                     "BB": f4.number_input("BB", 0.0, 3.0, step=0.01, key="fb_bb"),
                     "HBP": f5.number_input("HBP", 0.0, 1.0, step=0.01, key="fb_hbp"),
                     "SB": f6.number_input("SB", 0.0, 1.0, step=0.01, key="fb_sb")}

    p1, p2, p3 = st.columns(3)
    pa_mean = p1.number_input("PA mean", 2.0, 6.0, step=0.1, key="pa_mean")
    n_sims = p2.number_input("Simulations", 10_000, 1_000_000, step=10_000, key="n_sims")
    seed = p3.number_input("Seed", 0, 10_000, step=1, key="seed")
    submitted = st.form_submit_button("Run", type="primary")

if submitted:
    st.session_state["markets_df"] = markets_df
    problems = []
    if abs(sum(mix) - 1.0) > 0.005:
        problems.append(f"hit mix sums to {sum(mix):.2f}, not 1.")
    if abs(sum(shares.values()) - 1.0) > 0.005:
        problems.append(f"composite shares sum to {sum(shares.values()):.2f}, not 1.")
    rows = markets_df.dropna(subset=["stat", "threshold", "side", "american"])
    if len(rows) == 0:
        problems.append("add at least one component market.")
    if len(rows) > 5:
        problems.append("at most 5 component markets.")
    if problems:
        st.error(" ".join(problems))
        st.stop()
    markets = [MarketInput(r.stat, float(r.threshold), r.side, float(r.american),
                           None if pd.isna(r.other_side) else float(r.other_side),
                           None if pd.isna(r.hold) else float(r.hold)) for r in rows.itertuples()]
    fallbacks = {k: v for k, v in fb_inputs.items() if v > 0}
    try:
        res = run_playground(platform, float(line), side, markets, mix, shares, fallbacks,
                             pa_mean=float(pa_mean), n_sims=int(n_sims), seed=int(seed))
    except ValueError as e:
        st.error(f"Could not build the line: {e}")
        st.stop()

    st.subheader("Devigged markets")
    dv_show = res.devig.copy()
    dv_show["implied"] = dv_show["implied"].map("{:.4f}".format)
    dv_show["fair"] = dv_show["fair"].map("{:.4f}".format)
    dv_show["expected"] = dv_show["expected"].map("{:.4f}".format)
    st.dataframe(dv_show, hide_index=True, width="stretch")

    st.subheader("Expected components per game")
    comp_show = res.components.copy()
    comp_show["expected"] = comp_show["expected"].map("{:.4f}".format)
    st.dataframe(comp_show, hide_index=True, width="stretch")

    st.subheader("Fair line and simulation")
    a, b, c, dcol = st.columns(4)
    a.metric("Fair FS (linear)", f"{res.fair_fs:.3f}")
    b.metric("Simulated mean FS", f"{res.sim_mean:.3f}")
    c.metric(f"P(under {line})", f"{res.p_under:.4f}")
    dcol.metric(f"P(over {line})", f"{res.p_over:.4f}")
    e, f_, g, h = st.columns(4)
    e.metric(f"Breakeven per leg ({PAYOUT:.0f}x {N_LEGS}-pick)", f"{res.breakeven:.4f}")
    f_.metric(f"Edge on the {side}", f"{res.edge:+.4f}")
    g.metric("Raw Kelly (two equal legs)", f"{res.kelly:.4f}",
             help=f"Slip probability {res.p_slip:.4f} assuming an equal, independent second leg.")
    h.metric("Units (¼ Kelly, 3% cap)", f"{res.units:.2f}")
    st.pyplot(fig_histogram(res.sims, float(line), side), clear_figure=True)
    st.error("Illustrative inputs. Not run on live lines. Not betting advice.")
