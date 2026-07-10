"""
Entrada para execução como AWS Lambda agendada (ver terraform/).

Roda o pipeline com as credenciais da role da Lambda e, se SNS_TOPIC_ARN
estiver configurado, publica o relatório no tópico (e-mail, Slack via
subscription etc.). Sempre devolve o relatório no retorno da invocação.
"""

import os

import boto3

from cost_agent import analyzer, collector, reporter


def handler(event, context):
    days = int(os.environ.get("ANALYSIS_DAYS", "30"))
    records = collector.fetch_costs(days=days)
    summary = analyzer.summarize(records)
    report = reporter.generate_report(summary)

    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if topic_arn:
        boto3.client("sns").publish(
            TopicArn=topic_arn,
            Subject=f"Relatório de custos AWS — USD {summary['total']:.2f} em {days} dias",
            Message=report,
        )

    return {"total": summary["total"], "anomalies": len(summary["anomalies"]), "report": report}
