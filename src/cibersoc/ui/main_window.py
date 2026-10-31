from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any
import sys

from PySide6.QtCore import QSettings, QSize, QTimer, QUrl, Qt
from PySide6.QtGui import (
    QDesktopServices,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QKeySequence,
    QResizeEvent,
    QShortcut,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QBoxLayout,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..audit import build_localized_architectural_charter
from ..cybernetics import MacroAllocationPlebiscite, compute_embedded_labour_hours_jacobi
from ..i18n.translator import LocalizationCatalog, SupportedLocale
from ..sortition import MinistryPortfolio
from .icon import (
    apply_macos_dock_icon,
    build_freedom_wings_icon,
    build_freedom_wings_pixmap,
    export_fullhd_wallpaper,
)
from .markdown_renderer import render_markdown_to_html
from .mesh_canvas import CouncilMeshCanvas
from .simulation_view import SimulationTab
from .state import SimulationOrchestrator
from .theme import (
    DEFAULT_FONT_POINTS,
    FONT_STEP_POINTS,
    MAX_FONT_POINTS,
    MIN_FONT_POINTS,
    READABLE_FONT_FAMILIES,
    build_dark_cappuccino_stylesheet,
    clamp_font_points,
    font_scale_factor,
)

COMPACT_LAYOUT_BREAKPOINT: int = 960
FONT_SETTINGS_KEY: str = "ui/font_points"
LOCALE_SETTINGS_KEY: str = "ui/active_locale"
BUNDLED_FONT_DIRECTORY: Path = Path(__file__).resolve().parent / "assets" / "fonts"


class ResponsiveLayoutMode(StrEnum):
    COMPACT = "COMPACT"
    EXPANDED = "EXPANDED"


def compute_adaptive_window_size(available_width: int, available_height: int) -> tuple[int, int]:
    clamped_width = max(640, min(1320, int(available_width * 0.88)))
    clamped_height = max(480, min(880, int(available_height * 0.88)))
    return min(clamped_width, max(640, available_width)), min(
        clamped_height, max(480, available_height)
    )


def register_bundled_fonts(directory: Path | None = None) -> tuple[int, ...]:
    target_directory = directory if directory is not None else BUNDLED_FONT_DIRECTORY
    registered_identifiers: list[int] = []
    for font_file in sorted(target_directory.glob("*.ttf")):
        identifier = QFontDatabase.addApplicationFont(str(font_file))
        if identifier >= 0:
            registered_identifiers.append(identifier)
    return tuple(registered_identifiers)


def build_reading_font(points: int) -> QFont:
    font = QFont()
    font.setFamilies(list(READABLE_FONT_FAMILIES))
    font.setPointSizeF(float(clamp_font_points(points)))
    return font


class ResponsivePushButton(QPushButton):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._full_text = ""

    def setText(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._apply_elision()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._apply_elision()

    def _apply_elision(self) -> None:
        metrics = self.fontMetrics()
        available_width = max(24, self.width() - 2 * metrics.height())
        elided_text = metrics.elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, available_width
        )
        if elided_text != self.text():
            QPushButton.setText(self, elided_text)

    def minimumSizeHint(self) -> QSize:
        natural_hint = super().minimumSizeHint()
        return QSize(
            min(self.fontMetrics().horizontalAdvance("M") * 10, natural_hint.width()),
            natural_hint.height(),
        )


class ResponsiveGroupBox(QGroupBox):
    def minimumSizeHint(self) -> QSize:
        natural_hint = super().minimumSizeHint()
        return QSize(min(260, natural_hint.width()), natural_hint.height())


class CiberSocMainWindow(QMainWindow):
    def __init__(
        self,
        orchestrator: SimulationOrchestrator | None = None,
        translator: LocalizationCatalog | None = None,
        font_points: int | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__()
        register_bundled_fonts()
        self._settings = settings
        if font_points is not None:
            initial_font_points = font_points
        elif settings is not None:
            initial_font_points = int(str(settings.value(FONT_SETTINGS_KEY, DEFAULT_FONT_POINTS)))
        else:
            initial_font_points = DEFAULT_FONT_POINTS
        self._font_points: int = clamp_font_points(initial_font_points)
        self._line_height: int = 0
        self.orchestrator = orchestrator or SimulationOrchestrator()
        if translator is not None:
            active_translator = translator
        elif settings is not None:
            saved_code = str(settings.value(LOCALE_SETTINGS_KEY, ""))
            matched = next(
                (loc for loc in SupportedLocale if loc.value == saved_code),
                SupportedLocale.ENGLISH_UK,
            )
            active_translator = LocalizationCatalog(matched)
        else:
            active_translator = LocalizationCatalog(SupportedLocale.ENGLISH_UK)
        self.translator = active_translator
        self.translator.register_locale_listener(self._on_locale_changed)
        self._current_doc_path: Path = self.orchestrator.cibersoc_root / "README.md"

        self.setMinimumSize(640, 480)
        available_geometry = QApplication.primaryScreen().availableGeometry()
        initial_width, initial_height = compute_adaptive_window_size(
            available_geometry.width(), available_geometry.height()
        )
        self.resize(initial_width, initial_height)
        self.setStyleSheet(build_dark_cappuccino_stylesheet(base_points=self._font_points))
        self.setWindowIcon(build_freedom_wings_icon())

        self._adaptive_box_layouts: list[QBoxLayout] = []
        self.tab_scroll_areas: list[QScrollArea] = []
        self.current_layout_mode: ResponsiveLayoutMode | None = None

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(6)

        header_frame = QFrame()
        header_frame.setObjectName("HeaderBanner")
        self.header_box_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, header_frame)
        self.header_box_layout.setSpacing(10)
        self._adaptive_box_layouts.append(self.header_box_layout)

        self.lbl_header_emblem = QLabel()
        self.lbl_header_emblem.setObjectName("HeaderEmblem")
        self.lbl_header_emblem.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        emblem_pixels = max(36, int(round(48.0 * font_scale_factor(self._font_points))))
        self.lbl_header_emblem.setPixmap(build_freedom_wings_pixmap(emblem_pixels))
        self.header_box_layout.addWidget(self.lbl_header_emblem)

        title_column = QVBoxLayout()
        self.lbl_system_title = QLabel()
        self.lbl_system_title.setObjectName("SystemTitle")
        self.lbl_system_title.setWordWrap(True)
        self.lbl_system_subtitle = QLabel()
        self.lbl_system_subtitle.setObjectName("SystemSubtitle")
        self.lbl_system_subtitle.setWordWrap(True)
        title_column.addWidget(self.lbl_system_title)
        title_column.addWidget(self.lbl_system_subtitle)
        self.header_box_layout.addLayout(title_column, stretch=1)

        controls_column = QVBoxLayout()
        language_row = QHBoxLayout()
        self.lbl_language_prompt = QLabel()
        language_row.addWidget(self.lbl_language_prompt)

        self.cmb_language = QComboBox()
        self.cmb_language.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.cmb_language.setMinimumContentsLength(12)
        for supported_locale in SupportedLocale:
            self.cmb_language.addItem(
                self.translator.translate(f"locale.{supported_locale.value}"),
                supported_locale.value,
            )
        active_index = self.cmb_language.findData(self.translator.active_locale.value)
        self.cmb_language.setCurrentIndex(active_index)
        self.cmb_language.currentIndexChanged.connect(self._on_language_selector_changed)
        language_row.addWidget(self.cmb_language)

        self.lbl_cycle_badge = QLabel()
        self.lbl_cycle_badge.setObjectName("SectionHeading")
        language_row.addWidget(self.lbl_cycle_badge)
        language_row.addStretch(0)
        controls_column.addLayout(language_row)

        font_row = QHBoxLayout()
        self.lbl_font_size = QLabel()
        font_row.addWidget(self.lbl_font_size)
        self.btn_font_decrease = QPushButton("A\u2212")
        self.btn_font_increase = QPushButton("A+")
        self.btn_font_reset = QPushButton("Aa")
        for font_button in (self.btn_font_decrease, self.btn_font_increase, self.btn_font_reset):
            font_button.setObjectName("FontStepButton")
            font_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            font_row.addWidget(font_button)
        font_row.addStretch(0)
        controls_column.addLayout(font_row)
        self.btn_font_decrease.clicked.connect(self.decrease_font_size)
        self.btn_font_increase.clicked.connect(self.increase_font_size)
        self.btn_font_reset.clicked.connect(self.reset_font_size)
        self._font_shortcuts: tuple[QShortcut, ...] = (
            self._bind_shortcut(QKeySequence.StandardKey.ZoomIn, self.increase_font_size),
            self._bind_shortcut(QKeySequence("Ctrl+="), self.increase_font_size),
            self._bind_shortcut(QKeySequence.StandardKey.ZoomOut, self.decrease_font_size),
            self._bind_shortcut(QKeySequence("Ctrl+0"), self.reset_font_size),
        )
        self._navigation_shortcuts: tuple[QShortcut, ...] = (
            self._bind_shortcut(Qt.Key.Key_F1, self._show_shortcuts_dialog),
            self._bind_shortcut(QKeySequence("?"), self._show_shortcuts_dialog),
            self._bind_shortcut(QKeySequence("Ctrl+1"), lambda: self.tabs.setCurrentIndex(0)),
            self._bind_shortcut(QKeySequence("Ctrl+2"), lambda: self.tabs.setCurrentIndex(1)),
            self._bind_shortcut(QKeySequence("Ctrl+3"), lambda: self.tabs.setCurrentIndex(2)),
            self._bind_shortcut(QKeySequence("Ctrl+4"), lambda: self.tabs.setCurrentIndex(3)),
            self._bind_shortcut(QKeySequence("Ctrl+5"), lambda: self.tabs.setCurrentIndex(4)),
            self._bind_shortcut(QKeySequence("Ctrl+6"), lambda: self.tabs.setCurrentIndex(5)),
        )
        self.header_box_layout.addLayout(controls_column)
        root_layout.addWidget(header_frame)

        self.main_vertical_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_vertical_splitter.setChildrenCollapsible(False)
        root_layout.addWidget(self.main_vertical_splitter, stretch=1)

        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)
        self.tabs.tabBar().setExpanding(False)
        self.main_vertical_splitter.addWidget(self.tabs)

        self._build_councils_workspace()
        self._build_sortition_workspace()
        self._build_cybernetics_workspace()
        self._build_enterprise_workspace()
        self._build_charter_and_docs_workspace()
        self._build_simulation_workspace()

        self._responsive_tables: tuple[QTableWidget, ...] = (
            self.tbl_ministries,
            self.tbl_proofs,
            self.tbl_cyber,
            self.tbl_workers,
        )
        for table in self._responsive_tables:
            table.setWordWrap(True)
            table.setAlternatingRowColors(True)
            table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.grp_audit_console = ResponsiveGroupBox()
        console_layout = QVBoxLayout(self.grp_audit_console)
        self.txt_audit_log = QPlainTextEdit()
        self.txt_audit_log.setReadOnly(True)
        console_layout.addWidget(self.txt_audit_log)
        self.main_vertical_splitter.addWidget(self.grp_audit_console)
        self.main_vertical_splitter.setStretchFactor(0, 4)
        self.main_vertical_splitter.setStretchFactor(1, 1)

        self._apply_font_to_widgets()
        self.retranslate_static_labels()
        self.refresh_all_views()
        self.apply_responsive_layout(self.width(), self.height())

    def _bind_shortcut(
        self,
        key_sequence: QKeySequence | QKeySequence.StandardKey | Qt.Key | str,
        handler: Callable[[], Any],
    ) -> QShortcut:
        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(handler)
        return shortcut

    def _show_shortcuts_dialog(self) -> None:
        t = self.translator.translate
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dialog.shortcuts_title"))
        dialog.setMinimumWidth(440)
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(16, 16, 16, 16)
        dialog_layout.setSpacing(10)

        intro = QLabel(t("dialog.shortcuts_intro"))
        intro.setObjectName("SectionHeading")
        dialog_layout.addWidget(intro)

        table = QTableWidget(5, 2, dialog)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        shortcuts = [
            ("F1 / ?", t("shortcuts.f1")),
            ("Ctrl+1..6", t("shortcuts.tab_switch")),
            ("F11", t("shortcuts.fullscreen")),
            ("+ / -", t("shortcuts.zoom")),
            ("Alt+Up / Alt+Down", t("shortcuts.inspect")),
        ]
        for row, (key, desc) in enumerate(shortcuts):
            k_item = QTableWidgetItem(key)
            k_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            d_item = QTableWidgetItem(desc)
            table.setItem(row, 0, k_item)
            table.setItem(row, 1, d_item)

        dialog_layout.addWidget(table)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton(t("dialog.shortcuts_close"))
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_close)
        dialog_layout.addLayout(btn_row)

        dialog.exec()

    @property
    def font_points(self) -> int:
        return self._font_points

    def increase_font_size(self) -> int:
        return self.set_font_points(self._font_points + FONT_STEP_POINTS)

    def decrease_font_size(self) -> int:
        return self.set_font_points(self._font_points - FONT_STEP_POINTS)

    def reset_font_size(self) -> int:
        return self.set_font_points(DEFAULT_FONT_POINTS)

    def set_font_points(self, points: int) -> int:
        target_points = clamp_font_points(points)
        previous_points = self._font_points
        if target_points == previous_points:
            return target_points
        self._font_points = target_points
        self.setStyleSheet(build_dark_cappuccino_stylesheet(base_points=target_points))
        self._apply_font_to_widgets()
        self._scale_window_to_font(previous_points, target_points)
        self.refresh_all_views()
        self.apply_responsive_layout(self.width(), self.height())
        if self._settings is not None:
            self._settings.setValue(FONT_SETTINGS_KEY, target_points)
        return target_points

    def _scale_window_to_font(self, previous_points: int, target_points: int) -> None:
        if self.isMaximized() or self.isFullScreen():
            return
        available_geometry = self.screen().availableGeometry()
        ratio = target_points / previous_points
        scaled_width = min(
            available_geometry.width(), max(self.minimumWidth(), int(self.width() * ratio))
        )
        scaled_height = min(
            available_geometry.height(), max(self.minimumHeight(), int(self.height() * ratio))
        )
        self.resize(scaled_width, scaled_height)

    def _apply_font_to_widgets(self) -> None:
        reading_font = build_reading_font(self._font_points)
        metrics = QFontMetrics(reading_font)
        line_height = metrics.lineSpacing()
        self._line_height = line_height
        self.mesh_canvas.set_font_points(self._font_points)
        emblem_pixels = max(36, int(round(48.0 * font_scale_factor(self._font_points))))
        self.lbl_header_emblem.setPixmap(build_freedom_wings_pixmap(emblem_pixels))
        emblem_art_size = max(72, int(round(120.0 * font_scale_factor(self._font_points))))
        self.lbl_charter_emblem_art.setPixmap(build_freedom_wings_pixmap(emblem_art_size))
        minimum_section_width = metrics.horizontalAdvance("M") * 9
        for table in self._responsive_tables:
            table.setMinimumHeight(line_height * 6 + 16)
            table.horizontalHeader().setMinimumSectionSize(minimum_section_width)
        self.txt_audit_log.setMinimumHeight(line_height * 3 + 16)
        self.txt_charter_report.setMinimumHeight(line_height * 8 + 16)
        self.txt_readme_browser.setMinimumHeight(line_height * 10 + 16)
        self.btn_font_decrease.setEnabled(self._font_points > MIN_FONT_POINTS)
        self.btn_font_increase.setEnabled(self._font_points < MAX_FONT_POINTS)
        self.lbl_font_size.setText(
            self.translator.translate("header.font_label", points=self._font_points)
        )
        self._load_document_file(self._current_doc_path)

    def _add_scrollable_tab(self, workspace: QWidget) -> None:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidget(workspace)
        self.tab_scroll_areas.append(scroll_area)
        self.tabs.addTab(scroll_area, "")

    def _build_councils_workspace(self) -> None:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(6, 6, 6, 6)

        self.splitter_councils = QSplitter(Qt.Orientation.Horizontal)
        self.splitter_councils.setChildrenCollapsible(False)

        self.grp_mesh = ResponsiveGroupBox()
        left_layout = QVBoxLayout(self.grp_mesh)

        selector_row = QHBoxLayout()
        self.lbl_inspect_tier = QLabel()
        selector_row.addWidget(self.lbl_inspect_tier)
        self.cmb_council = QComboBox()
        self.cmb_council.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.cmb_council.setMinimumContentsLength(14)
        for council in self.orchestrator.mesh.list_councils():
            self.cmb_council.addItem(council.council_id, council.council_id)
        self.cmb_council.currentIndexChanged.connect(self._on_combo_council_changed)
        selector_row.addWidget(self.cmb_council, stretch=1)
        left_layout.addLayout(selector_row)

        self.mesh_canvas = CouncilMeshCanvas(self.orchestrator.mesh, self.translator)
        self.mesh_canvas.council_selected.connect(self._on_canvas_council_selected)
        left_layout.addWidget(self.mesh_canvas, stretch=1)

        self.btn_escalate_demand = ResponsivePushButton()
        self.btn_escalate_demand.clicked.connect(self._on_escalate_demand)
        left_layout.addWidget(self.btn_escalate_demand)
        self.splitter_councils.addWidget(self.grp_mesh)

        right_panel = QWidget()
        right_column = QVBoxLayout(right_panel)
        right_column.setContentsMargins(0, 0, 0, 0)

        self.grp_secretary = ResponsiveGroupBox()
        sg_layout = QVBoxLayout(self.grp_secretary)
        self.lbl_secretary_info = QLabel()
        self.lbl_secretary_info.setWordWrap(True)
        sg_layout.addWidget(self.lbl_secretary_info)
        self.lbl_council_proportionality = QLabel()
        self.lbl_council_proportionality.setWordWrap(True)
        self.lbl_council_proportionality.setObjectName("SubtleMetadata")
        sg_layout.addWidget(self.lbl_council_proportionality)

        self.sg_button_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.sg_button_layout)
        self.btn_sg_authenticate = ResponsivePushButton()
        self.btn_sg_authenticate.clicked.connect(self._on_sg_authenticate)
        self.btn_sg_veto_test = ResponsivePushButton()
        self.btn_sg_veto_test.setObjectName("AlertActionButton")
        self.btn_sg_veto_test.clicked.connect(self._on_sg_veto_test)
        self.sg_button_layout.addWidget(self.btn_sg_authenticate)
        self.sg_button_layout.addWidget(self.btn_sg_veto_test)
        sg_layout.addLayout(self.sg_button_layout)
        right_column.addWidget(self.grp_secretary)

        self.grp_ministries = ResponsiveGroupBox()
        ministries_layout = QVBoxLayout(self.grp_ministries)
        self.tbl_ministries = QTableWidget(0, 4)
        ministries_layout.addWidget(self.tbl_ministries)
        right_column.addWidget(self.grp_ministries, stretch=1)

        self.grp_defence = ResponsiveGroupBox()
        defence_layout = QVBoxLayout(self.grp_defence)
        self.lbl_defence_status = QLabel()
        self.lbl_defence_status.setWordWrap(True)
        defence_layout.addWidget(self.lbl_defence_status)
        self.defence_button_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.defence_button_layout)
        self.btn_defence_order = ResponsivePushButton()
        self.btn_defence_order.clicked.connect(self._on_defence_valid_order)
        self.btn_defence_block = ResponsivePushButton()
        self.btn_defence_block.setObjectName("AlertActionButton")
        self.btn_defence_block.clicked.connect(self._on_defence_insubordination_test)
        self.defence_button_layout.addWidget(self.btn_defence_order)
        self.defence_button_layout.addWidget(self.btn_defence_block)
        defence_layout.addLayout(self.defence_button_layout)
        right_column.addWidget(self.grp_defence)

        self.splitter_councils.addWidget(right_panel)
        self.splitter_councils.setStretchFactor(0, 5)
        self.splitter_councils.setStretchFactor(1, 6)
        layout.addWidget(self.splitter_councils, stretch=1)
        self._add_scrollable_tab(workspace)

    def _build_sortition_workspace(self) -> None:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(6, 6, 6, 6)

        self.grp_sortition_controls = ResponsiveGroupBox()
        controls_layout = QVBoxLayout(self.grp_sortition_controls)
        self.lbl_sortition_summary = QLabel()
        self.lbl_sortition_summary.setWordWrap(True)
        controls_layout.addWidget(self.lbl_sortition_summary)

        self.sortition_button_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.sortition_button_layout)
        self.btn_next_cycle = ResponsivePushButton()
        self.btn_next_cycle.clicked.connect(self._on_next_sortition_cycle)
        self.btn_block_election = ResponsivePushButton()
        self.btn_block_election.setObjectName("AlertActionButton")
        self.btn_block_election.clicked.connect(self._on_block_election)
        self.sortition_button_layout.addWidget(self.btn_next_cycle)
        self.sortition_button_layout.addWidget(self.btn_block_election)
        controls_layout.addLayout(self.sortition_button_layout)
        layout.addWidget(self.grp_sortition_controls)

        self.grp_sortition_proofs = ResponsiveGroupBox()
        proofs_layout = QVBoxLayout(self.grp_sortition_proofs)
        self.tbl_proofs = QTableWidget(0, 5)
        proofs_layout.addWidget(self.tbl_proofs)
        layout.addWidget(self.grp_sortition_proofs, stretch=1)

        self._add_scrollable_tab(workspace)

    def _build_cybernetics_workspace(self) -> None:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(6, 6, 6, 6)

        self.grp_plebiscite = ResponsiveGroupBox()
        plebiscite_layout = QVBoxLayout(self.grp_plebiscite)
        self.lbl_plebiscite_prompt = QLabel()
        self.lbl_plebiscite_prompt.setObjectName("SectionHeading")
        self.lbl_plebiscite_prompt.setWordWrap(True)
        plebiscite_layout.addWidget(self.lbl_plebiscite_prompt)

        self.plebiscite_ballot_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.plebiscite_ballot_layout)
        self.lbl_votes_edu = QLabel()
        self.plebiscite_ballot_layout.addWidget(self.lbl_votes_edu)
        self.spn_votes_edu = QSpinBox()
        self.spn_votes_edu.setRange(1, 50000)
        self.spn_votes_edu.setValue(432)
        self.plebiscite_ballot_layout.addWidget(self.spn_votes_edu)

        self.lbl_votes_health = QLabel()
        self.plebiscite_ballot_layout.addWidget(self.lbl_votes_health)
        self.spn_votes_health = QSpinBox()
        self.spn_votes_health.setRange(1, 50000)
        self.spn_votes_health.setValue(568)
        self.plebiscite_ballot_layout.addWidget(self.spn_votes_health)

        self.btn_run_plebiscite = ResponsivePushButton()
        self.btn_run_plebiscite.clicked.connect(self._on_run_plebiscite)
        self.plebiscite_ballot_layout.addWidget(self.btn_run_plebiscite)
        plebiscite_layout.addLayout(self.plebiscite_ballot_layout)

        self.plebiscite_guard_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.plebiscite_guard_layout)
        self.btn_block_person_pleb = ResponsivePushButton()
        self.btn_block_person_pleb.setObjectName("AlertActionButton")
        self.btn_block_person_pleb.clicked.connect(self._on_block_person_plebiscite)
        self.btn_block_council_override = ResponsivePushButton()
        self.btn_block_council_override.setObjectName("AlertActionButton")
        self.btn_block_council_override.clicked.connect(self._on_block_council_override)
        self.plebiscite_guard_layout.addWidget(self.btn_block_person_pleb)
        self.plebiscite_guard_layout.addWidget(self.btn_block_council_override)
        plebiscite_layout.addLayout(self.plebiscite_guard_layout)

        self.lbl_cyber_metrics = QLabel()
        self.lbl_cyber_metrics.setWordWrap(True)
        plebiscite_layout.addWidget(self.lbl_cyber_metrics)
        layout.addWidget(self.grp_plebiscite)

        self.grp_cyber_matrix = ResponsiveGroupBox()
        matrix_layout = QVBoxLayout(self.grp_cyber_matrix)
        self.tbl_cyber = QTableWidget(0, 6)
        matrix_layout.addWidget(self.tbl_cyber)
        layout.addWidget(self.grp_cyber_matrix, stretch=1)

        self._add_scrollable_tab(workspace)

    def _build_enterprise_workspace(self) -> None:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(6, 6, 6, 6)

        self.splitter_enterprise = QSplitter(Qt.Orientation.Horizontal)
        self.splitter_enterprise.setChildrenCollapsible(False)

        self.grp_enterprise_ledger = ResponsiveGroupBox()
        enterprise_layout = QVBoxLayout(self.grp_enterprise_ledger)

        self.revenue_controls_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._adaptive_box_layouts.append(self.revenue_controls_layout)
        self.lbl_revenue_prompt = QLabel()
        self.revenue_controls_layout.addWidget(self.lbl_revenue_prompt)
        self.spn_revenue = QSpinBox()
        self.spn_revenue.setRange(120000, 500000)
        self.spn_revenue.setSingleStep(5000)
        self.spn_revenue.setValue(185000)
        self.revenue_controls_layout.addWidget(self.spn_revenue)
        self.btn_distribute_profit = ResponsivePushButton()
        self.btn_distribute_profit.clicked.connect(self._on_distribute_profit)
        self.revenue_controls_layout.addWidget(self.btn_distribute_profit)
        enterprise_layout.addLayout(self.revenue_controls_layout)

        self.lbl_enterprise_summary = QLabel()
        self.lbl_enterprise_summary.setWordWrap(True)
        enterprise_layout.addWidget(self.lbl_enterprise_summary)

        self.tbl_workers = QTableWidget(0, 5)
        enterprise_layout.addWidget(self.tbl_workers, stretch=1)

        self.btn_block_ceo = ResponsivePushButton()
        self.btn_block_ceo.setObjectName("AlertActionButton")
        self.btn_block_ceo.clicked.connect(self._on_block_ceo)
        enterprise_layout.addWidget(self.btn_block_ceo)
        self.splitter_enterprise.addWidget(self.grp_enterprise_ledger)

        self.grp_mandate_lifecycle = ResponsiveGroupBox()
        mandate_layout = QVBoxLayout(self.grp_mandate_lifecycle)
        self.lbl_mandate_status = QLabel()
        self.lbl_mandate_status.setWordWrap(True)
        mandate_layout.addWidget(self.lbl_mandate_status)

        self.btn_mandate_start = ResponsivePushButton()
        self.btn_mandate_start.clicked.connect(self._on_mandate_start)
        self.btn_mandate_cpi = ResponsivePushButton()
        self.btn_mandate_cpi.clicked.connect(self._on_mandate_cpi)
        self.btn_mandate_return = ResponsivePushButton()
        self.btn_mandate_return.clicked.connect(self._on_mandate_return)
        self.btn_mandate_dismiss_test = ResponsivePushButton()
        self.btn_mandate_dismiss_test.setObjectName("AlertActionButton")
        self.btn_mandate_dismiss_test.clicked.connect(self._on_mandate_dismiss_test)

        mandate_layout.addWidget(self.btn_mandate_start)
        mandate_layout.addWidget(self.btn_mandate_cpi)
        mandate_layout.addWidget(self.btn_mandate_return)
        mandate_layout.addWidget(self.btn_mandate_dismiss_test)
        mandate_layout.addStretch(1)
        self.splitter_enterprise.addWidget(self.grp_mandate_lifecycle)
        self.splitter_enterprise.setStretchFactor(0, 6)
        self.splitter_enterprise.setStretchFactor(1, 5)

        layout.addWidget(self.splitter_enterprise, stretch=1)
        self._add_scrollable_tab(workspace)

    def _build_charter_and_docs_workspace(self) -> None:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(6, 6, 6, 6)

        self.grp_charter = ResponsiveGroupBox()
        box_layout = QVBoxLayout(self.grp_charter)

        self.lbl_charter_emblem_art = QLabel()
        self.lbl_charter_emblem_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(self.lbl_charter_emblem_art)

        actions_row = QHBoxLayout()
        self.btn_run_audit = ResponsivePushButton()
        self.btn_run_audit.clicked.connect(self._on_run_integrity_audit)
        actions_row.addWidget(self.btn_run_audit, stretch=1)

        self.btn_export_fullhd_wallpaper = ResponsivePushButton()
        self.btn_export_fullhd_wallpaper.clicked.connect(self._on_export_fullhd_wallpaper)
        actions_row.addWidget(self.btn_export_fullhd_wallpaper, stretch=1)
        box_layout.addLayout(actions_row)

        self.txt_charter_report = QPlainTextEdit()
        self.txt_charter_report.setReadOnly(True)
        box_layout.addWidget(self.txt_charter_report, stretch=1)

        layout.addWidget(self.grp_charter)

        self.grp_readme = ResponsiveGroupBox()
        readme_layout = QVBoxLayout(self.grp_readme)

        controls_row = QHBoxLayout()
        self.lbl_doc_selector = QLabel()
        controls_row.addWidget(self.lbl_doc_selector)

        self.cmb_doc_selector = QComboBox()
        self.cmb_doc_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.cmb_doc_selector.setMinimumContentsLength(20)
        self.cmb_doc_selector.currentIndexChanged.connect(self._on_doc_selector_changed)
        controls_row.addWidget(self.cmb_doc_selector, stretch=1)

        self.btn_open_readme = QPushButton()
        self.btn_open_readme.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.btn_open_readme.clicked.connect(self._on_open_readme_clicked)
        controls_row.addWidget(self.btn_open_readme)
        readme_layout.addLayout(controls_row)

        self.txt_readme_browser = QTextBrowser()
        self.txt_readme_browser.setOpenLinks(False)
        self.txt_readme_browser.setOpenExternalLinks(False)
        self.txt_readme_browser.anchorClicked.connect(self._on_doc_anchor_clicked)
        self.txt_readme_browser.setReadOnly(True)
        readme_layout.addWidget(self.txt_readme_browser, stretch=1)

        layout.addWidget(self.grp_readme, stretch=1)
        self._add_scrollable_tab(workspace)

    def _build_simulation_workspace(self) -> None:
        self.simulation_tab = SimulationTab(translator=self.translator)
        self._add_scrollable_tab(self.simulation_tab)

    def _resolve_doc_path_for_key(self, doc_key: str) -> Path:
        locale = self.translator.active_locale.value
        doc_filename_map = {
            "01": {
                "pt": "docs/pt/01_FUNDAMENTOS_TEORICOS_E_DEFESA_LOGICA.md",
                "es": "docs/es/01_FUNDAMENTOS_TEORICOS_Y_DEFENSA_LOGICA.md",
                "en-GB": "docs/en-GB/01_THEORETICAL_FOUNDATIONS_AND_LOGICAL_DEFENCE.md",
            },
            "02": {
                "pt": "docs/pt/02_GUIA_DA_INTERFACE_UI.md",
                "es": "docs/es/02_GUIA_DE_LA_INTERFAZ_UI.md",
                "en-GB": "docs/en-GB/02_UI_GUIDE.md",
            },
            "03": {
                "pt": "docs/pt/03_MANUAL_DE_OPERACAO_DO_SIMULADOR.md",
                "es": "docs/es/03_MANUAL_DE_OPERACION_DEL_SIMULADOR.md",
                "en-GB": "docs/en-GB/03_SIMULATOR_OPERATION_MANUAL.md",
            },
            "04": {
                "pt": "docs/pt/04_MECANICA_SUBJACENTE_UNDER_THE_HOOD.md",
                "es": "docs/es/04_MECANICA_SUBYACENTE_UNDER_THE_HOOD.md",
                "en-GB": "docs/en-GB/04_UNDER_THE_HOOD_MECHANICS.md",
            },
        }
        if doc_key in doc_filename_map:
            relative_str = doc_filename_map[doc_key].get(locale, doc_filename_map[doc_key]["en-GB"])
            return self.orchestrator.cibersoc_root / relative_str
        return self.orchestrator.cibersoc_root / "README.md"

    def _load_document_file(self, target_path: Path) -> None:
        if target_path.exists() and target_path.is_file():
            content = target_path.read_text(encoding="utf-8")
        else:
            fallback = self.orchestrator.cibersoc_root / "README.md"
            content = fallback.read_text(encoding="utf-8")
            target_path = fallback
        self._current_doc_path = target_path
        rendered_html = render_markdown_to_html(
            content,
            base_font_points=self._font_points,
            project_root=self.orchestrator.cibersoc_root,
        )
        self.txt_readme_browser.setHtml(rendered_html)

    def _on_doc_selector_changed(self, _index: int) -> None:
        doc_key = str(self.cmb_doc_selector.currentData())
        path = self._resolve_doc_path_for_key(doc_key)
        self._load_document_file(path)

    def _on_open_readme_clicked(self) -> None:
        readme_index = self.cmb_doc_selector.findData("README.md")
        self.cmb_doc_selector.setCurrentIndex(readme_index)
        readme_path = (self.orchestrator.cibersoc_root / "README.md").resolve()
        self._load_document_file(readme_path)
        self._open_file_in_desktop(readme_path)

    def _on_doc_anchor_clicked(self, url: QUrl) -> None:
        clean_url = url.toString().split("#")[0].strip()
        candidate_path = (self.orchestrator.cibersoc_root / clean_url).resolve()
        if candidate_path.is_file() and candidate_path.suffix == ".md":
            self._load_document_file(candidate_path)
            for index in range(self.cmb_doc_selector.count()):
                key = str(self.cmb_doc_selector.itemData(index))
                if self._resolve_doc_path_for_key(key) == candidate_path:
                    self.cmb_doc_selector.blockSignals(True)
                    self.cmb_doc_selector.setCurrentIndex(index)
                    self.cmb_doc_selector.blockSignals(False)
                    break

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.apply_responsive_layout(self.width(), self.height())

    def apply_responsive_layout(
        self, viewport_width: int, viewport_height: int
    ) -> ResponsiveLayoutMode:
        target_mode = (
            ResponsiveLayoutMode.COMPACT
            if viewport_width < COMPACT_LAYOUT_BREAKPOINT
            else ResponsiveLayoutMode.EXPANDED
        )
        if target_mode != self.current_layout_mode:
            self.current_layout_mode = target_mode
            is_compact = target_mode == ResponsiveLayoutMode.COMPACT
            splitter_orientation = (
                Qt.Orientation.Vertical if is_compact else Qt.Orientation.Horizontal
            )
            box_direction = (
                QBoxLayout.Direction.TopToBottom if is_compact else QBoxLayout.Direction.LeftToRight
            )
            header_resize_mode = (
                QHeaderView.ResizeMode.ResizeToContents
                if is_compact
                else QHeaderView.ResizeMode.Stretch
            )
            self.splitter_councils.setOrientation(splitter_orientation)
            self.splitter_enterprise.setOrientation(splitter_orientation)
            for adaptive_box in self._adaptive_box_layouts:
                adaptive_box.setDirection(box_direction)
            for table in self._responsive_tables:
                header = table.horizontalHeader()
                header.setSectionResizeMode(header_resize_mode)
                header.setStretchLastSection(is_compact)

        console_minimum = max(95, self._line_height * 6)
        console_maximum = max(220, self._line_height * 10)
        console_share = max(console_minimum, min(console_maximum, int(viewport_height * 0.19)))
        workspace_share = max(260, viewport_height - console_share)
        self.main_vertical_splitter.setSizes([workspace_share, console_share])
        return target_mode

    def _on_language_selector_changed(self, _index: int) -> None:
        chosen_code = self.cmb_language.currentData()
        valid_codes = {loc.value for loc in SupportedLocale}
        if isinstance(chosen_code, str) and chosen_code in valid_codes:
            self.translator.switch_locale(SupportedLocale(chosen_code))

    def _on_locale_changed(self, active_locale: SupportedLocale) -> None:
        combo_index = self.cmb_language.findData(active_locale.value)
        if combo_index != self.cmb_language.currentIndex():
            self.cmb_language.blockSignals(True)
            self.cmb_language.setCurrentIndex(combo_index)
            self.cmb_language.blockSignals(False)
        self.retranslate_static_labels()
        self.refresh_all_views()
        if self._settings is not None:
            self._settings.setValue(LOCALE_SETTINGS_KEY, active_locale.value)

    def retranslate_static_labels(self) -> None:
        t = self.translator.translate
        self.setWindowTitle(t("app.window_title"))
        self.lbl_system_title.setText(t("header.title"))
        self.lbl_system_subtitle.setText(t("header.subtitle"))
        self.lbl_language_prompt.setText(t("header.language_label"))
        self.cmb_language.setToolTip(t("header.language_label"))
        self.lbl_font_size.setText(t("header.font_label", points=self._font_points))
        self.btn_font_decrease.setToolTip(t("header.font_decrease_tip"))
        self.btn_font_increase.setToolTip(t("header.font_increase_tip"))
        self.btn_font_reset.setToolTip(t("header.font_reset_tip"))

        self.tabs.setTabText(0, t("tabs.councils"))
        self.tabs.setTabText(1, t("tabs.sortition"))
        self.tabs.setTabText(2, t("tabs.cybernetics"))
        self.tabs.setTabText(3, t("tabs.enterprise"))
        self.tabs.setTabText(4, t("tabs.charter_docs"))
        self.tabs.setTabText(5, t("tabs.simulation"))
        self.tabs.setTabToolTip(0, t("tabs.councils"))
        self.tabs.setTabToolTip(1, t("tabs.sortition"))
        self.tabs.setTabToolTip(2, t("tabs.cybernetics"))
        self.tabs.setTabToolTip(3, t("tabs.enterprise"))
        self.tabs.setTabToolTip(4, t("tabs.charter_docs"))
        self.tabs.setTabToolTip(5, t("tabs.simulation"))

        self.grp_mesh.setTitle(t("councils.mesh_group"))
        self.lbl_inspect_tier.setText(t("councils.inspect_label"))
        self.cmb_council.setToolTip(t("councils.inspect_label"))
        self.btn_escalate_demand.setText(t("councils.btn_escalate_demand"))
        self.grp_secretary.setTitle(t("councils.sg_group"))
        self.btn_sg_authenticate.setText(t("councils.btn_sg_authenticate"))
        self.btn_sg_veto_test.setText(t("councils.btn_sg_veto_test"))
        self.grp_ministries.setTitle(t("councils.ministries_group"))
        self.tbl_ministries.setHorizontalHeaderLabels(
            [
                t("councils.col_portfolio"),
                t("councils.col_lead"),
                t("councils.col_bond"),
                t("councils.col_members"),
            ]
        )
        self.grp_defence.setTitle(t("councils.defence_group"))
        self.btn_defence_order.setText(t("councils.btn_defence_order"))
        self.btn_defence_block.setText(t("councils.btn_defence_block"))

        self.grp_sortition_controls.setTitle(t("sortition.group_controls"))
        self.btn_next_cycle.setText(t("sortition.btn_next_cycle"))
        self.btn_block_election.setText(t("sortition.btn_block_election"))
        self.grp_sortition_proofs.setTitle(t("sortition.group_proofs"))
        self.tbl_proofs.setHorizontalHeaderLabels(
            [
                t("sortition.col_council"),
                t("sortition.col_cycle"),
                t("sortition.col_merkle"),
                t("sortition.col_quotas"),
                t("sortition.col_status"),
            ]
        )

        self.grp_plebiscite.setTitle(t("cyber.group_plebiscite"))
        self.lbl_plebiscite_prompt.setText(t("cyber.prompt_label"))
        self.lbl_votes_edu.setText(t("cyber.votes_edu_label"))
        self.lbl_votes_health.setText(t("cyber.votes_health_label"))
        self.btn_run_plebiscite.setText(t("cyber.btn_run_plebiscite"))
        self.btn_block_person_pleb.setText(t("cyber.btn_block_person"))
        self.btn_block_council_override.setText(t("cyber.btn_block_override"))
        self.grp_cyber_matrix.setTitle(t("cyber.group_matrix"))
        self.tbl_cyber.setHorizontalHeaderLabels(
            [
                t("cyber.col_sector"),
                t("cyber.col_share"),
                t("cyber.col_final_demand"),
                t("cyber.col_gross_output"),
                t("cyber.col_labour"),
                t("cyber.col_harmony"),
            ]
        )

        self.grp_enterprise_ledger.setTitle(t("enterprise.group_ledger"))
        self.lbl_revenue_prompt.setText(t("enterprise.revenue_label"))
        self.btn_distribute_profit.setText(t("enterprise.btn_distribute"))
        self.tbl_workers.setHorizontalHeaderLabels(
            [
                t("enterprise.col_worker"),
                t("enterprise.col_role"),
                t("enterprise.col_status"),
                t("enterprise.col_base_pay"),
                t("enterprise.col_profit_share"),
            ]
        )
        self.btn_block_ceo.setText(t("enterprise.btn_block_ceo"))
        self.grp_mandate_lifecycle.setTitle(t("mandate.group_lifecycle"))
        self.btn_mandate_start.setText(t("mandate.btn_start"))
        self.btn_mandate_cpi.setText(t("mandate.btn_cpi"))
        self.btn_mandate_return.setText(t("mandate.btn_return"))
        self.btn_mandate_dismiss_test.setText(t("mandate.btn_dismiss_test"))

        self.grp_charter.setTitle(t("charter.group_title"))
        self.btn_run_audit.setText(t("charter.btn_run_scan"))
        self.btn_export_fullhd_wallpaper.setText(t("charter.btn_export_fullhd"))
        self.grp_audit_console.setTitle(t("audit.console_group"))

        self.grp_readme.setTitle(t("docs.group_title"))
        self.lbl_doc_selector.setText(t("docs.selector_label"))
        self.btn_open_readme.setText(t("docs.btn_open_readme"))

        self.simulation_tab.set_group_titles(
            t("simulation.group_controls"),
            t("simulation.events_group"),
        )
        self.simulation_tab.set_button_texts(
            t("simulation.btn_advance_year"),
            t("simulation.btn_reset"),
        )
        self.simulation_tab.apply_translations(self.translator)

        current_doc_key = self.cmb_doc_selector.currentData() or "README.md"
        self.cmb_doc_selector.blockSignals(True)
        self.cmb_doc_selector.clear()
        doc_entries = (
            ("README.md", t("docs.opt_readme")),
            ("01", t("docs.opt_foundations")),
            ("02", t("docs.opt_ui_guide")),
            ("03", t("docs.opt_simulator")),
            ("04", t("docs.opt_mechanics")),
        )
        for key, label in doc_entries:
            self.cmb_doc_selector.addItem(label, key)
        restored_doc_index = max(0, self.cmb_doc_selector.findData(current_doc_key))
        self.cmb_doc_selector.setCurrentIndex(restored_doc_index)
        self.cmb_doc_selector.blockSignals(False)

        selected_doc_key = str(self.cmb_doc_selector.currentData())
        self._load_document_file(self._resolve_doc_path_for_key(selected_doc_key))

        self.cmb_council.blockSignals(True)
        for index, council in enumerate(self.orchestrator.mesh.list_councils()):
            tier_label = t(f"tier.{council.tier.value}")
            council_label = t(council.name)
            self.cmb_council.setItemText(index, f"[{tier_label}] {council_label}")
        self.cmb_council.blockSignals(False)

    def _selected_council_id(self) -> str:
        return str(self.cmb_council.currentData())

    def _resolve_worker_role_label(self, role_title: str) -> str:
        if role_title in self.translator.available_keys:
            return self.translator.translate(role_title)
        return role_title

    def _sync_revenue_parameter(self) -> Decimal:
        selected_revenue = Decimal(str(self.spn_revenue.value()))
        self.orchestrator.current_gross_revenue = selected_revenue
        return selected_revenue

    def _on_combo_council_changed(self, _index: int) -> None:
        council_id = self._selected_council_id()
        self.mesh_canvas.set_selected_council(council_id)
        self._refresh_council_inspector(council_id)

    def _on_canvas_council_selected(self, council_id: str) -> None:
        combo_index = self.cmb_council.findData(council_id)
        self.cmb_council.setCurrentIndex(combo_index)
        self._refresh_council_inspector(council_id)

    def _on_escalate_demand(self) -> None:
        self.orchestrator.escalate_demand_from_sector(
            "CONS-SET-BOQUEIRAO",
            "24h Polyclinic Expansion and Light-Rail Corridor",
        )
        self.refresh_all_views()

    def _on_sg_authenticate(self) -> None:
        self.orchestrator.secretary_order_and_authenticate(self._selected_council_id())
        self.refresh_all_views()

    def _on_sg_veto_test(self) -> None:
        self.orchestrator.test_secretary_autocratic_block(self._selected_council_id())
        self.refresh_all_views()

    def _on_defence_valid_order(self) -> None:
        self.orchestrator.issue_valid_civil_defence_order()
        self.refresh_all_views()

    def _on_defence_insubordination_test(self) -> None:
        self.orchestrator.test_military_insubordination_block()
        self.refresh_all_views()

    def _on_next_sortition_cycle(self) -> None:
        self.orchestrator.execute_next_sortition_cycle()
        self.mesh_canvas.set_mesh(self.orchestrator.mesh)
        self.refresh_all_views()

    def _on_block_election(self) -> None:
        self.orchestrator.test_electoral_candidacy_block()
        self.refresh_all_views()

    def _on_run_plebiscite(self) -> None:
        self.orchestrator.execute_macro_plebiscite(
            votes_education=self.spn_votes_edu.value(),
            votes_health=self.spn_votes_health.value(),
        )
        self.refresh_all_views()

    def _on_block_person_plebiscite(self) -> None:
        self.orchestrator.test_plebiscite_person_topic_block()
        self.refresh_all_views()

    def _on_block_council_override(self) -> None:
        self.orchestrator.test_council_budget_override_block()
        self.refresh_all_views()

    def _on_distribute_profit(self) -> None:
        self.orchestrator.execute_profit_distribution(gross_revenue=self._sync_revenue_parameter())
        self.refresh_all_views()

    def _on_block_ceo(self) -> None:
        self.orchestrator.test_ceo_appointment_block()
        self.refresh_all_views()

    def _on_mandate_start(self) -> None:
        self._sync_revenue_parameter()
        self.orchestrator.start_tracked_worker_mandate()
        self.refresh_all_views()

    def _on_mandate_cpi(self) -> None:
        self._sync_revenue_parameter()
        self.orchestrator.advance_inflation_and_compute_stipend()
        self.refresh_all_views()

    def _on_mandate_return(self) -> None:
        self._sync_revenue_parameter()
        self.orchestrator.reinstate_tracked_worker()
        self.refresh_all_views()

    def _on_mandate_dismiss_test(self) -> None:
        self._sync_revenue_parameter()
        self.orchestrator.test_post_mandate_dismissal_lock()
        self.refresh_all_views()

    def _on_run_integrity_audit(self) -> None:
        self.orchestrator.execute_project_integrity_audit()
        self._refresh_charter_panel()
        self._refresh_audit_log()

    def refresh_all_views(self) -> None:
        self.lbl_cycle_badge.setText(
            self.translator.translate("header.cycle_badge", cycle=self.orchestrator.current_cycle)
        )
        self.mesh_canvas.set_mesh(self.orchestrator.mesh)
        self._refresh_council_inspector(self._selected_council_id())
        self._refresh_sortition_tab()
        self._refresh_cybernetics_tab()
        self._refresh_enterprise_and_mandate_tab()
        self._refresh_charter_panel()
        self._refresh_audit_log()
        self.simulation_tab.set_active_macro_directive(self.orchestrator.active_macro_directive or "")

    def _refresh_council_inspector(self, council_id: str) -> None:
        t = self.translator.translate
        council = self.orchestrator.mesh.get_council(council_id)
        secretary_profile = council.secretary_general.profile
        self.lbl_secretary_info.setText(
            t(
                "councils.sg_summary",
                citizen_id=secretary_profile.citizen_id,
                full_name=secretary_profile.full_name,
                stratum=secretary_profile.stratum_key,
                tier=t(f"tier.{council.tier.value}"),
                weight=council.secretary_general.voting_weight,
            )
        )
        prop_metric = self.orchestrator.assess_council_proportionality(council_id)
        self.lbl_council_proportionality.setText(
            t(
                "councils.proportionality_format",
                seats=prop_metric.assigned_seats,
                aggregate=prop_metric.sectoral_base_aggregate,
                ratio=f"{prop_metric.proportionality_ratio:.2f}",
                status=(
                    t("proof.valid")
                    if prop_metric.is_mathematically_proportional
                    else t("proof.invalid")
                ),
                rationale=prop_metric.rationale,
            )
        )

        portfolios = list(council.portfolios.items())
        self.tbl_ministries.setRowCount(len(portfolios))
        for row_index, (portfolio, chamber_members) in enumerate(portfolios):
            lead = chamber_members[0]
            bond_label = t("bond.military") if lead.is_military_personnel else t("bond.civilian")
            self.tbl_ministries.setItem(
                row_index, 0, QTableWidgetItem(t(f"portfolio.{portfolio.value}"))
            )
            self.tbl_ministries.setItem(
                row_index, 1, QTableWidgetItem(f"{lead.citizen_id} ({lead.full_name})")
            )
            self.tbl_ministries.setItem(row_index, 2, QTableWidgetItem(bond_label))
            self.tbl_ministries.setItem(row_index, 3, QTableWidgetItem(str(len(chamber_members))))

        federal_council = self.orchestrator.mesh.get_council("CONS-FED-BRASIL")
        defence_lead = federal_council.portfolios[MinistryPortfolio.DEFENCE][0]
        self.lbl_defence_status.setText(
            t(
                "councils.defence_status",
                citizen_id=defence_lead.citizen_id,
                full_name=defence_lead.full_name,
                is_military=defence_lead.is_military_personnel,
            )
        )

    def _refresh_sortition_tab(self) -> None:
        t = self.translator.translate
        summary = self.orchestrator.last_cycle_summary
        assert summary is not None
        self.lbl_sortition_summary.setText(
            t(
                "sortition.summary",
                cycle=summary.cycle_number,
                population=len(self.orchestrator.population),
                active=len(self.orchestrator.sortition_engine.active_councillor_ids),
                quarantined=summary.quarantined_from_previous,
                overlap=summary.overlapping_consecutive_members,
            )
        )
        councils = self.orchestrator.mesh.list_councils()
        self.tbl_proofs.setRowCount(len(councils))
        for row_index, council in enumerate(councils):
            proof, is_valid = self.orchestrator.proofs_by_council[council.council_id]
            quotas_text = ", ".join(f"{stratum}:{quota}" for stratum, quota in proof.stratum_quotas)
            status_text = t("proof.valid") if is_valid else t("proof.invalid")
            self.tbl_proofs.setItem(row_index, 0, QTableWidgetItem(council.council_id))
            self.tbl_proofs.setItem(row_index, 1, QTableWidgetItem(str(proof.cycle_number)))
            self.tbl_proofs.setItem(
                row_index, 2, QTableWidgetItem(f"{proof.eligible_merkle_root[:20]}...")
            )
            self.tbl_proofs.setItem(row_index, 3, QTableWidgetItem(quotas_text))
            self.tbl_proofs.setItem(row_index, 4, QTableWidgetItem(status_text))

    def _refresh_cybernetics_tab(self) -> None:
        t = self.translator.translate
        directive = self.orchestrator.last_directive
        assert directive is not None
        spectral_radius = self.orchestrator.technical_matrix.estimate_spectral_radius()
        continuous_shift = MacroAllocationPlebiscite.compute_cockshott_continuous_shift(
            votes_increase=self.spn_votes_health.value(),
            votes_unchanged=0,
            votes_decrease=self.spn_votes_edu.value(),
            max_annual_shift_pct=5.0,
        )
        clearing = self.orchestrator.evaluate_market_clearing(
            sector_id="HEALTH",
            labor_value_hours=1.0,
            market_clearing_price_tokens=1.05,
        )
        eco = self.orchestrator.audit_carbon_budget(
            annual_carbon_budget_megatons=500.0,
            sector_outputs=directive.compulsory_gross_output,
            carbon_intensity_per_output=(0.04, 0.03, 0.02, 0.01),
        )
        base_summary = t(
            "cyber.metrics_summary",
            winner=directive.winning_option_id,
            ballots=directive.total_valid_ballots,
            rho=spectral_radius,
            shift=continuous_shift,
            hash_prefix=directive.directive_hash[:20],
        )
        self.lbl_cyber_metrics.setText(
            f"{base_summary}\n"
            f"[{t('cybernetics.market_clearing_title')}] r = p/v = {clearing.clearing_to_value_ratio:.2f} | Signal = {clearing.reallocation_signal:+.2f}\n"
            f"[{t('cybernetics.carbon_budget_title')}] {eco.current_physical_carbon_draw:.1f} / {eco.annual_carbon_budget_megatons:.1f} Mt (Safe: {eco.is_within_planetary_boundary})"
        )
        embedded_labour = compute_embedded_labour_hours_jacobi(
            self.orchestrator.technical_matrix, self.orchestrator.direct_labour_vector
        )
        shares_by_sector = dict(directive.compulsory_budget_shares_pct)
        self.tbl_cyber.setRowCount(len(self.orchestrator.sector_keys))
        for index, sector_key in enumerate(self.orchestrator.sector_keys):
            self.tbl_cyber.setItem(index, 0, QTableWidgetItem(t(sector_key)))
            self.tbl_cyber.setItem(
                index, 1, QTableWidgetItem(f"{shares_by_sector[sector_key]:.2f}%")
            )
            self.tbl_cyber.setItem(
                index, 2, QTableWidgetItem(f"{directive.compulsory_final_demand[index]:.2f}")
            )
            self.tbl_cyber.setItem(
                index, 3, QTableWidgetItem(f"{directive.compulsory_gross_output[index]:.2f}")
            )
            self.tbl_cyber.setItem(index, 4, QTableWidgetItem(f"{embedded_labour[index]:.4f} h"))
            self.tbl_cyber.setItem(
                index, 5, QTableWidgetItem(f"{self.orchestrator.last_harmonies[index]:+.4f}")
            )

    def _refresh_enterprise_and_mandate_tab(self) -> None:
        t = self.translator.translate
        receipt = self.orchestrator.last_profit_receipt
        assert receipt is not None
        self.lbl_enterprise_summary.setText(
            t(
                "enterprise.summary",
                name=self.orchestrator.enterprise.name,
                mask_code=self.orchestrator.enterprise.property_mask.state_code,
                net_profit=receipt.distributable_net_profit,
                workers=receipt.eligible_worker_count,
                share=receipt.equal_full_share_per_worker,
                retained=receipt.corporate_retained_profit,
                carry=receipt.next_carry_over_cents,
            )
        )
        payouts_by_worker = dict(receipt.payouts_by_worker)
        ordered_workers = sorted(
            self.orchestrator.enterprise.workers.values(), key=lambda w: w.worker_id
        )
        self.tbl_workers.setRowCount(len(ordered_workers))
        for row_index, worker in enumerate(ordered_workers):
            payout_label = (
                f"$ {payouts_by_worker[worker.worker_id]}"
                if worker.worker_id in payouts_by_worker
                else t("enterprise.state_stipend_cell")
            )
            localized_role = self._resolve_worker_role_label(worker.role_title)
            self.tbl_workers.setItem(
                row_index, 0, QTableWidgetItem(f"{worker.worker_id} ({worker.full_name})")
            )
            self.tbl_workers.setItem(row_index, 1, QTableWidgetItem(localized_role))
            self.tbl_workers.setItem(
                row_index, 2, QTableWidgetItem(t(f"employment.{worker.status.value}"))
            )
            self.tbl_workers.setItem(row_index, 3, QTableWidgetItem(f"$ {worker.monthly_base_pay}"))
            self.tbl_workers.setItem(row_index, 4, QTableWidgetItem(payout_label))

        record = self.orchestrator.protection_manager.get_record(
            self.orchestrator.tracked_worker_id
        )
        if record is None:
            self.lbl_mandate_status.setText(
                t(
                    "mandate.status_idle",
                    worker_id=self.orchestrator.tracked_worker_id,
                    cpi=self.orchestrator.price_index_series.current_index,
                )
            )
        elif record.reinstated_on is None:
            current_stipend = self.orchestrator.protection_manager.compute_state_councillor_stipend(
                record.citizen_id, self.orchestrator.price_index_series.current_index
            )
            self.lbl_mandate_status.setText(
                t(
                    "mandate.status_active",
                    worker_id=record.citizen_id,
                    council_id=record.council_id,
                    prior_income=record.prior_civilian_monthly_income,
                    cpi=self.orchestrator.price_index_series.current_index,
                    current_pay=current_stipend,
                )
            )
        else:
            self.lbl_mandate_status.setText(
                t(
                    "mandate.status_reinstated",
                    worker_id=record.citizen_id,
                    role=self._resolve_worker_role_label(record.original_role_title),
                    reinstated_on=record.reinstated_on,
                    base_pay=record.reinstated_monthly_base_pay,
                    locked_until=record.stability_locked_until,
                )
            )

    def _refresh_charter_panel(self) -> None:
        t = self.translator.translate
        lines: list[str] = []
        if self.orchestrator.last_scan_results is not None:
            integrity_report, clean_code_report = self.orchestrator.last_scan_results
            lines.append(t("charter.scan_header"))
            lines.append(
                t("charter.scan_project_files", count=integrity_report.project_files_scanned)
            )
            lines.append(
                t(
                    "charter.scan_locales",
                    locales=", ".join(integrity_report.documentation_locales_verified),
                )
            )
            lines.append(
                t("charter.scan_missing_paths", count=len(integrity_report.missing_required_paths))
            )
            lines.append(t("charter.scan_clean_code", clean=clean_code_report.is_compliant))
            lines.append(t("charter.scan_self_contained", ok=integrity_report.is_self_contained))
            lines.append("")

        charter = build_localized_architectural_charter(self.translator)
        lines.append(charter.system_heading)
        lines.append("")
        lines.append(t("charter.references_heading"))
        for reference in charter.foundational_references:
            lines.append(f"  • {reference}")
        lines.append("")
        lines.append(t("charter.axioms_heading"))
        for title, body in charter.structural_axioms:
            lines.append(f"  [{title}]\n    {body}")
        self.txt_charter_report.setPlainText("\n".join(lines))

    def _refresh_audit_log(self) -> None:
        rendered_entries = [
            entry.render(self.translator) for entry in self.orchestrator.audit_events[-25:]
        ]
        self.txt_audit_log.setPlainText("\n".join(rendered_entries))

    def _is_headless_execution(self) -> bool:
        return QApplication.platformName() == "offscreen"

    def _open_file_in_desktop(self, target_path: Path) -> bool:
        if self._is_headless_execution():
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(target_path.resolve())))

    def _sync_fullhd_wallpaper_locale(self, active_locale: SupportedLocale) -> Path:
        return export_fullhd_wallpaper(
            self.orchestrator.cibersoc_root / "assets" / "images",
            locale=active_locale.value,
        )

    def _on_export_fullhd_wallpaper(self) -> None:
        target_path = self._sync_fullhd_wallpaper_locale(self.translator.active_locale)
        if not self._is_headless_execution():
            loc_suffix = self.translator.active_locale.value.replace("-", "_")
            default_target = (
                Path.home() / "Desktop" / f"cibersoc_freedom_wings_fullhd_{loc_suffix}.png"
            )
            chosen_path, _ = QFileDialog.getSaveFileName(
                self,
                self.translator.translate("charter.btn_export_fullhd"),
                str(default_target),
                "PNG Images (*.png)",
            )
            if not chosen_path:
                return
            dest = Path(chosen_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(target_path.read_bytes())
            target_path = dest
        self._open_file_in_desktop(target_path)
        self.orchestrator.record_audit_event(
            "log.fullhd_wallpaper_exported",
            path=str(target_path.resolve()),
        )
        self._refresh_audit_log()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        apply_macos_dock_icon()


def obtain_qt_application(arguments: list[str] | None = None) -> QApplication:
    existing_instance = QApplication.instance()
    if isinstance(existing_instance, QApplication):
        return existing_instance
    return QApplication(arguments if arguments is not None else sys.argv)


def launch_application(
    arguments: list[str] | None = None,
    auto_close_ms: int | None = None,
    initial_locale: SupportedLocale = SupportedLocale.ENGLISH_UK,
    on_ready: Callable[[CiberSocMainWindow], None] | None = None,
) -> int:
    apply_macos_dock_icon()
    app = obtain_qt_application(arguments)
    app.setWindowIcon(build_freedom_wings_icon())
    translator = LocalizationCatalog(initial_locale=initial_locale)
    window = CiberSocMainWindow(translator=translator, settings=QSettings("CIBERSOC", "CiberSocUI"))
    window.show()
    apply_macos_dock_icon()
    if on_ready is not None:
        QTimer.singleShot(0, lambda: on_ready(window))
    if auto_close_ms is not None:
        QTimer.singleShot(auto_close_ms, app.quit)
    return app.exec()
