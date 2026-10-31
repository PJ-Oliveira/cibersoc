# Contributing to CIBERSOC

Thank you for your interest in contributing to **CIBERSOC** (*Permanent Cybernetic and Demarchic Socialism*).

CIBERSOC is both an ideological and computational platform engineered with extreme scientific and software rigor. To preserve mathematical determinism, cryptographic verifiability, and absolute maintainability, all contributions must strictly adhere to the project's **Five Architectural Invariants**.

---

## The Five Architectural Invariants

Every Pull Request submitted to CIBERSOC must pass automated continuous integration verifying these five rules:

### 1. 100.00% Statement and Branch Coverage
* The test suite enforces `--cov-fail-under=100` across all production modules in `src/cibersoc`.
* Every new function, method, condition, and branch must have deterministic test coverage.
* Run the test suite locally before submitting:
  ```bash
  uv run pytest
  ```

### 2. Strict Zero-Mocks Policy
* Synthetic doubles, stubs, and mock frameworks (`unittest.mock`, `MagicMock`, `AsyncMock`, `NonCallableMock`, `monkeypatch`) are **strictly prohibited** in the entire test suite.
* Tests must exercise real domain models, real Leontief matrices, real sortition engines, and real PySide6 event loops.
* This invariant is automatically checked by `tests/test_integrity_and_i18n.py::test_zero_mocks_in_entire_test_suite`.

### 3. Production Clean Code Standard
* Production code in `src/cibersoc/**/*.py` must contain **0 comments (`#`)** and **0 docstrings (`"""`)**.
* Code must be completely self-documenting through expressive variable naming, explicit typing, and transparent control flow.
* Architectural rationale and theoretical formulations belong exclusively in `docs/` and `README.md`.
* Enforced by `audit_clean_code_compliance`.

### 4. Trilingual Symmetry
* The system operates under complete parity across **English (UK)** (`en-GB`), **Português** (`pt`), and **Español** (`es`).
* Any new translation key added to `src/cibersoc/i18n/catalogues/en_GB.json` must be symmetrically translated and added to `pt.json` and `es.json`.
* Enforced by `test_trilingual_localization_catalog_and_symmetry`.

### 5. Analytical Vocabulary & Standalone Purity
* The system is self-contained and avoids external runtime dependencies beyond PySide6 and pure Python standard library modules.
* Code and documentation must avoid theological and speculative jargon, maintaining empirical, cybernetic, and mathematical precision.

---

## Local Development Workflow

### 1. Clone and Setup
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync
```

### 2. Type Checking
CIBERSOC enforces strict static typing with Pyright:
```bash
uv run pyright src/cibersoc
```
All code must pass with `0 errors, 0 warnings, 0 informations`.

### 3. Running the Test Suite
```bash
uv run pytest
```
All tests must pass with 100.00% statement and branch coverage.

### 4. Running the Desktop Application
```bash
.venv/bin/python cibersoc_ui.py
```

---

## Submitting a Pull Request

Before pushing your branch or opening a Pull Request:
1. Ensure `uv run pyright src/cibersoc` reports 0 errors.
2. Ensure `uv run pytest` passes 100% of tests with 100.00% coverage.
3. Ensure `uv run pytest tests/test_integrity_and_i18n.py --no-cov` reports all audits passed.
4. Provide a clear and concise description of the change, linking any relevant issues.
