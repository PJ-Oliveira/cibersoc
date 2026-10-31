# 03. Simulator Operation Manual

## 1. Provisioning the Environment and Launching the Simulator

The **CIBERSOC** simulator runs on **Python 3.12+** (the CI tests use CPython 3.14).  All third‑party packages are declared in `uv.lock` and installed with the ultra‑fast package manager **uv**.  This guarantees a deterministic, reproducible environment on macOS, Linux and Windows.

### 1.1 Clone and Create the Isolated Virtual Environment
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync                # creates .venv and installs the exact versions from uv.lock
```

> **Why `uv`?**  Unlike `pip`/`requirements.txt`, `uv` resolves the full dependency graph once, writes a lock file and never re‑downloads the same wheels.  This eliminates “works on my machine” surprises.

### 1.2 Running the Graphical UI (PySide6)
```bash
.venv/bin/python cibersoc_ui.py
# or, after the entry‑point script is installed:
.venv/bin/cibersoc-ui
```

When the UI starts it shows a **Checkpoint Selection Dialog**:
- **New** – start a fresh simulation.
- Any previously saved checkpoint (timestamped folder under `simulation_data/checkpoints/`).
Selecting a checkpoint loads the saved `population.json`, `mesh.json` and audit snapshot, so the user continues exactly where they left off.

### 1.3 Running the Trilingual CLI Simulator
```bash
.venv/bin/python run_simulation.py --locale en-GB   # English (UK)
.venv/bin/python run_simulation.py --locale pt      # Português
.venv/bin/python run_simulation.py --locale es      # Español
```
The CLI performs a full end‑to‑end deterministic run and prints a localized report containing:
- Population statistics
- Council composition per tier
- Results of the latest macro‑plebiscite
- Enterprise surplus distribution

## 2. Playbooks for Common Tasks

### Playbook A – Multi‑Cycle Sortition & Quarantine Verification
1. Open **Tab 2 – Sortition & Quarantine**.
2. Observe the cycle banner (`CYCLE #01`): `76` citizens serve across the 5 Councils (`20` Federal + `16` State + `20` Municipal + `10` Boqueirão + `10` Matriz), `In Quarantine = 0`, `Consecutive Re-Selection = 0`.
3. Press **Execute Next Sortition Cycle**.
   - `SimulationOrchestrator.execute_next_sortition_cycle` finalises current mandates, moves the `76` outgoing councillors into cryptographic quarantine, and draws `76` fresh councillors from the `244` remaining eligible citizens via **Commit‑Reveal SHA‑256** with Hamilton quota enforcement.
4. Verify that the summary badge shows `Ex‑Councillors Excluded from Urn (Quarantine) = 76` and `Consecutive Re-Selection = 0`, while every row of the **Proofs Table** displays `VERIFIED (SHA‑256)`.
5. Press **Execute Next Sortition Cycle** once more (Cycle `#03`): Cycle 1 councillors regain eligibility after 1 cooldown cycle, while Cycle 2 councillors enter quarantine, proving the strict zero consecutive re-selection invariant over unlimited cycles.

### Playbook B – Parameterising a Macro‑Plebiscite
1. Switch to **Tab 3 – Cybernetic Macro‑Allocation**.
2. Set the two ballot spin‑boxes:
   - `+5 % Education` → `750`
   - `+5 % Health` → `250`
3. Click **Tally Plebiscite & Broadcast Compulsory Directive**.
   - The winning directive flips to `EDU+5` (1000 audited ballots).
   - Cockshott’s continuous‑shift calculation updates the short‑run Harmony index to `‑2.50 %` (bias toward Education).
   - The **Input‑Output matrix table** updates the voted share, final demand `y*`, gross output `x`, embedded labour `H` and the harmony index for each sector.
4. Use the **Test Candidate Name on Ballot** and **Simulate Council Budget Deviation** buttons to confirm that illegal ballot contents and unauthorized budget overrides are instantly blocked.

### Playbook C – Enterprise Surplus Distribution & Ricardian Equalisation
1. Open **Tab 4 – CEO‑Free Enterprise & Civil Return**.
2. Adjust the **Period Operating Revenue** (`spn_revenue`) to a value in the range `120 000 – 500 000` (e.g. `220 000`).
3. Press **Execute Equal 1/N Distribution**.
   - `SocialistEnterprise.distribute_period_profit` deducts:
     * Audited material costs
     * Physical depreciation reserve
     * Macro‑social contribution
     * Capital‑endowment equalisation charge (the **Ricardian** component)
   - The net surplus is split **exactly** among all active workers using integer‑day rational arithmetic; any indivisible remainder (< 1 ¢ per worker) is carried forward.
   - Corporate retained profit is always `0.00` by construction.
4. Observe the **Worker Table** update: each worker’s payout is shown with two‑decimal precision and the total of all payouts equals the net surplus.

### Playbook D – Councillor Mandate Lifecycle, Inflation Indexing & Job Protection
1. In **Tab 4**, locate a worker (e.g. `CID‑0001`).
2. Click **Suspend Sorted Worker for Council Mandate**.
   - The worker’s status changes to `On Council Mandate`; the enterprise surplus is recalculated for the reduced active workforce.
3. Click **Apply Price Inflation (+0.50 %)** repeatedly.
   - Each click compounds the price‑index series and updates the stipend proportionally.
4. Click **Conclude Mandate & Reinstate (≥ 180 days)**.
   - The worker returns to `Reinstated Under Protected Stability`, the stipend is permanently adjusted for cumulative inflation, and a lock `stability_locked_until` is set 180 days into the future.
5. Click **Test Post‑Return Dismissal Attempt (Block)**.
   - The system raises `EmploymentStabilityLockError`, logs the block, and prevents the premature termination.

## 3. Programmatic Python API

Engineers can drive the simulator from pure Python scripts:
```python
from decimal import Decimal
from cibersoc.cybernetics import (
    CompressedSparseRowMatrix,
    solve_leontief_gross_output_gauss_seidel,
)
from cibersoc.enterprise import SocialistEnterprise, WorkerMember

# Build a tiny Leontief system
A = CompressedSparseRowMatrix.from_dense([[0.10, 0.20], [0.05, 0.15]])
final_demand = [120.0, 80.0]
output = solve_leontief_gross_output_gauss_seidel(A, final_demand)

# Create a socialist enterprise and distribute profit
plant = SocialistEnterprise('EMP‑01', 'Curitiba Precision Optics', 'IND‑OPT')
plant.register_worker(WorkerMember('W‑01', 'Alice', 'Optics Engineer', Decimal('4800.00'), 30))
plant.register_worker(WorkerMember('W‑02', 'Bruno', 'Assembly Technician', Decimal('4200.00'), 30))
receipt = plant.distribute_period_profit(
    period_label='2026‑M01',
    period_total_days=30,
    gross_revenue=Decimal('35000.00'),
    audited_material_costs=Decimal('10000.00'),
    physical_depreciation_reserve=Decimal('2000.00'),
    macro_social_contribution=Decimal('3000.00'),
    capital_endowment_equalisation_charge=Decimal('1000.00'),
)
print('Worker payouts:', receipt.payouts)
```
The API mirrors exactly what the UI does, but enables batch runs, experiments and integration with external data sources.

## 4. Automated Verification & 100 % Coverage QA

The repository ships a head‑less `pytest` + `pytest‑qt` + `coverage` test suite that enforces:
- **Zero missing documentation** for each language.
- **Clean‑Code compliance** (no stray `TODO`s, Pylint score ≥ 9.5, zero dead‑code warnings).
- **Full statement and branch coverage** (`--cov-fail-under=100`).
```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -v \
    --cov=cibersoc --cov-branch \
    --cov-report=term-missing --cov-fail-under=100
```
The suite also runs the **integrity audit** (`btn_run_audit`) programmatically to ensure that every source file contains no comments or docstrings, as required by the project’s Clean‑Code policy.
