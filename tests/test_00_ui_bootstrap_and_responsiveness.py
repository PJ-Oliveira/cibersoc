from __future__ import annotations

from decimal import Decimal
import pytest
from pytestqt.qtbot import QtBot
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QBoxLayout, QHeaderView

from cibersoc.cli import build_simulation_report, run_cli_entrypoint
from cibersoc.enterprise import WorkerMember
from cibersoc.i18n.translator import LocalizationCatalog, SupportedLocale
from cibersoc.sortition import CitizenProfile, MinistryPortfolio
from cibersoc.ui.main_window import (
    CiberSocMainWindow,
    ResponsiveLayoutMode,
    compute_adaptive_window_size,
    launch_application,
    obtain_qt_application,
)
from cibersoc.ui.state import SimulationOrchestrator
from cibersoc.ui.theme import DEFAULT_PALETTE, build_dark_cappuccino_stylesheet


def test_01_real_qt_application_singleton_and_real_event_loop_launch() -> None:
    created_app = obtain_qt_application(["cibersoc-ui"])
    assert isinstance(created_app, QApplication)

    reused_app = obtain_qt_application(["cibersoc-ui"])
    assert reused_app is created_app

    exit_with_timer = launch_application(
        arguments=[],
        auto_close_ms=15,
        initial_locale=SupportedLocale.PORTUGUESE,
    )
    assert exit_with_timer == 0

    observed_titles: list[str] = []

    def inspect_and_close_live_window(live_window: CiberSocMainWindow) -> None:
        observed_titles.append(live_window.windowTitle())
        live_window.close()
        QApplication.quit()

    exit_with_callback = launch_application(
        arguments=[],
        auto_close_ms=None,
        initial_locale=SupportedLocale.SPANISH,
        on_ready=inspect_and_close_live_window,
    )
    assert exit_with_callback == 0
    assert len(observed_titles) == 1
    assert "CIBERSOC" in observed_titles[0]


def test_02_adaptive_window_sizing_and_cli_reports(capsys: pytest.CaptureFixture[str]) -> None:
    assert compute_adaptive_window_size(640, 480) == (640, 480)
    assert compute_adaptive_window_size(800, 600) == (704, 528)
    assert compute_adaptive_window_size(1366, 768) == (1202, 675)
    assert compute_adaptive_window_size(1920, 1080) == (1320, 880)
    assert compute_adaptive_window_size(3840, 2160) == (1320, 880)

    stylesheet = build_dark_cappuccino_stylesheet(DEFAULT_PALETTE)
    assert DEFAULT_PALETTE.bg_espresso_deep in stylesheet
    assert DEFAULT_PALETTE.text_ivory_primary in stylesheet
    assert DEFAULT_PALETTE.accent_crema_amber in stylesheet
    assert "QScrollArea" in stylesheet
    assert "QSplitter::handle" in stylesheet

    for locale in SupportedLocale:
        report = build_simulation_report(locale)
        assert "CIBERSOC" in report
        assert "SHA-256: True" in report

    exit_code = run_cli_entrypoint(["--locale", "pt"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CIBERSOC" in captured.out


def test_03_responsive_layout_across_all_screen_resolutions(qtbot: QtBot) -> None:
    orchestrator = SimulationOrchestrator()
    translator = LocalizationCatalog(SupportedLocale.ENGLISH_UK)
    window = CiberSocMainWindow(orchestrator=orchestrator, translator=translator)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)

    assert window.mesh_canvas.sizeHint() == QSize(520, 360)
    assert len(window.tab_scroll_areas) == 6
    assert all(area.widgetResizable() for area in window.tab_scroll_areas)

    screen_profiles: tuple[tuple[int, int, ResponsiveLayoutMode], ...] = (
        (680, 500, ResponsiveLayoutMode.COMPACT),
        (820, 680, ResponsiveLayoutMode.COMPACT),
        (1280, 720, ResponsiveLayoutMode.EXPANDED),
        (1920, 1080, ResponsiveLayoutMode.EXPANDED),
        (2560, 1440, ResponsiveLayoutMode.EXPANDED),
    )

    for target_locale in SupportedLocale:
        translator.switch_locale(target_locale)
        for viewport_width, viewport_height, expected_mode in screen_profiles:
            window.resize(viewport_width, viewport_height)
            window.apply_responsive_layout(viewport_width, viewport_height)
            QApplication.processEvents()

            assert window.current_layout_mode == expected_mode
            if expected_mode == ResponsiveLayoutMode.COMPACT:
                assert window.splitter_councils.orientation() == Qt.Orientation.Vertical
                assert window.splitter_enterprise.orientation() == Qt.Orientation.Vertical
                assert window.header_box_layout.direction() == QBoxLayout.Direction.TopToBottom
                assert (
                    window.tbl_workers.horizontalHeader().sectionResizeMode(0)
                    == QHeaderView.ResizeMode.ResizeToContents
                )
                assert window.tbl_workers.horizontalHeader().stretchLastSection() is True
            else:
                assert window.splitter_councils.orientation() == Qt.Orientation.Horizontal
                assert window.splitter_enterprise.orientation() == Qt.Orientation.Horizontal
                assert window.header_box_layout.direction() == QBoxLayout.Direction.LeftToRight
                assert (
                    window.tbl_workers.horizontalHeader().sectionResizeMode(0)
                    == QHeaderView.ResizeMode.Stretch
                )
                assert window.tbl_workers.horizontalHeader().stretchLastSection() is False

            window.tabs.setCurrentIndex(0)
            QApplication.processEvents()
            window.mesh_canvas.repaint()

            canvas_bounds = QRectF(
                0.0,
                0.0,
                float(window.mesh_canvas.width()),
                float(window.mesh_canvas.height()),
            )
            upward_legend, downward_legend = window.mesh_canvas.compute_legend_rectangles()
            assert canvas_bounds.contains(upward_legend)
            assert canvas_bounds.contains(downward_legend)
            assert not upward_legend.intersects(downward_legend)

            node_rectangles = window.mesh_canvas.compute_node_rectangles()
            rect_items = list(node_rectangles.items())
            for _, node_rect in rect_items:
                assert canvas_bounds.contains(node_rect)
                assert not node_rect.intersects(upward_legend)
                assert not node_rect.intersects(downward_legend)

            for first_idx in range(len(rect_items)):
                for second_idx in range(first_idx + 1, len(rect_items)):
                    assert not rect_items[first_idx][1].intersects(rect_items[second_idx][1])

            for tab_index in range(window.tabs.count()):
                window.tabs.setCurrentIndex(tab_index)
                QApplication.processEvents()
                assert window.tab_scroll_areas[tab_index].horizontalScrollBar().maximum() == 0

    window.resize(1280, 720)
    window.tabs.setCurrentIndex(0)
    window.splitter_councils.setSizes([310, 930])
    QApplication.processEvents()
    window.mesh_canvas.repaint()
    narrow_pane_bounds = QRectF(
        0.0, 0.0, float(window.mesh_canvas.width()), float(window.mesh_canvas.height())
    )
    narrow_upward, narrow_downward = window.mesh_canvas.compute_legend_rectangles()
    assert window.mesh_canvas.width() == window.mesh_canvas.minimumWidth()
    assert narrow_pane_bounds.contains(narrow_upward)
    assert narrow_pane_bounds.contains(narrow_downward)
    assert not narrow_upward.intersects(narrow_downward)


def test_04_end_to_end_ui_integration_and_state_synchronisation(qtbot: QtBot) -> None:
    orchestrator = SimulationOrchestrator()
    translator = LocalizationCatalog(SupportedLocale.ENGLISH_UK)
    window = CiberSocMainWindow(orchestrator=orchestrator, translator=translator)
    qtbot.addWidget(window)
    window.resize(1320, 860)
    window.show()
    qtbot.waitExposed(window)

    military_lead = CitizenProfile(
        citizen_id="CID-0020",
        full_name="Juliana Almeida",
        sector_id="CURITIBA-BOQUEIRAO",
        municipality_id="MUN-CURITIBA",
        state_id="EST-PARANA",
        stratum_key="INDUSTRY",
        is_military_personnel=True,
        prior_monthly_income=Decimal("4200.00"),
        employer_id="EMP-PUBLIC-GRID-PR",
        job_role="Technical Officer",
    )
    boqueirao_council = orchestrator.mesh.get_council("CONS-SET-BOQUEIRAO")
    if military_lead.citizen_id not in boqueirao_council.member_ids:
        boqueirao_council.members.append(military_lead)
    boqueirao_council.portfolios[MinistryPortfolio.INFRASTRUCTURE_ECOLOGY].insert(0, military_lead)

    rectangles = window.mesh_canvas.compute_node_rectangles()
    boqueirao_centre = rectangles["CONS-SET-BOQUEIRAO"].center()
    click_inside = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        boqueirao_centre,
        window.mesh_canvas.mapToGlobal(boqueirao_centre.toPoint()),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.mesh_canvas.mousePressEvent(click_inside)
    assert window.mesh_canvas.selected_council_id == "CONS-SET-BOQUEIRAO"

    bond_texts = [
        window.tbl_ministries.item(row_idx, 2).text()
        for row_idx in range(window.tbl_ministries.rowCount())
    ]
    assert translator.translate("bond.military") in bond_texts
    assert translator.translate("bond.civilian") in bond_texts

    click_outside = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(2.0, 2.0),
        window.mesh_canvas.mapToGlobal(QPointF(2.0, 2.0).toPoint()),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    window.mesh_canvas.mousePressEvent(click_outside)
    window.mesh_canvas.repaint()

    window.cmb_council.setCurrentIndex(0)
    assert window.mesh_canvas.selected_council_id == "CONS-FED-BRASIL"

    qtbot.mouseClick(window.btn_escalate_demand, Qt.MouseButton.LeftButton)
    window.mesh_canvas.repaint()
    qtbot.mouseClick(window.btn_sg_authenticate, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.btn_sg_veto_test, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.btn_defence_order, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.btn_defence_block, Qt.MouseButton.LeftButton)

    window.tabs.setCurrentIndex(1)
    qtbot.mouseClick(window.btn_next_cycle, Qt.MouseButton.LeftButton)
    assert orchestrator.current_cycle == 2
    qtbot.mouseClick(window.btn_block_election, Qt.MouseButton.LeftButton)

    tampered_proof, _ = orchestrator.proofs_by_council["CONS-SET-MATRIZ"]
    orchestrator.proofs_by_council["CONS-SET-MATRIZ"] = (tampered_proof, False)
    window.refresh_all_views()
    assert window.tbl_proofs.item(4, 4).text() == translator.translate("proof.invalid")
    orchestrator.proofs_by_council["CONS-SET-MATRIZ"] = (tampered_proof, True)
    window.refresh_all_views()

    window.tabs.setCurrentIndex(2)
    window.spn_votes_edu.setValue(750)
    window.spn_votes_health.setValue(250)
    qtbot.mouseClick(window.btn_run_plebiscite, Qt.MouseButton.LeftButton)
    assert orchestrator.last_directive is not None
    assert orchestrator.last_directive.winning_option_id == "FLOW-EDU-PLUS5"

    window.spn_votes_edu.setValue(500)
    window.spn_votes_health.setValue(500)
    qtbot.mouseClick(window.btn_run_plebiscite, Qt.MouseButton.LeftButton)
    assert orchestrator.last_directive.winning_option_id == "TIED-EQUILIBRIUM"
    assert "+0.00%" in window.lbl_cyber_metrics.text()

    qtbot.mouseClick(window.btn_block_person_pleb, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.btn_block_council_override, Qt.MouseButton.LeftButton)

    window.tabs.setCurrentIndex(3)
    orchestrator.enterprise.register_worker(
        WorkerMember(
            worker_id="CID-0009",
            full_name="Larissa Almeida",
            role_title="Field Robotics Integrator",
            monthly_base_pay=Decimal("4900.00"),
            active_days_in_period=30,
        )
    )
    window.spn_revenue.setValue(225000)
    qtbot.mouseClick(window.btn_distribute_profit, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt is not None
    assert orchestrator.last_profit_receipt.eligible_worker_count == 9

    worker_roles_rendered = {
        window.tbl_workers.item(row_idx, 1).text()
        for row_idx in range(window.tbl_workers.rowCount())
    }
    assert "CNC Precision Machinist" in worker_roles_rendered
    assert "Field Robotics Integrator" in worker_roles_rendered

    qtbot.mouseClick(window.btn_mandate_cpi, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt.eligible_worker_count == 8
    assert window.tbl_workers.item(0, 4).text() == translator.translate("enterprise.state_stipend_cell")

    qtbot.mouseClick(window.btn_mandate_start, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt.eligible_worker_count == 8

    qtbot.mouseClick(window.btn_mandate_dismiss_test, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt.eligible_worker_count == 9
    assert "CNC Precision Machinist" in window.lbl_mandate_status.text()

    qtbot.mouseClick(window.btn_mandate_start, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt.eligible_worker_count == 8
    qtbot.mouseClick(window.btn_mandate_return, Qt.MouseButton.LeftButton)
    assert orchestrator.last_profit_receipt.eligible_worker_count == 9
    qtbot.mouseClick(window.btn_mandate_dismiss_test, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.btn_block_ceo, Qt.MouseButton.LeftButton)

    window.tabs.setCurrentIndex(4)
    qtbot.mouseClick(window.btn_run_audit, Qt.MouseButton.LeftButton)
    assert orchestrator.last_scan_results is not None
    integrity_rep, clean_rep = orchestrator.last_scan_results
    assert integrity_rep.is_self_contained is True
    assert clean_rep.is_compliant is True

    pt_index = window.cmb_language.findData(SupportedLocale.PORTUGUESE.value)
    window.cmb_language.setCurrentIndex(pt_index)
    assert translator.active_locale == SupportedLocale.PORTUGUESE
    assert "CICLO DEMÁRQUICO" in window.lbl_cycle_badge.text()
    assert "Operador de Usinagem CNC de Precisão" in window.lbl_mandate_status.text()

    translator.switch_locale(SupportedLocale.SPANISH)
    assert window.cmb_language.currentData() == SupportedLocale.SPANISH.value
    assert "Operador de Mecanizado CNC de Precisión" in window.lbl_mandate_status.text()

    window.cmb_language.addItem("Placeholder", None)
    window.cmb_language.setCurrentIndex(window.cmb_language.count() - 1)
    assert translator.active_locale == SupportedLocale.SPANISH

    translator.switch_locale(SupportedLocale.ENGLISH_UK)
    assert "DEMARCHIC CYCLE" in window.lbl_cycle_badge.text()
