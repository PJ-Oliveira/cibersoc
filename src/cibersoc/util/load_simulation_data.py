from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

BASE_DATA_ROOT = Path(__file__).resolve().parents[3] / "simulation_data"


def _checkpoint_path(name: str | None = None, data_root: Path | None = None) -> Path:
    root = data_root if data_root is not None else BASE_DATA_ROOT
    if name:
        return root / "checkpoints" / name
    return root


@lru_cache(maxsize=6)
def load_population(
    checkpoint: str | None = None, data_root: Path | None = None
) -> list[dict[str, Any]]:
    pop_path = _checkpoint_path(checkpoint, data_root) / "population.json"
    with pop_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=6)
def load_mesh(checkpoint: str | None = None, data_root: Path | None = None) -> dict[str, Any]:
    mesh_path = _checkpoint_path(checkpoint, data_root) / "mesh.json"
    with mesh_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=6)
def load_audit_snapshot(
    checkpoint: str | None = None, data_root: Path | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    audit_path = _checkpoint_path(checkpoint, data_root) / "audit_snapshot.json"
    if not audit_path.exists():
        return None, None
    with audit_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("project"), data.get("clean")


def list_checkpoints(data_root: Path | None = None) -> list[str]:
    checkpoints_dir = (data_root if data_root is not None else BASE_DATA_ROOT) / "checkpoints"
    if not checkpoints_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in checkpoints_dir.iterdir()
        if path.is_dir() and (path / "population.json").exists()
    )


def clear_loader_caches() -> None:
    load_population.cache_clear()
    load_mesh.cache_clear()
    load_audit_snapshot.cache_clear()


def save_checkpoint(
    name: str | None,
    population_payload: list[dict[str, Any]],
    mesh_payload: dict[str, Any],
    audit_payload: dict[str, Any] | None = None,
    data_root: Path | None = None,
) -> Path:
    if name is not None and not name.strip():
        raise ValueError("Checkpoint name cannot be blank when provided.")
    clean_name = name.strip() if name is not None else None
    target_dir = _checkpoint_path(clean_name, data_root)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "population.json").write_text(
        json.dumps(population_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (target_dir / "mesh.json").write_text(
        json.dumps(mesh_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if audit_payload is not None:
        (target_dir / "audit_snapshot.json").write_text(
            json.dumps(audit_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    clear_loader_caches()
    return target_dir
