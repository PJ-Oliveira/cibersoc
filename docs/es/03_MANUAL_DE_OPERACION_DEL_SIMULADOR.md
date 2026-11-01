# 03. Manual de Operación del Simulador

## 1. Aprovisionamiento del Entorno y Puesta en Marcha

El simulador **CIBERSOC** se ejecuta sobre **Python 3.12, 3.13 y 3.14** en macOS, Linux y Windows. Todas las dependencias están fijadas de forma determinista en [`uv.lock`](../../uv.lock) mediante **uv**.

### 1.1 Clonación y Sincronización del Entorno Virtual Aislado
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync --all-extras --all-groups
```

### 1.2 Lanzamiento del Cliente Gráfico de Escritorio (PySide6)
```bash
uv run python cibersoc_ui.py
# o mediante el punto de entrada de consola:
uv run cibersoc-ui
```
Se pueden guardar snapshots deterministas del padrón poblacional, de la malla de consejos y de la auditoría de integridad en cualquier momento pulsando **Guardar Snapshot (`btn_save_checkpoint`)** en la Pestaña 2 o programáticamente en `simulation_data/` y `simulation_data/checkpoints/`.

### 1.3 Ejecución del Simulador CLI Trilingüe Determinista
```bash
uv run python run_simulation.py --locale en-GB
uv run python run_simulation.py --locale pt
uv run python run_simulation.py --locale es
```
El CLI ejecuta una simulación integral determinista e imprime cuatro secciones traducidas:
- **`[1]` Sorteo, Consejos Federados y Habilitación Cívica:** Pruebas criptográficas del ciclo activo, cuarentenas y resumen de habilitación cívica.
- **`[2]` Economía Cooperativa y Paridad de Mandato:** Excedente operativo neto, reparto exacto $1/N$ por trabajador, retención corporativa `$0.00` y protección indexada al IPC.
- **`[3]` Macroasignación Cibernética y Retroalimentación del Plan:** Escrutinio plebiscitario, cuotas de trabajo incorporado, producción bruta de Leontief, Armonía a corto plazo y retroalimentación de vaciado/techo de carbono.
- **`[4]` Integridad Autónoma y Rastro de Auditoría:** Conformidad AST/lexer de Clean Code, simetría trilingüe y eventos auditados.

---

## 2. Playbooks de Operación

### Playbook A — Sorteo Multiciclo, Cuarentena y Habilitación Cívica
1. Abra la **Pestaña 2 (`Sorteo y Cuarentena`)**. Observe el Ciclo `#01`: `76` consejeros activos en los 5 consejos (`20` Federal + `16` Estatal + `20` Municipal + `10` Boqueirão + `10` Matriz), `En Cuarentena = 0`, `Reelección Consecutiva = 0`.
2. Pulse **Ejecutar Siguiente Ciclo de Sorteo (`btn_next_cycle`)**:
   - Los consejeros salientes pasan a cuarentena criptográfica; se sortean `76` nuevos consejeros entre los `244` ciudadanos elegibles mediante `Commit-Reveal SHA-256` + cuotas de Hamilton, manteniendo `Reelección Consecutiva = 0` y cada prueba `VERIFICADO (SHA-256)`.
3. Pulse **Ejecutar Ronda de Habilitación Cívica (`btn_civic_round`)** para registrar calificaciones en las 4 materias troncales y comprobar la exención estatutaria automática desde los $\ge 60$ años.

### Playbook B — Macroplebiscito, Cuotas de Trabajo y Techo de Carbono
1. Abra la **Pestaña 3 (`Macroasignación Cibernética`)**, fije `+5% Educación` en `750` y `+5% Salud` en `250`, y pulse **Escrutar Plebiscito y Emitir Directriz (`btn_run_plebiscite`)**.
2. Verifique el desplazamiento continuo de Cockshott (`-2,50%`), la conservación exacta de cuotas de trabajo incorporado en la tabla Insumo-Producto y el incremento `↓Dir` en la Pestaña 1.
3. Ajuste la **Razón Observada de Vaciado (`spn_clearing_ratio`)** y el **Presupuesto de Carbono (`spn_carbon_budget`)**, pulsando **Iterar Plan (`btn_iterate_plan`)** para inspeccionar el ajuste iterativo y el límite ecológico.

### Playbook C — Excedente Cooperativo $1/N$ y Ciclo de Mandato
1. Abra la **Pestaña 4 (`Empresa Sin CEO y Retorno Civil`)**, fije **Ingresos Operativos (`spn_revenue`)** en `220000` y pulse **Ejecutar Reparto Igualitario 1/N (`btn_distribute_profit`)**, confirmando retención corporativa `$0.00` y arrastre exacto de fracciones de centavo.
2. Recorra los cuatro botones del **Ciclo de Mandato** para `CID-0001`: suspensión por mandato, indexación del `+0,50%` por IPC, reincorporación protegida $\ge 180$ días y bloqueo de despido prematuro (`EmploymentStabilityLockError`).

### Playbook D — Comparación Contrafactual Nacional SEEM (`A / B / C`)
1. Abra la **Pestaña 6 (`Simulación Nacional — SEEM`)**, fije **Años por Paso (`spn_years_step`)** en `15` y pulse **Avanzar**.
2. Conmute el **Régimen Institucional (`cmb_regime`)** entre **(A) CIBERSOC Demárquico**, **(B) Oligarquía Electoral** y **(C) Centralismo Burocrático**. Dado que las tres trayectorias comparten **Números Aleatorios Comunes (CRN)**, las diferencias en IDH, Gini y empleo aíslan estrictamente el efecto del mecanismo institucional.

---

## 3. API Programática en Python

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

plant = SocialistEnterprise("EMP-01", "Óptica de Precisión Curitiba", "IND-OPT")
plant.register_worker(WorkerMember("W-01", "Alice", "Ingeniera Óptica", Decimal("4800.00"), 30))
plant.register_worker(WorkerMember("W-02", "Bruno", "Técnico de Montaje", Decimal("4200.00"), 30))
receipt = plant.distribute_period_profit(
    period_label="2026-M01",
    period_total_days=30,
    gross_revenue=Decimal("35000.00"),
    audited_material_costs=Decimal("10000.00"),
    physical_depreciation_reserve=Decimal("2000.00"),
    macro_social_contribution=Decimal("3000.00"),
    capital_endowment_equalisation_charge=Decimal("1000.00"),
)
print("Pagos por trabajador:", receipt.payouts_by_worker)
```

---

## 4. Verificación Automatizada y QA del 100% de Cobertura

```bash
uv run pyright src/cibersoc
QT_QPA_PLATFORM=offscreen uv run pytest -v \
    --cov=src/cibersoc --cov-branch \
    --cov-report=term-missing --cov-fail-under=100
```
La suite exige `0` errores estáticos de tipos, `100.00%` de cobertura de sentencias y ramas, `0` mocks o monkeypatches, `0` comentarios `#` o docstrings en todos los archivos `.py` y simetría trilingüe íntegra.

---

## 5. Benchmark Empírico Comparativo de 30 Años (3 Regímenes × 3 Escenarios)

Esta sección documenta el experimento longitudinal canónico de **30 ciclos anuales** (`seed=42`, `StochasticEventMatrix(seed=42)`, `150.700.000` habitantes en 10 estados federados, `150` consejeros únicos sorteados con `0` reelecciones consecutivas) ejecutado bajo **Números Aleatorios Comunes (CRN)** en los tres regímenes institucionales — **(A) Demarquía CIBERSOC (`CIBERSOC_DEMARCHY`)**, **(B) Oligarquía Electoral (`ELECTORAL_OLIGARCHY`)** y **(C) Centralismo Burocrático (`BUREAUCRATIC_CENTRALISM`)** — y en los tres escenarios macroestructurales.

### 5.1 Trayectoria Longitudinal Sin Macrodirectriz (`Macro = False`, Años 0 → 10 → 20 → 30)

| Escenario | Régimen | IDH (A0 → A10 → A20 → A30) | Gini (A0 → A10 → A20 → A30) | Empleo % (A0 → A10 → A20 → A30) | Brecha Regional IDH (A30) | $\sigma_{\text{IDH}}$ (A30) | Flujo Corredores (A30) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | **A. Demarquía** | `0.7379 → 0.8237 → 0.8786 → 0.9110` | `0.4045 → 0.3318 → 0.2880 → 0.2630` | `78.75% → 85.05% → 87.60% → 91.23%` | `0.0538` | `0.0135` | `0.9814` |
| **`BASELINE`** | **B. Oligarquía Electoral** | `0.7379 → 0.7513 → 0.7656 → 0.7738` | `0.4045 → 0.4649 → 0.5013 → 0.5255` | `78.75% → 78.19% → 76.54% → 77.70%` | `0.1438` | `0.0431` | `0.6057` |
| **`BASELINE`** | **C. Centralismo Burocrático** | `0.7379 → 0.7783 → 0.8028 → 0.8104` | `0.4045 → 0.3884 → 0.3761 → 0.3688` | `78.75% → 82.12% → 80.26% → 77.74%` | `0.0796` | `0.0212` | `0.7000` |
| **`ECOLOGICAL_STRESS`** | **A. Demarquía** | `0.7136 → 0.7971 → 0.8521 → 0.8833` | `0.4045 → 0.3340 → 0.2913 → 0.2678` | `76.93% → 82.69% → 85.08% → 88.23%` | `0.0631` | `0.0177` | `0.9044` |
| **`ECOLOGICAL_STRESS`** | **B. Oligarquía Electoral** | `0.7136 → 0.7235 → 0.7363 → 0.7412` | `0.4045 → 0.4673 → 0.5051 → 0.5312` | `76.93% → 75.36% → 73.22% → 73.59%` | `0.1684` | `0.0545` | `0.5285` |
| **`ECOLOGICAL_STRESS`** | **C. Centralismo Burocrático** | `0.7136 → 0.7508 → 0.7744 → 0.7796` | `0.4045 → 0.3907 → 0.3795 → 0.3739` | `76.93% → 79.54% → 77.37% → 74.21%` | `0.0969` | `0.0289` | `0.6260` |
| **`POST_CRISIS_EQUALISATION`** | **A. Demarquía** | `0.7476 → 0.8432 → 0.8943 → 0.9201` | `0.5729 → 0.4029 → 0.3174 → 0.2754` | `64.02% → 78.70% → 84.88% → 89.76%` | `0.0386` | `0.0105` | `0.9679` |
| **`POST_CRISIS_EQUALISATION`** | **B. Oligarquía Electoral** | `0.7476 → 0.7561 → 0.7661 → 0.7705` | `0.5729 → 0.5719 → 0.5688 → 0.5678` | `64.02% → 69.28% → 71.06% → 73.93%` | `0.0884` | `0.0275` | `0.5551` |
| **`POST_CRISIS_EQUALISATION`** | **C. Centralismo Burocrático** | `0.7476 → 0.7890 → 0.8089 → 0.8103` | `0.5729 → 0.4734 → 0.4189 → 0.3908` | `64.02% → 74.82% → 76.73% → 76.08%` | `0.0516` | `0.0146` | `0.6750` |

### 5.2 Sensibilidad a la Directriz Plebiscitaria Activa (`Macro = True`, Predeterminado de UI, Año 30)

Al acoplar el plebiscito cibernético anual (`PLEB-FED-01: +5% Health`, `bonus = 0.015`, atenuado por el margen cóncavo de frontera `max(0, 0.965 - IDH)`), la transmisión institucional (`macro_directive_multiplier`: `1.00` en A, `0.55` en C, `0.22` en B) amplía el diferencial neto de bienestar:

| Escenario (Año 30, `Macro = True`) | IDH (A. Demarquía) | IDH (B. Electoral) | IDH (C. Centralismo) | Ganancia Neta A vs B ($\Delta\text{IDH}$) | Ganancia Neta A vs C ($\Delta\text{IDH}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | `0.9218` | `0.7798` | `0.8215` | **`+0.1420`** | **`+0.1003`** |
| **`ECOLOGICAL_STRESS`** | `0.8972` | `0.7481` | `0.7927` | **`+0.1491`** | **`+0.1045`** |
| **`POST_CRISIS_EQUALISATION`** | `0.9275` | `0.7755` | `0.8194` | **`+0.1520`** | **`+0.1081`** |

### 5.3 Diagnóstico Estructural de las Diferencias Observadas

1. **Divergencia Distributiva y Convergencia Regional ($\sigma$-convergencia):** En la Demarquía (A), el reparto cooperativo $1/N$ sin captura de rentas (`rent_capture_drift = 0.0`) y la igualación interregional (`+0.032`) comprimen la brecha interestatal de IDH en `BASELINE` de `0.3260` (Año 0) a `0.0538` (Año 30, $\sigma = 0.0135$), elevando la intensidad media de los corredores productivos a `0.9814`. En la Oligarquía Electoral (B), la deriva de captura (`+0.0022/año`) y la polarización centro-periferia (`-0.005`) elevan el Gini a `0.5255` y dejan una brecha regional `2,67×` mayor (`0.1438`: `BR-SP = 0.788` frente a `BR-AM = 0.702`).
2. **Fractura Norte–Sur bajo Estrés Ecológico (`ECOLOGICAL_STRESS`):** Ante choques climáticos persistentes sobre latitudes tropicales ($\text{lat} > -16^\circ$), la supervisión demárquica mitiga el `30%` del daño neto, sosteniendo el IDH medio del Norte/Nordeste en `0.8637` frente a `0.8899` en el Centro-Sur (brecha Norte–Sur de apenas `0.0262`). Bajo Oligarquía Electoral (mitigación del `6%`), el Norte/Nordeste se estanca en `0.6840` (`BR-AM = 0.617`, `BR-BA = 0.646`) frente a `0.7571` en el Sur (fractura Norte–Sur `2,79×` más severa, `0.0731`).
3. **Osificación Burocrática a Largo Plazo en el Régimen C:** El Centralismo Burocrático logra una fuerte movilización inicial durante la primera década (`Empleo` sube del `78.75%` al `82.12%` en `BASELINE` y del `64.02%` al `74.82%` en `POST_CRISIS`), pero sufre osificación administrativa acumulada tras el Año 8 (`ossification_rate = 0.0018`), reduciendo el empleo del `82.12%` (Año 10) al `77.74%` (Año 30) en `BASELINE` y estabilizando el Gini en un piso jerárquico (`0.3688–0.3908`).
4. **Recuperación Poscrisis (`POST_CRISIS_EQUALISATION`):** Partiendo de una desigualdad poscrisis aguda (`Gini = 0.5729`) y desempleo elevado (`64.02%`), la Demarquía comprime el Gini en **`-0.2975` puntos** (`0.2754`) y crea **`+25.74 pp`** de empleo (`89.76%`), mientras que la Oligarquía Electoral queda atrapada en histéresis desigual (`Gini = 0.5678`, con variación residual de `-0.0051` en treinta años).
