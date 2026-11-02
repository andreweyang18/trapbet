import pytest
from trapbet.engines import trap as tp


def ctx(**kw):
    base = dict(player="X", platform="prizepicks", line=9.5)
    base.update(kw)
    return tp.PropContext(**base)


def test_star_lists_v2_and_v1():
    assert tp.STARS == {"ohtani", "judge"}
    assert tp.STARS < tp.STARS_V1 and len(tp.STARS_V1) == 9
    assert tp.is_star("Shohei Ohtani") and tp.is_star("Aaron Judge")
    assert not tp.is_star("Juan Soto") and tp.is_star("Juan Soto", "v1")
    assert tp.is_star("Ronald Acuña Jr.", "v1") and not tp.is_star("Ronald Acuña Jr.")
    assert not tp.is_star("Vladimir Guerrero Jr.") and tp.is_star("Vladimir Guerrero Jr.", "v1")
    with pytest.raises(ValueError):
        tp.is_star("Aaron Judge", "v3")


def test_all_missing_gives_all_none():
    s = tp.signals(ctx())
    assert set(s) == set(tp.SIGNAL_NAMES) and all(v is None for v in s.values())
    assert tp.trap_score(s) == 0 and tp.is_candidate(s) is False and tp.lean(ctx()) is None


def test_s1_streak_requires_all_five_same_side():
    assert tp.signals(ctx(last5=[12, 11, 10, 13, 10]))["S1"] == 1
    assert tp.signals(ctx(last5=[12, 11, 9, 13, 10]))["S1"] == 0
    assert tp.signals(ctx(last5=[12, 11, 10, 13]))["S1"] is None
    assert tp.streak_side(ctx(last5=[1, 2, 3, 4, 5])) == "under"


def test_s2_s3_s4():
    assert tp.signals(ctx(popularity_rank=25))["S2"] == 1
    assert tp.signals(ctx(popularity_rank=26))["S2"] == 0
    assert tp.signals(ctx(is_star=True))["S3"] == 1
    assert tp.signals(ctx(is_star=False))["S3"] == 0
    assert tp.signals(ctx(other_platform_line_converted=8.5))["S4"] == 1
    assert tp.signals(ctx(other_platform_line_converted=8.6))["S4"] == 0


def test_s5_gap_and_lean_direction():
    assert tp.signals(ctx(fair_fs=8.5))["S5"] == 1 and tp.lean(ctx(fair_fs=8.5)) == "under"
    assert tp.signals(ctx(fair_fs=10.5))["S5"] == 1 and tp.lean(ctx(fair_fs=10.5)) == "over"
    assert tp.signals(ctx(fair_fs=9.0))["S5"] == 0


def test_s6_matchup_and_platoon():
    assert tp.signals(ctx(opp_sp_quartile=1))["S6"] == 1 and tp.lean(ctx(opp_sp_quartile=1)) == "under"
    assert tp.signals(ctx(opp_sp_quartile=4))["S6"] == 1 and tp.lean(ctx(opp_sp_quartile=4)) == "over"
    assert tp.signals(ctx(opp_sp_quartile=2, platoon_disadvantage=False))["S6"] == 0
    assert tp.signals(ctx(opp_sp_quartile=2, platoon_disadvantage=True))["S6"] == 1


def test_s7_reverse_move_against_streak():
    over_streak = [12, 11, 10, 13, 10]
    assert tp.signals(ctx(last5=over_streak, open_line=9.0))["S7"] == 1   # line rose vs overs
    assert tp.signals(ctx(last5=over_streak, open_line=10.0))["S7"] == 0
    assert tp.signals(ctx(last5=[1, 2, 3, 4, 5], open_line=10.0))["S7"] == 1  # line fell vs unders
    assert tp.signals(ctx(last5=[12, 11, 9, 13, 10], open_line=9.0))["S7"] == 0  # no streak
    assert tp.signals(ctx(last5=over_streak))["S7"] is None
    assert tp.lean(ctx(last5=over_streak)) == "under"   # fade the streak when nothing else fires


def test_trap_score_double_weights_s5_and_ignores_none():
    assert tp.trap_score({"S5": 1}) == 2
    assert tp.trap_score({"S1": 1, "S2": None, "S5": None, "S6": 1}) == 2
    assert tp.trap_score({"S1": 1, "S5": 1, "S7": 0}) == 3
    assert tp.trap_score({k: None for k in tp.SIGNAL_NAMES}) == 0
    assert tp.trap_score({k: 1 for k in tp.SIGNAL_NAMES}) == 8


def test_is_candidate_rules():
    assert tp.is_candidate({"S5": 1}) is True                       # score 2 with S5
    assert tp.is_candidate({"S1": 1, "S2": 1}) is False             # score 2 without S5
    assert tp.is_candidate({"S1": 1, "S2": 1, "S3": 1}) is True     # score 3
    assert tp.is_candidate({"S1": 1, "S5": None, "S2": None}) is False
