"""Coleta métricas do test-results.json e grava um snapshot para o pipeline."""

import json
import os
import time

RESULTS_FILE = "test-results.json"
SNAPSHOT_FILE = "metrics_snapshot.json"


def read_test_metrics(path=RESULTS_FILE):
    """Extrai contagens e duração do relatório do pytest-json-report.

    Se o arquivo não existir (ou estiver malformado), retorna tudo zerado
    sem lançar erro.
    """
    metrics = {
        "test_count": 0,
        "test_failures": 0,
        "test_passed": 0,
        "test_duration_s": 0,
    }

    if not os.path.exists(path):
        return metrics

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return metrics

    summary = data.get("summary", {})
    metrics["test_count"] = summary.get("total", 0)
    metrics["test_failures"] = summary.get("failed", 0)
    metrics["test_passed"] = summary.get("passed", 0)
    metrics["test_duration_s"] = data.get("duration", 0)

    return metrics


def build_snapshot():
    """Monta o dict completo do snapshot a partir das métricas e do ambiente."""
    snapshot = read_test_metrics()

    commit_sha = os.environ.get("COMMIT_SHA", "")
    commit_msg = os.environ.get("COMMIT_MSG", "")

    snapshot["run_id"] = os.environ.get("RUN_ID", "")
    snapshot["repo"] = os.environ.get("REPO", "")
    snapshot["commit_sha"] = commit_sha[:7]
    snapshot["commit_msg"] = commit_msg.splitlines()[0][:80] if commit_msg else ""
    snapshot["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    return snapshot


def main():
    snapshot = build_snapshot()

    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
