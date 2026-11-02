"""Write the backtest figures for Experiment 1 to figures/.

  hit_rate_by_split.png  horizontal bars, Wilson 95% CI, W/N on every bar, breakeven lines
  hit_rate_by_stake.png  Hitters / Pitchers, each >= $100 vs < $100, CI bars, W/N labels
  hit_rate_by_month.png  Mar-Oct 2025 monthly hit rate, CI bars, W/N labels, no smoothing
Figures are built in analysis/figures_lib.py (shared with the Streamlit app); this file only
loads the log, calls those functions and saves the PNGs.

Usage:  python analysis/make_figures.py [path/to/bet_log.csv]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console defaults to cp1252
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.backtest_lib import load, monthly_table  # noqa: E402
from analysis.figures_lib import SURFACE, fig_by_month, fig_by_split, fig_by_stake  # noqa: E402

FIG_DIR = ROOT / "figures"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "bet_log.csv"
    d = load(path)
    FIG_DIR.mkdir(exist_ok=True)
    for name, fig in (("hit_rate_by_split.png", fig_by_split(d)),
                      ("hit_rate_by_stake.png", fig_by_stake(d)),
                      ("hit_rate_by_month.png", fig_by_month(d))):
        out = FIG_DIR / name
        fig.savefig(out, facecolor=SURFACE)
        print(f"wrote {out.relative_to(ROOT)}")
    g = monthly_table(d)
    print("\nMonthly: " + " · ".join(f"{p.strftime('%b')} {int(w)}/{int(n)} ({r:.0%})"
                                   for p, w, n, r in zip(g["month"], g["wins"], g["n"], g["rate"])))


if __name__ == "__main__":
    main()
