# Contributing to CIBERSOC

Thank you for your interest in contributing to **CIBERSOC** (*Cybernetic and Demarchic Governance Architecture*).

CIBERSOC is a computational mechanism-design, social-choice, and economic-cybernetics research platform engineered for mathematical determinism, cryptographic auditability, and long-term maintainability. Every contribution must preserve the repository's **Five Architectural Invariants**.

---

## The Five Architectural Invariants

Continuous Integration (`.github/workflows/ci.yml`) validates every Pull Request across CPython `3.12`, `3.13`, and `3.14` against these five non-negotiable rules:

### 1. 100.00% Statement and Branch Coverage + Strict Static Typing
- `pytest` enforces `--cov=src/cibersoc --cov-branch --cov-fail-under=100`.
- `pyright` enforces strict type checking across `src/cibersoc` with `0 errors, 0 warnings, 0 informations`.
- Every function, conditional branch, validation guard, and UI interaction path must be covered deterministically.

### 2. Zero Mocks & Zero Monkeypatching Policy
- Synthetic test doubles and runtime attribute patching (`unittest.mock`, `MagicMock`, `AsyncMock`, `NonCallableMock`, `monkeypatch`, or ad-hoc `setattr` overrides on Qt classes) are **strictly prohibited** across `tests/conftest.py` and `tests/test_*.py`.
- Boundary interactions (modal dialogs, file-save paths, URL launchers, headless detection, render-widget fallbacks, and temporary checkpoint roots) must use explicit, typed **Dependency Injection** parameters on constructors and functions.
- Enforced automatically by `tests/test_integrity_and_i18n.py::test_zero_mocks_in_entire_test_suite`.

### 3. AST & Lexer Self-Documenting Clean Code Standard
- Every Python file in the repository (`src/`, `tests/`, and root entrypoints) must contain **0 comments (`#`)** and **0 docstrings (`"""`)**.
- **Engineering Rationale:** Inline comments frequently decay into misleading artefacts when algorithms evolve. Requiring zero comments forces domain types, function signatures, and local identifiers to be completely self-explanatory, while full mathematical proofs, complexity analyses, and operational playbooks are maintained in `docs/` and `README.md`.
- Enforced via Python's `tokenize` and `ast` modules in `audit_clean_code_compliance`.

### 4. Complete Trilingual Symmetry (`en-GB`, `pt`, `es`)
- All UI keys in `src/cibersoc/i18n/catalogues/{en_GB,pt,es}.json` must have identical key sets and symmetric format placeholders (`{variable}`).
- All four technical manuals in `docs/en-GB/`, `docs/pt/`, and `docs/es/` must be updated together whenever domain mechanics or UI workflows change.
- Enforced by `test_trilingual_localization_catalog_and_symmetry` and `audit_project_integrity`.

### 5. Analytical Vocabulary & Standalone Purity
- Runtime dependencies are restricted to `PySide6` and the Python standard library, with zero external network calls.
- All code and documentation must maintain precise mathematical, statistical, and computational terminology, avoiding speculative philosophical jargon.
- Enforced by `test_analytical_vocabulary_and_standalone_purity`.

---

## Local Development Workflow

### 1. Clone and Provision
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync --all-extras --all-groups
```

### 2. Run Static Type Analysis
```bash
uv run pyright src/cibersoc
```

### 3. Run the Full Headless Test & Coverage Suite
```bash
QT_QPA_PLATFORM=offscreen uv run pytest
```

### 4. Verify CLI and Desktop Entrypoints
```bash
uv run python run_simulation.py --locale pt
uv run python cibersoc_ui.py
```

---

## Pull Request Checklist

Before opening a Pull Request, verify that:
1. `uv run pyright src/cibersoc` reports `0 errors, 0 warnings, 0 informations`.
2. `QT_QPA_PLATFORM=offscreen uv run pytest` passes 100% of tests with `100.00%` statement and branch coverage.
3. All new localization keys and documentation updates are symmetrically present in `en-GB`, `pt`, and `es`.
4. Your commit description clearly explains the mathematical, algorithmic, or UI improvement introduced.
