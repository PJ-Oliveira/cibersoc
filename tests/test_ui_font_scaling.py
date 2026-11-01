from __future__ import annotations

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QRectF, QSettings, QUrl, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
)
from pytestqt.qtbot import QtBot

from cibersoc.i18n.translator import LocalizationCatalog, SupportedLocale
from cibersoc.ui.main_window import (
    FONT_SETTINGS_KEY,
    CiberSocMainWindow,
    ResponsivePushButton,
    build_reading_font,
    register_bundled_fonts,
)
from cibersoc.ui.theme import (
    DEFAULT_FONT_POINTS,
    DEFAULT_PALETTE,
    MAX_FONT_POINTS,
    MIN_FONT_POINTS,
    ConstructivistEspressoPalette,
    build_constructivist_espresso_stylesheet,
    build_dark_cappuccino_stylesheet,
    clamp_font_points,
    font_scale_factor,
    quote_font_family_list,
)


def _create_window(qtbot: QtBot, **kwargs: object) -> CiberSocMainWindow:
    window = CiberSocMainWindow(**kwargs)
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


def test_theme_never_emits_font_sizes_below_twelve_points() -> None:
    assert MIN_FONT_POINTS == 12
    espresso_palette = ConstructivistEspressoPalette()
    espresso_css = build_constructivist_espresso_stylesheet(espresso_palette, 15)
    assert espresso_palette.bg_espresso_deep in espresso_css
    for requested in (-5, 0, 8, 11, 12, 15, 32, 99):
        stylesheet = build_dark_cappuccino_stylesheet(DEFAULT_PALETTE, requested)
        sizes = [int(size) for size in re.findall(r"font-size: (\d+)pt", stylesheet)]
        assert sizes and min(sizes) >= MIN_FONT_POINTS
        assert max(sizes) <= MAX_FONT_POINTS + 3
        assert "Atkinson Hyperlegible" in stylesheet

    assert clamp_font_points(1) == MIN_FONT_POINTS
    assert clamp_font_points(500) == MAX_FONT_POINTS
    assert clamp_font_points(17.4) == 17
    assert font_scale_factor(26) == pytest.approx(2.0)
    assert quote_font_family_list(("Atkinson Hyperlegible", "Arial")) == '"Atkinson Hyperlegible", Arial'


def test_bundled_readable_font_is_registered_and_bad_files_are_ignored(
    qtbot: QtBot, tmp_path: Path
) -> None:
    assert len(register_bundled_fonts()) == 2

    (tmp_path / "broken.ttf").write_bytes(b"not a real font")
    assert register_bundled_fonts(directory=tmp_path) == ()

    assert build_reading_font(3).pointSizeF() == float(MIN_FONT_POINTS)
    assert build_reading_font(20).families()[0] == "Atkinson Hyperlegible"


def test_font_size_controls_bounds_shortcuts_and_window_scaling(qtbot: QtBot) -> None:
    window = _create_window(qtbot)
    assert window.font_points == DEFAULT_FONT_POINTS
    assert str(DEFAULT_FONT_POINTS) in window.lbl_font_size.text()

    width_before = window.width()
    assert window.increase_font_size() == DEFAULT_FONT_POINTS + 1
    QApplication.processEvents()
    assert window.mesh_canvas.font_points == DEFAULT_FONT_POINTS + 1
    assert window.width() >= width_before or window.width() == window.screen().availableGeometry().width()

    assert window.decrease_font_size() == DEFAULT_FONT_POINTS
    assert window.reset_font_size() == DEFAULT_FONT_POINTS
    assert window.set_font_points(DEFAULT_FONT_POINTS) == DEFAULT_FONT_POINTS

    assert window.set_font_points(2) == MIN_FONT_POINTS
    assert window.btn_font_decrease.isEnabled() is False
    assert window.btn_font_increase.isEnabled() is True
    assert window.decrease_font_size() == MIN_FONT_POINTS

    assert window.set_font_points(500) == MAX_FONT_POINTS
    assert window.btn_font_increase.isEnabled() is False
    assert window.btn_font_decrease.isEnabled() is True

    window.reset_font_size()
    for shortcut, expected in zip(
        window._font_shortcuts,
        (DEFAULT_FONT_POINTS + 1, DEFAULT_FONT_POINTS + 2, DEFAULT_FONT_POINTS + 1, DEFAULT_FONT_POINTS),
        strict=True,
    ):
        shortcut.activated.emit()
        assert window.font_points == expected

    window.btn_font_increase.click()
    assert window.font_points == DEFAULT_FONT_POINTS + 1
    window.btn_font_decrease.click()
    window.btn_font_reset.click()
    assert window.font_points == DEFAULT_FONT_POINTS

    window.translator.switch_locale(SupportedLocale.PORTUGUESE)
    assert "Tamanho do texto" in window.lbl_font_size.text()
    assert "Ctrl" in window.btn_font_increase.toolTip()


def test_window_does_not_resize_when_maximised(qtbot: QtBot) -> None:
    window = _create_window(qtbot)
    window.setWindowState(Qt.WindowState.WindowMaximized)
    QApplication.processEvents()
    size_max = window.size()
    window.set_font_points(DEFAULT_FONT_POINTS + 4)
    assert window.size() == size_max
    window.setWindowState(Qt.WindowState.WindowFullScreen)
    QApplication.processEvents()
    size_full = window.size()
    window.set_font_points(DEFAULT_FONT_POINTS + 6)
    assert window.size() == size_full


def test_font_size_is_persisted_between_sessions(qtbot: QtBot, tmp_path: Path) -> None:
    from cibersoc.i18n.translator import SupportedLocale
    from cibersoc.ui.main_window import LOCALE_SETTINGS_KEY

    settings_path = str(tmp_path / "cibersoc_ui.ini")
    first_settings = QSettings(settings_path, QSettings.Format.IniFormat)
    first = _create_window(qtbot, settings=first_settings)
    assert first.font_points == DEFAULT_FONT_POINTS
    first.set_font_points(22)
    first.translator.switch_locale(SupportedLocale.PORTUGUESE)
    first_settings.sync()
    assert int(first_settings.value(FONT_SETTINGS_KEY)) == 22
    assert str(first_settings.value(LOCALE_SETTINGS_KEY)) == "pt"

    second_settings = QSettings(settings_path, QSettings.Format.IniFormat)
    second = _create_window(qtbot, settings=second_settings)
    assert second.font_points == 22
    assert second.mesh_canvas.font_points == 22
    assert second.translator.active_locale == SupportedLocale.PORTUGUESE

    explicit = _create_window(qtbot, font_points=18, settings=second_settings)
    assert explicit.font_points == 18

    invalid_settings = QSettings(str(tmp_path / "cibersoc_inv.ini"), QSettings.Format.IniFormat)
    invalid_settings.setValue(LOCALE_SETTINGS_KEY, "invalid_code")
    inv_win = _create_window(qtbot, settings=invalid_settings)
    assert inv_win.translator.active_locale == SupportedLocale.ENGLISH_UK


@pytest.mark.parametrize("font_points", [MIN_FONT_POINTS, DEFAULT_FONT_POINTS, 20, 26, MAX_FONT_POINTS])
def test_every_visible_text_widget_respects_minimum_font_size(qtbot: QtBot, font_points: int) -> None:
    window = _create_window(qtbot, font_points=font_points)
    QApplication.processEvents()
    checked = 0
    for widget_type in (QLabel, QPushButton, QComboBox, QTableWidget, QPlainTextEdit):
        for widget in window.findChildren(widget_type):
            widget.ensurePolished()
            assert widget.font().pointSizeF() >= MIN_FONT_POINTS, widget.objectName() or type(widget)
            checked += 1
    assert checked > 20
    window.tabs.tabBar().ensurePolished()
    assert window.tabs.tabBar().font().pointSizeF() >= MIN_FONT_POINTS


@pytest.mark.parametrize("font_points", [MIN_FONT_POINTS, DEFAULT_FONT_POINTS, 20, 26, MAX_FONT_POINTS])
@pytest.mark.parametrize("window_size", [(680, 520), (1000, 700), (1600, 1000)])
def test_diagram_tables_and_panels_stay_responsive_at_every_font_size(
    qtbot: QtBot, font_points: int, window_size: tuple[int, int]
) -> None:
    window = _create_window(qtbot, font_points=font_points)
    window.resize(*window_size)
    window.apply_responsive_layout(*window_size)
    window.tabs.setCurrentIndex(0)
    QApplication.processEvents()

    canvas = window.mesh_canvas
    canvas.grab()
    assert canvas.width() >= canvas.minimumWidth()
    assert canvas.height() >= canvas.minimumHeight()
    bounds = QRectF(0.0, 0.0, float(canvas.width()), float(canvas.height()))
    legends = canvas.compute_legend_rectangles()
    nodes = list(canvas.compute_node_rectangles().values())
    assert not legends[0].intersects(legends[1])
    for rectangle in (*legends, *nodes):
        assert bounds.contains(rectangle)
    for node in nodes:
        assert node.height() >= canvas._minimum_box_height() - 0.01
        assert not node.intersects(legends[0]) and not node.intersects(legends[1])
    for first in range(len(nodes)):
        for second in range(first + 1, len(nodes)):
            assert not nodes[first].intersects(nodes[second])

    line_height = window._line_height
    for table in window._responsive_tables:
        assert table.minimumHeight() >= line_height * 6
        for row in range(table.rowCount()):
            assert table.rowHeight(row) >= line_height
    assert window.txt_audit_log.minimumHeight() >= line_height * 3
    assert window.txt_charter_report.minimumHeight() >= line_height * 8

    for tab_index, area in enumerate(window.tab_scroll_areas):
        window.tabs.setCurrentIndex(tab_index)
        QApplication.processEvents()
        assert area.widgetResizable()
        assert area.verticalScrollBar().maximum() >= 0
        for button in area.widget().findChildren(ResponsivePushButton):
            assert button.toolTip() != ""


def test_long_button_labels_are_elided_with_full_text_in_tooltip(qtbot: QtBot) -> None:
    button = ResponsivePushButton()
    qtbot.addWidget(button)
    button.show()
    full_text = "Execute Full Clean Code, Trilingual Documentation & Project Integrity Scan"
    button.setText(full_text)
    assert button.toolTip() == full_text
    button.resize(120, 40)
    QApplication.processEvents()
    assert button.text().endswith("\u2026")
    assert len(button.text()) < len(full_text)
    button.resize(2500, 40)
    QApplication.processEvents()
    assert button.text() == full_text
    assert button.minimumSizeHint().width() <= button.fontMetrics().horizontalAdvance("M") * 10


def test_canvas_font_growth_enlarges_minimum_size_and_keeps_size_hint(qtbot: QtBot) -> None:
    window = _create_window(qtbot, font_points=MIN_FONT_POINTS)
    canvas = window.mesh_canvas
    small_minimum = canvas.minimumSize()
    size_hint = canvas.sizeHint()
    window.set_font_points(MAX_FONT_POINTS)
    large_minimum = canvas.minimumSize()
    assert large_minimum.width() > small_minimum.width()
    assert large_minimum.height() > small_minimum.height()
    assert canvas.sizeHint() == size_hint
    assert canvas.font_points == MAX_FONT_POINTS


def test_readme_and_documentation_tab_viewer_and_navigation(qtbot: QtBot) -> None:
    from PySide6.QtCore import QUrl

    window = _create_window(qtbot)
    assert window.tabs.count() == 6
    assert "Mesh" in window.grp_mesh.title() and "&" in window.grp_jury_security.title()
    assert window.tabs.tabText(5) == "6. Nation Simulation — SEEM Engine"

    window.tabs.setCurrentIndex(5)
    QApplication.processEvents()

    readme_text = window.txt_readme_browser.toPlainText()
    assert "CIBERSOC" in readme_text
    assert "Technical Documentation" in readme_text

    window.cmb_doc_selector.setCurrentIndex(1)
    QApplication.processEvents()
    foundations_text = window.txt_readme_browser.toPlainText()
    assert "Theoretical Foundations" in foundations_text or "Decision-Theoretic" in foundations_text

    window.btn_open_readme.click()
    QApplication.processEvents()
    assert window.cmb_doc_selector.currentData() == "README.md"
    assert "CIBERSOC" in window.txt_readme_browser.toPlainText()

    window.txt_readme_browser.anchorClicked.emit(QUrl("docs/en-GB/02_UI_GUIDE.md"))
    QApplication.processEvents()
    assert window.cmb_doc_selector.currentData() == "02"
    assert "User Interface" in window.txt_readme_browser.toPlainText()

    window.txt_readme_browser.anchorClicked.emit(QUrl("docs/en-GB/03_SIMULATOR_OPERATION_MANUAL.md#cli"))
    QApplication.processEvents()
    assert window.cmb_doc_selector.currentData() == "03"
    assert "Simulator" in window.txt_readme_browser.toPlainText()

    window.txt_readme_browser.anchorClicked.emit(QUrl("https://example.com/external"))
    QApplication.processEvents()

    window._load_document_file(Path("non_existent_path.md"))
    QApplication.processEvents()
    assert "CIBERSOC" in window.txt_readme_browser.toPlainText()

    window.cmb_doc_selector.setCurrentIndex(4)
    QApplication.processEvents()
    assert "Under the Hood" in window.txt_readme_browser.toPlainText() or "Under-the-Hood" in window.txt_readme_browser.toPlainText() or "Mecânica" in window.txt_readme_browser.toPlainText()

    window.txt_readme_browser.anchorClicked.emit(QUrl("docs/pt/04_MECANICA_SUBJACENTE_UNDER_THE_HOOD.md"))
    QApplication.processEvents()
    assert "Mecânica Subjacente" in window.txt_readme_browser.toPlainText()

    window.translator.switch_locale(SupportedLocale.PORTUGUESE)
    QApplication.processEvents()
    assert window.tabs.tabText(5) == "6. Simulação Nacional — Motor SEEM"
    assert window.lbl_doc_selector.text() == "Documento:"
    assert window.btn_open_readme.text() == "Abrir README.md"

    window.cmb_doc_selector.setCurrentIndex(1)
    QApplication.processEvents()
    assert "Fundamentos Teóricos" in window.txt_readme_browser.toPlainText()

    window.translator.switch_locale(SupportedLocale.SPANISH)
    QApplication.processEvents()
    assert window.tabs.tabText(5) == "6. Simulación Nacional — Motor SEEM"
    window.cmb_doc_selector.setCurrentIndex(1)
    QApplication.processEvents()
    assert "Fundamentos Teóricos" in window.txt_readme_browser.toPlainText()


def test_shortcuts_dialog_and_tab_navigation(qtbot: QtBot) -> None:
    presented_dialogs: list[QDialog] = []

    def capture_dialog(dlg: QDialog) -> int:
        presented_dialogs.append(dlg)
        return 0

    window = _create_window(qtbot, dialog_presenter=capture_dialog)
    window._show_shortcuts_dialog()
    assert len(presented_dialogs) == 1
    assert presented_dialogs[0].windowTitle() != ""


def test_open_readme_and_export_fullhd_wallpaper(qtbot: QtBot, tmp_path: Path) -> None:
    headless_win = _create_window(qtbot)
    assert headless_win._open_file_in_desktop(tmp_path / "dummy.png") is False

    opened_urls: list[str] = []
    dialog_responses: list[tuple[str, str]] = [
        ("", ""),
        (str(tmp_path / "custom_wallpaper.png"), "PNG Images (*.png)"),
    ]

    def record_url(url: QUrl) -> bool:
        opened_urls.append(url.toString())
        return True

    def next_save_choice(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return dialog_responses.pop(0)

    desktop_win = _create_window(
        qtbot,
        url_opener=record_url,
        save_file_dialog=next_save_choice,
        headless_detector=lambda: False,
    )
    desktop_win.btn_open_readme.click()
    assert desktop_win.cmb_doc_selector.currentData() == "README.md"
    assert "CIBERSOC" in desktop_win.txt_readme_browser.toPlainText()
    assert any("README.md" in u for u in opened_urls)

    assert desktop_win._open_file_in_desktop(tmp_path / "dummy.png") is True
    assert any("dummy.png" in u for u in opened_urls)

    initial_count = len(desktop_win.orchestrator.audit_events)
    desktop_win._on_export_fullhd_wallpaper()
    assert len(desktop_win.orchestrator.audit_events) == initial_count

    custom_dest = tmp_path / "custom_wallpaper.png"
    desktop_win._on_export_fullhd_wallpaper()
    assert custom_dest.is_file()
    assert custom_dest.stat().st_size > 0
    last_event = desktop_win.orchestrator.audit_events[-1]
    assert last_event.message_key == "log.fullhd_wallpaper_exported"
    assert last_event.parameters["path"] == str(custom_dest.resolve())


