from __future__ import annotations

import json
from pathlib import Path
import random as _random
import re
from typing import Any

import pytest
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from cibersoc.i18n.translator import LocalizationCatalog, SupportedLocale
from cibersoc.simulation.engine import (
    BRAZIL_REGIONS,
    GOVERNANCE_PORTFOLIOS,
    CouncillorSlot,
    EmergentEvent,
    GovernanceCycle,
    InstitutionalRegime,
    NationSimulationEngine,
    RegionProfile,
    SimulationScenario,
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

    def test_councillors_count_equals_portfolios(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        assert len(cycle.councillors) == len(GOVERNANCE_PORTFOLIOS)

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
        assert original_hdis != new_hdis

    def test_full_ten_year_run_and_regime_comparison(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        for year in range(1, 11):
            cycle = engine.advance_year(matrix)
            assert cycle.year == year
        assert engine.current_year == 11
        assert len(engine.cycles) == 10
        comp = engine.compare_regimes()
        assert comp["CIBERSOC_DEMARCHY"]["aggregate_hdi"] > comp["ELECTORAL_OLIGARCHY"]["aggregate_hdi"]
        assert comp["CIBERSOC_DEMARCHY"]["aggregate_gini"] < comp["ELECTORAL_OLIGARCHY"]["aggregate_gini"]

        engine.switch_regime(InstitutionalRegime.ELECTORAL_OLIGARCHY)
        assert engine.regime == InstitutionalRegime.ELECTORAL_OLIGARCHY
        assert engine.cycles[-1].aggregate_hdi == comp["ELECTORAL_OLIGARCHY"]["aggregate_hdi"]

        engine.switch_regime(InstitutionalRegime.BUREAUCRATIC_CENTRALISM)
        assert engine.cycles[-1].aggregate_gini == comp["BUREAUCRATIC_CENTRALISM"]["aggregate_gini"]

    def test_runs_far_beyond_ten_years(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        for year in range(1, 121):
            cycle = engine.advance_year(matrix)
            assert cycle.year == year
        assert engine.current_year == 121
        assert len(engine.cycles) == 120
        for region in engine.regions:
            assert 0.0 <= region.hdi <= 1.0
            assert 0.0 <= region.gini <= 1.0
            assert 0.0 <= region.employment_rate <= 1.0
        assert engine.serialise_for_renderer()["year"] == 121


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
        assert len(data["inter_regional_flows"]) == 10

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

    def test_population_size_is_sum_of_regions(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert data["population_size"] == sum(r[4] for r in BRAZIL_REGIONS)
        assert data["population_size"] == engine.total_population

    def test_no_year_cap_in_payload(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        assert "total_years" not in data
        assert not hasattr(NationSimulationEngine, "SIMULATION_YEARS")

    def test_citizens_drawn_counts_served_citizens(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        assert engine.serialise_for_renderer()["citizens_drawn"] == 0
        engine.advance_year(matrix)
        engine.advance_year(matrix)
        data = engine.serialise_for_renderer()
        assert data["citizens_drawn"] == 2 * len(GOVERNANCE_PORTFOLIOS)
        assert data["citizens_drawn"] == engine.citizens_drawn

    def test_region_dict_has_expected_keys(self) -> None:
        engine = _make_engine()
        data = engine.serialise_for_renderer()
        region_dict = data["regions"][0]
        for key in ("region_id", "name", "lat", "lon", "population_size", "hdi", "gini", "employment_rate"):
            assert key in region_dict


class TestDrawUniqueCitizen:
    def test_retries_on_collision(self) -> None:
        class _CollideFirstDrbg:
            def __init__(self) -> None:
                self._call_count = 0

            def randbelow_unbiased(self, upper_bound: int) -> int:
                result = 0 if self._call_count == 0 else min(1, upper_bound - 1)
                self._call_count += 1
                return result

        region = RegionProfile("BR-TS", "TestState", 0.0, 0.0, 2, 0.7, 0.45, 0.80)
        first_hash = _hash_citizen_id("BR-TS", 0)
        engine = _make_engine()
        engine._served_citizen_hashes.add(first_hash)
        drbg = _CollideFirstDrbg()
        result = engine._draw_unique_citizen(drbg, region, year=1)
        assert result == _hash_citizen_id("BR-TS", 1)
        assert first_hash in engine._served_citizen_hashes
        assert result in engine._served_citizen_hashes

    def test_scan_window_reuses_unquarantined_citizen(self) -> None:
        class _AlwaysZeroDrbg:
            def randbelow_unbiased(self, upper_bound: int) -> int:
                return 0

        region = RegionProfile("BR-TS", "TestState", 0.0, 0.0, 1, 0.7, 0.45, 0.80)
        only_hash = _hash_citizen_id("BR-TS", 0)
        engine = _make_engine()
        engine._served_citizen_hashes.add(only_hash)
        engine._quarantined_until_year[only_hash] = 1
        result = engine._draw_unique_citizen(_AlwaysZeroDrbg(), region, year=3)
        assert result == only_hash
        assert engine._quarantined_until_year[only_hash] == 4

    def test_exhaustion_fallback_when_all_quarantined(self) -> None:
        class _AlwaysZeroDrbg:
            def randbelow_unbiased(self, upper_bound: int) -> int:
                return 0

        region = RegionProfile("BR-TS", "TestState", 0.0, 0.0, 1, 0.7, 0.45, 0.80)
        only_hash = _hash_citizen_id("BR-TS", 0)
        engine = _make_engine()
        engine._served_citizen_hashes.add(only_hash)
        engine._quarantined_until_year[only_hash] = 5
        result = engine._draw_unique_citizen(_AlwaysZeroDrbg(), region, year=2)
        assert result != only_hash
        assert len(result) == 20
        assert result in engine._served_citizen_hashes


class TestSimulationScenario:
    def test_scenarios_initialize_distinct_metrics(self) -> None:
        base = NationSimulationEngine(seed=42, scenario=SimulationScenario.BASELINE)
        eco = NationSimulationEngine(seed=42, scenario=SimulationScenario.ECOLOGICAL_STRESS)
        crisis = NationSimulationEngine(seed=42, scenario=SimulationScenario.POST_CRISIS_EQUALISATION)

        assert base.scenario == SimulationScenario.BASELINE
        assert eco.scenario == SimulationScenario.ECOLOGICAL_STRESS
        assert crisis.scenario == SimulationScenario.POST_CRISIS_EQUALISATION

        base_north = [r for r in base.regions if r.lat > -15.0]
        eco_north = [r for r in eco.regions if r.lat > -15.0]
        assert all(e.hdi <= b.hdi for b, e in zip(base_north, eco_north))

        base_gini = sum(r.gini for r in base.regions) / len(base.regions)
        crisis_gini = sum(r.gini for r in crisis.regions) / len(crisis.regions)
        assert crisis_gini > base_gini


class TestEnginePoliciesAndExports:
    def test_set_active_macro_directive(self) -> None:
        engine = _make_engine()
        assert engine.active_macro_directive is None
        engine.set_active_macro_directive("option.FLOW-HEALTH-PLUSS", bonus=0.03)
        assert engine.active_macro_directive == "option.FLOW-HEALTH-PLUSS"
        assert engine.active_macro_bonus == 0.03
        data = engine.serialise_for_renderer()
        assert data["active_directive"] == "option.FLOW-HEALTH-PLUSS"
        assert data["scenario"] == "BASELINE"

    def test_councillor_oversight_mitigation(self) -> None:
        region = RegionProfile("BR-SP", "São Paulo", -23.55, -46.63, 45_000_000, 0.70, 0.35, 0.80)
        event_neg = EmergentEvent(
            event_id="EVT-01-NEG",
            category="ECONOMIC",
            title="Crisis",
            narrative="...",
            affected_region_ids=("BR-SP",),
            severity=0.5,
            gdp_delta=-2.0,
            welfare_delta=-2.0,
        )
        without_councillor = NationSimulationEngine._apply_event_effects(region, (event_neg,), ())
        slot = CouncillorSlot("ECONOMY", "hash-1", "BR-SP", 1)
        with_councillor = NationSimulationEngine._apply_event_effects(region, (event_neg,), (slot,))
        assert with_councillor.hdi > without_councillor.hdi
        assert with_councillor.employment_rate > without_councillor.employment_rate

        event_pos = EmergentEvent(
            event_id="EVT-01-POS",
            category="ECONOMIC",
            title="Boom",
            narrative="...",
            affected_region_ids=("BR-SP",),
            severity=0.5,
            gdp_delta=2.0,
            welfare_delta=2.0,
        )
        pos_without = NationSimulationEngine._apply_event_effects(region, (event_pos,), ())
        pos_with = NationSimulationEngine._apply_event_effects(region, (event_pos,), (slot,))
        assert pos_with.hdi > pos_without.hdi

    def test_export_time_series_csv_and_json(self, tmp_path: Path) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        engine.set_active_macro_directive("option.FLOW-TEST", bonus=0.02)
        engine.advance_year(matrix)
        engine.advance_year(matrix)

        csv_path = tmp_path / "exports" / "history.csv"
        out_csv = engine.export_time_series_csv(csv_path)
        assert out_csv.exists()
        csv_text = out_csv.read_text(encoding="utf-8")
        assert "aggregate_hdi" in csv_text
        assert "demarchy_hdi" in csv_text
        assert "option.FLOW-TEST" in csv_text
        assert len(csv_text.strip().splitlines()) == 3

        json_path = tmp_path / "exports" / "history.json"
        out_json = engine.export_time_series_json(json_path)
        assert out_json.exists()
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["total_cycles"] == 2
        assert data["scenario"] == "BASELINE"
        assert "regime_comparison" in data
        assert len(data["cycles"]) == 2


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
        assert isinstance(cycle.councillors[0], CouncillorSlot)
        assert isinstance(cycle.events[0], EmergentEvent)

    def test_councillor_portfolios_cover_all(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        portfolios_assigned = {c.portfolio for c in cycle.councillors}
        assert portfolios_assigned == set(GOVERNANCE_PORTFOLIOS)

    def test_each_councillor_term_is_one_year(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        cycle = engine.advance_year(matrix)
        for slot in cycle.councillors:
            assert slot.term_year == 1

    def test_no_citizen_serves_twice_across_sixty_years(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        all_hashes: list[str] = []
        for _ in range(60):
            cycle = engine.advance_year(matrix)
            all_hashes.extend(c.citizen_hash for c in cycle.councillors)
        assert len(all_hashes) == 60 * len(GOVERNANCE_PORTFOLIOS)
        assert len(all_hashes) == len(set(all_hashes))

    def test_served_hashes_accumulate_across_cycles(self) -> None:
        engine = _make_engine()
        matrix = _make_matrix()
        engine.advance_year(matrix)
        after_one = len(engine._served_citizen_hashes)
        engine.advance_year(matrix)
        after_two = len(engine._served_citizen_hashes)
        assert after_two == after_one + len(GOVERNANCE_PORTFOLIOS)

    def test_reset_clears_served_hashes(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        served_before = len(tab._sim_engine._served_citizen_hashes)
        tab._on_reset()
        assert len(tab._sim_engine._served_citizen_hashes) == 0
        assert served_before > 0


class TestSimulationView:
    def test_simulation_tab_creates(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        assert tab._sim_engine is not None
        assert tab._event_matrix is not None

    def test_set_group_titles(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.set_group_titles("Controls", "Events")
        assert tab.grp_controls.title() == "Controls"
        assert tab.grp_events.title() == "Events"

    def test_set_button_texts(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.set_button_texts("Next Year", "Reset")
        assert tab.btn_advance_year.text() == "Next Year"
        assert tab.btn_reset.text() == "Reset"

    def test_advance_year_updates_status(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 2
        assert len(tab._sim_engine.cycles) == 1

    def test_advance_year_past_ten_years_is_allowed(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._sim_engine.current_year = 11
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 12
        assert tab._sim_engine.cycles[-1].year == 11
        assert "Year 12" in tab.lbl_status_year.text()

    def test_years_per_step_advances_many_years(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.set_button_texts("Advance Year", "Reset")
        assert tab.btn_advance_year.text() == "Advance Year"
        tab.spn_years_step.setValue(25)
        assert tab.btn_advance_year.text() == "Advance 25 Years"
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 26
        assert len(tab._sim_engine.cycles) == 25
        tab.spn_years_step.setValue(1)
        assert tab.btn_advance_year.text() == "Advance Year"

    def test_years_per_step_has_no_total_cap(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import YEARS_PER_STEP_LIMIT, SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab.spn_years_step.setValue(YEARS_PER_STEP_LIMIT)
        tab._on_advance_year()
        tab._on_advance_year()
        assert tab._sim_engine.current_year == 2 * YEARS_PER_STEP_LIMIT + 1

    def test_status_shows_population_and_citizens_drawn(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        total = f"{sum(r[4] for r in BRAZIL_REGIONS):,}"
        assert f"Population: {total}" in tab.lbl_status_year.text()
        assert "Citizens drawn: 0" in tab.lbl_status_year.text()
        assert "/ 10" not in tab.lbl_status_year.text()
        tab._on_advance_year()
        assert f"Citizens drawn: {len(GOVERNANCE_PORTFOLIOS)}" in tab.lbl_status_year.text()

    def test_apply_translations_switches_language(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        catalog = LocalizationCatalog(SupportedLocale.PORTUGUESE)
        tab.apply_translations(catalog)
        assert tab.lbl_years_step.text() == "Anos por passo:"
        assert tab.lbl_status_metrics.text() == "Avance um ano para iniciar a simulação."
        assert "150.700.000" in tab.lbl_status_year.text()
        tab._on_advance_year()
        assert "IDH:" in tab.lbl_status_metrics.text()
        assert "," in tab.lbl_status_metrics.text().split("GINI:")[1]
        tab.set_button_texts("Avançar Ano", "Reiniciar")
        tab.spn_years_step.setValue(3)
        assert tab.btn_advance_year.text() == "Avançar 3 Anos"

    def test_reset_restores_year(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._on_reset()
        assert tab._sim_engine.current_year == 1
        assert tab._sim_engine.cycles == []

    def test_refresh_events_no_cycles(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._refresh_events()
        assert "No events" in tab.lbl_events.text()

    def test_refresh_events_after_cycle(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._refresh_events()
        assert tab.lbl_events.text() != ""
        assert "No events" not in tab.lbl_events.text()

    def test_refresh_status_no_cycles(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._refresh_status()
        assert "Advance year" in tab.lbl_status_metrics.text()

    def test_refresh_status_after_cycle(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._on_advance_year()
        tab._refresh_status()
        assert "HDI" in tab.lbl_status_metrics.text()

    def test_push_simulation_data_and_zoom_no_webengine(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        tab = SimulationTab()
        qtbot.addWidget(tab)
        tab._has_webengine = False
        tab._push_simulation_data('{"year":1}')
        tab.zoom_in()
        tab.zoom_out()

    def test_push_simulation_data_and_zoom_with_webengine(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        calls: list[str] = []

        class _FakePage:
            def runJavaScript(self, js: str) -> None:
                calls.append(js)

        class _FakeView(QWidget):
            loadFinished = Signal(bool)

            def page(self) -> _FakePage:
                return _FakePage()

        tab = SimulationTab(render_widget_factory=lambda _html: (_FakeView(), True))
        qtbot.addWidget(tab)
        calls.clear()
        tab._push_simulation_data('{"year":2}')
        tab.zoom_in()
        tab.zoom_out()
        assert len(calls) == 3
        assert '{"year":2}' in calls[0]
        assert "0.78" in calls[1]
        assert "1.28" in calls[2]


class TestViewerLegend:
    def test_html_keys_exist_in_catalogue_for_all_languages(self) -> None:
        from cibersoc.ui import simulation_view as sv

        used = set(re.findall(r'data-i18n(?:-term)?="([a-z_]+)"', sv._THREE_JS_HTML))
        assert used
        assert used <= set(sv.VIEWER_TEXT_KEYS)
        for locale in SupportedLocale:
            catalog = LocalizationCatalog(locale)
            for key in sv.VIEWER_TEXT_KEYS:
                assert catalog.translate(f"simulation.viewer.{key}").strip()
            for key in sv.STATUS_TEXT_KEYS:
                assert catalog.translate(f"simulation.{key}").strip()

    def test_legend_explains_rings_particles_and_indicators(self) -> None:
        for locale in SupportedLocale:
            catalog = LocalizationCatalog(locale)
            rings = catalog.translate("simulation.viewer.legend_rings_text")
            particles = catalog.translate("simulation.viewer.legend_particles_text")
            assert rings != particles
            for term_key in ("gl_population", "gl_citizens", "gl_hdi", "gl_gini", "gl_employment"):
                entry = catalog.translate(f"simulation.viewer.{term_key}")
                assert ":" in entry

    def test_html_has_no_year_cap_and_uses_new_hud_fields(self, qtbot: Any) -> None:
        from cibersoc.ui import simulation_view as sv

        assert "total_years" not in sv._THREE_JS_HTML
        assert "1 / 10" not in sv._THREE_JS_HTML
        assert "v-comp" not in sv._THREE_JS_HTML
        assert "citizens_drawn" in sv._THREE_JS_HTML
        assert "sr-dem" in sv._THREE_JS_HTML
        assert "sr-cen" in sv._THREE_JS_HTML
        assert "sr-oli" in sv._THREE_JS_HTML
        assert "window.updateHud" in sv._THREE_JS_HTML
        assert "window.applyI18n" in sv._THREE_JS_HTML

        tab = sv.SimulationTab()
        qtbot.addWidget(tab)
        tab.spn_years_step.setValue(10)
        tab._on_advance_year()
        tab.cmb_regime.setCurrentIndex(2)
        metrics_text = tab.lbl_status_metrics.text()
        assert "[A]" in metrics_text
        assert "[C]" in metrics_text
        assert "[B]" in metrics_text

    def test_push_viewer_texts_sends_strings_once(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        calls: list[str] = []

        class _FakePage:
            def runJavaScript(self, js: str) -> None:
                calls.append(js)

        class _FakeView(QWidget):
            loadFinished = Signal(bool)

            def page(self) -> _FakePage:
                return _FakePage()

        tab = SimulationTab(render_widget_factory=lambda _html: (_FakeView(), True))
        qtbot.addWidget(tab)
        calls.clear()
        tab._push_viewer_texts()
        assert len(calls) == 1
        assert calls[0].startswith("if(window.applyI18n){applyI18n(")
        payload = calls[0][len("if(window.applyI18n){applyI18n(") : -len(");}")]
        assert json.loads(payload)["number_locale"] == "en-GB"

    def test_page_loaded_pushes_texts_then_data(self, qtbot: Any) -> None:
        from cibersoc.ui.simulation_view import SimulationTab

        calls: list[str] = []

        class _FakePage:
            def runJavaScript(self, js: str) -> None:
                calls.append(js)

        class _FakeView(QWidget):
            loadFinished = Signal(bool)

            def page(self) -> _FakePage:
                return _FakePage()

        tab = SimulationTab(render_widget_factory=lambda _html: (_FakeView(), True))
        qtbot.addWidget(tab)
        calls.clear()
        tab._render_widget.loadFinished.emit(False)
        assert calls == []
        tab._render_widget.loadFinished.emit(True)
        assert len(calls) == 2
        assert "applyI18n" in calls[0]
        assert "updateHud" in calls[1] and "updateSimulation" in calls[1]


class TestCreateRenderWidget:
    def test_fallback_when_offscreen_or_loader_raises(self) -> None:
        from cibersoc.ui.simulation_view import _create_render_widget, _load_default_webengine_cls

        loaded_cls = _load_default_webengine_cls("PySide6.QtWidgets", "QLabel")
        assert loaded_cls is QLabel

        widget_offscreen, flag_offscreen = _create_render_widget("<html></html>")
        assert flag_offscreen is False
        assert isinstance(widget_offscreen, QLabel)

        def _raising_loader() -> Any:
            raise ImportError("no webengine")

        widget_err, flag_err = _create_render_widget(
            "<html></html>",
            module_loader=_raising_loader,
            allow_offscreen_webengine=True,
        )
        assert flag_err is False
        assert isinstance(widget_err, QLabel)

    def test_success_with_injected_view_and_loader(self) -> None:
        from cibersoc.ui.simulation_view import _create_render_widget

        class _FakeView(QWidget):
            def __init__(self) -> None:
                super().__init__()
                self._html: str = ""

            def setHtml(self, html: str, baseUrl: Any = None) -> None:
                self._html = html

        widget_direct, flag_direct = _create_render_widget(
            "<html>direct</html>",
            webengine_view_cls=_FakeView,
        )
        assert flag_direct is True
        assert isinstance(widget_direct, _FakeView)

        widget_loader, flag_loader = _create_render_widget(
            "<html>loader</html>",
            module_loader=lambda: _FakeView,
            allow_offscreen_webengine=True,
        )
        assert flag_loader is True
        assert isinstance(widget_loader, _FakeView)


def test_simulation_tab_scenario_regime_switching_and_export(tmp_path: Path) -> None:
    from cibersoc.ui.simulation_view import SimulationTab

    _ = QApplication.instance() or QApplication([])
    translator = LocalizationCatalog(SupportedLocale.ENGLISH_UK)
    csv_out = tmp_path / "test_sim.csv"
    json_out = tmp_path / "test_sim.json"
    dialog_choices: list[tuple[str, str]] = [
        (str(csv_out), "CSV"),
        (str(json_out), "JSON"),
        ("", ""),
        ("", ""),
    ]

    def choose_path(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return dialog_choices.pop(0)

    tab = SimulationTab(translator=translator, save_file_dialog=choose_path)

    assert tab.cmb_scenario.count() == 3
    assert tab.cmb_regime.count() == 3

    tab.cmb_scenario.setCurrentIndex(1)
    assert tab._sim_engine.scenario == SimulationScenario.ECOLOGICAL_STRESS
    assert tab._sim_engine.active_macro_directive is None

    tab.set_active_macro_directive("FLOW-EDU-PLUS5")
    assert tab._sim_engine.active_macro_directive == "FLOW-EDU-PLUS5"

    tab.cmb_scenario.setCurrentIndex(2)
    assert tab._sim_engine.scenario == SimulationScenario.POST_CRISIS_EQUALISATION
    assert tab._sim_engine.active_macro_directive == "FLOW-EDU-PLUS5"

    tab.cmb_regime.setCurrentIndex(1)
    assert tab._sim_engine.regime == InstitutionalRegime.ELECTORAL_OLIGARCHY

    tab._on_reset()
    assert tab._sim_engine.scenario == SimulationScenario.POST_CRISIS_EQUALISATION
    assert tab._sim_engine.regime == InstitutionalRegime.ELECTORAL_OLIGARCHY
    assert tab._sim_engine.active_macro_directive == "FLOW-EDU-PLUS5"

    tab._sim_engine.advance_year(tab._event_matrix)
    tab.cmb_scenario.setCurrentIndex(0)
    assert tab._sim_engine.scenario == SimulationScenario.BASELINE
    tab.cmb_regime.setCurrentIndex(0)
    assert tab._sim_engine.regime == InstitutionalRegime.CIBERSOC_DEMARCHY

    tab._on_export_csv()
    assert csv_out.exists()

    tab._on_export_json()
    assert json_out.exists()

    tab._on_export_csv()
    tab._on_export_json()

    tab.cmb_scenario.setCurrentIndex(0)
    tab.cmb_regime.setCurrentIndex(0)
    tab.apply_translations(translator)
    assert tab.cmb_scenario.currentIndex() == 0
    assert tab.cmb_regime.currentIndex() == 0

    tab.cmb_scenario.setCurrentIndex(-1)
    tab.cmb_regime.setCurrentIndex(-1)
    tab.apply_translations(translator)
    assert tab.cmb_scenario.currentIndex() == 0
    assert tab.cmb_regime.currentIndex() == 0

    tab.cmb_scenario.setItemData(0, "INVALID_SCENARIO")
    tab.cmb_regime.setItemData(0, "INVALID_REGIME")
    tab._on_scenario_changed(0)
    tab._on_regime_changed(0)
    tab._on_reset()
    assert tab._sim_engine.scenario == SimulationScenario.BASELINE
    assert tab._sim_engine.regime == InstitutionalRegime.CIBERSOC_DEMARCHY


def test_simulation_orchestrator_directive_none() -> None:
    from cibersoc.ui.state import SimulationOrchestrator

    orch = SimulationOrchestrator.__new__(SimulationOrchestrator)
    orch.last_directive = None
    assert orch.active_macro_directive is None

    orch_live = SimulationOrchestrator()
    assert orch_live.active_macro_directive is not None


class TestThirtyYearThreeByThreeBenchmark:
    def test_thirty_year_3x3_matrix_without_and_with_macro_directive(self) -> None:
        results_by_mode: dict[tuple[SimulationScenario, bool], dict[str, dict[str, float]]] = {}
        for scenario in SimulationScenario:
            for macro_enabled in (False, True):
                engine = NationSimulationEngine(seed=42, scenario=scenario)
                if macro_enabled:
                    engine.set_active_macro_directive("PLEB-FED-01: +5% Health")
                matrix = StochasticEventMatrix(seed=42)
                for _ in range(30):
                    engine.advance_year(matrix)

                assert engine.current_year == 31
                assert engine.citizens_drawn == 30 * len(GOVERNANCE_PORTFOLIOS)
                comp = engine.compare_regimes()
                results_by_mode[(scenario, macro_enabled)] = comp

                dem = comp[InstitutionalRegime.CIBERSOC_DEMARCHY.value]
                oli = comp[InstitutionalRegime.ELECTORAL_OLIGARCHY.value]
                cen = comp[InstitutionalRegime.BUREAUCRATIC_CENTRALISM.value]

                assert dem["aggregate_hdi"] > cen["aggregate_hdi"] > oli["aggregate_hdi"]
                assert dem["aggregate_gini"] < cen["aggregate_gini"] < oli["aggregate_gini"]
                assert dem["aggregate_employment"] > cen["aggregate_employment"]
                assert dem["aggregate_employment"] > oli["aggregate_employment"]

                gaps: dict[InstitutionalRegime, float] = {}
                flows: dict[InstitutionalRegime, float] = {}
                for regime in InstitutionalRegime:
                    engine.switch_regime(regime)
                    assert all(0.55 < r.hdi < 0.985 for r in engine.regions)
                    gaps[regime] = max(r.hdi for r in engine.regions) - min(
                        r.hdi for r in engine.regions
                    )
                    corridor_flows = engine._compute_inter_regional_flows()
                    flows[regime] = sum(f["intensity"] for f in corridor_flows) / len(
                        corridor_flows
                    )

                assert (
                    gaps[InstitutionalRegime.CIBERSOC_DEMARCHY]
                    < gaps[InstitutionalRegime.BUREAUCRATIC_CENTRALISM]
                    < gaps[InstitutionalRegime.ELECTORAL_OLIGARCHY]
                )
                assert (
                    flows[InstitutionalRegime.CIBERSOC_DEMARCHY]
                    > flows[InstitutionalRegime.BUREAUCRATIC_CENTRALISM]
                    > flows[InstitutionalRegime.ELECTORAL_OLIGARCHY]
                )

        for scenario in SimulationScenario:
            no_macro = results_by_mode[(scenario, False)]
            with_macro = results_by_mode[(scenario, True)]
            for regime in InstitutionalRegime:
                assert (
                    with_macro[regime.value]["aggregate_hdi"]
                    > no_macro[regime.value]["aggregate_hdi"]
                )
            dem_gain = (
                with_macro[InstitutionalRegime.CIBERSOC_DEMARCHY.value]["aggregate_hdi"]
                - no_macro[InstitutionalRegime.CIBERSOC_DEMARCHY.value]["aggregate_hdi"]
            )
            oli_gain = (
                with_macro[InstitutionalRegime.ELECTORAL_OLIGARCHY.value]["aggregate_hdi"]
                - no_macro[InstitutionalRegime.ELECTORAL_OLIGARCHY.value]["aggregate_hdi"]
            )
            assert dem_gain > oli_gain

    def test_ecological_cleavage_ossification_and_post_crisis_compression(self) -> None:
        eco_engine = NationSimulationEngine(
            seed=42, scenario=SimulationScenario.ECOLOGICAL_STRESS
        )
        eco_matrix = StochasticEventMatrix(seed=42)
        for _ in range(30):
            eco_engine.advance_year(eco_matrix)

        eco_engine.switch_regime(InstitutionalRegime.CIBERSOC_DEMARCHY)
        dem_north = [r.hdi for r in eco_engine.regions if r.lat > -16.0]
        dem_south = [r.hdi for r in eco_engine.regions if r.lat <= -16.0]
        dem_ns_gap = abs(sum(dem_south) / len(dem_south) - sum(dem_north) / len(dem_north))

        eco_engine.switch_regime(InstitutionalRegime.ELECTORAL_OLIGARCHY)
        oli_north = [r.hdi for r in eco_engine.regions if r.lat > -16.0]
        oli_south = [r.hdi for r in eco_engine.regions if r.lat <= -16.0]
        oli_ns_gap = abs(sum(oli_south) / len(oli_south) - sum(oli_north) / len(oli_north))
        assert dem_ns_gap < oli_ns_gap * 0.5

        eco_engine.switch_regime(InstitutionalRegime.BUREAUCRATIC_CENTRALISM)
        emp_yr10 = eco_engine.cycles[9].aggregate_employment
        emp_yr30 = eco_engine.cycles[29].aggregate_employment
        assert emp_yr30 < emp_yr10

        crisis_engine = NationSimulationEngine(
            seed=42, scenario=SimulationScenario.POST_CRISIS_EQUALISATION
        )
        init_gini = sum(
            r.gini * r.population_size for r in crisis_engine.regions
        ) / crisis_engine.total_population
        init_emp = sum(
            r.employment_rate * r.population_size for r in crisis_engine.regions
        ) / crisis_engine.total_population
        crisis_matrix = StochasticEventMatrix(seed=42)
        for _ in range(30):
            crisis_engine.advance_year(crisis_matrix)

        crisis_comp = crisis_engine.compare_regimes()
        dem_crisis = crisis_comp[InstitutionalRegime.CIBERSOC_DEMARCHY.value]
        oli_crisis = crisis_comp[InstitutionalRegime.ELECTORAL_OLIGARCHY.value]
        assert (init_gini - dem_crisis["aggregate_gini"]) > 0.28
        assert (dem_crisis["aggregate_employment"] - init_emp) > 0.24
        assert abs(init_gini - oli_crisis["aggregate_gini"]) < 0.01

