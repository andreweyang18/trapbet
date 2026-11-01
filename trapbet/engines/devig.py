"""Odds conversion and vig removal.

What it does: American <-> implied probability; two-way devig (multiplicative, power); one-sided
devig given an assumed hold; per-leg breakeven for an n-leg parlay paying payout_mult.
ASSUMPTION, not a result: one-sided markets (only one side offered) are devigged as
fair = implied / (1 + hold) with an *assumed* hold, i.e. the multiplicative convention. The additive
alternative, fair = implied - hold / 2, gives a lower fair line (about 7.4 vs 7.66 in the Ohtani
example). The choice only matters when one side of a market is available; with real two-way prices
the two conventions mostly cancel, and the live snapshotter will capture both sides. Both are
exposed via devig_one_sided(method=...) so the alternative is one keyword away.
"""
from __future__ import annotations

from scipy.optimize import brentq


def american_to_implied(a: float) -> float:
    """Implied probability of American odds `a` (vig included). -130 -> 0.5652, +150 -> 0.4."""
    a = float(a)
    if a == 0 or -100 < a < 100:
        raise ValueError(f"American odds must be <= -100 or >= +100, got {a}")
    return -a / (-a + 100.0) if a < 0 else 100.0 / (a + 100.0)


def implied_to_american(p: float) -> float:
    """American odds for implied probability p in (0, 1). p >= 0.5 gives negative odds."""
    p = float(p)
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {p}")
    return -100.0 * p / (1.0 - p) if p >= 0.5 else 100.0 * (1.0 - p) / p


def devig_multiplicative(a: float, b: float) -> tuple[float, float]:
    """Two-way multiplicative devig: each implied prob divided by their sum. Returns (fair_a, fair_b)."""
    pa, pb = american_to_implied(a), american_to_implied(b)
    s = pa + pb
    return pa / s, pb / s


def devig_power(a: float, b: float) -> tuple[float, float]:
    """Two-way power devig: find k with pa**k + pb**k = 1. Returns (fair_a, fair_b).

    Shrinks the favourite less and the longshot more than the multiplicative method.
    """
    pa, pb = american_to_implied(a), american_to_implied(b)
    k = brentq(lambda k: pa ** k + pb ** k - 1.0, 1e-3, 1e3)
    return pa ** k, pb ** k


def fair_prob_two_way(a: float, b: float, method: str = "multiplicative") -> float:
    """Fair probability of side `a` in a two-way market priced a / b."""
    if method == "multiplicative":
        return devig_multiplicative(a, b)[0]
    if method == "power":
        return devig_power(a, b)[0]
    raise ValueError(f"unknown method {method!r}; use 'multiplicative' or 'power'")


def devig_one_sided(implied: float, hold: float, method: str = "multiplicative") -> float:
    """Fair probability for a market where only one side is offered, given an assumed hold.

    method="multiplicative" (default): total book implied = 1 + hold, removed proportionally,
    fair = implied / (1 + hold). method="additive": each side carries half the overround,
    fair = implied - hold / 2. See the module docstring: this is an assumption, not a result.
    """
    if hold < 0:
        raise ValueError("hold must be >= 0")
    if not 0.0 < implied < 1.0:
        raise ValueError(f"implied must be in (0, 1), got {implied}")
    if method == "multiplicative":
        return float(implied) / (1.0 + float(hold))
    if method == "additive":
        fair = float(implied) - float(hold) / 2.0
        if fair <= 0.0:
            raise ValueError(f"additive devig gives fair <= 0 for implied={implied}, hold={hold}")
        return fair
    raise ValueError(f"unknown method {method!r}; use 'multiplicative' or 'additive'")


def breakeven_per_leg(payout_mult: float, n_legs: int) -> float:
    """Per-leg hit probability at which an n-leg slip paying payout_mult-to-stake breaks even,
    assuming independent legs: (1 / payout_mult) ** (1 / n_legs). 3x 2-pick -> 0.5774."""
    if payout_mult <= 0 or n_legs < 1:
        raise ValueError("payout_mult must be > 0 and n_legs >= 1")
    return (1.0 / float(payout_mult)) ** (1.0 / int(n_legs))
