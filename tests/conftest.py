from __future__ import annotations

import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def _stub_webengine():
    from PySide6.QtWidgets import QLabel
    from cibersoc.ui import simulation_view as sv

    original = sv._create_render_widget

    def _no_webengine(html_content: str) -> tuple:
        return QLabel("stub"), False

    sv._create_render_widget = _no_webengine
    yield
    sv._create_render_widget = original
