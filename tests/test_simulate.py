import numpy as np
import pytest

from trapbet.engines import fair_line as fl
from trapbet.engines import simulate as sim

MIX = {"1B": 0.45, "2B": 0.15, "3B": 0.05, "HR": 0.35}
COMPS = {"1B": 0.2805, "2B": 0.0935, "3B": 0.0312, "HR": 0.2181, "R": 0.483, "RBI": 0.452,
         "BB": 0.480, "HBP": 0.05, "SB": 0.197}


def test_pa_distribution_is_clipped_and_normalised():
    ks, p = sim.pa_distribution(4.3)
    assert ks.tolist() == [2, 3, 4, 5, 6]
    assert p.sum() == pytest.approx(1.0)
    assert 3.9 < (ks * p).sum() < 4.4


def test_simulated_mean_matches_linear_fair_fs():
    sims = sim.simulate_fs(COMPS, MIX, pa_mean=4.3, n=200_000, seed=1)
    assert sims.shape == (200_000,)
    assert abs(sims.mean() - fl.fair_fs(COMPS, "prizepicks")) < 0.15
    p_under = sim.hit_probability(sims, 9.5, "under")
    assert 0.0 <= p_under <= 1.0
    assert p_under + sim.hit_probability(sims, 9.5, "over") == pytest.approx(1.0)


def test_underdog_weights_change_mean_consistently():
    sims = sim.simulate_fs(COMPS, MIX, n=100_000, seed=3, platform="underdog")
    assert abs(sims.mean() - fl.fair_fs(COMPS, "underdog")) < 0.15


def test_seed_reproducible_and_scores_nonnegative_integers():
    a = sim.simulate_fs(COMPS, MIX, n=20_000, seed=42)
    b = sim.simulate_fs(COMPS, MIX, n=20_000, seed=42)
    assert np.array_equal(a, b)
    assert a.min() >= 0 and np.all(a == np.round(a))


def test_inconsistent_inputs_raise():
    bad = dict(COMPS, R=0.1)          # E[R] < E[HR]
    with pytest.raises(ValueError):
        sim.simulate_fs(bad, MIX, n=1000, seed=0)
    too_many = dict(COMPS, BB=5.0)    # H+BB+HBP > mean PA
    with pytest.raises(ValueError):
        sim.simulate_fs(too_many, MIX, n=1000, seed=0)


def test_hit_probability_pushes_count_for_neither():
    s = np.array([8, 9, 9, 10, 11], dtype=float)
    assert sim.hit_probability(s, 9, "under") == pytest.approx(0.2)
    assert sim.hit_probability(s, 9, "over") == pytest.approx(0.4)
    with pytest.raises(ValueError):
        sim.hit_probability(s, 9, "push")
