from __future__ import annotations

import math
from pathlib import Path
import sys
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)


def render_freedom_wings_image(size: int = 512) -> QImage:
    scale = size / 512.0
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.scale(scale, scale)

    squircle = QPainterPath()
    squircle.addRoundedRect(QRectF(16, 16, 480, 480), 108, 108)
    bg_gradient = QRadialGradient(256, 230, 280)
    bg_gradient.setColorAt(0.0, QColor("#2A1F19"))
    bg_gradient.setColorAt(0.55, QColor("#1A130F"))
    bg_gradient.setColorAt(1.0, QColor("#0F0B09"))
    painter.fillPath(squircle, bg_gradient)

    painter.setPen(QPen(QColor("#5C4335"), 4))
    painter.drawPath(squircle)

    inner_squircle = QPainterPath()
    inner_squircle.addRoundedRect(QRectF(22, 22, 468, 468), 102, 102)
    painter.setPen(QPen(QColor("#C89B6D"), 1.5))
    painter.drawPath(inner_squircle)

    painter.save()
    painter.setClipPath(squircle)
    rays = (
        (-55, 35, 18),
        (-45, 55, 36),
        (-35, 45, 24),
        (-25, 25, 14),
        (35, 25, 14),
        (45, 40, 28),
        (55, 30, 18),
    )
    for angle_deg, alpha, width in rays:
        rad = math.radians(angle_deg)
        painter.setPen(QPen(QColor(200, 155, 109, alpha), width))
        painter.drawLine(
            QPointF(256, 380),
            QPointF(256 + 400 * math.sin(rad), 380 - 400 * math.cos(rad)),
        )
    painter.restore()

    shield = QPainterPath()
    shield.moveTo(256, 70)
    shield.lineTo(396, 140)
    shield.lineTo(370, 310)
    shield.lineTo(256, 420)
    shield.lineTo(142, 310)
    shield.lineTo(116, 140)
    shield.closeSubpath()

    painter.save()
    painter.setClipPath(shield)
    painter.fillRect(QRectF(100, 50, 156, 400), QColor("#1F1814"))
    painter.fillRect(QRectF(256, 50, 160, 400), QColor("#29201B"))
    painter.restore()
    painter.setPen(QPen(QColor("#C89B6D"), 4))
    painter.drawPath(shield)

    inner_shield = QPainterPath()
    inner_shield.moveTo(256, 85)
    inner_shield.lineTo(382, 148)
    inner_shield.lineTo(358, 302)
    inner_shield.lineTo(256, 404)
    inner_shield.lineTo(154, 302)
    inner_shield.lineTo(130, 148)
    inner_shield.closeSubpath()
    painter.setPen(QPen(QColor("#4A3930"), 2))
    painter.drawPath(inner_shield)

    gear_center = QPointF(256, 345)
    gear_r_out = 60.0
    gear_r_in = 46.0
    gear_teeth = 12
    gear_path = QPainterPath()
    for index in range(gear_teeth * 2):
        angle = index * (math.pi / gear_teeth)
        radius = gear_r_out if (index % 2 == 0) else gear_r_in
        x_pos = gear_center.x() + radius * math.cos(angle)
        y_pos = gear_center.y() + radius * math.sin(angle)
        if index == 0:
            gear_path.moveTo(x_pos, y_pos)
        else:
            gear_path.lineTo(x_pos, y_pos)
    gear_path.closeSubpath()
    painter.fillPath(gear_path, QColor("#18120E"))
    painter.setPen(QPen(QColor("#C89B6D"), 3))
    painter.drawPath(gear_path)

    gear_hole = QPainterPath()
    gear_hole.addEllipse(gear_center, 24, 24)
    painter.fillPath(gear_hole, QColor("#2A1F19"))
    painter.setPen(QPen(QColor("#DFB589"), 2))
    painter.drawPath(gear_hole)

    left_feathers = (
        ((256, 270), (220, 230), (140, 120), (160, 190), (230, 275)),
        ((248, 280), (195, 235), (130, 160), (160, 230), (225, 290)),
        ((240, 295), (180, 255), (130, 210), (170, 270), (220, 310)),
        ((235, 310), (180, 285), (140, 260), (185, 310), (220, 325)),
        ((230, 325), (190, 310), (160, 300), (195, 330), (225, 335)),
    )
    crema_palette = (
        ("#F4EAD8", "#DFB589"),
        ("#DFB589", "#C89B6D"),
        ("#C89B6D", "#B58455"),
        ("#B58455", "#986B42"),
        ("#986B42", "#7D5533"),
    )
    for index, points in enumerate(left_feathers):
        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        gradient = QLinearGradient(points[2][0], points[2][1], points[0][0], points[0][1])
        gradient.setColorAt(0.0, QColor(crema_palette[index][0]))
        gradient.setColorAt(1.0, QColor(crema_palette[index][1]))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor("#1A130F"), 2))
        painter.drawPolygon(polygon)

    right_feathers = (
        ((256, 255), (290, 215), (372, 105), (352, 175), (282, 260)),
        ((264, 265), (317, 220), (382, 145), (352, 215), (287, 275)),
        ((272, 280), (332, 240), (382, 195), (342, 255), (292, 295)),
        ((277, 295), (332, 270), (372, 245), (327, 295), (292, 310)),
        ((282, 310), (322, 295), (352, 285), (317, 315), (287, 320)),
    )
    moka_palette = (
        ("#C26653", "#8C3D2E"),
        ("#8C3D2E", "#5A2A20"),
        ("#5A2A20", "#3D1D16"),
        ("#4A3225", "#2E1E16"),
        ("#36251B", "#1F150F"),
    )
    for index, points in enumerate(right_feathers):
        polygon = QPolygonF([QPointF(x, y) for x, y in points])
        gradient = QLinearGradient(points[2][0], points[2][1], points[0][0], points[0][1])
        gradient.setColorAt(0.0, QColor(moka_palette[index][0]))
        gradient.setColorAt(1.0, QColor(moka_palette[index][1]))
        painter.setBrush(QBrush(gradient))
        highlight_color = "#F4EAD8" if index == 0 else "#C89B6D"
        painter.setPen(QPen(QColor(highlight_color), 1.5))
        painter.drawPolygon(polygon)

    chain_left = QPainterPath()
    chain_left.addRoundedRect(QRectF(190, 415, 35, 18), 8, 8)
    painter.setPen(QPen(QColor("#C89B6D"), 3))
    painter.drawPath(chain_left)

    chain_right = QPainterPath()
    chain_right.addRoundedRect(QRectF(287, 415, 35, 18), 8, 8)
    painter.setPen(QPen(QColor("#C89B6D"), 3))
    painter.drawPath(chain_right)

    painter.setPen(QPen(QColor("#DFB589"), 3))
    painter.drawLine(QPointF(225, 424), QPointF(240, 420))
    painter.drawLine(QPointF(287, 424), QPointF(272, 428))

    star_points: list[QPointF] = []
    for index in range(10):
        angle = index * (math.pi / 5) - math.pi / 2
        radius = 18.0 if (index % 2 == 0) else 7.0
        star_points.append(QPointF(256 + radius * math.cos(angle), 72 + radius * math.sin(angle)))
    painter.setBrush(QBrush(QColor("#F4EAD8")))
    painter.setPen(QPen(QColor("#C89B6D"), 2))
    painter.drawPolygon(QPolygonF(star_points))

    painter.end()
    return image


def build_freedom_wings_pixmap(size: int = 64) -> QPixmap:
    image = render_freedom_wings_image(size)
    return QPixmap.fromImage(image)


def build_freedom_wings_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        pixmap = build_freedom_wings_pixmap(size)
        icon.addPixmap(pixmap)
    return icon


def generate_freedom_wings_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="bg" cx="50%" cy="45%" r="55%">
      <stop offset="0%" stop-color="#2A1F19"/>
      <stop offset="55%" stop-color="#1A130F"/>
      <stop offset="100%" stop-color="#0F0B09"/>
    </radialGradient>
    <linearGradient id="crema" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F4EAD8"/>
      <stop offset="100%" stop-color="#C89B6D"/>
    </linearGradient>
    <linearGradient id="moka" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#C26653"/>
      <stop offset="100%" stop-color="#36251B"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="480" height="480" rx="108" fill="url(#bg)" stroke="#5C4335" stroke-width="4"/>
  <rect x="22" y="22" width="468" height="468" rx="102" fill="none" stroke="#C89B6D" stroke-width="1.5"/>
  <g stroke="#C89B6D" stroke-opacity="0.25" stroke-width="18">
    <line x1="256" y1="380" x2="80" y2="120"/>
    <line x1="256" y1="380" x2="432" y2="120"/>
  </g>
  <polygon points="256,70 396,140 370,310 256,420 142,310 116,140" fill="#1F1814" stroke="#C89B6D" stroke-width="4"/>
  <polygon points="256,85 382,148 358,302 256,404 154,302 130,148" fill="#29201B" stroke="#4A3930" stroke-width="2"/>
  <circle cx="256" cy="345" r="54" fill="#18120E" stroke="#C89B6D" stroke-width="3"/>
  <circle cx="256" cy="345" r="22" fill="#2A1F19" stroke="#DFB589" stroke-width="2"/>
  <g id="wings">
    <polygon points="256,270 220,230 140,120 160,190 230,275" fill="url(#crema)" stroke="#1A130F" stroke-width="2"/>
    <polygon points="248,280 195,235 130,160 160,230 225,290" fill="url(#crema)" stroke="#1A130F" stroke-width="2"/>
    <polygon points="240,295 180,255 130,210 170,270 220,310" fill="url(#crema)" stroke="#1A130F" stroke-width="2"/>
    <polygon points="256,255 290,215 372,105 352,175 282,260" fill="url(#moka)" stroke="#F4EAD8" stroke-width="1.5"/>
    <polygon points="264,265 317,220 382,145 352,215 287,275" fill="url(#moka)" stroke="#C89B6D" stroke-width="1.5"/>
    <polygon points="272,280 332,240 382,195 342,255 292,295" fill="url(#moka)" stroke="#C89B6D" stroke-width="1.5"/>
  </g>
  <polygon points="256,54 261,67 274,67 263,75 267,88 256,80 245,88 249,75 238,67 251,67" fill="#F4EAD8" stroke="#C89B6D" stroke-width="1.5"/>
</svg>"""


_FULLHD_TITLES: dict[str, str] = {
    "pt": "CIBERSOC // SISTEMA SOCIALISTA CIBERNÉTICO E DEMÁRQUICO",
    "en-GB": "CIBERSOC // CYBERNETIC AND DEMARCHIC SOCIALIST SYSTEM",
    "es": "CIBERSOC // SISTEMA SOCIALISTA CIBERNÉTICO Y DEMÁRQUICO",
}

_FULLHD_SUBTITLES: dict[str, str] = {
    "pt": "ESTADO ACÉFALO • SORTEIO ESTATÍSTICO • EXTINÇÃO DO CEO • PARTILHA 1/N • PLANEJAMENTO INSUMO-PRODUTO",
    "en-GB": "HEADLESS STATE • STATISTICAL SORTITION • ZERO CEOS • EQUAL 1/N SURPLUS • INPUT-OUTPUT PLANNING",
    "es": "ESTADO ACÉFALO • SORTEO ESTADÍSTICO • EXTINCIÓN DEL CEO • REPARTO 1/N • PLANIFICACIÓN INSUMO-PRODUCTO",
}


def resolve_fullhd_locale(locale: str | None) -> str:
    if locale in _FULLHD_TITLES:
        return locale
    if isinstance(locale, str):
        lowered = locale.lower()
        if "en" in lowered:
            return "en-GB"
        if "es" in lowered:
            return "es"
    return "pt"


def render_freedom_wings_fullhd_image(
    width: int = 1920,
    height: int = 1080,
    application: QGuiApplication | None = None,
    locale: str | None = None,
) -> QImage:
    app = application if application is not None else QGuiApplication.instance()
    canvas = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(QColor("#0F0B09"))

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    bg_grad = QRadialGradient(width / 2.0, height * 0.48, max(width, height) * 0.75)
    bg_grad.setColorAt(0.0, QColor("#2A1F19"))
    bg_grad.setColorAt(0.45, QColor("#1A130F"))
    bg_grad.setColorAt(1.0, QColor("#0A0705"))
    painter.fillRect(QRectF(0, 0, width, height), bg_grad)

    widescreen_rays = (
        (-72, 18, 48),
        (-60, 28, 38),
        (-48, 38, 32),
        (-36, 48, 28),
        (-24, 38, 24),
        (-12, 28, 20),
        (0, 52, 26),
        (12, 28, 20),
        (24, 38, 24),
        (36, 48, 28),
        (48, 38, 32),
        (60, 28, 38),
        (72, 18, 48),
    )
    center_bottom = QPointF(width / 2.0, height * 0.92)
    for angle_deg, alpha, line_width in widescreen_rays:
        rad = math.radians(angle_deg)
        ray_color = (
            QColor(200, 155, 109, alpha) if abs(angle_deg) <= 36 else QColor(194, 102, 83, alpha)
        )
        painter.setPen(QPen(ray_color, line_width))
        target_x = center_bottom.x() + 1800 * math.sin(rad)
        target_y = center_bottom.y() - 1800 * math.cos(rad)
        painter.drawLine(center_bottom, QPointF(target_x, target_y))

    margin = 36.0
    frame_rect = QRectF(margin, margin, width - 2 * margin, height - 2 * margin)
    painter.setPen(QPen(QColor("#5C4335"), 3))
    painter.drawRect(frame_rect)

    inner_frame = QRectF(margin + 8, margin + 8, width - 2 * margin - 16, height - 2 * margin - 16)
    painter.setPen(QPen(QColor("#C89B6D"), 1.5))
    painter.drawRect(inner_frame)

    bracket_len = 54.0
    painter.setPen(QPen(QColor("#DFB589"), 4))
    painter.drawLine(QPointF(margin - 4, margin - 4), QPointF(margin - 4 + bracket_len, margin - 4))
    painter.drawLine(QPointF(margin - 4, margin - 4), QPointF(margin - 4, margin - 4 + bracket_len))
    painter.drawLine(
        QPointF(width - margin + 4, margin - 4),
        QPointF(width - margin + 4 - bracket_len, margin - 4),
    )
    painter.drawLine(
        QPointF(width - margin + 4, margin - 4),
        QPointF(width - margin + 4, margin - 4 + bracket_len),
    )
    painter.drawLine(
        QPointF(margin - 4, height - margin + 4),
        QPointF(margin - 4 + bracket_len, height - margin + 4),
    )
    painter.drawLine(
        QPointF(margin - 4, height - margin + 4),
        QPointF(margin - 4, height - margin + 4 - bracket_len),
    )
    painter.drawLine(
        QPointF(width - margin + 4, height - margin + 4),
        QPointF(width - margin + 4 - bracket_len, height - margin + 4),
    )
    painter.drawLine(
        QPointF(width - margin + 4, height - margin + 4),
        QPointF(width - margin + 4, height - margin + 4 - bracket_len),
    )

    emblem_pixels = min(740, int(round(height * 0.72)))
    emblem_image = render_freedom_wings_image(emblem_pixels)
    emblem_x = (width - emblem_pixels) / 2.0
    emblem_y = (height - emblem_pixels) / 2.0 - 15.0
    painter.drawImage(QPointF(emblem_x, emblem_y), emblem_image)

    loc_key = resolve_fullhd_locale(locale)
    top_title = _FULLHD_TITLES[loc_key]
    bottom_subtitle = _FULLHD_SUBTITLES[loc_key]

    top_banner_bg = QRectF(width / 2.0 - 520, margin + 14, 1040, 36)
    painter.fillRect(top_banner_bg, QColor("#16110E"))
    painter.setPen(QPen(QColor("#5C4335"), 1.5))
    painter.drawRect(top_banner_bg)

    painter.setPen(QColor("#F4EAD8"))
    title_font = painter.font()
    title_font.setFamily("Arial")
    title_font.setPointSize(13)
    title_font.setBold(True)
    title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
    painter.setFont(title_font)
    painter.drawText(
        top_banner_bg,
        Qt.AlignmentFlag.AlignCenter,
        top_title,
    )

    bottom_banner_bg = QRectF(width / 2.0 - 580, height - margin - 50, 1160, 36)
    painter.fillRect(bottom_banner_bg, QColor("#16110E"))
    painter.setPen(QPen(QColor("#5C4335"), 1.5))
    painter.drawRect(bottom_banner_bg)

    painter.setPen(QColor("#DFB589"))
    subtitle_font = painter.font()
    subtitle_font.setPointSize(10)
    subtitle_font.setBold(True)
    subtitle_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
    painter.setFont(subtitle_font)
    painter.drawText(
        bottom_banner_bg,
        Qt.AlignmentFlag.AlignCenter,
        bottom_subtitle,
    )

    painter.end()
    return canvas


def export_fullhd_wallpaper(
    destination_directory: Path | None = None,
    application: QGuiApplication | None = None,
    locale: str | None = None,
) -> Path:
    target_dir = destination_directory or (
        Path(__file__).resolve().parents[3] / "assets" / "images"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    loc_key = resolve_fullhd_locale(locale)
    fullhd_path = target_dir / "cibersoc_freedom_wings_fullhd.png"
    image = render_freedom_wings_fullhd_image(1920, 1080, application=application, locale=loc_key)
    image.save(str(fullhd_path))
    target_dir.joinpath(
        f"cibersoc_freedom_wings_fullhd_{loc_key.replace('-', '_')}.png"
    ).write_bytes(fullhd_path.read_bytes())
    return fullhd_path


def export_hd_emblem_image(destination_directory: Path | None = None) -> Path:
    target_dir = destination_directory or (
        Path(__file__).resolve().parents[3] / "assets" / "images"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    hd_path = target_dir / "cibersoc_emblem_hd.png"
    image = render_freedom_wings_image(1024)
    image.save(str(hd_path))
    return hd_path


def export_emblem_assets(destination_directory: Path | None = None) -> tuple[Path, Path]:
    target_dir = destination_directory or (Path(__file__).resolve().parents[3] / "assets" / "icons")
    target_dir.mkdir(parents=True, exist_ok=True)
    png_path = target_dir / "cibersoc_emblem.png"
    svg_path = target_dir / "cibersoc_freedom_wings.svg"

    image = render_freedom_wings_image(512)
    image.save(str(png_path))
    svg_path.write_text(generate_freedom_wings_svg(), encoding="utf-8")
    images_dir = target_dir.parent / "images"
    export_hd_emblem_image(images_dir)
    export_fullhd_wallpaper(images_dir, locale="pt")
    export_fullhd_wallpaper(images_dir, locale="en-GB")
    export_fullhd_wallpaper(images_dir, locale="es")
    export_fullhd_wallpaper(images_dir, locale="pt")
    return png_path, svg_path


def apply_macos_dock_icon(
    icon_path: Path | None = None,
    *,
    platform_name: str = sys.platform,
    appkit_path: str = "/System/Library/Frameworks/AppKit.framework/AppKit",
) -> bool:
    if platform_name != "darwin":
        return False
    target = icon_path or (
        Path(__file__).resolve().parents[3] / "assets" / "icons" / "cibersoc_emblem.png"
    )
    if not target.exists():
        target = export_emblem_assets()[0]
    try:
        import ctypes
        import ctypes.util

        objc_lib = ctypes.util.find_library("objc") or "/usr/lib/libobjc.dylib"
        objc = ctypes.cdll.LoadLibrary(objc_lib)
        ctypes.cdll.LoadLibrary(appkit_path)

        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]

        objc_msgSend = objc.objc_msgSend
        objc_msgSend.restype = ctypes.c_void_p
        objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        ns_app_cls = objc.objc_getClass(b"NSApplication")
        sel_shared_app = objc.sel_registerName(b"sharedApplication")
        ns_app = objc_msgSend(ns_app_cls, sel_shared_app)

        ns_image_cls = objc.objc_getClass(b"NSImage")
        sel_alloc = objc.sel_registerName(b"alloc")
        image_alloc = objc_msgSend(ns_image_cls, sel_alloc)

        ns_str_cls = objc.objc_getClass(b"NSString")
        sel_str_utf8 = objc.sel_registerName(b"stringWithUTF8String:")
        objc_msgSend_str = objc.objc_msgSend
        objc_msgSend_str.restype = ctypes.c_void_p
        objc_msgSend_str.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]

        path_bytes = str(target.resolve()).encode("utf-8")
        ns_path = objc_msgSend_str(ns_str_cls, sel_str_utf8, path_bytes)

        sel_init_path = objc.sel_registerName(b"initWithContentsOfFile:")
        objc_msgSend_init = objc.objc_msgSend
        objc_msgSend_init.restype = ctypes.c_void_p
        objc_msgSend_init.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        ns_image = objc_msgSend_init(image_alloc, sel_init_path, ns_path)
        if not ns_image:
            return False

        sel_set_icon = objc.sel_registerName(b"setApplicationIconImage:")
        objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        objc_msgSend(ns_app, sel_set_icon, ns_image)

        sel_dock_tile = objc.sel_registerName(b"dockTile")
        objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        dock_tile = objc_msgSend(ns_app, sel_dock_tile)
        sel_display = objc.sel_registerName(b"display")
        objc_msgSend(dock_tile, sel_display)
        return True
    except Exception:
        return False
