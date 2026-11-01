# 03. Manual de Operação do Simulador

## 1. Provisionamento do Ambiente e Inicialização do Simulador

O simulador **CIBERSOC** executa sobre **Python 3.12, 3.13 e 3.14** em macOS, Linux e Windows. Todas as dependências estão fixadas deterministicamente em [`uv.lock`](../../uv.lock) via **uv**.

### 1.1 Clonagem e Sincronização do Ambiente Virtual Isolado
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync --all-extras --all-groups
```

### 1.2 Executando o Cliente Gráfico Desktop (PySide6)
```bash
uv run python cibersoc_ui.py
# ou pelo script de console instalado:
uv run cibersoc-ui
```
Snapshots determinísticos do cadastro populacional, da malha de conselhos e da auditoria de integridade podem ser gravados a qualquer momento pelo botão **Salvar Snapshot (`btn_save_checkpoint`)** na Aba 2 ou programaticamente em `simulation_data/` e `simulation_data/checkpoints/`.

### 1.3 Executando o Simulador CLI Trilíngue Determinístico
```bash
uv run python run_simulation.py --locale en-GB
uv run python run_simulation.py --locale pt
uv run python run_simulation.py --locale es
```
O CLI executa uma orquestração ponta a ponta determinística e imprime quatro seções traduzidas:
- **`[1]` Sorteio, Conselhos Federados e Habilitação Cívica:** Provas criptográficas do ciclo ativo, quarentenas e resumo de habilitação cívica.
- **`[2]` Economia Cooperativa e Paridade de Mandato:** Excedente líquido, rateio exato $1/N$ por trabalhador, retenção corporativa `$0.00` e proteção indexada pelo IPCA.
- **`[3]` Macro-Alocação Cibernética e Feedback do Plano:** Apuração plebiscitária, cotas de trabalho incorporado, produção bruta de Leontief, Harmonia de curto prazo e feedback de escoamento/teto de carbono.
- **`[4]` Integridade Autônoma e Trilha de Auditoria:** Conformidade AST/lexer de Clean Code, simetria trilíngue e eventos auditados.

---

## 2. Playbooks Operacionais

### Playbook A — Sorteio Multiciclo, Quarentena e Habilitação Cívica
1. Abra a **Aba 2 (`Sorteio e Quarentena`)**. Observe o Ciclo `#01`: `76` conselheiros ativos nos 5 conselhos (`20` Federal + `16` Estadual + `20` Municipal + `10` Boqueirão + `10` Matriz), `Em Quarentena = 0`, `Reincidência Consecutiva = 0`.
2. Clique em **Executar Próximo Ciclo de Sorteio (`btn_next_cycle`)**:
   - Os conselheiros cessantes entram em quarentena criptográfica; `76` novos conselheiros são sorteados entre os `244` cidadãos elegíveis via `Commit-Reveal SHA-256` + cotas de Hamilton, mantendo `Reincidência Consecutiva = 0` e todas as provas `VERIFICADA (SHA-256)`.
3. Clique em **Executar Rodada de Habilitação Cívica (`btn_civic_round`)** para registrar notas nas 4 disciplinas essenciais e verificar a isenção estatutária automática aos $\ge 60$ anos.

### Playbook B — Macro-Plebiscito, Cotas de Trabalho e Teto de Carbono
1. Abra a **Aba 3 (`Macro-Alocação Cibernética`)**, defina `+5% Educação` em `750` e `+5% Saúde` em `250`, e clique em **Apurar Plebiscito e Difundir Diretriz (`btn_run_plebiscite`)**.
2. Verifique o deslocamento contínuo de Cockshott (`-2,50%`), a conservação exata das cotas de trabalho incorporado na tabela Insumo-Produto e o incremento `↓Dir` na Aba 1.
3. Ajuste a **Razão Observada de Escoamento (`spn_clearing_ratio`)** e o **Orçamento de Carbono (`spn_carbon_budget`)**, clicando em **Iterar Plano (`btn_iterate_plan`)** para inspecionar o ajuste iterativo e a trava ecológica.

### Playbook C — Excedente Cooperativo $1/N$ e Ciclo de Mandato
1. Abra a **Aba 4 (`Empresa Sem CEO e Retorno Civil`)**, ajuste a **Receita Operacional (`spn_revenue`)** para `220000` e clique em **Executar Partilha Igualitária 1/N (`btn_distribute_profit`)**, confirmando retenção corporativa `$0.00` e transporte exato de frações de centavo.
2. Percorra os quatro botões do **Ciclo de Mandato** para `CID-0001`: suspensão para serviço em conselho, reajuste de `+0,50%` pelo IPCA, reintegração protegida por $\ge 180$ dias e bloqueio de demissão prematura (`EmploymentStabilityLockError`).

### Playbook D — Comparação Contrafactual Nacional SEEM (`A / B / C`)
1. Abra a **Aba 6 (`Simulação Nacional — SEEM`)**, ajuste **Anos por Passo (`spn_years_step`)** para `15` e clique em **Avançar**.
2. Alterne o **Regime Institucional (`cmb_regime`)** entre **(A) CIBERSOC Demárquico**, **(B) Oligarquia Eleitoral** e **(C) Centralismo Burocrático**. Como as três trajetórias compartilham **Números Aleatórios Comuns (CRN)**, as diferenças em IDH, Gini e emprego isolam estritamente o efeito do desenho institucional.

---

## 3. API Programática em Python

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

plant = SocialistEnterprise("EMP-01", "Óptica de Precisão Curitiba", "IND-OPT")
plant.register_worker(WorkerMember("W-01", "Alice", "Engenheira de Óptica", Decimal("4800.00"), 30))
plant.register_worker(WorkerMember("W-02", "Bruno", "Técnico de Montagem", Decimal("4200.00"), 30))
receipt = plant.distribute_period_profit(
    period_label="2026-M01",
    period_total_days=30,
    gross_revenue=Decimal("35000.00"),
    audited_material_costs=Decimal("10000.00"),
    physical_depreciation_reserve=Decimal("2000.00"),
    macro_social_contribution=Decimal("3000.00"),
    capital_endowment_equalisation_charge=Decimal("1000.00"),
)
print("Pagamentos por trabalhador:", receipt.payouts_by_worker)
```

---

## 4. Verificação Automatizada e QA com 100% de Cobertura

```bash
uv run pyright src/cibersoc
QT_QPA_PLATFORM=offscreen uv run pytest -v \
    --cov=src/cibersoc --cov-branch \
    --cov-report=term-missing --cov-fail-under=100
```
A suíte impõe `0` erros estáticos de tipos, `100.00%` de cobertura de instruções e ramos, `0` mocks ou monkeypatches, `0` comentários `#` ou docstrings em todos os arquivos `.py` e simetria trilíngue completa.

---

## 5. Benchmark Empírico Comparativo de 30 Anos (3 Regimes × 3 Cenários)

Esta seção documenta o experimento longitudinal canônico de **30 ciclos anuais** (`seed=42`, `StochasticEventMatrix(seed=42)`, `150.700.000` habitantes em 10 unidades federativas, `150` conselheiros únicos sorteados com `0` reincidência consecutiva) sob **Números Aleatórios Comuns (CRN)** nos três regimes institucionais — **(A) Demarquia CIBERSOC (`CIBERSOC_DEMARCHY`)**, **(B) Oligarquia Eleitoral (`ELECTORAL_OLIGARCHY`)** e **(C) Centralismo Burocrático (`BUREAUCRATIC_CENTRALISM`)** — e nos três cenários macroestruturais.

### 5.1 Trajetória Longitudinal Sem Macro-Diretriz (`Macro = False`, Anos 0 → 10 → 20 → 30)

| Cenário | Regime | IDH (A0 → A10 → A20 → A30) | Gini (A0 → A10 → A20 → A30) | Emprego % (A0 → A10 → A20 → A30) | Gap Regional IDH (A30) | $\sigma_{\text{IDH}}$ (A30) | Fluxo Corredores (A30) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | **A. Demarquia** | `0.7379 → 0.8237 → 0.8786 → 0.9110` | `0.4045 → 0.3318 → 0.2880 → 0.2630` | `78.75% → 85.05% → 87.60% → 91.23%` | `0.0538` | `0.0135` | `0.9814` |
| **`BASELINE`** | **B. Oligarquia Eleitoral** | `0.7379 → 0.7513 → 0.7656 → 0.7738` | `0.4045 → 0.4649 → 0.5013 → 0.5255` | `78.75% → 78.19% → 76.54% → 77.70%` | `0.1438` | `0.0431` | `0.6057` |
| **`BASELINE`** | **C. Centralismo Burocrático** | `0.7379 → 0.7783 → 0.8028 → 0.8104` | `0.4045 → 0.3884 → 0.3761 → 0.3688` | `78.75% → 82.12% → 80.26% → 77.74%` | `0.0796` | `0.0212` | `0.7000` |
| **`ECOLOGICAL_STRESS`** | **A. Demarquia** | `0.7136 → 0.7971 → 0.8521 → 0.8833` | `0.4045 → 0.3340 → 0.2913 → 0.2678` | `76.93% → 82.69% → 85.08% → 88.23%` | `0.0631` | `0.0177` | `0.9044` |
| **`ECOLOGICAL_STRESS`** | **B. Oligarquia Eleitoral** | `0.7136 → 0.7235 → 0.7363 → 0.7412` | `0.4045 → 0.4673 → 0.5051 → 0.5312` | `76.93% → 75.36% → 73.22% → 73.59%` | `0.1684` | `0.0545` | `0.5285` |
| **`ECOLOGICAL_STRESS`** | **C. Centralismo Burocrático** | `0.7136 → 0.7508 → 0.7744 → 0.7796` | `0.4045 → 0.3907 → 0.3795 → 0.3739` | `76.93% → 79.54% → 77.37% → 74.21%` | `0.0969` | `0.0289` | `0.6260` |
| **`POST_CRISIS_EQUALISATION`** | **A. Demarquia** | `0.7476 → 0.8432 → 0.8943 → 0.9201` | `0.5729 → 0.4029 → 0.3174 → 0.2754` | `64.02% → 78.70% → 84.88% → 89.76%` | `0.0386` | `0.0105` | `0.9679` |
| **`POST_CRISIS_EQUALISATION`** | **B. Oligarquia Eleitoral** | `0.7476 → 0.7561 → 0.7661 → 0.7705` | `0.5729 → 0.5719 → 0.5688 → 0.5678` | `64.02% → 69.28% → 71.06% → 73.93%` | `0.0884` | `0.0275` | `0.5551` |
| **`POST_CRISIS_EQUALISATION`** | **C. Centralismo Burocrático** | `0.7476 → 0.7890 → 0.8089 → 0.8103` | `0.5729 → 0.4734 → 0.4189 → 0.3908` | `64.02% → 74.82% → 76.73% → 76.08%` | `0.0516` | `0.0146` | `0.6750` |

### 5.2 Sensibilidade à Diretriz Plebiscitária Ativa (`Macro = True`, Padrão da Interface, Ano 30)

Quando o plebiscito cibernético anual está acoplado (`PLEB-FED-01: +5% Health`, `bonus = 0.015`, atenuado por fronteira côncava `max(0, 0.965 - IDH)`), a transmissão institucional (`macro_directive_multiplier`: `1.00` em A, `0.55` em C, `0.22` em B) amplia o diferencial líquido:

| Cenário (Ano 30, `Macro = True`) | IDH (A. Demarquia) | IDH (B. Eleitoral) | IDH (C. Centralismo) | Ganho Líquido A vs B ($\Delta\text{IDH}$) | Ganho Líquido A vs C ($\Delta\text{IDH}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`BASELINE`** | `0.9218` | `0.7798` | `0.8215` | **`+0.1420`** | **`+0.1003`** |
| **`ECOLOGICAL_STRESS`** | `0.8972` | `0.7481` | `0.7927` | **`+0.1491`** | **`+0.1045`** |
| **`POST_CRISIS_EQUALISATION`** | `0.9275` | `0.7755` | `0.8194` | **`+0.1520`** | **`+0.1081`** |

### 5.3 Diagnóstico Estrutural das Diferenças Observadas

1. **Divergência Distributiva e Convergência Regional ($\sigma$-convergência):** Na Demarquia (A), o rateio cooperativo $1/N$ sem captura de renda (`rent_capture_drift = 0.0`) e a equalização inter-regional (`+0.032`) reduzem a amplitude regional de IDH no `BASELINE` de `0.3260` (Ano 0) para `0.0538` (Ano 30, $\sigma = 0.0135$), elevando o fluxo produtivo médio dos corredores para `0.9814`. Na Oligarquia Eleitoral (B), a deriva de captura (`+0.0022/ano`) e a polarização centro-periferia (`-0.005`) elevam o Gini para `0.5255` e mantêm um fosso regional `2,67×` maior (`0.1438`: `BR-SP = 0.788` contra `BR-AM = 0.702`).
2. **Clivagem Norte–Sul sob Estresse Ecológico (`ECOLOGICAL_STRESS`):** Diante de choques climáticos recorrentes sobre latitudes tropicais ($\text{lat} > -16^\circ$), a fiscalização demárquica mitiga `30%` do dano líquido, preservando o IDH médio do Norte/Nordeste em `0.8637` contra `0.8899` no Centro-Sul (diferença Norte–Sul de apenas `0.0262`). Sob Oligarquia Eleitoral (mitigação de `6%`), o Norte/Nordeste estagna em `0.6840` (`BR-AM = 0.617`, `BR-BA = 0.646`) contra `0.7571` no Centro-Sul (fosso Norte–Sul `2,79×` mais severo, `0.0731`).
3. **Ossificação Burocrática de Longo Prazo no Regime C:** O Centralismo Burocrático exibe rápida mobilização inicial nos primeiros 10 anos (`Emprego` sobe de `78.75%` para `82.12%` no `BASELINE` e de `64.02%` para `74.82%` no `POST_CRISIS`), mas sofre ossificação administrativa cumulativa após o Ano 8 (`ossification_rate = 0.0018`), fazendo o emprego recuar de `82.12%` (Ano 10) para `77.74%` (Ano 30) no `BASELINE` e travando o Gini acima do piso estratificado (`0.3688–0.3908`).
4. **Destravamento Pós-Crise (`POST_CRISIS_EQUALISATION`):** Partindo de desigualdade aguda (`Gini = 0.5729`) e desemprego elevado (`Emprego = 64.02%`), a Demarquia comprime o Gini em **`-0.2975` pontos** (`0.2754`) e cria **`+25.74 pp`** de emprego (`89.76%`), enquanto a Oligarquia Eleitoral permanece presa em histerese desigual (`Gini = 0.5678`, variação residual de `-0.0051` em três décadas).
