"""MLB fantasy-score weight tables and linear scoring.

What it does: holds per-platform, per-role point weights; scores a dict of stat counts (or expected
counts, since scoring is linear); converts a line between platforms at a fixed component mix.
Assumes: hitter tables below match PrizePicks / Underdog MLB scoring as of 2025. Pitcher weights are
UNVERIFIED (see PITCHER_NOTE) and scoring a pitcher emits a UserWarning rather than failing silently.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Mapping

Platform = str  # "prizepicks" | "underdog"
Role = str      # "hitter" | "pitcher"

HITTER_STATS = ("1B", "2B", "3B", "HR", "R", "RBI", "BB", "HBP", "SB")
PITCHER_STATS = ("W", "QS", "K", "IP", "ER", "H")


@dataclass(frozen=True)
class WeightTable:
    platform: Platform
    role: Role
    weights: Mapping[str, float]
    verified: bool
    note: str = field(default="")


PITCHER_NOTE = (
    "TODO: verify against current PrizePicks and Underdog MLB pitcher scoring. Values are Andrew's "
    "recollection (W 6, QS 4, K 3, IP 3 per inning = 1 per out, ER -3); H -0.6 is the least certain. "
    "Do not treat pitcher fair lines as validated until this flag is True."
)

_TABLES: dict[tuple[Platform, Role], WeightTable] = {
    ("prizepicks", "hitter"): WeightTable(
        "prizepicks", "hitter",
        {"1B": 3, "2B": 5, "3B": 8, "HR": 10, "R": 2, "RBI": 2, "BB": 2, "HBP": 2, "SB": 5},
        verified=True),
    ("underdog", "hitter"): WeightTable(
        "underdog", "hitter",
        {"1B": 3, "2B": 6, "3B": 8, "HR": 10, "R": 2, "RBI": 2, "BB": 3, "HBP": 3, "SB": 4},
        verified=True),
    ("prizepicks", "pitcher"): WeightTable(
        "prizepicks", "pitcher",
        {"W": 6, "QS": 4, "K": 3, "IP": 3, "ER": -3, "H": -0.6},
        verified=False, note=PITCHER_NOTE),
    ("underdog", "pitcher"): WeightTable(
        "underdog", "pitcher",
        {"W": 6, "QS": 4, "K": 3, "IP": 3, "ER": -3, "H": -0.6},
        verified=False, note=PITCHER_NOTE),
}


def weights(platform: Platform, role: Role) -> WeightTable:
    """Return the weight table for (platform, role). Raises KeyError for unknown combinations."""
    key = (platform.lower(), role.lower())
    if key not in _TABLES:
        raise KeyError(f"no weight table for platform={platform!r} role={role!r}; "
                       f"known: {sorted(_TABLES)}")
    return _TABLES[key]


def score(components: Mapping[str, float], platform: Platform, role: Role) -> float:
    """Linear fantasy score: sum(weight[stat] * components[stat]).

    `components` may hold integer counts (a realised game) or expected counts (a fair line), since
    the score is linear. IP is in innings (6.667 = 6 2/3; 1 point per out). Unknown stat keys raise
    KeyError so a mislabeled input cannot silently score zero. Missing stats count as 0.
    """
    table = weights(platform, role)
    if not table.verified:
        warnings.warn(f"{table.platform}/{table.role} weights are unverified: {table.note}",
                      UserWarning, stacklevel=2)
    unknown = set(components) - set(table.weights)
    if unknown:
        raise KeyError(f"unknown stat(s) {sorted(unknown)} for {table.platform}/{table.role}")
    return float(sum(table.weights[k] * float(v) for k, v in components.items()))


def convert_line(line: float, from_platform: Platform, to_platform: Platform,
                 components: Mapping[str, float], role: Role = "hitter") -> float:
    """Convert a fantasy-score line between platforms by proportional scaling.

    Assumes the line scales with the player's expected score under each weight table at the given
    component mix: line_to = line_from * score_to / score_from. Raises ZeroDivisionError if the
    from-platform expected score is 0.
    """
    s_from = score(components, from_platform, role)
    s_to = score(components, to_platform, role)
    if s_from == 0:
        raise ZeroDivisionError("expected score on from_platform is 0; cannot scale line")
    return float(line) * s_to / s_from
