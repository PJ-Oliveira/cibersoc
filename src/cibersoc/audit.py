from __future__ import annotations

import ast
from dataclasses import dataclass
import io
from pathlib import Path
import tokenize

from .i18n.translator import LocalizationCatalog

_EXCLUDED_DIRECTORY_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "cibersoc.egg-info",
    }
)

_EXCLUDED_FILE_NAMES: frozenset[str] = frozenset(
    {
        "uv.lock",
        ".coverage",
        ".DS_Store",
    }
)

_TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".html",
        "",
    }
)

_REQUIRED_RELATIVE_PATHS: tuple[str, ...] = (
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "docs/demo/index.html",
    "docs/en-GB/01_THEORETICAL_FOUNDATIONS_AND_LOGICAL_DEFENCE.md",
    "docs/en-GB/02_UI_GUIDE.md",
    "docs/en-GB/03_SIMULATOR_OPERATION_MANUAL.md",
    "docs/en-GB/04_UNDER_THE_HOOD_MECHANICS.md",
    "docs/pt/01_FUNDAMENTOS_TEORICOS_E_DEFESA_LOGICA.md",
    "docs/pt/02_GUIA_DA_INTERFACE_UI.md",
    "docs/pt/03_MANUAL_DE_OPERACAO_DO_SIMULADOR.md",
    "docs/pt/04_MECANICA_SUBJACENTE_UNDER_THE_HOOD.md",
    "docs/es/01_FUNDAMENTOS_TEORICOS_Y_DEFENSA_LOGICA.md",
    "docs/es/02_GUIA_DE_LA_INTERFAZ_UI.md",
    "docs/es/03_MANUAL_DE_OPERACION_DEL_SIMULADOR.md",
    "docs/es/04_MECANICA_SUBYACENTE_UNDER_THE_HOOD.md",
)


@dataclass(frozen=True)
class ArchitecturalCharter:
    system_heading: str
    foundational_references: tuple[str, ...]
    structural_axioms: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CleanCodeAuditReport:
    python_files_scanned: int
    comment_violations: tuple[str, ...]
    docstring_violations: tuple[str, ...]
    is_compliant: bool


@dataclass(frozen=True)
class ProjectIntegrityReport:
    project_files_scanned: int
    documentation_locales_verified: tuple[str, ...]
    missing_required_paths: tuple[str, ...]
    is_self_contained: bool


def build_localized_architectural_charter(translator: LocalizationCatalog) -> ArchitecturalCharter:
    axioms = tuple(
        (
            translator.translate(f"charter.axiom_{index}_title"),
            translator.translate(f"charter.axiom_{index}_body"),
        )
        for index in range(1, 8)
    )
    return ArchitecturalCharter(
        system_heading=translator.translate("charter.system_heading"),
        foundational_references=(
            translator.translate("charter.reference_1"),
            translator.translate("charter.reference_2"),
        ),
        structural_axioms=axioms,
    )


def _collect_scannable_files(root_directory: Path) -> list[Path]:
    if not root_directory.exists():
        raise FileNotFoundError(f"Project directory not found for audit: {root_directory}")
    discovered_files: list[Path] = []
    for candidate_path in sorted(root_directory.rglob("*")):
        if any(part in _EXCLUDED_DIRECTORY_NAMES for part in candidate_path.parts):
            continue
        if not candidate_path.is_file() or candidate_path.name in _EXCLUDED_FILE_NAMES:
            continue
        if candidate_path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue
        discovered_files.append(candidate_path)
    return discovered_files


def _collect_docstring_nodes(parsed_tree: ast.AST, relative_label: str) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(parsed_tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                violations.append(f"{relative_label}:{node.body[0].lineno}")
    return violations


def audit_clean_code_compliance(project_root: Path) -> CleanCodeAuditReport:
    python_files = [
        path for path in _collect_scannable_files(project_root) if path.suffix.lower() == ".py"
    ]
    comment_violations: list[str] = []
    docstring_violations: list[str] = []

    for python_file in python_files:
        source_text = python_file.read_text(encoding="utf-8")
        relative_label = str(python_file.relative_to(project_root))
        token_stream = tokenize.generate_tokens(io.StringIO(source_text).readline)
        for token in token_stream:
            if token.type == tokenize.COMMENT:
                comment_violations.append(f"{relative_label}:{token.start[0]}")

        parsed_module = ast.parse(source_text, filename=relative_label)
        docstring_violations.extend(_collect_docstring_nodes(parsed_module, relative_label))

    return CleanCodeAuditReport(
        python_files_scanned=len(python_files),
        comment_violations=tuple(comment_violations),
        docstring_violations=tuple(docstring_violations),
        is_compliant=(len(comment_violations) == 0 and len(docstring_violations) == 0),
    )


def audit_project_integrity(project_root: Path) -> ProjectIntegrityReport:
    scanned_files = _collect_scannable_files(project_root)
    missing_paths: list[str] = []
    for relative_target in _REQUIRED_RELATIVE_PATHS:
        target_path = project_root / relative_target
        if not target_path.is_file() or target_path.stat().st_size == 0:
            missing_paths.append(relative_target)

    verified_locales: list[str] = []
    for locale_folder in ("en-GB", "pt", "es"):
        locale_prefix = f"docs/{locale_folder}/"
        if not any(missing.startswith(locale_prefix) for missing in missing_paths):
            verified_locales.append(locale_folder)

    return ProjectIntegrityReport(
        project_files_scanned=len(scanned_files),
        documentation_locales_verified=tuple(verified_locales),
        missing_required_paths=tuple(missing_paths),
        is_self_contained=(len(missing_paths) == 0),
    )
