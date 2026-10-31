from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
import hashlib
import hmac
from typing import Mapping, Sequence


class ElectoralOperationForbiddenError(RuntimeError):
    pass


class EntropyVerificationError(ValueError):
    pass


class CivilianSupremacyViolationError(RuntimeError):
    pass


class MinistryPortfolio(StrEnum):
    ECONOMY = "ECONOMY"
    EDUCATION = "EDUCATION"
    HEALTH = "HEALTH"
    INFRASTRUCTURE_ECOLOGY = "INFRASTRUCTURE_ECOLOGY"
    LABOUR = "LABOUR"
    JUSTICE = "JUSTICE"
    PUBLIC_SECURITY = "PUBLIC_SECURITY"
    DEFENCE = "DEFENCE"


PORTFOLIO_PROPORTIONAL_WEIGHTS: Mapping[MinistryPortfolio, int] = {
    MinistryPortfolio.ECONOMY: 3,
    MinistryPortfolio.EDUCATION: 3,
    MinistryPortfolio.HEALTH: 3,
    MinistryPortfolio.INFRASTRUCTURE_ECOLOGY: 3,
    MinistryPortfolio.LABOUR: 3,
    MinistryPortfolio.JUSTICE: 5,
    MinistryPortfolio.PUBLIC_SECURITY: 3,
    MinistryPortfolio.DEFENCE: 3,
}


@dataclass(frozen=True)
class CitizenProfile:
    citizen_id: str
    full_name: str
    sector_id: str
    municipality_id: str
    state_id: str
    stratum_key: str
    is_military_personnel: bool
    prior_monthly_income: Decimal
    employer_id: str | None = None
    job_role: str = "worker.role.operational_specialist"


@dataclass(frozen=True)
class SortitionAuditProof:
    scope_id: str
    cycle_number: int
    eligible_merkle_root: str
    commitments: tuple[tuple[str, str], ...]
    revealed_seeds: tuple[tuple[str, str, str], ...]
    master_seed_hex: str
    stratum_quotas: tuple[tuple[str, int], ...]
    selected_citizen_ids: tuple[str, ...]


def compute_merkle_root(citizen_identifiers: Sequence[str]) -> str:
    if not citizen_identifiers:
        return hashlib.sha256(b"EMPTY_ELIGIBLE_POOL").hexdigest()

    sorted_unique_ids = sorted(set(citizen_identifiers))
    current_layer = [
        hashlib.sha256(identifier.encode("utf-8")).digest() for identifier in sorted_unique_ids
    ]
    while len(current_layer) > 1:
        if len(current_layer) % 2 == 1:
            current_layer.append(current_layer[-1])
        parent_layer: list[bytes] = []
        for pair_index in range(0, len(current_layer), 2):
            combined_digest = hashlib.sha256(
                current_layer[pair_index] + current_layer[pair_index + 1]
            ).digest()
            parent_layer.append(combined_digest)
        current_layer = parent_layer
    return current_layer[0].hex()


class CommitRevealEntropyBeacon:
    def __init__(self, minimum_sources: int = 3) -> None:
        if minimum_sources < 2:
            raise ValueError("At least 2 independent entropy sources are required.")
        self.minimum_sources = minimum_sources
        self._commitments_by_source: dict[str, str] = {}
        self._reveals_by_source: dict[str, tuple[str, str]] = {}
        self._is_locked: bool = False

    @staticmethod
    def create_commitment(secret_seed: str, nonce: str) -> str:
        encoded_payload = f"{secret_seed}||{nonce}".encode("utf-8")
        return hashlib.sha256(encoded_payload).hexdigest()

    def publish_commitment(self, source_id: str, commitment_hex: str) -> None:
        if self._is_locked:
            raise EntropyVerificationError("Commitment phase is already locked.")
        if not source_id.strip():
            raise EntropyVerificationError("Entropy source identifier cannot be empty.")
        if len(commitment_hex) != 64:
            raise EntropyVerificationError(
                "Commitment digest must be a 64-character SHA-256 hex string."
            )
        try:
            bytes.fromhex(commitment_hex)
        except ValueError as exc:
            raise EntropyVerificationError(
                "Commitment digest contains non-hexadecimal characters."
            ) from exc
        if source_id in self._commitments_by_source:
            raise EntropyVerificationError(
                f"Entropy source '{source_id}' has already published a commitment."
            )
        self._commitments_by_source[source_id] = commitment_hex.lower()

    def lock_commitments(self) -> None:
        if len(self._commitments_by_source) < self.minimum_sources:
            raise EntropyVerificationError(
                f"Insufficient entropy sources: registered {len(self._commitments_by_source)}, "
                f"minimum {self.minimum_sources}."
            )
        self._is_locked = True

    def reveal_seed(self, source_id: str, secret_seed: str, nonce: str) -> None:
        if not self._is_locked:
            raise EntropyVerificationError("Commitments must be locked prior to seed revelation.")
        if source_id not in self._commitments_by_source:
            raise EntropyVerificationError(f"Unknown entropy source: '{source_id}'.")
        expected_commitment = self._commitments_by_source[source_id]
        actual_commitment = self.create_commitment(secret_seed, nonce)
        if not hmac.compare_digest(expected_commitment, actual_commitment):
            raise EntropyVerificationError(
                f"Revelation mismatch detected for source '{source_id}': digest diverges from commitment."
            )
        self._reveals_by_source[source_id] = (secret_seed, nonce)

    def derive_master_seed(
        self, scope_id: str, cycle_number: int, eligible_merkle_root: str
    ) -> tuple[str, tuple[tuple[str, str], ...], tuple[tuple[str, str, str], ...]]:
        if not self._is_locked:
            raise EntropyVerificationError("Commitments have not been locked yet.")
        if len(self._reveals_by_source) != len(self._commitments_by_source):
            missing_sources = sorted(
                set(self._commitments_by_source) - set(self._reveals_by_source)
            )
            raise EntropyVerificationError(f"Pending revelations from sources: {missing_sources}")

        ordered_commitments = tuple(sorted(self._commitments_by_source.items()))
        ordered_reveals = tuple(
            (
                source_id,
                self._reveals_by_source[source_id][0],
                self._reveals_by_source[source_id][1],
            )
            for source_id, _ in ordered_commitments
        )
        seed_hasher = hashlib.sha256()
        seed_hasher.update(
            f"CIBERSOC_SORTITION_V2|{scope_id}|{cycle_number}|{eligible_merkle_root}".encode(
                "utf-8"
            )
        )
        for source_id, secret_seed, nonce in ordered_reveals:
            seed_hasher.update(f"|{source_id}:{secret_seed}:{nonce}".encode("utf-8"))
        return seed_hasher.hexdigest(), ordered_commitments, ordered_reveals


class CounterModeHmacDrbg:
    def __init__(self, seed_hex: str) -> None:
        if not seed_hex.strip():
            raise ValueError("Hexadecimal master seed cannot be empty.")
        self._hmac_key = bytes.fromhex(seed_hex)
        self._block_counter = 0

    def _next_uint64(self) -> int:
        counter_bytes = self._block_counter.to_bytes(8, byteorder="big")
        self._block_counter += 1
        digest = hmac.new(self._hmac_key, counter_bytes, hashlib.sha256).digest()
        return int.from_bytes(digest[:8], byteorder="big")

    def randbelow_unbiased(self, upper_bound: int) -> int:
        if upper_bound <= 0:
            raise ValueError("Upper bound must be strictly positive.")
        if upper_bound == 1:
            return 0
        uint64_space = 1 << 64
        rejection_threshold = uint64_space - (uint64_space % upper_bound)
        while True:
            candidate_value = self._next_uint64()
            if candidate_value < rejection_threshold:
                return candidate_value % upper_bound

    def sample_without_replacement(self, identifiers: Sequence[str], sample_size: int) -> list[str]:
        if sample_size < 0 or sample_size > len(identifiers):
            raise ValueError(
                f"Invalid sample_size={sample_size} for population size={len(identifiers)}."
            )
        pool = list(sorted(identifiers))
        pool_length = len(pool)
        for index in range(sample_size):
            swap_index = index + self.randbelow_unbiased(pool_length - index)
            pool[index], pool[swap_index] = pool[swap_index], pool[index]
        return pool[:sample_size]


def allocate_proportional_hamilton_quotas(
    strata_population_sizes: Mapping[str, int],
    total_seats: int,
    tie_breaker_priority: Sequence[str] | None = None,
) -> dict[str, int]:
    if any(population_count < 0 for population_count in strata_population_sizes.values()):
        raise ValueError("Stratum population size cannot be negative.")

    non_empty_strata = {
        stratum: count for stratum, count in strata_population_sizes.items() if count > 0
    }
    total_eligible_population = sum(non_empty_strata.values())
    if total_seats <= 0 or total_seats > total_eligible_population:
        raise ValueError(
            f"Requested seats ({total_seats}) incompatible with eligible population ({total_eligible_population})."
        )

    allocated_quotas: dict[str, int] = {
        stratum: 0 for stratum in sorted(strata_population_sizes.keys())
    }
    ranked_remainders: list[tuple[int, str]] = []
    seats_allocated_by_floor = 0

    for stratum in sorted(non_empty_strata.keys()):
        population_count = non_empty_strata[stratum]
        scaled_numerator = population_count * total_seats
        floor_quota = scaled_numerator // total_eligible_population
        remainder = scaled_numerator % total_eligible_population
        allocated_quotas[stratum] = floor_quota
        seats_allocated_by_floor += floor_quota
        ranked_remainders.append((remainder, stratum))

    unassigned_seats = total_seats - seats_allocated_by_floor
    if tie_breaker_priority is not None:
        priority_map = {name: idx for idx, name in enumerate(tie_breaker_priority)}
        ranked_remainders.sort(
            key=lambda entry: (-entry[0], priority_map.get(entry[1], 999999), entry[1])
        )
    else:
        ranked_remainders.sort(key=lambda entry: (-entry[0], entry[1]))
    for rank_index in range(unassigned_seats):
        _, winning_stratum = ranked_remainders[rank_index]
        allocated_quotas[winning_stratum] += 1

    return allocated_quotas


class StratifiedSortitionEngine:
    def __init__(self, cooldown_cycles: int = 1) -> None:
        if cooldown_cycles < 1:
            raise ValueError(
                "Post-mandate quarantine must span at least 1 subsequent cycle to prevent power perpetuation."
            )
        self.cooldown_cycles = cooldown_cycles
        self._quarantined_until_cycle: dict[str, int] = {}
        self._serving_councillor_ids: set[str] = set()

    @property
    def active_councillor_ids(self) -> frozenset[str]:
        return frozenset(self._serving_councillor_ids)

    @property
    def quarantined_registry(self) -> dict[str, int]:
        return dict(self._quarantined_until_cycle)

    @staticmethod
    def reject_electoral_mechanism(operation_name: str = "election") -> None:
        raise ElectoralOperationForbiddenError(
            f"Operation '{operation_name}' violates the Demarchic Constitution of CIBERSOC: "
            "direct/indirect elections, political parties and career politicians are permanently abolished."
        )

    def register_mandate_start(self, citizen_ids: Sequence[str]) -> None:
        for citizen_id in citizen_ids:
            self._serving_councillor_ids.add(citizen_id)

    def register_mandate_completion(self, citizen_ids: Sequence[str], completed_cycle: int) -> None:
        for citizen_id in citizen_ids:
            self._serving_councillor_ids.discard(citizen_id)
            locked_until = completed_cycle + self.cooldown_cycles
            prior_lock = self._quarantined_until_cycle.get(citizen_id, -1)
            self._quarantined_until_cycle[citizen_id] = max(prior_lock, locked_until)

    def is_eligible(self, citizen_id: str, current_cycle: int) -> bool:
        if citizen_id in self._serving_councillor_ids:
            return False
        blocked_until = self._quarantined_until_cycle.get(citizen_id)
        if blocked_until is not None and current_cycle <= blocked_until:
            return False
        return True

    def filter_eligible_citizens(
        self, population: Sequence[CitizenProfile], current_cycle: int
    ) -> list[CitizenProfile]:
        observed_citizen_ids: set[str] = set()
        for citizen in population:
            if citizen.citizen_id in observed_citizen_ids:
                raise ValueError(
                    f"Duplicate citizen identifier in population registry: '{citizen.citizen_id}'."
                )
            observed_citizen_ids.add(citizen.citizen_id)
        return [
            citizen for citizen in population if self.is_eligible(citizen.citizen_id, current_cycle)
        ]

    @staticmethod
    def filter_by_territorial_jurisdiction(
        population: Sequence[CitizenProfile],
        state_id: str | None = None,
        municipality_id: str | None = None,
        sector_id: str | None = None,
    ) -> list[CitizenProfile]:
        filtered: list[CitizenProfile] = []
        for citizen in population:
            if state_id is not None and citizen.state_id != state_id:
                continue
            if municipality_id is not None and citizen.municipality_id != municipality_id:
                continue
            if sector_id is not None and citizen.sector_id != sector_id:
                continue
            filtered.append(citizen)
        return filtered

    def draw_council(
        self,
        scope_id: str,
        cycle_number: int,
        population: Sequence[CitizenProfile],
        total_seats: int,
        beacon: CommitRevealEntropyBeacon,
    ) -> tuple[list[CitizenProfile], SortitionAuditProof]:
        if total_seats <= 0:
            raise ValueError("Council seat count must be strictly positive.")

        eligible_pool = self.filter_eligible_citizens(population, cycle_number)
        if len(eligible_pool) < total_seats:
            raise ValueError(
                f"Insufficient eligible urn ({len(eligible_pool)}) to fill {total_seats} seats in '{scope_id}'."
            )

        merkle_root = compute_merkle_root([citizen.citizen_id for citizen in eligible_pool])
        master_seed_hex, commitments, revealed_seeds = beacon.derive_master_seed(
            scope_id, cycle_number, merkle_root
        )
        drbg = CounterModeHmacDrbg(master_seed_hex)

        citizens_by_stratum: dict[str, list[str]] = {}
        profiles_by_id: dict[str, CitizenProfile] = {}
        for citizen in eligible_pool:
            citizens_by_stratum.setdefault(citizen.stratum_key, []).append(citizen.citizen_id)
            profiles_by_id[citizen.citizen_id] = citizen

        quotas_by_stratum = allocate_proportional_hamilton_quotas(
            {stratum: len(ids) for stratum, ids in citizens_by_stratum.items()},
            total_seats,
        )

        selected_ids: list[str] = []
        for stratum in sorted(quotas_by_stratum.keys()):
            seat_quota = quotas_by_stratum[stratum]
            if seat_quota > 0:
                drawn_stratum_ids = drbg.sample_without_replacement(
                    citizens_by_stratum[stratum], seat_quota
                )
                selected_ids.extend(drawn_stratum_ids)

        self.register_mandate_start(selected_ids)
        audit_proof = SortitionAuditProof(
            scope_id=scope_id,
            cycle_number=cycle_number,
            eligible_merkle_root=merkle_root,
            commitments=commitments,
            revealed_seeds=revealed_seeds,
            master_seed_hex=master_seed_hex,
            stratum_quotas=tuple(sorted(quotas_by_stratum.items())),
            selected_citizen_ids=tuple(selected_ids),
        )
        return [profiles_by_id[citizen_id] for citizen_id in selected_ids], audit_proof

    @staticmethod
    def verify_audit_proof(
        eligible_citizen_ids: Sequence[str],
        proof: SortitionAuditProof,
        eligible_strata_by_id: Mapping[str, str],
    ) -> bool:
        if len(set(eligible_citizen_ids)) != len(eligible_citizen_ids):
            return False
        if not proof.selected_citizen_ids or len(proof.selected_citizen_ids) > len(
            eligible_citizen_ids
        ):
            return False
        if len(proof.commitments) < 2:
            return False
        if compute_merkle_root(eligible_citizen_ids) != proof.eligible_merkle_root:
            return False

        sorted_commit_sources = [source_id for source_id, _ in sorted(proof.commitments)]
        revealed_sources = [source_id for source_id, _, _ in proof.revealed_seeds]
        if sorted_commit_sources != revealed_sources:
            return False

        commitments_by_source = dict(proof.commitments)
        seed_hasher = hashlib.sha256()
        seed_hasher.update(
            f"CIBERSOC_SORTITION_V2|{proof.scope_id}|{proof.cycle_number}|{proof.eligible_merkle_root}".encode(
                "utf-8"
            )
        )
        for source_id, secret_seed, nonce in proof.revealed_seeds:
            recomputed_commitment = CommitRevealEntropyBeacon.create_commitment(secret_seed, nonce)
            if not hmac.compare_digest(commitments_by_source[source_id], recomputed_commitment):
                return False
            seed_hasher.update(f"|{source_id}:{secret_seed}:{nonce}".encode("utf-8"))

        if seed_hasher.hexdigest() != proof.master_seed_hex:
            return False

        citizens_by_stratum: dict[str, list[str]] = {}
        for citizen_id in eligible_citizen_ids:
            if citizen_id not in eligible_strata_by_id:
                return False
            citizens_by_stratum.setdefault(eligible_strata_by_id[citizen_id], []).append(citizen_id)

        expected_quotas = allocate_proportional_hamilton_quotas(
            {stratum: len(ids) for stratum, ids in citizens_by_stratum.items()},
            len(proof.selected_citizen_ids),
        )
        if tuple(sorted(expected_quotas.items())) != proof.stratum_quotas:
            return False

        drbg = CounterModeHmacDrbg(proof.master_seed_hex)
        reconstructed_selection: list[str] = []
        for stratum, seat_quota in proof.stratum_quotas:
            if seat_quota > 0:
                reconstructed_selection.extend(
                    drbg.sample_without_replacement(citizens_by_stratum[stratum], seat_quota)
                )

        return tuple(reconstructed_selection) == proof.selected_citizen_ids

    @staticmethod
    def assign_internal_roles(
        councillors: Sequence[CitizenProfile],
        include_defence_ministry: bool,
        master_seed_hex: str,
    ) -> tuple[CitizenProfile, dict[MinistryPortfolio, list[CitizenProfile]]]:
        profiles_by_id = {councillor.citizen_id: councillor for councillor in councillors}
        if len(profiles_by_id) != len(councillors):
            raise ValueError("Councillor sequence contains duplicate citizen identifiers.")

        active_portfolios = [
            MinistryPortfolio.ECONOMY,
            MinistryPortfolio.EDUCATION,
            MinistryPortfolio.HEALTH,
            MinistryPortfolio.INFRASTRUCTURE_ECOLOGY,
            MinistryPortfolio.LABOUR,
            MinistryPortfolio.JUSTICE,
            MinistryPortfolio.PUBLIC_SECURITY,
        ]
        if include_defence_ministry:
            active_portfolios.append(MinistryPortfolio.DEFENCE)

        minimum_required_members = 1 + len(active_portfolios)
        if len(councillors) < minimum_required_members:
            raise ValueError(
                f"Council requires at least {minimum_required_members} members for Secretary-General and ministries."
            )

        role_seed_hex = hashlib.sha256(
            f"INTERNAL_ROLES|{master_seed_hex}".encode("utf-8")
        ).hexdigest()
        drbg = CounterModeHmacDrbg(role_seed_hex)
        shuffled_ids = drbg.sample_without_replacement(
            list(profiles_by_id.keys()), len(councillors)
        )
        shuffled_profiles = [profiles_by_id[citizen_id] for citizen_id in shuffled_ids]

        chamber_seat_pool = len(councillors) - 1
        active_weights = {
            portfolio.value: PORTFOLIO_PROPORTIONAL_WEIGHTS[portfolio]
            for portfolio in active_portfolios
        }
        total_weight_units = sum(active_weights.values())
        if chamber_seat_pool >= total_weight_units:
            scaled_weights = {
                key: weight * chamber_seat_pool for key, weight in active_weights.items()
            }
            raw_quotas = allocate_proportional_hamilton_quotas(scaled_weights, chamber_seat_pool)
            quotas_by_portfolio = {
                MinistryPortfolio(key): quota for key, quota in raw_quotas.items()
            }
        else:
            quotas_by_portfolio = {portfolio: 1 for portfolio in active_portfolios}
            extra_seats = chamber_seat_pool - len(active_portfolios)
            if extra_seats > 0:
                extra_quotas = allocate_proportional_hamilton_quotas(active_weights, extra_seats)
                for key, bonus in extra_quotas.items():
                    quotas_by_portfolio[MinistryPortfolio(key)] += bonus

        assigned_chambers: dict[MinistryPortfolio, list[CitizenProfile]] = {
            portfolio: [] for portfolio in active_portfolios
        }
        non_defence_portfolios = [
            portfolio for portfolio in active_portfolios if portfolio != MinistryPortfolio.DEFENCE
        ]

        if include_defence_ministry:
            eligible_civilians = [
                member for member in shuffled_profiles if not member.is_military_personnel
            ]
            if not eligible_civilians:
                raise CivilianSupremacyViolationError(
                    "Cannot constitute Ministry of Defence: no civilian councillor available in sample."
                )
            desired_defence_seats = quotas_by_portfolio[MinistryPortfolio.DEFENCE]
            actual_defence_seats = min(desired_defence_seats, len(eligible_civilians))
            defence_members = eligible_civilians[:actual_defence_seats]
            assigned_chambers[MinistryPortfolio.DEFENCE].extend(defence_members)
            selected_defence_ids = {member.citizen_id for member in defence_members}
            shuffled_profiles = [
                member
                for member in shuffled_profiles
                if member.citizen_id not in selected_defence_ids
            ]
            defence_shortfall = desired_defence_seats - actual_defence_seats
            if defence_shortfall > 0:
                non_defence_weights = {
                    portfolio.value: PORTFOLIO_PROPORTIONAL_WEIGHTS[portfolio]
                    for portfolio in non_defence_portfolios
                }
                redistributed = allocate_proportional_hamilton_quotas(
                    {
                        key: weight * defence_shortfall
                        for key, weight in non_defence_weights.items()
                    },
                    defence_shortfall,
                )
                for key, bonus in redistributed.items():
                    quotas_by_portfolio[MinistryPortfolio(key)] += bonus

        secretary_general_profile = shuffled_profiles[0]
        remaining_councillors = shuffled_profiles[1:]

        cursor = 0
        for portfolio in non_defence_portfolios:
            seat_count = quotas_by_portfolio[portfolio]
            assigned_chambers[portfolio].extend(remaining_councillors[cursor : cursor + seat_count])
            cursor += seat_count

        return secretary_general_profile, assigned_chambers
