from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from cibersoc.ui.icon import apply_macos_dock_icon
from cibersoc.ui.main_window import launch_application

if __name__ == "__main__":
    apply_macos_dock_icon()
    raise SystemExit(launch_application())
