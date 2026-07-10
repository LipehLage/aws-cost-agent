"""
Coleta de custos reais via AWS Cost Explorer (boto3).

Requer credenciais AWS configuradas (env vars, ~/.aws ou role) com a
permissão `ce:GetCostAndUsage`. Para experimentar sem conta AWS, use o
modo demo (--demo), que não passa por aqui.
"""

from datetime import date, timedelta

import boto3


def fetch_costs(days: int = 30, profile: str | None = None) -> list[dict]:
    """
    Busca os custos diários por serviço dos últimos `days` dias.

    Retorna registros no formato {date, service, amount} — o mesmo do
    dataset demo, para que o resto do pipeline não saiba a diferença.
    """
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    client = session.client("ce", region_name="us-east-1")

    end = date.today()
    start = end - timedelta(days=days)

    records: list[dict] = []
    token = None
    while True:
        kwargs = {
            "TimePeriod": {"Start": start.isoformat(), "End": end.isoformat()},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if token:
            kwargs["NextPageToken"] = token
        response = client.get_cost_and_usage(**kwargs)

        for day in response["ResultsByTime"]:
            for group in day["Groups"]:
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount <= 0:
                    continue
                records.append(
                    {
                        "date": day["TimePeriod"]["Start"],
                        "service": group["Keys"][0],
                        "amount": round(amount, 2),
                    }
                )

        token = response.get("NextPageToken")
        if not token:
            break

    return records
