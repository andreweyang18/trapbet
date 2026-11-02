"""Matplotlib figures for the backtest, one implementation shared by the CLI and the app.

What it does: builds (does not save) the four backtest figures and a simulation histogram with
one palette and ink/surface token set. Every rate is labeled with its W/N.
Assumes: a DataFrame from backtest_lib.load() (columns role, side, S3_star, S3_star_v1,
high_conf, result, month). Light surface only; the validated categorical palette is used in
fixed slot order and the v1 star curve shares the v2 hue, dashed, because it is the same entity
under an older definition.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from analysis.backtest_lib import (BREAKEVEN_CONV, BREAKEVEN_REAL, PRIOR_A, PRIOR_B,  # noqa: E402
                                   figure_splits, monthly_table, rate_row)

# validated categorical palette (light surface), fixed slot order; text wears ink tokens only
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SURFACE, INK, INK2, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#5f5e58", "#e1e0d9", "#c3c2b7"
PCT = matplotlib.ticker.PercentFormatter(1.0, decimals=0)


def _fig(w: float, h: float):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.set_axisbelow(True)
    return fig, ax


def _breakeven_lines(ax, axis: str):
    # the two lines sit 7.7 points apart, so their labels go on opposite sides of the lines
    for v, lab, ha in ((BREAKEVEN_CONV, "50% log convention ", "right"),
                       (BREAKEVEN_REAL, " 57.7% breakeven, 3x 2-pick", "left")):
        if axis == "x":
            ax.axvline(v, color=AXIS, lw=1, ls=(0, (4, 3)), zorder=0)
            ax.text(v, ax.get_ylim()[1], lab, color=INK2, fontsize=7.5, ha=ha, va="bottom")
        else:
            ax.axhline(v, color=AXIS, lw=1, ls=(0, (4, 3)), zorder=0)
            ax.text(ax.get_xlim()[1], v, lab.strip(), color=INK2, fontsize=7.5,
                    ha="right", va="bottom")


def fig_by_split(d: pd.DataFrame, title: str = "Hit rate by split, 2025 MLB fantasy-score props"):
    rows = [(name, rate_row(d, m)) for name, m in figure_splits(d)]
    rows = [(name, r) for name, r in rows if r["n"] > 0]
    names = [r[0] for r in rows]
    rates = np.array([r[1]["rate"] for r in rows])
    err = np.array([[r[1]["rate"] - r[1]["wilson_lo"] for r in rows],
                    [r[1]["wilson_hi"] - r[1]["rate"] for r in rows]])
    y = np.arange(len(rows))
    fig, ax = _fig(9, 5.6)
    ax.barh(y, rates, height=0.58, color=SERIES[0], zorder=2)
    ax.errorbar(rates, y, xerr=err, fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3, zorder=3)
    for yi, (name, r) in zip(y, rows):
        ax.text(r["wilson_hi"] + 0.012, yi, f"{r['wins']}/{r['n']}  ({r['rate']:.1%})",
                color=INK, fontsize=8, va="center")
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_xlim(0, 1.0)
    ax.xaxis.set_major_formatter(PCT)
    ax.grid(axis="x", color=GRID, lw=0.8)
    _breakeven_lines(ax, "x")
    ax.set_title(f"{title} (W/N, Wilson 95% CI)", color=INK, fontsize=11, loc="left", pad=22)
    ax.set_xlabel("Hit rate", color=INK2)
    fig.tight_layout()
    return fig


def fig_by_stake(d: pd.DataFrame, title: str = "Hit rate by role and stake tier"):
    groups = [("Hitters", d["role"] == "hitter"), ("Pitchers (control)", d["role"] == "pitcher")]
    tiers = [("Stake ≥ $100", d["high_conf"] == 1, SERIES[0]),
             ("Stake < $100", d["high_conf"] == 0, SERIES[1])]
    fig, ax = _fig(8, 5)
    x = np.arange(len(groups))
    width = 0.34
    for j, (tname, tmask, color) in enumerate(tiers):
        xs = x + (j - 0.5) * (width + 0.02)
        rs = [rate_row(d, gmask & tmask) for _, gmask in groups]
        rates = np.array([r["rate"] for r in rs])
        err = np.array([[r["rate"] - r["wilson_lo"] for r in rs], [r["wilson_hi"] - r["rate"] for r in rs]])
        ax.bar(xs, np.nan_to_num(rates), width=width, color=color, label=tname, zorder=2)
        ax.errorbar(xs, rates, yerr=np.nan_to_num(err), fmt="none", ecolor=INK2, elinewidth=1.2,
                    capsize=3, zorder=3)
        for xi, r in zip(xs, rs):
            if r["n"]:
                ax.text(xi, r["wilson_hi"] + 0.015, f"{r['wins']}/{r['n']}\n{r['rate']:.1%}",
                        color=INK, fontsize=8, ha="center", va="bottom")
    ax.set_xticks(x, [g[0] for g in groups])
    ax.set_ylim(0, 1.0)
    ax.set_xlim(-0.6, len(groups) + 0.15)   # right margin holds the breakeven labels
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="y", color=GRID, lw=0.8)
    _breakeven_lines(ax, "y")
    ax.set_title(f"{title} (W/N, Wilson 95% CI)", color=INK, fontsize=11, loc="left")
    ax.set_ylabel("Hit rate", color=INK2)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right", bbox_to_anchor=(1.0, 0.93))
    fig.tight_layout()
    return fig


def fig_by_month(d: pd.DataFrame, title: str = "Monthly hit rate, 2025 season"):
    g = monthly_table(d)
    x = np.arange(len(g))
    fig, ax = _fig(9, 4.8)
    ax.errorbar(x, g["rate"], yerr=[g["rate"] - g["lo"], g["hi"] - g["rate"]], fmt="o",
                color=SERIES[0], ecolor=INK2, elinewidth=1.2, capsize=3, markersize=7, zorder=3)
    for xi, (w, n, hi) in enumerate(zip(g["wins"], g["n"], g["hi"])):
        ax.text(xi, hi + 0.02, f"{int(w)}/{int(n)}", color=INK, fontsize=8, ha="center", va="bottom")
    ax.set_xticks(x, [p.strftime("%b %Y") for p in g["month"]])
    ax.set_ylim(0, 1.05)
    ax.set_xlim(-0.6, len(g) + 0.9)   # right margin holds the breakeven labels
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="y", color=GRID, lw=0.8)
    _breakeven_lines(ax, "y")
    ax.set_title(f"{title} (W/N above each point, Wilson 95% CI, no smoothing)",
                 color=INK, fontsize=11, loc="left")
    ax.set_ylabel("Hit rate", color=INK2)
    fig.tight_layout()
    return fig


def fig_posteriors(t: pd.DataFrame, n_total: int):
    """Overlapping Beta posteriors for the first seven rows of a backtest_lib.summarise() table."""
    x = np.linspace(0.30, 1.00, 701)
    fig, ax = _fig(9, 5)
    plotted = t.iloc[:7]  # six primary splits plus the v1 star list; stake < $100 is table-only
    styles = [(SERIES[0], "-"), (SERIES[1], "-"), (SERIES[2], "-"), (SERIES[3], "-"),
              (SERIES[4], "-"), (SERIES[4], (0, (5, 2))), (SERIES[5], "-")]
    for r, (c, ls) in zip(plotted.itertuples(), styles):
        if r.n == 0:
            continue
        ax.plot(x, stats.beta(r.a, r.b).pdf(x), color=c, lw=2, ls=ls, label=f"{r.split}  {r.wins}/{r.n}")
    ax.plot(x, stats.beta(PRIOR_A, PRIOR_B).pdf(x), color=INK2, lw=1.2, ls=(0, (3, 3)),
            label=f"Prior Beta({PRIOR_A}, {PRIOR_B})")
    for v, lab in ((BREAKEVEN_CONV, "50% convention"), (BREAKEVEN_REAL, "57.7% real breakeven")):
        ax.axvline(v, color=AXIS, lw=1, zorder=0)
        ax.text(v, ax.get_ylim()[1] * 0.98, lab, color=INK2, fontsize=8, ha="right", va="top", rotation=90)
    ax.set_title(f"Posterior hit rate by split, 2025 MLB fantasy-score props (n = {n_total})",
                 color=INK, fontsize=11, loc="left")
    ax.set_xlabel("Hit rate p", color=INK2)
    ax.set_ylabel("Posterior density", color=INK2)
    ax.xaxis.set_major_formatter(PCT)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right")
    fig.tight_layout()
    return fig


def fig_histogram(sims: np.ndarray, line: float, side: str, title: str = "Simulated fantasy scores"):
    """Histogram of simulated scores with the DFS line marked and the chosen side shaded."""
    sims = np.asarray(sims, dtype=float)
    hi = int(min(np.percentile(sims, 99.5), 60)) + 1
    bins = np.arange(-0.5, hi + 0.5, 1.0)
    fig, ax = _fig(9, 4.2)
    ax.hist(sims, bins=bins, color=SERIES[0], density=True, zorder=2, edgecolor=SURFACE, linewidth=0.6)
    ax.axvline(line, color=INK2, lw=1.2, ls=(0, (4, 3)), zorder=3)
    p_side = float((sims < line).mean() if side == "under" else (sims > line).mean())
    ax.text(line, ax.get_ylim()[1] * 0.97, f" line {line}  ·  P({side}) = {p_side:.3f}",
            color=INK, fontsize=8.5, ha="left", va="top")
    ax.set_title(f"{title} (n = {len(sims):,}, mean {sims.mean():.2f})", color=INK, fontsize=11, loc="left")
    ax.set_xlabel("Fantasy score", color=INK2)
    ax.set_ylabel("Share of simulations", color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8)
    fig.tight_layout()
    return fig
