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
