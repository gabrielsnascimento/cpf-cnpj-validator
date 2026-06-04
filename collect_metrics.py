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
    "timestamp",
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


def collect_job_durations(session, repo, run_id):
    """Retorna {nome_do_job: duracao_s} para os jobs de uma run."""
    url = f"{API}/repos/{repo}/actions/runs/{run_id}/jobs"
    data = get_json(session, url)
    durations = {}
    for job in data.get("jobs", []):
        durations[job["name"]] = duration_seconds(
            job.get("started_at"), job.get("completed_at")
        )
    return durations


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
    """Monta a linha do CSV para uma run do workflow."""
    run_id = run["id"]

    jobs = collect_job_durations(session, repo, run_id)
    snapshot = fetch_snapshot(session, repo, run_id)

    head_commit = run.get("head_commit") or {}
    commit_message = (head_commit.get("message") or "").splitlines()
    commit_message = commit_message[0] if commit_message else ""

    return {
        "run_id": run_id,
        "commit_sha": (run.get("head_sha") or "")[:7],
        "commit_message": commit_message,
        "status": run.get("conclusion") or run.get("status") or "",
        "workflow_duration": duration_seconds(
            run.get("run_started_at"), run.get("updated_at")
        ),
        "job_lint_duration": jobs.get("lint", 0),
        "job_test_duration": jobs.get("test", 0),
        "job_metrics_duration": jobs.get("metrics", 0),
        "test_count": snapshot.get("test_count", 0),
        "test_failures": snapshot.get("test_failures", 0),
        "test_passed": snapshot.get("test_passed", 0),
        "test_duration_s": snapshot.get("test_duration_s", 0),
        "timestamp": snapshot.get("timestamp", ""),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Coleta métricas das runs do GitHub Actions em um CSV."
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--output", default="metrics.csv", help="arquivo CSV de saída")
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

    rows = []
    for run in runs:
        rows.append(build_row(session, args.repo, run))
        time.sleep(0.5)  # respeita o rate limit da API

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} run(s) gravada(s) em {args.output}")


if __name__ == "__main__":
    main()
