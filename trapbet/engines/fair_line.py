"""Rebuild a fair fantasy-score line from devigged sportsbook component props.

What it does: turns each component prop (stat, threshold, side, fair probability) into an expected
count by inverting a Poisson (or binomial) tail; assembles the nine hitter components
(1B, 2B, 3B, HR, R, RBI, BB, HBP, SB) from whatever markets exist plus a hit-type mix, composite
shares, and season fallbacks; recombines them linearly with the platform weight table.
Assumes: per-game stat counts are Poisson (or binomial in PAs); a push (count == integer threshold)
is a loss for both sides; when only a composite (H+R+RBI or TB) exists, its parts split by the
supplied shares / hit mix. Hitters only; pitcher components are not modelled here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from scipy.optimize import brentq
from scipy.stats import binom, poisson

from . import scoring

HIT_TYPES = ("1B", "2B", "3B", "HR")
TB_PER_HIT_TYPE = {"1B": 1.0, "2B": 2.0, "3B": 3.0, "HR": 4.0}
COMPOSITE_PARTS = ("H", "R", "RBI")
_LAM_MAX = 60.0


@dataclass(frozen=True)
class ComponentProp:
    """One devigged book market: P(`side` of `threshold` on `stat`) = fair_prob.

    stat examples: "H", "H+R+RBI", "TB", "HR", "BB", "HBP", "SB", "R", "RBI".
    """
    stat: str
    threshold: float
    side: str  # "over" | "under"
    fair_prob: float

    def __post_init__(self) -> None:
        if self.side not in ("over", "under"):
            raise ValueError(f"side must be 'over' or 'under', got {self.side!r}")
        if not 0.0 < self.fair_prob < 1.0:
            raise ValueError(f"fair_prob must be in (0, 1), got {self.fair_prob}")

    def _tail(self, dist_obj) -> float:
        """P(side wins) under a frozen scipy distribution; pushes lose for both sides."""
        if self.side == "over":
            return float(dist_obj.sf(math.floor(self.threshold)))        # P(X > threshold)
        return float(dist_obj.cdf(math.ceil(self.threshold) - 1))        # P(X < threshold)

    def expected_count(self, dist: str = "poisson", pa: int | None = None) -> float:
        """Expected per-game count whose `dist` tail matches fair_prob (solved with brentq).

        dist="poisson": returns the Poisson mean. dist="binomial": needs integer `pa` trials;
        returns pa * p. Raises ValueError if no mean in (0, 60] reproduces fair_prob.
        """
        if dist == "poisson":
            f = lambda lam: self._tail(poisson(lam)) - self.fair_prob
            lo, hi = 1e-9, _LAM_MAX
        elif dist == "binomial":
            if pa is None or int(pa) < 1:
                raise ValueError("binomial needs pa (number of trials) >= 1")
            n = int(pa)
            f = lambda p: self._tail(binom(n, p)) - self.fair_prob
            lo, hi = 1e-9, 1.0 - 1e-9
        else:
            raise ValueError(f"unknown dist {dist!r}")
        if f(lo) * f(hi) > 0:
            raise ValueError(f"cannot match fair_prob={self.fair_prob} for {self.stat} "
                             f"{self.side} {self.threshold} with {dist}")
        x = brentq(f, lo, hi, xtol=1e-10)
        return float(x) if dist == "poisson" else float(n * x)


def _as_mix(hit_mix: Mapping[str, float] | Sequence[float]) -> dict[str, float]:
    mix = dict(zip(HIT_TYPES, hit_mix)) if not isinstance(hit_mix, Mapping) else dict(hit_mix)
    if set(mix) != set(HIT_TYPES):
        raise ValueError(f"hit_mix must have keys {HIT_TYPES}, got {sorted(mix)}")
    if not math.isclose(sum(mix.values()), 1.0, abs_tol=1e-6):
        raise ValueError(f"hit_mix must sum to 1, got {sum(mix.values()):.4f}")
    return {k: float(v) for k, v in mix.items()}


def expected_components(props: Iterable[ComponentProp],
                        hit_mix: Mapping[str, float] | Sequence[float],
                        shares: Mapping[str, float] | None = None,
                        fallbacks: Mapping[str, float] | None = None,
                        *, dist: str = "poisson", pa: int | None = None,
                        return_sources: bool = False):
    """Expected 1B, 2B, 3B, HR, R, RBI, BB, HBP, SB per game.

    Priority for each stat: its own market > share of a composite market (H+R+RBI via `shares`,
    TB via `hit_mix`) > `fallbacks` (season per-game rates) > ValueError. A direct HR market
    overrides the HR slice of the hit mix; the non-HR hits then split by the renormalised
    1B/2B/3B mix. With return_sources=True also returns {stat: "market"|"composite"|"fallback"}.
    """
    mix = _as_mix(hit_mix)
    shares = dict(shares or {})
    fallbacks = dict(fallbacks or {})
    market = {p.stat: p.expected_count(dist=dist, pa=pa) for p in props}
    out: dict[str, float] = {}
    src: dict[str, str] = {}

    def pick(stat: str) -> tuple[float, str] | None:
        if stat in market:
            return market[stat], "market"
        if "H+R+RBI" in market and stat in COMPOSITE_PARTS:
            if stat not in shares:
                raise ValueError(f"H+R+RBI market present but no share for {stat}")
            return shares[stat] * market["H+R+RBI"], "composite"
        if stat == "H" and "TB" in market:
            tb_per_hit = sum(mix[k] * TB_PER_HIT_TYPE[k] for k in HIT_TYPES)
            return market["TB"] / tb_per_hit, "composite"
        if stat in fallbacks:
            return fallbacks[stat], "fallback"
        if "H+R+RBI" in fallbacks and stat in COMPOSITE_PARTS and stat in shares:
            return shares[stat] * fallbacks["H+R+RBI"], "fallback"
        return None

    for stat in ("H", "R", "RBI", "BB", "HBP", "SB"):
        got = pick(stat)
        if got is None:
            raise ValueError(f"no market or fallback for {stat}")
        out[stat], src[stat] = got

    hits = out.pop("H")
    if "HR" in market:
        hr = market["HR"]
        if hr > hits:
            raise ValueError(f"E[HR]={hr:.3f} exceeds E[H]={hits:.3f}; inconsistent markets")
        rest = {k: mix[k] for k in ("1B", "2B", "3B")}
        tot = sum(rest.values())
        for k in rest:
            out[k], src[k] = (hits - hr) * rest[k] / tot, "composite"
        out["HR"], src["HR"] = hr, "market"
    else:
        for k in HIT_TYPES:
            out[k], src[k] = hits * mix[k], src["H"]
    src.pop("H", None)
    ordered = {k: float(out[k]) for k in scoring.HITTER_STATS}
    return (ordered, {k: src[k] for k in scoring.HITTER_STATS}) if return_sources else ordered


def fair_fs(components: Mapping[str, float], platform: str, role: str = "hitter") -> float:
    """Fair fantasy score: linear recombination of expected components with the platform weights."""
    return scoring.score(components, platform, role)
