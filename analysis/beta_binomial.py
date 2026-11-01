"""Beta-binomial posteriors for Experiment 1 (2025 MLB fantasy-score backtest).

Prior: Beta(5.77, 4.23) -- mean 0.577 (real DFS breakeven per leg on a 3x 2-pick),
weight of 10 pseudo-observations. Posterior per split: Beta(a + wins, b + losses).

Reports, for each split: W/N, raw rate, Wilson 95% CI, posterior mean, 95% equal-tailed
credible interval, P(p > 0.577) and P(p > 0.5). Saves overlapping posterior densities to
figures/beta_binomial_posteriors.png.

Usage:  python analysis/beta_binomial.py [path/to/bet_log.csv]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PRIOR_A, PRIOR_B = 5.77, 4.23
BREAKEVEN_REAL = 0.577   # 3x payout on a 2-pick
BREAKEVEN_CONV = 0.5     # log convention, odds_or_payout = 2.0

ROOT = Path(__file__).resolve().parents[1]


def wilson(w, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = w / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def load(path):
    d = pd.read_csv(path)
    d["role"] = d["notes"].str.extract(r"role=(hitter|pitcher)")[0]
    return d


def splits(d):
    hit = d["role"] == "hitter"
    under = d["side"] == "under"
    return [
        ("All props",            d["result"].notna()),
        ("Hitters",              hit),
        ("Pitchers (control)",   d["role"] == "pitcher"),
        ("Hitter unders",        hit & under),
        ("Star-list unders (S3)", (d["S3_star"] == 1) & under),
        ("Stake >= $100 (high_conf)", d["high_conf"] == 1),
        # comparison row, table only (not plotted)
        ("Stake < $100", d["high_conf"] == 0),
    ]


def summarise(d):
    rows = []
    for name, mask in splits(d):
        sub = d[mask]
        n = int(len(sub)); w = int(sub["result"].sum())
        a, b = PRIOR_A + w, PRIOR_B + (n - w)
        post = stats.beta(a, b)
        lo, hi = wilson(w, n)
        rows.append(dict(
            split=name, wins=w, n=n, rate=w / n if n else float("nan"),
            wilson_lo=lo, wilson_hi=hi,
            post_mean=post.mean(), cred_lo=post.ppf(0.025), cred_hi=post.ppf(0.975),
            p_gt_577=post.sf(BREAKEVEN_REAL), p_gt_50=post.sf(BREAKEVEN_CONV),
            a=a, b=b,
        ))
    return pd.DataFrame(rows)


def print_table(t):
    print(f"Prior Beta({PRIOR_A}, {PRIOR_B}): mean {PRIOR_A/(PRIOR_A+PRIOR_B):.3f}, "
          f"weight {PRIOR_A+PRIOR_B:.0f} pseudo-obs. Breakevens: {BREAKEVEN_CONV:.1%} (log convention), "
          f"{BREAKEVEN_REAL:.1%} (real 3x 2-pick).\n")
    hdr = ["Split", "W/N", "Rate", "Wilson 95%", "Post. mean", "95% credible", "P(p>57.7%)", "P(p>50%)"]
    print("| " + " | ".join(hdr) + " |")
    print("|" + "|".join("---" for _ in hdr) + "|")
    for r in t.itertuples():
        print(f"| {r.split} | {r.wins}/{r.n} | {r.rate:.1%} | {r.wilson_lo:.1%}-{r.wilson_hi:.1%} | "
              f"{r.post_mean:.1%} | {r.cred_lo:.1%}-{r.cred_hi:.1%} | {r.p_gt_577:.2f} | {r.p_gt_50:.2f} |")
    print("\nCaveats: sample is every bet placed (floor, not ceiling). Rows are not independent across splits "
          "(hitters contain hitter unders contain star unders). Star-list and stake splits are small; "
          "shrinkage toward the prior is intentional. No profit claim follows from these numbers.")


def plot(t, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # validated categorical palette (light surface), fixed slot order
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
    surface, ink, ink2, grid, axis = "#fcfcfb", "#0b0b0b", "#5f5e58", "#e1e0d9", "#c3c2b7"

    x = np.linspace(0.30, 0.90, 601)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150, facecolor=surface)
    ax.set_facecolor(surface)
    plotted = t.iloc[:6]  # the six primary splits; the stake < $100 comparison row is table-only
    for (r, c) in zip(plotted.itertuples(), colors):
        y = stats.beta(r.a, r.b).pdf(x)
        ax.plot(x, y, color=c, lw=2, label=f"{r.split}  {r.wins}/{r.n}")
    prior = stats.beta(PRIOR_A, PRIOR_B).pdf(x)
    ax.plot(x, prior, color=ink2, lw=1.2, ls=(0, (3, 3)), label="Prior Beta(5.77, 4.23)")
    for v, lab in ((BREAKEVEN_CONV, "50% convention"), (BREAKEVEN_REAL, "57.7% real breakeven")):
        ax.axvline(v, color=axis, lw=1, zorder=0)
        ax.text(v, ax.get_ylim()[1] * 0.98, lab, color=ink2, fontsize=8, ha="right", va="top", rotation=90)

    ax.set_title("Posterior hit rate by split, 2025 MLB fantasy-score props (n = 261)",
                 color=ink, fontsize=11, loc="left")
    ax.set_xlabel("Hit rate p", color=ink2)
    ax.set_ylabel("Posterior density", color=ink2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", color=grid, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(axis)
    ax.tick_params(colors=ink2, labelsize=8)
    ax.legend(frameon=False, fontsize=8, labelcolor=ink, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, facecolor=surface)
    return out


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "bet_log.csv"
    d = load(path)
    t = summarise(d)
    print_table(t)
    (ROOT / "figures").mkdir(exist_ok=True)
    out = plot(t, ROOT / "figures" / "beta_binomial_posteriors.png")
    print(f"\nplot -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
