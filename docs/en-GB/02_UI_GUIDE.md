# 02. User Interface (UI) Guide

## 1. Visual Architecture & *Dark Cappuccino* Design System

The **CIBERSOC** client is built with **PySide6 (Qt 6.12)**.  The UI follows a deliberately sober visual language called **Dark Cappuccino** – a palette of deeply muted browns and creams that maximises contrast for readability while avoiding flashy decorations.  All colours are defined in `src/cibersoc/ui/theme.py` and used consistently across widgets:

| Token | Hex Code | Role |
|---|---|---|
| `bg_espresso_deep` | `#16110E` | Main window background (deep structural canvas) |
| `bg_roast_panel` | `#1F1814` | Workspace containers, top‑level header, topology canvas background |
| `bg_moka_card` | `#29201B` | Interactive tables, buttons, numeric spin boxes, un‑selected council nodes |
| `bg_roast_elevated` | `#362A23` | Active tab headers, table section headers, selected council node highlight |
| `border_warm_roast` | `#4A3930` | 1 px structural dividers and inactive mesh links |
| `text_ivory_primary` | `#F4EAD8` | High‑contrast primary typography, monospaced telemetry |
| `text_cream_secondary` | `#D7C5B0` | Sub‑titles, secondary node metrics, inactive tab labels |
| `accent_crema_amber` | `#C89B6D` | Active borders, section headings, upward citizen‑demand flows (`↑`) |
| `accent_sage_ok` | `#84A97C` | Downward compulsory plebiscite directives (`↓`) |
| `accent_terracotta_alert` | `#C26653` | Constitutional guard test buttons (e.g. `#AlertActionButton`) |

> **Why this matters:** The colour choices guarantee a minimum contrast ratio of 4.5:1 (WCAG AA) on all supported monitors, making the UI accessible to users with moderate visual impairments.

---

## 2. Global Header Bar & Live `i18n` Language Switching

At the top of the window persistent elements appear:
1. **Wings of Freedom Emblem & System Identity** — The constructivist heraldic emblem (`lbl_header_emblem`) merges the Wings of Freedom with a Soviet cybernetic cogwheel and severed chains under the Dark Cappuccino palette, embodying the relentless striving for popular emancipation and breaking autocratic walls. This visual emblem also serves as the official application window and macOS Dock icon.
2. **Instant Language Selector (`cmb_language`)** – toggles between **English (UK)**, **Português**, and **Español**. Selecting a language calls `LocalizationCatalog.switch_locale`, which **re‑translates every widget, tab title, table header, canvas label, charter text and audit‑console entry** instantly, without resetting the simulation state.
3. **Typography Scaling Controls (`A-`, `A+`, `Aa`)** — Dynamic responsive font scaling (12 pt minimum, shortcuts `Ctrl++`, `Ctrl+-`, `Ctrl+0`).
4. **Active Demarchic Cycle Badge (`lbl_cycle_badge`)** – shows the current sortition cycle (`CYCLE #01`, `#02`, …).

> **Tip:** The language selector is keyboard‑focusable (`Alt+L`).  Pressing `Enter` after a selection triggers the translation synchronously.

---

## 3. Six Operational Workspaces (Tabs)

### 3.1 Councils & Federated Mesh (`tabs.councils`)
- **Left‑hand panel – Interactive Escalated Council Mesh** (`CouncilMeshCanvas`).  The canvas draws the four‑tier hierarchy in real time (Federal → State → Municipal → Sectoral).  Nodes are **click‑selectable**; hovering shows a tooltip with council statistics (members, budget share, current mandates).
- **Right‑hand panel – Role‑Resolution Box**:
  - **Secretary‑General box** displays the sorted holder’s ID, stratum, voting weight (`1`), and explicitly shows *zero veto power*.
  - **Mathematical Proportionality Banner** (`lbl_council_proportionality`): Displays the strictly calculated mathematical proportionality metrics and logical rationale for the inspected council (e.g. Curitiba Municipal Council with 20 seats strictly 1:1 proportional to the 20 aggregate members across child sectoral councils Boqueirão [10] and Matriz [10], sustaining a 4-member Justice chamber for the Popular Jury without demographic sample exhaustion).
  - **Ministry table** lists each ministry (or sector‑equivalent chamber), the sorted councillor, civil vs technical status, and staff count.
  - **Defence command box** lets the user issue a **Civilian Multi‑Sig Order** or test the **Autonomous General Block**.
- **Directional flow visualisation:** amber‑crema arrows (`↑`) illuminate when a neighbourhood demand escalates up the mesh; sage‑green dashed arrows (`↓`) illuminate when a compulsory macro‑plebiscite directive flows down.
- **Convenient shortcuts:** `Ctrl+E` escalates a random neighbourhood demand; `Ctrl+R` refreshes the mesh layout after a sortition.

### 3.2 Sortition & Quarantine (`tabs.sortition`)
- **Summary label** (`lbl_sortition_summary`) shows total registered citizens, active councillors, and how many are currently in quarantine.
- **Next‑Cycle button** (`btn_next_cycle`) terminates the current mandates, pushes outgoing councillors into a *cryptographic quarantine* (they cannot be re‑selected until the next cycle), and draws a fresh council via **Commit‑Reveal SHA‑256** with Hamilton‑quota enforcement.
- **Proof table** (`tbl_proofs`) displays each council’s Merkle root, Hamilton quota breakdown, and SHA‑256 verification stamp – useful for auditors.
- **Safety button** (`btn_block_election`) demonstrates that any attempt to trigger a traditional party‑based election raises a `ElectoralOperationForbiddenError`.

### 3.3 Cybernetic Macro‑Allocation (`tabs.cybernetics`)
- **Ballot spin‑boxes** (`spn_votes_edu`, `spn_votes_health`) let the user set the share of a binary plebiscite (e.g. `+5 % Education` vs `+5 % Health`).
- **Run‑Plebiscite button** (`btn_run_plebiscite`) solves the Leontief input‑output system (`CSR` sparse solver) and applies Cockshott’s short‑run Harmony relaxation to obtain a feasible production plan.  The resulting directive is broadcast to every council.
- **Constitutional guard buttons** allow testing of illegal ballot contents (`btn_block_person_pleb`) and simulated council budget overrides (`btn_block_council_override`).
- **Input‑Output matrix table** (`tbl_cyber`) shows the voted share (`%`), final demand `$y^*$`, gross output `$x = (I-A)^{-1} y^*$`, embedded labour hours `$H$`, and the short‑run Harmony index for each sector.

### 3.4 CEO‑Free Enterprise & Civil Return (`tabs.enterprise`)
- **Left panel – Socialist Enterprise Ledger** (`grp_enterprise_ledger`):
  - Adjust *Period Operating Revenue* (`spn_revenue`).
  - Press **Distribute Profit 1/N** (`btn_distribute_profit`) to recompute exact rational worker shares (using Python’s `fractions.Fraction` for zero‑loss arithmetic).  Corporate retention is always `$0.00`.
  - Worker table (`tbl_workers`) lists employment status (`Active`, `On Council Mandate`, `Reinstated with Protection`), monthly base pay, and the equal surplus payout.
  - **CEO‑block button** demonstrates that any attempt to appoint a CEO raises a `CEOAppointmentForbiddenError`.
- **Right panel – Sorted Citizen Mandate Lifecycle** (`grp_mandate_lifecycle`):
  1. **Suspend Mandate** – temporarily removes the citizen from the council.
  2. **Inflation Adjustment** – applies a configurable `%` increase to the stipend.
  3. **Protected Re‑instatement** – guarantees a lock of ≥ 180 days before dismissal.
  4. **Dismissal Block Test** – shows that a post‑return dismissal is rejected.

### 3.5 Architectural Charter & Integrity Audit (`tabs.charter`)
- Displays the **Autonomous CIBERSOC Charter** (the 7 structural axioms) in the currently selected language.
- **Full Clean‑Code & Documentation Scan** (`btn_run_audit`) traverses the entire repository, verifies:
  - Zero missing documentation manuals for each language.
  - Clean‑Code compliance (no stray `TODO`s, Pylint score ≥ 9.5, zero dead‑code warnings).
- Results appear in a modal dialog and are also logged to the persistent audit console.

### 3.6 README & System Documentation (`tabs.readme`)
- Embedded native markdown document reader (`QTextBrowser` with full Markdown rendering) allowing users to inspect `README.md` and all technical manuals directly within the desktop application.
- **Document Selector (`cmb_doc_selector`):** Switch instantly between `README.md` and the 4 localized technical manuals in `docs/` (01. Theoretical Foundations, 02. UI Guide, 03. Simulator Manual, 04. Under-the-Hood Mechanics).
- **Interactive Markdown Hyperlinks:** Clicking any relative markdown link in the reader automatically loads the target document into the viewer and updates the selector.
- **Quick-Return Button (`btn_open_readme`):** Instantly restores the root `README.md` view.
- **Dynamic Font Responsiveness:** Content automatically reflows and respects the user-configured font size (from 12 pt up to 32 pt).

### 3.7 Nation Simulation — SEEM Engine (`tabs.simulation`)
- **Years per step (`spn_years_step`):** Advances as many years as you choose in one click (1 to 1000). There is **no total limit**: the simulation keeps running for as many years as you like, until you press *Reset Simulation*.
- **Reading the 3D map** (collapsible *How to read this map* panel, available in all three languages):
  - **Towers = HDI.** One tower per state; height and colour (red → gold → green) show its HDI.
  - **Rings on the ground = population.** Ring size is proportional to the number of inhabitants of the state. Rings are fixed.
  - **Orbiting particles = citizens (symbolic).** Every state gets the same number of dots, so they do **not** measure population and one dot is not one person.
- **Glossary shown in the panel:**
  - **Population:** everyone who lives in a state (ring) or in the whole country (top-left panel).
  - **Citizens:** inhabitants who can be drawn by lot to govern; one is drawn per portfolio each year and nobody serves twice. The panel shows how many have already been drawn.
  - **HDI (Human Development Index):** 0 to 1 score combining health, education and income; higher is better.
  - **GINI:** income inequality from 0 (everyone earns the same) to 1 (one person holds everything); lower is better.
  - **Employment:** share of the workforce that has a job.

---

## 4. Persistent Audit Trail Console

A read‑only monospace console (`grp_audit_console`) is docked at the bottom of the window across all workspaces.  It shows the **latest 25 `LocalizedAuditEvent` records**, each indicating the action taken, the user (or system) that triggered it, and a timestamp.  The console **auto‑updates** whenever the language changes, ensuring that every entry is always displayed in the active locale.

---

## 5. Responsive Multi‑Screen Layout (`ResponsiveLayoutMode`)

- **Breakpoint at 960 px**:
  - `< 960 px` → *COMPACT* mode: dual `QSplitter` panels collapse into a vertical stack, action bars become column‑wise, tables use `ResizeToContents` with smooth pixel scrolling.
  - `≥ 960 px` → *EXPANDED* mode: panels sit side‑by‑side, columns stretch proportionally, and the mesh canvas expands to fill available space.
- **All workspaces are wrapped in a `QScrollArea`** with `widgetResizable=True`, preventing overflow on small displays.
- **Dynamic scaling of `CouncilMeshCanvas`** makes node rectangles, connector arrows and legends resize mathematically with the widget size, using `QFontMetrics.elidedText` to avoid label collisions.

---

## 6. Quick‑Start Tips for Power Users

| Action | Shortcut | Effect |
|---|---|---|
| Open language selector | `Alt+L` | Switch UI language instantly |
| Escalate a random neighbourhood demand | `Ctrl+E` | Sends a demand up the mesh |
| Refresh mesh after a sortition | `Ctrl+R` | Re‑draws the council graph |
| Run a full audit | `Ctrl+Shift+A` | Executes clean‑code, documentation and integrity checks |
| Save checkpoint (auto on close) | – | Closing the main window triggers `closeEvent` → writes `population.json`, `mesh.json`, `audit_snapshot.json` into a timestamped folder under `simulation_data/checkpoints/` |

---

*All UI elements are fully keyboard‑navigable and expose accessible names for screen‑readers via Qt’s `accessibleName` property.*