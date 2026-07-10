"""
CLI do agente: coleta → análise → relatório.

    python -m cost_agent --demo            # sem conta AWS, sem API key
    python -m cost_agent --days 30         # conta real (credenciais AWS)
    python -m cost_agent --demo -o rel.md  # salva em arquivo
"""

import argparse
import sys

from . import analyzer, demo_data, reporter


def main(argv: list[str] | None = None) -> int:
    # Consoles Windows usam cp1252 por padrão e quebram com setas/acentos
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="cost_agent",
        description="Analisa custos AWS e gera relatório executivo com IA.",
    )
    parser.add_argument("--demo", action="store_true", help="usa dataset de demonstração (não precisa de AWS)")
    parser.add_argument("--days", type=int, default=30, help="janela de análise em dias (padrão: 30)")
    parser.add_argument("--profile", help="profile AWS a usar (padrão: credenciais default)")
    parser.add_argument("--model", help="modelo Gemini (padrão: gemini-flash-latest)")
    parser.add_argument("-o", "--output", help="arquivo de saída (padrão: stdout)")
    args = parser.parse_args(argv)

    if args.demo:
        records = demo_data.generate(days=args.days)
    else:
        from . import collector  # boto3 só é exigido no modo real

        records = collector.fetch_costs(days=args.days, profile=args.profile)

    summary = analyzer.summarize(records)
    report = reporter.generate_report(summary, model=args.model)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
        print(f"Relatório salvo em {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
