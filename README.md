# CIBERSOC — Cybernetic and Demarchic Governance Architecture (v2.1.0)

<p align="center">
  <img src="assets/images/cibersoc_emblem_hd.png" alt="CIBERSOC Wings of Freedom Emblem" width="260"/>
</p>

<p align="center">
  <a href="https://github.com/PJ-Oliveira/cibersoc/actions/workflows/ci.yml"><img src="https://github.com/PJ-Oliveira/cibersoc/actions/workflows/ci.yml/badge.svg" alt="CI & Standalone Integrity"/></a>
  <a href="#prerequisites--installation"><img src="https://img.shields.io/badge/Python-3.12%20%7C%203.13%20%7C%203.14-blue.svg" alt="Python 3.12-3.14"/></a>
  <a href="#running-the-desktop-ui-pyside6"><img src="https://img.shields.io/badge/UI-PySide6%20Qt%206.12-darkgreen.svg" alt="UI Framework"/></a>
  <a href="#running-the-test-suite-100-coverage"><img src="https://img.shields.io/badge/Coverage-100.00%25%20Stmt%20%2B%20Branch-brightgreen.svg" alt="Coverage"/></a>
  <a href="#federated-council-proportionality-engine"><img src="https://img.shields.io/badge/Mechanism-Stratified%20Sortition-amber.svg" alt="Sortition"/></a>
  <a href="#technical-documentation--explanations-docs"><img src="https://img.shields.io/badge/Cybernetics-Leontief--Cockshott-orange.svg" alt="Cybernetics"/></a>
  <a href="https://pj-oliveira.github.io/cibersoc/"><img src="https://img.shields.io/badge/GitHub%20Pages-Live%20Web%20Lab-informational.svg" alt="Live GitHub Pages Web Lab"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-lightgrey.svg" alt="MIT License"/></a>
</p>

> **Methodological & Scientific Scope Note**  
> **CIBERSOC** is an open-source **computational mechanism-design, social-choice, and economic-cybernetics research laboratory**. Rather than relying on electoral competition or top-down state command, it models a **permanent, horizontal, non-electoral governance architecture** where public councils are selected by audited statistical lottery (**sortition**), productive enterprises operate as **CEO-free $1/N$ cooperatives**, and citizens vote directly on **macroeconomic budget shares** rather than politicians. Every institutional rule is encoded as deterministic, cryptographically verifiable software and benchmarked over multi-decade horizons against rival regimes under identical historical shocks (**Common Random Numbers — `CRN`**). It is strictly an academic, civic-engineering, and mathematical modeling platform.

### Foundational Concepts — Intuitive & Concrete Guide

Every technical expression in CIBERSOC maps to a concrete, everyday institutional problem:

| Technical Expression | Concrete Intuition (What It Means in Practice) | Where It Runs in Code |
| :--- | :--- | :--- |
| **Aristotle's Sortition vs. Elections** (*Demarchy*) | Elections act as wealth-weighted filters (campaigns, media, party donors) that create a career political class; **sortition** draws ordinary citizens by audited lottery across demographic/occupational quotas, like a national jury with mandatory post-term quarantine. | [`sortition.py`](src/cibersoc/sortition.py) |
| **Hurwicz–Maskin Mechanism Design** | Instead of hoping rulers are virtuous, **reverse-engineer the rules of the game** (`0` re-selection, `voting_weight = 1`, `0` CEOs, `$0.00` retained profit) so no actor can capture power or hoard surplus even if self-interested. | [`councils.py`](src/cibersoc/councils.py), [`enterprise.py`](src/cibersoc/enterprise.py) |
| **Arrow's Impossibility vs. Black's Median Voter** | Multi-candidate elections suffer cycling paradoxes and strategic manipulation (Arrow). Voting on a **continuous 1D budget slider** (e.g. `% Health` vs `% Education`) guarantees a single, stable median outcome where every ballot shifts the result (Black). | [`cybernetics.py`](src/cibersoc/cybernetics.py) |
| **Hoeffding Pivotal-Ballot & Sortition Bound** | In a 158M-voter election with a 1% lead, the chance your single vote changes the ruler is $\le 10^{-13,723}$ (virtually zero); the **same theorem** proves a sorted chamber of $n$ citizens converges exponentially to the true public median. | [`docs/en-GB/01_*`](docs/en-GB/01_THEORETICAL_FOUNDATIONS_AND_LOGICAL_DEFENCE.md) |
| **Sparse Leontief Input–Output (`CSR`)** | Each product directly uses only ~20–100 physical inputs (steel, electricity, grain), leaving $>99.9\%$ of an economy's matrix zero. Storing only non-zero links (`CSR`) balances millions of supply chains (`x = (I - A)^(-1) y*`) in seconds. | [`cybernetics.py`](src/cibersoc/cybernetics.py) |
| **Cockshott–Cottrell Labour-Time (`H`), `p/v` & Harmony** | `H` counts total direct + indirect work hours needed per unit; `p/v` compares real consumer demand to labour cost (`> 1` shortage -> expand output; `< 1` surplus -> scale back); **Harmony** smooths short-run factory bottlenecks without recessions. | [`cybernetics.py`](src/cibersoc/cybernetics.py) |
| **Usufruct Bitmask `[1,0,0,0]` & Rational $1/N$** | Workers collectively **use** (`1`) public machinery, but nobody can **sell** (`0`), **buy** (`0`), or **inherit** (`0`) an enterprise. 100% of net surplus is split equally per worked day via exact integer-cent fractions (`Decimal` + `gcd`). | [`enterprise.py`](src/cibersoc/enterprise.py) |
| **Commit-Reveal `SHA-256`, Merkle & Hamilton Quotas** | Independent sources lock secret hashes before revealing them so **no one can rig the lottery seed** (`Commit-Reveal`), `Merkle` hashes prove the voter roll wasn't altered, and `Hamilton` rounds seat quotas to exact whole numbers fairly. | [`sortition.py`](src/cibersoc/sortition.py) |
| **Common Random Numbers (`CRN`) Counterfactuals** | Runs **(A) CIBERSOC**, **(B) Electoral Capitalism**, and **(C) State Bureaucracy** through the **exact same yearly droughts, booms, and crises**, proving empirically which institution performs best without luck bias. | [`simulation/engine.py`](src/cibersoc/simulation/engine.py) |

---

## 1. Overview & Formal Institutional Mechanisms

**CIBERSOC** implements a self-contained, auditable computational model of **Cybernetic and Demarchic Governance** in pure Python (`3.12–3.14`), paired with an accessible **PySide6 (Qt 6.12)** desktop client, a zero-install interactive HTML5/WebCrypto browser laboratory ([`docs/demo/index.html`](docs/demo/index.html)), and complete trilingual parity (**English (UK)**, **Português**, and **Español**).

The platform formalises and verifies six interlocking institutional mechanisms:
- **Stratified Cryptographic Sortition (Zero Elections, Zero Party Apparatus):** Deliberative seats across sectoral, municipal, state, and federal councils are staffed exclusively through unbiased probability sampling (`Commit-Reveal SHA-256` multi-source entropy beacons + `HMAC-SHA256` rejection-sampled DRBG + exact integer Hamilton stratum quotas), paired with compulsory post-mandate quarantine (`0` consecutive re-selection).
- **Acéphalous Federated Council Mesh:** Unitary executive offices (*President*, *Prime Minister*, *Governor*, *Mayor*) are structurally absent. Councils are coordinated exclusively by a sorted logistical **Secretary-General** (`voting_weight = 1`, zero veto power, zero unilateral decree authority), while odd-numbered **Popular Jury** benches rotate alternates deterministically per case via cryptographic DRBG.
- **Horizontal Cooperative Enterprises (Zero CEOs, Exact $1/N$ Surplus Sharing):** Productive units operate under non-alienable usufruct rights `[Use=1, Sell=0, Buy=0, Inherit=0]` (`state_code = 8`). Executive hierarchy is barred; 100% of net period operating surplus (after audited materials, physical depreciation, macro-social contribution, and Ricardian capital-intensity equalisation) is distributed equally ($1/N$) per worked integer day using exact fixed-point rational reduction (`Decimal` + `math.gcd`) with `$0.00` corporate retention.
- **Closed Cybernetic Macro-Planning & Labour-Time Conservation:** Citizens vote exclusively on quantitative macroeconomic resource allocations (never on personal candidates). Ballots map into Embedded Labour Shares satisfying $s_j = 100 \cdot \frac{H_j y_j^*}{\sum_k H_k y_k^*}$, solved through Compressed Sparse Row (`CSR`) Gauss–Seidel Leontief solvers, Jacobi embedded-labour vectors, Cockshott short-run Harmony capacity relaxation, and iterative ecological carbon-boundary controls.
- **Civilian Multi-Signature Control over Defence & Public Security:** Federal Defence chambers exclude military personnel from political seats and require cryptographic multi-signature authorisation ($\ge \lceil 2/3 \cdot |D| \rceil$ sorted civilian councillors + civilian minister + Secretary-General certification) before any strategic order executes.
- **CPI-Indexed Stipend Parity, Civic Enablement & Post-Mandate Stability:** Sorted councillors receive inflation-indexed stipends matching their prior civil earnings and return to their original workplace under a statutory $\ge 180$-day anti-dismissal lock, complemented by a periodic **Civic Enablement Exam** scheduler with automatic statutory exemption from age 60.

---

## 2. Live GitHub Pages & Zero-Install Browser Laboratory

- **Live Online Web Lab:** [**https://pj-oliveira.github.io/cibersoc/**](https://pj-oliveira.github.io/cibersoc/) *(automatically deployed via [`.github/workflows/pages.yml`](.github/workflows/pages.yml))*
- **Offline Local File:** Open [`docs/demo/index.html`](docs/demo/index.html) directly in any modern browser without Python or Qt installed.

The standalone single-file laboratory includes full `en-GB` / `pt` / `es` live translation and four interactive modules:
1. **SEEM National Counterfactual Simulator (Brazil, 150.7M Citizens):** Interactive Canvas map of 10 Brazilian macro-regional poles with input-output corridors and live **Common-Random-Numbers (CRN)** comparison across **(A) CIBERSOC Demarchy**, **(B) Electoral Oligarchy**, and **(C) Bureaucratic Centralism**.
2. **Hoeffding Pivotal-Ballot & WebCrypto Sortition Verifier:** Live lower-tail Hoeffding bound calculator alongside real browser `crypto.subtle.digest('SHA-256', ...)` Commit-Reveal + Hamilton quota sortition.
3. **Leontief–Cockshott Cybernetic Planner:** Real-time sparse solver verifying $\mathbf{H}\cdot\mathbf{y}^* \equiv \mathbf{l}\cdot\mathbf{x}$, short-run Harmony relaxation, and ecological carbon-ceiling feedback.
4. **Horizontal $1/N$ Cooperative Ledger:** Exact integer-day rational surplus division with Ricardian capital-endowment equalisation and `$0.00` corporate retention.

---

## 3. Visual Identity: "Wings of Freedom" Constructivist Espresso Design

The visual system unites geometric **"Wings of Freedom"** heraldry with **Constructivist Espresso (`DarkCappuccinoPalette`)** ergonomics:
- **Vector Emblem & Multi-Resolution Icon:** [`assets/icons/cibersoc_freedom_wings.svg`](assets/icons/cibersoc_freedom_wings.svg) and [`assets/icons/cibersoc_emblem.png`](assets/icons/cibersoc_emblem.png) combine golden crema and roasted terracotta wings, an industrial cybernetic planning gear, broken chains at the base, and an apex star across window titles and the macOS Dock.
- **WCAG AA Low-Fatigue Palette:** Deep espresso (`#16110E`), dark roast panels (`#1F1814`), moka cards (`#29201B`), crema amber highlights (`#C89B6D`), sage green directives (`#84A97C`), terracotta constitutional alerts (`#C26653`), and high-contrast ivory typography (`#F4EAD8`).
- **Accessible Responsive Typography:** Ships with bundled **Atkinson Hyperlegible** fonts, guaranteed **12 pt minimum** font size, dynamic scaling up to **32 pt** (`A−`, `A+`, `Aa` or `Ctrl++` / `Ctrl+-` / `Ctrl+0`), and zero horizontal overflow down to `680×500` viewports.

---

## 4. Federated Council Proportionality Engine

Council seat counts follow a strictly proportional mathematical rule eliminating arbitrary assembly sizing:
- **Sectoral Base (Neighbourhoods):** **10 seats** per sector (`CONS-SET-BOQUEIRAO`: 10, `CONS-SET-MATRIZ`: 10), staffing all ministerial chambers and the logistical Secretary-General.
- **Municipal Council (`CONS-MUN-CURITIBA`):** **20 seats**, strictly $1:1$ proportional to the aggregate of subordinate sectoral councils:
  $$N_{\text{municipal}} = 1.0 \times \sum_{s \in \mathcal{S}(M)} N(s) = 10 + 10 = 20$$
  Preserves agile small-group deliberation while guaranteeing a 4-member Justice chamber capable of seating odd-numbered 3-juror **Popular Jury** benches with deterministic per-case alternate rotation.
- **State Council (`CONS-EST-PARANA`):** **16 seats** via $4:5$ regional consolidation.
- **Federal Council (`CONS-FED-BRASIL`):** **20 seats**, maintaining national inter-council coordination and 100% civilian supremacy over the Ministry of Defence.
- **Active Cohort & Quarantine Invariant:** **76 active councillors** across the 5 federated councils (`320` local registry citizens; Cycle `#01`: `76` serving, `0` quarantined; Cycle `#02`: `76` quarantined, `244` eligible, `76` newly sorted, `0` consecutive re-selection).

---

## 5. Empirical 30-Year Benchmark (`SEEM` 3×3): Why Permanent Sortition + $1/N$ Outperforms Both Elections and State Bureaucracy

Running all **3 regimes** across all **3 scenarios** over **30 continuous years** (`seed=42`, `150.7M` citizens across 10 Brazilian poles, identical `CRN` climate/economic shocks; verified in [`TestThirtyYearThreeByThreeBenchmark`](tests/test_simulation.py)) isolates the causal impact of horizontal sortition + $1/N$ cooperatives:

| Scenario (Year 30, `seed=42`) | **A. CIBERSOC (Sortition + $1/N$)** | **C. State Bureaucracy (Top-Down)** | **B. Electoral Capitalism (Parties + CEOs)** | CIBERSOC Structural Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **1. Baseline** *(Macro Plebiscite On / Off)* | **HDI `0.922`** (`0.911`) · **Gini `0.263`** · **Emp `91.2%`** | HDI `0.822` (`0.810`) · Gini `0.369` · Emp `77.7%` | HDI `0.780` (`0.774`) · Gini `0.526` · Emp `77.7%` | **`+0.142` HDI** & **`-0.263` Gini** vs. Elections; **`+0.100` HDI** vs. Bureaucracy |
| **2. Ecological Stress** *(Tropical Drought Bias)* | **HDI `0.897`** (`0.883`) · **Gini `0.268`** · **Emp `88.2%`** | HDI `0.793` (`0.780`) · Gini `0.374` · Emp `74.2%` | HDI `0.748` (`0.741`) · Gini `0.531` · Emp `73.6%` | North/NE gap only **`0.026`** in **A** vs. **`0.073`** in **B** (`2.79×` worse tropical abandonment) |
| **3. Post-Crisis** *(Initial Gini `0.573`, Emp `64.0%`)* | **HDI `0.928`** (`0.920`) · **Gini `0.275`** · **Emp `89.8%`** | HDI `0.819` (`0.810`) · Gini `0.391` · Emp `76.1%` | HDI `0.776` (`0.771`) · Gini `0.568` · Emp `73.9%` | Cuts Gini by **`-0.298`** (`+25.7 pp` jobs), while **B** freezes post-crisis oligarchy (`-0.005`) |

Four concrete empirical lessons emerge directly in favour of **CIBERSOC (`A`)**:
1. **Defeating Oligarchic Rent Capture (`A` vs. `B`):** Under Electoral Capitalism (`B`), CEO/shareholder retention and capital-filtered elections push Gini upward (`0.453 -> 0.526` in Baseline) and stall post-crisis recovery (`0.573 -> 0.568`). Equal $1/N$ cooperative surplus + public investment plebiscites compress Gini to **`0.263–0.275`** while raising employment above **`88%–91%`**.
2. **Eliminating Post-Year-8 Bureaucratic Ossification (`A` vs. `C`):** Top-down State Bureaucracy (`C`) mobilises briskly in Years 1–8 (`Emp` peaks at `82.1%` around Year 10), then **ossifies** as unrotated ministries hoard information and privilege (`Emp` falls back to `77.7%`, `Gini` stagnates at `0.369`). Mandatory **1-cycle sortition + quarantine** (`2,100` unique regional citizens drawn across 30 years with `0` repeats) prevents a permanent ruling stratum from ever forming.
3. **Preventing Regional & Climate Cleavage:** Under `ECOLOGICAL_STRESS`, market capital flees drought-hit Northern/Northeastern poles (`Amazonas` drops to `0.617` HDI, North–South gap widens `2.79×` vs. `A`), whereas inter-regional Leontief trade corridors (`Flow 0.981` vs. `0.606` in `B`) keep tropical poles at **`0.864` HDI**.
4. **Measurable Return on Direct Allocative Democracy:** Enabling binding popular budget plebiscites (`Macro=True`) adds a further **`+0.007` to `+0.014` national HDI** across all scenarios without adding a single career politician.

---

## 6. Desktop Workspaces & Visual Preview

The PySide6 desktop interface provides 6 integrated workspaces (`Ctrl+1` … `Ctrl+6`):
1. **Federated Mesh & Ministries:** Interactive 4-tier council topology, demand escalation, logistical Secretary-General authentication, Popular Jury adjudication, Public Security oversight, and Civilian Multi-Sig Defence gates.
2. **Sortition, Quarantine & Civic Enablement:** Multi-source SHA-256 Commit-Reveal sortition, Merkle/Hamilton cryptographic proof inspector, periodic Civic Enablement rounds (with statutory age-60 exemption), and snapshot persistence.
3. **Cybernetic Macro-Allocation:** Coercion-resistant blinded plebiscites, CSR Leontief + Jacobi embedded-labour solver, Cockshott Harmony relaxation, and iterative clearing/carbon-ceiling feedback.
4. **CEO-Free Enterprise & Civil Return:** Exact $1/N$ rational surplus ledger, horizontal `[1,0,0,0]` usufruct checks, CPI-indexed mandate stipends, and $\ge 180$-day post-return job protection.
5. **Axioms, Integrity & Documentation:** Trilingual charter, FullHD wallpaper exporter, live repository scanner auditing AST/tokenize Clean Code compliance and standalone completeness, and native Markdown + Mermaid diagram reader for all trilingual manuals.
6. **Nation Simulation — 3D SEEM Engine:** Interactive 3D WebGL/Three.js + QPainter simulation of **150,700,000 citizens** across 10 Brazilian poles with continental vector boundaries, 3D input-output trade arcs, and a live **3-Regime Side-by-Side Scoreboard (`A`, `C`, `B`)** under Common Random Numbers.

<p align="center">
  <b>Nation Simulation — 3D SEEM Engine & 3-Regime Live Scoreboard (Tab 6)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab6_nation_simulation_3d.png" alt="CIBERSOC 3D Nation Simulation SEEM Engine" width="95%"/>
</p>

<p align="center">
  <b>Federated Mesh, Popular Juries & Civilian Multi-Sig Defence (Tab 1)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab1_councils_mesh.png" alt="CIBERSOC Federated Mesh Ministries" width="95%"/>
</p>

<p align="center">
  <b>Stratified Sortition, Quarantine & Civic Enablement (Tab 2)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab2_sortition_and_quarantine.png" alt="CIBERSOC Sortition and Quarantine" width="95%"/>
</p>

<p align="center">
  <b>Cybernetic Macro-Allocation, Labour Shares & Plan Feedback (Tab 3)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab3_cybernetic_planning.png" alt="CIBERSOC Cybernetic Planning Matrix" width="95%"/>
</p>

<p align="center">
  <b>Horizontal Cooperative Enterprise & Mandate Protection (Tab 4)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab4_cooperative_enterprise.png" alt="CIBERSOC Cooperative Enterprise" width="95%"/>
</p>

<p align="center">
  <b>Architectural Charter & Standalone Integrity Audit (Tab 5)</b><br/>
  <img src="assets/images/screenshots/cibersoc_tab5_integrity_and_charter.png" alt="CIBERSOC Charter and Integrity Audit" width="95%"/>
</p>

---

## 7. Technical Documentation & Explanations (`docs/`)

All theoretical derivations, mathematical proofs, UI guides, and operational playbooks are maintained under strict trilingual symmetry:

### 🇧🇷 Português (`docs/pt/`)
- [**01. Fundamentos Teóricos e Defesa Lógica**](docs/pt/01_FUNDAMENTOS_TEORICOS_E_DEFESA_LOGICA.md) — *Glossário intuitivo dos conceitos formais, prova de cauda inferior de Hoeffding, defesa analítica do planejamento cibernético e evidência empírica de 30 anos (3×3) em favor do CIBERSOC.*
- [**02. Guia da Interface de Usuário (UI)**](docs/pt/02_GUIA_DA_INTERFACE_UI.md) — *Manual completo das 6 abas em PySide6, placar ao vivo dos 3 regimes, paleta Constructivist Espresso, atalhos de teclado e acessibilidade tipográfica.*
- [**03. Manual de Operação do Simulador**](docs/pt/03_MANUAL_DE_OPERACAO_DO_SIMULADOR.md) — *Playbooks operacionais, benchmark comparativo de 30 anos (3 regimes × 3 cenários), CLI trilíngue (`run_simulation.py`) e API Python.*
- [**04. Mecânica Subjacente (Under the Hood)**](docs/pt/04_MECANICA_SUBJACENTE_UNDER_THE_HOOD.md) — *Árvores de Merkle, Commit-Reveal SHA-256, DRBG sem viés, cotas de Hamilton, matrizes CSR de Leontief, identidade de cotas de trabalho e simulação contrafactual CRN.*

### 🇬🇧 English (UK) (`docs/en-GB/`)
- [**01. Theoretical Foundations and Logical Defence**](docs/en-GB/01_THEORETICAL_FOUNDATIONS_AND_LOGICAL_DEFENCE.md) — *Plain-language concept guide, lower-tail Hoeffding proof, analytical defence of sparse cybernetic planning, and 30-year 3×3 empirical proof in favour of CIBERSOC.*
- [**02. User Interface (UI) Guide**](docs/en-GB/02_UI_GUIDE.md) — *Complete guide to the 6 PySide6 workspaces, 3-regime live scoreboard, responsive layout modes, keyboard shortcuts, and accessible typography.*
- [**03. Simulator Operation Manual**](docs/en-GB/03_SIMULATOR_OPERATION_MANUAL.md) — *Step-by-step playbooks, 30-year 3×3 regime benchmark, headless CLI runner, programmatic Python API, and 100% coverage verification.*
- [**04. Under the Hood Mechanics**](docs/en-GB/04_UNDER_THE_HOOD_MECHANICS.md) — *Cryptographic sortition proofs, rational integer-day surplus division, CSR Leontief–Cockshott solvers, and SEEM CRN regime architecture.*

### 🇪🇸 Español (`docs/es/`)
- [**01. Fundamentos Teóricos y Defensa Lógica**](docs/es/01_FUNDAMENTOS_TEORICOS_Y_DEFENSA_LOGICA.md) — *Guía intuitiva de conceptos técnicos, demostración de Hoeffding, defensa analítica de la planificación cibernética y evidencia empírica de 30 años (3×3) a favor de CIBERSOC.*
- [**02. Guía de la Interfaz de Usuario (UI)**](docs/es/02_GUIA_DE_LA_INTERFAZ_UI.md) — *Guía integral de las 6 pestañas en PySide6, marcador en vivo de 3 regímenes, paleta cromática, atajos de teclado y escala tipográfica.*
- [**03. Manual de Operación del Simulador**](docs/es/03_MANUAL_DE_OPERACION_DEL_SIMULADOR.md) — *Playbooks de simulación, benchmark comparativo de 30 años (3×3), informe CLI trilingüe, API en Python y auditoría automatizada.*
- [**04. Mecánica Subyacente (Under the Hood)**](docs/es/04_MECANICA_SUBYACENTE_UNDER_THE_HOOD.md) — *Árboles de Merkle, balizas Commit-Reveal, DRBG insesgado, cuotas de Hamilton, matrices dispersas CSR y motor contrafactual SEEM.*

---

## 8. Prerequisites, Installation & Execution

### Requirements
- **macOS** (13+), **Linux**, or **Windows**
- **Python 3.12, 3.13, or 3.14**
- **[`uv`](https://docs.astral.sh/uv/)** deterministic package manager

### Setup
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync --all-extras --all-groups
```

### Launching the Desktop UI (PySide6)
```bash
uv run python cibersoc_ui.py
# or via installed console script:
uv run cibersoc-ui
```

### Launching the Trilingual CLI Report
```bash
uv run python run_simulation.py --locale en-GB
uv run python run_simulation.py --locale pt
uv run python run_simulation.py --locale es
```

---

## 9. Running the Test Suite & Architectural Invariants (100% Coverage)

```bash
uv run pyright src/cibersoc
QT_QPA_PLATFORM=offscreen uv run pytest
```

Every commit is verified against **Five Hard Architectural Invariants**:
1. **100.00% Statement and Branch Coverage:** Enforced via `pytest-cov` (`--cov=src/cibersoc --cov-branch --cov-fail-under=100`) and strict `pyright` static type checking (`0 errors, 0 warnings`).
2. **Zero Mocks & Zero Monkeypatching:** Test doubles (`unittest.mock`, `MagicMock`, `monkeypatch`) are banned across `tests/`. Every test exercises real cryptographic sortition, real sparse solvers, and real Qt widgets wired through explicit Dependency Injection parameters.
3. **AST-Enforced Self-Documenting Clean Code (`0` `#` Comments, `0` Docstrings in `.py`):** Verified by `audit_clean_code_compliance` via Python's `tokenize` and `ast` modules. Rather than allowing inline comments to drift out of sync with executable logic, every Python symbol must express intent through exact domain naming and static types, while mathematical proofs live in `docs/`.
4. **100% Trilingual Symmetry:** Verified across `en-GB`, `pt`, and `es` catalogues and documentation manuals.
5. **Standalone Analytical Purity:** Zero external network calls or cloud dependencies at runtime.

---

## 10. Project Structure

```text
.
├── assets/
│   ├── icons/                   # Multi-resolution SVG and PNG Wings of Freedom emblems
│   └── images/screenshots/      # High-DPI authentic workspace captures (Tabs 1-6)
├── docs/
│   ├── demo/index.html          # Zero-install trilingual HTML5/WebCrypto browser lab
│   ├── en-GB/                   # English (UK) theoretical proofs and manuals (01-04)
│   ├── pt/                      # Portuguese theoretical proofs and manuals (01-04)
│   └── es/                      # Spanish theoretical proofs and manuals (01-04)
├── simulation_data/             # Deterministic population, mesh, and checkpoint snapshots
├── src/cibersoc/
│   ├── audit.py                 # AST/lexer Clean Code and standalone integrity verifiers
│   ├── civic_exam.py            # Periodic civic enablement scheduler & age-60 exemption
│   ├── cli.py                   # Trilingual deterministic CLI report runner
│   ├── councils.py              # Federated councils, Popular Jury rotation, Defence gates
│   ├── cybernetics.py           # CSR Leontief, Jacobi labour shares, Harmony & feedback
│   ├── enterprise.py            # Horizontal [1,0,0,0] cooperative ledger (Decimal + gcd)
│   ├── mandate_protection.py    # CPI stipend parity and >=180-day reinstatement lock
│   ├── py.typed                 # PEP 561 static typing marker
│   ├── sortition.py             # SHA-256 Commit-Reveal, Merkle roots, DRBG, Hamilton quotas
│   ├── i18n/                    # Reactive localization engine and JSON catalogues
│   ├── simulation/              # SEEM 150.7M-citizen national engine & CRN regimes (A/B/C)
│   ├── ui/                      # PySide6 desktop client, 3D WebGL/QPainter map & Mermaid reader
│   └── util/                    # Deterministic checkpoint loader and serializer
├── tests/                       # 100% statement + branch test suite (zero mocks/monkeypatch)
├── CONTRIBUTING.md              # Engineering guidelines and Five Architectural Invariants
├── LICENSE                      # OSI-approved MIT License + Open Civic Architecture Notice
└── pyproject.toml               # Package metadata, console scripts, and strict QA settings
```

---

## 11. Contributing & License

Contributions grounded in mathematical, algorithmic, and software engineering rigour are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**CIBERSOC** is released under the **MIT License** (see [LICENSE](LICENSE)), accompanied by a trilingual Open Civic & Scientific Architecture Notice ensuring unrestricted academic, educational, and civic auditability.
