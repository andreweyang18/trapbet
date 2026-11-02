"""Figures for Experiment 1 (2025 MLB fantasy-score backtest) from data/bet_log.csv.

Writes to figures/:
  hit_rate_by_split.png  horizontal bars, Wilson 95% CI, n on every bar, breakeven lines
  hit_rate_by_stake.png  Hitters / Pitchers, each >= $100 vs < $100, CI bars, n labels
  hit_rate_by_month.png  Mar-Oct 2025 monthly hit rate, CI bars, n labels, no smoothing
Style matches analysis/beta_binomial.py (same palette, surface and ink tokens).

Usage:  python analysis/make_figures.py [path/to/bet_log.csv]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console defaults to cp1252

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from beta_binomial import BREAKEVEN_CONV, BREAKEVEN_REAL, load, wilson  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"

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


def _rate(d: pd.DataFrame, mask) -> tuple[int, int, float, float, float]:
    sub = d[mask]
    n, w = int(len(sub)), int(sub["result"].sum())
    lo, hi = wilson(w, n)
    return w, n, (w / n if n else np.nan), lo, hi


def _breakeven_lines(ax, axis: str, ymax_frac: float = 0.98):
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


def split_masks(d: pd.DataFrame) -> list[tuple[str, pd.Series]]:
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


def fig_by_split(d: pd.DataFrame, out: Path) -> Path:
    rows = [(name, *_rate(d, m)) for name, m in split_masks(d)]
    names = [r[0] for r in rows]
    rates = np.array([r[3] for r in rows])
    err = np.array([[r[3] - r[4] for r in rows], [r[5] - r[3] for r in rows]])
    y = np.arange(len(rows))

    fig, ax = _fig(9, 5.6)
    ax.barh(y, rates, height=0.58, color=SERIES[0], zorder=2)
    ax.errorbar(rates, y, xerr=err, fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3, zorder=3)
    for yi, (name, w, n, r, lo, hi) in zip(y, rows):
        ax.text(hi + 0.012, yi, f"{w}/{n}  ({r:.1%})", color=INK, fontsize=8, va="center")
    ax.set_yticks(y, names)
    ax.invert_yaxis()
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_xlim(0, 1.0)
    ax.xaxis.set_major_formatter(PCT)
    ax.grid(axis="x", color=GRID, lw=0.8)
    _breakeven_lines(ax, "x")
    ax.set_title("Hit rate by split, 2025 MLB fantasy-score props (W/N, Wilson 95% CI)",
                 color=INK, fontsize=11, loc="left", pad=22)
    ax.set_xlabel("Hit rate", color=INK2)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def fig_by_stake(d: pd.DataFrame, out: Path) -> Path:
    groups = [("Hitters", d["role"] == "hitter"), ("Pitchers (control)", d["role"] == "pitcher")]
    tiers = [("Stake ≥ $100", d["high_conf"] == 1, SERIES[0]),
             ("Stake < $100", d["high_conf"] == 0, SERIES[1])]
    fig, ax = _fig(8, 5)
    x = np.arange(len(groups))
    width = 0.34
    for j, (tname, tmask, color) in enumerate(tiers):
        xs = x + (j - 0.5) * (width + 0.02)
        stats = [_rate(d, gmask & tmask) for _, gmask in groups]
        rates = np.array([s[2] for s in stats])
        err = np.array([[s[2] - s[3] for s in stats], [s[4] - s[2] for s in stats]])
        ax.bar(xs, rates, width=width, color=color, label=tname, zorder=2)
        ax.errorbar(xs, rates, yerr=err, fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3, zorder=3)
        for xi, (w, n, r, lo, hi) in zip(xs, stats):
            ax.text(xi, hi + 0.015, f"{w}/{n}\n{r:.1%}", color=INK, fontsize=8, ha="center", va="bottom")
    ax.set_xticks(x, [g[0] for g in groups])
    ax.set_ylim(0, 1.0)
    ax.set_xlim(-0.6, len(groups) + 0.15)   # right margin holds the breakeven labels
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="y", color=GRID, lw=0.8)
    _breakeven_lines(ax, "y")
    ax.set_title("Hit rate by role and stake tier (W/N, Wilson 95% CI)", color=INK, fontsize=11, loc="left")
    ax.set_ylabel("Hit rate", color=INK2)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper right", bbox_to_anchor=(1.0, 0.93))
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def monthly_table(d: pd.DataFrame) -> pd.DataFrame:
    dd = d.dropna(subset=["date"]).copy()
    dd["month"] = pd.to_datetime(dd["date"]).dt.to_period("M")
    g = dd.groupby("month")["result"].agg(wins="sum", n="count").reset_index()
    g["rate"] = g["wins"] / g["n"]
    ci = np.array([wilson(int(w), int(n)) for w, n in zip(g["wins"], g["n"])])
    g["lo"], g["hi"] = ci[:, 0], ci[:, 1]
    return g


def fig_by_month(d: pd.DataFrame, out: Path) -> Path:
    g = monthly_table(d)
    x = np.arange(len(g))
    fig, ax = _fig(9, 4.8)
    ax.errorbar(x, g["rate"], yerr=[g["rate"] - g["lo"], g["hi"] - g["rate"]], fmt="o",
                color=SERIES[0], ecolor=INK2, elinewidth=1.2, capsize=3, markersize=7, zorder=3)
    for xi, (w, n, r, hi) in enumerate(zip(g["wins"], g["n"], g["rate"], g["hi"])):
        ax.text(xi, hi + 0.02, f"{int(w)}/{int(n)}", color=INK, fontsize=8, ha="center", va="bottom")
    ax.set_xticks(x, [p.strftime("%b %Y") for p in g["month"]])
    ax.set_ylim(0, 1.05)
    ax.set_xlim(-0.6, len(g) + 0.9)   # right margin holds the breakeven labels
    ax.yaxis.set_major_formatter(PCT)
    ax.grid(axis="y", color=GRID, lw=0.8)
    _breakeven_lines(ax, "y")
    ax.set_title("Monthly hit rate, 2025 season (W/N above each point, Wilson 95% CI, no smoothing)",
                 color=INK, fontsize=11, loc="left")
    ax.set_ylabel("Hit rate", color=INK2)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "bet_log.csv"
    d = load(path)
    FIG_DIR.mkdir(exist_ok=True)
    for f in (fig_by_split(d, FIG_DIR / "hit_rate_by_split.png"),
              fig_by_stake(d, FIG_DIR / "hit_rate_by_stake.png"),
              fig_by_month(d, FIG_DIR / "hit_rate_by_month.png")):
        print(f"wrote {f.relative_to(ROOT)}")
    g = monthly_table(d)
    print("\nMonthly: " + " · ".join(f"{p.strftime('%b')} {int(w)}/{int(n)} ({r:.0%})"
                                   for p, w, n, r in zip(g["month"], g["wins"], g["n"], g["rate"])))


if __name__ == "__main__":
    main()
