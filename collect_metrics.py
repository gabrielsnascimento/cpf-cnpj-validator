"""Coleta métricas das execuções do workflow no GitHub Actions e gera um CSV.

Roda localmente após as execuções do pipeline. Para cada run de `push`,
busca a duração de cada job, baixa o artefato `metrics-snapshot-*` (em
memória, sem salvar o zip em disco) e consolida tudo em um CSV.

Dependências: requests (já instalado) + stdlib.
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime

API = "https://api.github.com"

COLUMNS = [
    "run_id",
    "commit_sha",
    "commit_message",
    "status",
    "workflow_duration",
    "job_lint_duration",
    "job_test_duration",
    "job_metrics_duration",
    "test_count",
    "test_failures",
    "test_passed",
    "test_duration_s",
    "test_avg_duration_s",
    "timestamp",
]

# CSV de steps (formato "long": uma linha por etapa de cada job)
STEP_COLUMNS = [
    "run_id",
    "commit_sha",
    "job_name",
    "step_name",
    "step_duration_s",
    "conclusion",
]


def parse_ts(value):
    """Converte um timestamp ISO 8601 do GitHub em datetime (aware)."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(start, end):
    """Diferença em segundos entre dois timestamps ISO; 0 se faltar algum."""
    start_dt = parse_ts(start)
    end_dt = parse_ts(end)
    if not start_dt or not end_dt:
        return 0
    return (end_dt - start_dt).total_seconds()


def get_json(session, url, params=None):
    """GET na API do GitHub retornando o JSON; lança em caso de erro HTTP."""
    response = session.get(url, params=params)
    response.raise_for_status()
    return response.json()


def fetch_jobs(session, repo, run_id):
    """Retorna a lista bruta de jobs de uma run (uma chamada à API)."""
    url = f"{API}/repos/{repo}/actions/runs/{run_id}/jobs"
    return get_json(session, url).get("jobs", [])


def job_durations(jobs):
    """A partir da lista de jobs, retorna {nome_do_job: duracao_s}."""
    return {
        job["name"]: duration_seconds(
            job.get("started_at"), job.get("completed_at")
        )
        for job in jobs
    }


def step_rows(jobs, run_id, commit_sha):
    """Linhas (formato long) com a duração de cada step de cada job.

    Atende ao requisito de "tempo de cada etapa relevante" — a API do GitHub
    expõe os steps internos (checkout, install, pytest, etc.) com seus próprios
    timestamps.
    """
    rows = []
    for job in jobs:
        for step in job.get("steps", []) or []:
            rows.append({
                "run_id": run_id,
                "commit_sha": commit_sha,
                "job_name": job.get("name", ""),
                "step_name": step.get("name", ""),
                "step_duration_s": duration_seconds(
                    step.get("started_at"), step.get("completed_at")
                ),
                "conclusion": step.get("conclusion") or "",
            })
    return rows


def fetch_snapshot(session, repo, run_id):
    """Baixa e extrai o metrics_snapshot.json do artefato metrics-snapshot-*.

    Faz tudo em memória com BytesIO + zipfile. Retorna {} se não houver
    artefato ou se algo falhar.
    """
    url = f"{API}/repos/{repo}/actions/runs/{run_id}/artifacts"
    data = get_json(session, url)

    artifact = None
    for item in data.get("artifacts", []):
        if item.get("name", "").startswith("metrics-snapshot-"):
            artifact = item
            break

    if artifact is None:
        return {}

    try:
        download = session.get(artifact["archive_download_url"])
        download.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(download.content)) as zf:
            with zf.open("metrics_snapshot.json") as snap:
                return json.load(snap)
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, OSError):
        return {}


def build_row(session, repo, run):
    """Monta a linha do CSV de uma run e as linhas de steps dela.

    Retorna uma tupla (row, steps) — `row` é o dict da linha principal e
    `steps` é a lista de linhas (long) com a duração de cada step.
    """
    run_id = run["id"]
    commit_sha = (run.get("head_sha") or "")[:7]

    jobs = fetch_jobs(session, repo, run_id)
    durations = job_durations(jobs)
    snapshot = fetch_snapshot(session, repo, run_id)

    head_commit = run.get("head_commit") or {}
    commit_message = (head_commit.get("message") or "").splitlines()
    commit_message = commit_message[0] if commit_message else ""

    test_count = snapshot.get("test_count", 0)
    test_duration = snapshot.get("test_duration_s", 0)
    test_avg = round(test_duration / test_count, 6) if test_count else 0

    row = {
        "run_id": run_id,
        "commit_sha": commit_sha,
        "commit_message": commit_message,
        "status": run.get("conclusion") or run.get("status") or "",
        "workflow_duration": duration_seconds(
            run.get("run_started_at"), run.get("updated_at")
        ),
        "job_lint_duration": durations.get("lint", 0),
        "job_test_duration": durations.get("test", 0),
        "job_metrics_duration": durations.get("metrics", 0),
        "test_count": test_count,
        "test_failures": snapshot.get("test_failures", 0),
        "test_passed": snapshot.get("test_passed", 0),
        "test_duration_s": test_duration,
        "test_avg_duration_s": test_avg,
        "timestamp": snapshot.get("timestamp", ""),
    }
    return row, step_rows(jobs, run_id, commit_sha)


def main():
    parser = argparse.ArgumentParser(
        description="Coleta métricas das runs do GitHub Actions em um CSV."
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--output", default="metrics.csv", help="arquivo CSV de saída")
    parser.add_argument(
        "--steps-output",
        default="metrics_steps.csv",
        help="CSV com a duração de cada step (etapa) de cada job",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="limita às N execuções mais antigas (as do experimento controlado); "
             "0 = todas",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Erro: variável de ambiente GITHUB_TOKEN não definida.", file=sys.stderr)
        sys.exit(1)

    import requests

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    runs_url = f"{API}/repos/{args.repo}/actions/runs"
    data = get_json(session, runs_url, params={"per_page": 30, "event": "push"})
    runs = data.get("workflow_runs", [])

    # A API retorna da mais recente para a mais antiga. Limitar a N mantém as
    # N execuções MAIS ANTIGAS (as do experimento controlado), descartando
    # commits de housekeeping feitos depois.
    if args.max_runs and len(runs) > args.max_runs:
        runs = runs[-args.max_runs:]

    rows = []
    steps = []
    for run in runs:
        row, run_steps = build_row(session, args.repo, run)
        rows.append(row)
        steps.extend(run_steps)
        time.sleep(0.5)  # respeita o rate limit da API

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    with open(args.steps_output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STEP_COLUMNS)
        writer.writeheader()
        writer.writerows(steps)

    print(
        f"{len(rows)} run(s) em {args.output} | "
        f"{len(steps)} step(s) em {args.steps_output}"
    )


if __name__ == "__main__":
    main()
