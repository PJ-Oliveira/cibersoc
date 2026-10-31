from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Mapping

from .councils import CouncilTier
from .enterprise import EmploymentStatus, SocialistEnterprise


class EmploymentStabilityLockError(RuntimeError):
    pass


class MandateProtectionConfigurationError(ValueError):
    pass


MINIMUM_POST_MANDATE_STABILITY_DAYS: int = 180


@dataclass
class MandateProtectionRecord:
    citizen_id: str
    council_id: str
    tier: CouncilTier
    employer_id: str
    original_role_title: str
    original_monthly_base_pay: Decimal
    prior_civilian_monthly_income: Decimal
    entry_price_index: Decimal
    mandate_start_date: date
    mandate_end_date: date
    reinstated_on: date | None = None
    stability_locked_until: date | None = None
    reinstated_monthly_base_pay: Decimal | None = None


class PriceIndexSeries:
    def __init__(self, base_index: Decimal = Decimal("100.000000")) -> None:
        if not base_index.is_finite() or base_index <= Decimal("0"):
            raise ValueError("Base price index must be finite and strictly positive.")
        self._current_index = base_index
        self._history: list[tuple[str, Decimal, Decimal]] = [
            ("BASE", Decimal("0.0000"), base_index)
        ]

    @property
    def current_index(self) -> Decimal:
        return self._current_index

    @property
    def history(self) -> tuple[tuple[str, Decimal, Decimal], ...]:
        return tuple(self._history)

    def apply_monthly_inflation(self, month_label: str, monthly_rate: Decimal) -> Decimal:
        if not month_label.strip():
            raise ValueError("Month label cannot be empty.")
        if not monthly_rate.is_finite() or monthly_rate <= Decimal("-1"):
            raise ValueError("Monthly inflation rate must be finite and greater than -100%.")
        self._current_index = (self._current_index * (Decimal("1") + monthly_rate)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )
        self._history.append((month_label, monthly_rate, self._current_index))
        return self._current_index


class MandateProtectionManager:
    def __init__(self, enterprises_by_id: Mapping[str, SocialistEnterprise]) -> None:
        self._enterprises_by_id = enterprises_by_id
        self._records_by_citizen: dict[str, MandateProtectionRecord] = {}

    def get_record(self, citizen_id: str) -> MandateProtectionRecord | None:
        return self._records_by_citizen.get(citizen_id)

    def activate_council_mandate(
        self,
        citizen_id: str,
        council_id: str,
        tier: CouncilTier,
        employer_id: str,
        prior_civilian_monthly_income: Decimal,
        current_price_index: Decimal,
        start_date: date,
        end_date: date,
    ) -> MandateProtectionRecord:
        if (
            not prior_civilian_monthly_income.is_finite()
            or prior_civilian_monthly_income <= Decimal("0")
        ):
            raise MandateProtectionConfigurationError(
                "Prior civilian monthly income must be strictly positive."
            )
        if not current_price_index.is_finite() or current_price_index <= Decimal("0"):
            raise MandateProtectionConfigurationError(
                "Entry price index must be strictly positive."
            )
        if end_date <= start_date:
            raise MandateProtectionConfigurationError(
                "Mandate end_date must be later than start_date."
            )
        if (end_date - start_date).days > 735:
            raise MandateProtectionConfigurationError(
                "Demarchic mandates in CIBERSOC are strictly short-term (maximum 24 months)."
            )

        existing_record = self._records_by_citizen.get(citizen_id)
        if existing_record is not None and existing_record.reinstated_on is None:
            raise MandateProtectionConfigurationError(
                f"Citizen '{citizen_id}' is already serving an active demarchic mandate."
            )

        enterprise = self._enterprises_by_id.get(employer_id)
        if enterprise is None or citizen_id not in enterprise.workers:
            raise ValueError(f"Worker '{citizen_id}' not found in enterprise '{employer_id}'.")

        worker = enterprise.workers[citizen_id]
        original_role_title = worker.role_title
        original_monthly_base_pay = worker.monthly_base_pay
        worker.status = EmploymentStatus.DEMARCHIC_SUSPENSION
        worker.active_days_in_period = 0

        protection_record = MandateProtectionRecord(
            citizen_id=citizen_id,
            council_id=council_id,
            tier=tier,
            employer_id=employer_id,
            original_role_title=original_role_title,
            original_monthly_base_pay=original_monthly_base_pay,
            prior_civilian_monthly_income=prior_civilian_monthly_income.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_EVEN
            ),
            entry_price_index=current_price_index,
            mandate_start_date=start_date,
            mandate_end_date=end_date,
        )
        self._records_by_citizen[citizen_id] = protection_record
        return protection_record

    def compute_state_councillor_stipend(
        self, citizen_id: str, current_price_index: Decimal
    ) -> Decimal:
        protection_record = self._records_by_citizen[citizen_id]
        if protection_record.reinstated_on is not None:
            raise RuntimeError(
                f"Mandate for '{citizen_id}' has already concluded; citizen has returned to civilian employment."
            )
        if not current_price_index.is_finite() or current_price_index <= Decimal("0"):
            raise ValueError("Current price index must be strictly positive.")

        inflation_multiplier = current_price_index / protection_record.entry_price_index
        return (protection_record.prior_civilian_monthly_income * inflation_multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )

    def conclude_mandate_and_reinstate(
        self,
        citizen_id: str,
        return_date: date,
        current_price_index: Decimal,
        stability_days: int = MINIMUM_POST_MANDATE_STABILITY_DAYS,
        period_active_days: int = 30,
    ) -> MandateProtectionRecord:
        if stability_days < MINIMUM_POST_MANDATE_STABILITY_DAYS:
            raise MandateProtectionConfigurationError(
                f"Labour protection violation: requested stability ({stability_days} days) is below "
                f"the constitutional floor of {MINIMUM_POST_MANDATE_STABILITY_DAYS} days (6 months)."
            )
        if not current_price_index.is_finite() or current_price_index <= Decimal("0"):
            raise ValueError("Reinstatement price index must be strictly positive.")
        if period_active_days < 0:
            raise ValueError("Reinstatement period_active_days cannot be negative.")

        protection_record = self._records_by_citizen[citizen_id]
        if protection_record.reinstated_on is not None:
            raise RuntimeError(
                f"Mandate for '{citizen_id}' has already been concluded and reinstated."
            )
        if return_date < protection_record.mandate_end_date:
            raise MandateProtectionConfigurationError(
                "Return date cannot precede the formal conclusion of the mandate."
            )

        enterprise = self._enterprises_by_id[protection_record.employer_id]
        worker = enterprise.workers[citizen_id]

        inflation_multiplier = current_price_index / protection_record.entry_price_index
        worker.role_title = protection_record.original_role_title
        worker.monthly_base_pay = (
            protection_record.original_monthly_base_pay * inflation_multiplier
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        worker.status = EmploymentStatus.REINSTATED_PROTECTED
        worker.active_days_in_period = period_active_days

        stability_deadline = return_date + timedelta(days=stability_days)
        protection_record.reinstated_on = return_date
        protection_record.stability_locked_until = stability_deadline
        protection_record.reinstated_monthly_base_pay = worker.monthly_base_pay
        return protection_record

    def validate_termination_attempt(
        self,
        citizen_id: str,
        attempt_date: date,
        proven_criminal_misconduct: bool = False,
    ) -> bool:
        protection_record = self._records_by_citizen.get(citizen_id)
        if protection_record is None or protection_record.stability_locked_until is None:
            return True

        if (
            attempt_date <= protection_record.stability_locked_until
            and not proven_criminal_misconduct
        ):
            raise EmploymentStabilityLockError(
                f"Dismissal blocked by CIBERSOC: worker '{citizen_id}' returned from a demarchic mandate "
                f"on {protection_record.reinstated_on} and holds protected stability until "
                f"{protection_record.stability_locked_until}."
            )
        return True
