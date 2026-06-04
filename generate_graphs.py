"""Lê o metrics.csv e gera 4 gráficos em graphs/.

Uso: python generate_graphs.py [--input metrics.csv] [--outdir graphs]

Dependências: pandas, matplotlib.
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")  # backend sem display, para rodar em CI/headless
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

GREEN = "#2ca02c"
RED = "#d62728"


def is_success(status):
    return str(status).strip().lower() == "success"


def make_labels(df):
    """Rótulo do eixo X: número da execução + commit sha (ex: '1\n<sha>')."""
    return [f"{i + 1}\n{sha}" for i, sha in enumerate(df["commit_sha"])]


def grafico_tempo_total(df, labels, path):
    """Gráfico 1 — barras do tempo total do pipeline por execução."""
    colors = [GREEN if is_success(s) else RED for s in df["status"]]
    fig, ax = plt.subplots(figsize=(max(8, len(df) * 1.2), 6))
    bars = ax.bar(labels, df["workflow_duration"], color=colors)

    for bar, value in zip(bars, df["workflow_duration"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.0f}s",
            ha="center",
            va="bottom",
        )

    ax.set_xlabel("Execução + commit")
    ax.set_ylabel("Duração (s)")
    ax.set_title("Tempo total do pipeline por execução")

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=GREEN, label="success"),
        plt.Rectangle((0, 0), 1, 1, color=RED, label="falha"),
    ]
    ax.legend(handles=handles)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def grafico_tempo_por_job(df, labels, path):
    """Gráfico 2 — barras empilhadas com a duração de cada job."""
    fig, ax = plt.subplots(figsize=(max(8, len(df) * 1.2), 6))

    lint = df["job_lint_duration"]
    test = df["job_test_duration"]
    metrics = df["job_metrics_duration"]

    ax.bar(labels, lint, label="lint", color="#1f77b4")
    ax.bar(labels, test, bottom=lint, label="test", color="#ff7f0e")
    ax.bar(labels, metrics, bottom=lint + test, label="metrics", color="#9467bd")

    ax.set_xlabel("Execução + commit")
    ax.set_ylabel("Duração (s)")
    ax.set_title("Tempo por job em cada execução")
    ax.legend()

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def grafico_taxa_sucesso(df, path):
    """Gráfico 3 — pizza de sucesso vs falha."""
    total = len(df)
    sucessos = sum(is_success(s) for s in df["status"])
    falhas = total - sucessos

    valores = []
    rotulos = []
    cores = []
    if sucessos:
        valores.append(sucessos)
        rotulos.append("Sucesso")
        cores.append(GREEN)
    if falhas:
        valores.append(falhas)
        rotulos.append("Falha")
        cores.append(RED)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(valores, labels=rotulos, colors=cores, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    ax.set_title(f"Taxa de sucesso vs falha (total: {total} execuções)")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def grafico_testes_vs_duracao(df, path):
    """Gráfico 4 — scatter de test_count vs workflow_duration."""
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [GREEN if is_success(s) else RED for s in df["status"]]

    ax.scatter(df["test_count"], df["workflow_duration"], c=colors, s=80)

    for _, row in df.iterrows():
        ax.annotate(
            row["commit_sha"],
            (row["test_count"], row["workflow_duration"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=8,
        )

    ax.set_xlabel("Quantidade de testes (test_count)")
    ax.set_ylabel("Duração do pipeline (s)")
    ax.set_title("Quantidade de testes × duração do pipeline")

    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=GREEN, label="success"),
        plt.Line2D([], [], marker="o", linestyle="", color=RED, label="falha"),
    ]
    ax.legend(handles=handles)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Gera gráficos a partir do metrics.csv")
    parser.add_argument("--input", default="metrics.csv", help="CSV de entrada")
    parser.add_argument("--outdir", default="graphs", help="diretório de saída")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    os.makedirs(args.outdir, exist_ok=True)
    labels = make_labels(df)

    grafico_tempo_total(
        df, labels, os.path.join(args.outdir, "01_tempo_total_pipeline.png")
    )
    grafico_tempo_por_job(
        df, labels, os.path.join(args.outdir, "02_tempo_por_job.png")
    )
    grafico_taxa_sucesso(df, os.path.join(args.outdir, "03_taxa_sucesso_falha.png"))
    grafico_testes_vs_duracao(
        df, os.path.join(args.outdir, "04_testes_vs_duracao.png")
    )

    print(f"4 gráficos gerados em {args.outdir}/")


if __name__ == "__main__":
    main()
