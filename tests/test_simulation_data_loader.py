from __future__ import annotations

from pathlib import Path
import pytest

from cibersoc.util.load_simulation_data import (
    _checkpoint_path,
    clear_loader_caches,
    list_checkpoints,
    load_audit_snapshot,
    load_mesh,
    load_population,
    save_checkpoint,
)


def test_checkpoint_path_resolution(tmp_path: Path) -> None:
    root_path = _checkpoint_path(None)
    assert root_path.name == "simulation_data"
    scenario_path = _checkpoint_path("custom_scenario")
    assert scenario_path.name == "custom_scenario"
    assert scenario_path.parent.name == "checkpoints"
    custom_root_path = _checkpoint_path("alpha", data_root=tmp_path)
    assert custom_root_path == tmp_path / "checkpoints" / "alpha"


def test_load_population_default_and_custom() -> None:
    clear_loader_caches()
    default_pop = load_population(None)
    assert isinstance(default_pop, list)
    assert len(default_pop) > 0
    assert "citizen_id" in default_pop[0]

    custom_pop = load_population("scenario_10y_full_automation")
    assert isinstance(custom_pop, list)
    assert len(custom_pop) > 0


def test_load_mesh_default_and_custom() -> None:
    clear_loader_caches()
    default_mesh = load_mesh(None)
    assert isinstance(default_mesh, dict)
    assert "total_councils" in default_mesh

    custom_mesh = load_mesh("scenario_10y_full_automation")
    assert isinstance(custom_mesh, dict)
    assert custom_mesh["total_councils"] > 0


def test_load_audit_snapshot_existing_and_missing() -> None:
    clear_loader_caches()
    project_audit, clean_audit = load_audit_snapshot("scenario_10y_full_automation")
    assert project_audit is not None
    assert clean_audit is not None
    assert project_audit.get("is_self_contained") is True

    missing_project, missing_clean = load_audit_snapshot("scenario_climate_resilience_shock")
    assert missing_project is None
    assert missing_clean is None


def test_list_checkpoints_and_save_checkpoint(tmp_path: Path) -> None:
    checkpoints = list_checkpoints()
    assert "scenario_10y_full_automation" in checkpoints
    assert "scenario_climate_resilience_shock" in checkpoints

    missing_root = tmp_path / "missing_dir"
    assert list_checkpoints(data_root=missing_root) == []

    test_data_dir = tmp_path / "test_data"
    test_checkpoints = test_data_dir / "checkpoints"
    test_checkpoints.mkdir(parents=True)
    (test_checkpoints / "some_file.txt").write_text("not a dir", encoding="utf-8")
    (test_checkpoints / "empty_dir").mkdir()

    saved_named = save_checkpoint(
        name="  valid_scenario  ",
        population_payload=[{"citizen_id": "CID-0001"}],
        mesh_payload={"cycle": 1, "total_councils": 1},
        audit_payload={"project": {"is_self_contained": True}, "clean": {"is_compliant": True}},
        data_root=test_data_dir,
    )
    assert saved_named == test_checkpoints / "valid_scenario"
    assert list_checkpoints(data_root=test_data_dir) == ["valid_scenario"]
    assert load_population("valid_scenario", data_root=test_data_dir) == [{"citizen_id": "CID-0001"}]
    assert load_mesh("valid_scenario", data_root=test_data_dir)["total_councils"] == 1
    proj, clean = load_audit_snapshot("valid_scenario", data_root=test_data_dir)
    assert proj == {"is_self_contained": True}
    assert clean == {"is_compliant": True}

    saved_root = save_checkpoint(
        name=None,
        population_payload=[{"citizen_id": "CID-0002"}],
        mesh_payload={"cycle": 2, "total_councils": 5},
        audit_payload=None,
        data_root=test_data_dir,
    )
    assert saved_root == test_data_dir
    assert load_audit_snapshot(None, data_root=test_data_dir) == (None, None)

    with pytest.raises(ValueError, match="cannot be blank"):
        save_checkpoint(
            name="   ",
            population_payload=[],
            mesh_payload={},
            data_root=test_data_dir,
        )
