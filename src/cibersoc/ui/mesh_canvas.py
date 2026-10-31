from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..councils import EscalatedCouncilMesh
from ..i18n.translator import LocalizationCatalog
from .theme import (
    DEFAULT_FONT_POINTS,
    DEFAULT_PALETTE,
    READABLE_FONT_FAMILIES,
    clamp_font_points,
    font_scale_factor,
)


class CouncilMeshCanvas(QWidget):
    council_selected = Signal(str)

    def __init__(
        self,
        mesh: EscalatedCouncilMesh,
        translator: LocalizationCatalog,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._mesh = mesh
        self._translator = translator
        self._selected_council_id = "CONS-FED-BRASIL"
        self._font_points = DEFAULT_FONT_POINTS
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._apply_font_metrics_to_minimum_size()

    @property
    def font_points(self) -> int:
        return self._font_points

    def set_font_points(self, points: int) -> None:
        self._font_points = clamp_font_points(points)
        self._apply_font_metrics_to_minimum_size()
        self.updateGeometry()
        self.update()

    def _build_font(self, extra_points: int = 0, bold: bool = False) -> QFont:
        font = QFont()
        font.setFamilies(list(READABLE_FONT_FAMILIES))
        font.setPointSizeF(float(self._font_points + extra_points))
        font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
        return font

    def _title_font(self) -> QFont:
        return self._build_font(extra_points=1, bold=True)

    def _metadata_font(self) -> QFont:
        return self._build_font()

    def _legend_font(self) -> QFont:
        return self._build_font()

    def _minimum_box_height(self) -> float:
        title_height = QFontMetricsF(self._title_font()).height()
        metadata_height = QFontMetricsF(self._metadata_font()).height()
        return title_height + metadata_height + 14.0 * font_scale_factor(self._font_points)

    def _legend_line_height(self) -> float:
        return QFontMetricsF(self._legend_font()).height() + 4.0

    def _stacked_header_band(self) -> float:
        return 2.0 * self._legend_line_height() + 6.0

    def _vertical_gap(self) -> float:
        return 18.0 * font_scale_factor(self._font_points)

    def _apply_font_metrics_to_minimum_size(self) -> None:
        scale = font_scale_factor(self._font_points)
        title_metrics = QFontMetricsF(self._title_font())
        node_text_width = title_metrics.averageCharWidth() * 24.0
        minimum_width = max(280.0 * scale, 2.0 * node_text_width + 3.0 * 12.0 + 24.0)
        minimum_height = (
            self._stacked_header_band()
            + 4.0 * self._minimum_box_height()
            + 3.0 * self._vertical_gap()
            + 14.0
        )
        self.setMinimumSize(int(minimum_width), int(minimum_height))

    def _legends_fit_side_by_side(self, canvas_width: float) -> bool:
        legend_metrics = QFontMetricsF(self._legend_font())
        needed_width = sum(
            legend_metrics.horizontalAdvance(self._translator.translate(key))
            for key in ("councils.canvas_upward_legend", "councils.canvas_downward_legend")
        )
        return canvas_width >= needed_width + 40.0

    def sizeHint(self) -> QSize:
        return QSize(520, 360)

    @property
    def selected_council_id(self) -> str:
        return self._selected_council_id

    def set_mesh(self, mesh: EscalatedCouncilMesh) -> None:
        self._mesh = mesh
        self.update()

    def set_selected_council(self, council_id: str) -> None:
        self._selected_council_id = council_id
        self.update()

    def compute_legend_rectangles(self) -> tuple[QRectF, QRectF]:
        canvas_width = max(1.0, float(self.width()))
        line_height = self._legend_line_height()
        if not self._legends_fit_side_by_side(canvas_width):
            line_width = max(40.0, canvas_width - 16.0)
            return (
                QRectF(8.0, 2.0, line_width, line_height),
                QRectF(8.0, 2.0 + line_height + 2.0, line_width, line_height),
            )
        half_width = (canvas_width - 24.0) / 2.0
        return (
            QRectF(8.0, 4.0, half_width, line_height),
            QRectF(16.0 + half_width, 4.0, half_width, line_height),
        )

    def compute_node_rectangles(self) -> dict[str, QRectF]:
        canvas_width = max(1.0, float(self.width()))
        canvas_height = max(1.0, float(self.height()))
        scale = font_scale_factor(self._font_points)
        stacked = not self._legends_fit_side_by_side(canvas_width)
        header_band = (
            self._stacked_header_band() + 2.0 if stacked else self._legend_line_height() + 10.0
        )
        bottom_padding = 8.0
        minimum_box = self._minimum_box_height()
        available_height = max(
            canvas_height - header_band - bottom_padding,
            4.0 * minimum_box + 3.0 * self._vertical_gap(),
        )

        box_height = max(minimum_box, min(60.0 * scale, available_height * 0.19))
        tier_step = (available_height - box_height) / 3.0

        y_federal = header_band + 2.0
        y_state = y_federal + tier_step
        y_municipal = y_federal + 2.0 * tier_step
        y_sectoral = y_federal + 3.0 * tier_step

        side_margin = max(8.0, canvas_width * 0.03)
        usable_width = max(100.0, canvas_width - 2.0 * side_margin)
        primary_box_width = min(330.0 * scale, usable_width * 0.96)
        sectoral_gap = max(8.0, min(20.0, usable_width * 0.04))
        sectoral_box_width = min(230.0 * scale, (usable_width - sectoral_gap) / 2.0)

        centre_x = canvas_width / 2.0
        return {
            "CONS-FED-BRASIL": QRectF(
                centre_x - primary_box_width / 2.0, y_federal, primary_box_width, box_height
            ),
            "CONS-EST-PARANA": QRectF(
                centre_x - primary_box_width / 2.0, y_state, primary_box_width, box_height
            ),
            "CONS-MUN-CURITIBA": QRectF(
                centre_x - primary_box_width / 2.0, y_municipal, primary_box_width, box_height
            ),
            "CONS-SET-BOQUEIRAO": QRectF(
                centre_x - sectoral_gap / 2.0 - sectoral_box_width,
                y_sectoral,
                sectoral_box_width,
                box_height,
            ),
            "CONS-SET-MATRIZ": QRectF(
                centre_x + sectoral_gap / 2.0,
                y_sectoral,
                sectoral_box_width,
                box_height,
            ),
        }

    def mousePressEvent(self, event: QMouseEvent) -> None:
        cursor_position = event.position()
        for council_id, rectangle in self.compute_node_rectangles().items():
            if rectangle.contains(cursor_position):
                self._selected_council_id = council_id
                self.update()
                self.council_selected.emit(council_id)
                return
        super().mousePressEvent(event)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(DEFAULT_PALETTE.bg_roast_panel))

        rectangles = self.compute_node_rectangles()
        councils_by_id = {council.council_id: council for council in self._mesh.list_councils()}

        for council_id, council in councils_by_id.items():
            if council.parent_council_id is not None:
                child_rect = rectangles[council_id]
                parent_rect = rectangles[council.parent_council_id]
                line_offset = min(14.0, child_rect.width() * 0.12)
                has_upward_flow = len(council.upward_demands) > 0
                has_downward_flow = len(council.binding_macro_directives) > 0

                upward_pen = QPen(
                    QColor(
                        DEFAULT_PALETTE.accent_crema_amber
                        if has_upward_flow
                        else DEFAULT_PALETTE.border_warm_roast
                    ),
                    2.0 if has_upward_flow else 1.2,
                )
                painter.setPen(upward_pen)
                painter.drawLine(
                    QPointF(child_rect.center().x() - line_offset, child_rect.top()),
                    QPointF(parent_rect.center().x() - line_offset, parent_rect.bottom()),
                )

                downward_pen = QPen(
                    QColor(
                        DEFAULT_PALETTE.accent_sage_ok
                        if has_downward_flow
                        else DEFAULT_PALETTE.border_warm_roast
                    ),
                    2.0 if has_downward_flow else 1.2,
                    Qt.PenStyle.DashLine,
                )
                painter.setPen(downward_pen)
                painter.drawLine(
                    QPointF(parent_rect.center().x() + line_offset, parent_rect.bottom()),
                    QPointF(child_rect.center().x() + line_offset, child_rect.top()),
                )

        upward_legend_rect, downward_legend_rect = self.compute_legend_rectangles()
        painter.setFont(self._legend_font())
        legend_metrics = painter.fontMetrics()

        painter.setPen(QColor(DEFAULT_PALETTE.accent_crema_amber))
        upward_text = legend_metrics.elidedText(
            self._translator.translate("councils.canvas_upward_legend"),
            Qt.TextElideMode.ElideRight,
            int(upward_legend_rect.width()),
        )
        painter.drawText(
            upward_legend_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            upward_text,
        )

        painter.setPen(QColor(DEFAULT_PALETTE.accent_sage_ok))
        downward_alignment = (
            Qt.AlignmentFlag.AlignRight
            if self._legends_fit_side_by_side(float(self.width()))
            else Qt.AlignmentFlag.AlignLeft
        )
        downward_text = legend_metrics.elidedText(
            self._translator.translate("councils.canvas_downward_legend"),
            Qt.TextElideMode.ElideRight,
            int(downward_legend_rect.width()),
        )
        painter.drawText(
            downward_legend_rect,
            int(downward_alignment | Qt.AlignmentFlag.AlignVCenter),
            downward_text,
        )

        title_font = self._title_font()
        metadata_font = self._metadata_font()
        title_metrics = QFontMetricsF(title_font)
        metadata_metrics = QFontMetricsF(metadata_font)

        for council_id, rectangle in rectangles.items():
            council = councils_by_id[council_id]
            is_selected = council_id == self._selected_council_id
            fill_colour = QColor(
                DEFAULT_PALETTE.bg_roast_elevated if is_selected else DEFAULT_PALETTE.bg_moka_card
            )
            border_colour = QColor(
                DEFAULT_PALETTE.accent_crema_amber
                if is_selected
                else DEFAULT_PALETTE.border_warm_roast
            )

            painter.setBrush(fill_colour)
            painter.setPen(QPen(border_colour, 2.4 if is_selected else 1.1))
            painter.drawRoundedRect(rectangle, 6.0, 6.0)

            title_line_height = title_metrics.height()
            metadata_line_height = metadata_metrics.height()
            content_height = title_line_height + metadata_line_height + 2.0
            content_top = rectangle.top() + max(0.0, (rectangle.height() - content_height) / 2.0)
            band_width = max(10.0, rectangle.width() - 16.0)
            title_band = QRectF(rectangle.left() + 8.0, content_top, band_width, title_line_height)
            meta_band = QRectF(
                rectangle.left() + 8.0,
                content_top + title_line_height + 2.0,
                band_width,
                metadata_line_height,
            )

            tier_label = self._translator.translate(f"tier.{council.tier.value}").upper()
            council_title = self._translator.translate(council.name)
            painter.setFont(title_font)
            painter.setPen(QColor(DEFAULT_PALETTE.text_ivory_primary))
            elided_title = painter.fontMetrics().elidedText(
                f"[{tier_label}] {council_title}",
                Qt.TextElideMode.ElideRight,
                int(title_band.width()),
            )
            painter.drawText(
                title_band,
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                elided_title,
            )

            painter.setFont(metadata_font)
            painter.setPen(QColor(DEFAULT_PALETTE.text_cream_secondary))
            metadata_text = self._translator.translate(
                "councils.canvas_node_meta",
                seats=len(council.members),
                portfolios=len(council.portfolios),
                upward=len(council.upward_demands),
                downward=len(council.binding_macro_directives),
            )
            elided_meta = painter.fontMetrics().elidedText(
                metadata_text,
                Qt.TextElideMode.ElideRight,
                int(meta_band.width()),
            )
            painter.drawText(
                meta_band,
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                elided_meta,
            )

        painter.end()
