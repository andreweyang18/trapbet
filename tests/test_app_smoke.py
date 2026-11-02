"""Smoke tests for the Streamlit app: the pure playground computation reproduces the Ohtani
example, and each page renders under streamlit.testing without raising."""
from pathlib import Path

import pytest

from app import playground_lib as pl

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def test_playground_reproduces_ohtani_example():
    res = pl.run_ohtani_example()
    assert 7.5 <= res.fair_fs <= 7.7
    assert 0.68 <= res.p_under <= 0.72
    assert res.units == 3.0
    assert res.p_under + res.p_over == pytest.approx(1.0)
    assert abs(res.sim_mean - res.fair_fs) < 0.15
    assert res.breakeven == pytest.approx(0.5774, abs=5e-5)
    assert set(res.components["stat"]) == {"1B", "2B", "3B", "HR", "R", "RBI", "BB", "HBP", "SB"}
    assert len(res.devig) == 3 and res.devig["method"].str.contains("one-sided").all()


def test_two_way_market_devigs_without_hold():
    m = pl.MarketInput("H", 0.5, "over", -200, other_side=+160)
    row = pl.devig_market(m)
    assert row["method"].startswith("two-way")
    assert 0.5 < row["fair"] < row["implied"]


def test_bad_inputs_raise_readably():
    with pytest.raises(ValueError, match="at least one"):
        pl.run_playground("prizepicks", 9.5, "under", [], (0.45, 0.15, 0.05, 0.35), {}, {}, n_sims=1000)
    with pytest.raises(ValueError, match="no market or fallback"):
        pl.run_playground("prizepicks", 9.5, "under", [pl.MarketInput("H", 0.5, "over", -150)],
                          (0.45, 0.15, 0.05, 0.35), {}, {}, n_sims=1000)


@pytest.mark.parametrize("page", ["streamlit_app.py", "pages/results.py", "pages/about.py"])
def test_page_renders_without_exception(page):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP / page), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]


def test_playground_page_runs_ohtani_end_to_end():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP / "pages" / "playground.py"), default_timeout=120).run()
    assert not at.exception
    at.button[0].click().run()          # Load Ohtani example
    assert not at.exception
    at.button[1].click().run()          # form submit "Run"
    assert not at.exception, [e.value for e in at.exception]
    labels = {m.label: m.value for m in at.metric}
    assert 7.5 <= float(labels["Fair FS (linear)"]) <= 7.7
    assert 0.68 <= float(labels["P(under 9.5)"]) <= 0.72
    assert float(labels["Units (¼ Kelly, 3% cap)"]) == 3.0
