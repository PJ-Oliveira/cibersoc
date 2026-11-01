# 02. User Interface (UI) Guide

## 1. Visual Architecture & *Constructivist Espresso* (`DarkCappuccinoPalette`) Design System

The **CIBERSOC** desktop client ([`CiberSocMainWindow`](../../src/cibersoc/ui/main_window.py)) is built with **PySide6 (Qt 6.12)**. The interface follows a sober, low-fatigue visual system defined by `ConstructivistEspressoPalette` (`DarkCappuccinoPalette`) in [`theme.py`](../../src/cibersoc/ui/theme.py):

| Token | Hex Code | Functional Role |
| :--- | :--- | :--- |
| `bg_espresso_deep` | `#16110E` | Main window structural canvas |
| `bg_roast_panel` | `#1F1814` | Workspace containers, global header bar, topology canvas background |
| `bg_moka_card` | `#29201B` | Interactive tables, buttons, numeric spin boxes, unselected council nodes |
| `bg_roast_elevated` | `#362A23` | Active tab headers, table section headers, inspected council highlight |
| `border_warm_roast` | `#4A3930` | Crisp 1 px structural dividers and inactive mesh links |
| `text_ivory_primary` | `#F4EAD8` | High-contrast primary typography and monospaced telemetry |
| `text_cream_secondary` | `#D7C5B0` | Subtitles, secondary node metrics, inactive tab labels |
| `accent_crema_amber` | `#C89B6D` | Active borders, section headings, upward citizen-demand flows (`↑`) |
| `accent_sage_ok` | `#84A97C` | Downward compulsory plebiscite directives (`↓`) and verified stamps |
| `accent_terracotta_alert` | `#C26653` | Constitutional safeguard test buttons (`#AlertActionButton`) |

> **Accessibility Standard:** Every foreground/background pair satisfies WCAG AA contrast ($\ge 4.5:1$), paired with bundled **Atkinson Hyperlegible** fonts and a guaranteed **12 pt minimum** font size across all controls.

---

## 2. Global Header Bar & Live `i18n` Switching

Persistent controls at the top of the main window:
1. **Wings of Freedom Emblem & System Identity (`lbl_header_emblem`):** Multi-resolution vector emblem uniting geometric wings, an industrial cybernetic planning gear, and severed chains; also powers the window icon and macOS Dock icon.
2. **Instant Language Selector (`cmb_language`):** Switches seamlessly between **English (UK) — `en-GB`**, **Português — `pt`**, and **Español — `es`** via `LocalizationCatalog.switch_locale`, re-translating every widget, table cell, canvas node, charter axiom, and audit log entry in place without resetting state.
3. **Typography Scaling Controls (`A-`, `A+`, `Aa`):** Dynamic font scaling from **12 pt** to **32 pt** (`Ctrl++`, `Ctrl+-`, `Ctrl+0`) with session persistence.
4. **Keyboard Shortcuts Button (`?` / `F1`):** Opens a localized reference dialog listing every bound shortcut.
5. **Active Demarchic Cycle Badge (`lbl_cycle_badge`):** Displays the active sortition cycle (`DEMARCHIC CYCLE #01`, `#02`, …).

---

## 3. Six Integrated Workspaces (Tabs)

### 3.1 Federated Mesh & Ministries (`tabs.councils`)
- **Left Panel — Interactive Escalated Council Mesh (`CouncilMeshCanvas`):** Real-time 4-tier topology (`Federal → State → Municipal → Sectoral`) with click-selectable nodes, synchronized selector (`cmb_council`), upward demand escalation (`btn_escalate_demand`, `↑`), and downward plebiscite directive channels (`↓`).
- **Right Panel — Granular Role & Chamber Resolution:**
  - **Secretary-General Box (`grp_secretary`):** Displays sorted holder ID, stratum, unit voting weight (`1`), zero veto/decree authority, majority authentication (`btn_sg_authenticate`), and autocratic block verification (`btn_sg_veto_test`).
  - **Mathematical Proportionality Banner (`lbl_council_proportionality`):** Displays exact seat-scaling ratios (e.g. Curitiba Municipal Council `20` seats strictly $1:1$ proportional to child sectoral councils Boqueirão `[10]` + Matriz `[10]`).
  - **Ministry-Equivalent Chambers Table (`tbl_ministries`):** Lists every `MinistryPortfolio`, sorted rapporteur, civilian vs. military status, and headcount.
  - **Popular Jury & Public Security Oversight (`grp_jury_security`):** Adjudicates disputes on odd-numbered citizen benches with deterministic per-case alternate rotation (`btn_jury_adjudicate`), blocks magistrate bench overrides (`btn_jury_block`), dispatches civilian-bound security patrols (`btn_security_dispatch`), and blocks unilateral coercion (`btn_security_block`).
  - **Federal Ministry of Defence Gate (`grp_defence`):** Issues multi-signature civilian orders (`btn_defence_order`) and blocks unilateral general mobilisation (`btn_defence_block`).

### 3.2 Sortition, Quarantine & Civic Enablement (`tabs.sortition`)
- **Control Summary (`lbl_sortition_summary`):** Displays active cycle, registered local pool (`320`), serving councillors (`76` across 5 councils), quarantined outgoing councillors, and consecutive re-selection (`0` invariant).
- **Sortition & Snapshot Actions:** Execute the next `Commit-Reveal SHA-256` sortition cycle (`btn_next_cycle`), test the party-candidacy constitutional block (`btn_block_election` -> `ElectoralOperationForbiddenError`), or persist a deterministic snapshot (`btn_save_checkpoint`) under `simulation_data/checkpoints/`.
- **Civic Enablement Exam Scheduler (`grp_civic_enablement`):** Tracks periodic civic qualification across 4 core subjects (`btn_civic_round`), enforcing automatic statutory exemption from age 60 while tracking technical-audit eligibility (`>= 70%`).
- **Cryptographic Proofs Table (`tbl_proofs`):** Displays each council's SHA-256 Merkle root, Hamilton stratum breakdown, and `VERIFIED (SHA-256)` audit status.

### 3.3 Cybernetic Macro-Allocation (`tabs.cybernetics`)
- **Ballot Controls (`spn_votes_edu`, `spn_votes_health`) & Tally (`btn_run_plebiscite`):** Executes a coercion-resistant blinded plebiscite, derives physical final demand from exact embedded labour shares ($s_j = 100 \cdot H_j y_j^* / \sum_k H_k y_k^*$), solves CSR Leontief gross output, applies Cockshott short-run Harmony relaxation, and broadcasts the binding directive.
- **Iterative Plan Adjustment & Ecological Carbon Boundary (`grp_cyber_feedback`):** Simulates real-time clearing-ratio feedback (`spn_clearing_ratio`) and physical carbon-ceiling enforcement (`spn_carbon_budget`, `btn_iterate_plan`).
- **Constitutional Safeguards:** Blocks personal candidate names on ballots (`btn_block_person_pleb`) and unauthorized council budget deviations (`btn_block_council_override`).
- **Input–Output Matrix Table (`tbl_cyber`):** Displays voted labour share (`%`), final demand $y^*$, gross output $x$, Jacobi embedded labour $H$, and short-run Harmony per sector.

### 3.4 CEO-Free Enterprise & Civil Return (`tabs.enterprise`)
- **Left Panel — Cooperative Enterprise Ledger (`grp_enterprise_ledger`):** Adjusts Period Operating Revenue (`spn_revenue`) and computes exact integer-day rational $1/N$ worker shares (`btn_distribute_profit`) via `Decimal` and `math.gcd`, keeping corporate retained profit identically at `$0.00`. Attempting to appoint a CEO (`btn_block_ceo`) raises `OrganisationalViolationError`.
- **Right Panel — Sorted Citizen Mandate Lifecycle (`grp_mandate_lifecycle`):** Guides worker `CID-0001` through (1) Mandate Suspension, (2) `+0.50%` CPI Stipend Indexing, (3) Protected Reinstatement ($\ge 180$ days), and (4) Post-Return Dismissal Block (`EmploymentStabilityLockError`).

### 3.5 Axioms, Integrity & Documentation (`tabs.charter_docs`)
- **Architectural Charter & Integrity Scanner (`grp_charter`):** Displays the localized 7 structural axioms, exports FullHD localized emblem artwork (`btn_export_fullhd_wallpaper`), and executes `btn_run_audit`, verifying 0 `#` comments and 0 docstrings across all `.py` files (`tokenize` + `ast.parse`) and complete trilingual documentation parity.
- **README & System Documentation Reader (`grp_readme`):** Native Markdown + styled HTML **Mermaid diagram** viewer (`QTextBrowser`) with instant selector (`cmb_doc_selector`), relative-link navigation, quick-return (`btn_open_readme`), and responsive font scaling up to 32 pt.

### 3.6 Nation Simulation — 3D SEEM Engine (`tabs.simulation`)
- **National Scale & Continental Topology:** Simulates **150,700,000 inhabitants** across 10 Brazilian macro-regional poles over an authentic continental vector silhouette with 3D quadratic-Bézier inter-regional input–output trade arcs, HDI towers, population ground rings, and rotating 1-cycle quarantined regional councillors (`70` active per year across 7 portfolios × 10 poles).
- **Institutional Regime Comparator (`cmb_regime`):** Evaluates three regimes side-by-side under **Common Random Numbers (CRN)** (identical shock streams): **(A) CIBERSOC (Demarchy + Cybernetics + 1/N)**, **(B) Electoral Oligarchy (Market + Parties)**, and **(C) Bureaucratic Centralism (Command State)**, displaying real-time comparative HDI and Gini deltas (`ΔHDI`, `ΔGini`) and exporting multi-regime CSV/JSON trajectories.

---

## 4. Persistent Audit Trail Console & Responsive Layout

- **Audit Console (`grp_audit_console`):** Docked across all tabs, displaying the latest 25 localized `LocalizedAuditEvent` entries and re-translating live upon locale switch.
- **Adaptive Breakpoint (`< 960 px` `COMPACT` vs. `>= 960 px` `EXPANDED`):** Automatically stacks splitters and button rows vertically on narrow screens, guaranteeing zero horizontal scrollbar overflow down to `680×500`.

---

## 5. Keyboard Shortcuts Reference

| Shortcut | Scope | Action |
| :--- | :--- | :--- |
| `F1` or `?` | Global | Open localized Keyboard Shortcuts dialog |
| `Ctrl+1` … `Ctrl+6` | Global | Switch directly to Workspace Tab 1 … 6 |
| `Ctrl++` / `Ctrl+=` | Global | Increase interface font size (`A+`, up to 32 pt) |
| `Ctrl+-` | Global | Decrease interface font size (`A-`, down to 12 pt) |
| `Ctrl+0` | Global | Reset interface font size to default (`Aa`) |
| `F11` | Global | Toggle fullscreen presentation mode |
| `Alt+Up` / `Alt+Down` | Global | Cycle inspected council across the 4-tier federated mesh |
| `Space` | Tab 6 (SEEM) | Play / Pause continuous yearly simulation |
| `Right` | Tab 6 (SEEM) | Advance simulation by `spn_years_step` years |
| `R` | Tab 6 (SEEM) | Reset SEEM simulation to Year 2026 |
| `+` / `-` | Tab 6 (SEEM) | Zoom 3D camera in / out |
