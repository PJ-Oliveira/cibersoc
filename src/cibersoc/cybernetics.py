from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import re
from typing import Mapping, Sequence


class InvalidPlebisciteTopicError(RuntimeError):
    pass


class InfeasibleMacroPlanError(ValueError):
    pass


class CompulsoryDirectiveOverrideError(RuntimeError):
    pass


_ELECTORAL_PERSON_KEYWORDS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bcandidates?\b", re.IGNORECASE),
    re.compile(r"\bcandidat(?:o|a|os|as|ura|uras)\b", re.IGNORECASE),
    re.compile(r"\bpolitical\s+part(?:y|ies)\b", re.IGNORECASE),
    re.compile(r"\bpartidos?\b", re.IGNORECASE),
    re.compile(r"\bpartid[áa]ri[oa]s?\b", re.IGNORECASE),
    re.compile(r"\bpresident(?:s|ial|ship)?\b", re.IGNORECASE),
    re.compile(r"\bpresident[ea]s?\b", re.IGNORECASE),
    re.compile(r"\bpresidencia(?:l|is|les)?\b", re.IGNORECASE),
    re.compile(r"\bsenators?\b", re.IGNORECASE),
    re.compile(r"\bsenador(?:a|es|as)?\b", re.IGNORECASE),
    re.compile(r"\bdeputad[oa]s?\b", re.IGNORECASE),
    re.compile(r"\bdiputad[oa]s?\b", re.IGNORECASE),
    re.compile(r"\bprime\s+ministers?\b", re.IGNORECASE),
    re.compile(r"\bprimeiro[\s\-]*ministro\b", re.IGNORECASE),
    re.compile(r"\bprimer\s+ministro\b", re.IGNORECASE),
    re.compile(r"\bgovernors?\b", re.IGNORECASE),
    re.compile(r"\bgovernador(?:a|es|as)?\b", re.IGNORECASE),
    re.compile(r"\bgobernador(?:a|es|as)?\b", re.IGNORECASE),
    re.compile(r"\bmayors?\b", re.IGNORECASE),
    re.compile(r"\bprefeit[oa]s?\b", re.IGNORECASE),
    re.compile(r"\balcalde(?:sa|s|sas)?\b", re.IGNORECASE),
    re.compile(r"\belections?\b", re.IGNORECASE),
    re.compile(r"\beleitoral\b", re.IGNORECASE),
    re.compile(r"\belectoral(?:es)?\b", re.IGNORECASE),
    re.compile(r"\belei[cç][aã]o\b", re.IGNORECASE),
    re.compile(r"\belei[cç][oõ]es\b", re.IGNORECASE),
    re.compile(r"\belecci[oó]n\b", re.IGNORECASE),
    re.compile(r"\belecciones\b", re.IGNORECASE),
    re.compile(r"\bre-?elections?\b", re.IGNORECASE),
    re.compile(r"\breelei[cç][aã]o\b", re.IGNORECASE),
    re.compile(r"\breelecci[oó]n\b", re.IGNORECASE),
)


class CompressedSparseRowMatrix:
    def __init__(
        self,
        dimension: int,
        values: Sequence[float],
        column_indices: Sequence[int],
        row_pointers: Sequence[int],
    ) -> None:
        if dimension <= 0:
            raise ValueError("Matrix dimension must be strictly positive.")
        if len(row_pointers) != dimension + 1:
            raise ValueError("row_pointers must have length dimension + 1.")
        if len(values) != len(column_indices):
            raise ValueError("values and column_indices must have identical lengths.")
        if row_pointers[0] != 0 or row_pointers[-1] != len(values):
            raise ValueError("CSR row_pointers must start at 0 and end at len(values).")
        if any(row_pointers[index] > row_pointers[index + 1] for index in range(dimension)):
            raise ValueError("CSR row_pointers must be monotonically non-decreasing.")
        if any(column_index < 0 or column_index >= dimension for column_index in column_indices):
            raise ValueError("CSR column_indices out of matrix dimension bounds.")
        if any(not math.isfinite(coefficient) or coefficient < 0.0 for coefficient in values):
            raise ValueError("CSR technical coefficients must be finite and non-negative.")
        self.dimension = dimension
        self.values = list(values)
        self.column_indices = list(column_indices)
        self.row_pointers = list(row_pointers)

    @classmethod
    def from_dense(
        cls, dense_rows: Sequence[Sequence[float]], zero_threshold: float = 1e-15
    ) -> CompressedSparseRowMatrix:
        dimension = len(dense_rows)
        if dimension == 0:
            raise ValueError("Dense matrix cannot be empty.")
        values: list[float] = []
        column_indices: list[int] = []
        row_pointers: list[int] = [0]
        for row in dense_rows:
            if len(row) != dimension:
                raise ValueError("Technical coefficient matrix A must be square.")
            for column_index, coefficient in enumerate(row):
                if coefficient < 0.0:
                    raise ValueError("Physical technical coefficients a_ij cannot be negative.")
                if abs(coefficient) > zero_threshold:
                    values.append(float(coefficient))
                    column_indices.append(column_index)
            row_pointers.append(len(values))
        return cls(dimension, values, column_indices, row_pointers)

    @property
    def non_zero_count(self) -> int:
        return len(self.values)

    def multiply_column_vector(self, column_vector: Sequence[float]) -> list[float]:
        if len(column_vector) != self.dimension:
            raise ValueError("Column vector dimension does not match CSR matrix.")
        result = [0.0] * self.dimension
        for row_index in range(self.dimension):
            row_sum = 0.0
            for ptr in range(self.row_pointers[row_index], self.row_pointers[row_index + 1]):
                row_sum += self.values[ptr] * column_vector[self.column_indices[ptr]]
            result[row_index] = row_sum
        return result

    def multiply_row_vector(self, row_vector: Sequence[float]) -> list[float]:
        if len(row_vector) != self.dimension:
            raise ValueError("Row vector dimension does not match CSR matrix.")
        result = [0.0] * self.dimension
        for row_index in range(self.dimension):
            multiplier = row_vector[row_index]
            if multiplier == 0.0:
                continue
            for ptr in range(self.row_pointers[row_index], self.row_pointers[row_index + 1]):
                result[self.column_indices[ptr]] += multiplier * self.values[ptr]
        return result

    def estimate_spectral_radius(self, max_iterations: int = 200, tolerance: float = 1e-9) -> float:
        unit_vector = [1.0 / math.sqrt(self.dimension)] * self.dimension
        eigenvalue_estimate = 0.0
        for _ in range(max_iterations):
            image_vector = self.multiply_column_vector(unit_vector)
            euclidean_norm = math.sqrt(sum(component * component for component in image_vector))
            if euclidean_norm == 0.0:
                return 0.0
            next_vector = [component / euclidean_norm for component in image_vector]
            vector_delta = max(abs(next_vector[i] - unit_vector[i]) for i in range(self.dimension))
            if vector_delta < tolerance and abs(euclidean_norm - eigenvalue_estimate) < tolerance:
                return euclidean_norm
            unit_vector = next_vector
            eigenvalue_estimate = euclidean_norm
        return eigenvalue_estimate


def solve_leontief_gross_output_gauss_seidel(
    technical_matrix: CompressedSparseRowMatrix,
    final_demand: Sequence[float],
    tolerance: float = 1e-8,
    max_iterations: int = 500,
) -> list[float]:
    dimension = technical_matrix.dimension
    if len(final_demand) != dimension:
        raise ValueError("Dimension of final_demand does not match technical_matrix.")
    if any(not math.isfinite(component) or component < 0.0 for component in final_demand):
        raise InfeasibleMacroPlanError("Physical final demand must be finite and non-negative.")

    spectral_radius = technical_matrix.estimate_spectral_radius()
    if spectral_radius >= 1.0:
        raise InfeasibleMacroPlanError(
            f"Economy violates Hawkins-Simon productivity condition: spectral radius "
            f"rho(A) = {spectral_radius:.6f} >= 1."
        )

    gross_output = [float(component) for component in final_demand]
    for _ in range(max_iterations):
        max_relative_change = 0.0
        for row_index in range(dimension):
            updated_value = float(final_demand[row_index])
            for ptr in range(
                technical_matrix.row_pointers[row_index],
                technical_matrix.row_pointers[row_index + 1],
            ):
                updated_value += (
                    technical_matrix.values[ptr]
                    * gross_output[technical_matrix.column_indices[ptr]]
                )
            relative_change = abs(updated_value - gross_output[row_index]) / max(
                1.0, abs(updated_value)
            )
            if relative_change > max_relative_change:
                max_relative_change = relative_change
            gross_output[row_index] = updated_value
        if max_relative_change < tolerance:
            return gross_output

    raise InfeasibleMacroPlanError("Gauss-Seidel solver failed to converge within max_iterations.")


def compute_embedded_labour_hours_jacobi(
    technical_matrix: CompressedSparseRowMatrix,
    direct_labour_vector: Sequence[float],
    tolerance: float = 1e-8,
    max_iterations: int = 500,
) -> list[float]:
    dimension = technical_matrix.dimension
    if len(direct_labour_vector) != dimension:
        raise ValueError("Dimension of direct_labour_vector does not match technical_matrix.")
    if any(not math.isfinite(hours) or hours < 0.0 for hours in direct_labour_vector):
        raise ValueError("Direct labour vector must contain finite non-negative values.")

    spectral_radius = technical_matrix.estimate_spectral_radius()
    if spectral_radius >= 1.0:
        raise InfeasibleMacroPlanError(
            f"Economy violates Hawkins-Simon productivity condition: spectral radius "
            f"rho(A) = {spectral_radius:.6f} >= 1."
        )

    embedded_labour = [float(hours) for hours in direct_labour_vector]
    for _ in range(max_iterations):
        indirect_labour = technical_matrix.multiply_row_vector(embedded_labour)
        next_embedded = [
            float(direct_labour_vector[j]) + indirect_labour[j] for j in range(dimension)
        ]
        max_relative_change = max(
            abs(next_embedded[j] - embedded_labour[j]) / max(1e-9, abs(next_embedded[j]))
            for j in range(dimension)
        )
        embedded_labour = next_embedded
        if max_relative_change < tolerance:
            return embedded_labour

    raise InfeasibleMacroPlanError("Jacobi embedded-labour solver failed to converge.")


def evaluate_asymmetric_cockshott_harmony(relative_fulfilment: float) -> float:
    if relative_fulfilment < 0.0:
        return -(relative_fulfilment * relative_fulfilment)
    return math.sqrt(relative_fulfilment)


def relax_short_run_capacity_harmony(
    technical_matrix: CompressedSparseRowMatrix,
    target_final_demand: Sequence[float],
    capacity_ceiling: Sequence[float],
    iterations: int = 80,
    step_gain: float = 0.25,
) -> tuple[list[float], list[float], list[float]]:
    dimension = technical_matrix.dimension
    if len(capacity_ceiling) != dimension:
        raise ValueError("Dimension of capacity_ceiling does not match technical_matrix.")
    if any(ceiling <= 0.0 for ceiling in capacity_ceiling):
        raise InfeasibleMacroPlanError("Installed capacity ceilings must be strictly positive.")

    unconstrained_gross_output = solve_leontief_gross_output_gauss_seidel(
        technical_matrix, target_final_demand
    )
    positive_capacity_ratios = [
        capacity_ceiling[i] / unconstrained_gross_output[i]
        for i in range(dimension)
        if unconstrained_gross_output[i] > 0.0
    ]
    initial_scale = min(1.0, min(positive_capacity_ratios)) if positive_capacity_ratios else 1.0
    gross_output = [unconstrained_gross_output[i] * initial_scale for i in range(dimension)]

    for iteration_step in range(iterations):
        intermediate_consumption = technical_matrix.multiply_column_vector(gross_output)
        net_output = [gross_output[i] - intermediate_consumption[i] for i in range(dimension)]
        sector_harmonies = [
            evaluate_asymmetric_cockshott_harmony(
                (net_output[i] - target_final_demand[i]) / max(1e-6, target_final_demand[i])
            )
            for i in range(dimension)
        ]
        mean_harmony = sum(sector_harmonies) / dimension
        annealing_factor = 1.0 - (iteration_step / max(1, iterations))
        for i in range(dimension):
            harmony_gap = mean_harmony - sector_harmonies[i]
            proposed_output = gross_output[i] * (1.0 + step_gain * annealing_factor * harmony_gap)
            gross_output[i] = min(capacity_ceiling[i], max(0.0, proposed_output))

        updated_intermediate = technical_matrix.multiply_column_vector(gross_output)
        for i in range(dimension):
            if gross_output[i] < updated_intermediate[i]:
                gross_output[i] = min(capacity_ceiling[i], updated_intermediate[i])

    final_intermediate = technical_matrix.multiply_column_vector(gross_output)
    final_net_output = [gross_output[i] - final_intermediate[i] for i in range(dimension)]
    final_harmonies = [
        evaluate_asymmetric_cockshott_harmony(
            (final_net_output[i] - target_final_demand[i]) / max(1e-6, target_final_demand[i])
        )
        for i in range(dimension)
    ]
    return gross_output, final_net_output, final_harmonies


@dataclass(frozen=True)
class MacroAllocationOption:
    option_id: str
    description: str
    target_final_demand: tuple[float, ...]
    budget_shares_pct: Mapping[str, float]


@dataclass(frozen=True)
class SimulatedOptionImpact:
    option_id: str
    required_gross_output: tuple[float, ...]
    total_embedded_labour_hours: float
    capacity_utilisation_peak: float


@dataclass(frozen=True)
class CompulsoryAllocationDirective:
    plebiscite_id: str
    winning_option_id: str
    winning_description: str
    total_valid_ballots: int
    votes_by_option: tuple[tuple[str, int], ...]
    compulsory_final_demand: tuple[float, ...]
    compulsory_gross_output: tuple[float, ...]
    compulsory_budget_shares_pct: tuple[tuple[str, float], ...]
    directive_hash: str


def assert_concrete_macroeconomic_topic(topic_text: str) -> None:
    if not topic_text.strip():
        raise InvalidPlebisciteTopicError("Macroeconomic plebiscite topic cannot be empty.")
    for forbidden_pattern in _ELECTORAL_PERSON_KEYWORDS:
        if forbidden_pattern.search(topic_text):
            raise InvalidPlebisciteTopicError(
                f"Blocked ballot topic ('{topic_text}'): the cybernetic plebiscite system votes exclusively "
                "on concrete macroeconomic resource flows, NEVER on candidates, persons or parties."
            )


class MacroAllocationPlebiscite:
    def __init__(
        self,
        plebiscite_id: str,
        question_prompt: str,
        sector_keys: Sequence[str],
        technical_matrix: CompressedSparseRowMatrix,
        direct_labour_vector: Sequence[float],
        capacity_ceiling: Sequence[float],
        max_available_labour_hours: float,
        options: Sequence[MacroAllocationOption],
    ) -> None:
        assert_concrete_macroeconomic_topic(question_prompt)
        if len(sector_keys) != technical_matrix.dimension or len(set(sector_keys)) != len(
            sector_keys
        ):
            raise ValueError(
                "sector_keys must contain unique labels matching technical_matrix dimension."
            )
        if len(capacity_ceiling) != technical_matrix.dimension:
            raise ValueError("Dimension of capacity_ceiling does not match technical_matrix.")
        if any(not math.isfinite(ceiling) or ceiling <= 0.0 for ceiling in capacity_ceiling):
            raise InfeasibleMacroPlanError(
                "Installed capacity ceilings must be finite and strictly positive."
            )
        if not math.isfinite(max_available_labour_hours) or max_available_labour_hours <= 0.0:
            raise InfeasibleMacroPlanError(
                "Maximum available social labour hours must be strictly positive."
            )
        if len(options) < 2:
            raise ValueError(
                "A macroeconomic plebiscite requires at least 2 concrete resource-flow options."
            )

        self.plebiscite_id = plebiscite_id
        self.question_prompt = question_prompt
        self.sector_keys = tuple(sector_keys)
        self.technical_matrix = technical_matrix
        self.embedded_labour = compute_embedded_labour_hours_jacobi(
            technical_matrix, direct_labour_vector
        )
        self.capacity_ceiling = tuple(capacity_ceiling)
        self.max_available_labour_hours = max_available_labour_hours
        self.options: dict[str, MacroAllocationOption] = {}
        self.simulated_impacts: dict[str, SimulatedOptionImpact] = {}

        expected_sector_set = set(self.sector_keys)
        for option in options:
            if option.option_id in self.options:
                raise ValueError(f"Duplicate allocation option identifier: '{option.option_id}'.")
            assert_concrete_macroeconomic_topic(option.description)
            if set(option.budget_shares_pct.keys()) != expected_sector_set:
                raise ValueError(
                    f"Option '{option.option_id}' budget share keys must match sector_keys."
                )
            if any(
                not math.isfinite(share) or share < 0.0
                for share in option.budget_shares_pct.values()
            ):
                raise InfeasibleMacroPlanError(
                    f"Option '{option.option_id}' contains negative or non-finite budget shares."
                )
            percentage_sum = sum(option.budget_shares_pct.values())
            if abs(percentage_sum - 100.0) > 1e-4:
                raise InfeasibleMacroPlanError(
                    f"Option '{option.option_id}' violates budget conservation: "
                    f"sum of shares = {percentage_sum:.4f}% != 100%."
                )
            gross_output = solve_leontief_gross_output_gauss_seidel(
                technical_matrix, option.target_final_demand
            )
            peak_utilisation = 0.0
            for index, sector_gross in enumerate(gross_output):
                if sector_gross > capacity_ceiling[index] + 1e-7:
                    raise InfeasibleMacroPlanError(
                        f"Option '{option.option_id}' exceeds physical capacity in sector "
                        f"'{sector_keys[index]}' ({sector_gross:.2f} > {capacity_ceiling[index]:.2f})."
                    )
                sector_ratio = sector_gross / capacity_ceiling[index]
                peak_utilisation = max(peak_utilisation, sector_ratio)

            total_labour_hours = sum(
                self.embedded_labour[j] * option.target_final_demand[j]
                for j in range(technical_matrix.dimension)
            )
            if total_labour_hours > max_available_labour_hours + 1e-7:
                raise InfeasibleMacroPlanError(
                    f"Option '{option.option_id}' requires {total_labour_hours:.2f} social labour hours, "
                    f"exceeding available ceiling ({max_available_labour_hours:.2f})."
                )

            self.options[option.option_id] = option
            self.simulated_impacts[option.option_id] = SimulatedOptionImpact(
                option_id=option.option_id,
                required_gross_output=tuple(round(value, 6) for value in gross_output),
                total_embedded_labour_hours=round(total_labour_hours, 6),
                capacity_utilisation_peak=round(peak_utilisation, 6),
            )

        self._anonymous_ballots_by_slot: dict[str, str] = {}
        self._sealed_directive: CompulsoryAllocationDirective | None = None

    def cast_anonymous_ballot(self, unlinkable_voter_token: str, option_id: str) -> None:
        if self._sealed_directive is not None:
            raise RuntimeError("Plebiscite has already been tallied and sealed.")
        if not unlinkable_voter_token.strip():
            raise ValueError("Voter token cannot be empty.")
        if option_id not in self.options:
            raise ValueError(f"Unknown allocation option: '{option_id}'.")
        blinded_slot = hashlib.sha256(
            f"{self.plebiscite_id}||{unlinkable_voter_token}".encode("utf-8")
        ).hexdigest()
        self._anonymous_ballots_by_slot[blinded_slot] = option_id

    def tally_and_seal_directive(self) -> CompulsoryAllocationDirective:
        if self._sealed_directive is not None:
            return self._sealed_directive
        if not self._anonymous_ballots_by_slot:
            raise RuntimeError("No ballots have been cast in the allocative plebiscite.")

        vote_counts = {option_id: 0 for option_id in sorted(self.options.keys())}
        for selected_option in self._anonymous_ballots_by_slot.values():
            vote_counts[selected_option] += 1

        highest_vote_total = max(vote_counts.values())
        top_option_ids = [
            option_id
            for option_id in sorted(vote_counts.keys())
            if vote_counts[option_id] == highest_vote_total
        ]
        ordered_counts = tuple(sorted(vote_counts.items()))

        if len(top_option_ids) == 1:
            winning_option_id = top_option_ids[0]
            winning_option = self.options[winning_option_id]
            winning_description = winning_option.description
            compulsory_final_demand = winning_option.target_final_demand
            compulsory_gross_output = self.simulated_impacts[
                winning_option_id
            ].required_gross_output
            ordered_shares = tuple(
                sorted(
                    (key, round(value, 4))
                    for key, value in winning_option.budget_shares_pct.items()
                )
            )
        else:
            tie_divisor = float(len(top_option_ids))
            winning_option_id = "TIED-EQUILIBRIUM"
            winning_description = "Balanced convex midpoint across tied options: " + ", ".join(
                top_option_ids
            )
            compulsory_final_demand = tuple(
                round(
                    sum(self.options[oid].target_final_demand[j] for oid in top_option_ids)
                    / tie_divisor,
                    6,
                )
                for j in range(self.technical_matrix.dimension)
            )
            solved_tie_gross = solve_leontief_gross_output_gauss_seidel(
                self.technical_matrix, compulsory_final_demand
            )
            compulsory_gross_output = tuple(round(value, 6) for value in solved_tie_gross)
            ordered_shares = tuple(
                sorted(
                    (
                        sector_key,
                        round(
                            sum(
                                self.options[oid].budget_shares_pct[sector_key]
                                for oid in top_option_ids
                            )
                            / tie_divisor,
                            4,
                        ),
                    )
                    for sector_key in self.sector_keys
                )
            )

        digest_payload = (
            f"CIBERSOC_MACRO_DIRECTIVE_V2|{self.plebiscite_id}|{winning_option_id}|"
            f"{ordered_counts}|{compulsory_final_demand}|{ordered_shares}"
        )
        directive_hash = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()

        self._sealed_directive = CompulsoryAllocationDirective(
            plebiscite_id=self.plebiscite_id,
            winning_option_id=winning_option_id,
            winning_description=winning_description,
            total_valid_ballots=len(self._anonymous_ballots_by_slot),
            votes_by_option=ordered_counts,
            compulsory_final_demand=compulsory_final_demand,
            compulsory_gross_output=compulsory_gross_output,
            compulsory_budget_shares_pct=ordered_shares,
            directive_hash=directive_hash,
        )
        return self._sealed_directive

    @staticmethod
    def compute_cockshott_continuous_shift(
        votes_increase: int,
        votes_unchanged: int,
        votes_decrease: int,
        max_annual_shift_pct: float = 5.0,
    ) -> float:
        if votes_increase < 0 or votes_unchanged < 0 or votes_decrease < 0:
            raise ValueError("Vote counts cannot be negative.")
        total_votes = votes_increase + votes_unchanged + votes_decrease
        if total_votes <= 0:
            raise ValueError("Total votes must be strictly positive.")
        return ((votes_increase - votes_decrease) / total_votes) * max_annual_shift_pct

    @staticmethod
    def verify_council_execution_compliance(
        directive: CompulsoryAllocationDirective,
        attempted_budget_shares_pct: Mapping[str, float],
        tolerance: float = 1e-4,
    ) -> None:
        expected_shares = dict(directive.compulsory_budget_shares_pct)
        if set(expected_shares.keys()) != set(attempted_budget_shares_pct.keys()):
            raise CompulsoryDirectiveOverrideError(
                "Allocative sovereignty violation: budget rubrics altered without authorisation by Council."
            )
        for sector_key, mandated_pct in expected_shares.items():
            attempted_pct = attempted_budget_shares_pct[sector_key]
            if abs(attempted_pct - mandated_pct) > tolerance:
                raise CompulsoryDirectiveOverrideError(
                    f"Illegal budget deviation in sector '{sector_key}': mandated = {mandated_pct:.4f}%, "
                    f"attempted by Council = {attempted_pct:.4f}%. Plebiscite execution is compulsory."
                )


@dataclass(frozen=True)
class MarketClearingFeedbackMetric:
    sector_id: str
    labor_value_hours: float
    market_clearing_price_tokens: float
    clearing_to_value_ratio: float
    reallocation_signal: float
    is_excess_demand: bool
    is_strumilin_equilibrium: bool


def evaluate_market_clearing_feedback(
    sector_id: str,
    labor_value_hours: float,
    market_clearing_price_tokens: float,
    response_gain: float = 0.5,
) -> MarketClearingFeedbackMetric:
    if labor_value_hours <= 0.0:
        raise ValueError("Labor value hours must be strictly positive.")
    if market_clearing_price_tokens < 0.0:
        raise ValueError("Market clearing price tokens cannot be negative.")

    ratio = market_clearing_price_tokens / labor_value_hours
    deviation = ratio - 1.0
    signal = response_gain * deviation
    is_eq = abs(deviation) < 1e-4
    is_excess = ratio > 1.0 and not is_eq

    return MarketClearingFeedbackMetric(
        sector_id=sector_id,
        labor_value_hours=labor_value_hours,
        market_clearing_price_tokens=market_clearing_price_tokens,
        clearing_to_value_ratio=round(ratio, 4),
        reallocation_signal=round(signal, 4),
        is_excess_demand=is_excess,
        is_strumilin_equilibrium=is_eq,
    )


def apply_cockshott_plan_iteration(
    current_final_demand: Sequence[float],
    feedback_metrics: Sequence[MarketClearingFeedbackMetric],
    adjustment_speed: float = 0.5,
) -> list[float]:
    if len(current_final_demand) != len(feedback_metrics):
        raise ValueError("Mismatched dimensions between demand vector and feedback metrics.")
    if any(demand < 0.0 for demand in current_final_demand):
        raise ValueError("Final demand values cannot be negative.")
    if adjustment_speed < 0.0:
        raise ValueError("Adjustment speed cannot be negative.")

    adjusted_demand: list[float] = []
    for demand, metric in zip(current_final_demand, feedback_metrics):
        ratio_deviation = metric.clearing_to_value_ratio - 1.0
        scale = max(0.05, 1.0 + adjustment_speed * ratio_deviation)
        adjusted_demand.append(round(demand * scale, 4))
    return adjusted_demand


@dataclass(frozen=True)
class KantorovichPlanRayResult:
    ray_vector: tuple[float, ...]
    max_expansion_lambda: float
    binding_resource_index: int
    balanced_output: tuple[float, ...]


def solve_kantorovich_plan_ray_expansion(
    proportional_ray: Sequence[float],
    available_capacities: Sequence[float],
    unit_input_requirements: Sequence[float],
) -> KantorovichPlanRayResult:
    if not (len(proportional_ray) == len(available_capacities) == len(unit_input_requirements)):
        raise ValueError("Mismatched dimensions for plan ray optimization.")
    if any(p <= 0.0 for p in proportional_ray):
        raise ValueError("Plan ray proportions must be strictly positive.")

    lambda_limits: list[float] = []
    for prop, cap, req in zip(proportional_ray, available_capacities, unit_input_requirements):
        consumption_per_lambda = prop * req
        if consumption_per_lambda <= 0.0:
            raise ValueError("Unit consumption per ray unit must be strictly positive.")
        lambda_limits.append(cap / consumption_per_lambda)

    min_lambda = min(lambda_limits)
    binding_idx = lambda_limits.index(min_lambda)
    balanced = tuple(round(prop * min_lambda, 4) for prop in proportional_ray)

    return KantorovichPlanRayResult(
        ray_vector=tuple(proportional_ray),
        max_expansion_lambda=round(min_lambda, 4),
        binding_resource_index=binding_idx,
        balanced_output=balanced,
    )


@dataclass(frozen=True)
class InNaturaEcologicalConstraint:
    annual_carbon_budget_megatons: float
    current_physical_carbon_draw: float
    carbon_intensity_per_output: tuple[float, ...]
    is_within_planetary_boundary: bool
    remaining_ecological_space: float


def audit_in_natura_ecological_budget(
    annual_carbon_budget_megatons: float,
    sector_outputs: Sequence[float],
    carbon_intensity_per_output: Sequence[float],
) -> InNaturaEcologicalConstraint:
    if len(sector_outputs) != len(carbon_intensity_per_output):
        raise ValueError("Mismatched sector output and carbon intensity lengths.")
    if annual_carbon_budget_megatons <= 0.0:
        raise ValueError("Ecological carbon budget must be strictly positive.")

    total_carbon = sum(
        out * intensity for out, intensity in zip(sector_outputs, carbon_intensity_per_output)
    )
    remaining = annual_carbon_budget_megatons - total_carbon
    is_safe = remaining >= 0.0

    return InNaturaEcologicalConstraint(
        annual_carbon_budget_megatons=round(annual_carbon_budget_megatons, 4),
        current_physical_carbon_draw=round(total_carbon, 4),
        carbon_intensity_per_output=tuple(carbon_intensity_per_output),
        is_within_planetary_boundary=is_safe,
        remaining_ecological_space=round(remaining, 4),
    )
