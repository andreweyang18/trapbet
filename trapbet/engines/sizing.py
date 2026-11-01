"""Stake sizing: Kelly fraction, slip probability, and a capped fractional-Kelly unit count.

What it does: kelly_fraction for a bet paying b-to-1; slip_probability as the product of leg
probabilities; units() = min(fraction * Kelly, cap) / unit, so a 0.25 fraction with a 3% cap and
1% unit yields at most 3 units.
Assumes: legs are independent (slip probability multiplies); the estimated probabilities are
correct, which they are not in practice, hence the fraction and the cap. This is a research
sizing rule, not a recommendation to bet.
"""
from __future__ import annotations

from typing import Sequence


def kelly_fraction(p: float, b: float) -> float:
    """Kelly fraction (p*b - (1-p)) / b for win probability p and net odds b-to-1; floored at 0."""
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p must be in [0, 1], got {p}")
    if b <= 0:
        raise ValueError(f"b must be > 0, got {b}")
    return max(0.0, (p * b - (1.0 - p)) / b)


def slip_probability(leg_probs: Sequence[float]) -> float:
    """P(all legs hit) assuming independence."""
    if not leg_probs:
        raise ValueError("need at least one leg")
    out = 1.0
    for p in leg_probs:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"leg probability out of range: {p}")
        out *= float(p)
    return out


def units(p_slip: float, payout_mult: float, fraction: float = 0.25, cap: float = 0.03,
          unit: float = 0.01) -> tuple[float, float]:
    """(units, raw_kelly) for a slip paying payout_mult x stake (net odds payout_mult - 1).

    units = min(fraction * raw_kelly, cap) / unit, rounded to 2 decimals; 0 when there is no edge.
    """
    if payout_mult <= 1.0:
        raise ValueError("payout_mult must exceed 1 (it is total return per 1 staked)")
    if not (0.0 < fraction <= 1.0 and cap > 0 and unit > 0):
        raise ValueError("fraction in (0, 1], cap > 0, unit > 0 required")
    raw = kelly_fraction(p_slip, payout_mult - 1.0)
    staked = min(fraction * raw, cap)
    return round(staked / unit, 2), raw
