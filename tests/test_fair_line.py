import pytest
from scipy.stats import binom, poisson

from trapbet.engines import fair_line as fl
from trapbet.engines import scoring as sc

OHTANI_MIX = {"1B": 0.45, "2B": 0.15, "3B": 0.05, "HR": 0.35}
OHTANI_SHARES = {"H": 0.40, "R": 0.31, "RBI": 0.29}


@pytest.mark.parametrize("lam,thr,side", [(1.3, 1.5, "over"), (1.3, 1.5, "under"),
                                          (0.48, 0.5, "over"), (0.2, 0.5, "over"), (2.0, 2, "under")])
def test_poisson_tail_fit_recovers_known_mean(lam, thr, side):
    d = poisson(lam)
    p = d.sf(int(thr)) if side == "over" else d.cdf(int(-(-thr // 1)) - 1)
    prop = fl.ComponentProp("X", thr, side, float(p))
    assert prop.expected_count() == pytest.approx(lam, abs=1e-6)


def test_binomial_fit_recovers_known_expectation():
    n, p = 4, 0.3
    prop = fl.ComponentProp("H", 0.5, "over", float(1 - (1 - p) ** n))
    assert prop.expected_count(dist="binomial", pa=n) == pytest.approx(n * p, abs=1e-6)
    assert binom(n, p).sf(0) == pytest.approx(prop.fair_prob)


def test_component_prop_validation():
    with pytest.raises(ValueError):
        fl.ComponentProp("H", 0.5, "sideways", 0.4)
    with pytest.raises(ValueError):
        fl.ComponentProp("H", 0.5, "over", 1.0)
    with pytest.raises(ValueError):
        fl.ComponentProp("H", 0.5, "over", 0.4).expected_count(dist="binomial")


def test_expected_components_from_composite_and_fallback():
    props = [fl.ComponentProp("H+R+RBI", 1.5, "under", 0.5383),
             fl.ComponentProp("BB", 0.5, "over", 0.381),
             fl.ComponentProp("SB", 0.5, "over", 0.1786)]
    comps, src = fl.expected_components(props, OHTANI_MIX, OHTANI_SHARES, {"HBP": 0.05},
                                        return_sources=True)
    lam = props[0].expected_count()
    assert comps["HR"] == pytest.approx(0.40 * lam * 0.35)
    assert comps["1B"] == pytest.approx(0.40 * lam * 0.45)
    assert comps["R"] == pytest.approx(0.31 * lam)
    assert comps["RBI"] == pytest.approx(0.29 * lam)
    assert comps["BB"] == pytest.approx(props[1].expected_count())
    assert comps["SB"] == pytest.approx(props[2].expected_count())
    assert comps["HBP"] == 0.05
    assert src == {"1B": "composite", "2B": "composite", "3B": "composite", "HR": "composite",
                   "R": "composite", "RBI": "composite", "BB": "market", "HBP": "fallback",
                   "SB": "market"}
    assert set(comps) == set(sc.HITTER_STATS)


def test_direct_hr_market_overrides_mix_slice():
    props = [fl.ComponentProp("H", 0.5, "over", 0.7), fl.ComponentProp("HR", 0.5, "over", 0.2)]
    fb = {"R": 0.5, "RBI": 0.5, "BB": 0.3, "HBP": 0.03, "SB": 0.1}
    comps = fl.expected_components(props, OHTANI_MIX, None, fb)
    h = props[0].expected_count(); hr = props[1].expected_count()
    assert comps["HR"] == pytest.approx(hr)
    assert comps["1B"] + comps["2B"] + comps["3B"] == pytest.approx(h - hr)
    assert comps["1B"] / comps["2B"] == pytest.approx(0.45 / 0.15)


def test_tb_market_converts_to_hits_via_mix():
    props = [fl.ComponentProp("TB", 1.5, "over", 0.45)]
    fb = {"R": 0.5, "RBI": 0.5, "BB": 0.3, "HBP": 0.03, "SB": 0.1}
    comps = fl.expected_components(props, OHTANI_MIX, None, fb)
    tb = props[0].expected_count()
    tb_per_hit = 0.45 * 1 + 0.15 * 2 + 0.05 * 3 + 0.35 * 4
    assert sum(comps[k] for k in ("1B", "2B", "3B", "HR")) == pytest.approx(tb / tb_per_hit)


def test_missing_stat_raises_and_bad_mix_raises():
    with pytest.raises(ValueError, match="no market or fallback for R"):
        fl.expected_components([fl.ComponentProp("H", 0.5, "over", 0.7)], OHTANI_MIX, None, {})
    with pytest.raises(ValueError, match="sum to 1"):
        fl.expected_components([], {"1B": 0.5, "2B": 0.5, "3B": 0.5, "HR": 0.5}, None, {})


def test_fair_fs_matches_hand_computation():
    comps = {"1B": 0.28, "2B": 0.09, "3B": 0.03, "HR": 0.22, "R": 0.48, "RBI": 0.45,
             "BB": 0.48, "HBP": 0.05, "SB": 0.20}
    hand = 0.28 * 3 + 0.09 * 5 + 0.03 * 8 + 0.22 * 10 + 0.48 * 2 + 0.45 * 2 + 0.48 * 2 + 0.05 * 2 + 0.20 * 5
    assert fl.fair_fs(comps, "prizepicks") == pytest.approx(hand)
    hand_ud = 0.28 * 3 + 0.09 * 6 + 0.03 * 8 + 0.22 * 10 + 0.48 * 2 + 0.45 * 2 + 0.48 * 3 + 0.05 * 3 + 0.20 * 4
    assert fl.fair_fs(comps, "underdog") == pytest.approx(hand_ud)
