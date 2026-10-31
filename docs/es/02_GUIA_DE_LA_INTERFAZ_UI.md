# 02. Guía de la Interfaz de Usuario (UI)

## 1. Arquitectura Visual y Sistema de Diseño *Dark Cappuccino*

La aplicación cliente de **CIBERSOC** ([`CiberSocMainWindow`](../../src/cibersoc/ui/main_window.py)) está construida en **PySide6 (Qt 6.12)** como un instrumento institucional sobrio de control y simulación, libre de frivolidades visuales. Su ergonomía cromática está gobernada por [`DarkCappuccinoPalette`](../../src/cibersoc/ui/theme.py):

| Token | Código Hex | Asignación Funcional |
| :--- | :--- | :--- |
| `bg_espresso_deep` | `#16110E` | Lienzo estructural profundo de la ventana principal |
| `bg_roast_panel` | `#1F1814` | Contenedores de área de trabajo, cabecera superior y fondo del lienzo topológico |
| `bg_moka_card` | `#29201B` | Tablas interactivas, botones, controles numéricos y nodos de consejo no seleccionados |
| `bg_roast_elevated` | `#362A23` | Pestañas activas, cabeceras de tabla y resaltado del nodo de consejo inspeccionado |
| `border_warm_roast` | `#4A3930` | Divisores estructurales nítidos de 1px y enlaces inactivos de la malla |
| `text_ivory_primary` | `#F4EAD8` | Tipografía primaria de alto contraste y telemetría monoespaciada |
| `text_cream_secondary` | `#D7C5B0` | Subtítulos, métricas secundarias de nodos y etiquetas de pestañas inactivas |
| `accent_crema_amber` | `#C89B6D` | Bordes activos, títulos de sección y flujos ascendentes de demandas ciudadanas (`↑`) |
| `accent_sage_ok` | `#84A97C` | Directrices descendentes obligatorias de plebiscitos (`↓`) |
| `accent_terracotta_alert` | `#C26653` | Botones de prueba de salvaguardas constitucionales (`#AlertActionButton`) |

> **Por qué importa:** Las elecciones cromáticas garantizan un índice de contraste mínimo de 4,5:1 (WCAG AA) en todos los monitores compatibles, haciendo la interfaz accesible a usuarios con discapacidad visual moderada.

---

## 2. Barra Superior Global y Conmutación Nativa de Idioma (`i18n`)

Ubicada en la franja superior de la ventana, la **Cabecera Global** expone elementos permanentes:
1. **Emblema de las Alas de la Libertad e Identidad del Sistema (`lbl_header_emblem`):** Emblema heráldico-constructivista que fusiona las Alas de la Libertad con engranaje cibernético y grilletes rotos bajo la paleta Dark Cappuccino, reflejando el impulso incesante de emancipación popular y ruptura de muros autocráticos. Constituye también el icono oficial de la aplicación y del Dock de macOS.
2. **Selector Instantáneo de Idioma (`cmb_language`):** Admite conmutación fluida entre **Inglés Británico (`English (UK) — en-GB`)**, **Portugués (`Português — pt`)** y **Español (`Español — es`)**.
   * Seleccionar un nuevo idioma invoca [`LocalizationCatalog.switch_locale`](../../src/cibersoc/i18n/translator.py), retraduciendo al instante **cada widget, título de pestaña, cabecera y celda de tabla, etiqueta del lienzo topológico, carta arquitectónica y evento histórico de la consola de auditoría** sin reiniciar el estado de la simulación.
3. **Controles de Escala Tipográfica (`A-`, `A+`, `Aa`):** Ajuste dinámico de fuente (mínimo de 12 pt, atajos `Ctrl++`, `Ctrl+-`, `Ctrl+0`).
4. **Insignia del Ciclo Demárquico Activo (`lbl_cycle_badge`):** Indica el ciclo de sorteo vigente (`CICLO DEMÁRQUICO #01`, `#02`, etc.).

> **Consejo:** El selector de idioma es accesible por teclado (`Alt+L`). Pulsar `Enter` tras la selección dispara la traducción de forma síncrona.

---

## 3. Navegación por las Seis Áreas Operativas de Trabajo

### 3.1 Malla Federada y Ministerios (`tabs.councils`)
* **Panel Izquierdo — Malla Escalonada Interactiva de Consejos ([`CouncilMeshCanvas`](../../src/cibersoc/ui/mesh_canvas.py)):**
  * Renderiza en tiempo real los 4 niveles federados: **Consejo Federal de Brasil** (arriba), **Consejo Estatal de Paraná**, **Consejo Municipal de Curitiba** y los dos consejos barriales de base (**Consejo Sectorial Boqueirão** y **Consejo Sectorial Matriz**).
  * **Selección de Consejo:** Haga clic directamente sobre cualquier bloque rectangular del lienzo *o* utilice el selector **Inspeccionar Nivel de Consejo (`cmb_council`)**. Ambos controles permanecen sincronizados bidireccionalmente.
  * **Canales Direccionales Vivos:** Las líneas continuas ámbar-crema a la izquierda (`↑`) se iluminan cuando las demandas vecinales ascienden por la malla; las líneas discontinuas verde salvia a la derecha (`↓`) se iluminan cuando las directrices macroeconómicas obligatorias descienden a todos los Consejos.
  * **Escalar Demanda Vecinal (`btn_escalate_demand`):** Despacha una demanda concreta de salud/transporte desde `CONS-SET-BOQUEIRAO` a través de `Municipal -> Estatal -> Federal`, actualizando los contadores ascendentes (`↑Dem`).
* **Panel Derecho — Resolución Granular de Funciones:**
  * **Cuadro del Secretario General (`grp_secretary`):** Muestra matrícula, estrato de origen, peso unitario de voto (`1`) y ausencia explícita de veto o decreto. Ofrece **Ordenar Agenda y Autenticar Mayoría (`btn_sg_authenticate`)** y **Probar Intento de Veto/Decreto Autocrático (`btn_sg_veto_test`)**.
  * **Panel de Proporcionalidad Matemática (`lbl_council_proportionality`):** Presenta la justificación lógica rigurosa y métricas analíticas de escaños del consejo (ej.: Consejo Municipal de Curitiba con 20 escaños, estrictamente proporcional 1:1 a la suma de 20 miembros de los consejos sectoriales dependientes Boqueirão [10] y Matriz [10], asegurando 4 integrantes en Justicia para el Jurado Popular sin saturar la cuarentena muestral).
  * **Tabla de Cámaras Equivalentes a Ministerios (`tbl_ministries`):** Enumera cada [`MinistryPortfolio`](../../src/cibersoc/sortition.py) del Consejo seleccionado, su consejero relator sorteado, condición cívica (`Civil Sorteado` vs `Militar Técnico`) y dotación de la cámara. Observe que el `Ministerio de Defensa y Ejército Nacional` aparece exclusivamente al inspeccionar el Consejo Federal y es 100% civil.
  * **Cuadro de Mando del Ministerio de Defensa (`grp_defence`):** Permite emitir una **Orden Civil Multifirma (`btn_defence_order`)** o probar el **Bloqueo de Movilización Autónoma de General (`btn_defence_block`)**.

### 3.2 Sorteo y Cuarentena (`tabs.sortition`)
* **Resumen de Control (`lbl_sortition_summary`):** Muestra ciclo activo, padrón total (`320` en jurisdicciones federadas), consejeros en ejercicio (`76` en los 5 consejos), exconsejeros bloqueados en cuarentena y reelección consecutiva (`0` invariante).
* **Ejecutar Siguiente Ciclo de Sorteo (`btn_next_cycle`):** Concluye los mandatos vigentes, ingresa a los consejeros salientes en cuarentena obligatoria fuera de la urna, sortea nuevos consejos vía `Commit-Reveal SHA-256` y verifica todas las pruebas.
* **Probar Registro de Candidatura Partidaria (`btn_block_election`):** Dispara [`ElectoralOperationForbiddenError`](../../src/cibersoc/sortition.py) y registra el bloqueo constitucional.
* **Tabla de Pruebas Criptográficas (`tbl_proofs`):** Muestra `Merkle Root`, `Cuotas Estratificadas de Hamilton` e insignia de verificación `SHA-256` de cada Consejo.

### 3.3 Macroasignación Cibernética (`tabs.cybernetics`)
* **Controles de Papeletas (`spn_votes_edu`, `spn_votes_health`) y Botón de Escrutinio (`btn_run_plebiscite`):** Parametrizan el recuento de papeletas anónimas entre `+5% Educación Pública` vs `+5% Salud Pública`, resuelven la producción bruta de Leontief y la Armonía de corto plazo de Cockshott y difunden la directriz vinculante.
* **Botones de Salvaguarda Constitucional:** **Probar Nombre de Candidato en Papeleta (`btn_block_person_pleb`)** y **Simular Desviación Presupuestaria del Consejo (`btn_block_council_override`)** prueban el bloqueo inmediato frente a temas electorales personalizados o desviaciones burocráticas.
* **Tabla de Matriz Insumo-Producto (`tbl_cyber`):** Expone cuota votada (`%`), demanda final $y^*$, producción bruta $x = (\mathbf{I}-\mathbf{A})^{-1}y^*$, trabajo incorporado $H$ e índice de Armonía a corto plazo por sector.

### 3.4 Empresa Sin CEO y Retorno Civil (`tabs.enterprise`)
* **Panel Izquierdo — Libro Mayor de la Empresa Socialista (`grp_enterprise_ledger`):**
  * Ajuste los **Ingresos Operativos del Período (`spn_revenue`)** y pulse **Ejecutar Reparto Igualitario 1/N (`btn_distribute_profit`)** para recalcular cuotas exactas en coma fija por trabajador, retención corporativa cero (`$ 0.00`) y remanente indivisible de centavos.
  * **Tabla de Trabajadores (`tbl_workers`):** Enumera estado laboral (`Activo en Producción`, `En Mandato de Consejo` o `Reincorporado con Estabilidad`), sueldo base mensual y cuota igualitaria de excedente.
  * **Probar Nombramiento de CEO (`btn_block_ceo`):** Demuestra el rechazo inmediato de cargos ejecutivos jerárquicos.
* **Panel Derecho — Ciclo de Mandato del Ciudadano Sorteado (`grp_mandate_lifecycle`):**
  * Cuatro botones secuenciales guían al trabajador monitorizado (`CID-0001`) por: **(1) Suspensión por Mandato**, **(2) Ajuste Inflacionario de `+0,50%`**, **(3) Reincorporación al Puesto con Bloqueo $\ge 180$ Días** y **(4) Bloqueo de Despido Tras Retorno**.

### 3.5 Axiomas Arquitectónicos e Integridad (`tabs.charter`)
* Muestra la Carta Arquitectónica autónoma de CIBERSOC y sus 7 axiomas estructurales en el idioma activo. Al pulsar **Ejecutar Escaneo Completo de Clean Code, Documentación Trilingüe e Integridad (`btn_run_audit`)**, inspecciona todos los archivos de `cibersoc`, confirmando `0` manuales faltantes en `en-GB`, `pt` y `es` y conformidad `True` de Clean Code sin comentarios.

### 3.6 README y Documentación del Sistema (`tabs.readme`)
* Visualizador nativo integrado (`QTextBrowser` con soporte completo de Markdown) para leer `README.md` y todos los manuales técnicos sin abandonar la interfaz de escritorio.
* **Selector de Documentos (`cmb_doc_selector`):** Permite navegar al instante entre el `README.md` y los 4 manuales técnicos en la carpeta `docs/` en el idioma activo (01. Fundamentos Teóricos, 02. Guía de la UI, 03. Manual del Simulador, 04. Mecánica Subyacente).
* **Hiperenlaces Interactivos:** Al hacer clic en cualquier enlace relativo de Markdown en el texto, el visor carga de inmediato el documento de destino y sincroniza el selector.
* **Botón de Retorno Rápido (`btn_open_readme`):** Restaura en un clic la vista del `README.md`.
* **Escala Tipográfica Responsiva:** El texto de la documentación responde dinámicamente al tamaño de fuente seleccionado (mínimo de 12 pt hasta 32 pt).

### 3.7 Simulación Nacional — Motor SEEM (`tabs.simulation`)
* **Años por paso (`spn_years_step`):** Avanza tantos años como elija en un clic (de 1 a 1000). **No hay límite total**: la simulación continúa todo el tiempo que desee, hasta que pulse *Reiniciar Simulación*.
* **Cómo leer el mapa 3D** (panel plegable *Cómo leer este mapa*, disponible en los tres idiomas):
  * **Torres = IDH.** Una torre por estado; la altura y el color (rojo → dorado → verde) muestran el IDH.
  * **Anillos en el suelo = población.** El tamaño del anillo es proporcional al número de habitantes del estado. Los anillos son fijos.
  * **Partículas en órbita = ciudadanos (simbólico).** Cada estado recibe el mismo número de puntos, así que **no** miden la población y un punto no es una persona.
* **Glosario mostrado en el panel:**
  * **Población:** todas las personas que viven en un estado (anillo) o en todo el país (panel superior izquierdo).
  * **Ciudadanos:** habitantes que pueden ser sorteados para gobernar; se sortea uno por cartera cada año y nadie sirve dos veces. El panel muestra cuántos ya fueron sorteados.
  * **IDH (Índice de Desarrollo Humano):** nota de 0 a 1 que combina salud, educación e ingresos; cuanto mayor, mejor.
  * **GINI:** desigualdad de ingresos de 0 (todos ganan lo mismo) a 1 (una sola persona concentra todo); cuanto menor, mejor.
  * **Empleo:** proporción de la fuerza laboral que tiene trabajo.

---

## 4. Consola Persistente de Rastro de Auditoría (`grp_audit_console`)

Anclada en el borde inferior de todas las áreas operativas, la consola monoespaciada de solo lectura presenta los 25 registros [`LocalizedAuditEvent`](../../src/cibersoc/ui/state.py) más recientes. Cada paso simulado y bloqueo constitucional añade una entrada determinista que se vuelve a renderizar automáticamente al cambiar de idioma.

---

## 5. Arquitectura Responsiva Multipantalla (`ResponsiveLayoutMode`)

`CiberSocMainWindow` y `CouncilMeshCanvas` se adaptan dinámicamente desde pantallas compactas (`680x500`) hasta monitores de ultraalta definición (`2560x1440`+):
* **Reorganización por Punto de Corte (`< 960px` `COMPACT` vs `>= 960px` `EXPANDED`):** Por debajo de `960px`, los divisores `QSplitter` de doble panel (`splitter_councils`, `splitter_enterprise`) pasan a apilamiento vertical, las filas de acción `QBoxLayout` fluyen de arriba abajo y las cabeceras de `QTableWidget` adoptan `ResizeToContents` con desplazamiento suave por píxel. Desde `960px` en adelante, los paneles se expanden horizontalmente con columnas en modo `Stretch`.
* **Áreas de Trabajo en `QScrollArea` y Divisor Vertical Proporcional:** Cada pestaña operativa se aloja dentro de un `QScrollArea` sin marco (`widgetResizable = True`) junto con `main_vertical_splitter`, evitando desbordamientos horizontales o recortes verticales en ventanas reducidas.
* **Escalado Dinámico de `CouncilMeshCanvas`:** Los rectángulos de nodos, conectores direccionales y leyendas superiores escalan matemáticamente según las dimensiones reales del widget con elisión tipográfica (`QFontMetrics.elidedText`), garantizando cero colisiones geométricas en cualquier tamaño de ventana.

---

## 6. Atajos Rápidos para Usuarios Avanzados

| Acción | Atajo | Efecto |
|---|---|---|
| Abrir selector de idioma | `Alt+L` | Conmutación instantánea de idioma |
| Escalar demanda vecinal aleatoria | `Ctrl+E` | Envía una demanda a través de la malla |
| Actualizar malla tras sorteo | `Ctrl+R` | Redibuja el grafo de consejos |
| Ejecutar auditoría completa | `Ctrl+Shift+A` | Ejecuta verificación de Clean Code, documentación e integridad |
| Guardar checkpoint (automático al cerrar) | – | Cerrar la ventana principal dispara `closeEvent` → escribe `population.json`, `mesh.json`, `audit_snapshot.json` en una carpeta con marca de tiempo bajo `simulation_data/checkpoints/` |

---

*Todos los elementos de la interfaz son completamente navegables por teclado y exponen nombres accesibles para lectores de pantalla mediante la propiedad `accessibleName` de Qt.*
