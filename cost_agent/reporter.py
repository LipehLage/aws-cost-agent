"""
Geração do relatório executivo.

Com GEMINI_API_KEY configurada, um LLM escreve o relatório em linguagem
executiva, com recomendações de otimização. Sem a chave, um fallback
determinístico monta um relatório objetivo com os mesmos dados — o
pipeline nunca fica refém da API.
"""

import json
import os


def build_prompt(summary: dict) -> str:
    """Monta o prompt com o resumo estruturado dos custos."""
    return (
        "Você é um especialista em FinOps. Analise o resumo de custos AWS "
        "abaixo (valores em USD) e escreva um relatório executivo em "
        "português, formato Markdown, com as seções: Visão Geral, Principais "
        "Ofensores, Anomalias Detectadas e Recomendações de Otimização. Seja "
        "direto e acionável: cada recomendação deve citar o serviço, o motivo "
        "e uma ação concreta (ex.: rever NAT Gateway, Savings Plans, "
        "right-sizing, lifecycle de S3). Não invente números que não estejam "
        "no resumo.\n\n"
        f"RESUMO:\n{json.dumps(summary, ensure_ascii=False, indent=2)}"
    )


def basic_report(summary: dict) -> str:
    """Relatório determinístico usado quando não há chave de API."""
    lines = [
        "# Relatório de custos AWS",
        "",
        f"Período: {summary['period']['start']} a {summary['period']['end']} "
        f"({summary['period']['days']} dias)",
        f"Custo total: **USD {summary['total']:.2f}**",
        "",
        "## Principais ofensores",
        "",
    ]
    for item in summary["by_service"][:5]:
        lines.append(f"- {item['service']}: USD {item['total']:.2f} ({item['share']}%)")

    lines += ["", "## Anomalias detectadas", ""]
    if summary["anomalies"]:
        for a in summary["anomalies"]:
            lines.append(
                f"- **{a['service']}**: USD {a['previous_week']:.2f} → "
                f"USD {a['last_week']:.2f} na última semana "
                f"(+{a['growth_pct']}%) — investigar."
            )
    else:
        lines.append("Nenhum crescimento anômalo semana contra semana.")

    lines += [
        "",
        "_Relatório básico (sem LLM). Configure GEMINI_API_KEY para o "
        "relatório executivo com recomendações._",
    ]
    return "\n".join(lines)


def generate_report(summary: dict, api_key: str | None = None, model: str | None = None) -> str:
    """Gera o relatório: LLM se houver chave, fallback básico caso contrário."""
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return basic_report(summary)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model or os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
            contents=build_prompt(summary),
            config=types.GenerateContentConfig(
                # Tokens de raciocínio contam no limite de saída; desativa
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2000,
                temperature=0.3,
            ),
        )
    except Exception as exc:  # API fora do ar não pode derrubar o pipeline
        return (
            basic_report(summary)
            + f"\n\n_Falha ao consultar o LLM ({type(exc).__name__}); "
            "relatório básico entregue no lugar._"
        )
    return (response.text or "").strip() or basic_report(summary)
