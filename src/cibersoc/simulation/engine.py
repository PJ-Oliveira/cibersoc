from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field


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

_EVENT_TEMPLATES: tuple[tuple[str, str, str], ...] = (
    ("ECONOMIC", "Inter-regional Cooperative Alliance Formed", "Multiple productive cooperatives unite their supply chains under collective governance, increasing efficiency by a statistical margin."),
    ("CLIMATE", "Amazonian Rainfall Pattern Shift Detected", "Meteorological models indicate a 0.8-sigma deviation in precipitation across northern biomes, affecting agro-ecological outputs."),
    ("SOCIAL", "Grassroots Sortition Literacy Programme Launched", "Citizens across municipalities participate in civic education modules on demarchic governance, raising participatory awareness."),
    ("ECONOMIC", "Leontief Input-Output Recalibration Required", "Structural changes in energy distribution have altered the technical matrix, requiring a Jacobi-iteration recalculation of embedded labour hours."),
    ("POLITICAL", "Federal Lottery Draw Triggers Constitutional Review", "A newly drawn federal councillor proposes a constitutional amendment, triggering review procedures across the five-council mesh."),
    ("CLIMATE", "Solar Energy Grid Expansion Milestone Reached", "State-owned solar cooperatives in the north-east achieve a new generation threshold, altering the energy sector Leontief coefficient."),
    ("SOCIAL", "Universal Basic Services Index Rises 0.03 Points", "Aggregate data from 26 states indicates improvement in combined health and education provision, reflecting policy compliance."),
    ("ECONOMIC", "Automation Productivity Shock in Industrial Sector", "Introduction of CNC-integrated robotics in metalworking cooperatives has altered the direct labour coefficient for industrial inputs."),
    ("POLITICAL", "Military Subordination Protocol Successfully Executed", "A routine multi-sig civilian oversight order to the High Command was authenticated by the full Defence Chamber without incident."),
    ("CLIMATE", "Cerrado Biome Carbon Sequestration Peaks", "Carbon sink data from the central savannah shows above-baseline sequestration, improving the planetary boundary constraint margin."),
    ("SOCIAL", "Inter-Generational Stratification Recalibration", "The sortition engine detected a minor generational imbalance in council composition, triggering a Hamilton-quota correction."),
    ("ECONOMIC", "Workers Cooperative Merger Increases 1/N Base", "Two metalworking cooperatives in Paraná unite their worker rosters, expanding the eligible surplus-sharing population."),
    ("POLITICAL", "Cybernetic Budget Plebiscite Turnout Record", "Anonymous token issuance for the annual macro-allocation vote broke a ten-year record."),
    ("SOCIAL", "Healthcare Distribution Normalises Across Strata", "Statistical distribution of healthcare access across income strata has narrowed, indicating convergence toward the target Gini reduction trajectory."),
    ("CLIMATE", "Flood Risk Matrix Updated for Coastal Regions", "LIDAR survey data reveals coastal land-use changes in Rio and Bahia states requiring updated vulnerability coefficients."),
    ("ECONOMIC", "Kantorovich Plan Identifies New Expansion Path", "A Kantorovich ray-expansion calculation reveals a feasible output-expansion trajectory under current capacity constraints."),
    ("POLITICAL", "Ex-Councillor Successfully Reinstated Under Protection Lock", "A citizen completing their demarchic mandate has been reinstated with the 180-day employment stability lock duly activated."),
    ("SOCIAL", "Cross-Regional Educational Equalisation Programme Begins", "Federal allocative directive resources are channelled into eight low-HDI municipalities to reduce educational provision variance."),
)


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
class GovernorSlot:
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


@dataclass
class GovernanceCycle:
    year: int
    regions: tuple[RegionProfile, ...]
    governors: tuple[GovernorSlot, ...]
    events: tuple[EmergentEvent, ...]
    aggregate_hdi: float
    aggregate_gini: float
    aggregate_employment: float


def _hash_citizen_id(region_id: str, citizen_index: int) -> str:
    payload = f"{region_id}:{citizen_index}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


class NationSimulationEngine:
    POPULATION_SIZE: int = 1_000_000
    SIMULATION_YEARS: int = 10

    def __init__(self, seed: int = 42) -> None:
        self._base_seed = seed
        self.current_year: int = 1
        self.regions: tuple[RegionProfile, ...] = self._initialize_regions()
        self.cycles: list[GovernanceCycle] = []
        self._served_citizen_hashes: set[str] = set()

    def _initialize_regions(self) -> tuple[RegionProfile, ...]:
        rng = random.Random(self._base_seed)
        return tuple(
            RegionProfile(
                region_id=region_id,
                name=name,
                lat=lat,
                lon=lon,
                population_size=pop,
                hdi=round(0.55 + rng.random() * 0.35, 3),
                gini=round(0.35 + rng.random() * 0.25, 3),
                employment_rate=round(0.70 + rng.random() * 0.20, 3),
            )
            for region_id, name, lat, lon, pop in BRAZIL_REGIONS
        )

    def advance_year(self, event_matrix: StochasticEventMatrix) -> GovernanceCycle:
        year = self.current_year
        cycle_seed = self._base_seed * 1000 + year * 7 + 13
        events = event_matrix.generate_cycle_events(year, cycle_seed)
        governors = self._draw_governors(year, cycle_seed)
        updated = tuple(self._apply_event_effects(r, events) for r in self.regions)
        self.regions = updated
        total_pop = sum(r.population_size for r in self.regions)
        safe_pop = max(1, total_pop)
        agg_hdi = sum(r.hdi * r.population_size for r in self.regions) / safe_pop
        agg_gini = sum(r.gini * r.population_size for r in self.regions) / safe_pop
        agg_emp = sum(r.employment_rate * r.population_size for r in self.regions) / safe_pop
        cycle = GovernanceCycle(
            year=year,
            regions=self.regions,
            governors=governors,
            events=events,
            aggregate_hdi=round(agg_hdi, 4),
            aggregate_gini=round(agg_gini, 4),
            aggregate_employment=round(agg_emp, 4),
        )
        self.cycles.append(cycle)
        self.current_year += 1
        return cycle

    def _draw_governors(self, year: int, cycle_seed: int) -> tuple[GovernorSlot, ...]:
        rng = random.Random(cycle_seed + year * 13)
        slots: list[GovernorSlot] = []
        for portfolio in GOVERNANCE_PORTFOLIOS:
            region = rng.choice(self.regions)
            citizen_hash = self._draw_unique_citizen(rng, region)
            slots.append(GovernorSlot(
                portfolio=portfolio,
                citizen_hash=citizen_hash,
                region_id=region.region_id,
                term_year=year,
            ))
        return tuple(slots)

    def _draw_unique_citizen(self, rng: random.Random, region: RegionProfile) -> str:
        while True:
            index = rng.randint(0, region.population_size - 1)
            citizen_hash = _hash_citizen_id(region.region_id, index)
            if citizen_hash not in self._served_citizen_hashes:
                self._served_citizen_hashes.add(citizen_hash)
                return citizen_hash

    @staticmethod
    def _apply_event_effects(
        region: RegionProfile, events: tuple[EmergentEvent, ...]
    ) -> RegionProfile:
        delta_hdi = 0.0
        delta_gini = 0.0
        delta_emp = 0.0
        for event in events:
            if region.region_id in event.affected_region_ids:
                delta_hdi += event.welfare_delta * 0.01
                delta_gini -= event.welfare_delta * 0.005
                delta_emp += event.gdp_delta * 0.02
        return RegionProfile(
            region_id=region.region_id,
            name=region.name,
            lat=region.lat,
            lon=region.lon,
            population_size=region.population_size,
            hdi=round(max(0.0, min(1.0, region.hdi + delta_hdi)), 4),
            gini=round(max(0.0, min(1.0, region.gini + delta_gini)), 4),
            employment_rate=round(max(0.0, min(1.0, region.employment_rate + delta_emp)), 4),
        )

    def serialise_for_renderer(self) -> dict:
        base: dict = {
            "year": self.current_year,
            "total_years": self.SIMULATION_YEARS,
            "population_size": self.POPULATION_SIZE,
            "regions": [
                {
                    "region_id": r.region_id,
                    "name": r.name,
                    "lat": r.lat,
                    "lon": r.lon,
                    "population_size": r.population_size,
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
        }
        return base


class StochasticEventMatrix:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def generate_cycle_events(self, year: int, base_seed: int) -> tuple[EmergentEvent, ...]:
        rng = random.Random(base_seed * 137 + year * 31 + self.seed * 7)
        count = rng.randint(2, 5)
        indices = list(range(len(_EVENT_TEMPLATES)))
        rng.shuffle(indices)
        selected = indices[:count]
        result: list[EmergentEvent] = []
        for idx in selected:
            result.append(self._instantiate_template(idx, rng, year))
        return tuple(result)

    @staticmethod
    def _instantiate_template(template_index: int, rng: random.Random, year: int) -> EmergentEvent:
        template = _EVENT_TEMPLATES[template_index]
        region_pool = [r[0] for r in BRAZIL_REGIONS]
        affected_count = rng.randint(1, min(3, len(region_pool)))
        affected = tuple(rng.sample(region_pool, affected_count))
        severity = round(0.1 + rng.random() * 0.9, 3)
        gdp_delta = round((rng.random() - 0.4) * 3.0, 3)
        welfare_delta = round((rng.random() - 0.3) * 2.0, 3)
        return EmergentEvent(
            event_id=f"EVT-{year:02d}-{template_index:03d}",
            category=template[0],
            title=template[1],
            narrative=template[2],
            affected_region_ids=affected,
            severity=severity,
            gdp_delta=gdp_delta,
            welfare_delta=welfare_delta,
        )
