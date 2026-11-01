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
