from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from enum import StrEnum
import hashlib
import math
import re
from typing import Sequence


class OrganisationalViolationError(RuntimeError):
    pass


class PropertyRegimeViolationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PropertyRightsBitmask:
    use: bool
    sell: bool
    buy: bool
    inherit: bool

    @property
    def state_code(self) -> int:
        return (
            (int(self.use) << 3) | (int(self.sell) << 2) | (int(self.buy) << 1) | int(self.inherit)
        )

    def assert_socialist_productive_unit(self) -> None:
        if (self.use, self.sell, self.buy, self.inherit) != (True, False, False, False):
            raise PropertyRegimeViolationError(
                f"Invalid property bitmask ({self.state_code}): socialist productive units require "
                "[Use=1, Sell=0, Buy=0, Inherit=0] (state 8). Private accumulation and alienation are forbidden."
            )


SOCIALIST_ENTERPRISE_PROPERTY = PropertyRightsBitmask(
    use=True, sell=False, buy=False, inherit=False
)

_FORBIDDEN_EXECUTIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bceo\b", re.IGNORECASE),
    re.compile(r"\bcfo\b", re.IGNORECASE),
    re.compile(r"\bcoo\b", re.IGNORECASE),
    re.compile(r"\bchief\s+\w+\s+officer\b", re.IGNORECASE),
    re.compile(r"\bmanaging\s+director\b", re.IGNORECASE),
    re.compile(r"\bexecutive\s+president\b", re.IGNORECASE),
    re.compile(r"\bdiretor[\s\-]*presidente\b", re.IGNORECASE),
    re.compile(r"\bpresidente\s+executivo\b", re.IGNORECASE),
    re.compile(r"\bpresidente\s+ejecutivo\b", re.IGNORECASE),
    re.compile(r"\bmajority\s+shareholder\b", re.IGNORECASE),
    re.compile(r"\bshareholder\b", re.IGNORECASE),
    re.compile(r"\bacionista\b", re.IGNORECASE),
    re.compile(r"\baccionista\b", re.IGNORECASE),
)


class EmploymentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEMARCHIC_SUSPENSION = "DEMARCHIC_SUSPENSION"
    REINSTATED_PROTECTED = "REINSTATED_PROTECTED"


@dataclass
class WorkerMember:
    worker_id: str
    full_name: str
    role_title: str
    monthly_base_pay: Decimal
    active_days_in_period: int
    status: EmploymentStatus = EmploymentStatus.ACTIVE
    has_unilateral_executive_power: bool = False
    profit_share_weight: Decimal = Decimal("1")


@dataclass(frozen=True)
class ProfitDistributionReceipt:
    enterprise_id: str
    period_label: str
    gross_revenue: Decimal
    audited_material_costs: Decimal
    physical_depreciation_reserve: Decimal
    macro_social_contribution: Decimal
    capital_endowment_equalisation_charge: Decimal
    base_payroll_total: Decimal
    prior_carry_over: Decimal
    distributable_net_profit: Decimal
    eligible_worker_count: int
    equal_full_share_per_worker: Decimal
    payouts_by_worker: tuple[tuple[str, Decimal], ...]
    corporate_retained_profit: Decimal
    next_carry_over_cents: Decimal
    audit_hash: str


def validate_worker_member(worker: WorkerMember) -> None:
    if not worker.worker_id.strip() or not worker.full_name.strip():
        raise ValueError("Worker identifier and full name cannot be empty.")
    stripped_title = worker.role_title.strip()
    if not stripped_title:
        raise ValueError(f"Empty role_title for worker '{worker.worker_id}'.")
    for forbidden_pattern in _FORBIDDEN_EXECUTIVE_PATTERNS:
        if forbidden_pattern.search(stripped_title):
            raise OrganisationalViolationError(
                f"Horizontal governance invariant violated ('{worker.role_title}'): unilateral executive "
                "roles (CEO/C-Suite) are excluded under productive usufruct bitmask [1,0,0,0]."
            )
    if worker.has_unilateral_executive_power:
        raise OrganisationalViolationError(
            f"Organisational violation on '{worker.worker_id}': unilateral executive authority is forbidden."
        )
    if not worker.profit_share_weight.is_finite() or worker.profit_share_weight != Decimal("1"):
        raise OrganisationalViolationError(
            f"Equality violation on '{worker.worker_id}': profit_share_weight ({worker.profit_share_weight}) != 1. "
            "Surplus distribution must be strictly equal across all workers."
        )
    if not worker.monthly_base_pay.is_finite() or worker.monthly_base_pay < Decimal("0"):
        raise ValueError(
            f"Monthly base pay for '{worker.worker_id}' must be finite and non-negative."
        )
    if worker.active_days_in_period < 0:
        raise ValueError(f"Active days for '{worker.worker_id}' cannot be negative.")


@dataclass
class SocialistEnterprise:
    enterprise_id: str
    name: str
    sector_code: str
    property_mask: PropertyRightsBitmask = field(default=SOCIALIST_ENTERPRISE_PROPERTY)
    workers: dict[str, WorkerMember] = field(default_factory=dict)
    carry_over_cents: Decimal = field(default=Decimal("0.00"))

    def __post_init__(self) -> None:
        self.property_mask.assert_socialist_productive_unit()
        if not self.carry_over_cents.is_finite() or self.carry_over_cents < Decimal("0"):
            raise ValueError("Enterprise carry_over_cents must be finite and non-negative.")
        for worker in self.workers.values():
            validate_worker_member(worker)

    def register_worker(self, worker: WorkerMember) -> None:
        validate_worker_member(worker)
        self.workers[worker.worker_id] = worker

    def distribute_period_profit(
        self,
        period_label: str,
        period_total_days: int,
        gross_revenue: Decimal,
        audited_material_costs: Decimal,
        physical_depreciation_reserve: Decimal,
        macro_social_contribution: Decimal,
        capital_endowment_equalisation_charge: Decimal = Decimal("0.00"),
    ) -> ProfitDistributionReceipt:
        self.property_mask.assert_socialist_productive_unit()
        if period_total_days <= 0:
            raise ValueError("Period total days must be strictly positive.")
        if any(
            not amount.is_finite() or amount < Decimal("0")
            for amount in (
                gross_revenue,
                audited_material_costs,
                physical_depreciation_reserve,
                macro_social_contribution,
                capital_endowment_equalisation_charge,
            )
        ):
            raise ValueError("Financial ledger entries must be finite and non-negative.")

        for worker in self.workers.values():
            validate_worker_member(worker)
            if worker.active_days_in_period > period_total_days:
                raise ValueError(
                    f"Active days for '{worker.worker_id}' ({worker.active_days_in_period}) "
                    f"exceed period_total_days ({period_total_days})."
                )

        eligible_active_workers = [
            worker
            for worker in sorted(self.workers.values(), key=lambda entry: entry.worker_id)
            if worker.status in (EmploymentStatus.ACTIVE, EmploymentStatus.REINSTATED_PROTECTED)
            and worker.active_days_in_period > 0
        ]
        if not eligible_active_workers:
            raise ValueError(
                f"Enterprise '{self.enterprise_id}' has no active workers in the period."
            )

        base_payroll_total = sum(
            (
                (
                    worker.monthly_base_pay
                    * Decimal(worker.active_days_in_period)
                    / Decimal(period_total_days)
                ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
                for worker in eligible_active_workers
            ),
            start=Decimal("0.00"),
        )

        prior_carry_over = self.carry_over_cents
        net_operating_surplus = (
            gross_revenue
            - audited_material_costs
            - physical_depreciation_reserve
            - macro_social_contribution
            - capital_endowment_equalisation_charge
            - base_payroll_total
            + prior_carry_over
        ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        if net_operating_surplus <= Decimal("0.00"):
            zero_payouts = tuple(
                (worker.worker_id, Decimal("0.00")) for worker in eligible_active_workers
            )
            self.carry_over_cents = Decimal("0.00")
            zero_hash = self._compute_receipt_digest(
                period_label, Decimal("0.00"), zero_payouts, Decimal("0.00")
            )
            return ProfitDistributionReceipt(
                enterprise_id=self.enterprise_id,
                period_label=period_label,
                gross_revenue=gross_revenue,
                audited_material_costs=audited_material_costs,
                physical_depreciation_reserve=physical_depreciation_reserve,
                macro_social_contribution=macro_social_contribution,
                capital_endowment_equalisation_charge=capital_endowment_equalisation_charge,
                base_payroll_total=base_payroll_total,
                prior_carry_over=prior_carry_over,
                distributable_net_profit=Decimal("0.00"),
                eligible_worker_count=len(eligible_active_workers),
                equal_full_share_per_worker=Decimal("0.00"),
                payouts_by_worker=zero_payouts,
                corporate_retained_profit=Decimal("0.00"),
                next_carry_over_cents=Decimal("0.00"),
                audit_hash=zero_hash,
            )

        total_active_worker_days = sum(
            worker.active_days_in_period for worker in eligible_active_workers
        )
        full_period_divisor = math.gcd(period_total_days, total_active_worker_days)
        equal_full_unit_share = (
            net_operating_surplus
            * Decimal(period_total_days // full_period_divisor)
            / Decimal(total_active_worker_days // full_period_divisor)
        ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        worker_payouts: list[tuple[str, Decimal]] = []
        distributed_total = Decimal("0.00")
        for worker in eligible_active_workers:
            worker_divisor = math.gcd(worker.active_days_in_period, total_active_worker_days)
            worker_share = (
                net_operating_surplus
                * Decimal(worker.active_days_in_period // worker_divisor)
                / Decimal(total_active_worker_days // worker_divisor)
            ).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
            worker_payouts.append((worker.worker_id, worker_share))
            distributed_total += worker_share

        indivisible_residual_cents = (net_operating_surplus - distributed_total).quantize(
            Decimal("0.01")
        )
        self.carry_over_cents = indivisible_residual_cents

        payouts_tuple = tuple(worker_payouts)
        receipt_digest = self._compute_receipt_digest(
            period_label, net_operating_surplus, payouts_tuple, indivisible_residual_cents
        )

        return ProfitDistributionReceipt(
            enterprise_id=self.enterprise_id,
            period_label=period_label,
            gross_revenue=gross_revenue,
            audited_material_costs=audited_material_costs,
            physical_depreciation_reserve=physical_depreciation_reserve,
            macro_social_contribution=macro_social_contribution,
            capital_endowment_equalisation_charge=capital_endowment_equalisation_charge,
            base_payroll_total=base_payroll_total,
            prior_carry_over=prior_carry_over,
            distributable_net_profit=net_operating_surplus,
            eligible_worker_count=len(eligible_active_workers),
            equal_full_share_per_worker=equal_full_unit_share,
            payouts_by_worker=payouts_tuple,
            corporate_retained_profit=Decimal("0.00"),
            next_carry_over_cents=indivisible_residual_cents,
            audit_hash=receipt_digest,
        )

    def _compute_receipt_digest(
        self,
        period_label: str,
        distributable_profit: Decimal,
        payouts: Sequence[tuple[str, Decimal]],
        carry_over: Decimal,
    ) -> str:
        serialised_payouts = "|".join(f"{worker_id}:{amount}" for worker_id, amount in payouts)
        payload = (
            f"CIBERSOC_SURPLUS_V2|{self.enterprise_id}|{period_label}|"
            f"{distributable_profit}|{serialised_payouts}|carry={carry_over}|retained=0.00"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
