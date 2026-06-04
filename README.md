# cpf-cnpj-validator

Validador de **CPF e CNPJ** em Python, usado como base para um **experimento de
observabilidade de pipeline CI/CD** no GitHub Actions.

> O foco da atividade **não é** o validador em si, e sim **medir e analisar o
> comportamento do pipeline** ao longo de múltiplas execuções, variando o código
> e a configuração de forma controlada.

---

## 🎯 Objetivo do experimento

Instrumentar um pipeline de CI/CD, **coletar métricas reais** de execução
(direto da API do GitHub Actions), **armazenar em formato estruturado** (CSV),
**gerar gráficos** e produzir uma **análise crítica** sobre desempenho,
estabilidade e gargalos do processo.

O pipeline foi executado **12+ vezes**, cada uma com uma variação controlada
(testes passando/falhando, teste lento, alteração de cache, jobs em
paralelo/sequencial, etc.).

---

## 📁 Estrutura do repositório

```
cpf-cnpj-validator/
├── src/
│   ├── __init__.py
│   └── validator.py            # lógica de validação/formatação de CPF e CNPJ
├── tests/
│   ├── __init__.py
│   └── test_validator.py       # suíte de testes (pytest)
├── scripts/
│   ├── snapshot_metrics.py     # roda no CI: gera o snapshot de métricas de cada run
│   └── build_entregaveis.py    # empacota os entregáveis na pasta entregaveis/
├── .github/workflows/
│   └── ci.yml                  # pipeline de 3 jobs (lint → test → metrics)
├── collect_metrics.py          # consulta a API do GitHub e gera o metrics.csv
├── generate_graphs.py          # lê o metrics.csv e gera os 4 gráficos
├── entregaveis/                # 📦 entregáveis finais (CSV + gráficos + relatório)
├── REPORT.md                   # relatório técnico do experimento
├── requirements.txt
├── pyproject.toml              # configuração do pytest
└── .flake8                     # configuração do lint (max-line-length=100)
```

---

## 🔍 O que é testado

O módulo `src/validator.py` expõe:

| Função | Descrição |
|---|---|
| `validate_cpf(cpf)` | Valida CPF pelos 2 dígitos verificadores oficiais; rejeita sequências repetidas |
| `format_cpf(cpf)` | Formata para `123.456.789-09`; `ValueError` se não tiver 11 dígitos |
| `validate_cnpj(cnpj)` | Valida CNPJ pelos 2 dígitos verificadores oficiais; rejeita sequências repetidas |
| `format_cnpj(cnpj)` | Formata para `11.222.333/0001-81`; `ValueError` se não tiver 14 dígitos |
| `identify_and_validate(value)` | Detecta CPF (11 díg.) ou CNPJ (14 díg.), valida e retorna um `dict` |

A suíte em `tests/test_validator.py` cobre CPFs/CNPJs válidos e inválidos,
formatação, sequências repetidas, entradas com letras/tamanho errado e a
detecção automática — organizada em classes por cenário.

---

## ⚙️ O pipeline (`.github/workflows/ci.yml`)

Três jobs encadeados:

```
lint  →  test  →  metrics
```

| Job | O que faz |
|---|---|
| **lint** | Instala dependências (com cache do pip) e roda `flake8 src/ tests/` |
| **test** | Roda `pytest`, gera o `test-results.json` e o sobe como artefato (`if: always()`) |
| **metrics** | Roda `scripts/snapshot_metrics.py`, gera o `metrics_snapshot.json` e o sobe como artefato (roda sempre, mesmo após falha) |

O cache do pip usa a chave `hashFiles('requirements.txt')` — muda o
`requirements.txt`, o cache é invalidado.

---

## 📊 Métricas coletadas

Para cada execução são coletadas (ver `collect_metrics.py`):

- tempo total do workflow (`workflow_duration`);
- tempo de cada job (`job_lint_duration`, `job_test_duration`, `job_metrics_duration`);
- **tempo de cada etapa/step** (arquivo `metrics_steps.csv`: checkout, install, pytest, flake8, ...);
- status (sucesso/falha);
- quantidade de testes (`test_count`), falhas (`test_failures`) e duração da suíte (`test_duration_s`);
- **tempo médio dos testes** (`test_avg_duration_s`);
- commit (`commit_sha`), mensagem (`commit_message`) e data/hora (`timestamp`).

> ⚠️ Os dados **não** são copiados manualmente da interface — o script consulta
> a **API REST do GitHub** (`/repos/{repo}/actions/runs`, `/jobs`, `/artifacts`).

---

## ▶️ Como rodar localmente

### 1. Ambiente e dependências
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
> Use Python 3.11–3.13 (o CI usa 3.12) para que as wheels do `matplotlib`
> instalem sem precisar compilar.

### 2. Lint e testes
```bash
flake8 src/ tests/
pytest
```

---

## 🔁 Como reproduzir o experimento completo

1. **Rodar o pipeline** fazendo pushes com variações (cada push dispara uma run).

2. **Coletar as métricas reais** das execuções:
   ```bash
   export GITHUB_TOKEN=$(gh auth token)
   python collect_metrics.py --repo gabrielsnascimento/cpf-cnpj-validator --max-runs 12
   ```
   → gera o `metrics.csv` (por run) e o `metrics_steps.csv` (por etapa).

3. **Gerar os 4 gráficos**:
   ```bash
   python generate_graphs.py --input metrics.csv
   ```
   → cria os PNGs em `graphs/`.

4. **Empacotar os entregáveis**:
   ```bash
   python scripts/build_entregaveis.py
   ```
   → organiza tudo em `entregaveis/`.

---

## 📦 Pasta `entregaveis/`

Reúne, em um só lugar, os artefatos finais da atividade:

```
entregaveis/
├── metrics.csv                       # base de dados gerada a partir das runs reais
├── REPORT.md                         # relatório técnico
└── graphs/
    ├── 01_tempo_total_pipeline.png   # tempo total do pipeline por execução
    ├── 02_tempo_por_job.png          # tempo por job (barras empilhadas)
    ├── 03_taxa_sucesso_falha.png     # taxa de sucesso × falha (pizza)
    └── 04_testes_vs_duracao.png      # nº de testes × duração (scatter)
```

É montada automaticamente pelo `scripts/build_entregaveis.py`, que copia o
`metrics.csv`, os gráficos e o `REPORT.md` para dentro dela.

---

## 📈 Gráficos gerados

1. **Tempo total do pipeline por execução** — barras por run (verde = sucesso, vermelho = falha).
2. **Tempo por job em cada execução** — barras empilhadas (`lint` / `test` / `metrics`).
3. **Taxa de sucesso × falha** — pizza com o percentual de cada resultado.
4. **Quantidade de testes × duração do pipeline** — scatter colorido por status.

---

## 🧪 Variações realizadas no experimento

| Tipo de variação | Efeito esperado |
|---|---|
| Commit neutro / baseline | referência de tempo |
| Aumento da quantidade de testes | mais testes executados |
| Teste lento (`sleep`) | aumenta o tempo do job `test` |
| Teste falhando | `lint` verde, `test` vermelho, `test_failures > 0` |
| Falha de lint | pipeline para no `lint`, `test` nem roda |
| Alteração no `requirements.txt` | invalida o cache do pip (instalação mais lenta) |
| Jobs em paralelo (`needs` removido) | `lint` e `test` rodam juntos |
| Jobs sequenciais | par de comparação com a execução em paralelo |

> O detalhamento commit-a-commit (SHAs, run IDs e resultados reais) está no
> [`REPORT.md`](REPORT.md).

---

## 📄 Relatório técnico

A análise completa — evidências reais das execuções, IDs dos workflows,
gráficos, respostas às perguntas da atividade, resultados inesperados e
limitações — está em **[`REPORT.md`](REPORT.md)**.
