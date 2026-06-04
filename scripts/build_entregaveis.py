"""Organiza os entregáveis finais na pasta entregaveis/.

Copia os 4 gráficos de graphs/, o metrics.csv e o REPORT.md para
entregaveis/, criando a estrutura necessária. Encerra com mensagem de erro
clara se algum arquivo obrigatório estiver faltando.

Usa apenas stdlib: shutil, os, pathlib, sys.
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "entregaveis"

GRAPH_NAMES = [
    "01_tempo_total_pipeline.png",
    "02_tempo_por_job.png",
    "03_taxa_sucesso_falha.png",
    "04_testes_vs_duracao.png",
]


def check_required():
    """Verifica se todos os arquivos obrigatórios existem; lista os ausentes."""
    required = [ROOT / "graphs" / name for name in GRAPH_NAMES]
    required.append(ROOT / "metrics.csv")
    required.append(ROOT / "REPORT.md")

    missing = [p for p in required if not p.is_file()]
    return required, missing


def main():
    required, missing = check_required()

    if missing:
        print("Erro: arquivos obrigatórios não encontrados:", file=sys.stderr)
        for p in missing:
            print(f"  - {p.relative_to(ROOT)}", file=sys.stderr)
        print(
            "\nGere-os antes de montar os entregáveis:\n"
            "  python collect_metrics.py --repo SEU_USUARIO/cpf-cnpj-validator\n"
            "  python generate_graphs.py --input metrics.csv",
            file=sys.stderr,
        )
        sys.exit(1)

    # Cria a estrutura de destino
    (DEST / "graphs").mkdir(parents=True, exist_ok=True)

    copied = []

    # Copia os gráficos
    for name in GRAPH_NAMES:
        src = ROOT / "graphs" / name
        dst = DEST / "graphs" / name
        shutil.copy2(src, dst)
        copied.append(dst)
        print(f"Copiado: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    # Copia metrics.csv e REPORT.md
    for name in ("metrics.csv", "REPORT.md"):
        src = ROOT / name
        dst = DEST / name
        shutil.copy2(src, dst)
        copied.append(dst)
        print(f"Copiado: {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    # Resumo final
    print(f"\nEntregáveis montados em {DEST.relative_to(ROOT)}/ "
          f"({len(copied)} arquivos):")
    for path in sorted(DEST.rglob("*")):
        if path.is_file():
            size = path.stat().st_size
            print(f"  {path.relative_to(DEST)}  ({size} bytes)")


if __name__ == "__main__":
    main()
