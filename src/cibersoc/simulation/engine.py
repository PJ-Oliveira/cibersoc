from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Mapping, Protocol

from ..sortition import CounterModeHmacDrbg

BRAZIL_REGIONS: tuple[tuple[str, str, float, float, int], ...] = (
    ("BR-SP", "São Paulo", -23.55, -46.63, 45_000_000),
    ("BR-RJ", "Rio de Janeiro", -22.91, -43.17, 17_000_000),
    ("BR-MG", "Minas Gerais", -19.92, -43.94, 21_000_000),
    ("BR-BA", "Bahia", -12.97, -38.50, 14_000_000),
    ("BR-PR", "Paraná", -25.42, -49.27, 11_000_000),
    ("BR-RS", "Rio Grande do Sul", -30.03, -51.22, 11_000_000),
    ("BR-PE", "Pernambuco", -8.05, -34.90, 9_600_000),
    ("BR-CE", "Ceará", -3.72, -38.54, 9_200_000),
    ("BR-PA", "Pará", -1.46, -48.50, 8_700_000),
    ("BR-AM", "Amazonas", -3.10, -60.02, 4_200_000),
)

GOVERNANCE_PORTFOLIOS: tuple[str, ...] = (
    "EDUCATION",
    "HEALTH",
    "INFRASTRUCTURE",
    "JUSTICE",
    "ECONOMY",
)

PORTFOLIO_EVENT_CATEGORIES: Mapping[str, frozenset[str]] = {
    "ECONOMY": frozenset({"ECONOMIC"}),
    "EDUCATION": frozenset({"SOCIAL"}),
    "HEALTH": frozenset({"SOCIAL", "CLIMATE"}),
    "INFRASTRUCTURE": frozenset({"CLIMATE", "ECONOMIC"}),
    "JUSTICE": frozenset({"POLITICAL", "SOCIAL"}),
}

INTER_REGIONAL_CORRIDORS: tuple[tuple[str, str], ...] = (
    ("BR-SP", "BR-RJ"),
    ("BR-SP", "BR-MG"),
    ("BR-SP", "BR-PR"),
    ("BR-PR", "BR-RS"),
    ("BR-MG", "BR-BA"),
    ("BR-BA", "BR-PE"),
    ("BR-PE", "BR-CE"),
    ("BR-CE", "BR-PA"),
    ("BR-PA", "BR-AM"),
    ("BR-MG", "BR-PA"),
)

_EVENT_TEMPLATES: tuple[tuple[str, str, str], ...] = (
    (
        "ECONOMIC",
        "Inter-regional Cooperative Alliance Formed",
        "Multiple productive cooperatives unite their supply chains under collective governance, increasing efficiency by a statistical margin.",
    ),
    (
        "CLIMATE",
        "Amazonian Rainfall Pattern Shift Detected",
        "Meteorological models indicate a 0.8-sigma deviation in precipitation across northern biomes, affecting agro-ecological outputs.",
    ),
    (
        "SOCIAL",
        "Grassroots Sortition Literacy Programme Launched",
        "Citizens across municipalities participate in civic education modules on demarchic governance, raising participatory awareness.",
    ),
    (
        "ECONOMIC",
        "Leontief Input-Output Recalibration Required",
        "Structural changes in energy distribution have altered the technical matrix, requiring a Jacobi-iteration recalculation of embedded labour hours.",
    ),
    (
        "POLITICAL",
        "Federal Lottery Draw Triggers Constitutional Review",
        "A newly drawn federal councillor proposes a constitutional amendment, triggering review procedures across the five-council mesh.",
    ),
    (
        "CLIMATE",
        "Solar Energy Grid Expansion Milestone Reached",
        "Public-utility solar cooperatives in the north-east achieve a new generation threshold, altering the energy sector Leontief coefficient.",
    ),
    (
        "SOCIAL",
        "Universal Basic Services Index Rises 0.03 Points",
        "Aggregate data from federated states indicates improvement in combined health and education provision, reflecting policy compliance.",
    ),
    (
        "ECONOMIC",
        "Automation Productivity Shock in Industrial Sector",
        "Introduction of CNC-integrated robotics in metalworking cooperatives has altered the direct labour coefficient for industrial inputs.",
    ),
    (
        "POLITICAL",
        "Military Subordination Protocol Successfully Executed",
        "A routine multi-sig civilian oversight order to the High Command was authenticated by the full Defence Chamber without incident.",
    ),
    (
        "CLIMATE",
        "Cerrado Biome Carbon Sequestration Peaks",
        "Carbon sink data from the central savannah shows above-baseline sequestration, improving the planetary boundary constraint margin.",
    ),
    (
        "SOCIAL",
        "Inter-Generational Stratification Recalibration",
        "The sortition engine detected a minor generational imbalance in council composition, triggering a Hamilton-quota correction.",
    ),
    (
        "ECONOMIC",
        "Workers Cooperative Merger Increases 1/N Base",
        "Two metalworking cooperatives in Paraná unite their worker rosters, expanding the eligible surplus-sharing population.",
    ),
    (
        "POLITICAL",
        "Cybernetic Budget Plebiscite Turnout Record",
        "Anonymous token issuance for the annual macro-allocation vote broke a ten-year record.",
    ),
    (
        "SOCIAL",
        "Healthcare Distribution Normalises Across Strata",
        "Statistical distribution of healthcare access across income strata has narrowed, indicating convergence toward the target Gini reduction trajectory.",
    ),
    (
        "CLIMATE",
        "Flood Risk Matrix Updated for Coastal Regions",
        "LIDAR survey data reveals coastal land-use changes in Rio and Bahia states requiring updated vulnerability coefficients.",
    ),
    (
        "ECONOMIC",
        "Kantorovich Plan Identifies New Expansion Path",
        "A Kantorovich ray-expansion calculation reveals a feasible output-expansion trajectory under current capacity constraints.",
    ),
    (
        "POLITICAL",
        "Ex-Councillor Successfully Reinstated Under Protection Lock",
        "A citizen completing their demarchic mandate has been reinstated with the 180-day employment stability lock duly activated.",
    ),
    (
        "SOCIAL",
        "Cross-Regional Educational Equalisation Programme Begins",
        "Federal allocative directive resources are channelled into low-HDI municipalities to reduce educational provision variance.",
    ),
)


class _BoundedDrbg(Protocol):
    def randbelow_unbiased(self, upper_bound: int) -> int: ...


@dataclass(frozen=True)
class RegionProfile:
    region_id: str
    name: str
    lat: float
    lon: float
    population_size: int
    hdi: float
    gini: float
    employment_rate: float


@dataclass(frozen=True)
class CouncillorSlot:
    portfolio: str
    citizen_hash: str
    region_id: str
    term_year: int


@dataclass(frozen=True)
class EmergentEvent:
    event_id: str
    category: str
    title: str
    narrative: str
    affected_region_ids: tuple[str, ...]
    severity: float
    gdp_delta: float
    welfare_delta: float


class SimulationScenario(StrEnum):
    BASELINE = "BASELINE"
    ECOLOGICAL_STRESS = "ECOLOGICAL_STRESS"
    POST_CRISIS_EQUALISATION = "POST_CRISIS_EQUALISATION"


class InstitutionalRegime(StrEnum):
    CIBERSOC_DEMARCHY = "CIBERSOC_DEMARCHY"
    ELECTORAL_OLIGARCHY = "ELECTORAL_OLIGARCHY"
    BUREAUCRATIC_CENTRALISM = "BUREAUCRATIC_CENTRALISM"


@dataclass(frozen=True)
class RegimeParameters:
    target_hdi: float
    target_gini: float
    target_employment: float
    convergence_rate: float
    shock_mitigation_gain: float
    rent_capture_drift: float
    macro_directive_multiplier: float
    equalisation_transfer: float
    ossification_rate: float


REGIME_PARAMETERS: Mapping[InstitutionalRegime, RegimeParameters] = {
    InstitutionalRegime.CIBERSOC_DEMARCHY: RegimeParameters(
        target_hdi=0.925,
        target_gini=0.245,
        target_employment=0.935,
        convergence_rate=0.055,
        shock_mitigation_gain=0.30,
        rent_capture_drift=0.0,
        macro_directive_multiplier=1.0,
        equalisation_transfer=0.032,
        ossification_rate=0.0,
    ),
    InstitutionalRegime.ELECTORAL_OLIGARCHY: RegimeParameters(
        target_hdi=0.755,
        target_gini=0.535,
        target_employment=0.780,
        convergence_rate=0.042,
        shock_mitigation_gain=0.06,
        rent_capture_drift=0.0022,
        macro_directive_multiplier=0.22,
        equalisation_transfer=-0.005,
        ossification_rate=0.0,
    ),
    InstitutionalRegime.BUREAUCRATIC_CENTRALISM: RegimeParameters(
        target_hdi=0.825,
        target_gini=0.355,
        target_employment=0.880,
        convergence_rate=0.050,
        shock_mitigation_gain=0.15,
        rent_capture_drift=0.0009,
        macro_directive_multiplier=0.55,
        equalisation_transfer=0.014,
        ossification_rate=0.0018,
    ),
}


@dataclass
class GovernanceCycle:
    year: int
    regions: tuple[RegionProfile, ...]
    councillors: tuple[CouncillorSlot, ...]
    events: tuple[EmergentEvent, ...]
    aggregate_hdi: float
    aggregate_gini: float
    aggregate_employment: float
    regime_comparison: dict[str, dict[str, float]] | None = None


def _hash_citizen_id(region_id: str, citizen_index: int) -> str:
    payload = f"{region_id}:{citizen_index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def _aggregate_region_metrics(regions: tuple[RegionProfile, ...]) -> dict[str, float]:
    safe_pop = max(1, sum(r.population_size for r in regions))
    agg_hdi = sum(r.hdi * r.population_size for r in regions) / safe_pop
    agg_gini = sum(r.gini * r.population_size for r in regions) / safe_pop
    agg_emp = sum(r.employment_rate * r.population_size for r in regions) / safe_pop
    return {
        "aggregate_hdi": round(agg_hdi, 4),
        "aggregate_gini": round(agg_gini, 4),
        "aggregate_employment": round(agg_emp, 4),
    }


class NationSimulationEngine:
    def __init__(
        self,
        seed: int = 42,
        scenario: SimulationScenario = SimulationScenario.BASELINE,
        regime: InstitutionalRegime = InstitutionalRegime.CIBERSOC_DEMARCHY,
    ) -> None:
        self._base_seed = seed
        self.scenario = scenario
        self.regime = regime
        self.current_year: int = 1
        initial_regions = self._initialize_regions()
        self.regions: tuple[RegionProfile, ...] = initial_regions
        self._shadow_regions: dict[InstitutionalRegime, tuple[RegionProfile, ...]] = {
            candidate: initial_regions for candidate in InstitutionalRegime
        }
        self._cycle_shadow_snapshots: list[dict[InstitutionalRegime, tuple[RegionProfile, ...]]] = []
        self.cycles: list[GovernanceCycle] = []
        self._served_citizen_hashes: set[str] = set()
        self._quarantined_until_year: dict[str, int] = {}
        self.active_macro_directive: str | None = None
        self.active_macro_bonus: float = 0.0

    @property
    def total_population(self) -> int:
        return sum(region.population_size for region in self.regions)

    @property
    def citizens_drawn(self) -> int:
        return len(self._served_citizen_hashes)

    def set_active_macro_directive(self, directive_id: str, bonus: float = 0.015) -> None:
        self.active_macro_directive = directive_id
        self.active_macro_bonus = bonus

    def switch_regime(self, regime: InstitutionalRegime) -> None:
        self.regime = regime
        self.regions = self._shadow_regions[regime]
        for idx, cycle in enumerate(self.cycles):
            snapshot = self._cycle_shadow_snapshots[idx][regime]
            metrics = _aggregate_region_metrics(snapshot)
            cycle.regions = snapshot
            cycle.aggregate_hdi = metrics["aggregate_hdi"]
            cycle.aggregate_gini = metrics["aggregate_gini"]
            cycle.aggregate_employment = metrics["aggregate_employment"]

    def compare_regimes(self) -> dict[str, dict[str, float]]:
        return {
            candidate.value: _aggregate_region_metrics(self._shadow_regions[candidate])
            for candidate in InstitutionalRegime
        }

    def _initialize_regions(self) -> tuple[RegionProfile, ...]:
        rng = random.Random(self._base_seed)
        profiles: list[RegionProfile] = []
        for region_id, name, lat, lon, pop in BRAZIL_REGIONS:
            base_hdi = round(0.55 + rng.random() * 0.35, 3)
            base_gini = round(0.35 + rng.random() * 0.25, 3)
            base_emp = round(0.70 + rng.random() * 0.20, 3)
            if self.scenario == SimulationScenario.ECOLOGICAL_STRESS:
                if lat > -15.0:
                    base_hdi = round(max(0.35, base_hdi - 0.08), 3)
                    base_emp = round(max(0.50, base_emp - 0.06), 3)
            elif self.scenario == SimulationScenario.POST_CRISIS_EQUALISATION:
                base_gini = round(min(0.68, 0.52 + rng.random() * 0.12), 3)
                base_emp = round(max(0.55, 0.58 + rng.random() * 0.12), 3)
            profiles.append(
                RegionProfile(
                    region_id=region_id,
                    name=name,
                    lat=lat,
                    lon=lon,
                    population_size=pop,
                    hdi=base_hdi,
                    gini=base_gini,
                    employment_rate=base_emp,
                )
            )
        return tuple(profiles)

    def advance_year(self, event_matrix: StochasticEventMatrix) -> GovernanceCycle:
        year = self.current_year
        cycle_seed = self._base_seed * 1000 + year * 7 + 13
        events = event_matrix.generate_cycle_events(year, cycle_seed, scenario=self.scenario)
        councillors = self._draw_councillors(year, cycle_seed)
        macro_bonus = self.active_macro_bonus if self.active_macro_directive else 0.0

        cycle_snapshots: dict[InstitutionalRegime, tuple[RegionProfile, ...]] = {}
        for candidate in InstitutionalRegime:
            shocked_regions = tuple(
                self._apply_event_effects(
                    r,
                    events,
                    councillors=councillors,
                    macro_bonus=macro_bonus,
                    regime=candidate,
                )
                for r in self._shadow_regions[candidate]
            )
            updated_candidate = self._apply_institutional_governance(
                shocked_regions,
                regime=candidate,
                scenario=self.scenario,
                year=year,
            )
            self._shadow_regions[candidate] = updated_candidate
            cycle_snapshots[candidate] = updated_candidate

        self._cycle_shadow_snapshots.append(cycle_snapshots)
        self.regions = self._shadow_regions[self.regime]
        comparison = self.compare_regimes()
        active_metrics = comparison[self.regime.value]
        cycle = GovernanceCycle(
            year=year,
            regions=self.regions,
            councillors=councillors,
            events=events,
            aggregate_hdi=active_metrics["aggregate_hdi"],
            aggregate_gini=active_metrics["aggregate_gini"],
            aggregate_employment=active_metrics["aggregate_employment"],
            regime_comparison=comparison,
        )
        self.cycles.append(cycle)
        self.current_year += 1
        return cycle

    def _draw_councillors(self, year: int, cycle_seed: int) -> tuple[CouncillorSlot, ...]:
        seed_hex = hashlib.sha256(
            f"SEEM_SORTITION|{self._base_seed}|{year}|{cycle_seed}".encode("utf-8")
        ).hexdigest()
        drbg = CounterModeHmacDrbg(seed_hex)
        slots: list[CouncillorSlot] = []
        for portfolio in GOVERNANCE_PORTFOLIOS:
            region = self.regions[drbg.randbelow_unbiased(len(self.regions))]
            citizen_hash = self._draw_unique_citizen(drbg, region, year=year)
            slots.append(
                CouncillorSlot(
                    portfolio=portfolio,
                    citizen_hash=citizen_hash,
                    region_id=region.region_id,
                    term_year=year,
                )
            )
        return tuple(slots)

    def _draw_unique_citizen(
        self, drbg: _BoundedDrbg, region: RegionProfile, year: int = 1
    ) -> str:
        pool_size = max(1, region.population_size)
        for _ in range(64):
            index = drbg.randbelow_unbiased(pool_size)
            citizen_hash = _hash_citizen_id(region.region_id, index)
            if (
                citizen_hash not in self._served_citizen_hashes
                and self._quarantined_until_year.get(citizen_hash, 0) < year
            ):
                self._served_citizen_hashes.add(citizen_hash)
                self._quarantined_until_year[citizen_hash] = year + 1
                return citizen_hash

        scan_limit = min(pool_size, 256)
        start_offset = drbg.randbelow_unbiased(pool_size)
        for offset in range(scan_limit):
            index = (start_offset + offset) % pool_size
            citizen_hash = _hash_citizen_id(region.region_id, index)
            if self._quarantined_until_year.get(citizen_hash, 0) < year:
                self._served_citizen_hashes.add(citizen_hash)
                self._quarantined_until_year[citizen_hash] = year + 1
                return citizen_hash

        fallback_index = max(pool_size, len(self._served_citizen_hashes)) + year
        fallback_hash = _hash_citizen_id(region.region_id, fallback_index)
        self._served_citizen_hashes.add(fallback_hash)
        self._quarantined_until_year[fallback_hash] = year + 1
        return fallback_hash

    @staticmethod
    def _apply_event_effects(
        region: RegionProfile,
        events: tuple[EmergentEvent, ...],
        councillors: tuple[CouncillorSlot, ...] = (),
        macro_bonus: float = 0.0,
        regime: InstitutionalRegime = InstitutionalRegime.CIBERSOC_DEMARCHY,
    ) -> RegionProfile:
        matching_events = [e for e in events if region.region_id in e.affected_region_ids]
        if not matching_events and macro_bonus == 0.0:
            return region

        params = REGIME_PARAMETERS[regime]
        delta_hdi = 0.0
        delta_gini = 0.0
        delta_emp = 0.0
        councillor_portfolios = {
            slot.portfolio for slot in councillors if slot.region_id == region.region_id
        }
        covered_categories: set[str] = set()
        for portfolio in councillor_portfolios:
            covered_categories.update(
                PORTFOLIO_EVENT_CATEGORIES.get(portfolio, frozenset({portfolio}))
            )
        for event in matching_events:
            mitigation = (
                params.shock_mitigation_gain if event.category in covered_categories else 0.0
            )
            effective_welfare = (
                event.welfare_delta * (1.0 - mitigation)
                if event.welfare_delta < 0.0
                else event.welfare_delta * (1.0 + mitigation)
            )
            effective_gdp = (
                event.gdp_delta * (1.0 - mitigation)
                if event.gdp_delta < 0.0
                else event.gdp_delta * (1.0 + mitigation)
            )
            delta_hdi += effective_welfare * 0.01
            delta_gini -= effective_welfare * 0.005
            delta_emp += effective_gdp * 0.02

        headroom = max(0.0, 0.965 - region.hdi)
        effective_macro = macro_bonus * params.macro_directive_multiplier * headroom * 0.55

        return RegionProfile(
            region_id=region.region_id,
            name=region.name,
            lat=region.lat,
            lon=region.lon,
            population_size=region.population_size,
            hdi=round(max(0.0, min(1.0, region.hdi + delta_hdi + effective_macro)), 4),
            gini=round(max(0.0, min(1.0, region.gini + delta_gini)), 4),
            employment_rate=round(max(0.0, min(1.0, region.employment_rate + delta_emp)), 4),
        )

    @staticmethod
    def _apply_institutional_governance(
        regions: tuple[RegionProfile, ...],
        regime: InstitutionalRegime,
        scenario: SimulationScenario,
        year: int,
    ) -> tuple[RegionProfile, ...]:
        params = REGIME_PARAMETERS[regime]
        mean_hdi = sum(r.hdi for r in regions) / max(1, len(regions))
        ossification = min(0.055, max(0.0, (year - 8) * params.ossification_rate))
        effective_target_hdi = params.target_hdi - ossification
        speed_mult = 1.25 if scenario == SimulationScenario.POST_CRISIS_EQUALISATION else 1.0
        rate = params.convergence_rate * speed_mult

        evolved: list[RegionProfile] = []
        for r in regions:
            eco_hdi_drag = (
                0.0032
                if (scenario == SimulationScenario.ECOLOGICAL_STRESS and r.lat > -16.0)
                else 0.0
            )
            eco_emp_drag = (
                0.0024
                if (scenario == SimulationScenario.ECOLOGICAL_STRESS and r.lat > -16.0)
                else 0.0
            )
            eco_mitigated_hdi = eco_hdi_drag * (1.0 - params.shock_mitigation_gain)
            eco_mitigated_emp = eco_emp_drag * (1.0 - params.shock_mitigation_gain)
            equalisation = (mean_hdi - r.hdi) * params.equalisation_transfer * speed_mult

            next_hdi = (
                r.hdi
                + (effective_target_hdi - r.hdi) * rate
                + equalisation
                - eco_mitigated_hdi
            )
            next_gini = (
                r.gini
                + (params.target_gini - r.gini) * rate
                + params.rent_capture_drift
            )
            next_emp = (
                r.employment_rate
                + (params.target_employment - r.employment_rate) * rate
                - ossification * 0.25
                - eco_mitigated_emp
            )
            evolved.append(
                RegionProfile(
                    region_id=r.region_id,
                    name=r.name,
                    lat=r.lat,
                    lon=r.lon,
                    population_size=r.population_size,
                    hdi=round(max(0.0, min(0.985, next_hdi)), 4),
                    gini=round(max(0.0, min(1.0, next_gini)), 4),
                    employment_rate=round(max(0.0, min(0.99, next_emp)), 4),
                )
            )
        return tuple(evolved)

    def _compute_inter_regional_flows(self) -> list[dict[str, Any]]:
        by_id = {region.region_id: region for region in self.regions}
        flows: list[dict[str, Any]] = []
        for source_id, target_id in INTER_REGIONAL_CORRIDORS:
            src = by_id[source_id]
            dst = by_id[target_id]
            vitality = ((src.hdi * src.employment_rate) + (dst.hdi * dst.employment_rate)) * 0.5
            equality_factor = 1.0 - ((src.gini + dst.gini) * 0.25)
            intensity = round(max(0.15, min(1.0, vitality * equality_factor * 1.35)), 4)
            flows.append(
                {
                    "from_id": source_id,
                    "to_id": target_id,
                    "intensity": intensity,
                }
            )
        return flows

    def export_time_series_csv(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "year",
                    "regime",
                    "aggregate_hdi",
                    "aggregate_gini",
                    "aggregate_employment",
                    "demarchy_hdi",
                    "demarchy_gini",
                    "oligarchy_hdi",
                    "oligarchy_gini",
                    "centralism_hdi",
                    "centralism_gini",
                    "event_count",
                    "scenario",
                    "active_directive",
                ]
            )
            for cycle in self.cycles:
                comp = cycle.regime_comparison or {}
                dem = comp.get(InstitutionalRegime.CIBERSOC_DEMARCHY.value, {})
                oli = comp.get(InstitutionalRegime.ELECTORAL_OLIGARCHY.value, {})
                cen = comp.get(InstitutionalRegime.BUREAUCRATIC_CENTRALISM.value, {})
                writer.writerow(
                    [
                        cycle.year,
                        self.regime.value,
                        cycle.aggregate_hdi,
                        cycle.aggregate_gini,
                        cycle.aggregate_employment,
                        dem.get("aggregate_hdi", ""),
                        dem.get("aggregate_gini", ""),
                        oli.get("aggregate_hdi", ""),
                        oli.get("aggregate_gini", ""),
                        cen.get("aggregate_hdi", ""),
                        cen.get("aggregate_gini", ""),
                        len(cycle.events),
                        self.scenario.value,
                        self.active_macro_directive or "",
                    ]
                )
        return destination

    def export_time_series_json(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "scenario": self.scenario.value,
            "regime": self.regime.value,
            "active_directive": self.active_macro_directive,
            "total_cycles": len(self.cycles),
            "regime_comparison": self.compare_regimes(),
            "cycles": [
                {
                    "year": c.year,
                    "aggregate_hdi": c.aggregate_hdi,
                    "aggregate_gini": c.aggregate_gini,
                    "aggregate_employment": c.aggregate_employment,
                    "event_count": len(c.events),
                    "regime_comparison": c.regime_comparison,
                }
                for c in self.cycles
            ],
        }
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return destination

    def serialise_for_renderer(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "year": self.current_year,
            "population_size": self.total_population,
            "citizens_drawn": self.citizens_drawn,
            "scenario": self.scenario.value,
            "regime": self.regime.value,
            "active_directive": self.active_macro_directive,
            "regime_comparison": self.compare_regimes(),
            "inter_regional_flows": self._compute_inter_regional_flows(),
            "regions": [
                {
                    "region_id": r.region_id,
                    "name": r.name,
                    "lat": r.lat,
                    "lon": r.lon,
                    "population_size": r.population_size,
                    "active_workforce": round(r.population_size * r.employment_rate),
                    "hdi": r.hdi,
                    "gini": r.gini,
                    "employment_rate": r.employment_rate,
                }
                for r in self.regions
            ],
        }
        if not self.cycles:
            base["latest_cycle"] = None
            return base
        latest = self.cycles[-1]
        base["latest_cycle"] = {
            "year": latest.year,
            "aggregate_hdi": latest.aggregate_hdi,
            "aggregate_gini": latest.aggregate_gini,
            "aggregate_employment": latest.aggregate_employment,
            "event_count": len(latest.events),
            "events": [
                {
                    "category": e.category,
                    "title": e.title,
                    "severity": e.severity,
                    "affected_region_ids": list(e.affected_region_ids),
                }
                for e in latest.events
            ],
        }
        return base


class StochasticEventMatrix:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def generate_cycle_events(
        self,
        year: int,
        base_seed: int,
        scenario: SimulationScenario = SimulationScenario.BASELINE,
    ) -> tuple[EmergentEvent, ...]:
        rng = random.Random(base_seed * 137 + year * 31 + self.seed * 7)
        count = rng.randint(2, 5)
        indices = list(range(len(_EVENT_TEMPLATES)))
        rng.shuffle(indices)
        selected = indices[:count]
        result: list[EmergentEvent] = []
        for idx in selected:
            result.append(self._instantiate_template(idx, rng, year, scenario=scenario))
        return tuple(result)

    @staticmethod
    def _instantiate_template(
        template_index: int,
        rng: random.Random,
        year: int,
        scenario: SimulationScenario = SimulationScenario.BASELINE,
    ) -> EmergentEvent:
        template = _EVENT_TEMPLATES[template_index]
        category = template[0]
        region_pool = [r[0] for r in BRAZIL_REGIONS]
        affected_count = rng.randint(1, min(3, len(region_pool)))
        affected = tuple(rng.sample(region_pool, affected_count))
        severity = round(0.1 + rng.random() * 0.9, 3)
        gdp_center = 0.48
        welfare_center = 0.46
        if scenario == SimulationScenario.ECOLOGICAL_STRESS and category == "CLIMATE":
            gdp_center = 0.64
            welfare_center = 0.66
        elif scenario == SimulationScenario.POST_CRISIS_EQUALISATION and category == "ECONOMIC":
            gdp_center = 0.54
            welfare_center = 0.52
        gdp_delta = round((rng.random() - gdp_center) * 2.4, 3)
        welfare_delta = round((rng.random() - welfare_center) * 1.8, 3)
        return EmergentEvent(
            event_id=f"EVT-{year:02d}-{template_index:03d}",
            category=category,
            title=template[1],
            narrative=template[2],
            affected_region_ids=affected,
            severity=severity,
            gdp_delta=gdp_delta,
            welfare_delta=welfare_delta,
        )
