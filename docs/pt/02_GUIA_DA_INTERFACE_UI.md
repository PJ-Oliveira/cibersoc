# 02. Guia da Interface de Usuário (UI)

## 1. Arquitetura Visual e Sistema de Design *Constructivist Espresso* (`DarkCappuccinoPalette`)

O cliente desktop do **CIBERSOC** ([`CiberSocMainWindow`](../../src/cibersoc/ui/main_window.py)) foi construído em **PySide6 (Qt 6.12)**. A interface adota uma linguagem visual sóbria e ergonômica definida por `ConstructivistEspressoPalette` (`DarkCappuccinoPalette`) em [`theme.py`](../../src/cibersoc/ui/theme.py):

| Token | Código Hex | Papel Funcional |
| :--- | :--- | :--- |
| `bg_espresso_deep` | `#16110E` | Canvas estrutural profundo da janela principal |
| `bg_roast_panel` | `#1F1814` | Contêineres das áreas de trabalho, barra superior global e fundo topológico |
| `bg_moka_card` | `#29201B` | Tabelas interativas, botões, controles numéricos e nós não selecionados |
| `bg_roast_elevated` | `#362A23` | Cabeçalhos de abas ativas, seções de tabelas e destaque do conselho selecionado |
| `border_warm_roast` | `#4A3930` | Divisores estruturais nítidos de 1 px e conexões inativas da malha |
| `text_ivory_primary` | `#F4EAD8` | Tipografia primária de alto contraste e telemetria monoespaçada |
| `text_cream_secondary` | `#D7C5B0` | Subtítulos, métricas secundárias e rótulos de abas inativas |
| `accent_crema_amber` | `#C89B6D` | Bordas ativas, títulos de seção e fluxos ascendentes de demandas cidadãs (`↑`) |
| `accent_sage_ok` | `#84A97C` | Diretrizes descendentes compulsórias (`↓`) e selos verificados |
| `accent_terracotta_alert` | `#C26653` | Botões de teste de salvaguardas constitucionais (`#AlertActionButton`) |

> **Padrão de Acessibilidade:** Todos os pares texto/fundo cumprem índice de contraste mínimo de 4,5:1 (WCAG AA), combinados à fonte embarcada **Atkinson Hyperlegible** e tamanho mínimo garantido de **12 pt** em todos os controles.

---

## 2. Barra Superior Global e Troca de Idioma `i18n` em Tempo Real

Controles persistentes no topo da janela principal:
1. **Emblema Asas da Liberdade e Identidade do Sistema (`lbl_header_emblem`):** Emblema vetorial multirresolução que une asas geométricas, engrenagem cibernética industrial e elos rompidos; define também o ícone da janela e da Dock do macOS.
2. **Seletor Instantâneo de Idioma (`cmb_language`):** Alterna instantaneamente entre **English (UK) — `en-GB`**, **Português — `pt`** e **Español — `es`** via `LocalizationCatalog.switch_locale`, retraduzindo cada widget, célula de tabela, nó do canvas, axioma da Carta e histórico de auditoria sem reiniciar o estado da simulação.
3. **Controles de Escala Tipográfica (`A-`, `A+`, `Aa`):** Escala responsiva de **12 pt** a **32 pt** (`Ctrl++`, `Ctrl+-`, `Ctrl+0`) com persistência entre sessões.
4. **Botão de Atalhos de Teclado (`?` / `F1`):** Abre um diálogo localizado listando todos os atalhos ativos.
5. **Selo do Ciclo Demárquico Ativo (`lbl_cycle_badge`):** Exibe o ciclo de sorteio vigente (`CICLO DEMÁRQUICO #01`, `#02`, …).

---

## 3. Seis Áreas Operacionais Integradas (Abas)

### 3.1 Malha Federada e Ministérios (`tabs.councils`)
- **Painel Esquerdo — Malha Escalonada Interativa (`CouncilMeshCanvas`):** Topologia em 4 níveis (`Federal → Estadual → Municipal → Setorial`) com nós clicáveis, seletor sincronizado (`cmb_council`), escalonamento de demandas (`btn_escalate_demand`, `↑`) e canais descendentes de diretrizes (`↓`).
- **Painel Direito — Resolução Granular de Funções e Câmaras:**
  - **Quadro do Secretário-Geral (`grp_secretary`):** Exibe matrícula sorteada, estrato, peso unitário de voto (`1`), zero poder de veto/decreto, autenticação de maioria (`btn_sg_authenticate`) e teste de bloqueio autocrático (`btn_sg_veto_test`).
  - **Banner de Proporcionalidade Matemática (`lbl_council_proportionality`):** Mostra a razão analítica exata de assentos (ex.: Conselho Municipal de Curitiba com `20` vagas estritamente proporcionais $1:1$ aos conselhos setoriais Boqueirão `[10]` + Matriz `[10]`).
  - **Tabela de Câmaras Equivalentes a Ministérios (`tbl_ministries`):** Lista cada `MinistryPortfolio`, relator sorteado, condição civil vs. militar e efetivo.
  - **Júri Popular e Supervisão de Segurança Pública (`grp_jury_security`):** Julga casos em bancada cidadã ímpar com rotação determinística de suplente por processo (`btn_jury_adjudicate`), bloqueia substituição por juiz de carreira (`btn_jury_block`), despacha patrulha vinculada a ordem civil (`btn_security_dispatch`) e bloqueia coerção unilateral (`btn_security_block`).
  - **Trava Civil do Ministério da Defesa (`grp_defence`):** Emite ordens civis multi-assinatura (`btn_defence_order`) e bloqueia mobilização unilateral de general (`btn_defence_block`).

### 3.2 Sorteio, Quarentena e Habilitação Cívica (`tabs.sortition`)
- **Resumo Operacional (`lbl_sortition_summary`):** Exibe ciclo ativo, cadastro local (`320`), conselheiros em exercício (`76` nos 5 conselhos), ex-conselheiros em quarentena e reincidência consecutiva (`0` invariante).
- **Ações de Sorteio e Snapshot:** Executa o próximo ciclo `Commit-Reveal SHA-256` (`btn_next_cycle`), testa o bloqueio constitucional de candidatura partidária (`btn_block_election` -> `ElectoralOperationForbiddenError`) ou salva um snapshot determinístico (`btn_save_checkpoint`) em `simulation_data/checkpoints/`.
- **Agendador de Exames de Habilitação Cívica (`grp_civic_enablement`):** Monitora a qualificação periódica nas 4 disciplinas essenciais (`btn_civic_round`), aplicando isenção estatutária automática a partir dos 60 anos e habilitação para auditoria técnica (`>= 70%`).
- **Tabela de Provas Criptográficas (`tbl_proofs`):** Exibe raiz de Merkle SHA-256 (impressão digital imutável do cadastro elegível), cotas inteiras de Hamilton por estrato e selo `VERIFICADA (SHA-256)`.

### 3.3 Macro-Alocação Cibernética (`tabs.cybernetics`)
- **Controles de Cédulas (`spn_votes_edu`, `spn_votes_health`) e Apuração (`btn_run_plebiscite`):** Executa plebiscito anônimo resistente à coação, deriva a demanda final física a partir das cotas exatas de trabalho incorporado ($s_j = 100 \cdot H_j y_j^* / \sum_k H_k y_k^*$), resolve produção bruta CSR de Leontief (`rho(A) < 1,0` = economia produtiva sem espiral infinita de insumos), aplica Harmonia de curto prazo de Cockshott e difunde a diretriz vinculante.
- **Ajuste Iterativo do Plano e Fronteira Ecológica de Carbono (`grp_cyber_feedback`):** Simula feedback da razão demanda/trabalho `p/v` (`spn_clearing_ratio`: `> 1` indica falta/fila -> expande meta; `< 1` indica sobra -> reduz meta) e respeito ao teto físico de carbono (`spn_carbon_budget`, `btn_iterate_plan`, escalonamento `lambda*`).
- **Salvaguardas Constitucionais:** Bloqueia nomes de candidatos na cédula (`btn_block_person_pleb`) e desvios orçamentários de conselhos (`btn_block_council_override`).
- **Tabela da Matriz Insumo-Produto (`tbl_cyber`):** Exibe cota de trabalho votada (`%`), demanda final $y^*$ (bens líquidos entregues à sociedade), produção bruta $x$ (total produzido incluindo insumos intermediários), trabalho incorporado de Jacobi $H$ (horas diretas + indiretas por unidade) e índice de Harmonia por setor.

### 3.4 Empresa Sem CEO e Retorno Civil (`tabs.enterprise`)
- **Painel Esquerdo — Livro-Razão da Empresa Cooperativa (`grp_enterprise_ledger`):** Exibe a máscara de usufruto coletivo `1,0,0,0` (`Uso=Sim`, `Venda/Compra/Herança=Não`), ajusta a Receita Operacional do Período (`spn_revenue`) e calcula cotas racionais exatas $1/N$ em dias inteiros (`btn_distribute_profit`) via `Decimal` e `math.gcd`, mantendo retenção corporativa identicamente em `$0.00`. Tentar nomear um CEO (`btn_block_ceo`) dispara `OrganisationalViolationError`.
- **Painel Direito — Ciclo de Mandato do Cidadão Sorteado (`grp_mandate_lifecycle`):** Conduz `CID-0001` por (1) Suspensão por Mandato, (2) Reajuste de Subsídio pelo IPCA (`+0,50%`), (3) Reintegração Protegida ($\ge 180$ dias) e (4) Bloqueio de Demissão Pós-Retorno (`EmploymentStabilityLockError`).

### 3.5 Axiomas, Integridade e Documentação (`tabs.charter_docs`)
- **Carta Arquitetural e Scanner de Integridade (`grp_charter`):** Apresenta os 7 axiomas estruturais traduzidos, exporta arte FullHD localizada do emblema (`btn_export_fullhd_wallpaper`) e executa `btn_run_audit`, verificando 0 comentários `#` e 0 docstrings em todos os arquivos `.py` (`tokenize` + `ast.parse`) e paridade documental trilíngue completa.
- **Leitor de README e Documentação do Sistema (`grp_readme`):** Leitor nativo Markdown com renderização estilizada de **diagramas Mermaid** (`QTextBrowser`), seletor instantâneo (`cmb_doc_selector`), navegação por links relativos, retorno rápido (`btn_open_readme`) e escala tipográfica até 32 pt.

### 3.6 Simulação Nacional — Motor 3D SEEM (`tabs.simulation`)
- **Escala Nacional e Topologia Continental:** Simula **150.700.000 habitantes** distribuídos em 10 polos macrorregionais brasileiros sobre silhueta vetorial continental com arcos 3D Bézier de comércio insumo-produto inter-regional, torres de IDH, anéis populacionais e conselheiros regionais com quarentena pós-mandato (`70` ativos/ano em 7 pastas × 10 polos).
- **Placar Comparativo Ao Vivo dos 3 Regimes (`cmb_regime` + HUD):** Avalia simultaneamente três sistemas sob **Números Aleatórios Comuns (CRN)** (exatamente os mesmos choques climáticos e econômicos anuais): **(A) CIBERSOC (Sorteio + 1/N + Plebiscito)**, **(C) Burocracia Estatal (Comando Top-Down)** e **(B) Capitalismo Eleitoral (Partidos + CEOs)**, exibindo lado a lado o **IDH e o GINI reais dos 3 regimes** tanto no HUD 3D quanto na barra superior de status, além de exportar trajetórias CSV/JSON.

---

## 4. Console Persistente de Auditoria e Layout Responsivo

- **Console de Auditoria (`grp_audit_console`):** Ancorado na base da janela em todas as abas, exibindo os 25 eventos `LocalizedAuditEvent` mais recentes retraduzidos ao vivo na troca de idioma.
- **Ponto de Corte Adaptativo (`< 960 px` `COMPACT` vs. `>= 960 px` `EXPANDED`):** Empilha divisores e barras de ação verticalmente em janelas estreitas, garantindo zero rolagem horizontal até `680×500`.

---

## 5. Referência de Atalhos de Teclado

| Atalho | Escopo | Ação |
| :--- | :--- | :--- |
| `F1` ou `?` | Global | Abrir diálogo localizado de Atalhos de Teclado |
| `Ctrl+1` … `Ctrl+6` | Global | Alternar diretamente para a Aba 1 … 6 |
| `Ctrl++` / `Ctrl+=` | Global | Aumentar tamanho da fonte (`A+`, até 32 pt) |
| `Ctrl+-` | Global | Diminuir tamanho da fonte (`A-`, mínimo 12 pt) |
| `Ctrl+0` | Global | Restaurar tamanho padrão da fonte (`Aa`) |
| `F11` | Global | Alternar modo tela cheia (*fullscreen*) |
| `Alt+Up` / `Alt+Down` | Global | Percorrer conselho inspecionado na malha federativa de 4 níveis |
| `Space` | Aba 6 (SEEM) | Iniciar / Pausar simulação anual contínua |
| `Right` | Aba 6 (SEEM) | Avançar simulação pelo número de anos em `spn_years_step` |
| `R` | Aba 6 (SEEM) | Reiniciar simulação SEEM para o Ano 2026 |
| `+` / `-` | Aba 6 (SEEM) | Aproximar / Afastar câmera 3D |
