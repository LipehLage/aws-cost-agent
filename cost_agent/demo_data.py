"""
Dataset de demonstração: 30 dias de custos de uma conta AWS fictícia.

Gerado de forma determinística (seed fixa) para que o modo demo produza
sempre o mesmo cenário: uma conta estável com um problema plantado — o
custo de NAT Gateway cresce dia após dia, como acontece quando alguém
esquece tráfego cruzando AZs. É o tipo de anomalia que o agente deve pegar.
"""

import random
from datetime import date, timedelta

# Custo diário base (USD) por serviço, inspirado em uma conta de médio porte
BASELINE = {
    "Amazon Elastic Container Service": 38.0,
    "Amazon Relational Database Service": 55.0,
    "Amazon EC2 - Other": 22.0,
    "AWS Lambda": 4.5,
    "Amazon Simple Queue Service": 2.1,
    "Amazon Virtual Private Cloud": 12.0,
    "Amazon CloudWatch": 8.5,
    "Amazon Simple Storage Service": 6.2,
}

# Serviço com anomalia plantada: cresce ~6% ao dia no período
ANOMALY_SERVICE = "Amazon Virtual Private Cloud"
ANOMALY_DAILY_GROWTH = 1.06


def generate(days: int = 30, end: date | None = None) -> list[dict]:
    """Retorna registros {date, service, amount} como o Cost Explorer devolveria."""
    rng = random.Random(42)
    end = end or date.today()
    records = []
    for offset in range(days, 0, -1):
        day = end - timedelta(days=offset)
        for service, base in BASELINE.items():
            amount = base * rng.uniform(0.9, 1.1)
            if service == ANOMALY_SERVICE:
                # crescimento composto a partir do início do período
                amount *= ANOMALY_DAILY_GROWTH ** (days - offset)
            records.append(
                {
                    "date": day.isoformat(),
                    "service": service,
                    "amount": round(amount, 2),
                }
            )
    return records
