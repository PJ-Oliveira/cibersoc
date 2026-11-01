from __future__ import annotations

from dataclasses import replace

from pathlib import Path
import sys
import pytest
from PySide6.QtGui import QGuiApplication

from cibersoc.councils import (
    AutocraticActForbiddenError,
    CouncilTier,
    FederatedSeatProportionality,
    PopularJuryCase,
)
from cibersoc.cybernetics import (
    apply_cockshott_plan_iteration,
    audit_in_natura_ecological_budget,
    evaluate_market_clearing_feedback,
    solve_kantorovich_plan_ray_expansion,
)
from cibersoc.sortition import MinistryPortfolio, StratifiedSortitionEngine
from cibersoc.ui.icon import (
    apply_macos_dock_icon,
    build_freedom_wings_icon,
    build_freedom_wings_pixmap,
    export_emblem_assets,
    export_fullhd_wallpaper,
    export_hd_emblem_image,
    generate_freedom_wings_svg,
    render_freedom_wings_fullhd_image,
    render_freedom_wings_image,
    resolve_fullhd_locale,
)
from cibersoc.ui.state import SimulationOrchestrator


def _federal_council():
    orchestrator = SimulationOrchestrator()
    return orchestrator, orchestrator.mesh.get_council("CONS-FED-BRASIL")


def test_popular_jury_bench_validation_and_even_chamber_trimming() -> None:
    _, council = _federal_council()
    justice = council.portfolios[MinistryPortfolio.JUSTICE]

    too_small = replace(
        council, portfolios={**council.portfolios, MinistryPortfolio.JUSTICE: justice[:2]}
    )
    with pytest.raises(ValueError):
        too_small.active_popular_jury_bench()

    even = replace(
        council, portfolios={**council.portfolios, MinistryPortfolio.JUSTICE: list(council.members[:4])}
    )
    assert len(even.active_popular_jury_bench()) == 3

    valid_case = PopularJuryCase("JURI-X", "Audit review", council.council_id)
    bench = council.active_popular_jury_bench()
    full_ballots = {juror.citizen_id: True for juror in bench}

    with pytest.raises(ValueError):
        council.adjudicate_by_popular_jury(PopularJuryCase(" ", "Audit review", council.council_id), full_ballots)
    with pytest.raises(ValueError):
        council.adjudicate_by_popular_jury(PopularJuryCase("JURI-X", " ", council.council_id), full_ballots)
    with pytest.raises(ValueError):
        council.adjudicate_by_popular_jury(PopularJuryCase("JURI-X", "Audit review", "OTHER"), full_ballots)
    with pytest.raises(ValueError):
        council.adjudicate_by_popular_jury(valid_case, {bench[0].citizen_id: True})

    verdict = council.adjudicate_by_popular_jury(valid_case, full_ballots)
    assert verdict.is_liability_upheld is True
    assert verdict.juror_count == len(bench)


def test_public_security_dispatch_guards() -> None:
    _, council = _federal_council()
    security = council.portfolios[MinistryPortfolio.PUBLIC_SECURITY]
    justice_lead = council.portfolios[MinistryPortfolio.JUSTICE][0]
    all_yes = {member.citizen_id: True for member in security}

    with pytest.raises(ValueError):
        council.dispatch_public_security_protocol(" ", "Patrol", all_yes, justice_lead.citizen_id)
    with pytest.raises(ValueError):
        council.dispatch_public_security_protocol("SEG-X", " ", all_yes, justice_lead.citizen_id)

    without_security = replace(
        council, portfolios={**council.portfolios, MinistryPortfolio.PUBLIC_SECURITY: []}
    )
    with pytest.raises(ValueError):
        without_security.dispatch_public_security_protocol(
            "SEG-X", "Patrol", all_yes, justice_lead.citizen_id
        )

    with pytest.raises(AutocraticActForbiddenError):
        council.dispatch_public_security_protocol(
            "SEG-X", "Patrol", all_yes, council.secretary_general.profile.citizen_id
        )
    with pytest.raises(ValueError):
        council.dispatch_public_security_protocol(
            "SEG-X", "Patrol", {"CID-UNKNOWN": True}, justice_lead.citizen_id
        )
    all_no = {member.citizen_id: False for member in security}
    with pytest.raises(AutocraticActForbiddenError):
        council.dispatch_public_security_protocol("SEG-X", "Patrol", all_no, justice_lead.citizen_id)

    dispatch = council.dispatch_public_security_protocol(
        "SEG-X", "Patrol", all_yes, justice_lead.citizen_id
    )
    assert dispatch.approving_security_members == len(security)


def test_internal_roles_scale_proportionally_for_large_and_minimal_councils() -> None:
    population = SimulationOrchestrator._generate_federated_population()
    civilians = [citizen for citizen in population if not citizen.is_military_personnel]

    for include_defence in (True, False):
        large = civilians[:60]
        secretary, chambers = StratifiedSortitionEngine.assign_internal_roles(
            large, include_defence, "ab" * 32
        )
        seated = sum(len(members) for members in chambers.values())
        assert seated + 1 == len(large)
        assert secretary.citizen_id not in {
            member.citizen_id for members in chambers.values() for member in members
        }

    minimal = civilians[:8]
    _, minimal_chambers = StratifiedSortitionEngine.assign_internal_roles(minimal, False, "cd" * 32)
    assert all(len(members) == 1 for members in minimal_chambers.values())

    few_civilians = civilians[:12]
    mixed = few_civilians + [citizen for citizen in population if citizen.is_military_personnel][:30]
    _, mixed_chambers = StratifiedSortitionEngine.assign_internal_roles(mixed, True, "ef" * 32)
    assert len(mixed_chambers[MinistryPortfolio.DEFENCE]) <= 12


def test_federated_seat_proportionality_and_council_metrics() -> None:
    calculated = FederatedSeatProportionality.calculate_municipal_seats([10, 10], ratio=1.0)
    assert calculated == 20
    assert FederatedSeatProportionality.validate_municipal_proportionality(20, [10, 10], 1.0) is True
    assert FederatedSeatProportionality.validate_municipal_proportionality(12, [10, 10], 1.0) is False

    with pytest.raises(ValueError):
        FederatedSeatProportionality.calculate_municipal_seats([])
    with pytest.raises(ValueError):
        FederatedSeatProportionality.calculate_municipal_seats([8, 10])
    with pytest.raises(ValueError):
        FederatedSeatProportionality.calculate_municipal_seats([10, 10], ratio=0.3)
    with pytest.raises(ValueError):
        FederatedSeatProportionality.calculate_municipal_seats([25, 25], ratio=1.0)

    sec_metric = FederatedSeatProportionality.evaluate_council_metric(
        "CONS-SET-DEMO", CouncilTier.SECTORAL, 10, [10]
    )
    assert sec_metric.is_mathematically_proportional is True
    assert sec_metric.proportionality_ratio == 1.0

    mun_metric = FederatedSeatProportionality.evaluate_council_metric(
        "CONS-MUN-DEMO", CouncilTier.MUNICIPAL, 20, [10, 10]
    )
    assert mun_metric.is_mathematically_proportional is True
    assert mun_metric.proportionality_ratio == 1.0

    state_metric = FederatedSeatProportionality.evaluate_council_metric(
        "CONS-EST-DEMO", CouncilTier.STATE, 16, [10, 10]
    )
    assert state_metric.is_mathematically_proportional is True

    fed_metric = FederatedSeatProportionality.evaluate_council_metric(
        "CONS-FED-DEMO", CouncilTier.FEDERAL, 20, [10, 10]
    )
    assert fed_metric.is_mathematically_proportional is True

    orchestrator = SimulationOrchestrator()
    for council in orchestrator.mesh.list_councils():
        metric = orchestrator.assess_council_proportionality(council.council_id)
        assert metric.is_mathematically_proportional is True
        assert metric.assigned_seats == len(council.members)

    curitiba_metric = orchestrator.assess_council_proportionality("CONS-MUN-CURITIBA")
    assert curitiba_metric.assigned_seats == 20
    assert curitiba_metric.sectoral_base_aggregate == 20
    assert curitiba_metric.proportionality_ratio == 1.0


def test_freedom_wings_icon_and_asset_export(qapp, tmp_path: Path) -> None:
    image = render_freedom_wings_image(64)
    assert image.width() == 64
    assert image.height() == 64

    pixmap = build_freedom_wings_pixmap(48)
    assert pixmap.width() == 48
    assert pixmap.height() == 48

    icon = build_freedom_wings_icon()
    assert len(icon.availableSizes()) == 8

    svg_content = generate_freedom_wings_svg()
    assert "<svg" in svg_content
    assert "</svg>" in svg_content

    png_path, svg_path = export_emblem_assets(destination_directory=tmp_path)
    assert png_path.exists()
    assert svg_path.exists()
    assert png_path.stat().st_size > 0
    assert svg_path.stat().st_size > 0

    if sys.platform == "darwin":
        assert apply_macos_dock_icon(png_path) is True
        assert apply_macos_dock_icon(platform_name="linux") is False

        invalid_text_file = tmp_path / "not_an_image.txt"
        invalid_text_file.write_text("plain text file", encoding="utf-8")
        assert apply_macos_dock_icon(invalid_text_file) is False

        assert apply_macos_dock_icon(appkit_path="/system/nonexistent/appkit.dylib") is False

        missing_asset = tmp_path / "regenerated" / "cibersoc_emblem.png"
        assert apply_macos_dock_icon(missing_asset) is True
    else:
        assert apply_macos_dock_icon(png_path) is False
        assert apply_macos_dock_icon(platform_name="linux") is False


def test_freedom_wings_fullhd_artwork_and_export(tmp_path: Path) -> None:
    fullhd_img = render_freedom_wings_fullhd_image(1920, 1080)
    assert fullhd_img.width() == 1920
    assert fullhd_img.height() == 1080

    fullhd_explicit = render_freedom_wings_fullhd_image(
        1920, 1080, application=QGuiApplication.instance()
    )
    assert fullhd_explicit.width() == 1920

    wallpaper_path = export_fullhd_wallpaper(tmp_path)
    assert wallpaper_path.exists()
    assert wallpaper_path.stat().st_size > 0

    assert resolve_fullhd_locale("pt") == "pt"
    assert resolve_fullhd_locale("en-GB") == "en-GB"
    assert resolve_fullhd_locale("es") == "es"
    assert resolve_fullhd_locale("en") == "en-GB"
    assert resolve_fullhd_locale("espanol") == "es"
    assert resolve_fullhd_locale(None) == "pt"
    assert resolve_fullhd_locale("unknown") == "pt"

    img_en = render_freedom_wings_fullhd_image(locale="en-GB")
    assert img_en.width() == 1920
    img_es = render_freedom_wings_fullhd_image(locale="es")
    assert img_es.width() == 1920

    wp_en = export_fullhd_wallpaper(tmp_path, locale="en-GB")
    assert wp_en.exists()
    assert (tmp_path / "cibersoc_freedom_wings_fullhd_en_GB.png").exists()

    wp_es = export_fullhd_wallpaper(tmp_path, locale="es")
    assert wp_es.exists()
    assert (tmp_path / "cibersoc_freedom_wings_fullhd_es.png").exists()

    hd_path = export_hd_emblem_image(tmp_path)
    assert hd_path.exists()
    assert hd_path.stat().st_size > 0

    hd_default_path = export_hd_emblem_image()
    assert hd_default_path.exists()
    assert hd_default_path.stat().st_size > 0


def test_cockshott_critique_responses_and_cybernetic_mechanisms() -> None:
    excess_metric = evaluate_market_clearing_feedback("FOOD-01", 10.0, 14.0)
    assert excess_metric.clearing_to_value_ratio == 1.4
    assert excess_metric.reallocation_signal > 0.0
    assert excess_metric.is_excess_demand is True
    assert excess_metric.is_strumilin_equilibrium is False

    deficit_metric = evaluate_market_clearing_feedback("TEXTILE-02", 20.0, 15.0)
    assert deficit_metric.clearing_to_value_ratio == 0.75
    assert deficit_metric.reallocation_signal < 0.0
    assert deficit_metric.is_excess_demand is False
    assert deficit_metric.is_strumilin_equilibrium is False

    parity_metric = evaluate_market_clearing_feedback("HEALTH-03", 50.0, 50.0)
    assert parity_metric.clearing_to_value_ratio == 1.0
    assert parity_metric.reallocation_signal == 0.0
    assert parity_metric.is_strumilin_equilibrium is True

    adjusted_plan = apply_cockshott_plan_iteration(
        current_final_demand=(100.0, 200.0, 50.0),
        feedback_metrics=(excess_metric, deficit_metric, parity_metric),
        adjustment_speed=0.5,
    )
    assert adjusted_plan[0] > 100.0
    assert adjusted_plan[1] < 200.0
    assert adjusted_plan[2] == 50.0

    with pytest.raises(ValueError, match="Mismatched dimensions"):
        apply_cockshott_plan_iteration((10.0,), (excess_metric, deficit_metric))
    with pytest.raises(ValueError, match="cannot be negative"):
        apply_cockshott_plan_iteration((-10.0,), (excess_metric,))
    with pytest.raises(ValueError, match="Adjustment speed"):
        apply_cockshott_plan_iteration((10.0,), (excess_metric,), adjustment_speed=-0.1)

    with pytest.raises(ValueError, match="strictly positive"):
        evaluate_market_clearing_feedback("ERR-01", 0.0, 10.0)
    with pytest.raises(ValueError, match="cannot be negative"):
        evaluate_market_clearing_feedback("ERR-02", 10.0, -5.0)

    ray_result = solve_kantorovich_plan_ray_expansion(
        proportional_ray=(2.0, 1.0, 3.0),
        available_capacities=(100.0, 80.0, 90.0),
        unit_input_requirements=(1.0, 2.0, 1.0),
    )
    assert ray_result.max_expansion_lambda == 30.0
    assert ray_result.binding_resource_index == 2
    assert ray_result.balanced_output == (60.0, 30.0, 90.0)

    with pytest.raises(ValueError, match="Mismatched dimensions"):
        solve_kantorovich_plan_ray_expansion((1.0,), (1.0, 2.0), (1.0,))
    with pytest.raises(ValueError, match="strictly positive"):
        solve_kantorovich_plan_ray_expansion((-1.0, 1.0), (10.0, 10.0), (1.0, 1.0))
    with pytest.raises(ValueError, match="strictly positive"):
        solve_kantorovich_plan_ray_expansion((1.0, 1.0), (10.0, 10.0), (0.0, 1.0))

    safe_budget = audit_in_natura_ecological_budget(
        annual_carbon_budget_megatons=500.0,
        sector_outputs=(100.0, 200.0),
        carbon_intensity_per_output=(1.5, 1.0),
    )
    assert safe_budget.current_physical_carbon_draw == 350.0
    assert safe_budget.remaining_ecological_space == 150.0
    assert safe_budget.is_within_planetary_boundary is True

    overshoot_budget = audit_in_natura_ecological_budget(
        annual_carbon_budget_megatons=300.0,
        sector_outputs=(100.0, 200.0),
        carbon_intensity_per_output=(1.5, 1.0),
    )
    assert overshoot_budget.current_physical_carbon_draw == 350.0
    assert overshoot_budget.remaining_ecological_space == -50.0
    assert overshoot_budget.is_within_planetary_boundary is False

    with pytest.raises(ValueError, match="Mismatched sector output"):
        audit_in_natura_ecological_budget(100.0, (1.0,), (1.0, 2.0))
    with pytest.raises(ValueError, match="strictly positive"):
        audit_in_natura_ecological_budget(0.0, (1.0,), (1.0,))

    orchestrator = SimulationOrchestrator()
    orch_clearing = orchestrator.evaluate_market_clearing("FOOD-01", 10.0, 14.0)
    assert orch_clearing.is_excess_demand is True

    orch_ray = orchestrator.solve_plan_ray(
        proportional_ray=(2.0, 1.0, 3.0),
        available_capacities=(100.0, 80.0, 90.0),
        unit_input_requirements=(1.0, 2.0, 1.0),
    )
    assert orch_ray.max_expansion_lambda == 30.0

    orch_eco = orchestrator.audit_carbon_budget(
        annual_carbon_budget_megatons=500.0,
        sector_outputs=(100.0, 200.0),
        carbon_intensity_per_output=(1.5, 1.0),
    )
    assert orch_eco.is_within_planetary_boundary is True


def test_export_fullhd_wallpaper_button_and_banner_in_main_window(qtbot, tmp_path: Path) -> None:
    from cibersoc.councils import AgendaItem, SecretaryGeneral
    from cibersoc.ui.main_window import CiberSocMainWindow
    from cibersoc.i18n.translator import LocalizationCatalog, SupportedLocale
    from PySide6.QtGui import QShowEvent

    window = CiberSocMainWindow(
        translator=LocalizationCatalog(SupportedLocale.ENGLISH_UK),
        checkpoint_data_root=tmp_path,
    )
    qtbot.addWidget(window)
    window.showEvent(QShowEvent())
    assert window.lbl_charter_emblem_art.pixmap() is not None
    assert not window.lbl_charter_emblem_art.pixmap().isNull()

    window.btn_export_fullhd_wallpaper.click()
    exported_events = [
        e for e in window.orchestrator.audit_events if e.message_key == "log.fullhd_wallpaper_exported"
    ]
    assert len(exported_events) >= 1

    window.cmb_language.setCurrentIndex(window.cmb_language.findData("pt"))
    assert window.lbl_system_title.text() == "CIBERSOC // ARQUITETURA DE GOVERNANÇA CIBERNÉTICA E DEMÁRQUICA"
    window.cmb_language.setCurrentIndex(window.cmb_language.findData("es"))
    assert window.lbl_system_title.text() == "CIBERSOC // ARQUITECTURA DE GOBERNANZA CIBERNÉTICA Y DEMÁRQUICA"
    window.cmb_language.setCurrentIndex(window.cmb_language.findData("en-GB"))
    assert window.lbl_system_title.text() == "CIBERSOC // CYBERNETIC AND DEMARCHIC GOVERNANCE ARCHITECTURE"

    window.btn_jury_adjudicate.click()
    window.btn_jury_block.click()
    window.btn_security_dispatch.click()
    window.btn_security_block.click()
    assert len(window.orchestrator.mesh.get_council(window._selected_council_id()).jury_verdicts) >= 1
    assert len(window.orchestrator.mesh.get_council(window._selected_council_id()).security_dispatches) >= 1

    window.btn_save_checkpoint.click()
    assert "ui_snapshot" in window.orchestrator.available_checkpoints(data_root=tmp_path)
    window.btn_run_audit.click()
    window.btn_save_checkpoint.click()

    window.btn_civic_round.click()
    window.btn_civic_round.click()
    assert window.orchestrator.civic_enablement_summary()["pending_enablement"] == 0

    shares = window.orchestrator.embedded_labour_shares_for_directive()
    assert sum(shares.values()) == pytest.approx(100.0)

    for ratio, cap in ((1.00, 450.0), (1.25, 450.0), (0.80, 10.0)):
        window.spn_clearing_ratio.setValue(ratio)
        window.spn_carbon_budget.setValue(cap)
        window.btn_iterate_plan.click()
    assert window.orchestrator.last_ecological_audit is not None
    assert window.orchestrator.last_ecological_audit.is_within_planetary_boundary is False

    window._toggle_fullscreen()
    window._toggle_fullscreen()
    window._step_council_selection(1)
    window._step_council_selection(-1)
    window.tabs.setCurrentIndex(0)
    window._zoom_3d_if_active(True)
    window.tabs.setCurrentIndex(5)
    window._zoom_3d_if_active(True)
    window._zoom_3d_if_active(False)

    fed = window.orchestrator.mesh.get_council("CONS-FED-BRASIL")
    even_council = replace(
        fed,
        portfolios={**fed.portfolios, MinistryPortfolio.JUSTICE: list(fed.members[:4])},
    )
    bench_default = even_council.active_popular_jury_bench()
    case_rot = PopularJuryCase("JURI-ROT-99", "Rotation audit", even_council.council_id)
    bench_case = even_council.active_popular_jury_bench(case_id=case_rot.case_id)
    assert len(bench_case) == 3
    verdict_default = even_council.adjudicate_by_popular_jury(
        case_rot, {m.citizen_id: True for m in bench_default}
    )
    assert verdict_default.is_liability_upheld is True
    case_rot_2 = PopularJuryCase("JURI-ROT-100", "Rotation audit 2", even_council.council_id)
    bench_case_2 = even_council.active_popular_jury_bench(case_id=case_rot_2.case_id)
    verdict_case = even_council.adjudicate_by_popular_jury(
        case_rot_2, {m.citizen_id: False for m in bench_case_2}
    )
    assert verdict_case.is_liability_upheld is False

    weighted_sg = SecretaryGeneral(
        profile=fed.secretary_general.profile,
        council_id=fed.council_id,
        tier=fed.tier,
    )
    weighted_sg.voting_weight = 2
    agenda = AgendaItem("AG-1", "Item", MinistryPortfolio.ECONOMY, 3, fed.council_id, 1)
    ballots = {m.citizen_id: True for m in fed.members}
    with pytest.raises(AutocraticActForbiddenError, match="voting_weight"):
        weighted_sg.authenticate_resolution("RES-ERR", agenda, "Err", ballots, fed.member_ids)

    dissent_ballots = {
        m.citizen_id: (m.citizen_id != fed.secretary_general.profile.citizen_id)
        for m in fed.members
    }
    res_dissent = fed.secretary_general.authenticate_resolution(
        "RES-OK", agenda, "SG voted against", dissent_ballots, fed.member_ids
    )
    assert res_dissent.votes_in_favour > res_dissent.votes_against




