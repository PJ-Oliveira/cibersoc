from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import pytest

from cibersoc.councils import (
    AgendaItem,
    AutocraticActForbiddenError,
    CivilianMilitaryCommandGate,
    CouncilTier,
    DemarchicCouncil,
    EscalatedCouncilMesh,
    GeneralOfficer,
    MilitarySubordinationViolationError,
    SecretaryGeneral,
    assert_no_autocratic_title,
)
from cibersoc.cybernetics import (
    CompressedSparseRowMatrix,
    CompulsoryDirectiveOverrideError,
    InfeasibleMacroPlanError,
    InvalidPlebisciteTopicError,
    MacroAllocationOption,
    MacroAllocationPlebiscite,
    assert_concrete_macroeconomic_topic,
    compute_embedded_labour_hours_jacobi,
    compute_embedded_labour_shares_pct,
    derive_final_demand_from_labour_shares,
    evaluate_asymmetric_cockshott_harmony,
    relax_short_run_capacity_harmony,
    solve_leontief_gross_output_gauss_seidel,
)
from cibersoc.enterprise import (
    EmploymentStatus,
    OrganisationalViolationError,
    PropertyRegimeViolationError,
    PropertyRightsBitmask,
    SOCIALIST_ENTERPRISE_PROPERTY,
    SocialistEnterprise,
    WorkerMember,
    validate_worker_member,
)
from cibersoc.mandate_protection import (
    EmploymentStabilityLockError,
    MandateProtectionConfigurationError,
    MandateProtectionManager,
    PriceIndexSeries,
)
from cibersoc.sortition import (
    CitizenProfile,
    CivilianSupremacyViolationError,
    CommitRevealEntropyBeacon,
    CounterModeHmacDrbg,
    ElectoralOperationForbiddenError,
    EntropyVerificationError,
    MinistryPortfolio,
    StratifiedSortitionEngine,
    allocate_proportional_hamilton_quotas,
    compute_merkle_root,
)
from cibersoc.ui.state import SimulationOrchestrator


def _build_real_federated_population() -> list[CitizenProfile]:
    return SimulationOrchestrator._generate_federated_population()


def _create_ready_beacon(tag: str = "B1") -> CommitRevealEntropyBeacon:
    beacon = CommitRevealEntropyBeacon(minimum_sources=3)
    sources = (
        ("UNIV-PARANA-CRYPTO", f"ufpr-entropy-{tag}", f"nonce-a-{tag}"),
        ("CIVIC-AUDIT-BAHIA", f"ufba-entropy-{tag}", f"nonce-b-{tag}"),
        ("METROLOGY-OBSERVATORY", f"inmetro-entropy-{tag}", f"nonce-c-{tag}"),
    )
    for source_id, secret_seed, nonce in sources:
        beacon.publish_commitment(
            source_id, CommitRevealEntropyBeacon.create_commitment(secret_seed, nonce)
        )
    beacon.lock_commitments()
    for source_id, secret_seed, nonce in sources:
        beacon.reveal_seed(source_id, secret_seed, nonce)
    return beacon


def test_real_cryptography_merkle_beacon_drbg_and_hamilton_quotas() -> None:
    empty_digest = compute_merkle_root([])
    assert len(empty_digest) == 64
    single_digest = compute_merkle_root(["CID-0001"])
    odd_digest = compute_merkle_root(["CID-0003", "CID-0001", "CID-0002", "CID-0001"])
    assert single_digest != empty_digest
    assert len(odd_digest) == 64

    with pytest.raises(ValueError):
        CommitRevealEntropyBeacon(minimum_sources=1)

    beacon = CommitRevealEntropyBeacon(minimum_sources=2)
    commit_a = beacon.create_commitment("ufpr-real-seed-2026", "nonce-alpha-01")

    with pytest.raises(EntropyVerificationError):
        beacon.publish_commitment("   ", commit_a)
    with pytest.raises(EntropyVerificationError):
        beacon.publish_commitment("NODE-1", "abc123")
    with pytest.raises(EntropyVerificationError):
        beacon.publish_commitment("NODE-1", "z" * 64)

    beacon.publish_commitment("NODE-1", commit_a.upper())
    with pytest.raises(EntropyVerificationError):
        beacon.publish_commitment("NODE-1", commit_a)
    with pytest.raises(EntropyVerificationError):
        beacon.lock_commitments()
    with pytest.raises(EntropyVerificationError):
        beacon.reveal_seed("NODE-1", "ufpr-real-seed-2026", "nonce-alpha-01")
    with pytest.raises(EntropyVerificationError):
        beacon.derive_master_seed("CONS-FED-BRASIL", 1, odd_digest)

    beacon.publish_commitment("NODE-2", beacon.create_commitment("ufba-real-seed-2026", "nonce-beta-02"))
    beacon.lock_commitments()

    with pytest.raises(EntropyVerificationError):
        beacon.publish_commitment("NODE-3", commit_a)
    with pytest.raises(EntropyVerificationError):
        beacon.reveal_seed("NODE-UNKNOWN", "x", "y")
    with pytest.raises(EntropyVerificationError):
        beacon.reveal_seed("NODE-1", "tampered-secret", "nonce-alpha-01")

    beacon.reveal_seed("NODE-1", "ufpr-real-seed-2026", "nonce-alpha-01")
    with pytest.raises(EntropyVerificationError):
        beacon.derive_master_seed("CONS-FED-BRASIL", 1, odd_digest)

    beacon.reveal_seed("NODE-2", "ufba-real-seed-2026", "nonce-beta-02")
    master_seed, commitments, reveals = beacon.derive_master_seed("CONS-FED-BRASIL", 1, odd_digest)
    assert len(master_seed) == 64
    assert len(commitments) == 2
    assert len(reveals) == 2

    with pytest.raises(ValueError):
        CounterModeHmacDrbg("   ")
    with pytest.raises(ValueError):
        CounterModeHmacDrbg("not-valid-hex")

    drbg = CounterModeHmacDrbg(master_seed)
    with pytest.raises(ValueError):
        drbg.randbelow_unbiased(0)
    assert drbg.randbelow_unbiased(1) == 0

    near_half_space_bound = (1 << 63) + 1
    initial_counter = drbg._block_counter
    real_draws = [drbg.randbelow_unbiased(near_half_space_bound) for _ in range(24)]
    assert all(0 <= value < near_half_space_bound for value in real_draws)
    assert (drbg._block_counter - initial_counter) > 24

    fresh_drbg = CounterModeHmacDrbg(master_seed)
    with pytest.raises(ValueError):
        fresh_drbg.sample_without_replacement(["CID-0001", "CID-0002"], -1)
    with pytest.raises(ValueError):
        fresh_drbg.sample_without_replacement(["CID-0001", "CID-0002"], 3)
    sampled = fresh_drbg.sample_without_replacement(
        ["CID-0001", "CID-0002", "CID-0003", "CID-0004"], 2
    )
    assert len(sampled) == 2
    assert len(set(sampled)) == 2

    with pytest.raises(ValueError):
        allocate_proportional_hamilton_quotas({"INDUSTRY": -1, "HEALTH_EDUCATION": 5}, 2)
    with pytest.raises(ValueError):
        allocate_proportional_hamilton_quotas({"INDUSTRY": 2, "HEALTH_EDUCATION": 2}, 0)
    with pytest.raises(ValueError):
        allocate_proportional_hamilton_quotas({"INDUSTRY": 2, "HEALTH_EDUCATION": 2}, 5)

    quotas = allocate_proportional_hamilton_quotas(
        {
            "EMPTY_STRATUM": 0,
            "INDUSTRY": 80,
            "HEALTH_EDUCATION": 80,
            "LOGISTICS_SERVICES": 80,
            "SCIENCE_ENGINEERING": 80,
        },
        15,
    )
    assert quotas["EMPTY_STRATUM"] == 0
    assert sum(quotas.values()) == 15

    tied_strata = {"B_STRATUM": 10, "A_STRATUM": 10}
    default_tied = allocate_proportional_hamilton_quotas(tied_strata, 1)
    assert default_tied["A_STRATUM"] == 1
    custom_tied = allocate_proportional_hamilton_quotas(
        tied_strata, 1, tie_breaker_priority=["B_STRATUM", "A_STRATUM"]
    )
    assert custom_tied["B_STRATUM"] == 1


def test_sortition_territorial_jurisdiction_quarantine_and_sole_civilian_defence() -> None:
    with pytest.raises(ValueError):
        StratifiedSortitionEngine(cooldown_cycles=0)

    with pytest.raises(ElectoralOperationForbiddenError):
        StratifiedSortitionEngine.reject_electoral_mechanism("presidential election")

    population = _build_real_federated_population()
    assert len(population) == 320

    parana_pool = StratifiedSortitionEngine.filter_by_territorial_jurisdiction(
        population, state_id="EST-PARANA"
    )
    assert len(parana_pool) == 260
    curitiba_pool = StratifiedSortitionEngine.filter_by_territorial_jurisdiction(
        population, state_id="EST-PARANA", municipality_id="MUN-CURITIBA"
    )
    assert len(curitiba_pool) == 200
    boqueirao_pool = StratifiedSortitionEngine.filter_by_territorial_jurisdiction(
        population,
        state_id="EST-PARANA",
        municipality_id="MUN-CURITIBA",
        sector_id="CURITIBA-BOQUEIRAO",
    )
    assert len(boqueirao_pool) == 100
    assert all(c.sector_id == "CURITIBA-BOQUEIRAO" for c in boqueirao_pool)

    engine = StratifiedSortitionEngine(cooldown_cycles=1)
    with pytest.raises(ValueError):
        engine.filter_eligible_citizens([population[0], population[0]], current_cycle=1)
    with pytest.raises(ValueError):
        engine.draw_council("CONS-1", 1, boqueirao_pool, 0, _create_ready_beacon("Z0"))
    with pytest.raises(ValueError):
        engine.draw_council("CONS-1", 1, boqueirao_pool[:5], 10, _create_ready_beacon("Z1"))

    eligible_cycle_1 = engine.filter_eligible_citizens(boqueirao_pool, current_cycle=1)
    drawn_cycle_1, proof_1 = engine.draw_council(
        "CONS-SET-BOQUEIRAO", 1, boqueirao_pool, 9, _create_ready_beacon("C1")
    )
    assert len(drawn_cycle_1) == 9
    assert len(engine.active_councillor_ids) == 9
    assert engine.is_eligible(drawn_cycle_1[0].citizen_id, current_cycle=1) is False

    sparse_subset = [
        replace(boqueirao_pool[0], stratum_key="RARE_SPECIALTY"),
        boqueirao_pool[1],
        boqueirao_pool[2],
        boqueirao_pool[3],
    ]
    sparse_engine = StratifiedSortitionEngine(cooldown_cycles=1)
    _, sparse_proof = sparse_engine.draw_council(
        "CONS-SPARSE", 1, sparse_subset, 1, _create_ready_beacon("SP1")
    )
    assert StratifiedSortitionEngine.verify_audit_proof(
        [c.citizen_id for c in sparse_subset],
        sparse_proof,
        {c.citizen_id: c.stratum_key for c in sparse_subset},
    )

    eligible_ids = [c.citizen_id for c in eligible_cycle_1]
    strata_map = {c.citizen_id: c.stratum_key for c in eligible_cycle_1}
    assert StratifiedSortitionEngine.verify_audit_proof(eligible_ids, proof_1, strata_map) is True
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids + [eligible_ids[0]], proof_1, strata_map
        )
        is False
    )
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids, replace(proof_1, selected_citizen_ids=()), strata_map
        )
        is False
    )
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids, replace(proof_1, commitments=(("ONLY-ONE", "a" * 64),)), strata_map
        )
        is False
    )
    assert StratifiedSortitionEngine.verify_audit_proof(eligible_ids[1:], proof_1, strata_map) is False
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids,
            replace(proof_1, revealed_seeds=(("WRONG-SRC", "s", "n"), proof_1.revealed_seeds[1], proof_1.revealed_seeds[2])),
            strata_map,
        )
        is False
    )
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids,
            replace(
                proof_1,
                revealed_seeds=(
                    (proof_1.revealed_seeds[0][0], "forged-seed", proof_1.revealed_seeds[0][2]),
                    proof_1.revealed_seeds[1],
                    proof_1.revealed_seeds[2],
                ),
            ),
            strata_map,
        )
        is False
    )
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids, replace(proof_1, master_seed_hex="f" * 64), strata_map
        )
        is False
    )
    incomplete_strata = dict(strata_map)
    incomplete_strata.pop(eligible_ids[0])
    assert StratifiedSortitionEngine.verify_audit_proof(eligible_ids, proof_1, incomplete_strata) is False
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids, replace(proof_1, stratum_quotas=(("INDUSTRY", 9),)), strata_map
        )
        is False
    )
    assert (
        StratifiedSortitionEngine.verify_audit_proof(
            eligible_ids,
            replace(proof_1, selected_citizen_ids=tuple(reversed(proof_1.selected_citizen_ids))),
            strata_map,
        )
        is False
    )

    cycle_1_ids = [c.citizen_id for c in drawn_cycle_1]
    engine.register_mandate_completion(cycle_1_ids, completed_cycle=1)
    assert len(engine.quarantined_registry) == 9
    assert all(not engine.is_eligible(cid, current_cycle=2) for cid in cycle_1_ids)
    drawn_cycle_2, _ = engine.draw_council(
        "CONS-SET-BOQUEIRAO", 2, boqueirao_pool, 9, _create_ready_beacon("C2")
    )
    assert set(cycle_1_ids).isdisjoint({c.citizen_id for c in drawn_cycle_2})
    assert all(engine.is_eligible(cid, current_cycle=3) for cid in cycle_1_ids)

    with pytest.raises(ValueError):
        StratifiedSortitionEngine.assign_internal_roles(
            [population[0], population[0]], False, proof_1.master_seed_hex
        )
    with pytest.raises(ValueError):
        StratifiedSortitionEngine.assign_internal_roles(
            population[:5], False, proof_1.master_seed_hex
        )

    all_military = [replace(c, is_military_personnel=True) for c in population[:10]]
    with pytest.raises(CivilianSupremacyViolationError):
        StratifiedSortitionEngine.assign_internal_roles(all_military, True, proof_1.master_seed_hex)

    sole_civilian_sample = [replace(population[0], is_military_personnel=False)] + [
        replace(population[i], is_military_personnel=True) for i in range(1, 18)
    ]
    sg_sole, chambers_sole = StratifiedSortitionEngine.assign_internal_roles(
        sole_civilian_sample, True, proof_1.master_seed_hex
    )
    assert chambers_sole[MinistryPortfolio.DEFENCE] == [sole_civilian_sample[0]]
    assert sg_sole.citizen_id != sole_civilian_sample[0].citizen_id
    assert all(not m.is_military_personnel for m in chambers_sole[MinistryPortfolio.DEFENCE])


def test_councils_secretary_general_and_civilian_military_gate_invariants() -> None:
    assert_no_autocratic_title("Logistics Technician")
    with pytest.raises(AutocraticActForbiddenError):
        assert_no_autocratic_title("President of the Republic")

    population = _build_real_federated_population()
    civilians = [c for c in population if not c.is_military_personnel]
    military_member = next(c for c in population if c.is_military_personnel)

    sg_fed, fed_portfolios = StratifiedSortitionEngine.assign_internal_roles(
        civilians[:15], True, "a" * 64
    )
    federal_sg = SecretaryGeneral(sg_fed, "CONS-FED", CouncilTier.FEDERAL)
    assert federal_sg.voting_weight == 1

    with pytest.raises(AutocraticActForbiddenError):
        federal_sg.attempt_unilateral_decree("Emergency decree")
    with pytest.raises(AutocraticActForbiddenError):
        federal_sg.attempt_veto("RES-01")

    agenda = [
        AgendaItem("IT-2", "Routine", MinistryPortfolio.ECONOMY, 1, "CONS-FED", 2),
        AgendaItem("IT-1", "Urgent", MinistryPortfolio.HEALTH, 5, "CONS-FED", 1),
    ]
    ordered_agenda = federal_sg.order_meeting_agenda(agenda)
    assert ordered_agenda[0].item_id == "IT-1"

    valid_ids = frozenset(c.citizen_id for c in civilians[:15])
    with pytest.raises(ValueError):
        federal_sg.authenticate_resolution("RES-EMPTY", ordered_agenda[0], "Summary", {}, frozenset())
    outsider_sg = SecretaryGeneral(civilians[25], "CONS-FED", CouncilTier.FEDERAL)
    with pytest.raises(ValueError):
        outsider_sg.authenticate_resolution("RES-OUT", ordered_agenda[0], "Summary", {}, valid_ids)
    with pytest.raises(ValueError):
        federal_sg.authenticate_resolution(
            "RES-BAD", ordered_agenda[0], "Summary", {"OUTSIDER-99": True}, valid_ids
        )

    minority_votes = {cid: (idx < 3) for idx, cid in enumerate(sorted(valid_ids))}
    with pytest.raises(AutocraticActForbiddenError):
        federal_sg.authenticate_resolution(
            "RES-MIN", ordered_agenda[0], "Summary", minority_votes, valid_ids
        )
    majority_votes = {cid: (idx < 10) for idx, cid in enumerate(sorted(valid_ids))}
    resolution = federal_sg.authenticate_resolution(
        "RES-OK", ordered_agenda[0], "Approved", majority_votes, valid_ids
    )
    assert resolution.votes_in_favour == 10
    assert len(resolution.resolution_hash) == 64

    general_01 = GeneralOfficer("GEN-1", "Army General", "Carlos Mendes", "Southern Logistics Command")
    defence_lead = fed_portfolios[MinistryPortfolio.DEFENCE][0]

    with pytest.raises(ValueError):
        CivilianMilitaryCommandGate(defence_lead, [], federal_sg, [general_01])
    with pytest.raises(ValueError):
        CivilianMilitaryCommandGate(defence_lead, [defence_lead], federal_sg, [])
    with pytest.raises(CivilianSupremacyViolationError):
        CivilianMilitaryCommandGate(military_member, civilians[:3], federal_sg, [general_01])
    with pytest.raises(CivilianSupremacyViolationError):
        CivilianMilitaryCommandGate(sg_fed, civilians[:3], federal_sg, [general_01])
    with pytest.raises(CivilianSupremacyViolationError):
        CivilianMilitaryCommandGate(defence_lead, [military_member], federal_sg, [general_01])
    municipal_sg = SecretaryGeneral(civilians[0], "CONS-MUN", CouncilTier.MUNICIPAL)
    with pytest.raises(ValueError):
        CivilianMilitaryCommandGate(defence_lead, civilians[1:4], municipal_sg, [general_01])

    chamber_civilians = [c for c in civilians[1:4] if c.citizen_id != sg_fed.citizen_id][:3]
    gate = CivilianMilitaryCommandGate(defence_lead, chamber_civilians, federal_sg, [general_01])
    with pytest.raises(ValueError):
        gate.issue_strategic_order(
            "O-1", "Desc", "GEN-UNKNOWN", defence_lead.citizen_id, sg_fed.citizen_id, []
        )
    with pytest.raises(MilitarySubordinationViolationError):
        gate.issue_strategic_order(
            "O-1", "Desc", "GEN-1", "WRONG-MIN", sg_fed.citizen_id, []
        )
    with pytest.raises(MilitarySubordinationViolationError):
        gate.issue_strategic_order(
            "O-1", "Desc", "GEN-1", defence_lead.citizen_id, "WRONG-SG", []
        )
    with pytest.raises(MilitarySubordinationViolationError):
        gate.issue_strategic_order(
            "O-1",
            "Desc",
            "GEN-1",
            defence_lead.citizen_id,
            sg_fed.citizen_id,
            [chamber_civilians[0].citizen_id],
        )

    valid_order = gate.issue_strategic_order(
        "O-1",
        "Bridge relief",
        "GEN-1",
        defence_lead.citizen_id,
        sg_fed.citizen_id,
        [chamber_civilians[0].citizen_id, chamber_civilians[1].citizen_id],
    )
    assert len(valid_order.multisig_token) == 64

    with pytest.raises(MilitarySubordinationViolationError):
        gate.attempt_autonomous_general_mobilisation("GEN-1", "Unauthorised mobilisation")
    with pytest.raises(MilitarySubordinationViolationError):
        gate.attempt_autonomous_general_mobilisation("GEN-UNKNOWN", "Rogue attempt")

    with pytest.raises(ValueError):
        DemarchicCouncil(
            "CONS-FED",
            "Duplicate Members",
            CouncilTier.FEDERAL,
            None,
            [civilians[0], civilians[0]],
            federal_sg,
            fed_portfolios,
        )
    with pytest.raises(ValueError):
        DemarchicCouncil(
            "CONS-WRONG", "Wrong", CouncilTier.FEDERAL, None, civilians[:15], federal_sg, fed_portfolios
        )
    with pytest.raises(ValueError):
        DemarchicCouncil(
            "CONS-FED", "Fed", CouncilTier.FEDERAL, None, civilians[:15], outsider_sg, fed_portfolios
        )
    corrupted_portfolios = dict(fed_portfolios)
    corrupted_portfolios[MinistryPortfolio.ECONOMY] = [civilians[30]]
    with pytest.raises(ValueError):
        DemarchicCouncil(
            "CONS-FED", "Fed", CouncilTier.FEDERAL, None, civilians[:15], federal_sg, corrupted_portfolios
        )

    federal_council = DemarchicCouncil(
        "CONS-FED", "Fed", CouncilTier.FEDERAL, None, civilians[:15], federal_sg, fed_portfolios
    )
    mesh = EscalatedCouncilMesh()
    with pytest.raises(ValueError):
        mesh.register_council(replace(federal_council, parent_council_id="SOME-PARENT"))
    mesh.register_council(federal_council)
    with pytest.raises(ValueError):
        mesh.register_council(federal_council)

    sg_state, state_portfolios = StratifiedSortitionEngine.assign_internal_roles(
        civilians[:10], False, "b" * 64
    )
    state_sg = SecretaryGeneral(sg_state, "CONS-ST", CouncilTier.STATE)
    state_council = DemarchicCouncil(
        "CONS-ST", "State", CouncilTier.STATE, "CONS-FED", civilians[:10], state_sg, state_portfolios
    )
    with pytest.raises(ValueError):
        mesh.register_council(replace(state_council, parent_council_id=None))
    mesh.register_council(state_council)

    sg_mun, mun_portfolios = StratifiedSortitionEngine.assign_internal_roles(
        civilians[:10], False, "c" * 64
    )
    mun_sg = SecretaryGeneral(sg_mun, "CONS-MUN", CouncilTier.MUNICIPAL)
    with pytest.raises(ValueError):
        mesh.register_council(
            DemarchicCouncil(
                "CONS-MUN", "Mun", CouncilTier.MUNICIPAL, "CONS-FED", civilians[:10], mun_sg, mun_portfolios
            )
        )
    illegal_mun_portfolios = dict(mun_portfolios)
    illegal_mun_portfolios[MinistryPortfolio.DEFENCE] = [civilians[0]]
    with pytest.raises(ValueError):
        mesh.register_council(
            DemarchicCouncil(
                "CONS-MUN",
                "Mun",
                CouncilTier.MUNICIPAL,
                "CONS-ST",
                civilians[:10],
                mun_sg,
                illegal_mun_portfolios,
            )
        )
    mun_council = DemarchicCouncil(
        "CONS-MUN", "Mun", CouncilTier.MUNICIPAL, "CONS-ST", civilians[:10], mun_sg, mun_portfolios
    )
    mesh.register_council(mun_council)

    sg_sec, sec_portfolios = StratifiedSortitionEngine.assign_internal_roles(
        civilians[:9], False, "d" * 64
    )
    sec_sg = SecretaryGeneral(sg_sec, "CONS-SEC", CouncilTier.SECTORAL)
    sec_council = DemarchicCouncil(
        "CONS-SEC", "Sec", CouncilTier.SECTORAL, "CONS-MUN", civilians[:9], sec_sg, sec_portfolios
    )
    mesh.register_council(sec_council)

    with pytest.raises(ValueError):
        mesh.escalate_citizen_demand("CONS-MUN", ordered_agenda[0])
    route = mesh.escalate_citizen_demand("CONS-SEC", ordered_agenda[0])
    assert route == ["CONS-SEC", "CONS-MUN", "CONS-ST", "CONS-FED"]
    assert mesh.broadcast_compulsory_macro_directive({"directive": "EDU+5"}) == 4


def test_enterprise_conservation_finite_decimals_and_mandate_parity() -> None:
    assert SOCIALIST_ENTERPRISE_PROPERTY.state_code == 8
    SOCIALIST_ENTERPRISE_PROPERTY.assert_socialist_productive_unit()

    capitalist_mask = PropertyRightsBitmask(use=True, sell=True, buy=True, inherit=True)
    assert capitalist_mask.state_code == 15
    with pytest.raises(PropertyRegimeViolationError):
        capitalist_mask.assert_socialist_productive_unit()

    with pytest.raises(ValueError):
        validate_worker_member(WorkerMember("  ", "Helena Almeida", "Machinist", Decimal("3000"), 30))
    with pytest.raises(ValueError):
        validate_worker_member(WorkerMember("W1", "Helena Almeida", "   ", Decimal("3000"), 30))
    with pytest.raises(OrganisationalViolationError):
        validate_worker_member(WorkerMember("W1", "Helena Almeida", "Company CEO", Decimal("3000"), 30))
    with pytest.raises(OrganisationalViolationError):
        validate_worker_member(
            WorkerMember(
                "W1", "Helena Almeida", "Technician", Decimal("3000"), 30, has_unilateral_executive_power=True
            )
        )
    with pytest.raises(OrganisationalViolationError):
        validate_worker_member(
            WorkerMember(
                "W1", "Helena Almeida", "Technician", Decimal("3000"), 30, profit_share_weight=Decimal("2")
            )
        )
    with pytest.raises(OrganisationalViolationError):
        validate_worker_member(
            WorkerMember(
                "W1", "Helena Almeida", "Technician", Decimal("3000"), 30, profit_share_weight=Decimal("NaN")
            )
        )
    with pytest.raises(ValueError):
        validate_worker_member(WorkerMember("W1", "Helena Almeida", "Technician", Decimal("-1"), 30))
    with pytest.raises(ValueError):
        validate_worker_member(WorkerMember("W1", "Helena Almeida", "Technician", Decimal("Infinity"), 30))
    with pytest.raises(ValueError):
        validate_worker_member(WorkerMember("W1", "Helena Almeida", "Technician", Decimal("3000"), -1))

    with pytest.raises(ValueError):
        SocialistEnterprise("EMP-BAD", "Bad Carry", "IND", carry_over_cents=Decimal("-0.01"))
    with pytest.raises(ValueError):
        SocialistEnterprise("EMP-NAN", "NaN Carry", "IND", carry_over_cents=Decimal("NaN"))

    population = _build_real_federated_population()
    initial_worker = WorkerMember(
        population[0].citizen_id, population[0].full_name, "CNC Machinist", Decimal("3000.00"), 30
    )
    enterprise = SocialistEnterprise(
        "EMP-COOP-01",
        "Curitiba Tooling Cooperative",
        "IND-METAL",
        workers={initial_worker.worker_id: initial_worker},
    )
    for citizen in population[1:7]:
        enterprise.register_worker(
            WorkerMember(citizen.citizen_id, citizen.full_name, "CNC Machinist", Decimal("3000.00"), 30)
        )

    with pytest.raises(ValueError):
        enterprise.distribute_period_profit(
            "P0", 0, Decimal("100"), Decimal("0"), Decimal("0"), Decimal("0")
        )
    with pytest.raises(ValueError):
        enterprise.distribute_period_profit(
            "P0", 30, Decimal("-1"), Decimal("0"), Decimal("0"), Decimal("0")
        )
    with pytest.raises(ValueError):
        enterprise.distribute_period_profit(
            "P0", 30, Decimal("NaN"), Decimal("0"), Decimal("0"), Decimal("0")
        )

    enterprise.workers["CID-0001"].active_days_in_period = 35
    with pytest.raises(ValueError):
        enterprise.distribute_period_profit(
            "P0", 30, Decimal("50000"), Decimal("0"), Decimal("0"), Decimal("0")
        )
    enterprise.workers["CID-0001"].active_days_in_period = 30

    empty_enterprise = SocialistEnterprise("EMP-EMPTY", "Empty", "IND")
    with pytest.raises(ValueError):
        empty_enterprise.distribute_period_profit(
            "P0", 30, Decimal("50000"), Decimal("0"), Decimal("0"), Decimal("0")
        )

    zero_receipt = enterprise.distribute_period_profit(
        "P-ZERO", 30, Decimal("21000.00"), Decimal("5000.00"), Decimal("0.00"), Decimal("0.00")
    )
    assert zero_receipt.distributable_net_profit == Decimal("0.00")
    assert zero_receipt.corporate_retained_profit == Decimal("0.00")

    cumulative_paid_to_workers = Decimal("0.00")
    cumulative_economic_surplus = Decimal("0.00")
    for month_idx in range(1, 13):
        monthly_revenue = Decimal("21100.00") + Decimal(month_idx * 13)
        receipt = enterprise.distribute_period_profit(
            f"2026-M{month_idx:02d}",
            30,
            monthly_revenue,
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
        )
        assert receipt.corporate_retained_profit == Decimal("0.00")
        assert receipt.next_carry_over_cents < Decimal("0.07")
        cumulative_economic_surplus += monthly_revenue - receipt.base_payroll_total
        cumulative_paid_to_workers += sum(
            (amount for _, amount in receipt.payouts_by_worker), start=Decimal("0.00")
        )
    assert cumulative_paid_to_workers + enterprise.carry_over_cents == cumulative_economic_surplus

    with pytest.raises(ValueError):
        PriceIndexSeries(Decimal("0"))
    with pytest.raises(ValueError):
        PriceIndexSeries(Decimal("NaN"))
    cpi = PriceIndexSeries(Decimal("100.000000"))
    with pytest.raises(ValueError):
        cpi.apply_monthly_inflation("   ", Decimal("0.01"))
    with pytest.raises(ValueError):
        cpi.apply_monthly_inflation("M1", Decimal("-1.0"))
    with pytest.raises(ValueError):
        cpi.apply_monthly_inflation("M1", Decimal("Infinity"))
    cpi.apply_monthly_inflation("2026-01", Decimal("0.0250"))
    cpi.apply_monthly_inflation("2026-02", Decimal("0.02439024"))
    assert len(cpi.history) == 3

    manager = MandateProtectionManager({"EMP-COOP-01": enterprise})
    assert manager.validate_termination_attempt("UNKNOWN", date(2026, 6, 1)) is True

    start_d = date(2026, 1, 1)
    end_d = date(2026, 12, 31)
    with pytest.raises(MandateProtectionConfigurationError):
        manager.activate_council_mandate(
            "CID-0001", "CONS-MUN", CouncilTier.MUNICIPAL, "EMP-COOP-01", Decimal("0"), cpi.current_index, start_d, end_d
        )
    with pytest.raises(MandateProtectionConfigurationError):
        manager.activate_council_mandate(
            "CID-0001", "CONS-MUN", CouncilTier.MUNICIPAL, "EMP-COOP-01", Decimal("3000"), Decimal("0"), start_d, end_d
        )
    with pytest.raises(MandateProtectionConfigurationError):
        manager.activate_council_mandate(
            "CID-0001", "CONS-MUN", CouncilTier.MUNICIPAL, "EMP-COOP-01", Decimal("3000"), cpi.current_index, end_d, start_d
        )
    with pytest.raises(MandateProtectionConfigurationError):
        manager.activate_council_mandate(
            "CID-0001",
            "CONS-MUN",
            CouncilTier.MUNICIPAL,
            "EMP-COOP-01",
            Decimal("3000"),
            cpi.current_index,
            start_d,
            start_d + timedelta(days=800),
        )
    with pytest.raises(ValueError):
        manager.activate_council_mandate(
            "NON-WORKER",
            "CONS-MUN",
            CouncilTier.MUNICIPAL,
            "EMP-COOP-01",
            Decimal("3000"),
            cpi.current_index,
            start_d,
            end_d,
        )

    record = manager.activate_council_mandate(
        "CID-0001",
        "CONS-MUN",
        CouncilTier.MUNICIPAL,
        "EMP-COOP-01",
        Decimal("3000.00"),
        Decimal("100.000000"),
        start_d,
        end_d,
    )
    assert enterprise.workers["CID-0001"].status == EmploymentStatus.DEMARCHIC_SUSPENSION
    enterprise.workers["CID-0001"].monthly_base_pay = Decimal("0.00")

    with pytest.raises(MandateProtectionConfigurationError):
        manager.activate_council_mandate(
            "CID-0001",
            "CONS-MUN",
            CouncilTier.MUNICIPAL,
            "EMP-COOP-01",
            Decimal("3000.00"),
            Decimal("100.000000"),
            start_d,
            end_d,
        )

    with pytest.raises(ValueError):
        manager.compute_state_councillor_stipend("CID-0001", Decimal("0"))
    stipend = manager.compute_state_councillor_stipend("CID-0001", Decimal("105.000000"))
    assert stipend == Decimal("3150.00")

    with pytest.raises(MandateProtectionConfigurationError):
        manager.conclude_mandate_and_reinstate("CID-0001", date(2027, 1, 1), Decimal("105.000000"), stability_days=90)
    with pytest.raises(ValueError):
        manager.conclude_mandate_and_reinstate("CID-0001", date(2027, 1, 1), Decimal("0"))
    with pytest.raises(ValueError):
        manager.conclude_mandate_and_reinstate("CID-0001", date(2027, 1, 1), Decimal("105.000000"), period_active_days=-1)
    with pytest.raises(MandateProtectionConfigurationError):
        manager.conclude_mandate_and_reinstate("CID-0001", date(2026, 6, 1), Decimal("105.000000"))

    reinstated = manager.conclude_mandate_and_reinstate("CID-0001", date(2027, 1, 1), Decimal("105.000000"))
    assert reinstated.reinstated_monthly_base_pay == Decimal("3150.00")
    assert enterprise.workers["CID-0001"].monthly_base_pay == Decimal("3150.00")
    assert record.stability_locked_until == date(2027, 6, 30)

    with pytest.raises(RuntimeError):
        manager.compute_state_councillor_stipend("CID-0001", Decimal("105.000000"))
    with pytest.raises(RuntimeError):
        manager.conclude_mandate_and_reinstate("CID-0001", date(2027, 1, 2), Decimal("105.000000"))

    with pytest.raises(EmploymentStabilityLockError):
        manager.validate_termination_attempt("CID-0001", date(2027, 3, 1))
    assert manager.validate_termination_attempt("CID-0001", date(2027, 3, 1), proven_criminal_misconduct=True) is True
    assert manager.validate_termination_attempt("CID-0001", date(2027, 8, 1)) is True


def test_cybernetics_csr_validation_solvers_and_tie_equilibrium() -> None:
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(0, [], [], [0])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(2, [1.0], [0], [0, 1])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(1, [1.0], [0, 0], [0, 1])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(2, [0.1], [0], [1, 1, 1])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(3, [0.1, 0.2], [0, 1], [0, 2, 1, 2])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(2, [0.1], [-1], [0, 1, 1])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix(2, [float("nan")], [0], [0, 1, 1])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix.from_dense([])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix.from_dense([[0.1, 0.2]])
    with pytest.raises(ValueError):
        CompressedSparseRowMatrix.from_dense([[-0.1, 0.0], [0.0, 0.1]])

    zero_matrix = CompressedSparseRowMatrix.from_dense([[0.0, 0.0], [0.0, 0.0]])
    assert zero_matrix.non_zero_count == 0
    assert zero_matrix.estimate_spectral_radius() == 0.0

    asymmetric_matrix = CompressedSparseRowMatrix.from_dense([[0.4, 0.2], [0.1, 0.1]])
    assert asymmetric_matrix.estimate_spectral_radius(max_iterations=1, tolerance=1e-15) > 0.0

    matrix = CompressedSparseRowMatrix.from_dense([[0.10, 0.20], [0.05, 0.15]])
    with pytest.raises(ValueError):
        matrix.multiply_column_vector([1.0])
    with pytest.raises(ValueError):
        matrix.multiply_row_vector([1.0])
    assert matrix.multiply_row_vector([0.0, 1.0]) == pytest.approx([0.05, 0.15])

    non_productive = CompressedSparseRowMatrix.from_dense([[0.8, 0.5], [0.5, 0.8]])
    with pytest.raises(ValueError):
        solve_leontief_gross_output_gauss_seidel(matrix, [10.0])
    with pytest.raises(InfeasibleMacroPlanError):
        solve_leontief_gross_output_gauss_seidel(matrix, [-1.0, 10.0])
    with pytest.raises(InfeasibleMacroPlanError):
        solve_leontief_gross_output_gauss_seidel(non_productive, [10.0, 10.0])
    with pytest.raises(InfeasibleMacroPlanError):
        solve_leontief_gross_output_gauss_seidel(matrix, [100.0, 100.0], tolerance=1e-30, max_iterations=1)

    gross_output = solve_leontief_gross_output_gauss_seidel(matrix, [100.0, 50.0])
    net_check = [gross_output[i] - matrix.multiply_column_vector(gross_output)[i] for i in range(2)]
    assert net_check == pytest.approx([100.0, 50.0], rel=1e-6)

    with pytest.raises(ValueError):
        compute_embedded_labour_hours_jacobi(matrix, [0.5])
    with pytest.raises(ValueError):
        compute_embedded_labour_hours_jacobi(matrix, [-0.5, 0.5])
    with pytest.raises(InfeasibleMacroPlanError):
        compute_embedded_labour_hours_jacobi(non_productive, [0.4, 0.6])
    with pytest.raises(InfeasibleMacroPlanError):
        compute_embedded_labour_hours_jacobi(matrix, [0.5, 0.5], tolerance=1e-30, max_iterations=1)

    direct_labour = [0.4, 0.6]
    embedded_labour = compute_embedded_labour_hours_jacobi(matrix, direct_labour)
    total_embedded = sum(embedded_labour[i] * [100.0, 50.0][i] for i in range(2))
    total_direct = sum(direct_labour[i] * gross_output[i] for i in range(2))
    assert total_embedded == pytest.approx(total_direct, rel=1e-6)

    derived_y = derive_final_demand_from_labour_shares(
        matrix, direct_labour, ("EDU", "HLT"), {"EDU": 35.0, "HLT": 65.0}, 200.0
    )
    recovered_shares = compute_embedded_labour_shares_pct(
        matrix, direct_labour, derived_y, ("EDU", "HLT")
    )
    assert recovered_shares["EDU"] == pytest.approx(35.0, abs=1e-3)
    assert recovered_shares["HLT"] == pytest.approx(65.0, abs=1e-3)

    with pytest.raises(ValueError):
        compute_embedded_labour_shares_pct(matrix, direct_labour, derived_y, ("EDU",))
    with pytest.raises(ValueError):
        compute_embedded_labour_shares_pct(matrix, direct_labour, (-1.0, 10.0), ("EDU", "HLT"))
    with pytest.raises(ValueError):
        compute_embedded_labour_shares_pct(matrix, direct_labour, (0.0, 0.0), ("EDU", "HLT"))

    with pytest.raises(ValueError):
        derive_final_demand_from_labour_shares(
            matrix, direct_labour, ("EDU", "EDU"), {"EDU": 100.0}, 100.0
        )
    with pytest.raises(ValueError):
        derive_final_demand_from_labour_shares(
            matrix, direct_labour, ("EDU", "HLT"), {"EDU": 50.0, "OTHER": 50.0}, 100.0
        )
    with pytest.raises(InfeasibleMacroPlanError):
        derive_final_demand_from_labour_shares(
            matrix, direct_labour, ("EDU", "HLT"), {"EDU": 50.0, "HLT": 50.0}, 0.0
        )
    with pytest.raises(InfeasibleMacroPlanError):
        derive_final_demand_from_labour_shares(
            matrix, direct_labour, ("EDU", "HLT"), {"EDU": 120.0, "HLT": -20.0}, 100.0
        )
    with pytest.raises(InfeasibleMacroPlanError):
        derive_final_demand_from_labour_shares(
            matrix, direct_labour, ("EDU", "HLT"), {"EDU": 50.0, "HLT": 40.0}, 100.0
        )
    with pytest.raises(InfeasibleMacroPlanError):
        derive_final_demand_from_labour_shares(
            matrix, (0.0, 0.0), ("EDU", "HLT"), {"EDU": 50.0, "HLT": 50.0}, 100.0
        )

    assert evaluate_asymmetric_cockshott_harmony(-0.5) == pytest.approx(-0.25)
    assert evaluate_asymmetric_cockshott_harmony(0.25) == pytest.approx(0.5)

    with pytest.raises(ValueError):
        relax_short_run_capacity_harmony(matrix, [10.0, 10.0], [50.0])
    with pytest.raises(InfeasibleMacroPlanError):
        relax_short_run_capacity_harmony(matrix, [10.0, 10.0], [0.0, 50.0])

    intermediate_bottleneck = CompressedSparseRowMatrix.from_dense([[0.0, 0.50], [0.0, 0.10]])
    relaxed_x, _, _ = relax_short_run_capacity_harmony(
        intermediate_bottleneck,
        target_final_demand=[0.0, 100.0],
        capacity_ceiling=[200.0, 200.0],
        iterations=5,
        step_gain=0.9,
    )
    assert relaxed_x[0] >= 0.0

    zero_gross, _, _ = relax_short_run_capacity_harmony(matrix, [0.0, 0.0], [50.0, 50.0], iterations=2)
    assert zero_gross == [0.0, 0.0]

    assert_concrete_macroeconomic_topic("Allocate +5% to Public Health")
    with pytest.raises(InvalidPlebisciteTopicError):
        assert_concrete_macroeconomic_topic("Elect Senator X")

    opt_a = MacroAllocationOption("OPT-A", "Education +5%", (60.0, 40.0), {"EDU": 60.0, "HLT": 40.0})
    opt_b = MacroAllocationOption("OPT-B", "Health +5%", (40.0, 60.0), {"EDU": 40.0, "HLT": 60.0})

    with pytest.raises(ValueError):
        MacroAllocationPlebiscite(
            "P-SEC", "Budget flow?", ("EDU",), matrix, direct_labour, (200.0, 200.0), 500.0, [opt_a, opt_b]
        )
    with pytest.raises(ValueError):
        MacroAllocationPlebiscite(
            "P-CDIM", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0,), 500.0, [opt_a, opt_b]
        )
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-CNEG", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (0.0, 200.0), 500.0, [opt_a, opt_b]
        )
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-LNEG", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 0.0, [opt_a, opt_b]
        )
    with pytest.raises(ValueError):
        MacroAllocationPlebiscite(
            "P-MIN", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 500.0, [opt_a]
        )
    with pytest.raises(ValueError):
        MacroAllocationPlebiscite(
            "P-DUP", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 500.0, [opt_a, opt_a]
        )
    wrong_key_opt = MacroAllocationOption("BAD-K", "Flow", (50.0, 50.0), {"EDU": 50.0, "OTHER": 50.0})
    with pytest.raises(ValueError):
        MacroAllocationPlebiscite(
            "P-KEY",
            "Budget flow?",
            ("EDU", "HLT"),
            matrix,
            direct_labour,
            (200.0, 200.0),
            500.0,
            [opt_a, wrong_key_opt],
        )
    negative_share_opt = MacroAllocationOption("BAD-NEG", "Flow", (50.0, 50.0), {"EDU": 120.0, "HLT": -20.0})
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-NEG",
            "Budget flow?",
            ("EDU", "HLT"),
            matrix,
            direct_labour,
            (200.0, 200.0),
            500.0,
            [opt_a, negative_share_opt],
        )
    bad_sum_opt = MacroAllocationOption("BAD-SUM", "Flow", (50.0, 50.0), {"EDU": 50.0, "HLT": 40.0})
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-SUM",
            "Budget flow?",
            ("EDU", "HLT"),
            matrix,
            direct_labour,
            (200.0, 200.0),
            500.0,
            [opt_a, bad_sum_opt],
        )
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-CAP", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (30.0, 200.0), 500.0, [opt_a, opt_b]
        )
    with pytest.raises(InfeasibleMacroPlanError):
        MacroAllocationPlebiscite(
            "P-LAB", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 10.0, [opt_a, opt_b]
        )

    plebiscite = MacroAllocationPlebiscite(
        "P-01", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 500.0, [opt_a, opt_b]
    )
    with pytest.raises(RuntimeError):
        plebiscite.tally_and_seal_directive()
    with pytest.raises(ValueError):
        plebiscite.cast_anonymous_ballot("   ", "OPT-A")
    with pytest.raises(ValueError):
        plebiscite.cast_anonymous_ballot("V-1", "OPT-UNKNOWN")

    plebiscite.cast_anonymous_ballot("V-1", "OPT-A")
    plebiscite.cast_anonymous_ballot("V-1", "OPT-B")
    plebiscite.cast_anonymous_ballot("V-2", "OPT-B")
    directive = plebiscite.tally_and_seal_directive()
    assert plebiscite.tally_and_seal_directive() == directive
    assert directive.winning_option_id == "OPT-B"
    assert directive.total_valid_ballots == 2

    with pytest.raises(RuntimeError):
        plebiscite.cast_anonymous_ballot("V-3", "OPT-A")

    tied_plebiscite = MacroAllocationPlebiscite(
        "P-TIE", "Budget flow?", ("EDU", "HLT"), matrix, direct_labour, (200.0, 200.0), 500.0, [opt_a, opt_b]
    )
    tied_plebiscite.cast_anonymous_ballot("T-1", "OPT-A")
    tied_plebiscite.cast_anonymous_ballot("T-2", "OPT-B")
    tied_directive = tied_plebiscite.tally_and_seal_directive()
    assert tied_directive.winning_option_id == "TIED-EQUILIBRIUM"
    assert tied_directive.compulsory_final_demand == (50.0, 50.0)
    assert dict(tied_directive.compulsory_budget_shares_pct) == {"EDU": 50.0, "HLT": 50.0}

    with pytest.raises(ValueError):
        MacroAllocationPlebiscite.compute_cockshott_continuous_shift(-1, 0, 1)
    with pytest.raises(ValueError):
        MacroAllocationPlebiscite.compute_cockshott_continuous_shift(0, 0, 0)
    assert MacroAllocationPlebiscite.compute_cockshott_continuous_shift(60, 20, 20, 5.0) == pytest.approx(2.0)

    MacroAllocationPlebiscite.verify_council_execution_compliance(directive, {"EDU": 40.0, "HLT": 60.0})
    with pytest.raises(CompulsoryDirectiveOverrideError):
        MacroAllocationPlebiscite.verify_council_execution_compliance(directive, {"EDU": 100.0})
    with pytest.raises(CompulsoryDirectiveOverrideError):
        MacroAllocationPlebiscite.verify_council_execution_compliance(directive, {"EDU": 45.0, "HLT": 55.0})


def test_multi_cycle_real_data_system_invariants_end_to_end() -> None:
    orchestrator = SimulationOrchestrator()
    orchestrator.execute_profit_distribution(
        gross_revenue=Decimal("195000.00"),
        capital_equalisation_charge=Decimal("4500.00"),
    )
    assert orchestrator.current_capital_charge == Decimal("4500.00")

    for expected_cycle in range(1, 9):
        if expected_cycle > 1:
            summary = orchestrator.execute_next_sortition_cycle()
            assert summary.cycle_number == expected_cycle
            assert summary.overlapping_consecutive_members == 0
            assert summary.all_proofs_valid is True

        boqueirao = orchestrator.mesh.get_council("CONS-SET-BOQUEIRAO")
        matriz = orchestrator.mesh.get_council("CONS-SET-MATRIZ")
        curitiba = orchestrator.mesh.get_council("CONS-MUN-CURITIBA")
        parana = orchestrator.mesh.get_council("CONS-EST-PARANA")
        federal = orchestrator.mesh.get_council("CONS-FED-BRASIL")

        assert all(m.sector_id == "CURITIBA-BOQUEIRAO" for m in boqueirao.members)
        assert all(m.sector_id == "CURITIBA-MATRIZ" for m in matriz.members)
        assert all(m.municipality_id == "MUN-CURITIBA" for m in curitiba.members)
        assert all(m.state_id == "EST-PARANA" for m in parana.members)

        defence_chamber = federal.portfolios[MinistryPortfolio.DEFENCE]
        assert all(not m.is_military_personnel for m in defence_chamber)
        assert defence_chamber[0].citizen_id != federal.secretary_general.profile.citizen_id

    fresh_orchestrator = SimulationOrchestrator()
    block_detail = fresh_orchestrator.test_post_mandate_dismissal_lock()
    assert "CID-0001" in block_detail


def test_adversarial_multilingual_guards_partial_month_accounting_and_entrypoints() -> None:
    for autocratic_title in (
        "President",
        "Prime Minister",
        "Presidente da República",
        "Primeiro-Ministro",
        "Primer Ministro",
        "Governador",
        "Gobernador",
        "Prefeito",
        "Alcalde",
    ):
        with pytest.raises(AutocraticActForbiddenError):
            assert_no_autocratic_title(autocratic_title)

    for executive_title in (
        "Chief Financial Officer",
        "Chief Operating Officer",
        "Managing Director",
        "Diretor-Presidente",
        "Presidente Executivo",
        "Presidente Ejecutivo",
        "Majority Shareholder",
        "Acionista Majoritário",
        "Accionista Principal",
    ):
        with pytest.raises(OrganisationalViolationError):
            validate_worker_member(
                WorkerMember("W-ADV", "Helena Almeida", executive_title, Decimal("3200.00"), 30)
            )

    for electoral_topic in (
        "   ",
        "Reeleição para o conselho federal",
        "Candidato oficial ao orçamento",
        "Partidos dos trabalhadores cibernéticos",
        "Presidential recall vote",
        "Elección de diputados federales",
    ):
        with pytest.raises(InvalidPlebisciteTopicError):
            assert_concrete_macroeconomic_topic(electoral_topic)

    coop = SocialistEnterprise("EMP-PARTIAL", " Londrina Precision Cooperative", "IND-PREC")
    coop.register_worker(WorkerMember("CID-0101", "Mateus Ferreira", "Lathe Operator", Decimal("3000.00"), 10))
    coop.register_worker(WorkerMember("CID-0102", "Beatriz Nascimento", "Metrology Specialist", Decimal("3000.00"), 20))
    coop.register_worker(WorkerMember("CID-0103", "Rafael Cavalcanti", "Tooling Technician", Decimal("3000.00"), 30))

    partial_receipt = coop.distribute_period_profit(
        period_label="2026-M06",
        period_total_days=30,
        gross_revenue=Decimal("15000.00"),
        audited_material_costs=Decimal("0.00"),
        physical_depreciation_reserve=Decimal("0.00"),
        macro_social_contribution=Decimal("0.00"),
    )
    assert partial_receipt.base_payroll_total == Decimal("6000.00")
    assert partial_receipt.distributable_net_profit == Decimal("9000.00")
    assert partial_receipt.corporate_retained_profit == Decimal("0.00")
    payout_map = dict(partial_receipt.payouts_by_worker)
    assert payout_map["CID-0101"] == Decimal("1500.00")
    assert payout_map["CID-0102"] == Decimal("3000.00")
    assert payout_map["CID-0103"] == Decimal("4500.00")
    assert partial_receipt.next_carry_over_cents == Decimal("0.00")

    matrix_3 = CompressedSparseRowMatrix.from_dense(
        [
            [0.05, 0.02, 0.03],
            [0.02, 0.06, 0.02],
            [0.10, 0.12, 0.15],
        ]
    )
    labour_3 = (0.50, 0.55, 0.35)
    ceilings_3 = (300.0, 300.0, 450.0)
    opt_edu = MacroAllocationOption(
        "OPT-EDU", "Education Focus", (90.0, 60.0, 60.0), {"EDU": 45.0, "HLT": 30.0, "INF": 25.0}
    )
    opt_hlt = MacroAllocationOption(
        "OPT-HLT", "Health Focus", (60.0, 90.0, 60.0), {"EDU": 30.0, "HLT": 45.0, "INF": 25.0}
    )
    opt_inf = MacroAllocationOption(
        "OPT-INF", "Infrastructure Focus", (60.0, 60.0, 90.0), {"EDU": 30.0, "HLT": 30.0, "INF": 40.0}
    )
    three_way_plebiscite = MacroAllocationPlebiscite(
        "PLEB-3WAY",
        "Allocate annual physical surplus across Education, Health and Infrastructure?",
        ("EDU", "HLT", "INF"),
        matrix_3,
        labour_3,
        ceilings_3,
        400.0,
        [opt_edu, opt_hlt, opt_inf],
    )
    three_way_plebiscite.cast_anonymous_ballot("B-1", "OPT-EDU")
    three_way_plebiscite.cast_anonymous_ballot("B-2", "OPT-HLT")
    three_way_plebiscite.cast_anonymous_ballot("B-3", "OPT-INF")
    three_way_directive = three_way_plebiscite.tally_and_seal_directive()
    assert three_way_directive.winning_option_id == "TIED-EQUILIBRIUM"
    assert three_way_directive.compulsory_final_demand == pytest.approx((70.0, 70.0, 70.0))
    equilibrium_gross = solve_leontief_gross_output_gauss_seidel(
        matrix_3, three_way_directive.compulsory_final_demand
    )
    assert all(equilibrium_gross[idx] <= ceilings_3[idx] for idx in range(3))

    cibersoc_root = Path(__file__).resolve().parents[1]
    for cli_locale in ("en-GB", "pt", "es"):
        completed = subprocess.run(
            [sys.executable, str(cibersoc_root / "run_simulation.py"), "--locale", cli_locale],
            check=True,
            capture_output=True,
            text=True,
        )
        assert "CIBERSOC" in completed.stdout
        assert "SHA-256: True" in completed.stdout
