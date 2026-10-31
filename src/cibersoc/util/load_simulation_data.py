import json
from pathlib import Path
from functools import lru_cache

BASE_DATA_ROOT = Path(__file__).parents[2] / "simulation_data"


def _checkpoint_path(name: str | None = None) -> Path:
    if name:
        return BASE_DATA_ROOT / "checkpoints" / name
    return BASE_DATA_ROOT


@lru_cache(maxsize=3)
def load_population(checkpoint: str | None = None) -> list[dict]:
    pop_path = _checkpoint_path(checkpoint) / "population.json"
    with pop_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=3)
def load_mesh(checkpoint: str | None = None) -> dict:
    mesh_path = _checkpoint_path(checkpoint) / "mesh.json"
    with mesh_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=3)
def load_audit_snapshot(checkpoint: str | None = None) -> tuple[dict | None, dict | None]:
    audit_path = _checkpoint_path(checkpoint) / "audit_snapshot.json"
    if not audit_path.exists():
        return None, None
    with audit_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("project"), data.get("clean")


def list_checkpoints() -> list[str]:
    checkpoints_dir = BASE_DATA_ROOT / "checkpoints"
    if not checkpoints_dir.is_dir():
        return []
    return [
        p.name for p in checkpoints_dir.iterdir() if p.is_dir() and (p / "population.json").exists()
    ]
