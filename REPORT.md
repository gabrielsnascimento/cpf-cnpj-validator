# Relatório — Experimento de CI/CD com métricas de pipeline

## 1. Introdução

Este projeto implementa um **validador de CPF e CNPJ** em Python e o utiliza como
base para um experimento de **observabilidade de pipeline de CI/CD** no GitHub
Actions. O código em si é simples e estável de propósito: o foco do experimento
não é o validador, mas sim **medir e analisar o comportamento do pipeline** ao
longo de 12 execuções, variando intencionalmente o conteúdo dos commits.

**Objetivo do experimento:** coletar métricas reais de execução do pipeline
(duração total, duração por job, taxa de sucesso/falha, número de testes e
duração da suíte) e investigar como diferentes variações nos commits impactam
esses números — respondendo a um conjunto de perguntas sobre desempenho,
paralelismo, cache e confiabilidade.

**Tecnologias utilizadas:**

- **Python 3.12** (runtime do pipeline)
- **pytest** + **pytest-json-report** — execução de testes e relatório em JSON
- **flake8** — linting (`max-line-length = 100`)
- **GitHub Actions** — orquestração do pipeline (3 jobs)
- **requests** — coleta de dados via API REST do GitHub
- **pandas** + **matplotlib** — análise e geração dos gráficos

---

## 2. Estrutura do pipeline

O pipeline é definido em [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
<!-- TODO: substituir pelo link absoluto, ex: https://github.com/SEU_USUARIO/cpf-cnpj-validator/blob/main/.github/workflows/ci.yml -->
e é composto por **três jobs executados em sequência**:

```
lint  ──▶  test (needs: lint)  ──▶  metrics (needs: test, if: always())
```

### Job `lint`
- Roda em `ubuntu-latest` com Python 3.12.
- Restaura o **cache do pip** com chave `${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}`.
- Instala as dependências e executa `flake8 src/ tests/`.
- É o **portão de entrada**: se o lint falhar, o `test` nem começa.

### Job `test` (`needs: lint`)
- Mesma base (checkout, Python 3.12, cache do pip, instalação).
- Executa `pytest`, que gera o `test-results.json` (via `pytest-json-report`).
- Faz **upload do `test-results.json`** como artefato `test-results-${{ github.run_id }}`,
  com **`if: always()`** para preservar o relatório mesmo quando os testes falham.

### Job `metrics` (`needs: test`, `if: always()`)
- Roda **mesmo se o `test` falhar** (graças ao `if: always()`).
- Instala **apenas `requests`** (não precisa das deps de teste).
- Baixa o artefato de testes (`continue-on-error: true`, para não quebrar se ele não existir).
- Executa `scripts/snapshot_metrics.py`, que consolida métricas de teste +
  metadados do commit em `metrics_snapshot.json`.
- Faz upload de `metrics_snapshot.json` como artefato `metrics-snapshot-${{ github.run_id }}`.

A coleta consolidada de todas as runs é feita **localmente** depois das 12
execuções, por `collect_metrics.py` (gera `metrics.csv`), e a visualização por
`generate_graphs.py` (gera os 4 PNGs em `graphs/`).

---

## 3. Variações realizadas

As 12 execuções foram planejadas para exercitar diferentes caminhos do pipeline
(cache frio/quente, testes passando/falhando, mudanças só de lint, etc.).

| # | Commit SHA | Mensagem do commit | Tipo de variação aplicada | Resultado esperado | Resultado real |
|---|------------|--------------------|---------------------------|--------------------|----------------|
| 1 | <!-- TODO --> | setup inicial do projeto | Primeira run — cache frio | success (build do cache) | <!-- TODO --> |
| 2 | <!-- TODO --> | adiciona validador de CPF | Código novo + testes passando | success (cache quente) | <!-- TODO --> |
| 3 | <!-- TODO --> | adiciona validador de CNPJ | Código novo + testes passando | success | <!-- TODO --> |
| 4 | <!-- TODO --> | adiciona suíte de testes | Aumenta `test_count` | success, duração de teste maior | <!-- TODO --> |
| 5 | <!-- TODO --> | introduz bug no dígito verificador | Teste quebrado proposital | failure no job `test` | <!-- TODO --> |
| 6 | <!-- TODO --> | corrige o bug do dígito verificador | Volta a passar | success | <!-- TODO --> |
| 7 | <!-- TODO --> | viola o flake8 (linha > 100) | Erro de lint proposital | failure no job `lint` (test não roda) | <!-- TODO --> |
| 8 | <!-- TODO --> | corrige a violação de estilo | Volta a passar | success | <!-- TODO --> |
| 9 | <!-- TODO --> | atualiza requirements.txt | Invalida a chave do cache do pip | success, instalação mais lenta (cache frio) | <!-- TODO --> |
| 10 | <!-- TODO --> | refatora sem mudar comportamento | Mudança neutra, cache quente | success, tempos estáveis | <!-- TODO --> |
| 11 | <!-- TODO --> | adiciona mais casos de teste | Aumenta `test_count` de novo | success, `test_duration_s` maior | <!-- TODO --> |
| 12 | <!-- TODO --> | ajuste de documentação (README) | Mudança trivial, sem efeito em código | success, tempos mínimos | <!-- TODO --> |

> As colunas **Commit SHA** e **Resultado real** devem ser preenchidas após
> coletar os dados das runs reais (`metrics.csv`).

---

## 4. Evidências de execução

Links e/ou prints das runs reais do GitHub Actions, com os IDs dos workflows:

| # | Run ID | Link da run | Print |
|---|--------|-------------|-------|
| 1 | <!-- TODO --> | <!-- TODO: https://github.com/SEU_USUARIO/cpf-cnpj-validator/actions/runs/RUN_ID --> | <!-- TODO --> |
| 2 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 3 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 4 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 5 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 6 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 7 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 8 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 9 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 10 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 11 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |
| 12 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |

<!-- TODO: inserir capturas de tela do painel de Actions mostrando os 3 jobs de cada run -->

---

## 5. Resultados e gráficos

### 5.1 Tempo total do pipeline por execução

![Tempo total do pipeline por execução](graphs/01_tempo_total_pipeline.png)

<!-- TODO: análise — qual run foi a mais lenta/rápida? As falhas (barras vermelhas) foram mais rápidas ou mais lentas? A run 1 (cache frio) e a run 9 (cache invalidado) se destacaram? -->

### 5.2 Tempo por job em cada execução

![Tempo por job em cada execução](graphs/02_tempo_por_job.png)

<!-- TODO: análise — qual job domina o tempo total? A camada de instalação/lint encolheu nas runs com cache quente? O job metrics tem peso relevante? -->

### 5.3 Taxa de sucesso vs falha

![Taxa de sucesso vs falha](graphs/03_taxa_sucesso_falha.png)

<!-- TODO: análise — qual foi a taxa de sucesso final? As falhas correspondem às variações intencionais (runs 5 e 7)? -->

### 5.4 Quantidade de testes × duração do pipeline

![Quantidade de testes × duração do pipeline](graphs/04_testes_vs_duracao.png)

<!-- TODO: análise — há correlação visível entre número de testes e duração total? Os pontos vermelhos (falha) ficam acima ou abaixo da tendência? -->

---

## 6. Análise das perguntas

### 6.1 Qual job consome mais tempo no pipeline?

<!-- TODO: responder com base no gráfico 02 e nos dados de job_*_duration do metrics.csv -->

Hipótese baseada na arquitetura: o job `test` tende a ser o mais custoso, pois
soma instalação de dependências + execução do pytest; `lint` e `metrics`
instalam menos coisas (este último, só `requests`).

### 6.2 Os jobs rodam em paralelo ou em sequência? Como isso afeta o tempo total?

**Resposta (arquitetural):** rodam em **sequência**. A cadeia de dependências
`lint → test (needs: lint) → metrics (needs: test)` força a serialização: cada
job só inicia após o anterior concluir. Consequentemente, **o tempo total é a
soma dos três jobs** (mais o overhead de provisionar um runner novo por job),
e não o tempo do job mais longo. Essa escolha privilegia o "fail-fast" (não
gastar recursos rodando testes se o lint já falhou) em troca de maior latência
total. Se quiséssemos minimizar o tempo de parede, `lint` e `test` poderiam
rodar em paralelo (removendo o `needs`), ao custo de rodar testes mesmo quando
o lint falha.

### 6.3 O cache de dependências reduz o tempo de execução? Em quanto?

**Resposta (arquitetural) + dados:** o cache do pip é chaveado por
`hashFiles('requirements.txt')`. Espera-se que a **primeira run (cache frio)** e
qualquer run que **altere o `requirements.txt`** (invalidando a chave — caso da
variação da run 9) paguem o custo cheio de download/instalação, enquanto as
demais reaproveitam o cache e instalam mais rápido.

<!-- TODO: quantificar a diferença em segundos comparando a run 1 / run 9 (cache frio) com runs de cache quente, usando job_test_duration -->

### 6.4 Como o número de testes impacta a duração do pipeline?

<!-- TODO: responder com base no gráfico 04 (scatter test_count × workflow_duration) -->

Hipótese: com uma suíte tão rápida (dezenas de ms), o `test_count` deve ter
**impacto desprezível** sobre a duração total, que é dominada por provisionamento
de runner, checkout e instalação de dependências — não pela execução dos testes.

### 6.5 Falhas nos testes aumentam ou diminuem o tempo de execução?

<!-- TODO: comparar workflow_duration das runs com falha (5 e 7) vs runs de sucesso -->

Hipótese: uma **falha de lint (run 7)** tende a **reduzir** o tempo total,
porque o job `test` nem chega a rodar. Já uma **falha de teste (run 5)** roda o
pytest inteiro até o fim, então o tempo é semelhante ao de uma run de sucesso.

### 6.6 Qual foi a taxa de sucesso vs falha das 12 execuções?

<!-- TODO: extrair do gráfico 03 / metrics.csv -->

Pela matriz de variações planejada, esperam-se **2 falhas intencionais**
(runs 5 e 7) e 10 sucessos — taxa de sucesso de ~83%.

### 6.7 Há variação de tempo entre runs equivalentes (mesmo código / mudança neutra)?

**Resposta (arquitetural) + dados:** sim, espera-se variação mesmo entre runs
equivalentes, porque os runners do GitHub Actions são **compartilhados** e cada
run roda em uma VM diferente, com contenção de CPU/IO e latência de rede
variável. As runs 10 e 12 (mudanças neutras) servem de referência para medir
esse "ruído" de base.

<!-- TODO: medir a dispersão (min/max/desvio) de workflow_duration entre runs de mudança neutra -->

### 6.8 O job `metrics` (que roda com `if: always()`) tem peso relevante no tempo total?

**Resposta (arquitetural) + dados:** o `metrics` é deliberadamente leve —
instala só `requests` e roda um script de poucos segundos. Como roda **sempre**
(inclusive após falhas), ele **adiciona um custo fixo** ao tempo total em toda
run, mas espera-se que seja pequeno frente a `lint` + `test`.

<!-- TODO: confirmar com job_metrics_duration do metrics.csv -->

---

## 7. Resultados inesperados

> Comparar a hipótese inicial com o que de fato foi observado nos dados.

### 7.1 Resultado inesperado #1

- **Hipótese inicial:** <!-- TODO -->
- **Resultado observado:** <!-- TODO -->
- **Possível explicação:** <!-- TODO -->

### 7.2 Resultado inesperado #2

- **Hipótese inicial:** <!-- TODO -->
- **Resultado observado:** <!-- TODO -->
- **Possível explicação:** <!-- TODO -->

---

## 8. Limitações do experimento

1. **Ambiente compartilhado do GitHub Actions** — os runners hospedados são VMs
   compartilhadas com recursos não dedicados; a contenção de CPU/IO com outras
   cargas introduz variabilidade que não controlamos.
2. **Variação de tempo entre runs** — mesmo com código idêntico, a duração de
   cada run oscila (provisionamento de VM, latência de rede, estado do cache),
   o que dificulta atribuir diferenças pequenas a uma variação específica.
3. **Tamanho pequeno da amostra (12 runs)** — 12 execuções são insuficientes
   para conclusões estatisticamente robustas; outliers têm peso desproporcional
   e não dá para separar bem sinal de ruído.
4. **Dependência de rede para instalar pacotes** — o tempo de instalação depende
   da disponibilidade e velocidade do PyPI e do cache; uma lentidão pontual na
   rede contamina a medição de duração dos jobs.
5. **Suíte de testes muito rápida** — como os testes rodam em milissegundos, o
   tempo de teste fica ofuscado pelo overhead de infraestrutura, limitando o que
   se pode concluir sobre o impacto do `test_count`.

---

## 9. Como reproduzir

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/cpf-cnpj-validator.git
   cd cpf-cnpj-validator
   ```
   <!-- TODO: ajustar a URL para o repositório real -->

2. **Criar o ambiente virtual e instalar as dependências:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   > Use Python 3.11–3.13 para que as wheels de `matplotlib` instalem sem
   > compilação. O CI usa Python 3.12.

3. **Rodar os testes localmente:**
   ```bash
   pytest
   ```
   Isso gera o `test-results.json` na raiz.

4. **Executar o pipeline no GitHub Actions:**
   Faça push dos commits (as 12 variações). Cada push dispara o workflow
   `lint → test → metrics`, que produz os artefatos `metrics-snapshot-<run_id>`.

5. **Coletar as métricas das runs (após as 12 execuções):**
   ```bash
   export GITHUB_TOKEN=ghp_seu_token        # token com acesso ao repo
   python collect_metrics.py --repo SEU_USUARIO/cpf-cnpj-validator
   ```
   Gera o `metrics.csv` com uma linha por execução.

6. **Gerar os gráficos:**
   ```bash
   python generate_graphs.py --input metrics.csv
   ```
   Cria os 4 PNGs em `graphs/`:
   `01_tempo_total_pipeline.png`, `02_tempo_por_job.png`,
   `03_taxa_sucesso_falha.png`, `04_testes_vs_duracao.png`.

7. **Preencher este relatório:** substituir os marcadores
   `<!-- TODO -->` pelos dados reais (SHAs, run IDs, resultados, análises).
