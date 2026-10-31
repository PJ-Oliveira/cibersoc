from __future__ import annotations

import argparse
from typing import Sequence

from .i18n.translator import LocalizationCatalog, SupportedLocale
from .ui.state import SimulationOrchestrator


def build_simulation_report(locale: SupportedLocale = SupportedLocale.ENGLISH_UK) -> str:
    translator = LocalizationCatalog(initial_locale=locale)
    orchestrator = SimulationOrchestrator()

    orchestrator.escalate_demand_from_sector(
        "CONS-SET-BOQUEIRAO",
        "24h Polyclinic Expansion and Light-Rail Corridor",
    )
    orchestrator.secretary_order_and_authenticate("CONS-FED-BRASIL")
    orchestrator.test_secretary_autocratic_block("CONS-FED-BRASIL")
    orchestrator.adjudicate_popular_jury_case("CONS-FED-BRASIL")
    orchestrator.test_monocratic_sentence_block("CONS-FED-BRASIL")
    orchestrator.dispatch_public_security_action("CONS-MUN-CURITIBA")
    orchestrator.test_warrantless_security_block("CONS-MUN-CURITIBA")
    orchestrator.issue_valid_civil_defence_order()
    orchestrator.test_military_insubordination_block()
    orchestrator.execute_next_sortition_cycle()
    orchestrator.test_ceo_appointment_block()
    orchestrator.start_tracked_worker_mandate()
    orchestrator.advance_inflation_and_compute_stipend()
    orchestrator.reinstate_tracked_worker()
    orchestrator.test_post_mandate_dismissal_lock()
    orchestrator.execute_project_integrity_audit()

    separator = "=" * 92
    lines: list[str] = [
        separator,
        translator.translate("cli.banner_title"),
        separator,
        "",
        translator.translate("cli.section_politics"),
    ]
    for council in orchestrator.mesh.list_councils():
        proof, is_valid = orchestrator.proofs_by_council[council.council_id]
        tier_label = translator.translate(f"tier.{council.tier.value}")
        council_name = translator.translate(council.name)
        status_label = translator.translate("proof.valid" if is_valid else "proof.invalid")
        lines.append(
            f"  • [{tier_label:<9}] {council_name:<36} | "
            f"{len(council.members):>2} | "
            f"{status_label} | {proof.eligible_merkle_root[:16]}..."
        )

    lines.append("")
    lines.append(translator.translate("cli.section_economy"))
    lines.append("")
    lines.append(translator.translate("cli.section_cybernetics"))
    lines.append("")
    for event in orchestrator.audit_events:
        lines.append(f"  {event.render(translator)}")
    lines.append(separator)
    return "\n".join(lines)


def run_cli_entrypoint(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cibersoc-sim")
    parser.add_argument(
        "--locale",
        choices=[loc.value for loc in SupportedLocale],
        default=SupportedLocale.ENGLISH_UK.value,
    )
    parsed = parser.parse_args(argv)
    report = build_simulation_report(SupportedLocale(parsed.locale))
    print(report)
    return 0
