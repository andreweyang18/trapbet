"""Beta-binomial posteriors for Experiment 1 (2025 MLB fantasy-score backtest).

Prior: Beta(5.77, 4.23) -- mean 0.577 (real DFS breakeven per leg on a 3x 2-pick),
weight of 10 pseudo-observations. Posterior per split: Beta(a + wins, b + losses).

Prints, for each split: W/N, raw rate, Wilson 95% CI, posterior mean, 95% equal-tailed
credible interval, P(p > 0.577) and P(p > 0.5). Saves overlapping posterior densities to
figures/beta_binomial_posteriors.png. Computation lives in analysis/backtest_lib.py and the
figure in analysis/figures_lib.py; this file is the command-line entry point.

Usage:  python analysis/beta_binomial.py [path/to/bet_log.csv]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows console defaults to cp1252
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.backtest_lib import (BREAKEVEN_CONV, BREAKEVEN_REAL, PRIOR_A, PRIOR_B,  # noqa: E402
                                   load, summarise, table_markdown)
from analysis.figures_lib import SURFACE, fig_posteriors  # noqa: E402


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "bet_log.csv"
    d = load(path)
    t = summarise(d)
    print(f"Prior Beta({PRIOR_A}, {PRIOR_B}): mean {PRIOR_A/(PRIOR_A+PRIOR_B):.3f}, "
          f"weight {PRIOR_A+PRIOR_B:.0f} pseudo-obs. Breakevens: {BREAKEVEN_CONV:.1%} (log convention), "
          f"{BREAKEVEN_REAL:.1%} (real 3x 2-pick).\n")
    print(table_markdown(t))
    print("\nCaveats: sample is every bet placed (floor, not ceiling). Rows are not independent across splits "
          "(hitters contain hitter unders contain star unders). Star-list and stake splits are small; "
          "shrinkage toward the prior is intentional. No profit claim follows from these numbers.")
    out_dir = ROOT / "figures"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "beta_binomial_posteriors.png"
    fig_posteriors(t, len(d)).savefig(out, facecolor=SURFACE)
    print(f"\nplot -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
