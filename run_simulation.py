from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from cibersoc.cli import run_cli_entrypoint

if __name__ == "__main__":
    raise SystemExit(run_cli_entrypoint())
