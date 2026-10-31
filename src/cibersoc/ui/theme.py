from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DarkCappuccinoPalette:
    bg_espresso_deep: str = "#16110E"
    bg_roast_panel: str = "#1F1814"
    bg_moka_card: str = "#29201B"
    bg_moka_alt: str = "#241C17"
    bg_roast_elevated: str = "#362A23"
    border_warm_roast: str = "#4A3930"
    text_ivory_primary: str = "#F4EAD8"
    text_cream_secondary: str = "#D7C5B0"
    text_latte_muted: str = "#A58F7B"
    accent_crema_amber: str = "#C89B6D"
    accent_crema_hover: str = "#DFB589"
    accent_sage_ok: str = "#84A97C"
    accent_terracotta_alert: str = "#C26653"


DEFAULT_PALETTE = DarkCappuccinoPalette()

MIN_FONT_POINTS: int = 12
MAX_FONT_POINTS: int = 32
DEFAULT_FONT_POINTS: int = 15
FONT_STEP_POINTS: int = 1
REFERENCE_FONT_POINTS: int = 13

READABLE_FONT_FAMILIES: tuple[str, ...] = (
    "Atkinson Hyperlegible",
    "Lexend",
    "Verdana",
    "Tahoma",
    "Segoe UI",
    "Helvetica Neue",
    "Arial",
    "sans-serif",
)
MONOSPACE_FONT_FAMILIES: tuple[str, ...] = ("Menlo", "Consolas", "DejaVu Sans Mono", "monospace")


def clamp_font_points(points: int | float) -> int:
    return max(MIN_FONT_POINTS, min(MAX_FONT_POINTS, int(round(points))))


def font_scale_factor(points: int | float) -> float:
    return clamp_font_points(points) / REFERENCE_FONT_POINTS


def quote_font_family_list(families: tuple[str, ...]) -> str:
    return ", ".join(f'"{family}"' if " " in family else family for family in families)


def build_dark_cappuccino_stylesheet(
    palette: DarkCappuccinoPalette = DEFAULT_PALETTE,
    base_points: int = DEFAULT_FONT_POINTS,
) -> str:
    base = clamp_font_points(base_points)
    scale = font_scale_factor(base)

    def px(reference_pixels: float) -> int:
        return max(1, int(round(reference_pixels * scale)))

    sans_stack = quote_font_family_list(READABLE_FONT_FAMILIES)
    mono_stack = quote_font_family_list(MONOSPACE_FONT_FAMILIES)
    return f"""
    QMainWindow, QWidget {{
        background-color: {palette.bg_espresso_deep};
        color: {palette.text_ivory_primary};
        font-family: {sans_stack};
        font-size: {base}pt;
    }}
    QScrollArea {{
        background-color: {palette.bg_roast_panel};
        border: none;
    }}
    QSplitter::handle {{
        background-color: {palette.border_warm_roast};
    }}
    QSplitter::handle:horizontal {{
        width: {px(4)}px;
    }}
    QSplitter::handle:vertical {{
        height: {px(4)}px;
    }}
    QSplitter::handle:hover {{
        background-color: {palette.accent_crema_amber};
    }}
    QFrame#HeaderBanner {{
        background-color: {palette.bg_roast_panel};
        border-bottom: 1px solid {palette.border_warm_roast};
        padding: {px(8)}px {px(14)}px;
    }}
    QFrame#StatusFeedbackBar {{
        background-color: {palette.bg_roast_panel};
        border-top: 1px solid {palette.border_warm_roast};
        padding: {px(5)}px {px(12)}px;
    }}
    QFrame#MetricCard {{
        background-color: {palette.bg_moka_card};
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(6)}px;
        padding: {px(6)}px {px(10)}px;
    }}
    QLabel {{
        background-color: transparent;
    }}
    QLabel#SystemTitle {{
        color: {palette.text_ivory_primary};
        font-size: {base + 3}pt;
        font-weight: 700;
        letter-spacing: 0.4px;
    }}
    QLabel#SystemSubtitle {{
        color: {palette.text_latte_muted};
        font-size: {base}pt;
    }}
    QLabel#CycleBadgePill {{
        background-color: {palette.bg_moka_card};
        color: {palette.accent_crema_amber};
        border: 1px solid {palette.accent_crema_amber};
        border-radius: {px(10)}px;
        padding: {px(3)}px {px(10)}px;
        font-size: {base}pt;
        font-weight: 700;
    }}
    QLabel#TabIntro {{
        color: {palette.text_cream_secondary};
        font-size: {base}pt;
        padding: {px(2)}px {px(4)}px {px(4)}px {px(4)}px;
    }}
    QLabel#SectionHeading {{
        color: {palette.accent_crema_amber};
        font-size: {base + 1}pt;
        font-weight: 700;
    }}
    QLabel#SafeguardCaption {{
        color: {palette.text_latte_muted};
        font-size: {base}pt;
        font-weight: 600;
    }}
    QLabel#MetricTitle {{
        color: {palette.text_latte_muted};
        font-size: {base}pt;
        font-weight: 600;
    }}
    QLabel#MetricValue {{
        color: {palette.text_ivory_primary};
        font-size: {base + 2}pt;
        font-weight: 700;
    }}
    QLabel#LiveEventBanner {{
        color: {palette.accent_sage_ok};
        font-size: {base}pt;
        font-weight: 600;
    }}
    QLabel#LiveAlertBanner {{
        color: {palette.accent_terracotta_alert};
        font-size: {base}pt;
        font-weight: 600;
    }}
    QLabel#HeaderEmblem {{
        background-color: transparent;
        padding-right: {px(4)}px;
    }}
    QLabel#SubtleMetadata {{
        color: {palette.accent_crema_amber};
        font-size: {base}pt;
        border-left: 2px solid {palette.accent_crema_amber};
        padding-left: {px(6)}px;
        margin-top: {px(4)}px;
    }}
    QGroupBox {{
        background-color: {palette.bg_roast_panel};
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(6)}px;
        margin-top: 10px;
        padding: {px(12)}px {px(10)}px {px(10)}px {px(10)}px;
        font-weight: 600;
        color: {palette.accent_crema_amber};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 {px(6)}px;
    }}
    QTabWidget::pane {{
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(4)}px;
        background-color: {palette.bg_roast_panel};
    }}
    QTabBar::tab {{
        background-color: {palette.bg_moka_card};
        color: {palette.text_cream_secondary};
        border: 1px solid {palette.border_warm_roast};
        border-bottom: none;
        border-top-left-radius: {px(4)}px;
        border-top-right-radius: {px(4)}px;
        padding: {px(7)}px {px(14)}px;
        min-width: {px(80)}px;
        margin-right: 3px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.text_ivory_primary};
        border-top: 2px solid {palette.accent_crema_amber};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.text_cream_secondary};
        border-top: 2px solid {palette.border_warm_roast};
    }}
    QPushButton {{
        background-color: {palette.bg_moka_card};
        color: {palette.text_ivory_primary};
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(4)}px;
        padding: {px(6)}px {px(12)}px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {palette.bg_roast_elevated};
        border-color: {palette.accent_crema_hover};
    }}
    QPushButton:focus {{
        border-color: {palette.accent_crema_amber};
        outline: none;
    }}
    QPushButton:disabled {{
        color: {palette.text_latte_muted};
        border-color: {palette.border_warm_roast};
        background-color: {palette.bg_espresso_deep};
    }}
    QPushButton#PrimaryActionButton {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.text_ivory_primary};
        border: 1px solid {palette.accent_crema_amber};
        font-weight: 700;
    }}
    QPushButton#PrimaryActionButton:hover {{
        border-color: {palette.accent_crema_hover};
    }}
    QPushButton#AlertActionButton {{
        background-color: {palette.bg_moka_alt};
        border: 1px solid {palette.accent_terracotta_alert};
        color: {palette.text_cream_secondary};
    }}
    QPushButton#AlertActionButton:hover {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.text_ivory_primary};
    }}
    QPushButton#SubtleToggleButton {{
        background-color: {palette.bg_moka_card};
        color: {palette.text_cream_secondary};
        border: 1px solid {palette.border_warm_roast};
        padding: {px(4)}px {px(10)}px;
        font-size: {base}pt;
    }}
    QPushButton#FontStepButton {{
        background-color: {palette.bg_moka_card};
        color: {palette.accent_crema_amber};
        border: 1px solid {palette.accent_crema_amber};
        padding: {px(4)}px {px(10)}px;
        font-weight: 700;
    }}
    QPushButton#FontStepButton:hover {{
        background-color: {palette.bg_roast_elevated};
        border-color: {palette.accent_crema_hover};
    }}
    QPushButton#FontStepButton:disabled {{
        color: {palette.text_latte_muted};
        border-color: {palette.border_warm_roast};
    }}
    QToolTip {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.text_ivory_primary};
        border: 1px solid {palette.accent_crema_amber};
        font-size: {base}pt;
        padding: {px(4)}px;
    }}
    QComboBox, QSpinBox {{
        background-color: {palette.bg_moka_card};
        color: {palette.text_ivory_primary};
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(4)}px;
        padding: {px(5)}px {px(8)}px;
    }}
    QComboBox:hover, QSpinBox:hover {{
        border-color: {palette.text_latte_muted};
    }}
    QComboBox:focus, QSpinBox:focus {{
        border-color: {palette.accent_crema_amber};
    }}
    QComboBox QAbstractItemView {{
        background-color: {palette.bg_moka_card};
        color: {palette.text_ivory_primary};
        selection-background-color: {palette.bg_roast_elevated};
        selection-color: {palette.text_ivory_primary};
        border: 1px solid {palette.border_warm_roast};
        outline: none;
        padding: {px(2)}px;
    }}
    QTableWidget, QPlainTextEdit, QTextBrowser {{
        background-color: {palette.bg_moka_card};
        alternate-background-color: {palette.bg_moka_alt};
        color: {palette.text_ivory_primary};
        border: 1px solid {palette.border_warm_roast};
        border-radius: {px(4)}px;
        gridline-color: {palette.border_warm_roast};
        selection-background-color: {palette.bg_roast_elevated};
        selection-color: {palette.text_ivory_primary};
        font-size: {base}pt;
    }}
    QTextBrowser {{
        font-family: {sans_stack};
        padding: {px(8)}px {px(12)}px;
    }}
    QPlainTextEdit {{
        font-family: {mono_stack};
    }}
    QHeaderView::section {{
        background-color: {palette.bg_roast_elevated};
        color: {palette.accent_crema_amber};
        border: 1px solid {palette.border_warm_roast};
        padding: {px(6)}px;
        font-weight: 700;
    }}
    QScrollBar:vertical {{
        background-color: {palette.bg_espresso_deep};
        width: {px(10)}px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {palette.border_warm_roast};
        border-radius: {px(4)}px;
        min-height: {px(24)}px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {palette.accent_crema_amber};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        border: none;
        background: none;
    }}
    QScrollBar:horizontal {{
        background-color: {palette.bg_espresso_deep};
        height: {px(10)}px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {palette.border_warm_roast};
        border-radius: {px(4)}px;
        min-width: {px(24)}px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {palette.accent_crema_amber};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        border: none;
        background: none;
    }}
    """
