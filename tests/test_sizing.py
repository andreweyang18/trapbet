import pytest
from trapbet.engines import sizing as sz


def test_kelly_fraction_basics():
    assert sz.kelly_fraction(0.5, 1.0) == 0.0
    assert sz.kelly_fraction(0.6, 1.0) == pytest.approx(0.2)
    assert sz.kelly_fraction(0.49, 2.0) == pytest.approx((0.98 - 0.51) / 2)
    assert sz.kelly_fraction(0.2, 2.0) == 0.0            # negative edge floors at 0
    with pytest.raises(ValueError):
        sz.kelly_fraction(1.2, 1.0)
    with pytest.raises(ValueError):
        sz.kelly_fraction(0.5, 0.0)


def test_slip_probability_multiplies():
    assert sz.slip_probability([0.7, 0.7]) == pytest.approx(0.49)
    assert sz.slip_probability([0.5]) == 0.5
    with pytest.raises(ValueError):
        sz.slip_probability([])


def test_units_cap_at_three():
    u, raw = sz.units(0.49, 3.0)          # quarter Kelly 0.0588 > cap 0.03
    assert u == 3.0 and raw == pytest.approx(0.235)
    u, raw = sz.units(0.99, 3.0)
    assert u == 3.0
    u, raw = sz.units(0.35, 3.0)          # Kelly (0.70 - 0.65)/2 = 0.025 -> quarter 0.00625
    assert u == pytest.approx(0.62, abs=0.01) and raw == pytest.approx(0.025)
    u, raw = sz.units(1 / 3, 3.0)         # breakeven -> 0
    assert u == 0.0 and raw == 0.0
    with pytest.raises(ValueError):
        sz.units(0.5, 1.0)
