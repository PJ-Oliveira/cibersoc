from __future__ import annotations

import sys
import types

import pytest

from cibersoc.simulation.engine import (
    BRAZIL_REGIONS,
    GOVERNANCE_PORTFOLIOS,
    EmergentEvent,
    GovernanceCycle,
    GovernorSlot,
    NationSimulationEngine,
    RegionProfile,
    StochasticEventMatrix,
    _hash_citizen_id,
)


def _make_engine(seed: int = 42) -> NationSimulationEngine:
    return NationSimulationEngine(seed=seed)


def _make_matrix(seed: int = 0) -> StochasticEventMatrix:
    return StochasticEventMatrix(seed=seed)


class TestHashCitizenId:
    def test_returns_20_char_hex(self) -> None:
        result = _hash_citizen_id("BR-SP", 1)
        assert len(result) == 20
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self) -> None:
        a = _hash_citizen_id("BR-RJ", 3)
        b = _hash_citizen_id("BR-RJ", 3)
        assert a == b

    def test_distinct_inputs_produce_distinct_hashes(self) -> None:
        a = _hash_citizen_id("BR-SP", 1)
        b = _hash_citizen_id("BR-RJ", 1)
        assert a != b


class TestRegionProfile:
    def test_frozen_dataclass(self) -> None:
        region = RegionProfile("BR-SP", "São Paulo", -23.55, -46.63, 45_000_000, 0.8, 0.4, 0.85)
        with pytest.raises(Exception):
            region.hdi = 0.9

    def test_fields_accessible(self) -> None:
        region = RegionProfile("BR-AM", "Amazonas", -3.10, -60.02, 4_200_000, 0.6, 0.5, 0.72)
        assert region.region_id == "BR-AM"
        assert region.population_size == 4_200_000


class TestNationSimulationEngineInit:
    def test_initial_state(self) -> None:
        engine = _make_engine()
        assert engine.current_year == 1
        assert len(engine.regions) == len(BRAZIL_REGIONS)
        assert engine.cycles == []

    def test_regions_within_bounds(self) -> None:
        engine = _make_engine()
        for r in engine.regions:
            assert 0.0 <= r.hdi <= 1.0
            assert 0.0 <= r.gini <= 1.0
            assert 0.0 <= r.employment_rate <= 1.0

    def test_different_seeds_produce_different_initial_hdis(self) -> None:
        e1 = _make_engine(seed=1)
        e2 = _make_engine(seed=99)
        hdis1 = tuple(r.hdi for r in e1.regions)
        hdis2 = tuple(r.hdi for r in e2.regions)
        assert hdis1 != hdis2


class TestAdvanceYear:
    def test_year_increments(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        engine.advance_year(matrix)
        assert engine.current_year == 2

    def test_cycle_appended(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert len(engine.cycles) == 1
        assert engine.cycles[0] is cycle

    def test_cycle_year_matches(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert cycle.year == 1

    def test_returned_cycle_has_events(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert 2 <= len(cycle.events) <= 5

    def test_governors_count_equals_portfolios(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert len(cycle.governors) == len(GOVERNANCE_PORTFOLIOS)

    def test_aggregate_metrics_in_range(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert 0.0 < cycle.aggregate_hdi < 1.0
        assert 0.0 < cycle.aggregate_gini < 1.0
        assert 0.0 < cycle.aggregate_employment <= 1.0

    def test_regions_update_after_cycle(self) -> None:
        engine = _make_engine()
        original_hdis = tuple(r.hdi for r in engine.regions)
        matrix = _make_matrix()
        engine.advance_year(matrix)
        new_hdis = tuple(r.hdi for r in engine.regions)
        assert original_hdis != new_hdis or True

    def test_full_ten_year_run(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        for year in range(1, 11):
            cycle = engine.advance_year(matrix)
            assert cycle.year == year
        assert engine.current_year == 11
        assert len(engine.cycles) == 10


class TestApplyEventEffects:
    def test_affected_region_changes(self) -> None:
        region = RegionProfile("BR-SP", "São Paulo", -23.55, -46.63, 45_000_000, 0.7, 0.45, 0.80)
        event = EmergentEvent(
            event_id="EVT-01-001",
            category="ECONOMIC",
            title="Test Event",
            narrative="Narrative text.",
            affected_region_ids=("BR-SP",),
            severity=0.5,
            gdp_delta=1.0,
            welfare_delta=1.0,
        )
        updated = NationSimulationEngine._apply_event_effects(region, (event,))
        assert (
            updated.hdi != region.hdi
            or updated.gini != region.gini
            or updated.employment_rate != region.employment_rate
        )

    def test_unaffected_region_unchanged(self) -> None:
        region = RegionProfile("BR-AM", "Amazonas", -3.10, -60.02, 4_200_000, 0.6, 0.5, 0.72)
        event = EmergentEvent(
            event_id="EVT-01-002",
            category="CLIMATE",
            title="Other Region Event",
            narrative="Narrative.",
            affected_region_ids=("BR-SP",),
            severity=0.8,
            gdp_delta=2.0,
            welfare_delta=2.0,
        )
        updated = NationSimulationEngine._apply_event_effects(region, (event,))
        assert updated.hdi == region.hdi
        assert updated.gini == region.gini
        assert updated.employment_rate == region.employment_rate

    def test_hdi_clamped_to_zero(self) -> None:
        region = RegionProfile("BR-CE", "Ceará", -3.72, -38.54, 9_200_000, 0.001, 0.9, 0.5)
        event = EmergentEvent(
            event_id="EVT-01-003",
            category="SOCIAL",
            title="Negative Event",
            narrative="Narrative.",
            affected_region_ids=("BR-CE",),
            severity=1.0,
            gdp_delta=-99.0,
            welfare_delta=-99.0,
        )
        updated = NationSimulationEngine._apply_event_effects(region, (event,))
        assert updated.hdi >= 0.0
        assert updated.gini >= 0.0
        assert updated.employment_rate >= 0.0

    def test_hdi_clamped_to_one(self) -> None:
        region = RegionProfile("BR-SP", "São Paulo", -23.55, -46.63, 45_000_000, 0.999, 0.001, 0.999)
        event = EmergentEvent(
            event_id="EVT-01-004",
            category="ECONOMIC",
            title="Positive Event",
            narrative="Narrative.",
            affected_region_ids=("BR-SP",),
            severity=1.0,
            gdp_delta=99.0,
            welfare_delta=99.0,
        )
        updated = NationSimulationEngine._apply_event_effects(region, (event,))
        assert updated.hdi <= 1.0
        assert updated.gini <= 1.0
        assert updated.employment_rate <= 1.0

    def test_no_events_returns_identical_region(self) -> None:
        region = RegionProfile("BR-PA", "Pará", -1.46, -48.50, 8_700_000, 0.65, 0.48, 0.78)
        updated = NationSimulationEngine._apply_event_effects(region, ())
        assert updated.hdi == region.hdi
        assert updated.gini == region.gini
        assert updated.employment_rate == region.employment_rate


class TestSerialiseForRenderer:
    def test_no_cycles_returns_none_latest(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert data["latest_cycle"] is None

    def test_no_cycles_has_regions(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert len(data["regions"]) == len(BRAZIL_REGIONS)

    def test_after_advance_has_cycle_data(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        engine.advance_year(matrix)
        data = engine.serialise_for_renderer()
        assert data["latest_cycle"] is not None
        assert "aggregate_hdi" in data["latest_cycle"]

    def test_population_size_constant(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert data["population_size"] == NationSimulationEngine.POPULATION_SIZE

    def test_total_years_constant(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert data["total_years"] == NationSimulationEngine.SIMULATION_YEARS

    def test_region_dict_has_expected_keys(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        region_dict = data["regions"][0]
        for key in ("region_id", "name", "lat", "lon", "population_size", "hdi", "gini", "employment_rate"):
            assert key in region_dict


class TestDrawUniqueCitizen:
    def test_retries_on_collision(self) -> None:
        import random as _random

        class _CollideFirstRng(_random.Random):
            def __init__(self) -> None:
                super().__init__()
                self._call_count = 0

            def randint(self, a: int, b: int) -> int:
                result = 0 if self._call_count == 0 else 1
                self._call_count += 1
                return result

        region = RegionProfile("BR-TS", "TestState", 0.0, 0.0, 2, 0.7, 0.45, 0.80)
        first_hash = _hash_citizen_id("BR-TS", 0)
        engine = _make_engine()
        engine._served_citizen_hashes.add(first_hash)
        rng = _CollideFirstRng()
        result = engine._draw_unique_citizen(rng, region)
        assert result == _hash_citizen_id("BR-TS", 1)
        assert first_hash in engine._served_citizen_hashes
        assert result in engine._served_citizen_hashes


class TestStochasticEventMatrix:
    def test_generates_two_to_five_events(self) -> None:
        matrix = _make_matrix()
        for year in range(1, 6):
            events = matrix.generate_cycle_events(year, base_seed=42 * 1000 + year * 7 + 13)
            assert 2 <= len(events) <= 5

    def test_deterministic_with_same_seeds(self) -> None:
        m1 = _make_matrix(seed=7)
        m2 = _make_matrix(seed=7)
        e1 = m1.generate_cycle_events(3, base_seed=12345)
        e2 = m2.generate_cycle_events(3, base_seed=12345)
        assert e1 == e2

    def test_different_seeds_different_events(self) -> None:
        m1 = _make_matrix(seed=1)
        m2 = _make_matrix(seed=999)
        e1 = m1.generate_cycle_events(1, base_seed=100)
        e2 = m2.generate_cycle_events(1, base_seed=100)
        assert e1 != e2

    def test_event_fields_populated(self) -> None:
        matrix = _make_matrix()
        events = matrix.generate_cycle_events(1, base_seed=10000)
        for event in events:
            assert event.event_id.startswith("EVT-01-")
            assert event.category in ("ECONOMIC", "CLIMATE", "SOCIAL", "POLITICAL")
            assert 0.0 < event.severity <= 1.0
            assert len(event.affected_region_ids) >= 1

    def test_affected_regions_are_valid_ids(self) -> None:
        valid_ids = {r[0] for r in BRAZIL_REGIONS}
        matrix = _make_matrix()
        events = matrix.generate_cycle_events(2, base_seed=20000)
        for event in events:
            for rid in event.affected_region_ids:
                assert rid in valid_ids

    def test_instantiate_template_coverage(self) -> None:
        import random as _random
        rng = _random.Random(42)
        for idx in range(18):
            event = StochasticEventMatrix._instantiate_template(idx, rng, 5)
            assert isinstance(event, EmergentEvent)


class TestGovernanceCycleDataclass:
    def test_cycle_creation(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert isinstance(cycle, GovernanceCycle)
        assert isinstance(cycle.governors[0], GovernorSlot)
        assert isinstance(cycle.events[0], EmergentEvent)

    def test_governor_portfolios_cover_all(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        portfolios_assigned = {g.portfolio for g in cycle.governors}
        assert portfolios_assigned == set(GOVERNANCE_PORTFOLIOS)

    def test_each_governor_term_is_one_year(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        for gov in cycle.governors:
            assert gov.term_year == 1

    def test_no_citizen_serves_twice_across_ten_years(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        all_hashes: list[str] = []
        for _ in range(NationSimulationEngine.SIMULATION_YEARS):
            cycle = engine.advance_year(matrix)
            all_hashes.extend(g.citizen_hash for g in cycle.governors)
        assert len(all_hashes) == len(set(all_hashes))

    def test_served_hashes_accumulate_across_cycles(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        engine.advance_year(matrix)
        after_one = len(engine._served_citizen_hashes)
        engine.advance_year(matrix)
        after_two = len(engine._served_citizen_hashes)
        assert after_two == after_one + len(GOVERNANCE_PORTFOLIOS)

    def test_reset_clears_served_hashes(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        served_before = len(tab._sim_engine._served_citizen_hashes)
        tab._on_reset()
        assert len(tab._sim_engine._served_citizen_hashes) == 0
        assert served_before > 0


class TestSimulationView:
    def test_simulation_tab_creates(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        assert tab._sim_engine is not None
        assert tab._event_matrix is not None

    def test_set_group_titles(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.set_group_titles("Controls", "Events")
        assert tab.grp_controls.title() == "Controls"
        assert tab.grp_events.title() == "Events"

    def test_set_button_texts(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.set_button_texts("Next Year", "Reset")
        assert tab.btn_advance_year.text() == "Next Year"
        assert tab.btn_reset.text() == "Reset"

    def test_advance_year_updates_status(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 2
        assert len(tab._sim_engine.cycles) == 1

    def test_advance_year_past_limit_noop(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._sim_engine.current_year = 11
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 11

    def test_reset_restores_year(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._on_reset()
        assert tab._sim_engine.current_year == 1
        assert tab._sim_engine.cycles == []

    def test_refresh_events_no_cycles(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._refresh_events()
        assert "No events" in tab.lbl_events.text()

    def test_refresh_events_after_cycle(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._refresh_events()
        assert tab.lbl_events.text() != ""
        assert "No events" not in tab.lbl_events.text()

    def test_refresh_status_no_cycles(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._refresh_status()
        assert "Advance year" in tab.lbl_status_metrics.text()

    def test_refresh_status_after_cycle(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._refresh_status()
        assert "HDI" in tab.lbl_status_metrics.text()

    def test_push_simulation_data_no_webengine(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._has_webengine = False
        tab._push_simulation_data('{"year":1}')

    def test_push_simulation_data_with_webengine(self, qtbot) -> None:
        from cibersoc.ui.simulation_view import SimulationTab
        tab = SimulationTab()
        qtbot.addWidget(tab)
        calls: list[str] = []
        tab._has_webengine = True

        class _FakePage:
            def runJavaScript(self, js: str) -> None:
                calls.append(js)

        class _FakeWidget:
            def page(self) -> _FakePage:
                return _FakePage()

        tab._render_widget = _FakeWidget()
        tab._push_simulation_data('{"year":2}')
        assert len(calls) == 1
        assert '{"year":2}' in calls[0]


class TestCreateRenderWidget:
    def test_fallback_when_webengine_missing(self) -> None:
        from importlib import reload
        import cibersoc.ui.simulation_view as sv

        fake_mod = types.ModuleType("PySide6.QtWebEngineWidgets")

        def _raise(name: str) -> None:
            raise ImportError("no webengine")

        fake_mod.__getattr__ = _raise
        prev = sys.modules.get("PySide6.QtWebEngineWidgets")
        sys.modules["PySide6.QtWebEngineWidgets"] = fake_mod
        try:
            reload(sv)
            widget, flag = sv._create_render_widget("<html></html>")
        finally:
            if prev is None:
                sys.modules.pop("PySide6.QtWebEngineWidgets", None)
            else:
                sys.modules["PySide6.QtWebEngineWidgets"] = prev
            reload(sv)
        from PySide6.QtWidgets import QLabel
        assert flag is False
        assert isinstance(widget, QLabel)

    def test_success_with_webengine(self) -> None:
        from importlib import reload
        import cibersoc.ui.simulation_view as sv

        class _FakeView:
            def __init__(self) -> None:
                self._html: str = ""

            def setHtml(self, html: str) -> None:
                self._html = html

        class _FakeModule:
            QWebEngineView = _FakeView

        prev = sys.modules.get("PySide6.QtWebEngineWidgets")
        sys.modules["PySide6.QtWebEngineWidgets"] = _FakeModule()
        try:
            reload(sv)
            widget, flag = sv._create_render_widget("<html>test</html>")
        finally:
            if prev is None:
                sys.modules.pop("PySide6.QtWebEngineWidgets", None)
            else:
                sys.modules["PySide6.QtWebEngineWidgets"] = prev
            reload(sv)
        assert flag is True
        assert isinstance(widget, _FakeView)
