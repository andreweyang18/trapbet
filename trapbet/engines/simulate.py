"""Plate-appearance Monte Carlo for a hitter's fantasy-score distribution.

What it does: simulates n games. PA ~ Poisson(pa_mean) clipped to [2, 6]; each PA is one of
out / 1B / 2B / 3B / HR / BB / HBP with per-PA probabilities scaled so the expected counts equal the
input components; a HR scores 1 R and 1 RBI; every other on-base event scores with a calibrated
P(score | on base); every non-HR hit drives in a run with a calibrated P(RBI | non-HR hit); one SB
draw per game with P = E[SB]. Returns the array of fantasy scores under the platform weights.
Assumes: PAs are independent and identically distributed within a game; at most 1 RBI per non-HR
hit and exactly 1 per HR (so E[RBI] >= E[HR] and E[R] >= E[HR] are required); at most one SB.
Hitters only. The mean of the output equals the linear fair score up to Monte Carlo noise.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np
from scipy.stats import poisson

from . import scoring
from .fair_line import HIT_TYPES, _as_mix

PA_MIN, PA_MAX = 2, 6
_CATS = ("OUT", "1B", "2B", "3B", "HR", "BB", "HBP")


def pa_distribution(pa_mean: float) -> tuple[np.ndarray, np.ndarray]:
    """Support [2..6] and probabilities of Poisson(pa_mean) clipped to that range."""
    ks = np.arange(PA_MIN, PA_MAX + 1)
    p = poisson.pmf(ks, pa_mean).astype(float)
    p[0] = poisson.cdf(PA_MIN, pa_mean)
    p[-1] = poisson.sf(PA_MAX - 1, pa_mean)
    return ks, p / p.sum()


def _calibrate(components: Mapping[str, float], mix: Mapping[str, float], mean_pa: float):
    e = {k: float(components.get(k, 0.0)) for k in scoring.HITTER_STATS}
    e_h = sum(e[k] for k in HIT_TYPES)
    e_hr = e["HR"]
    non_hr_hits = e_h - e_hr
    on_base_non_hr = non_hr_hits + e["BB"] + e["HBP"]
    per_pa = {"H": e_h / mean_pa, "BB": e["BB"] / mean_pa, "HBP": e["HBP"] / mean_pa}
    p_out = 1.0 - sum(per_pa.values())
    if p_out < 0:
        raise ValueError(f"expected H+BB+HBP={e_h + e['BB'] + e['HBP']:.3f} exceeds mean PA "
                         f"{mean_pa:.3f}; inputs inconsistent")
    p_score = (e["R"] - e_hr) / on_base_non_hr if on_base_non_hr > 0 else 0.0
    p_rbi = (e["RBI"] - e_hr) / non_hr_hits if non_hr_hits > 0 else 0.0
    for name, p in (("P(score | on base)", p_score), ("P(RBI | non-HR hit)", p_rbi)):
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"{name}={p:.3f} outside [0, 1]; E[R] and E[RBI] must be >= E[HR] "
                             f"and <= E[HR] + on-base events")
    if not 0.0 <= e["SB"] <= 1.0:
        raise ValueError("E[SB] must be in [0, 1] for a single Bernoulli draw")
    probs = np.array([p_out] + [per_pa["H"] * mix[k] for k in HIT_TYPES]
                     + [per_pa["BB"], per_pa["HBP"]])
    return probs, p_score, p_rbi, e["SB"]


def simulate_fs(components: Mapping[str, float],
                hit_mix: Mapping[str, float] | Sequence[float],
                pa_mean: float = 4.3, n: int = 200_000, seed: int | None = None,
                platform: str = "prizepicks") -> np.ndarray:
    """Simulate n fantasy scores for a hitter. See module docstring for the model.

    `hit_mix` must be consistent with the HR/1B/2B/3B split in `components` (as produced by
    fair_line.expected_components) for the simulated E[HR] to match the input.
    """
    rng = np.random.default_rng(seed)
    mix = _as_mix(hit_mix)
    ks, pk = pa_distribution(pa_mean)
    mean_pa = float((ks * pk).sum())
    probs, p_score, p_rbi, p_sb = _calibrate(components, mix, mean_pa)

    pa = rng.choice(ks, size=n, p=pk)
    u = rng.random((n, PA_MAX))
    cat = np.searchsorted(np.cumsum(probs), u, side="right")       # 0..6 per slot
    cat = np.minimum(cat, len(_CATS) - 1)
    active = np.arange(PA_MAX)[None, :] < pa[:, None]
    counts = {c: ((cat == i) & active).sum(axis=1) for i, c in enumerate(_CATS)}

    non_hr_hits = counts["1B"] + counts["2B"] + counts["3B"]
    on_base_non_hr = non_hr_hits + counts["BB"] + counts["HBP"]
    runs = counts["HR"] + rng.binomial(on_base_non_hr, p_score)
    rbi = counts["HR"] + rng.binomial(non_hr_hits, p_rbi)
    sb = (rng.random(n) < p_sb).astype(int)

    w = scoring.weights(platform, "hitter").weights
    fs = (w["1B"] * counts["1B"] + w["2B"] * counts["2B"] + w["3B"] * counts["3B"]
          + w["HR"] * counts["HR"] + w["R"] * runs + w["RBI"] * rbi
          + w["BB"] * counts["BB"] + w["HBP"] * counts["HBP"] + w["SB"] * sb)
    return fs.astype(float)


def hit_probability(sims: np.ndarray, line: float, side: str) -> float:
    """Fraction of simulated scores strictly beyond `line` on `side`. Pushes count for neither."""
    sims = np.asarray(sims, dtype=float)
    if side == "over":
        return float((sims > line).mean())
    if side == "under":
        return float((sims < line).mean())
    raise ValueError(f"side must be 'over' or 'under', got {side!r}")
