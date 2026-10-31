from __future__ import annotations

from pathlib import Path
from cibersoc.util import load_simulation_data as loader_module
from cibersoc.util.load_simulation_data import (
    _checkpoint_path,
    list_checkpoints,
    load_audit_snapshot,
    load_mesh,
    load_population,
)


def test_checkpoint_path_resolution() -> None:
    root_path = _checkpoint_path(None)
    assert root_path.name == "simulation_data"
    scenario_path = _checkpoint_path("custom_scenario")
    assert scenario_path.name == "custom_scenario"
    assert scenario_path.parent.name == "checkpoints"


def test_load_population_default_and_custom() -> None:
    loader_module.load_population.cache_clear()
    default_pop = load_population(None)
    assert isinstance(default_pop, list)
    assert len(default_pop) > 0
    assert "citizen_id" in default_pop[0]

    custom_pop = load_population("scenario_10y_full_automation")
    assert isinstance(custom_pop, list)
    assert len(custom_pop) > 0


def test_load_mesh_default_and_custom() -> None:
    loader_module.load_mesh.cache_clear()
    default_mesh = load_mesh(None)
    assert isinstance(default_mesh, dict)
    assert "total_councils" in default_mesh

    custom_mesh = load_mesh("scenario_10y_full_automation")
    assert isinstance(custom_mesh, dict)
    assert custom_mesh["total_councils"] > 0


def test_load_audit_snapshot_existing_and_missing() -> None:
    loader_module.load_audit_snapshot.cache_clear()
    project_audit, clean_audit = load_audit_snapshot("scenario_10y_full_automation")
    assert project_audit is not None
    assert clean_audit is not None
    assert project_audit.get("is_self_contained") is True

    missing_project, missing_clean = load_audit_snapshot("scenario_climate_resilience_shock")
    assert missing_project is None
    assert missing_clean is None


def test_list_checkpoints_comprehensive(tmp_path: Path) -> None:
    checkpoints = list_checkpoints()
    assert "scenario_10y_full_automation" in checkpoints
    assert "scenario_climate_resilience_shock" in checkpoints

    original_root = loader_module.BASE_DATA_ROOT
    try:
        loader_module.BASE_DATA_ROOT = tmp_path / "missing_dir"
        assert list_checkpoints() == []

        test_data_dir = tmp_path / "test_data"
        test_checkpoints = test_data_dir / "checkpoints"
        test_checkpoints.mkdir(parents=True)
        (test_checkpoints / "some_file.txt").write_text("not a dir", encoding="utf-8")
        (test_checkpoints / "empty_dir").mkdir()
        valid_dir = test_checkpoints / "valid_scenario"
        valid_dir.mkdir()
        (valid_dir / "population.json").write_text("[]", encoding="utf-8")

        loader_module.BASE_DATA_ROOT = test_data_dir
        discovered = list_checkpoints()
        assert discovered == ["valid_scenario"]
    finally:
        loader_module.BASE_DATA_ROOT = original_root
