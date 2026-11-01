from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
from typing import Mapping, Sequence

from .sortition import (
    CitizenProfile,
    CivilianSupremacyViolationError,
    CounterModeHmacDrbg,
    MinistryPortfolio,
)


class AutocraticActForbiddenError(RuntimeError):
    pass


class MilitarySubordinationViolationError(RuntimeError):
    pass


class CouncilTier(StrEnum):
    SECTORAL = "SECTORAL"
    MUNICIPAL = "MUNICIPAL"
    STATE = "STATE"
    FEDERAL = "FEDERAL"


FORBIDDEN_SUPREME_TITLES: frozenset[str] = frozenset(
    {
        "president",
        "president of the republic",
        "prime minister",
        "governor",
        "mayor",
        "head of state",
        "supreme leader",
        "presidente",
        "presidente da republica",
        "presidente da república",
        "primeiro-ministro",
        "primeiro ministro",
        "primer ministro",
        "governador",
        "gobernador",
        "prefeito",
        "alcalde",
    }
)


def assert_no_autocratic_title(role_title: str) -> None:
    normalized_title = " ".join(role_title.strip().lower().split())
    if normalized_title in FORBIDDEN_SUPREME_TITLES:
        raise AutocraticActForbiddenError(
            f"The supreme executive title '{role_title}' is permanently abolished in CIBERSOC."
        )


@dataclass(frozen=True)
class AgendaItem:
    item_id: str
    title: str
    portfolio: MinistryPortfolio
    urgency_level: int
    origin_council_id: str
    submission_sequence: int


@dataclass(frozen=True)
class CollegiateResolution:
    resolution_id: str
    council_id: str
    tier: CouncilTier
    agenda_item_id: str
    summary: str
    votes_in_favour: int
    votes_against: int
    total_council_members: int
    authenticated_by_secretary_id: str
    resolution_hash: str


class SecretaryGeneral:
    voting_weight: int = 1

    def __init__(self, profile: CitizenProfile, council_id: str, tier: CouncilTier) -> None:
        self.profile = profile
        self.council_id = council_id
        self.tier = tier

    def order_meeting_agenda(self, items: Sequence[AgendaItem]) -> list[AgendaItem]:
        return sorted(
            items,
            key=lambda entry: (-entry.urgency_level, entry.submission_sequence, entry.item_id),
        )

    def authenticate_resolution(
        self,
        resolution_id: str,
        agenda_item: AgendaItem,
        summary: str,
        ballots_by_member: Mapping[str, bool],
        valid_member_ids: frozenset[str],
    ) -> CollegiateResolution:
        if self.voting_weight != 1:
            raise AutocraticActForbiddenError(
                f"Equal suffrage violation: Secretary-General voting_weight must equal 1 (got {self.voting_weight})."
            )
        if not valid_member_ids:
            raise ValueError("Council membership cannot be empty.")
        if self.profile.citizen_id not in valid_member_ids:
            raise ValueError("Secretary-General does not belong to the target Council membership.")
        unrecognised_voters = set(ballots_by_member.keys()) - valid_member_ids
        if unrecognised_voters:
            raise ValueError(
                f"Ballots cast by non-members of Council: {sorted(unrecognised_voters)}"
            )

        votes_in_favour = sum(
            self.voting_weight if voter_id == self.profile.citizen_id else 1
            for voter_id, vote in ballots_by_member.items()
            if vote
        )
        votes_against = sum(
            self.voting_weight if voter_id == self.profile.citizen_id else 1
            for voter_id, vote in ballots_by_member.items()
            if not vote
        )
        majority_threshold = (len(valid_member_ids) // 2) + 1

        if votes_in_favour < majority_threshold:
            raise AutocraticActForbiddenError(
                f"Authentication blocked: resolution '{resolution_id}' obtained "
                f"{votes_in_favour}/{len(valid_member_ids)} favourable votes "
                f"(required majority: {majority_threshold}). The Secretary-General cannot override a minority."
            )

        digest_payload = (
            f"{resolution_id}|{self.council_id}|{self.tier}|{agenda_item.item_id}|"
            f"{votes_in_favour}:{votes_against}|{self.profile.citizen_id}|{summary}"
        )
        resolution_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        return CollegiateResolution(
            resolution_id=resolution_id,
            council_id=self.council_id,
            tier=self.tier,
            agenda_item_id=agenda_item.item_id,
            summary=summary,
            votes_in_favour=votes_in_favour,
            votes_against=votes_against,
            total_council_members=len(valid_member_ids),
            authenticated_by_secretary_id=self.profile.citizen_id,
            resolution_hash=resolution_hash,
        )

    def attempt_unilateral_decree(self, decree_text: str) -> None:
        raise AutocraticActForbiddenError(
            f"Constitutional violation: the Secretary-General holds zero unilateral decree power ('{decree_text}')."
        )

    def attempt_veto(self, resolution_id: str) -> None:
        raise AutocraticActForbiddenError(
            f"Constitutional violation: the Secretary-General holds zero veto power over '{resolution_id}'."
        )


@dataclass(frozen=True)
class GeneralOfficer:
    officer_id: str
    rank: str
    full_name: str
    operational_command: str


@dataclass(frozen=True)
class StrategicMilitaryOrder:
    order_id: str
    directive_description: str
    target_general_id: str
    civilian_minister_id: str
    secretary_general_id: str
    defence_chamber_approvals: tuple[str, ...]
    multisig_token: str


class CivilianMilitaryCommandGate:
    def __init__(
        self,
        civilian_minister: CitizenProfile,
        defence_chamber_civilians: Sequence[CitizenProfile],
        secretary_general: SecretaryGeneral,
        subordinate_generals: Sequence[GeneralOfficer],
    ) -> None:
        if not defence_chamber_civilians:
            raise ValueError("Defence Chamber requires at least one sorted civilian member.")
        if not subordinate_generals:
            raise ValueError("At least one subordinate general officer must be registered.")
        if civilian_minister.is_military_personnel:
            raise CivilianSupremacyViolationError(
                "The holder of the Ministry of Defence must be a sorted civilian citizen."
            )
        if civilian_minister.citizen_id == secretary_general.profile.citizen_id:
            raise CivilianSupremacyViolationError(
                "Multi-signature separation requires distinct citizens for Defence Minister and Secretary-General."
            )
        for chamber_member in defence_chamber_civilians:
            if chamber_member.is_military_personnel:
                raise CivilianSupremacyViolationError(
                    f"Defence Chamber member '{chamber_member.citizen_id}' cannot be military personnel."
                )
        if secretary_general.tier != CouncilTier.FEDERAL:
            raise ValueError("The Ministry of Defence is strictly bound to the Federal Council.")

        self.civilian_minister = civilian_minister
        self.defence_chamber = {member.citizen_id: member for member in defence_chamber_civilians}
        self.secretary_general = secretary_general
        self.generals = {officer.officer_id: officer for officer in subordinate_generals}

    def issue_strategic_order(
        self,
        order_id: str,
        directive_description: str,
        target_general_id: str,
        signed_by_minister_id: str,
        signed_by_secretary_id: str,
        chamber_approving_ids: Sequence[str],
    ) -> StrategicMilitaryOrder:
        if target_general_id not in self.generals:
            raise ValueError(
                f"General officer '{target_general_id}' is not registered under subordinate command."
            )
        if signed_by_minister_id != self.civilian_minister.citizen_id:
            raise MilitarySubordinationViolationError(
                "Strategic order rejected: missing signature from the sorted Civilian Defence Minister."
            )
        if signed_by_secretary_id != self.secretary_general.profile.citizen_id:
            raise MilitarySubordinationViolationError(
                "Strategic order rejected: missing minutes certification from the Federal Secretary-General."
            )

        valid_approvals = sorted(set(chamber_approving_ids) & set(self.defence_chamber.keys()))
        required_two_thirds_quorum = max(1, (2 * len(self.defence_chamber) + 2) // 3)
        if len(valid_approvals) < required_two_thirds_quorum:
            raise MilitarySubordinationViolationError(
                f"Insufficient civilian quorum in Defence Chamber: "
                f"{len(valid_approvals)}/{required_two_thirds_quorum}."
            )

        token_payload = (
            f"CIVIL_DEFENCE_MULTISIG|{order_id}|{target_general_id}|{signed_by_minister_id}|"
            f"{signed_by_secretary_id}|{','.join(valid_approvals)}|{directive_description}"
        )
        multisig_token = hashlib.sha256(token_payload.encode("utf-8")).hexdigest()
        return StrategicMilitaryOrder(
            order_id=order_id,
            directive_description=directive_description,
            target_general_id=target_general_id,
            civilian_minister_id=signed_by_minister_id,
            secretary_general_id=signed_by_secretary_id,
            defence_chamber_approvals=tuple(valid_approvals),
            multisig_token=multisig_token,
        )

    def attempt_autonomous_general_mobilisation(self, officer_id: str, description: str) -> None:
        general = self.generals.get(officer_id)
        officer_label = f"{general.rank} {general.full_name}" if general else officer_id
        raise MilitarySubordinationViolationError(
            f"Cybernetic Insubordination Lock: {officer_label} holds neither political authority nor "
            f"cryptographic clearance for autonomous mobilisation ('{description}'). "
            "High-ranking generals answer strictly to the sorted civilian minister."
        )


@dataclass(frozen=True)
class PopularJuryCase:
    case_id: str
    case_summary: str
    council_id: str


@dataclass(frozen=True)
class PopularJuryVerdict:
    case_id: str
    council_id: str
    tier: CouncilTier
    juror_count: int
    votes_upheld: int
    votes_acquitted: int
    is_liability_upheld: bool
    verdict_hash: str


@dataclass(frozen=True)
class PublicSecurityDispatch:
    protocol_id: str
    council_id: str
    tier: CouncilTier
    protocol_summary: str
    approving_security_members: int
    total_security_members: int
    justice_oversight_lead_id: str
    dispatch_hash: str


@dataclass
class DemarchicCouncil:
    council_id: str
    name: str
    tier: CouncilTier
    parent_council_id: str | None
    members: list[CitizenProfile]
    secretary_general: SecretaryGeneral
    portfolios: dict[MinistryPortfolio, list[CitizenProfile]]
    upward_demands: list[AgendaItem] = field(default_factory=list)
    binding_macro_directives: list[dict[str, object]] = field(default_factory=list)
    jury_verdicts: list[PopularJuryVerdict] = field(default_factory=list)
    security_dispatches: list[PublicSecurityDispatch] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.member_ids) != len(self.members):
            raise ValueError("Council membership contains duplicate citizen identifiers.")
        if (
            self.secretary_general.council_id != self.council_id
            or self.secretary_general.tier != self.tier
        ):
            raise ValueError("Secretary-General bound to mismatched Council identifier or tier.")
        if self.secretary_general.profile.citizen_id not in self.member_ids:
            raise ValueError(
                "Secretary-General must belong to the sorted membership of the Council."
            )
        for chamber_members in self.portfolios.values():
            for chamber_member in chamber_members:
                if chamber_member.citizen_id not in self.member_ids:
                    raise ValueError(
                        f"Portfolio member '{chamber_member.citizen_id}' does not belong to Council '{self.council_id}'."
                    )

    @property
    def member_ids(self) -> frozenset[str]:
        return frozenset(member.citizen_id for member in self.members)

    def active_popular_jury_bench(self, case_id: str | None = None) -> list[CitizenProfile]:
        justice_chamber = self.portfolios.get(MinistryPortfolio.JUSTICE, [])
        if len(justice_chamber) < 3:
            raise ValueError(
                f"Popular Jury requires at least 3 sorted citizens in the Justice portfolio (found {len(justice_chamber)})."
            )
        if len(justice_chamber) % 2 == 0:
            rotation_token = case_id.strip() if case_id and case_id.strip() else "DEFAULT"
            seed_material = (
                f"JURY_BENCH|{self.council_id}|{rotation_token}|"
                f"{','.join(member.citizen_id for member in justice_chamber)}"
            ).encode("utf-8")
            drbg = CounterModeHmacDrbg(hashlib.sha256(seed_material).hexdigest())
            excluded_index = drbg.randbelow_unbiased(len(justice_chamber))
            return [
                member for index, member in enumerate(justice_chamber) if index != excluded_index
            ]
        return list(justice_chamber)

    def adjudicate_by_popular_jury(
        self,
        case: PopularJuryCase,
        ballots_by_juror: Mapping[str, bool],
    ) -> PopularJuryVerdict:
        if not case.case_id.strip() or not case.case_summary.strip():
            raise ValueError("Popular Jury case identifier and summary cannot be empty.")
        if case.council_id != self.council_id:
            raise ValueError("Case jurisdiction does not match target Council.")

        case_bench = self.active_popular_jury_bench(case.case_id)
        default_bench = self.active_popular_jury_bench()
        submitted_juror_ids = frozenset(ballots_by_juror.keys())
        case_juror_ids = frozenset(member.citizen_id for member in case_bench)
        default_juror_ids = frozenset(member.citizen_id for member in default_bench)
        if submitted_juror_ids == case_juror_ids:
            jury_bench = case_bench
        elif submitted_juror_ids == default_juror_ids:
            jury_bench = default_bench
        else:
            raise ValueError(
                "All active Popular Jury members must cast individual secret ballots without outsiders."
            )

        votes_upheld = sum(1 for vote in ballots_by_juror.values() if vote)
        votes_acquitted = sum(1 for vote in ballots_by_juror.values() if not vote)
        is_liability_upheld = votes_upheld > votes_acquitted
        digest_payload = (
            f"POPULAR_JURY_VERDICT|{case.case_id}|{self.council_id}|{self.tier}|"
            f"{votes_upheld}:{votes_acquitted}|{case.case_summary}"
        )
        verdict_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        verdict = PopularJuryVerdict(
            case_id=case.case_id,
            council_id=self.council_id,
            tier=self.tier,
            juror_count=len(jury_bench),
            votes_upheld=votes_upheld,
            votes_acquitted=votes_acquitted,
            is_liability_upheld=is_liability_upheld,
            verdict_hash=verdict_hash,
        )
        self.jury_verdicts.append(verdict)
        return verdict

    def attempt_monocratic_judicial_sentence(self, actor_id: str, case_id: str) -> None:
        raise AutocraticActForbiddenError(
            f"Monocratic sentence blocked ('{actor_id}' on '{case_id}'): adjudication belongs exclusively "
            "to the collegiate Popular Jury sorted into the Justice portfolio."
        )

    def dispatch_public_security_protocol(
        self,
        protocol_id: str,
        protocol_summary: str,
        ballots_by_member: Mapping[str, bool],
        justice_oversight_lead_id: str,
    ) -> PublicSecurityDispatch:
        if not protocol_id.strip() or not protocol_summary.strip():
            raise ValueError("Public Security protocol identifier and summary cannot be empty.")
        security_chamber = self.portfolios.get(MinistryPortfolio.PUBLIC_SECURITY, [])
        justice_chamber = self.portfolios.get(MinistryPortfolio.JUSTICE, [])
        if not security_chamber or not justice_chamber:
            raise ValueError("Council requires constituted Public Security and Justice chambers.")

        justice_member_ids = {member.citizen_id for member in justice_chamber}
        if justice_oversight_lead_id not in justice_member_ids:
            raise AutocraticActForbiddenError(
                "Public Security dispatch rejected: missing legality countersignature from the Justice & Popular Jury chamber."
            )

        valid_security_ids = frozenset(member.citizen_id for member in security_chamber)
        if not set(ballots_by_member.keys()).issubset(valid_security_ids):
            raise ValueError("Ballots in Public Security chamber contain non-member identifiers.")

        approving_count = sum(1 for vote in ballots_by_member.values() if vote)
        majority_threshold = (len(valid_security_ids) // 2) + 1
        if approving_count < majority_threshold:
            raise AutocraticActForbiddenError(
                f"Public Security protocol '{protocol_id}' lacked collegiate majority "
                f"({approving_count}/{len(valid_security_ids)})."
            )

        digest_payload = (
            f"PUBLIC_SECURITY_PROTOCOL|{protocol_id}|{self.council_id}|{self.tier}|"
            f"{approving_count}/{len(valid_security_ids)}|{justice_oversight_lead_id}|{protocol_summary}"
        )
        dispatch_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
        dispatch = PublicSecurityDispatch(
            protocol_id=protocol_id,
            council_id=self.council_id,
            tier=self.tier,
            protocol_summary=protocol_summary,
            approving_security_members=approving_count,
            total_security_members=len(valid_security_ids),
            justice_oversight_lead_id=justice_oversight_lead_id,
            dispatch_hash=dispatch_hash,
        )
        self.security_dispatches.append(dispatch)
        return dispatch

    def attempt_warrantless_security_measure(self, measure_description: str) -> None:
        raise AutocraticActForbiddenError(
            f"Constitutional safeguard triggered: warrantless security action ('{measure_description}') is forbidden "
            "without Popular Jury and Justice chamber oversight."
        )


class EscalatedCouncilMesh:
    EXPECTED_PARENT_TIER: Mapping[CouncilTier, CouncilTier | None] = {
        CouncilTier.SECTORAL: CouncilTier.MUNICIPAL,
        CouncilTier.MUNICIPAL: CouncilTier.STATE,
        CouncilTier.STATE: CouncilTier.FEDERAL,
        CouncilTier.FEDERAL: None,
    }

    def __init__(self) -> None:
        self._councils_by_id: dict[str, DemarchicCouncil] = {}

    def register_council(self, council: DemarchicCouncil) -> None:
        if council.council_id in self._councils_by_id:
            raise ValueError(
                f"Council '{council.council_id}' is already registered in the federated mesh."
            )
        expected_parent_tier = self.EXPECTED_PARENT_TIER[council.tier]
        if expected_parent_tier is None and council.parent_council_id is not None:
            raise ValueError(
                "The Federal Council is the coordination apex and cannot have a parent council."
            )
        if expected_parent_tier is not None:
            if (
                council.parent_council_id is None
                or council.parent_council_id not in self._councils_by_id
            ):
                raise ValueError(
                    f"Council {council.tier} '{council.council_id}' requires registered parent tier "
                    f"'{expected_parent_tier}'."
                )
            parent_council = self._councils_by_id[council.parent_council_id]
            if parent_council.tier != expected_parent_tier:
                raise ValueError(
                    f"Invalid hierarchy: {council.tier} cannot attach directly to {parent_council.tier}."
                )
        if council.tier != CouncilTier.FEDERAL and MinistryPortfolio.DEFENCE in council.portfolios:
            raise ValueError("The Ministry of Defence is exclusive to the Federal Council.")
        self._councils_by_id[council.council_id] = council

    def get_council(self, council_id: str) -> DemarchicCouncil:
        return self._councils_by_id[council_id]

    def list_councils(self) -> list[DemarchicCouncil]:
        tier_display_order = {
            CouncilTier.FEDERAL: 0,
            CouncilTier.STATE: 1,
            CouncilTier.MUNICIPAL: 2,
            CouncilTier.SECTORAL: 3,
        }
        return sorted(
            self._councils_by_id.values(),
            key=lambda council: (tier_display_order[council.tier], council.council_id),
        )

    def escalate_citizen_demand(self, sectoral_council_id: str, item: AgendaItem) -> list[str]:
        origin_council = self._councils_by_id[sectoral_council_id]
        if origin_council.tier != CouncilTier.SECTORAL:
            raise ValueError(
                "Primary citizen communication originates exclusively at a Sectoral Council."
            )

        escalation_route: list[str] = []
        cursor: DemarchicCouncil | None = origin_council
        while cursor is not None:
            cursor.upward_demands.append(item)
            escalation_route.append(cursor.council_id)
            cursor = (
                self._councils_by_id[cursor.parent_council_id] if cursor.parent_council_id else None
            )
        return escalation_route

    def broadcast_compulsory_macro_directive(self, directive_payload: dict[str, object]) -> int:
        propagated_count = 0
        for council in self._councils_by_id.values():
            council.binding_macro_directives.append(dict(directive_payload))
            propagated_count += 1
        return propagated_count


@dataclass(frozen=True)
class CouncilProportionalityMetric:
    council_id: str
    tier: CouncilTier
    assigned_seats: int
    sectoral_base_aggregate: int
    proportionality_ratio: float
    is_mathematically_proportional: bool
    rationale: str


class FederatedSeatProportionality:
    MIN_COUNCIL_SEATS: int = 10
    MAX_COUNCIL_SEATS: int = 40
    DEFAULT_MUNICIPAL_RATIO: float = 1.0

    @classmethod
    def calculate_municipal_seats(
        cls,
        sectoral_seats: Sequence[int],
        ratio: float = DEFAULT_MUNICIPAL_RATIO,
    ) -> int:
        if not sectoral_seats:
            raise ValueError(
                "Sectoral seat list cannot be empty to compute municipal proportionality."
            )
        for seats in sectoral_seats:
            if seats < cls.MIN_COUNCIL_SEATS:
                raise ValueError(
                    f"Sectoral council size ({seats}) below required minimum ({cls.MIN_COUNCIL_SEATS})."
                )
        raw_target = int(round(sum(sectoral_seats) * ratio))
        if raw_target < cls.MIN_COUNCIL_SEATS:
            raise ValueError(
                f"Computed municipal seats ({raw_target}) below representational threshold ({cls.MIN_COUNCIL_SEATS})."
            )
        if raw_target > cls.MAX_COUNCIL_SEATS:
            raise ValueError(
                f"Computed municipal seats ({raw_target}) exceeds deliberative ceiling ({cls.MAX_COUNCIL_SEATS})."
            )
        return raw_target

    @classmethod
    def validate_municipal_proportionality(
        cls,
        municipal_seats: int,
        sectoral_seats: Sequence[int],
        expected_ratio: float = DEFAULT_MUNICIPAL_RATIO,
    ) -> bool:
        calculated = cls.calculate_municipal_seats(sectoral_seats, expected_ratio)
        return municipal_seats == calculated

    @classmethod
    def evaluate_council_metric(
        cls,
        council_id: str,
        tier: CouncilTier,
        assigned_seats: int,
        child_sectoral_seats: Sequence[int],
    ) -> CouncilProportionalityMetric:
        aggregate = sum(child_sectoral_seats)
        if tier == CouncilTier.MUNICIPAL:
            ratio = float(assigned_seats / aggregate) if aggregate > 0 else 0.0
            is_valid = cls.validate_municipal_proportionality(assigned_seats, child_sectoral_seats)
            rationale = (
                f"Municipal seats ({assigned_seats}) strictly proportional to aggregate sectoral members "
                f"({aggregate}) under ratio {ratio:.2f}."
            )
        elif tier == CouncilTier.SECTORAL:
            ratio = 1.0
            is_valid = cls.MIN_COUNCIL_SEATS <= assigned_seats <= cls.MAX_COUNCIL_SEATS
            rationale = f"Base neighbourhood council operates with {assigned_seats} seats satisfying primary citizen parity."
        elif tier == CouncilTier.STATE:
            ratio = (
                float(assigned_seats / cls.calculate_municipal_seats(child_sectoral_seats))
                if child_sectoral_seats
                else 0.8
            )
            is_valid = cls.MIN_COUNCIL_SEATS <= assigned_seats <= cls.MAX_COUNCIL_SEATS
            rationale = f"State coordination tier sized at {assigned_seats} seats via regional deliberative condensation."
        else:
            ratio = 1.0
            is_valid = cls.MIN_COUNCIL_SEATS <= assigned_seats <= cls.MAX_COUNCIL_SEATS
            rationale = f"Federal coordination tier sized at {assigned_seats} seats with civilian Defence command parity."

        return CouncilProportionalityMetric(
            council_id=council_id,
            tier=tier,
            assigned_seats=assigned_seats,
            sectoral_base_aggregate=aggregate,
            proportionality_ratio=ratio,
            is_mathematically_proportional=is_valid,
            rationale=rationale,
        )
