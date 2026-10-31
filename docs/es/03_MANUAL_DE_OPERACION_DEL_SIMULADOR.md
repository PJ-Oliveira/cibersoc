# 03. Manual de Operación del Simulador

## 1. Aprovisionamiento del Entorno y Puesta en Marcha

El simulador **CIBERSOC** requiere **Python 3.12+** (validado sobre **CPython 3.14.7**) gestionado mediante [`uv`](https://docs.astral.sh/uv/). Todas las dependencias (`PySide6`, `pytest`, `pytest-cov`, `pytest-qt`, `coverage`) se encuentran fijadas en [`uv.lock`](../../uv.lock).

### 1.1 Sincronización del Entorno Virtual Aislado
```bash
cd cibersoc
uv sync
```

> **¿Por qué `uv`?**  A diferencia de `pip`/`requirements.txt`, `uv` resuelve el grafo de dependencias una única vez, genera un fichero lock y nunca vuelve a descargar los mismos paquetes, eliminando sorpresas del tipo "funciona en mi máquina".

### 1.2 Lanzamiento del Simulador Gráfico de Escritorio (PySide6)
```bash
cd cibersoc
.venv/bin/python cibersoc_ui.py
# o, tras instalar el punto de entrada del paquete:
.venv/bin/cibersoc-ui
```

Al iniciarse, la interfaz muestra un **Diálogo de Selección de Checkpoint**:
- **Nuevo** – inicia una simulación limpia.
- Cualquier checkpoint guardado previamente (carpeta con marca de tiempo bajo `simulation_data/checkpoints/`).
Seleccionar un checkpoint carga `population.json`, `mesh.json` y el snapshot de auditoría, permitiendo reanudar exactamente donde se dejó.

### 1.3 Ejecución del Simulador CLI Trilingüe Parametrizado
El script [`run_simulation.py`](../../run_simulation.py) (respaldado por [`cli.py`](../../src/cibersoc/cli.py)) ejecuta una simulación determinista de extremo a extremo sobre todos los subsistemas e imprime el informe íntegro traducido en `en-GB`, `pt` o `es`:
```bash
cd cibersoc
.venv/bin/python run_simulation.py --locale en-GB
.venv/bin/python run_simulation.py --locale pt
.venv/bin/python run_simulation.py --locale es
```

---

## 2. Playbooks de Orquestación de Simulaciones

### Playbook A – Orquestación de Múltiples Ciclos de Sorteo y Verificación de Cuarentena
1. Abra la **Pestaña 2 (`2. Sorteo y Cuarentena`)**. Observe el Ciclo `#01`: `76` ciudadanos sirven en los 5 Consejos (`20` Federal + `16` Estatal + `20` Municipal + `10` Boqueirão + `10` Matriz), `En Cuarentena = 0`, `Reelección Consecutiva = 0`.
2. Pulse **Ejecutar Siguiente Ciclo de Sorteo**.
   * [`SimulationOrchestrator.execute_next_sortition_cycle`](../../src/cibersoc/ui/state.py) registra la conclusión del mandato de los `76` consejeros del Ciclo 1, bloqueándolos para el Ciclo `#02`.
   * Balizas independientes de entropía (`UNIV-CRYPTO-NODE`, `CIVIC-AUDIT-SOUTH`, `LABOUR-OBSERVATORY`) generan nuevas semillas maestras `SHA-256` y sortean `76` nuevos consejeros entre los `244` ciudadanos elegibles restantes dentro de sus respectivas jurisdicciones territoriales.
   * Compruebe en la cabecera de resumen que **`Exconsejeros Fuera de Urna = 76`** y **`Reelección Consecutiva = 0`**, mostrando cada fila de la Tabla de Pruebas el estado `VERIFICADO (SHA-256)`.
3. Pulse de nuevo **Ejecutar Siguiente Ciclo de Sorteo** (Ciclo `#03`): los consejeros del Ciclo 1 recuperan su elegibilidad tras cumplir 1 ciclo de enfriamiento, mientras los consejeros del Ciclo 2 pasan a cuarentena (`Reelección Consecutiva = 0` se mantiene invariante durante ciclos ilimitados).

### Playbook B – Parametrización de Plebiscitos Macroeconómicos
1. Abra la **Pestaña 3 (`3. Macroasignación Cibernética`)**.
2. Fije **Papeletas Anónimas (+5% Educación)** en `750` y **Papeletas Anónimas (+5% Salud)** en `250`.
3. Pulse **Escrutar Plebiscito y Emitir Directriz Obligatoria**:
   * La directriz ganadora cambia de `FLOW-HEALTH-PLUS5` a `FLOW-EDU-PLUS5` (`1000` papeletas auditadas).
   * El desplazamiento continuo de Cockshott se actualiza a `-2.50%` (desplazando recursos hacia Educación respecto a Salud).
   * En la tabla insumo-producto, la cuota votada de `Educación Pública` asciende a `30.00%` ($y_0^* = 165.00$, producción bruta $x_0 = 192.35$), y cada nodo de Consejo en la Pestaña 1 incrementa su contador `↓Dir`.
4. Pulse **Probar Nombre de Candidato en Papeleta** y **Simular Desviación Presupuestaria del Consejo** para comprobar el bloqueo en tiempo real de propuestas electorales personalistas y de desviaciones burocráticas del 2%.

### Playbook C – Parametrización del Excedente Empresarial y Ecualización Ricardiana
1. Abra la **Pestaña 4 (`4. Empresa Sin CEO y Retorno Civil`)**.
2. Ajuste **Ingresos Operativos del Período ($)** (`spn_revenue`) entre `120000` y `500000` (p. ej., `220000`) y pulse **Ejecutar Reparto Igualitario 1/N**.
3. [`SocialistEnterprise.distribute_period_profit`](../../src/cibersoc/enterprise.py) deduce:
   * Costes materiales auditados (`$ 62,000.00`),
   * Reserva de depreciación física (`$ 14,000.00`),
   * Contribución macro social (`$ 21,000.00`),
   * Cargo ricardiano de ecualización de dotación de capital (`$ 4,000.00`),
   * Nómina base de los trabajadores activos,
   y divide el excedente operativo neto exactamente en partes iguales (`1/N`) hasta el centavo, trasladando cualquier remanente indivisible ($< N \times \$0.01$) al período siguiente y manteniendo **`Beneficio Retenido Corporativo = $ 0.00`**.

### Playbook D – Orquestación de Paridad Civil, Indexación Inflacionaria y Retorno al Empleo
1. En la **Pestaña 4**, observe al trabajador `CID-0001` inicialmente `Activo en Producción` (`8` trabajadores elegibles compartiendo el excedente).
2. Pulse **1. Suspender Trabajador Sorteado por Mandato**:
   * `CID-0001` pasa a `En Mandato de Consejo (Remunerado por el Estado)`; el reparto empresarial se recalcula automáticamente entre los `7` trabajadores activos restantes (`Estipendio Estatal (En Mandato)` mostrado para `CID-0001`).
3. Pulse una o varias veces **2. Aplicar Inflación de Precios (+0,50%) y Recalcular Estipendio Exacto**:
   * Cada pulsación capitaliza la serie `PriceIndexSeries` un $+0,50\%$ y actualiza el estipendio estatal de `CID-0001` en la proporción exacta `current_index / entry_index`.
4. Pulse **3. Concluir Mandato y Reincorporar al Puesto Original (>= 180 Días)**:
   * `CID-0001` regresa como `Reincorporado con Estabilidad Protegida` (`8` trabajadores activos nuevamente), con sueldo base mensual actualizado por la inflación acumulada y `stability_locked_until` fijado `180` días hacia adelante.
5. Pulse **4. Probar Intento de Despido Tras Retorno (Bloquear)**:
   * Simula un intento de rescisión laboral `60` días después del retorno, lanzando [`EmploymentStabilityLockError`](../../src/cibersoc/mandate_protection.py) y registrando el bloqueo.

---

## 3. Parametrización Programática mediante API Python

Los ingenieros pueden instanciar y parametrizar directamente los subsistemas centrales desde scripts Python:

```python
from decimal import Decimal
from cibersoc.cybernetics import CompressedSparseRowMatrix, solve_leontief_gross_output_gauss_seidel
from cibersoc.enterprise import SocialistEnterprise, WorkerMember

matrix_a = CompressedSparseRowMatrix.from_dense([[0.10, 0.20], [0.05, 0.15]])
gross_x = solve_leontief_gross_output_gauss_seidel(matrix_a, final_demand=[120.0, 80.0])

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
print('Pagos por trabajador:', receipt.payouts)
```

---

## 4. Ejecución de Verificación Automatizada y QA del 100% de Cobertura

Ejecute la suite *headless* `pytest` + `pytest-qt` + `coverage` exigiendo **100% de cobertura de sentencias y ramas condicionales (*branches*)**, **Clean Code con cero comentarios/docstrings** y **integridad autónoma del proyecto**:

```bash
cd cibersoc
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -v --cov=cibersoc --cov-branch --cov-report=term-missing --cov-fail-under=100
```
La suite también ejecuta la **auditoría de integridad** (`btn_run_audit`) de forma programática para garantizar que ningún archivo fuente contenga comentarios ni docstrings, conforme a la política Clean‑Code del proyecto.
