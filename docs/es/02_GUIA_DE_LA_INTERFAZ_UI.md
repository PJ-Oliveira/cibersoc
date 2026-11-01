# 02. Guía de la Interfaz de Usuario (UI)

## 1. Arquitectura Visual y Sistema de Diseño *Constructivist Espresso* (`DarkCappuccinoPalette`)

El cliente de escritorio de **CIBERSOC** ([`CiberSocMainWindow`](../../src/cibersoc/ui/main_window.py)) está construido en **PySide6 (Qt 6.12)**. Su ergonomía visual sobria y de baja fatiga está gobernada por `ConstructivistEspressoPalette` (`DarkCappuccinoPalette`) en [`theme.py`](../../src/cibersoc/ui/theme.py):

| Token | Código Hex | Función |
| :--- | :--- | :--- |
| `bg_espresso_deep` | `#16110E` | Lienzo estructural profundo de la ventana principal |
| `bg_roast_panel` | `#1F1814` | Contenedores de área de trabajo, cabecera superior y fondo topológico |
| `bg_moka_card` | `#29201B` | Tablas interactivas, botones, controles numéricos y nodos no seleccionados |
| `bg_roast_elevated` | `#362A23` | Cabeceras de pestañas activas, secciones de tabla y nodo inspeccionado |
| `border_warm_roast` | `#4A3930` | Divisores estructurales nítidos de 1 px y enlaces inactivos de la malla |
| `text_ivory_primary` | `#F4EAD8` | Tipografía primaria de alto contraste y telemetría monoespaciada |
| `text_cream_secondary` | `#D7C5B0` | Subtítulos, métricas secundarias y etiquetas de pestañas inactivas |
| `accent_crema_amber` | `#C89B6D` | Bordes activos, títulos de sección y flujos ascendentes ciudadanos (`↑`) |
| `accent_sage_ok` | `#84A97C` | Directrices descendentes vinculantes (`↓`) y sellos verificados |
| `accent_terracotta_alert` | `#C26653` | Botones de prueba de salvaguardas constitucionales (`#AlertActionButton`) |

> **Estándar de Accesibilidad:** Cada par texto/fondo cumple una relación de contraste mínima de 4,5:1 (WCAG AA), combinada con la tipografía integrada **Atkinson Hyperlegible** y un tamaño mínimo garantizado de **12 pt** en todos los controles.

---

## 2. Barra Superior Global y Conmutación `i18n` en Vivo

Controles permanentes en la franja superior de la ventana principal:
1. **Emblema Alas de la Libertad e Identidad del Sistema (`lbl_header_emblem`):** Emblema vectorial multirresolución que fusiona alas geométricas, engranaje cibernético industrial y cadenas rotas; define asimismo el icono de ventana y del Dock de macOS.
2. **Selector Instantáneo de Idioma (`cmb_language`):** Conmuta al instante entre **English (UK) — `en-GB`**, **Português — `pt`** y **Español — `es`** mediante `LocalizationCatalog.switch_locale`, retraduciendo cada widget, celda de tabla, nodo del lienzo, axioma de la Carta y evento de auditoría sin reiniciar el estado.
3. **Controles de Escala Tipográfica (`A-`, `A+`, `Aa`):** Escalado dinámico entre **12 pt** y **32 pt** (`Ctrl++`, `Ctrl+-`, `Ctrl+0`) con persistencia de sesión.
4. **Botón de Atajos de Teclado (`?` / `F1`):** Abre un cuadro de referencia localizado con todos los atajos activos.
5. **Insignia del Ciclo Demárquico Activo (`lbl_cycle_badge`):** Muestra el ciclo de sorteo vigente (`CICLO DEMÁRQUICO #01`, `#02`, …).

---

## 3. Seis Áreas Operativas Integradas (Pestañas)

### 3.1 Malla Federada y Ministerios (`tabs.councils`)
- **Panel Izquierdo — Malla Escalonada Interactiva (`CouncilMeshCanvas`):** Topología de 4 niveles (`Federal → Estatal → Municipal → Sectorial`) con nodos seleccionables, selector sincronizado (`cmb_council`), escalado de demandas (`btn_escalate_demand`, `↑`) y canales descendentes de directrices (`↓`).
- **Panel Derecho — Resolución Granular de Funciones y Cámaras:**
  - **Cuadro del Secretario General (`grp_secretary`):** Muestra matrícula sorteada, estrato, peso unitario de voto (`1`), cero poder de veto/decreto, autenticación de mayoría (`btn_sg_authenticate`) y bloqueo autocrático (`btn_sg_veto_test`).
  - **Panel de Proporcionalidad Matemática (`lbl_council_proportionality`):** Expone las razones exactas de escaños (p. ej., Consejo Municipal de Curitiba con `20` escaños estrictamente proporcionales $1:1$ a los consejos sectoriales Boqueirão `[10]` + Matriz `[10]`).
  - **Tabla de Cámaras Equivalentes a Ministerios (`tbl_ministries`):** Enumera cada `MinistryPortfolio`, relator sorteado, condición civil vs. militar y dotación.
  - **Jurado Popular y Supervisión de Seguridad Pública (`grp_jury_security`):** Adjudica causas en bancada ciudadana impar con rotación determinista de suplente por expediente (`btn_jury_adjudicate`), bloquea sustitución por juez profesional (`btn_jury_block`), despacha patrulla vinculada a orden civil (`btn_security_dispatch`) y bloquea coerción unilateral (`btn_security_block`).
  - **Compuerta Civil del Ministerio de Defensa (`grp_defence`):** Emite órdenes civiles multifirma (`btn_defence_order`) y bloquea movilizaciones unilaterales de generales (`btn_defence_block`).

### 3.2 Sorteo, Cuarentena y Habilitación Cívica (`tabs.sortition`)
- **Resumen de Control (`lbl_sortition_summary`):** Muestra ciclo activo, padrón local (`320`), consejeros en ejercicio (`76` en los 5 consejos), exconsejeros en cuarentena y reelección consecutiva (`0` invariante).
- **Acciones de Sorteo y Snapshot:** Ejecuta el siguiente ciclo `Commit-Reveal SHA-256` (`btn_next_cycle`), prueba el bloqueo constitucional de candidatura partidaria (`btn_block_election` -> `ElectoralOperationForbiddenError`) o guarda un snapshot determinista (`btn_save_checkpoint`) en `simulation_data/checkpoints/`.
- **Planificador de Exámenes de Habilitación Cívica (`grp_civic_enablement`):** Registra la cualificación periódica en las 4 materias troncales (`btn_civic_round`), aplicando exención estatutaria automática desde los 60 años y habilitación para auditoría técnica (`>= 70%`).
- **Tabla de Pruebas Criptográficas (`tbl_proofs`):** Muestra raíz de Merkle SHA-256 (huella digital inalterable del padrón elegible), cuotas enteras de Hamilton por estrato y sello `VERIFICADO (SHA-256)`.

### 3.3 Macroasignación Cibernética (`tabs.cybernetics`)
- **Controles de Papeletas (`spn_votes_edu`, `spn_votes_health`) y Escrutinio (`btn_run_plebiscite`):** Ejecuta un plebiscito anónimo resistente a coacción, deriva la demanda final física a partir de cuotas exactas de trabajo incorporado ($s_j = 100 \cdot H_j y_j^* / \sum_k H_k y_k^*$), resuelve producción bruta CSR de Leontief (`rho(A) < 1,0` = economía productiva sin bucle infinito de insumos), aplica Armonía a corto plazo de Cockshott y difunde la directriz vinculante.
- **Ajuste Iterativo del Plan y Frontera Ecológica de Carbono (`grp_cyber_feedback`):** Simula retroalimentación de la razón demanda/trabajo `p/v` (`spn_clearing_ratio`: `> 1` escasez -> ampliar meta; `< 1` excedente -> reducir meta) y cumplimiento del techo físico de carbono (`spn_carbon_budget`, `btn_iterate_plan`, factor `lambda*`).
- **Salvaguardas Constitucionales:** Bloquea nombres de candidatos en papeleta (`btn_block_person_pleb`) y desviaciones presupuestarias de consejos (`btn_block_council_override`).
- **Tabla de Matriz Insumo-Producto (`tbl_cyber`):** Expone cuota de trabajo votada (`%`), demanda final $y^*$ (bienes netos entregados a la ciudadanía), producción bruta $x$ (total producido incluidos insumos intermedios), trabajo incorporado de Jacobi $H$ (horas directas + indirectas por unidad) y Armonía por sector.

### 3.4 Empresa Sin CEO y Retorno Civil (`tabs.enterprise`)
- **Panel Izquierdo — Libro Mayor de la Empresa Cooperativa (`grp_enterprise_ledger`):** Muestra la máscara de usufructo colectivo `1,0,0,0` (`Uso=Sí`, `Venta/Compra/Herencia=No`), ajusta los Ingresos Operativos del Período (`spn_revenue`) y calcula cuotas racionales exactas $1/N$ por días enteros (`btn_distribute_profit`) vía `Decimal` y `math.gcd`, manteniendo el beneficio retenido corporativo idénticamente en `$0.00`. Intentar nombrar un CEO (`btn_block_ceo`) lanza `OrganisationalViolationError`.
- **Panel Derecho — Ciclo de Mandato del Ciudadano Sorteado (`grp_mandate_lifecycle`):** Guía a `CID-0001` por (1) Suspensión por Mandato, (2) Indexación de Estipendio por IPC (`+0,50%`), (3) Reincorporación Protegida ($\ge 180$ días) y (4) Bloqueo de Despido Tras Retorno (`EmploymentStabilityLockError`).

### 3.5 Axiomas, Integridad y Documentación (`tabs.charter_docs`)
- **Carta Arquitectónica y Escáner de Integridad (`grp_charter`):** Presenta los 7 axiomas estructurales traducidos, exporta arte FullHD localizado del emblema (`btn_export_fullhd_wallpaper`) y ejecuta `btn_run_audit`, verificando 0 comentarios `#` y 0 docstrings en todos los archivos `.py` (`tokenize` + `ast.parse`) y paridad documental trilingüe íntegra.
- **Visor de README y Documentación del Sistema (`grp_readme`):** Visor nativo Markdown con renderizado estilizado de **diagramas Mermaid** (`QTextBrowser`), selector instantáneo (`cmb_doc_selector`), navegación por enlaces relativos, retorno rápido (`btn_open_readme`) y escala tipográfica hasta 32 pt.

### 3.6 Simulación Nacional — Motor 3D SEEM (`tabs.simulation`)
- **Escala Nacional y Topología Continental:** Simula **150.700.000 habitantes** distribuidos en 10 polos macrorregionales brasileños sobre una silueta vectorial continental con arcos 3D Bézier de flujos insumo-producto interregionales, torres de IDH, anillos poblacionales y consejeros regionales con cuarentena posmandato (`70` activos/año en 7 carteras × 10 polos).
- **Marcador Comparativo en Vivo de 3 Regímenes (`cmb_regime` + HUD):** Evalúa simultáneamente tres sistemas bajo **Números Aleatorios Comunes (CRN)** (idénticos choques climáticos y económicos anuales): **(A) CIBERSOC (Sorteo + 1/N + Plebiscito)**, **(C) Burocracia Estatal (Mando Top-Down)** y **(B) Capitalismo Electoral (Partidos + CEOs)**, mostrando lado a lado el **IDH y el GINI reales de los 3 regímenes** tanto en el HUD 3D como en la barra superior de estado, además de exportar trayectorias CSV/JSON.

---

## 4. Consola Persistente de Auditoría y Diseño Responsivo

- **Consola de Auditoría (`grp_audit_console`):** Anclada en la base de la ventana en todas las pestañas, mostrando los 25 registros `LocalizedAuditEvent` más recientes retraducidos al cambiar de idioma.
- **Punto de Corte Adaptativo (`< 960 px` `COMPACT` vs. `>= 960 px` `EXPANDED`):** Apila divisores y barras de acción verticalmente en pantallas estrechas, garantizando cero desbordamiento horizontal hasta `680×500`.

---

## 5. Referencia de Atajos de Teclado

| Atajo | Ámbito | Acción |
| :--- | :--- | :--- |
| `F1` o `?` | Global | Abrir diálogo localizado de Atajos de Teclado |
| `Ctrl+1` … `Ctrl+6` | Global | Cambiar directamente a la Pestaña 1 … 6 |
| `Ctrl++` / `Ctrl+=` | Global | Aumentar tamaño de fuente (`A+`, hasta 32 pt) |
| `Ctrl+-` | Global | Reducir tamaño de fuente (`A-`, mínimo 12 pt) |
| `Ctrl+0` | Global | Restablecer tamaño de fuente predeterminado (`Aa`) |
| `F11` | Global | Alternar modo de pantalla completa (*fullscreen*) |
| `Alt+Up` / `Alt+Down` | Global | Recorrer el consejo inspeccionado en la malla federativa de 4 niveles |
| `Space` | Pestaña 6 (SEEM) | Iniciar / Pausar simulación anual continua |
| `Right` | Pestaña 6 (SEEM) | Avanzar simulación según los años en `spn_years_step` |
| `R` | Pestaña 6 (SEEM) | Reiniciar simulación SEEM al Año 2026 |
| `+` / `-` | Pestaña 6 (SEEM) | Acercar / Alejar cámara 3D |
