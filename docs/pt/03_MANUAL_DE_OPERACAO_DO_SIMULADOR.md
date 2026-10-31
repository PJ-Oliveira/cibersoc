# 03. Manual de Operação do Simulador

## 1. Provisionamento do Ambiente e Execução do Simulador

O simulador **CIBERSOC** roda em **Python 3.12+** (os testes CI utilizam CPython 3.14).  Todas as dependências são declaradas em `uv.lock` e instaladas com o gerenciador ultra‑rápido **uv**, garantindo um ambiente determinístico e reproduzível em macOS, Linux e Windows.

### 1.1 Clonagem e Criação do Ambiente Virtual Isolado
```bash
git clone https://github.com/PJ-Oliveira/cibersoc.git
cd cibersoc
uv sync                # cria .venv e instala as versões exatas de uv.lock
```
> **Por que `uv`?**  Diferente de `pip`/`requirements.txt`, `uv` resolve o grafo de dependências uma única vez, grava um lock file e nunca baixa novamente os mesmos pacotes, eliminando surpresas do tipo “funciona na minha máquina”.

### 1.2 Executando a UI Gráfica (PySide6)
```bash
.venv/bin/python cibersoc_ui.py
# ou, após o script de entrada ser instalado:
.venv/bin/cibersoc-ui
```
Ao iniciar, a UI exibe um **Diálogo de Seleção de Checkpoint**:
- **Novo** – inicia uma simulação limpa.
- Qualquer checkpoint salvo previamente (pasta com timestamp em `simulation_data/checkpoints/`).
Selecionar um checkpoint carrega `population.json`, `mesh.json` e o snapshot de auditoria, permitindo retomar exatamente de onde parou.

### 1.3 Executando o Simulador CLI Trilingue
```bash
.venv/bin/python run_simulation.py --locale en-GB   # English (UK)
.venv/bin/python run_simulation.py --locale pt      # Português
.venv/bin/python run_simulation.py --locale es      # Español
```
O CLI realiza uma execução end‑to‑end determinística e imprime um relatório localizado contendo:
- Estatísticas da população
- Composição dos conselhos por nível
- Resultado do último plebiscito macroeconômico
- Distribuição do excedente empresarial

## 2. Playbooks para Tarefas Comuns

### Playbook A – Sortição Multiciclo & Verificação de Quarentena
1. Abra a **Aba 2 – Sortição & Quarentena**.
2. Observe o banner do ciclo (`CICLO DEMÁRQUICO #01`): `76` cidadãos servem nos 5 Conselhos (`20` Federal + `16` Estadual + `20` Municipal + `10` Boqueirão + `10` Matriz), `Em Quarentena = 0`, `Reincidência Consecutiva = 0`.
3. Pressione **Executar Próximo Ciclo de Sortição**.
   - `SimulationOrchestrator.execute_next_sortition_cycle` finaliza os mandatos atuais, move os `76` conselheiros que saem para a quarentena criptográfica (fora da urna) e sorteia `76` novos conselheiros entre os `244` cidadãos elegíveis restantes via protocolo **Commit‑Reveal SHA‑256** com cotas de Hamilton.
4. Verifique que o selo de resumo mostra `Ex‑Conselheiros Retirados da Urna (Quarentena) = 76` e `Reincidência Consecutiva = 0`, e que a **Tabela de Provas** apresenta status verde `VERIFICADA (SHA‑256)` para cada conselho.
5. Pressione novamente **Executar Próximo Ciclo de Sortição** (Ciclo `#03`): os conselheiros do Ciclo 1 recuperam a elegibilidade após 1 ciclo de resfriamento, enquanto os do Ciclo 2 passam à quarentena, mantendo invariante a taxa zero de reeleição consecutiva.

### Playbook B – Parametrização de Plebiscito Macro
1. Mude para a **Aba 3 – Alocação Macro‑Cibernética**.
2. Defina os dois spin‑boxes de cédulas:
   - `+5 % Educação` → `750`
   - `+5 % Saúde` → `250`
3. Clique em **Apurar Plebiscito & Broadcast Diretriz Compulsória**.
   - A diretiva vencedora passa para `EDU+5` (1000 cédulas auditadas).
   - O cálculo de mudança contínua de Cockshott atualiza o índice de Harmonia de curto prazo para `‑2,50 %` (tendência à Educação).
   - A **Tabela de Input‑Output** atualiza a parcela votada, demanda final `$y^*`, produção bruta `$x`, horas‑trabalho embutidas `$H` e o índice de Harmonia por setor.
4. Use os botões **Testar Nome de Candidato na Cédula** e **Simular Desvio Orçamentário do Conselho** para confirmar que conteúdo ilegal de cédula e alterações de orçamento não autorizadas são bloqueados imediatamente.

### Playbook C – Distribuição de Excedente Empresarial & Equalização Ricardiana
1. Abra a **Aba 4 – Empresa Sem CEO & Retorno Civil**.
2. Ajuste a **Receita Operacional do Período** (`spn_revenue`) dentro do intervalo `120 000 – 500 000` (ex.: `220 000`).
3. Pressione **Executar Distribuição Igual 1/N**.
   - `SocialistEnterprise.distribute_period_profit` deduz:
     * Custos materiais auditados
     * Reserva de depreciação física
     * Contribuição macro‑social
     * Charge de equalização de dotação de capital (componente **Ricardiano**)
   - O excedente líquido é dividido **exatamente** entre todos os trabalhadores ativos usando aritmética racional de dias‑inteiros; qualquer resto indivisível (< 1 ¢ por trabalhador) é transportado para o próximo período.
   - O lucro retido corporativo permanece `0.00` por construção.
4. Observe a **Tabela de Trabalhadores** atualizar: cada pagamento é exibido com duas casas decimais e a soma de todos os pagamentos equivale ao excedente líquido.

### Playbook D – Ciclo de Mandato do Conselheiro, Indexação de Inflação & Proteção ao Emprego
1. Na **Aba 4**, localize um trabalhador (ex.: `CID‑0001`).
2. Clique em **Suspender Trabalhador Ordenado para Mandato de Conselho**.
   - O status do trabalhador muda para `Em Mandato de Conselho`; o excedente empresarial é recalculado para a força‑de‑trabalho reduzida.
3. Clique repetidamente em **Aplicar Inflação de Preço (+0,50 %)**.
   - Cada clique compõe a série de índice de preço e atualiza o subsídio proporcionalmente.
4. Clique em **Concluir Mandato & Reintegrar (≥ 180 dias)**.
   - O trabalhador retorna a `Reintegrado com Estabilidade Protegida`, o subsídio é ajustado permanentemente à inflação acumulada e um bloqueio `stability_locked_until` é definido 180 dias à frente.
5. Clique em **Testar Tentativa de Demissão Pós‑Retorno (Bloquear)**.
   - O sistema lança `EmploymentStabilityLockError`, registra o bloqueio e impede a demissão prematura.

## 3. API Python Programática

Engenheiros podem conduzir o simulador via scripts Python puros:
```python
from decimal import Decimal
from cibersoc.cybernetics import (
    CompressedSparseRowMatrix,
    solve_leontief_gross_output_gauss_seidel,
)
from cibersoc.enterprise import SocialistEnterprise, WorkerMember

# Construir um pequeno sistema Leontief
A = CompressedSparseRowMatrix.from_dense([[0.10, 0.20], [0.05, 0.15]])
final_demand = [120.0, 80.0]
output = solve_leontief_gross_output_gauss_seidel(A, final_demand)

# Criar uma empresa socialista e distribuir lucro
plant = SocialistEnterprise('EMP‑01', 'Curitiba Precision Optics', 'IND‑OPT')
plant.register_worker(WorkerMember('W‑01', 'Alice', 'Engenheira de Óptica', Decimal('4800.00'), 30))
plant.register_worker(WorkerMember('W‑02', 'Bruno', 'Técnico de Montagem', Decimal('4200.00'), 30))
receipt = plant.distribute_period_profit(
    period_label='2026‑M01',
    period_total_days=30,
    gross_revenue=Decimal('35000.00'),
    audited_material_costs=Decimal('10000.00'),
    physical_depreciation_reserve=Decimal('2000.00'),
    macro_social_contribution=Decimal('3000.00'),
    capital_endowment_equalisation_charge=Decimal('1000.00'),
)
print('Pagamentos por trabalhador:', receipt.payouts)
```
A API replica exatamente o que a UI faz, mas permite execuções em lote, experimentos e integração com fontes de dados externas.

## 4. Verificação Automatizada & QA com Cobertura 100 %

O repositório inclui uma suíte de testes `pytest` + `pytest‑qt` + `coverage` que garante:
- **Zero documentação faltante** para cada idioma.
- **Conformidade Clean‑Code** (sem `TODO`s, pontuação Pylint ≥ 9.5, zero avisos de código morto).
- **Cobertura completa de instruções e ramos** (`--cov-fail-under=100`).
```bash
QT_QPA_PLATFORM=offscreen .venv/bin/pytest -v \
    --cov=cibersoc --cov-branch \
    --cov-report=term-missing --cov-fail-under=100
```
A suíte também executa a **auditoria de integridade** (`btn_run_audit`) programaticamente para garantir que cada arquivo fonte não contenha comentários ou docstrings, conforme a política Clean‑Code do projeto.
