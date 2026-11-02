"""Pure computation behind the Playground page: devig -> fair_line -> simulate -> sizing.

What it does: turns a list of component markets plus mixing assumptions into devigged
probabilities, expected components, a fair fantasy score, a simulated score distribution and a
capped fractional-Kelly unit count. No Streamlit import, so tests can call it directly.
Assumes: markets with an other-side price are devigged two-way (multiplicative); markets without
one use devig_one_sided with the assumed hold. Hitters only. Everything else is delegated to
trapbet.engines; nothing is duplicated here.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from trapbet.engines import devig as dv  # noqa: E402
from trapbet.engines import fair_line as fl  # noqa: E402
from trapbet.engines import simulate as sim  # noqa: E402
from trapbet.engines import sizing as sz  # noqa: E402

STATS = ("H+R+RBI", "TB", "H", "R", "RBI", "BB", "HBP", "SB")
DEFAULT_HOLD = {"SB": 0.12}
DEFAULT_HOLD_OTHER = 0.05
PAYOUT, N_LEGS = 3.0, 2


@dataclass(frozen=True)
class MarketInput:
    stat: str
    threshold: float
    side: str                      # "over" | "under"
    american: float
    other_side: Optional[float] = None   # the opposite side's American odds, if offered
    hold: Optional[float] = None         # assumed hold, used only when other_side is None

    def effective_hold(self) -> float:
        return self.hold if self.hold is not None else DEFAULT_HOLD.get(self.stat, DEFAULT_HOLD_OTHER)


@dataclass
class PlaygroundResult:
    devig: pd.DataFrame
    components: pd.DataFrame
    fair_fs: float
    sim_mean: float
    p_under: float
    p_over: float
    breakeven: float
    edge: float
    p_slip: float
    kelly: float
    units: float
    sims: np.ndarray = field(repr=False)


OHTANI_EXAMPLE = dict(
    platform="prizepicks", line=9.5, side="under",
    markets=[MarketInput("H+R+RBI", 1.5, "under", -130, None, 0.05),
             MarketInput("BB", 0.5, "over", 150, None, 0.05),
             MarketInput("SB", 0.5, "over", 400, None, 0.12)],
    hit_mix=(0.45, 0.15, 0.05, 0.35),
    shares={"H": 0.40, "R": 0.31, "RBI": 0.29},
    fallbacks={"HBP": 0.05},
    pa_mean=4.3, n_sims=400_000, seed=7,
)


def devig_market(m: MarketInput) -> dict:
    """Fair probability for the listed side of one market, plus how it was obtained."""
    implied = dv.american_to_implied(m.american)
    if m.other_side is not None:
        fair = dv.fair_prob_two_way(m.american, m.other_side)
        method, hold = "two-way multiplicative", float("nan")
    else:
        hold = m.effective_hold()
        fair = dv.devig_one_sided(implied, hold)
        method = "one-sided, fair = implied / (1 + hold)"
    prop = fl.ComponentProp(m.stat, m.threshold, m.side, fair)
    return dict(stat=m.stat, threshold=m.threshold, side=m.side, american=m.american,
                other_side=m.other_side, hold=hold, implied=implied, fair=fair, method=method,
                expected=prop.expected_count(), _prop=prop)


def run_playground(platform: str, line: float, side: str, markets: Sequence[MarketInput],
                   hit_mix: Sequence[float] | Mapping[str, float], shares: Mapping[str, float],
                   fallbacks: Mapping[str, float], pa_mean: float = 4.3, n_sims: int = 200_000,
                   seed: int = 7, payout: float = PAYOUT, n_legs: int = N_LEGS) -> PlaygroundResult:
    """Full pipeline for one hitter prop. Raises ValueError with a readable message when a
    required component has neither a market nor a fallback, or inputs are inconsistent."""
    if side not in ("over", "under"):
        raise ValueError("side must be 'over' or 'under'")
    if not markets:
        raise ValueError("add at least one component market")
    rows = [devig_market(m) for m in markets]
    props = [r.pop("_prop") for r in rows]
    devig_df = pd.DataFrame(rows)
    comps, src = fl.expected_components(props, hit_mix, shares, fallbacks, return_sources=True)
    comps_df = pd.DataFrame({"stat": list(comps), "expected": list(comps.values()),
                             "source": [src[k] for k in comps]})
    fair = fl.fair_fs(comps, platform)
    sims = sim.simulate_fs(comps, hit_mix, pa_mean=pa_mean, n=int(n_sims), seed=seed, platform=platform)
    p_under = sim.hit_probability(sims, line, "under")
    p_over = sim.hit_probability(sims, line, "over")
    p_side = p_under if side == "under" else p_over
    be = dv.breakeven_per_leg(payout, n_legs)
    p_slip = sz.slip_probability([p_side] * n_legs)
    units, kelly = sz.units(p_slip, payout)
    return PlaygroundResult(devig=devig_df, components=comps_df, fair_fs=fair, sim_mean=float(sims.mean()),
                            p_under=p_under, p_over=p_over, breakeven=be, edge=p_side - be,
                            p_slip=p_slip, kelly=kelly, units=units, sims=sims)


def run_ohtani_example() -> PlaygroundResult:
    return run_playground(**OHTANI_EXAMPLE)
