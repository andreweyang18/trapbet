import pytest
from trapbet.engines import scoring as sc


def test_hitter_tables_match_spec():
    pp = sc.weights("prizepicks", "hitter").weights
    ud = sc.weights("underdog", "hitter").weights
    assert pp == {"1B": 3, "2B": 5, "3B": 8, "HR": 10, "R": 2, "RBI": 2, "BB": 2, "HBP": 2, "SB": 5}
    assert ud == {"1B": 3, "2B": 6, "3B": 8, "HR": 10, "R": 2, "RBI": 2, "BB": 3, "HBP": 3, "SB": 4}
    assert sc.weights("prizepicks", "hitter").verified and sc.weights("underdog", "hitter").verified


def test_score_linear_hand_computation():
    comps = {"1B": 1, "2B": 1, "HR": 1, "R": 2, "RBI": 3, "BB": 1, "SB": 1}
    assert sc.score(comps, "prizepicks", "hitter") == pytest.approx(3 + 5 + 10 + 4 + 6 + 2 + 5)
    assert sc.score(comps, "underdog", "hitter") == pytest.approx(3 + 6 + 10 + 4 + 6 + 3 + 4)


def test_score_accepts_expected_counts_and_missing_stats():
    assert sc.score({"HR": 0.25}, "prizepicks", "hitter") == pytest.approx(2.5)


def test_unknown_stat_raises():
    with pytest.raises(KeyError):
        sc.score({"H": 1}, "prizepicks", "hitter")
    with pytest.raises(KeyError):
        sc.weights("draftkings", "hitter")


def test_pitcher_tables_verified_and_hand_computation():
    import warnings
    line = {"W": 1, "QS": 1, "K": 7, "IP": 6.0, "ER": 2}
    for plat in ("prizepicks", "underdog"):
        t = sc.weights(plat, "pitcher")
        assert t.verified is True and "Verified against the platform scoring pages 2026-11-02" in t.note
        assert "H" not in t.weights
    with warnings.catch_warnings():
        warnings.simplefilter("error")          # scoring a pitcher must not warn
        assert sc.score(line, "prizepicks", "pitcher") == pytest.approx(6 + 4 + 21 + 18 - 6)   # 43
        assert sc.score(line, "underdog", "pitcher") == pytest.approx(5 + 5 + 21 + 18 - 6)     # 43
    assert sc.score({"IP": 6.667}, "prizepicks", "pitcher") == pytest.approx(20.0, abs=1e-3)  # 1/out


def test_pitcher_platforms_differ_on_w_and_qs_only():
    pp = sc.weights("prizepicks", "pitcher").weights
    ud = sc.weights("underdog", "pitcher").weights
    assert set(pp) == set(ud) == set(sc.PITCHER_STATS)
    differ = {k for k in pp if pp[k] != ud[k]}
    assert differ == {"W", "QS"}
    assert (pp["W"], pp["QS"], ud["W"], ud["QS"]) == (6, 4, 5, 5)


def test_convert_line_scales_with_component_mix():
    comps = {"1B": 0.3, "2B": 0.1, "3B": 0.03, "HR": 0.2, "R": 0.5, "RBI": 0.45,
             "BB": 0.5, "HBP": 0.05, "SB": 0.2}
    pp = sc.score(comps, "prizepicks", "hitter")
    ud = sc.score(comps, "underdog", "hitter")
    assert sc.convert_line(9.5, "prizepicks", "underdog", comps) == pytest.approx(9.5 * ud / pp)
    assert sc.convert_line(9.5, "prizepicks", "prizepicks", comps) == pytest.approx(9.5)
