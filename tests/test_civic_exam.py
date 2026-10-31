from __future__ import annotations

from datetime import date, timedelta

import pytest

from cibersoc.civic_exam import (
    EXAM_SUBJECTS,
    MINIMUM_SCORE,
    RENEWAL_YEARS,
    RETRY_DAYS_FIRST,
    RETRY_DAYS_SUBSEQUENT,
    UPPER_AGE_LIMIT,
    CitizenExamRecord,
    CivicExamScheduler,
    ExamAttempt,
    SubjectScore,
    _attempt_id,
    _next_due_after_fail,
    _next_due_after_pass,
    _scores_pass,
)


def _passing_scores() -> tuple[SubjectScore, ...]:
    return tuple(SubjectScore(s, MINIMUM_SCORE) for s in EXAM_SUBJECTS)


def _failing_scores() -> tuple[SubjectScore, ...]:
    scores = list(_passing_scores())
    scores[0] = SubjectScore(EXAM_SUBJECTS[0], MINIMUM_SCORE - 1)
    return tuple(scores)


def _dob(age: int) -> date:
    ref = date(2024, 6, 15)
    return ref.replace(year=ref.year - age)


def _record(age: int = 25) -> CitizenExamRecord:
    return CitizenExamRecord(citizen_id="CIT-001", date_of_birth=_dob(age))


def _scheduler() -> CivicExamScheduler:
    return CivicExamScheduler()


class TestSubjectScore:
    def test_frozen(self) -> None:
        s = SubjectScore("LOGIC", 75)
        with pytest.raises(Exception):
            s.score = 80

    def test_fields(self) -> None:
        s = SubjectScore("MATHEMATICS", 60)
        assert s.subject == "MATHEMATICS"
        assert s.score == 60


class TestExamSubjectsConstant:
    def test_five_subjects(self) -> None:
        assert len(EXAM_SUBJECTS) == 5
        assert "LOGIC" in EXAM_SUBJECTS
        assert "COMPUTING" in EXAM_SUBJECTS
        assert "LANGUAGES" in EXAM_SUBJECTS
        assert "MATHEMATICS" in EXAM_SUBJECTS
        assert "GEOGRAPHY" in EXAM_SUBJECTS


class TestScoresPass:
    def test_all_at_minimum_passes(self) -> None:
        assert _scores_pass(_passing_scores()) is True

    def test_one_below_minimum_fails(self) -> None:
        assert _scores_pass(_failing_scores()) is False

    def test_all_above_passes(self) -> None:
        scores = tuple(SubjectScore(s, 100) for s in EXAM_SUBJECTS)
        assert _scores_pass(scores) is True

    def test_all_zero_fails(self) -> None:
        scores = tuple(SubjectScore(s, 0) for s in EXAM_SUBJECTS)
        assert _scores_pass(scores) is False


class TestAttemptId:
    def test_returns_16_chars(self) -> None:
        aid = _attempt_id("CIT-001", date(2024, 1, 1))
        assert len(aid) == 16

    def test_deterministic(self) -> None:
        a = _attempt_id("CIT-042", date(2025, 3, 10))
        b = _attempt_id("CIT-042", date(2025, 3, 10))
        assert a == b

    def test_different_inputs_differ(self) -> None:
        a = _attempt_id("CIT-001", date(2024, 1, 1))
        b = _attempt_id("CIT-002", date(2024, 1, 1))
        assert a != b


class TestNextDueAfterPass:
    def test_renewal_is_five_years_ahead(self) -> None:
        taken = date(2024, 6, 1)
        dob = date(1990, 6, 1)
        result = _next_due_after_pass(taken, dob)
        assert result == date(2029, 6, 1)

    def test_returns_none_when_renewal_past_age_limit(self) -> None:
        dob = date(1965, 1, 1)
        taken = date(2024, 5, 1)
        result = _next_due_after_pass(taken, dob)
        assert result is None

    def test_exactly_at_limit_returns_none(self) -> None:
        dob = date(1970, 1, 1)
        limit = date(dob.year + UPPER_AGE_LIMIT, dob.month, dob.day)
        taken = limit - timedelta(days=RENEWAL_YEARS * 365 - 1)
        result = _next_due_after_pass(taken, dob)
        assert result is None


class TestNextDueAfterFail:
    def test_first_failure_is_30_days(self) -> None:
        taken = date(2024, 1, 1)
        result = _next_due_after_fail(taken, 1)
        assert result == taken + timedelta(days=RETRY_DAYS_FIRST)

    def test_second_failure_is_60_days(self) -> None:
        taken = date(2024, 1, 1)
        result = _next_due_after_fail(taken, 2)
        assert result == taken + timedelta(days=RETRY_DAYS_SUBSEQUENT)

    def test_third_failure_is_still_60_days(self) -> None:
        taken = date(2024, 1, 1)
        assert _next_due_after_fail(taken, 3) == taken + timedelta(days=RETRY_DAYS_SUBSEQUENT)


class TestCitizenExamRecordLastPassing:
    def test_no_attempts_returns_none(self) -> None:
        record = _record()
        assert record.last_passing_attempt() is None

    def test_returns_most_recent_pass(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _passing_scores(), date(2020, 1, 1))
        sched.record_attempt(record, _passing_scores(), date(2023, 1, 1))
        result = record.last_passing_attempt()
        assert result is not None
        assert result.date_taken == date(2023, 1, 1)

    def test_skips_failures_to_find_last_pass(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _passing_scores(), date(2020, 1, 1))
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        result = record.last_passing_attempt()
        assert result is not None
        assert result.date_taken == date(2020, 1, 1)

    def test_only_failures_returns_none(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        assert record.last_passing_attempt() is None


class TestCitizenExamRecordNextDue:
    def test_no_attempts_returns_none(self) -> None:
        assert _record().next_due_date() is None

    def test_after_pass_is_five_years(self) -> None:
        sched = _scheduler()
        record = _record(age=25)
        sched.record_attempt(record, _passing_scores(), date(2024, 6, 1))
        assert record.next_due_date() == date(2029, 6, 1)

    def test_after_first_fail_is_30_days(self) -> None:
        sched = _scheduler()
        record = _record(age=25)
        sched.record_attempt(record, _failing_scores(), date(2024, 6, 1))
        assert record.next_due_date() == date(2024, 6, 1) + timedelta(days=RETRY_DAYS_FIRST)

    def test_after_second_fail_is_60_days(self) -> None:
        sched = _scheduler()
        record = _record(age=25)
        sched.record_attempt(record, _failing_scores(), date(2024, 6, 1))
        sched.record_attempt(record, _failing_scores(), date(2024, 7, 1))
        assert record.next_due_date() == date(2024, 7, 1) + timedelta(days=RETRY_DAYS_SUBSEQUENT)

    def test_after_pass_near_age_limit_returns_none(self) -> None:
        sched = _scheduler()
        record = _record(age=56)
        sched.record_attempt(record, _passing_scores(), date(2024, 6, 1))
        assert record.next_due_date() is None


class TestCitizenExamRecordIsCompliant:
    def test_no_attempts_not_compliant(self) -> None:
        assert _record().is_compliant(date(2024, 1, 1)) is False

    def test_valid_pass_within_window_compliant(self) -> None:
        sched = _scheduler()
        record = _record(age=30)
        sched.record_attempt(record, _passing_scores(), date(2022, 1, 1))
        assert record.is_compliant(date(2024, 1, 1)) is True

    def test_pass_expired_not_compliant(self) -> None:
        sched = _scheduler()
        record = _record(age=30)
        sched.record_attempt(record, _passing_scores(), date(2015, 1, 1))
        assert record.is_compliant(date(2024, 1, 1)) is False

    def test_citizen_over_60_always_compliant(self) -> None:
        sched = _scheduler()
        record = _record(age=62)
        sched.record_attempt(record, _passing_scores(), date(2000, 1, 1))
        assert record.is_compliant(date(2024, 1, 1)) is True

    def test_pass_renewal_past_age_60_still_compliant(self) -> None:
        sched = _scheduler()
        record = _record(age=57)
        sched.record_attempt(record, _passing_scores(), date(2024, 1, 1))
        assert record.is_compliant(date(2024, 6, 1)) is True

    def test_only_failures_not_compliant(self) -> None:
        sched = _scheduler()
        record = _record(age=25)
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        assert record.is_compliant(date(2024, 1, 1)) is False


class TestCivicExamSchedulerRecordAttempt:
    def test_passing_attempt_consecutive_failures_zero(self) -> None:
        sched = _scheduler()
        record = _record()
        attempt = sched.record_attempt(record, _passing_scores(), date(2024, 1, 1))
        assert attempt.passed is True
        assert attempt.consecutive_failures == 0

    def test_first_failure_consecutive_one(self) -> None:
        sched = _scheduler()
        record = _record()
        attempt = sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        assert attempt.passed is False
        assert attempt.consecutive_failures == 1

    def test_second_failure_consecutive_two(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        attempt = sched.record_attempt(record, _failing_scores(), date(2024, 2, 1))
        assert attempt.consecutive_failures == 2

    def test_third_failure_consecutive_three(self) -> None:
        sched = _scheduler()
        record = _record()
        for m in (1, 2, 3):
            attempt = sched.record_attempt(record, _failing_scores(), date(2024, m, 1))
        assert attempt.consecutive_failures == 3

    def test_pass_after_failures_resets_consecutive(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        sched.record_attempt(record, _failing_scores(), date(2024, 2, 1))
        attempt = sched.record_attempt(record, _passing_scores(), date(2024, 3, 1))
        assert attempt.passed is True
        assert attempt.consecutive_failures == 0

    def test_attempt_appended_to_record(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _passing_scores(), date(2024, 1, 1))
        assert len(record.attempts) == 1

    def test_failure_after_pass_starts_new_streak(self) -> None:
        sched = _scheduler()
        record = _record()
        sched.record_attempt(record, _passing_scores(), date(2023, 1, 1))
        attempt = sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        assert attempt.consecutive_failures == 1

    def test_attempt_id_deterministic(self) -> None:
        sched = _scheduler()
        r1 = _record()
        r2 = _record()
        a1 = sched.record_attempt(r1, _passing_scores(), date(2024, 5, 1))
        a2 = sched.record_attempt(r2, _passing_scores(), date(2024, 5, 1))
        assert a1.attempt_id == a2.attempt_id


class TestCivicExamSchedulerEligibility:
    def test_compliant_citizen_eligible(self) -> None:
        sched = _scheduler()
        record = _record(age=30)
        sched.record_attempt(record, _passing_scores(), date(2022, 1, 1))
        assert sched.is_eligible_for_sortition(record, date(2024, 1, 1)) is True

    def test_non_compliant_not_eligible(self) -> None:
        sched = _scheduler()
        record = _record(age=30)
        sched.record_attempt(record, _failing_scores(), date(2024, 1, 1))
        assert sched.is_eligible_for_sortition(record, date(2024, 1, 1)) is False

    def test_no_attempts_not_eligible(self) -> None:
        sched = _scheduler()
        record = _record()
        assert sched.is_eligible_for_sortition(record, date(2024, 1, 1)) is False


class TestNextDueAfterPassLeapYear:
    def test_feb29_dob_renewal(self) -> None:
        dob = date(1980, 1, 10)
        taken = date(2020, 2, 29)
        result = _next_due_after_pass(taken, dob)
        assert result is not None
        assert result.year == 2025
        assert result.month == 2

    def test_feb29_dob_non_leap_century_limit(self) -> None:
        dob = date(2040, 2, 29)
        taken = date(2060, 1, 1)
        result = _next_due_after_pass(taken, dob)
        assert result is not None
        assert result.year == 2065
