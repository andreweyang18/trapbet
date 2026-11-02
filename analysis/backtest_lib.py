"""Stats helpers for Experiment 1 (2025 MLB fantasy-score backtest).

What it does: loads data/bet_log.csv with derived columns (role, S3_star_v1, month), Wilson
intervals, the Beta(5.77, 4.23) posterior, the standard split list, and a summary table.
Assumes: `result` is 0/1; `S3_star` in the CSV is the v2 (household) star definition and must
agree with trapbet.engines.trap.STARS; `high_conf` is 1 for >= $100 real-money stake.
Shared by analysis/beta_binomial.py, analysis/make_figures.py and the Streamlit app.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from trapbet.engines.trap import is_star  # noqa: E402

PRIOR_A, PRIOR_B = 5.77, 4.23
BREAKEVEN_REAL = 0.577   # 3x payout on a 2-pick
BREAKEVEN_CONV = 0.5     # log convention, odds_or_payout = 2.0
DEFAULT_LOG = ROOT / "data" / "bet_log.csv"


def wilson(w: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% interval for w successes in n trials; (nan, nan) when n == 0."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = w / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def posterior(w: int, n: int):
    """Frozen Beta posterior for w wins in n under the Beta(5.77, 4.23) prior."""
    return stats.beta(PRIOR_A + w, PRIOR_B + (n - w))


def load(path: Path | str = DEFAULT_LOG) -> pd.DataFrame:
    """bet_log.csv plus derived columns: role, S3_star_v1, month (Period). Raises if the S3_star
    column disagrees with the code's star list, so data and definition cannot drift apart."""
    d = pd.read_csv(path)
    d["role"] = d["notes"].str.extract(r"role=(hitter|pitcher)")[0]
    v2 = d["player"].map(lambda p: int(is_star(p, "v2")))
    if not (v2 == d["S3_star"]).all():
        raise ValueError("S3_star column disagrees with trap.STARS; rebuild data/bet_log.csv")
    d["S3_star_v1"] = d["player"].map(lambda p: int(is_star(p, "v1")))
    d["month"] = pd.to_datetime(d["date"]).dt.to_period("M")
    return d


def splits(d: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    """Named boolean masks in the order used by the posterior table and plot."""
    hit = d["role"] == "hitter"
    under = d["side"] == "under"
    return [
        ("All props",            d["result"].notna()),
        ("Hitters",              hit),
        ("Pitchers (control)",   d["role"] == "pitcher"),
        ("Hitter unders",        hit & under),
        ("Household-star unders (S3 v2: Ohtani, Judge)", (d["S3_star"] == 1) & under),
        ("Star list v1 (9 players) unders", (d["S3_star_v1"] == 1) & under),
        ("Stake >= $100 (high_conf)", d["high_conf"] == 1),
        # comparison row, table only (not plotted)
        ("Stake < $100", d["high_conf"] == 0),
    ]


def figure_splits(d: pd.DataFrame) -> list[tuple[str, pd.Series]]:
    """Masks for the horizontal-bar figure (adds hitter overs; labels wrap for the axis)."""
    hit = d["role"] == "hitter"
    under = d["side"] == "under"
    return [
        ("All", d["result"].notna()),
        ("Hitters", hit),
        ("Pitchers (control)", d["role"] == "pitcher"),
        ("Hitter unders", hit & under),
        ("Hitter overs", hit & (d["side"] == "over")),
        ("Household-star unders\n(S3 v2: Ohtani, Judge)", (d["S3_star"] == 1) & under),
        ("Star list v1 unders\n(9 players)", (d["S3_star_v1"] == 1) & under),
        ("Stake ≥ $100", d["high_conf"] == 1),
        ("Stake < $100", d["high_conf"] == 0),
    ]


def rate_row(d: pd.DataFrame, mask) -> dict:
    """wins, n, rate, Wilson bounds, posterior mean / credible interval / P(p > breakevens)."""
    sub = d[mask]
    n, w = int(len(sub)), int(sub["result"].sum())
    lo, hi = wilson(w, n)
    post = posterior(w, n)
    return dict(wins=w, n=n, rate=(w / n if n else float("nan")), wilson_lo=lo, wilson_hi=hi,
                post_mean=post.mean(), cred_lo=post.ppf(0.025), cred_hi=post.ppf(0.975),
                p_gt_577=post.sf(BREAKEVEN_REAL), p_gt_50=post.sf(BREAKEVEN_CONV),
                a=PRIOR_A + w, b=PRIOR_B + (n - w))


def summarise(d: pd.DataFrame, split_fn=splits) -> pd.DataFrame:
    """One row per split from `split_fn(d)` with the fields of rate_row()."""
    return pd.DataFrame([dict(split=name, **rate_row(d, m)) for name, m in split_fn(d)])


def monthly_table(d: pd.DataFrame) -> pd.DataFrame:
    """wins, n, rate and Wilson bounds per calendar month (dated rows only)."""
    dd = d.dropna(subset=["date"])
    g = dd.groupby("month")["result"].agg(wins="sum", n="count").reset_index()
    g["rate"] = g["wins"] / g["n"]
    ci = np.array([wilson(int(w), int(n)) for w, n in zip(g["wins"], g["n"])]).reshape(-1, 2)
    g["lo"], g["hi"] = ci[:, 0], ci[:, 1]
    return g


def table_markdown(t: pd.DataFrame) -> str:
    hdr = ["Split", "W/N", "Rate", "Wilson 95%", "Post. mean", "95% credible", "P(p>57.7%)", "P(p>50%)"]
    lines = ["| " + " | ".join(hdr) + " |", "|" + "|".join("---" for _ in hdr) + "|"]
    for r in t.itertuples():
        lines.append(f"| {r.split} | {r.wins}/{r.n} | {r.rate:.1%} | {r.wilson_lo:.1%}-{r.wilson_hi:.1%} | "
                     f"{r.post_mean:.1%} | {r.cred_lo:.1%}-{r.cred_hi:.1%} | {r.p_gt_577:.2f} | {r.p_gt_50:.2f} |")
    return "\n".join(lines)
