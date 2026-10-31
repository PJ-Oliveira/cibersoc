from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta


EXAM_SUBJECTS: tuple[str, ...] = (
    "LOGIC",
    "COMPUTING",
    "LANGUAGES",
    "MATHEMATICS",
    "GEOGRAPHY",
)

MINIMUM_SCORE: int = 60
RENEWAL_YEARS: int = 5
UPPER_AGE_LIMIT: int = 60
RETRY_DAYS_FIRST: int = 30
RETRY_DAYS_SUBSEQUENT: int = 60


@dataclass(frozen=True)
class SubjectScore:
    subject: str
    score: int


@dataclass(frozen=True)
class ExamAttempt:
    attempt_id: str
    citizen_id: str
    date_taken: date
    scores: tuple[SubjectScore, ...]
    passed: bool
    consecutive_failures: int


def _attempt_id(citizen_id: str, date_taken: date) -> str:
    payload = f"{citizen_id}:{date_taken.isoformat()}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _scores_pass(scores: tuple[SubjectScore, ...]) -> bool:
    return all(s.score >= MINIMUM_SCORE for s in scores)


def _next_due_after_pass(date_taken: date, dob: date) -> date | None:
    limit = date(dob.year + UPPER_AGE_LIMIT, dob.month, dob.day)
    try:
        candidate = date(date_taken.year + RENEWAL_YEARS, date_taken.month, date_taken.day)
    except ValueError:
        candidate = date(date_taken.year + RENEWAL_YEARS, date_taken.month, 28)
    if candidate >= limit:
        return None
    return candidate


def _next_due_after_fail(date_taken: date, consecutive_failures: int) -> date:
    days = RETRY_DAYS_FIRST if consecutive_failures == 1 else RETRY_DAYS_SUBSEQUENT
    return date_taken + timedelta(days=days)


@dataclass
class CitizenExamRecord:
    citizen_id: str
    date_of_birth: date
    attempts: list[ExamAttempt] = field(default_factory=list)

    def last_passing_attempt(self) -> ExamAttempt | None:
        for attempt in reversed(self.attempts):
            if attempt.passed:
                return attempt
        return None

    def next_due_date(self) -> date | None:
        if not self.attempts:
            return None
        last = self.attempts[-1]
        if last.passed:
            return _next_due_after_pass(last.date_taken, self.date_of_birth)
        return _next_due_after_fail(last.date_taken, last.consecutive_failures)

    def is_compliant(self, reference_date: date) -> bool:
        last_pass = self.last_passing_attempt()
        if last_pass is None:
            return False
        age_days = (reference_date - self.date_of_birth).days
        if age_days >= UPPER_AGE_LIMIT * 365:
            return True
        due = _next_due_after_pass(last_pass.date_taken, self.date_of_birth)
        if due is None:
            return True
        return reference_date <= due


class CivicExamScheduler:
    def record_attempt(
        self,
        record: CitizenExamRecord,
        scores: tuple[SubjectScore, ...],
        date_taken: date,
    ) -> ExamAttempt:
        passed = _scores_pass(scores)
        if passed:
            consecutive_failures = 0
        else:
            prev_failures = 0
            if record.attempts and not record.attempts[-1].passed:
                prev_failures = record.attempts[-1].consecutive_failures
            consecutive_failures = prev_failures + 1
        attempt = ExamAttempt(
            attempt_id=_attempt_id(record.citizen_id, date_taken),
            citizen_id=record.citizen_id,
            date_taken=date_taken,
            scores=scores,
            passed=passed,
            consecutive_failures=consecutive_failures,
        )
        record.attempts.append(attempt)
        return attempt

    def is_eligible_for_sortition(
        self, record: CitizenExamRecord, reference_date: date
    ) -> bool:
        return record.is_compliant(reference_date)
