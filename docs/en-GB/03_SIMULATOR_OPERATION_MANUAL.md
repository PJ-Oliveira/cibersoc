# 03. Simulator Operation Manual

## 1. Provisioning the Environment and Launching the Simulator

The **CIBERSOC** simulator runs on **Python 3.12, 3.13, and 3.14** across macOS, Linux, and Windows. All dependencies are pinned deterministically in [`uv.lock`](../../uv.lock) via **uv**.

### 1.1 Clone and Synchronise the Isolated Environment
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync --all-extras --all-groups
```

### 1.2 Launching the Desktop Graphical Client (PySide6)
```bash
uv run python cibersoc_ui.py
# or via console entrypoint:
uv run cibersoc-ui
```
Snapshots of the active population registry, federated council mesh, and integrity audit can be persisted at any point via **Save Snapshot (`btn_save_checkpoint`)** in Tab 2 or programmatically into `simulation_data/` and `simulation_data/checkpoints/`.

### 1.3 Running the Trilingual Deterministic CLI Simulator
```bash
uv run python run_simulation.py --locale en-GB
uv run python run_simulation.py --locale pt
uv run python run_simulation.py --locale es
```
The CLI executes a deterministic end-to-end orchestration and prints four localized report sections:
- **`[1]` Sortition, Federated Councils & Civic Enablement:** Active cycle proofs, quarantine counts, and periodic civic enablement summary.
- **`[2]` Cooperative Economy & Mandate Parity:** Net operating surplus, exact $1/N$ worker payout, `$0.00` corporate retention, and CPI-indexed mandate protection.
- **`[3]` Cybernetic Macro-Allocation & Plan Feedback:** Blinded plebiscite tally, embedded labour shares, Leontief gross output, short-run Harmony, and iterative clearing/carbon-ceiling feedback.
- **`[4]` Standalone Integrity & Audit Trail:** Clean Code AST/lexer verification, trilingual parity, and recent audit events.

---

## 2. Operational Playbooks

### Playbook A — Multi-Cycle Sortition, Quarantine & Civic Enablement
1. Open **Tab 2 (`Sortition & Quarantine`)**. Observe Cycle `#01`: `76` active councillors across the 5 councils (`20` Federal + `16` State + `20` Municipal + `10` Boqueirão + `10` Matriz), `Quarantined = 0`, `Consecutive Re-Selection = 0`.
2. Click **Execute Next Sortition Cycle (`btn_next_cycle`)**:
   - Outgoing Cycle `#01` councillors enter cryptographic quarantine; `76` fresh councillors are drawn from the `244` remaining eligible citizens via `Commit-Reveal SHA-256` + Hamilton quotas, keeping `Consecutive Re-Selection = 0` and every proof row `VERIFIED (SHA-256)`.
3. Click **Execute Civic Enablement Round (`btn_civic_round`)** to record deterministic 4-subject civic qualification scores while verifying automatic statutory exemption for citizens aged $\ge 60$.

### Playbook B — Macro-Plebiscite, Labour Shares & Carbon Feedback
1. Open **Tab 3 (`Cybernetic Macro-Allocation`)**, set `+5% Education` to `750` and `+5% Health` to `250`, and click **Tally Plebiscite & Broadcast Compulsory Directive (`btn_run_plebiscite`)**.
2. Observe the continuous Cockshott shift (`-2.50%`), exact embedded labour-share conservation in the Input–Output table, and incremented `↓Dir` counters on Tab 1.
3. Adjust the **Observed Clearing Ratio (`spn_clearing_ratio`)** and **Carbon Budget (`spn_carbon_budget`)**, then click **Iterate Plan (`btn_iterate_plan`)** to inspect iterative target adjustment and ecological carbon-ceiling enforcement.

### Playbook C — Horizontal $1/N$ Cooperative Surplus & Mandate Lifecycle
1. Open **Tab 4 (`CEO-Free Enterprise & Civil Return`)**, set **Period Operating Revenue (`spn_revenue`)** to `220000`, and click **Execute Equal 1/N Distribution (`btn_distribute_profit`)** to verify zero corporate retention (`$0.00`) and bounded sub-cent remainder carry-over.
2. Step through the four **Mandate Lifecycle** buttons for `CID-0001`: suspend for council service, apply `+0.50%` CPI stipend indexing, reinstate with a $\ge 180$-day lock, and verify that premature dismissal raises `EmploymentStabilityLockError`.

### Playbook D — National SEEM Counterfactual Regime Comparison (`A / B / C`)
1. Open **Tab 6 (`Nation Simulation — SEEM`)**, set **Years per Step (`spn_years_step`)** to `15`, and click **Advance**.
2. Switch **Institutional Regime (`cmb_regime`)** between **(A) CIBERSOC Demarchy**, **(B) Electoral Oligarchy**, and **(C) Bureaucratic Centralism**. Because all three trajectories share **Common Random Numbers (CRN)**, differences in national HDI, Gini inequality, and employment isolate pure institutional mechanism effects.

---

## 3. Programmatic Python API

```python
from decimal import Decimal
from cibersoc.cybernetics import (
    CompressedSparseRowMatrix,
    compute_embedded_labour_hours_jacobi,
    derive_final_demand_from_labour_shares,
    solve_leontief_gross_output_gauss_seidel,
)
from cibersoc.enterprise import SocialistEnterprise, WorkerMember

matrix_a = CompressedSparseRowMatrix.from_dense([[0.10, 0.20], [0.05, 0.15]])
labour_h = compute_embedded_labour_hours_jacobi(matrix_a, [0.40, 0.60])
final_demand = derive_final_demand_from_labour_shares([60.0, 40.0], labour_h, total_labour_budget=200.0)
gross_output = solve_leontief_gross_output_gauss_seidel(matrix_a, final_demand)

plant = SocialistEnterprise("EMP-01", "Curitiba Precision Optics", "IND-OPT")
plant.register_worker(WorkerMember("W-01", "Alice", "Optics Engineer", Decimal("4800.00"), 30))
plant.register_worker(WorkerMember("W-02", "Bruno", "Assembly Technician", Decimal("4200.00"), 30))
receipt = plant.distribute_period_profit(
    period_label="2026-M01",
    period_total_days=30,
    gross_revenue=Decimal("35000.00"),
    audited_material_costs=Decimal("10000.00"),
    physical_depreciation_reserve=Decimal("2000.00"),
    macro_social_contribution=Decimal("3000.00"),
    capital_endowment_equalisation_charge=Decimal("1000.00"),
)
print("Worker payouts:", receipt.payouts_by_worker)
```

---

## 4. Automated Verification & 100% Coverage QA

```bash
uv run pyright src/cibersoc
QT_QPA_PLATFORM=offscreen uv run pytest -v \
    --cov=src/cibersoc --cov-branch \
    --cov-report=term-missing --cov-fail-under=100
```
The verification suite enforces `0` static type errors, `100.00%` statement and branch coverage, `0` mocks or monkeypatches, `0` `#` comments or docstrings across all `.py` files, and full trilingual symmetry.
