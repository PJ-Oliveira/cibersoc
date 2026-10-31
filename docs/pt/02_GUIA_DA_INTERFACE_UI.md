# 02. Guia da Interface de Usuário (UI)

## 1. Arquitetura Visual & Sistema de Design *Dark Cappuccino*

A aplicação cliente do **CIBERSOC** foi construída com **PySide6 (Qt 6.12)**.  A UI segue uma linguagem visual deliberadamente sóbria chamada **Dark Cappuccino** – uma paleta de marrons e cremes muito apagados que maximiza o contraste para legibilidade enquanto evita decorações chamativas.  Todas as cores são definidas em `src/cibersoc/ui/theme.py` e usadas de forma consistente nos widgets:

| Token | Código Hex | Função |
|---|---|---|
| `bg_espresso_deep` | `#16110E` | Fundo da janela principal (canvas estrutural profundo) |
| `bg_roast_panel` | `#1F1814` | Contêineres de área de trabalho, banner superior, fundo do canvas topológico |
| `bg_moka_card` | `#29201B` | Tabelas interativas, botões, spin boxes numéricos, nós de conselho não selecionados |
| `bg_roast_elevated` | `#362A23` | Cabeçalhos de abas ativas, cabeçalhos de seções de tabelas, destaque do nó de conselho selecionado |
| `border_warm_roast` | `#4A3930` | Divisores estruturais nítidos de 1 px e links inativos da malha |
| `text_ivory_primary` | `#F4EAD8` | Tipografia primária de alto contraste, telemetria monoespaçada |
| `text_cream_secondary` | `#D7C5B0` | Subtítulos, métricas secundárias de nós, rótulos de abas inativas |
| `accent_crema_amber` | `#C89B6D` | Bordas ativas, títulos de seção, fluxos ascendentes de demanda cidadã (`↑`) |
| `accent_sage_ok` | `#84A97C` | Diretrizes descendentes compulsórias de plebiscito (`↓`) |
| `accent_terracotta_alert` | `#C26653` | Botões de teste de guardas constitucionais (ex.: `#AlertActionButton`) |

> **Por que isso importa:** As escolhas de cores garantem um índice de contraste mínimo de 4,5:1 (WCAG AA) em todos os monitores suportados, tornando a UI acessível a usuários com deficiência visual moderada.

---

## 2. Barra Superior Global & Troca de Idioma `i18n` ao Vivo

No topo da janela há elementos persistentes:
1. **Emblema das Asas da Liberdade & Identidade do Sistema** — O emblema heráldico-construtivista (`lbl_header_emblem`) une as Asas da Liberdade a uma engrenagem cibernética soviética e grilhões rompidos sob a paleta Dark Cappuccino, simbolizando a busca incessante pela emancipação popular e superação de muralhas autocráticas, definindo também o ícone oficial da janela e da Dock do sistema.
2. **Seletor Instantâneo de Idioma (`cmb_language`)** – alterna entre **Inglês (UK)**, **Português**, e **Espanhol**. Selecionar um idioma chama `LocalizationCatalog.switch_locale`, que **re‑traduz cada widget, título de aba, cabeçalho de tabela, rótulo do canvas, texto da Carta e entradas do console de auditoria** instantaneamente, sem resetar o estado da simulação.
3. **Controle de Escala Tipográfica (`A-`, `A+`, `Aa`)** — Ajuste dinâmico responsivo da fonte (mínimo de 12 pt, atalhos `Ctrl++`, `Ctrl+-`, `Ctrl+0`).
4. **Selo de Ciclo Demárquico Ativo (`lbl_cycle_badge`)** – indica o ciclo de sorteio corrente (`CICLO DEMÁRQUICO #01`, `#02`, …).

> **Dica:** O seletor de idioma recebe foco de teclado (`Alt+L`). Pressionar `Enter` após a seleção dispara a tradução de forma síncrona.

---

## 3. Seis Áreas Operacionais (Abas)

### 3.1 Conselhos & Malha Federada (`tabs.councils`)
- **Painel esquerdo – Malha Escalonada Interativa de Conselhos** (`CouncilMeshCanvas`).  O canvas desenha em tempo real a hierarquia de quatro níveis (Federal → Estadual → Municipal → Setorial).  Os nós são **clicáveis**; ao pairar o mouse aparece uma tooltip com estatísticas do conselho (membros, participação no orçamento, mandatos atuais).
- **Painel direito – Caixa de Resolução de Papéis**:
  - **Caixa do Secretário‑Geral** exibe o ID do titular sorteado, estrato, peso unitário de voto (`1`) e mostra explicitamente *zero poder de veto*.
  - **Banner de Proporcionalidade Matemática** (`lbl_council_proportionality`): Exibe a auditoria analítica e justificativa lógica das vagas (ex.: Conselho Municipal de Curitiba com 20 vagas, rigorosamente proporcional 1:1 à soma de 20 integrantes dos conselhos setoriais Boqueirão [10] e Matriz [10], garantindo 4 assentos para a Justiça e sustentando o quórum do Júri Popular sem sobrecarregar a quarentena amostral).
  - **Tabela de Ministérios** lista cada ministério (ou câmara‑equivalente), o conselheiro sorteado, status civil vs técnico, e número de funcionários.
  - **Caixa de comando da Defesa** permite emitir uma **Ordem Civil Multi‑Assinatura** ou testar o **Bloqueio Autônomo de General**.
- **Visualização de fluxos direcionais:** setas âmbar‑crema (`↑`) iluminam quando uma demanda de bairro sobe a malha; setas verde‑sálvia tracejadas (`↓`) iluminam quando uma diretriz macro‑plebiscitária desce.
- **Atalhos convenientes:** `Ctrl+E` escalona uma demanda aleatória de bairro; `Ctrl+R` refresca a malha após um sorteio.

### 3.2 Sortição & Quarentena (`tabs.sortition`)
- **Rótulo de resumo** (`lbl_sortition_summary`) mostra total de cidadãos cadastrados, conselheiros ativos e quantos estão em quarentena.
- **Botão Próximo Ciclo** (`btn_next_cycle`) encerra os mandatos atuais, coloca os conselheiros que saem em **quarentena criptográfica** (não podem ser re‑selecionados até o próximo ciclo) e sorteia um novo conselho via **Commit‑Reveal SHA‑256** com quotas de Hamilton.
- **Tabela de provas** (`tbl_proofs`) exibe o Merkle root de cada conselho, detalhamento das quotas de Hamilton e selo SHA‑256 – útil para auditorias.
- **Botão de segurança** (`btn_block_election`) demonstra que qualquer tentativa de acionar uma eleição tradicional levanta um `ElectoralOperationForbiddenError`.

### 3.3 Macro‑alocação Cibernética (`tabs.cybernetics`)
- **Spin‑boxes de cédulas** (`spn_votes_edu`, `spn_votes_health`) permitem definir a parcela de um plebiscito binário (ex.: `+5 % Educação` vs `+5 % Saúde`).
- **Botão Executar Plebiscito** (`btn_run_plebiscite`) resolve o sistema Leontief (`CSR` sparse solver) e aplica a **Harmonia de curto‑prazo de Cockshott** para obter um plano de produção viável.  A diretiva resultante é broadcast a todos os conselhos.
- **Botões de guardas constitucionais** permitem testar conteúdo ilegal de cédula (`btn_block_person_pleb`) e simular desvios orçamentários de conselhos (`btn_block_council_override`).
- **Tabela de Input‑Output** (`tbl_cyber`) mostra a parcela votada (`%`), demanda final `$y^*$`, produção bruta `$x = (I-A)^{-1} y^*$`, horas‑trabalho incorporadas `$H$` e índice de Harmonia de curto‑prazo por setor.

### 3.4 Empresa Sem CEO & Retorno Civil (`tabs.enterprise`)
- **Painel esquerdo – Livro‑Razão da Empresa Socialista** (`grp_enterprise_ledger`):
  - Ajuste a *Receita Operacional do Período* (`spn_revenue`).
  - Pressione **Distribuir Lucro 1/N** (`btn_distribute_profit`) para recomputar cotas exatas de trabalhadores usando aritmética racional (`fractions.Fraction`), garantindo retenção corporativa `$0.00`.
  - Tabela de trabalhadores (`tbl_workers`) lista status de emprego (`Ativo na Produção`, `Em Mandato de Conselho`, `Reintegrado com Proteção`), pagamento base mensal e o pagamento igualitário do excedente.
  - **Botão de bloqueio de CEO** demonstra que qualquer tentativa de nomear um CEO levanta um `CEOAppointmentForbiddenError`.
- **Painel direito – Ciclo de Mandato do Cidadão Sorteado** (`grp_mandate_lifecycle`):
  1. **Suspender Mandato** – remove temporariamente o cidadão do conselho.
  2. **Ajuste de Inflação** – aplica um aumento percentual configurável ao subsídio.
  3. **Reintegração Protegida** – garante um bloqueio de ≥ 180 dias antes de uma possível demissão.
  4. **Teste de Bloqueio de Demissão Pós‑Retorno** – mostra que uma demissão após o retorno é rejeitada.

### 3.5 Carta Arquitetural & Auditoria de Integridade (`tabs.charter`)
- Exibe a **Carta Autônoma do CIBERSOC** (os 7 axiomas estruturais) no idioma ativo.
- **Varredura completa de Clean‑Code & Documentação** (`btn_run_audit`) percorre todo o repositório, verifica:
  - Zero manuais ausentes para cada idioma.
  - Conformidade Clean‑Code (sem `TODO`s, pontuação Pylint ≥ 9.5, zero avisos de código morto).
- Os resultados aparecem em um modal e são também registrados no console de auditoria persistente.

### 3.6 README & Documentação do Sistema (`tabs.readme`)
- Visualizador integrado nativo (`QTextBrowser` com renderização rica em Markdown) que permite ler o `README.md` e toda a documentação técnica sem sair da aplicação desktop.
- **Seletor de Documentos (`cmb_doc_selector`):** Permite alternar instantaneamente entre o `README.md` e os 4 manuais técnicos da pasta `docs/` no idioma atualmente selecionado (01. Fundamentos Teóricos, 02. Guia da UI, 03. Manual do Simulador, 04. Mecânica Subjacente).
- **Navegação Clicável por Hiperlinks:** Clicar em qualquer link Markdown relativo dentro do texto carrega o documento correspondente diretamente no visualizador e sincroniza o seletor.
- **Botão de Retorno Rápido (`btn_open_readme`):** Restaura a exibição imediata do `README.md`.
- **Acessibilidade e Zoom:** O conteúdo adapta-se em tempo real ao tamanho de fonte configurado pelo usuário (mínimo de 12 pt até 32 pt).

### 3.7 Simulação Nacional — Motor SEEM (`tabs.simulation`)
- **Anos por passo (`spn_years_step`):** Avança quantos anos você escolher em um clique (de 1 a 1000). **Não há limite total**: a simulação continua pelo tempo que você quiser, até você pressionar *Reiniciar Simulação*.
- **Como ler o mapa 3D** (painel recolhível *Como ler este mapa*, disponível nos três idiomas):
  - **Torres = IDH.** Uma torre por estado; a altura e a cor (vermelho → dourado → verde) mostram o IDH.
  - **Anéis no chão = população.** O tamanho do anel é proporcional ao número de habitantes do estado. Os anéis são fixos.
  - **Partículas em órbita = cidadãos (simbólico).** Todo estado recebe o mesmo número de pontos, então eles **não** medem a população e um ponto não é uma pessoa.
- **Glossário exibido no painel:**
  - **População:** todos que vivem em um estado (anel) ou no país inteiro (painel superior esquerdo).
  - **Cidadãos:** habitantes que podem ser sorteados para governar; sorteia-se um por pasta a cada ano e ninguém serve duas vezes. O painel mostra quantos já foram sorteados.
  - **IDH (Índice de Desenvolvimento Humano):** nota de 0 a 1 que combina saúde, educação e renda; quanto maior, melhor.
  - **GINI:** desigualdade de renda de 0 (todos ganham igual) a 1 (uma só pessoa concentra tudo); quanto menor, melhor.
  - **Emprego:** parcela da força de trabalho que tem ocupação.

---

## 4. Console Persistente de Trilha de Auditoria

Um console de texto somente‑leitura (`grp_audit_console`) está ancorado na base da janela em todas as áreas de trabalho.  Ele mostra os **últimos 25 registros `LocalizedAuditEvent`**, indicando a ação, o agente que a disparou e o carimbo de tempo.  O console **auto‑atualiza** sempre que o idioma muda, garantindo que cada entrada seja exibida no idioma ativo.

---

## 5. Layout Responsivo Multi‑Tela (`ResponsiveLayoutMode`)

- **Ponto de quebra em 960 px**:
  - `< 960 px` → modo *COMPACT*: os `QSplitter` duplos colapsam em pilha vertical, as barras de ação reorganizam‑se de cima para baixo, as tabelas usam `ResizeToContents` com rolagem suave por pixel.
  - `≥ 960 px` → modo *EXPANDED*: os painéis permanecem lado a lado, as colunas se esticam proporcionalmente, e o canvas da malha expande para preencher o espaço.
- **Todas as áreas de trabalho são envolvidas em um `QScrollArea`** com `widgetResizable=True`, evitando overflow em telas pequenas.
- **Escala dinâmica do `CouncilMeshCanvas`** faz os retângulos de nós, conectores direcionais e legendas redimensionarem‑se matematicamente com as dimensões reais do widget, usando `QFontMetrics.elidedText` para evitar colisões de rótulos.

---

## 6. Dicas Rápidas para Usuários Avançados

| Ação | Atalho | Efeito |
|---|---|---|
| Abrir seletor de idioma | `Alt+L` | Troca instantânea de idioma |
| Escalar demanda aleatória de bairro | `Ctrl+E` | Envia uma demanda ao longo da malha |
| Atualizar malha após sortição | `Ctrl+R` | Redesenha o grafo de conselhos |
| Executar auditoria completa | `Ctrl+Shift+A` | Roda verificação de Clean‑Code, documentação e integridade |
| Salvar checkpoint (automático ao fechar) | – | Fechar a janela dispara `closeEvent` → grava `population.json`, `mesh.json`, `audit_snapshot.json` em uma pasta timestamped em `simulation_data/checkpoints/` |

---

*Todos os elementos da UI são totalmente navegáveis por teclado e expõem nomes acessíveis para leitores de tela via a propriedade `accessibleName` do Qt.*