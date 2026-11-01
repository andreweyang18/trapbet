"""Worked example: PrizePicks hitter fantasy-score line 9.5 rebuilt from three book markets.

Inputs are illustrative, not a live capture. Acceptance window (hand calculation):
fair FS 7.5-7.7, P(under 9.5) 0.68-0.72, 3 units. If the engine lands outside the window the
script exits non-zero and says what differs; the inputs are not to be tuned toward the target.
Run from the repo root:  python examples/ohtani_example.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trapbet.engines import devig as dv                      # noqa: E402
from trapbet.engines import fair_line as fl                  # noqa: E402
from trapbet.engines import simulate as sim                  # noqa: E402
from trapbet.engines import sizing as sz                     # noqa: E402

PLATFORM, LINE, SIDE = "prizepicks", 9.5, "under"
BOOK = [  # (stat, threshold, side, american, assumed hold) -- all one-sided markets
    ("H+R+RBI", 1.5, "under", -130, 0.05),
    ("BB", 0.5, "over", +150, 0.05),
    ("SB", 0.5, "over", +400, 0.12),
]
HIT_MIX = {"1B": 0.45, "2B": 0.15, "3B": 0.05, "HR": 0.35}
SHARES = {"H": 0.40, "R": 0.31, "RBI": 0.29}
FALLBACKS = {"HBP": 0.05}
PA_MEAN, N_SIMS, SEED = 4.3, 400_000, 7
PAYOUT, N_LEGS = 3.0, 2
ACCEPT = {"fair_fs": (7.5, 7.7), "p_under": (0.68, 0.72), "units": (3.0, 3.0)}


def main() -> int:
    print(f"Shohei Ohtani, {PLATFORM} fantasy score {SIDE} {LINE} (illustrative inputs)\n")
    props = []
    print("Devigged book markets (one-sided, fair = implied / (1 + hold)):")
    for stat, thr, side, amer, hold in BOOK:
        imp = dv.american_to_implied(amer)
        fair = dv.devig_one_sided(imp, hold)
        props.append(fl.ComponentProp(stat, thr, side, fair))
        lam = props[-1].expected_count()
        print(f"  {stat:8s} {side:5s} {thr:<4} {amer:+5d}  implied {imp:.4f}  hold {hold:.2f}  "
              f"fair {fair:.4f}  -> Poisson mean {lam:.4f}")

    comps, src = fl.expected_components(props, HIT_MIX, SHARES, FALLBACKS, return_sources=True)
    print("\nExpected components per game:")
    for k, v in comps.items():
        print(f"  E[{k:3s}] = {v:.4f}  ({src[k]})")

    fair = fl.fair_fs(comps, PLATFORM)
    sims = sim.simulate_fs(comps, HIT_MIX, pa_mean=PA_MEAN, n=N_SIMS, seed=SEED, platform=PLATFORM)
    p_under = sim.hit_probability(sims, LINE, SIDE)
    be = dv.breakeven_per_leg(PAYOUT, N_LEGS)
    edge = p_under - be
    p_slip = sz.slip_probability([p_under, p_under])
    u, raw_kelly = sz.units(p_slip, PAYOUT)

    print(f"\nFair FS (linear)          {fair:.3f}")
    print(f"Simulated mean FS         {sims.mean():.3f}   (n = {N_SIMS:,}, seed {SEED})")
    print(f"P({SIDE} {LINE})            {p_under:.4f}")
    print(f"Breakeven per leg         {be:.4f}   ({PAYOUT:.0f}x {N_LEGS}-pick)")
    print(f"Edge per leg              {edge:+.4f}")
    print(f"Slip P (two equal legs)   {p_slip:.4f}   raw Kelly {raw_kelly:.4f}")
    print(f"Units (1/4 Kelly, 3% cap) {u:.2f}")

    got = {"fair_fs": fair, "p_under": p_under, "units": u}
    misses = [f"{k}={v:.4f} outside [{lo}, {hi}]" for k, v in got.items()
              for lo, hi in [ACCEPT[k]] if not lo - 1e-9 <= v <= hi + 1e-9]
    if misses:
        print("\nACCEPTANCE FAILED: " + "; ".join(misses))
        print("Stopping. Do not tune inputs; report the discrepancy.")
        return 1
    print("\nAcceptance: within hand-calculated window (fair FS 7.5-7.7, P(under) 0.68-0.72, 3 units).")
    print("These are illustrative inputs; no claim about live lines follows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
