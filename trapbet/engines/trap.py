"""Trap signals S1..S7, lean, trap score, and candidate rule for one DFS prop.

What it does: evaluates seven binary signals from a PropContext; any signal whose inputs are
missing is None (unknown), never 0. trap_score sums the 1s with S5 (fair-line gap) counting
double; is_candidate is score >= 2 with S5 present, or score >= 3.
Assumes: `last5` are the player's last five fantasy scores (most recent last) on the same
platform scale as `line`; `other_platform_line_converted` is already converted to this platform;
`opp_sp_quartile` is 1 for the top (toughest) quartile and 4 for the bottom.
Signal definitions (from the project brief):
  S1 streak: all five of last5 on the same side of the line.
  S2 popular: popularity_rank <= 25.
  S3 star: player on the star list.
  S4 cross-platform: |line - other platform line converted| >= 1.0.
  S5 fair gap: line - fair_fs >= 1.0 (lean under) or <= -1.0 (lean over).
  S6 matchup: opposing SP top quartile (lean under) or bottom quartile (lean over),
     or platoon disadvantage.
  S7 reverse move: line moved against the streak side since open.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

GAP_THRESHOLD = 1.0
POPULAR_RANK = 25
SIGNAL_NAMES = ("S1", "S2", "S3", "S4", "S5", "S6", "S7")
S5_WEIGHT = 2


@dataclass
class PropContext:
    player: str
    platform: str
    line: float
    side: Optional[str] = None                      # side being considered, if any
    last5: Optional[Sequence[float]] = None
    popularity_rank: Optional[int] = None
    is_star: Optional[bool] = None
    other_platform_line_converted: Optional[float] = None
    fair_fs: Optional[float] = None
    opp_sp_quartile: Optional[int] = None           # 1 = toughest .. 4 = easiest
    platoon_disadvantage: Optional[bool] = None
    open_line: Optional[float] = None
    notes: dict = field(default_factory=dict)


def streak_side(ctx: PropContext) -> Optional[str]:
    """'over' / 'under' if all five of last5 sit on that side of the line; '' if no streak;
    None if last5 is missing or shorter than 5."""
    if ctx.last5 is None or len(ctx.last5) < 5:
        return None
    recent = list(ctx.last5)[-5:]
    if all(x > ctx.line for x in recent):
        return "over"
    if all(x < ctx.line for x in recent):
        return "under"
    return ""


def _s5_direction(ctx: PropContext) -> Optional[str]:
    if ctx.fair_fs is None:
        return None
    gap = ctx.line - ctx.fair_fs
    if gap >= GAP_THRESHOLD:
        return "under"
    if gap <= -GAP_THRESHOLD:
        return "over"
    return ""


def _s6_direction(ctx: PropContext) -> Optional[str]:
    if ctx.opp_sp_quartile is None and ctx.platoon_disadvantage is None:
        return None
    if ctx.opp_sp_quartile == 1:
        return "under"
    if ctx.opp_sp_quartile == 4:
        return "over"
    if ctx.platoon_disadvantage:
        return "under"
    return ""


def signals(ctx: PropContext) -> dict[str, Optional[int]]:
    """Return {S1..S7: 1, 0 or None}. None means the input needed for that signal is missing."""
    s: dict[str, Optional[int]] = {}
    streak = streak_side(ctx)
    s["S1"] = None if streak is None else int(streak != "")
    s["S2"] = None if ctx.popularity_rank is None else int(ctx.popularity_rank <= POPULAR_RANK)
    s["S3"] = None if ctx.is_star is None else int(bool(ctx.is_star))
    s["S4"] = (None if ctx.other_platform_line_converted is None
               else int(abs(ctx.line - ctx.other_platform_line_converted) >= GAP_THRESHOLD))
    d5 = _s5_direction(ctx)
    s["S5"] = None if d5 is None else int(d5 != "")
    d6 = _s6_direction(ctx)
    s["S6"] = None if d6 is None else int(d6 != "")
    if streak is None or ctx.open_line is None:
        s["S7"] = None
    elif streak == "":
        s["S7"] = 0
    else:
        moved_up = ctx.line > ctx.open_line
        moved_down = ctx.line < ctx.open_line
        s["S7"] = int((streak == "over" and moved_up) or (streak == "under" and moved_down))
    return s


def lean(ctx: PropContext) -> Optional[str]:
    """Which side the signals point to: the fair-gap direction (S5) if it fires, else the matchup
    direction (S6) if it fires, else the fade of a five-game streak (S1), else None."""
    for d in (_s5_direction(ctx), _s6_direction(ctx)):
        if d:
            return d
    streak = streak_side(ctx)
    if streak:
        return "under" if streak == "over" else "over"
    return None


def trap_score(sig: dict[str, Optional[int]]) -> int:
    """Sum of signals that are 1, with S5 weighted S5_WEIGHT. None is ignored (missing != absent)."""
    total = 0
    for name in SIGNAL_NAMES:
        v = sig.get(name)
        if v is None:
            continue
        total += (S5_WEIGHT if name == "S5" else 1) * int(bool(v))
    return total


def is_candidate(sig: dict[str, Optional[int]]) -> bool:
    """score >= 2 with S5 == 1, or score >= 3."""
    score = trap_score(sig)
    return (score >= 2 and sig.get("S5") == 1) or score >= 3
