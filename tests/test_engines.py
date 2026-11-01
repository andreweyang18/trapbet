"""Cross-module acceptance checks required by the project brief. Per-module detail lives in
test_scoring.py, test_devig.py, test_fair_line.py, test_simulate.py, test_trap.py, test_sizing.py."""
import pytest
from scipy.stats import poisson

from trapbet.engines import devig as dv
from trapbet.engines import fair_line as fl
from trapbet.engines import simulate as sim
from trapbet.engines import sizing as sz
from trapbet.engines import trap as tp

MIX = {"1B": 0.45, "2B": 0.15, "3B": 0.05, "HR": 0.35}
COMPS = {"1B": 0.28, "2B": 0.09, "3B": 0.03, "HR": 0.22, "R": 0.48, "RBI": 0.45,
         "BB": 0.48, "HBP": 0.05, "SB": 0.20}


@pytest.mark.parametrize("a", [-130, +150, -110, +400])
def test_american_implied_round_trip(a):
    assert dv.implied_to_american(dv.american_to_implied(a)) == pytest.approx(a)


def test_devig_sums_to_one():
    assert sum(dv.devig_multiplicative(-130, +110)) == pytest.approx(1.0)
    assert sum(dv.devig_power(-130, +110)) == pytest.approx(1.0)


def test_poisson_tail_fit_recovers_known_mean():
    lam = 1.558
    prop = fl.ComponentProp("H+R+RBI", 1.5, "under", float(poisson(lam).cdf(1)))
    assert prop.expected_count() == pytest.approx(lam, abs=1e-6)


def test_fair_fs_matches_hand_computation():
    hand = 0.28 * 3 + 0.09 * 5 + 0.03 * 8 + 0.22 * 10 + (0.48 + 0.45 + 0.48 + 0.05) * 2 + 0.20 * 5
    assert fl.fair_fs(COMPS, "prizepicks") == pytest.approx(hand)


def test_simulate_mean_within_015_of_linear_and_p_under_in_unit_interval():
    sims = sim.simulate_fs(COMPS, MIX, pa_mean=4.3, n=200_000, seed=11)
    assert abs(sims.mean() - fl.fair_fs(COMPS, "prizepicks")) < 0.15
    assert 0.0 <= sim.hit_probability(sims, 9.5, "under") <= 1.0


def test_trap_score_double_weights_s5_and_treats_none_as_missing():
    assert tp.trap_score({"S5": 1, "S1": 1}) == 3
    assert tp.trap_score({"S5": None, "S1": 1, "S2": None}) == 1
    assert tp.is_candidate({"S5": None, "S1": 1, "S2": 1}) is False


def test_units_cap_at_three():
    u, _ = sz.units(sz.slip_probability([0.7, 0.7]), 3.0)
    assert u == 3.0
    assert sz.units(0.999, 3.0)[0] == 3.0
