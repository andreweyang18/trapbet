import pytest
from trapbet.engines import devig as dv


@pytest.mark.parametrize("a", [-130, +150, -110, +400, -250, +100, -100])
def test_american_implied_round_trip(a):
    p = dv.american_to_implied(a)
    assert 0 < p < 1
    # +100 and -100 are both p = 0.5; the inverse returns -100 by convention
    assert dv.implied_to_american(p) == pytest.approx(a if a != 100 else -100)


def test_known_implied_values():
    assert dv.american_to_implied(-130) == pytest.approx(130 / 230)
    assert dv.american_to_implied(+150) == pytest.approx(0.4)
    assert dv.american_to_implied(+400) == pytest.approx(0.2)


def test_invalid_american_rejected():
    for bad in (0, 50, -50):
        with pytest.raises(ValueError):
            dv.american_to_implied(bad)


def test_devig_sums_to_one_both_methods():
    for a, b in ((-110, -110), (-130, +110), (+300, -400), (-150, +130)):
        pm = dv.devig_multiplicative(a, b)
        pw = dv.devig_power(a, b)
        assert sum(pm) == pytest.approx(1.0)
        assert sum(pw) == pytest.approx(1.0)
        assert pm[0] == pytest.approx(dv.fair_prob_two_way(a, b))
        assert pw[0] == pytest.approx(dv.fair_prob_two_way(a, b, "power"))


def test_symmetric_market_is_coin_flip():
    assert dv.fair_prob_two_way(-110, -110) == pytest.approx(0.5)
    assert dv.fair_prob_two_way(-110, -110, "power") == pytest.approx(0.5)


def test_power_shrinks_longshot_more_than_multiplicative():
    fav_m, dog_m = dv.devig_multiplicative(-400, +300)
    fav_p, dog_p = dv.devig_power(-400, +300)
    assert dog_p < dog_m and fav_p > fav_m


def test_one_sided_devig_multiplicative_default():
    assert dv.devig_one_sided(130 / 230, 0.05) == pytest.approx((130 / 230) / 1.05)
    assert dv.devig_one_sided(130 / 230, 0.05, "multiplicative") == pytest.approx((130 / 230) / 1.05)
    assert dv.devig_one_sided(0.4, 0.0) == pytest.approx(0.4)
    with pytest.raises(ValueError):
        dv.devig_one_sided(0.4, -0.1)


def test_one_sided_devig_additive():
    assert dv.devig_one_sided(130 / 230, 0.05, "additive") == pytest.approx(130 / 230 - 0.025)
    assert dv.devig_one_sided(0.2, 0.12, "additive") == pytest.approx(0.14)
    # additive removes a fixed amount, so it cuts longshots harder than multiplicative
    assert dv.devig_one_sided(0.2, 0.12, "additive") < dv.devig_one_sided(0.2, 0.12)
    # and favourites less
    assert dv.devig_one_sided(0.8, 0.05, "additive") > dv.devig_one_sided(0.8, 0.05)
    with pytest.raises(ValueError):
        dv.devig_one_sided(0.02, 0.12, "additive")
    with pytest.raises(ValueError):
        dv.devig_one_sided(0.5, 0.05, "power")


def test_breakeven_per_leg():
    assert dv.breakeven_per_leg(3.0, 2) == pytest.approx(0.5774, abs=5e-5)
    assert dv.breakeven_per_leg(2.0, 1) == pytest.approx(0.5)
    assert dv.breakeven_per_leg(6.0, 3) == pytest.approx(6 ** (-1 / 3))
