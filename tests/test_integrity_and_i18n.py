from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import pytest

from cibersoc.audit import (
    audit_clean_code_compliance,
    audit_project_integrity,
    build_localized_architectural_charter,
)
from cibersoc.i18n.translator import LocalizationCatalog, SupportedLocale


def test_trilingual_localization_catalog_and_symmetry(tmp_path: Path) -> None:
    catalog = LocalizationCatalog(SupportedLocale.ENGLISH_UK)
    assert catalog.active_locale == SupportedLocale.ENGLISH_UK
    assert "app.window_title" in catalog.available_keys
    assert "Labour" in catalog.translate("portfolio.LABOUR")
    assert "Defence" in catalog.translate("portfolio.DEFENCE")
    assert "#03" in catalog.translate("header.cycle_badge", cycle=3)

    observed_locales: list[SupportedLocale] = []
    catalog.register_locale_listener(observed_locales.append)

    catalog.switch_locale(SupportedLocale.ENGLISH_UK)
    assert observed_locales == []

    catalog.switch_locale(SupportedLocale.PORTUGUESE)
    assert catalog.active_locale == SupportedLocale.PORTUGUESE
    assert observed_locales == [SupportedLocale.PORTUGUESE]
    assert "Trabalho" in catalog.translate("portfolio.LABOUR")

    catalog.switch_locale(SupportedLocale.SPANISH)
    assert catalog.active_locale == SupportedLocale.SPANISH
    assert observed_locales == [SupportedLocale.PORTUGUESE, SupportedLocale.SPANISH]
    assert "Trabajo" in catalog.translate("portfolio.LABOUR")

    with pytest.raises(KeyError):
        catalog.translate("non_existent.key")

    asymmetric_dir = tmp_path / "catalogues"
    asymmetric_dir.mkdir()
    (asymmetric_dir / "en_GB.json").write_text(json.dumps({"alpha": "A", "beta": "B"}), encoding="utf-8")
    (asymmetric_dir / "pt.json").write_text(json.dumps({"alpha": "A"}), encoding="utf-8")
    (asymmetric_dir / "es.json").write_text(
        json.dumps({"alpha": "A", "beta": "B", "gamma": "G"}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        LocalizationCatalog(catalogue_directory=asymmetric_dir)


def test_real_cibersoc_clean_code_and_standalone_integrity() -> None:
    cibersoc_root = Path(__file__).resolve().parents[1]

    for locale in SupportedLocale:
        translator = LocalizationCatalog(locale)
        charter = build_localized_architectural_charter(translator)
        assert "CIBERSOC" in charter.system_heading
        assert len(charter.foundational_references) == 2
        assert len(charter.structural_axioms) == 7

    clean_report = audit_clean_code_compliance(cibersoc_root)
    assert clean_report.python_files_scanned >= 15
    assert clean_report.comment_violations == ()
    assert clean_report.docstring_violations == ()
    assert clean_report.is_compliant is True

    integrity_report = audit_project_integrity(cibersoc_root)
    assert integrity_report.project_files_scanned >= 30
    assert integrity_report.documentation_locales_verified == ("en-GB", "pt", "es")
    assert integrity_report.missing_required_paths == ()
    assert integrity_report.is_self_contained is True


def test_zero_mocks_in_entire_test_suite() -> None:
    tests_directory = Path(__file__).resolve().parent
    forbidden_mock_names = {"mock", "unittest.mock", "MagicMock", "AsyncMock", "NonCallableMock", "monkeypatch"}
    violations: list[str] = []

    for test_file in sorted(tests_directory.glob("test_*.py")):
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=test_file.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_mock_names or alias.name.endswith(".mock"):
                        violations.append(f"{test_file.name}:import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if module_name in forbidden_mock_names or module_name.endswith(".mock"):
                    violations.append(f"{test_file.name}:from:{module_name}")
                for alias in node.names:
                    if alias.name in forbidden_mock_names:
                        violations.append(f"{test_file.name}:symbol:{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.arg in forbidden_mock_names:
                        violations.append(f"{test_file.name}:{node.name}:arg:{arg.arg}")

    assert violations == []


def test_analytical_vocabulary_and_standalone_purity() -> None:
    cibersoc_root = Path(__file__).resolve().parents[1]
    excluded_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "cibersoc.egg-info"}
    excluded_files = {"uv.lock", ".coverage", ".DS_Store"}
    forbidden_stems = (
        "cib" + "com",
        "dial" + "et",
        "dial" + "éct",
        "dial" + "ect",
        "heg" + "el",
        "bela " + "alma",
        "alma " + "bella",
        "beautiful " + "soul",
        "sch" + "öne",
        "ontol" + "og",
        "teleol" + "og",
        "wert" + "kritik",
        "post-" + "festum",
    )
    pattern = re.compile("|".join(re.escape(stem) for stem in forbidden_stems), re.IGNORECASE)

    offending_locations: list[str] = []
    for path in sorted(cibersoc_root.rglob("*")):
        if any(part in excluded_dirs for part in path.parts):
            continue
        if not path.is_file() or path.name in excluded_files:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".toml", ".txt", ""}:
            continue
        if pattern.search(path.name):
            offending_locations.append(f"filename:{path.relative_to(cibersoc_root)}")
        content = path.read_text(encoding="utf-8")
        if pattern.search(content):
            offending_locations.append(str(path.relative_to(cibersoc_root)))

    assert offending_locations == []


def test_audit_edge_cases_and_synthetic_violations(tmp_path: Path) -> None:
    missing_directory = tmp_path / "non_existent_root"
    with pytest.raises(FileNotFoundError):
        audit_clean_code_compliance(missing_directory)

    with pytest.raises(FileNotFoundError):
        audit_project_integrity(missing_directory)

    synthetic_root = tmp_path / "synthetic_code"
    (synthetic_root / ".git").mkdir(parents=True)
    (synthetic_root / ".git" / "ignored.py").write_text("x = 1\n", encoding="utf-8")
    (synthetic_root / ".DS_Store").write_bytes(b"binary")
    (synthetic_root / "icon.png").write_bytes(b"\x89PNG")

    hash_mark = chr(35)
    triple_quote = chr(34) * 3
    violating_python_source = (
        f"{triple_quote}Forbidden module docstring.{triple_quote}\n"
        f"{hash_mark} Forbidden inline comment\n"
        "class SampleEntity:\n"
        f"    {triple_quote}Forbidden class docstring.{triple_quote}\n"
        "    def compute_value(self) -> int:\n"
        "        return 42\n"
    )
    (synthetic_root / "violating_module.py").write_text(violating_python_source, encoding="utf-8")
    (synthetic_root / "clean_module.py").write_text("value = 1\n", encoding="utf-8")

    violation_report = audit_clean_code_compliance(synthetic_root)
    assert violation_report.python_files_scanned == 2
    assert len(violation_report.comment_violations) == 1
    assert len(violation_report.docstring_violations) == 2
    assert violation_report.is_compliant is False

    incomplete_integrity = audit_project_integrity(synthetic_root)
    assert incomplete_integrity.is_self_contained is False
    assert incomplete_integrity.documentation_locales_verified == ()
    assert len(incomplete_integrity.missing_required_paths) >= 12
