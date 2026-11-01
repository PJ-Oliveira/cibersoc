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

---

## 5. Empirical 30-Year Comparative Benchmark (3 Regimes × 3 Scenarios)

This section documents the canonical **30-year longitudinal experiment** (`seed=42`, `StochasticEventMatrix(seed=42)`, `150,700,000` citizens across 10 federated states, `150` unique sorted councillors with `0` consecutive re-selection) executed under **Common Random Numbers (CRN)** across all three institutional regimes — **(A) CIBERSOC Demarchy (`CIBERSOC_DEMARCHY`)**, **(B) Electoral Oligarchy (`ELECTORAL_OLIGARCHY`)**, and **(C) Bureaucratic Centralism (`BUREAUCRATIC_CENTRALISM`)** — and all three macro-structural scenarios.

### 5.1 Standalone Longitudinal Trajectory (`Macro = False`, Years 0 → 10 → 20 → 30)

| Scenario | Regime | HDI (Y0 → Y10 → Y20 → Y30) | Gini (Y0 → Y10 → Y20 → Y30) | Employment % (Y0 → Y10 → Y20 → Y30) | Regional HDI Gap (Y30) | $\sigma_{\text{HDI}}$ (Y30) | Corridor Flow (Y30) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | **A. Demarchy** | `0.7379 → 0.8237 → 0.8786 → 0.9110` | `0.4045 → 0.3318 → 0.2880 → 0.2630` | `78.75% → 85.05% → 87.60% → 91.23%` | `0.0538` | `0.0135` | `0.9814` |
| **`BASELINE`** | **B. Electoral Oligarchy** | `0.7379 → 0.7513 → 0.7656 → 0.7738` | `0.4045 → 0.4649 → 0.5013 → 0.5255` | `78.75% → 78.19% → 76.54% → 77.70%` | `0.1438` | `0.0431` | `0.6057` |
| **`BASELINE`** | **C. Bureaucratic Centralism** | `0.7379 → 0.7783 → 0.8028 → 0.8104` | `0.4045 → 0.3884 → 0.3761 → 0.3688` | `78.75% → 82.12% → 80.26% → 77.74%` | `0.0796` | `0.0212` | `0.7000` |
| **`ECOLOGICAL_STRESS`** | **A. Demarchy** | `0.7136 → 0.7971 → 0.8521 → 0.8833` | `0.4045 → 0.3340 → 0.2913 → 0.2678` | `76.93% → 82.69% → 85.08% → 88.23%` | `0.0631` | `0.0177` | `0.9044` |
| **`ECOLOGICAL_STRESS`** | **B. Electoral Oligarchy** | `0.7136 → 0.7235 → 0.7363 → 0.7412` | `0.4045 → 0.4673 → 0.5051 → 0.5312` | `76.93% → 75.36% → 73.22% → 73.59%` | `0.1684` | `0.0545` | `0.5285` |
| **`ECOLOGICAL_STRESS`** | **C. Bureaucratic Centralism** | `0.7136 → 0.7508 → 0.7744 → 0.7796` | `0.4045 → 0.3907 → 0.3795 → 0.3739` | `76.93% → 79.54% → 77.37% → 74.21%` | `0.0969` | `0.0289` | `0.6260` |
| **`POST_CRISIS_EQUALISATION`** | **A. Demarchy** | `0.7476 → 0.8432 → 0.8943 → 0.9201` | `0.5729 → 0.4029 → 0.3174 → 0.2754` | `64.02% → 78.70% → 84.88% → 89.76%` | `0.0386` | `0.0105` | `0.9679` |
| **`POST_CRISIS_EQUALISATION`** | **B. Electoral Oligarchy** | `0.7476 → 0.7561 → 0.7661 → 0.7705` | `0.5729 → 0.5719 → 0.5688 → 0.5678` | `64.02% → 69.28% → 71.06% → 73.93%` | `0.0884` | `0.0275` | `0.5551` |
| **`POST_CRISIS_EQUALISATION`** | **C. Bureaucratic Centralism** | `0.7476 → 0.7890 → 0.8089 → 0.8103` | `0.5729 → 0.4734 → 0.4189 → 0.3908` | `64.02% → 74.82% → 76.73% → 76.08%` | `0.0516` | `0.0146` | `0.6750` |

### 5.2 Active Plebiscitary Directive Sensitivity (`Macro = True`, UI Default, Year 30)

When the annual cybernetic plebiscite is coupled (`PLEB-FED-01: +5% Health`, `bonus = 0.015`, attenuated by concave frontier headroom `max(0, 0.965 - HDI)`), institutional pass-through (`macro_directive_multiplier`: `1.00` in A, `0.55` in C, `0.22` in B) widens the net welfare differential:

| Scenario (Year 30, `Macro = True`) | HDI (A. Demarchy) | HDI (B. Electoral) | HDI (C. Centralism) | Net Gain A vs B ($\Delta\text{HDI}$) | Net Gain A vs C ($\Delta\text{HDI}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | `0.9218` | `0.7798` | `0.8215` | **`+0.1420`** | **`+0.1003`** |
| **`ECOLOGICAL_STRESS`** | `0.8972` | `0.7481` | `0.7927` | **`+0.1491`** | **`+0.1045`** |
| **`POST_CRISIS_EQUALISATION`** | `0.9275` | `0.7755` | `0.8194` | **`+0.1520`** | **`+0.1081`** |

### 5.3 Structural Diagnosis of Observed Regime Differences

1. **Distributive Divergence and Regional $\sigma$-Convergence:** Under Demarchy (A), horizontal $1/N$ cooperative surplus sharing without rent capture (`rent_capture_drift = 0.0`) and inter-regional equalisation (`+0.032`) compress the `BASELINE` inter-state HDI gap from `0.3260` (Year 0) to `0.0538` (Year 30, $\sigma = 0.0135$), lifting mean productive corridor flow intensity to `0.9814`. Under Electoral Oligarchy (B), rent-capture drift (`+0.0022/yr`) and core-periphery polarization (`-0.005`) push Gini to `0.5255` and leave a `2.67×` wider regional gap (`0.1438`: `BR-SP = 0.788` vs `BR-AM = 0.702`).
2. **North–South Cleavage under `ECOLOGICAL_STRESS`:** Facing persistent climate shocks across northern tropical latitudes ($\text{lat} > -16^\circ$), demarchic council oversight mitigates `30%` of net shock damage, sustaining Northern/Northeastern mean HDI at `0.8637` vs `0.8899` in the South/Southeast (a North–South gap of just `0.0262`). Under Electoral Oligarchy (`6%` mitigation), Northern/Northeastern HDI stagnates at `0.6840` (`BR-AM = 0.617`, `BR-BA = 0.646`) vs `0.7571` in the South (`0.0731` North–South cleavage, `2.79×` wider).
3. **Long-Run Bureaucratic Ossification in Regime C:** Bureaucratic Centralism achieves strong initial mobilization during the first decade (`Employment` rises from `78.75%` to `82.12%` in `BASELINE` and `64.02%` to `74.82%` in `POST_CRISIS`), but suffers cumulative administrative ossification after Year 8 (`ossification_rate = 0.0018`), causing employment to erode from `82.12%` (Year 10) back down to `77.74%` (Year 30) in `BASELINE` while Gini plateaus at a stratified administrative floor (`0.3688–0.3908`).
4. **Post-Crisis Recovery (`POST_CRISIS_EQUALISATION`):** Starting from acute post-crisis inequality (`Gini = 0.5729`) and depressed employment (`64.02%`), Demarchy compresses Gini by **`-0.2975` points** (`0.2754`) and adds **`+25.74 pp`** of employment (`89.76%`), whereas Electoral Oligarchy remains locked in high-inequality hysteresis (`Gini = 0.5678`, moving only `-0.0051` across thirty years).
