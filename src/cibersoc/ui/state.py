from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Mapping, Sequence

from ..audit import (
    CleanCodeAuditReport,
    ProjectIntegrityReport,
    audit_clean_code_compliance,
    audit_project_integrity,
)
from ..councils import (
    AgendaItem,
    AutocraticActForbiddenError,
    CivilianMilitaryCommandGate,
    CollegiateResolution,
    CouncilProportionalityMetric,
    CouncilTier,
    DemarchicCouncil,
    EscalatedCouncilMesh,
    FederatedSeatProportionality,
    GeneralOfficer,
    MilitarySubordinationViolationError,
    PopularJuryCase,
    PopularJuryVerdict,
    PublicSecurityDispatch,
    SecretaryGeneral,
)
from ..cybernetics import (
    CompressedSparseRowMatrix,
    CompulsoryAllocationDirective,
    CompulsoryDirectiveOverrideError,
    InNaturaEcologicalConstraint,
    InvalidPlebisciteTopicError,
    KantorovichPlanRayResult,
    MacroAllocationOption,
    MacroAllocationPlebiscite,
    MarketClearingFeedbackMetric,
    audit_in_natura_ecological_budget,
    evaluate_market_clearing_feedback,
    relax_short_run_capacity_harmony,
    solve_kantorovich_plan_ray_expansion,
)
from ..enterprise import (
    OrganisationalViolationError,
    ProfitDistributionReceipt,
    SocialistEnterprise,
    WorkerMember,
)
from ..i18n.translator import LocalizationCatalog
from ..mandate_protection import (
    EmploymentStabilityLockError,
    MandateProtectionManager,
    MandateProtectionRecord,
    PriceIndexSeries,
)
from ..sortition import (
    CitizenProfile,
    CommitRevealEntropyBeacon,
    ElectoralOperationForbiddenError,
    MinistryPortfolio,
    SortitionAuditProof,
    StratifiedSortitionEngine,
)

COUNCIL_TOPOLOGY_SPECIFICATIONS: tuple[
    tuple[str, CouncilTier, str | None, int, bool, str | None, str | None, str | None], ...
] = (
    ("CONS-FED-BRASIL", CouncilTier.FEDERAL, None, 20, True, None, None, None),
    ("CONS-EST-PARANA", CouncilTier.STATE, "CONS-FED-BRASIL", 16, False, "EST-PARANA", None, None),
    (
        "CONS-MUN-CURITIBA",
        CouncilTier.MUNICIPAL,
        "CONS-EST-PARANA",
        20,
        False,
        "EST-PARANA",
        "MUN-CURITIBA",
        None,
    ),
    (
        "CONS-SET-BOQUEIRAO",
        CouncilTier.SECTORAL,
        "CONS-MUN-CURITIBA",
        10,
        False,
        "EST-PARANA",
        "MUN-CURITIBA",
        "CURITIBA-BOQUEIRAO",
    ),
    (
        "CONS-SET-MATRIZ",
        CouncilTier.SECTORAL,
        "CONS-MUN-CURITIBA",
        10,
        False,
        "EST-PARANA",
        "MUN-CURITIBA",
        "CURITIBA-MATRIZ",
    ),
)

COOPERATIVE_WORKER_ROLE_KEYS: tuple[str, ...] = (
    "worker.role.cnc_machinist",
    "worker.role.metallurgical_engineer",
    "worker.role.plc_automation_tech",
    "worker.role.quality_metrologist",
    "worker.role.industrial_electrician",
    "worker.role.foundry_operator",
    "worker.role.tooling_specialist",
    "worker.role.logistics_planner",
)


@dataclass(frozen=True)
class LocalizedAuditEvent:
    message_key: str
    parameters: Mapping[str, object]
    is_safeguard_alert: bool = False

    def render(self, translator: LocalizationCatalog) -> str:
        available_keys = translator.available_keys
        resolved_parameters: dict[str, object] = {}
        for key, raw_value in self.parameters.items():
            if isinstance(raw_value, bool):
                resolved_parameters[key] = translator.translate(
                    "status.yes" if raw_value else "status.no"
                )
            elif isinstance(raw_value, str) and raw_value in available_keys:
                resolved_parameters[key] = translator.translate(raw_value)
            elif isinstance(raw_value, tuple):
                rendered_items = [
                    (
                        translator.translate(item)
                        if isinstance(item, str) and item in available_keys
                        else str(item)
                    )
                    for item in raw_value
                ]
                resolved_parameters[key] = " → ".join(rendered_items)
            else:
                resolved_parameters[key] = raw_value
        return translator.translate(self.message_key, **resolved_parameters)


@dataclass(frozen=True)
class CycleTransitionSummary:
    cycle_number: int
    quarantined_from_previous: int
    overlapping_consecutive_members: int
    all_proofs_valid: bool


@dataclass(frozen=True)
class StrategicMilitaryOrderSummary:
    order_id: str
    minister_id: str
    multisig_token: str


class SimulationOrchestrator:
    def __init__(
        self,
        cibersoc_root: Path | None = None,
    ) -> None:
        default_root = Path(__file__).resolve().parents[3]
        self.cibersoc_root = cibersoc_root or default_root

        self.population: list[CitizenProfile] = self._generate_federated_population()
        self.sortition_engine = StratifiedSortitionEngine(cooldown_cycles=1)
        self.current_cycle: int = 0
        self.mesh = EscalatedCouncilMesh()
        self.proofs_by_council: dict[str, tuple[SortitionAuditProof, bool]] = {}
        self.military_gate: CivilianMilitaryCommandGate | None = None
        self.last_cycle_summary: CycleTransitionSummary | None = None
        self._demand_sequence: int = 0
        self._resolution_sequence: int = 0
        self._jury_case_sequence: int = 0
        self._security_protocol_sequence: int = 0

        self.enterprise = SocialistEnterprise(
            enterprise_id="EMP-COOP-METAL-PR",
            name="enterprise.default_name",
            sector_code="IND-METAL",
        )
        for worker_index, citizen in enumerate(self.population[:8]):
            self.enterprise.register_worker(
                WorkerMember(
                    worker_id=citizen.citizen_id,
                    full_name=citizen.full_name,
                    role_title=COOPERATIVE_WORKER_ROLE_KEYS[worker_index],
                    monthly_base_pay=citizen.prior_monthly_income,
                    active_days_in_period=30,
                )
            )
        self.price_index_series = PriceIndexSeries(base_index=Decimal("100.000000"))
        self.protection_manager = MandateProtectionManager({"EMP-COOP-METAL-PR": self.enterprise})
        self.tracked_worker_id: str = self.population[0].citizen_id
        self._mandate_month_cursor: int = 0
        self._mandate_year_cursor: int = 2026
        self.current_gross_revenue: Decimal = Decimal("185000.00")
        self.current_capital_charge: Decimal = Decimal("4000.00")
        self.last_profit_receipt: ProfitDistributionReceipt | None = None

        self.sector_keys: tuple[str, ...] = (
            "sector.public_education",
            "sector.public_health",
            "sector.industry_inputs",
            "sector.energy_infrastructure",
        )
        self.technical_matrix = CompressedSparseRowMatrix.from_dense(
            [
                [0.04, 0.02, 0.03, 0.02],
                [0.01, 0.06, 0.02, 0.01],
                [0.12, 0.18, 0.22, 0.20],
                [0.08, 0.10, 0.16, 0.15],
            ]
        )
        self.direct_labour_vector = (0.55, 0.60, 0.35, 0.30)
        self.capacity_ceilings = (260.0, 260.0, 520.0, 420.0)
        self.last_directive: CompulsoryAllocationDirective | None = None
        self.last_harmonies: tuple[float, ...] = ()
        self._plebiscite_sequence: int = 0

        self.audit_events: list[LocalizedAuditEvent] = []
        self.last_scan_results: tuple[ProjectIntegrityReport, CleanCodeAuditReport] | None = None

        self.execute_next_sortition_cycle()
        self.execute_profit_distribution()
        self.execute_macro_plebiscite(votes_education=432, votes_health=568)

    @staticmethod
    def _generate_federated_population() -> list[CitizenProfile]:
        given_names = (
            "Helena",
            "Mateus",
            "Beatriz",
            "Rafael",
            "Camila",
            "Lucas",
            "Mariana",
            "Gabriel",
            "Larissa",
            "Thiago",
            "Fernanda",
            "Bruno",
            "Juliana",
            "Diego",
            "Aline",
            "Rodrigo",
        )
        family_names = (
            "Almeida",
            "Ferreira",
            "Nascimento",
            "Cavalcanti",
            "Oliveira",
            "Ribeiro",
            "Cardoso",
            "Moreira",
            "Teixeira",
            "Barbosa",
            "Carvalho",
            "Monteiro",
            "Mendes",
            "Araujo",
            "Santana",
            "Correia",
            "Rocha",
            "Pinto",
            "Freitas",
            "Gomes",
        )
        strata = ("INDUSTRY", "HEALTH_EDUCATION", "LOGISTICS_SERVICES", "SCIENCE_ENGINEERING")
        citizens: list[CitizenProfile] = []
        for index in range(1, 321):
            if index <= 100:
                state_id = "EST-PARANA"
                municipality_id = "MUN-CURITIBA"
                sector_id = "CURITIBA-BOQUEIRAO"
                employer_id = "EMP-COOP-METAL-PR" if index <= 8 else "EMP-PUBLIC-GRID-PR"
            elif index <= 200:
                state_id = "EST-PARANA"
                municipality_id = "MUN-CURITIBA"
                sector_id = "CURITIBA-MATRIZ"
                employer_id = "EMP-CLINIC-NETWORK-PR"
            elif index <= 260:
                state_id = "EST-PARANA"
                municipality_id = "MUN-LONDRINA"
                sector_id = "LONDRINA-CENTRO"
                employer_id = "EMP-AGRO-TECH-PR"
            else:
                state_id = "EST-BAHIA"
                municipality_id = "MUN-SALVADOR"
                sector_id = "SALVADOR-BROTAS"
                employer_id = "EMP-SOLAR-PORT-BA"

            is_military = index % 20 == 0
            given = given_names[(index - 1) % len(given_names)]
            surname = family_names[((index - 1) // len(given_names)) % len(family_names)]
            citizens.append(
                CitizenProfile(
                    citizen_id=f"CID-{index:04d}",
                    full_name=f"{given} {surname}",
                    sector_id=sector_id,
                    municipality_id=municipality_id,
                    state_id=state_id,
                    stratum_key=strata[index % len(strata)],
                    is_military_personnel=is_military,
                    prior_monthly_income=Decimal("4200.00") + Decimal((index % 7) * 350),
                    employer_id=employer_id,
                    job_role=(
                        COOPERATIVE_WORKER_ROLE_KEYS[index - 1]
                        if index <= 8
                        else (
                            "worker.role.technical_officer"
                            if is_military
                            else "worker.role.operational_specialist"
                        )
                    ),
                )
            )
        return citizens

    @staticmethod
    def _build_entropy_beacon(scope_id: str, cycle_number: int) -> CommitRevealEntropyBeacon:
        beacon = CommitRevealEntropyBeacon(minimum_sources=3)
        sources = (
            ("UNIV-CRYPTO-NODE", f"univ-{scope_id}-c{cycle_number}", f"n1-{cycle_number}"),
            ("CIVIC-AUDIT-SOUTH", f"south-{scope_id}-c{cycle_number}", f"n2-{cycle_number}"),
            ("LABOUR-OBSERVATORY", f"obs-{scope_id}-c{cycle_number}", f"n3-{cycle_number}"),
        )
        for source_id, secret_seed, nonce in sources:
            beacon.publish_commitment(
                source_id, CommitRevealEntropyBeacon.create_commitment(secret_seed, nonce)
            )
        beacon.lock_commitments()
        for source_id, secret_seed, nonce in sources:
            beacon.reveal_seed(source_id, secret_seed, nonce)
        return beacon

    def record_audit_event(
        self, message_key: str, is_safeguard_alert: bool = False, **parameters: object
    ) -> None:
        self.audit_events.append(
            LocalizedAuditEvent(
                message_key=message_key,
                parameters=parameters,
                is_safeguard_alert=is_safeguard_alert,
            )
        )

    def execute_next_sortition_cycle(self) -> CycleTransitionSummary:
        outgoing_member_ids: set[str] = set()
        if self.current_cycle > 0:
            for council in self.mesh.list_councils():
                outgoing_member_ids.update(member.citizen_id for member in council.members)
            self.sortition_engine.register_mandate_completion(
                sorted(outgoing_member_ids), self.current_cycle
            )

        self.current_cycle += 1
        next_mesh = EscalatedCouncilMesh()
        next_proofs: dict[str, tuple[SortitionAuditProof, bool]] = {}
        newly_drawn_ids: set[str] = set()

        for (
            council_id,
            tier,
            parent_id,
            seat_count,
            has_defence,
            state_filter,
            municipality_filter,
            sector_filter,
        ) in COUNCIL_TOPOLOGY_SPECIFICATIONS:
            territorial_pool = StratifiedSortitionEngine.filter_by_territorial_jurisdiction(
                self.population,
                state_id=state_filter,
                municipality_id=municipality_filter,
                sector_id=sector_filter,
            )
            eligible_snapshot = self.sortition_engine.filter_eligible_citizens(
                territorial_pool, self.current_cycle
            )
            drawn_members, audit_proof = self.sortition_engine.draw_council(
                scope_id=council_id,
                cycle_number=self.current_cycle,
                population=territorial_pool,
                total_seats=seat_count,
                beacon=self._build_entropy_beacon(council_id, self.current_cycle),
            )
            proof_verified = StratifiedSortitionEngine.verify_audit_proof(
                eligible_citizen_ids=[citizen.citizen_id for citizen in eligible_snapshot],
                proof=audit_proof,
                eligible_strata_by_id={
                    citizen.citizen_id: citizen.stratum_key for citizen in eligible_snapshot
                },
            )
            secretary_profile, chambers = StratifiedSortitionEngine.assign_internal_roles(
                councillors=drawn_members,
                include_defence_ministry=has_defence,
                master_seed_hex=audit_proof.master_seed_hex,
            )
            secretary = SecretaryGeneral(
                profile=secretary_profile, council_id=council_id, tier=tier
            )
            council = DemarchicCouncil(
                council_id=council_id,
                name=f"council.{council_id}",
                tier=tier,
                parent_council_id=parent_id,
                members=drawn_members,
                secretary_general=secretary,
                portfolios=chambers,
            )
            next_mesh.register_council(council)
            next_proofs[council_id] = (audit_proof, proof_verified)
            newly_drawn_ids.update(member.citizen_id for member in drawn_members)

        self.mesh = next_mesh
        self.proofs_by_council = next_proofs

        federal_council = self.mesh.get_council("CONS-FED-BRASIL")
        defence_chamber = federal_council.portfolios[MinistryPortfolio.DEFENCE]
        self.military_gate = CivilianMilitaryCommandGate(
            civilian_minister=defence_chamber[0],
            defence_chamber_civilians=defence_chamber,
            secretary_general=federal_council.secretary_general,
            subordinate_generals=[
                GeneralOfficer("GEN-01", "General", "Carlos Eduardo Mendes", "1R"),
            ],
        )

        consecutive_overlap = len(outgoing_member_ids & newly_drawn_ids)
        all_valid = all(is_valid for _, is_valid in next_proofs.values())
        summary = CycleTransitionSummary(
            cycle_number=self.current_cycle,
            quarantined_from_previous=len(outgoing_member_ids),
            overlapping_consecutive_members=consecutive_overlap,
            all_proofs_valid=all_valid,
        )
        self.last_cycle_summary = summary
        self.record_audit_event(
            "log.cycle_completed",
            cycle=self.current_cycle,
            active=len(newly_drawn_ids),
            quarantined=summary.quarantined_from_previous,
            overlap=consecutive_overlap,
            valid=str(all_valid),
        )
        return summary

    def escalate_demand_from_sector(
        self, sectoral_council_id: str, title: str, urgency_level: int = 4
    ) -> list[str]:
        self._demand_sequence += 1
        demand_item = AgendaItem(
            item_id=f"DEM-{self._demand_sequence:03d}",
            title=title,
            portfolio=MinistryPortfolio.HEALTH,
            urgency_level=urgency_level,
            origin_council_id=sectoral_council_id,
            submission_sequence=self._demand_sequence,
        )
        route = self.mesh.escalate_citizen_demand(sectoral_council_id, demand_item)
        self.record_audit_event(
            "log.demand_escalated",
            item_id=demand_item.item_id,
            route=tuple(f"council.{cid}" for cid in route),
        )
        return route

    def secretary_order_and_authenticate(self, council_id: str) -> CollegiateResolution:
        council = self.mesh.get_council(council_id)
        self._resolution_sequence += 1
        pending_items = [
            AgendaItem(
                "AG-ROUTINE",
                "Preventive Sectoral Maintenance",
                MinistryPortfolio.INFRASTRUCTURE_ECOLOGY,
                2,
                council_id,
                2,
            ),
            AgendaItem(
                "AG-URGENT",
                "Logistical Execution of Allocative Targets",
                MinistryPortfolio.ECONOMY,
                5,
                council_id,
                1,
            ),
        ]
        ordered_items = council.secretary_general.order_meeting_agenda(pending_items)
        priority_item = ordered_items[0]
        sorted_member_ids = sorted(council.member_ids)
        majority_threshold = (len(sorted_member_ids) // 2) + 1
        ballots = {
            member_id: (index < majority_threshold)
            for index, member_id in enumerate(sorted_member_ids)
        }
        resolution = council.secretary_general.authenticate_resolution(
            resolution_id=f"RES-{self._resolution_sequence:03d}",
            agenda_item=priority_item,
            summary=f"Collegiate deliberation on '{priority_item.title}'",
            ballots_by_member=ballots,
            valid_member_ids=council.member_ids,
        )
        self.record_audit_event(
            "log.sg_authenticated",
            council=council.name,
            resolution_id=resolution.resolution_id,
            favour=resolution.votes_in_favour,
            total=resolution.total_council_members,
        )
        return resolution

    def test_secretary_autocratic_block(self, council_id: str) -> str:
        council = self.mesh.get_council(council_id)
        detail = ""
        try:
            council.secretary_general.attempt_veto("RES-PLENARY-01")
        except AutocraticActForbiddenError as error:
            detail = str(error)
        self.record_audit_event(
            "log.sg_veto_blocked",
            is_safeguard_alert=True,
            council=council.name,
            sg_id=council.secretary_general.profile.citizen_id,
        )
        return detail

    def adjudicate_popular_jury_case(self, council_id: str) -> PopularJuryVerdict:
        council = self.mesh.get_council(council_id)
        self._jury_case_sequence += 1
        jury_bench = council.active_popular_jury_bench()
        majority_count = (len(jury_bench) // 2) + 1
        ballots = {
            juror.citizen_id: (index < majority_count) for index, juror in enumerate(jury_bench)
        }
        case = PopularJuryCase(
            case_id=f"JURI-{self._jury_case_sequence:03d}",
            case_summary="Public cooperative audit and civil restitution review",
            council_id=council_id,
        )
        verdict = council.adjudicate_by_popular_jury(case, ballots)
        self.record_audit_event(
            "log.jury_verdict_sealed",
            council=council.name,
            case_id=verdict.case_id,
            upheld=verdict.votes_upheld,
            jurors=verdict.juror_count,
            hash_prefix=verdict.verdict_hash[:12],
        )
        return verdict

    def test_monocratic_sentence_block(self, council_id: str) -> str:
        council = self.mesh.get_council(council_id)
        detail = ""
        try:
            council.attempt_monocratic_judicial_sentence(
                council.secretary_general.profile.citizen_id, "JURI-MONO-01"
            )
        except AutocraticActForbiddenError as error:
            detail = str(error)
        self.record_audit_event(
            "log.jury_monocratic_blocked",
            is_safeguard_alert=True,
            council=council.name,
        )
        return detail

    def dispatch_public_security_action(self, council_id: str) -> PublicSecurityDispatch:
        council = self.mesh.get_council(council_id)
        self._security_protocol_sequence += 1
        security_members = council.portfolios[MinistryPortfolio.PUBLIC_SECURITY]
        justice_lead = council.portfolios[MinistryPortfolio.JUSTICE][0]
        majority_count = (len(security_members) // 2) + 1
        ballots = {
            member.citizen_id: (index < majority_count)
            for index, member in enumerate(security_members)
        }
        dispatch = council.dispatch_public_security_protocol(
            protocol_id=f"SEG-{self._security_protocol_sequence:03d}",
            protocol_summary="Preventive community lighting and civil protection patrol",
            ballots_by_member=ballots,
            justice_oversight_lead_id=justice_lead.citizen_id,
        )
        self.record_audit_event(
            "log.security_dispatched",
            council=council.name,
            protocol_id=dispatch.protocol_id,
            favour=dispatch.approving_security_members,
            total=dispatch.total_security_members,
            justice_id=dispatch.justice_oversight_lead_id,
        )
        return dispatch

    def test_warrantless_security_block(self, council_id: str) -> str:
        council = self.mesh.get_council(council_id)
        detail = ""
        try:
            council.attempt_warrantless_security_measure("Unauthorised warrantless surveillance")
        except AutocraticActForbiddenError as error:
            detail = str(error)
        self.record_audit_event(
            "log.security_warrantless_blocked",
            is_safeguard_alert=True,
            council=council.name,
        )
        return detail

    def issue_valid_civil_defence_order(self) -> StrategicMilitaryOrderSummary:
        assert self.military_gate is not None
        federal_council = self.mesh.get_council("CONS-FED-BRASIL")
        chamber_ids = [
            member.citizen_id for member in federal_council.portfolios[MinistryPortfolio.DEFENCE]
        ]
        order = self.military_gate.issue_strategic_order(
            order_id=f"ORD-CIV-{self.current_cycle:02d}",
            directive_description="Civil engineering bridge support under civilian oversight",
            target_general_id="GEN-01",
            signed_by_minister_id=self.military_gate.civilian_minister.citizen_id,
            signed_by_secretary_id=federal_council.secretary_general.profile.citizen_id,
            chamber_approving_ids=chamber_ids,
        )
        self.record_audit_event(
            "log.defence_order_issued",
            order_id=order.order_id,
            minister_id=order.civilian_minister_id,
            approvals=len(order.defence_chamber_approvals),
            token_prefix=order.multisig_token[:14],
        )
        return StrategicMilitaryOrderSummary(
            order.order_id, order.civilian_minister_id, order.multisig_token
        )

    def test_military_insubordination_block(self) -> str:
        assert self.military_gate is not None
        detail = ""
        try:
            self.military_gate.attempt_autonomous_general_mobilisation(
                "GEN-01", "Unauthorised troop movement"
            )
        except MilitarySubordinationViolationError as error:
            detail = str(error)
        self.record_audit_event(
            "log.defence_insubordination_blocked",
            is_safeguard_alert=True,
            officer_id="GEN-01",
        )
        return detail

    def assess_council_proportionality(self, council_id: str) -> CouncilProportionalityMetric:
        target_council = self.mesh.get_council(council_id)
        child_sectoral_seats: list[int] = []
        for council in self.mesh.list_councils():
            if council.tier == CouncilTier.SECTORAL and (
                target_council.tier != CouncilTier.MUNICIPAL
                or council.parent_council_id == target_council.council_id
            ):
                child_sectoral_seats.append(len(council.members))
        return FederatedSeatProportionality.evaluate_council_metric(
            council_id=target_council.council_id,
            tier=target_council.tier,
            assigned_seats=len(target_council.members),
            child_sectoral_seats=child_sectoral_seats,
        )

    def test_electoral_candidacy_block(self) -> str:
        detail = ""
        try:
            StratifiedSortitionEngine.reject_electoral_mechanism("party candidacy registration")
        except ElectoralOperationForbiddenError as error:
            detail = str(error)
        self.record_audit_event("log.election_blocked", is_safeguard_alert=True)
        return detail

    def execute_macro_plebiscite(
        self, votes_education: int, votes_health: int
    ) -> CompulsoryAllocationDirective:
        self._plebiscite_sequence += 1
        option_education = MacroAllocationOption(
            option_id="FLOW-EDU-PLUS5",
            description="Allocate +5% of annual federal budget to Public Education and Technical Centres",
            target_final_demand=(165.0, 140.0, 180.0, 130.0),
            budget_shares_pct={
                "sector.public_education": 30.0,
                "sector.public_health": 25.0,
                "sector.industry_inputs": 25.0,
                "sector.energy_infrastructure": 20.0,
            },
        )
        option_health = MacroAllocationOption(
            option_id="FLOW-HEALTH-PLUS5",
            description="Allocate +5% of annual federal budget to Public Health and State Pharmaceuticals",
            target_final_demand=(140.0, 165.0, 180.0, 130.0),
            budget_shares_pct={
                "sector.public_education": 25.0,
                "sector.public_health": 30.0,
                "sector.industry_inputs": 25.0,
                "sector.energy_infrastructure": 20.0,
            },
        )
        plebiscite = MacroAllocationPlebiscite(
            plebiscite_id=f"PLEB-FED-{self._plebiscite_sequence:02d}",
            question_prompt=(
                "Should we allocate +5% of this year's budget to Public Education or to Public Health?"
            ),
            sector_keys=self.sector_keys,
            technical_matrix=self.technical_matrix,
            direct_labour_vector=self.direct_labour_vector,
            capacity_ceiling=self.capacity_ceilings,
            max_available_labour_hours=600.0,
            options=[option_education, option_health],
        )
        ballot_cursor = 0
        for _ in range(votes_education):
            ballot_cursor += 1
            plebiscite.cast_anonymous_ballot(
                f"TOK-{self._plebiscite_sequence}-{ballot_cursor}", "FLOW-EDU-PLUS5"
            )
        for _ in range(votes_health):
            ballot_cursor += 1
            plebiscite.cast_anonymous_ballot(
                f"TOK-{self._plebiscite_sequence}-{ballot_cursor}", "FLOW-HEALTH-PLUS5"
            )

        directive = plebiscite.tally_and_seal_directive()
        self.mesh.broadcast_compulsory_macro_directive(
            {
                "plebiscite_id": directive.plebiscite_id,
                "winning_option": directive.winning_option_id,
                "directive_hash": directive.directive_hash,
            }
        )
        _, _, harmonies = relax_short_run_capacity_harmony(
            technical_matrix=self.technical_matrix,
            target_final_demand=directive.compulsory_final_demand,
            capacity_ceiling=(250.0, 250.0, 330.0, 400.0),
        )
        self.last_directive = directive
        self.last_harmonies = tuple(round(value, 4) for value in harmonies)
        self.record_audit_event(
            "log.plebiscite_sealed",
            plebiscite_id=directive.plebiscite_id,
            winner=f"plebiscite.option.{directive.winning_option_id}",
            ballots=directive.total_valid_ballots,
        )
        return directive

    @property
    def active_macro_directive(self) -> str | None:
        if self.last_directive is None:
            return None
        return self.last_directive.winning_option_id

    def test_plebiscite_person_topic_block(self) -> str:
        detail = ""
        try:
            MacroAllocationPlebiscite(
                plebiscite_id="PLEB-ILLEGAL",
                question_prompt="Which candidate should be elected president?",
                sector_keys=self.sector_keys,
                technical_matrix=self.technical_matrix,
                direct_labour_vector=self.direct_labour_vector,
                capacity_ceiling=self.capacity_ceilings,
                max_available_labour_hours=600.0,
                options=[],
            )
        except InvalidPlebisciteTopicError as error:
            detail = str(error)
        self.record_audit_event("log.plebiscite_person_blocked", is_safeguard_alert=True)
        return detail

    def test_council_budget_override_block(self) -> str:
        assert self.last_directive is not None
        tampered_shares = dict(self.last_directive.compulsory_budget_shares_pct)
        tampered_shares["sector.public_education"] -= 2.0
        tampered_shares["sector.public_health"] += 2.0
        detail = ""
        try:
            MacroAllocationPlebiscite.verify_council_execution_compliance(
                self.last_directive, tampered_shares
            )
        except CompulsoryDirectiveOverrideError as error:
            detail = str(error)
        self.record_audit_event("log.council_override_blocked", is_safeguard_alert=True)
        return detail

    def execute_profit_distribution(
        self,
        gross_revenue: Decimal | None = None,
        capital_equalisation_charge: Decimal | None = None,
    ) -> ProfitDistributionReceipt:
        if gross_revenue is not None:
            self.current_gross_revenue = gross_revenue
        if capital_equalisation_charge is not None:
            self.current_capital_charge = capital_equalisation_charge
        receipt = self.enterprise.distribute_period_profit(
            period_label=f"CYCLE-{self.current_cycle:02d}",
            period_total_days=30,
            gross_revenue=self.current_gross_revenue,
            audited_material_costs=Decimal("62000.00"),
            physical_depreciation_reserve=Decimal("14000.00"),
            macro_social_contribution=Decimal("21000.00"),
            capital_endowment_equalisation_charge=self.current_capital_charge,
        )
        self.last_profit_receipt = receipt
        self.record_audit_event(
            "log.profit_distributed",
            enterprise=self.enterprise.name,
            net_profit=receipt.distributable_net_profit,
            workers=receipt.eligible_worker_count,
            share=receipt.equal_full_share_per_worker,
            retained=receipt.corporate_retained_profit,
        )
        return receipt

    def test_ceo_appointment_block(self) -> str:
        detail = ""
        try:
            self.enterprise.register_worker(
                WorkerMember(
                    worker_id="CID-CEO-99",
                    full_name="Abolished Executive",
                    role_title="CEO / Chief Executive Officer",
                    monthly_base_pay=Decimal("45000.00"),
                    active_days_in_period=30,
                )
            )
        except OrganisationalViolationError as error:
            detail = str(error)
        self.record_audit_event("log.ceo_blocked", is_safeguard_alert=True)
        return detail

    def start_tracked_worker_mandate(self) -> MandateProtectionRecord:
        existing_record = self.protection_manager.get_record(self.tracked_worker_id)
        if existing_record is not None and existing_record.reinstated_on is None:
            return existing_record

        start_date = date(self._mandate_year_cursor, 1, 1)
        end_date = date(self._mandate_year_cursor, 12, 31)
        self._mandate_year_cursor += 2
        worker = self.enterprise.workers[self.tracked_worker_id]
        record = self.protection_manager.activate_council_mandate(
            citizen_id=self.tracked_worker_id,
            council_id="CONS-MUN-CURITIBA",
            tier=CouncilTier.MUNICIPAL,
            employer_id=self.enterprise.enterprise_id,
            prior_civilian_monthly_income=worker.monthly_base_pay,
            current_price_index=self.price_index_series.current_index,
            start_date=start_date,
            end_date=end_date,
        )
        self.record_audit_event(
            "log.mandate_started",
            worker_id=record.citizen_id,
            council=f"council.{record.council_id}",
            income=record.prior_civilian_monthly_income,
            cpi=record.entry_price_index,
        )
        self.execute_profit_distribution()
        return record

    def advance_inflation_and_compute_stipend(
        self, monthly_rate: Decimal = Decimal("0.0050")
    ) -> Decimal:
        self.start_tracked_worker_mandate()
        self._mandate_month_cursor += 1
        self.price_index_series.apply_monthly_inflation(
            f"M{self._mandate_month_cursor:02d}", monthly_rate
        )
        stipend = self.protection_manager.compute_state_councillor_stipend(
            self.tracked_worker_id, self.price_index_series.current_index
        )
        self.record_audit_event(
            "log.mandate_cpi_updated",
            cpi=self.price_index_series.current_index,
            worker_id=self.tracked_worker_id,
            stipend=stipend,
        )
        return stipend

    def reinstate_tracked_worker(self) -> MandateProtectionRecord:
        active_record = self.start_tracked_worker_mandate()
        return_date = active_record.mandate_end_date + timedelta(days=1)
        reinstated_record = self.protection_manager.conclude_mandate_and_reinstate(
            citizen_id=self.tracked_worker_id,
            return_date=return_date,
            current_price_index=self.price_index_series.current_index,
            stability_days=180,
        )
        self.record_audit_event(
            "log.mandate_reinstated",
            worker_id=reinstated_record.citizen_id,
            reinstated_on=reinstated_record.reinstated_on,
            base_pay=reinstated_record.reinstated_monthly_base_pay,
            locked_until=reinstated_record.stability_locked_until,
        )
        self.execute_profit_distribution()
        return reinstated_record

    def test_post_mandate_dismissal_lock(self) -> str:
        record = self.protection_manager.get_record(self.tracked_worker_id)
        if record is None or record.reinstated_on is None:
            record = self.reinstate_tracked_worker()
        assert record.reinstated_on is not None
        detail = ""
        try:
            self.protection_manager.validate_termination_attempt(
                self.tracked_worker_id, record.reinstated_on + timedelta(days=60)
            )
        except EmploymentStabilityLockError as error:
            detail = str(error)
        self.record_audit_event(
            "log.mandate_dismissal_blocked",
            is_safeguard_alert=True,
            worker_id=self.tracked_worker_id,
            locked_until=record.stability_locked_until,
        )
        return detail

    def execute_project_integrity_audit(
        self,
    ) -> tuple[ProjectIntegrityReport, CleanCodeAuditReport]:
        integrity_report = audit_project_integrity(self.cibersoc_root)
        clean_code_report = audit_clean_code_compliance(self.cibersoc_root)
        self.last_scan_results = (integrity_report, clean_code_report)
        self.record_audit_event(
            "log.integrity_audited",
            scanned_files=integrity_report.project_files_scanned,
            locales=", ".join(integrity_report.documentation_locales_verified),
            self_contained=integrity_report.is_self_contained,
            clean=clean_code_report.is_compliant,
        )
        return integrity_report, clean_code_report

    def evaluate_market_clearing(
        self,
        sector_id: str,
        labor_value_hours: float,
        market_clearing_price_tokens: float,
        response_gain: float = 0.5,
    ) -> MarketClearingFeedbackMetric:
        return evaluate_market_clearing_feedback(
            sector_id=sector_id,
            labor_value_hours=labor_value_hours,
            market_clearing_price_tokens=market_clearing_price_tokens,
            response_gain=response_gain,
        )

    def solve_plan_ray(
        self,
        proportional_ray: Sequence[float],
        available_capacities: Sequence[float],
        unit_input_requirements: Sequence[float],
    ) -> KantorovichPlanRayResult:
        return solve_kantorovich_plan_ray_expansion(
            proportional_ray=proportional_ray,
            available_capacities=available_capacities,
            unit_input_requirements=unit_input_requirements,
        )

    def audit_carbon_budget(
        self,
        annual_carbon_budget_megatons: float,
        sector_outputs: Sequence[float],
        carbon_intensity_per_output: Sequence[float],
    ) -> InNaturaEcologicalConstraint:
        return audit_in_natura_ecological_budget(
            annual_carbon_budget_megatons=annual_carbon_budget_megatons,
            sector_outputs=sector_outputs,
            carbon_intensity_per_output=carbon_intensity_per_output,
        )
