"""
Análise dos custos: agrega, ranqueia e caça anomalias.

Trabalha sobre registros {date, service, amount} — não importa se vieram
do Cost Explorer real ou do dataset demo. A saída é um resumo estruturado
que o repórter (LLM ou fallback) transforma em relatório executivo.
"""

from collections import defaultdict

# Uma anomalia só interessa se o serviço cresceu de verdade E custa algo
GROWTH_THRESHOLD = 0.25  # +25% semana contra semana
MIN_WEEKLY_COST = 10.0  # USD na última semana


def summarize(records: list[dict]) -> dict:
    """Resume o período: totais, ranking por serviço e anomalias de crescimento."""
    if not records:
        return {
            "period": {"start": None, "end": None, "days": 0},
            "total": 0.0,
            "by_service": [],
            "anomalies": [],
        }

    dates = sorted({r["date"] for r in records})
    by_service: dict[str, float] = defaultdict(float)
    daily_by_service: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for r in records:
        by_service[r["service"]] += r["amount"]
        daily_by_service[r["service"]][r["date"]] += r["amount"]

    total = sum(by_service.values())
    ranking = [
        {
            "service": service,
            "total": round(amount, 2),
            "share": round(amount / total * 100, 1) if total else 0.0,
        }
        for service, amount in sorted(by_service.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # Semana contra semana: últimos 7 dias vs. os 7 anteriores
    last_week = set(dates[-7:])
    previous_week = set(dates[-14:-7])
    anomalies = []
    for service, per_day in daily_by_service.items():
        current = sum(v for d, v in per_day.items() if d in last_week)
        previous = sum(v for d, v in per_day.items() if d in previous_week)
        if previous <= 0 or current < MIN_WEEKLY_COST:
            continue
        growth = (current - previous) / previous
        if growth >= GROWTH_THRESHOLD:
            anomalies.append(
                {
                    "service": service,
                    "last_week": round(current, 2),
                    "previous_week": round(previous, 2),
                    "growth_pct": round(growth * 100, 1),
                }
            )
    anomalies.sort(key=lambda a: a["growth_pct"], reverse=True)

    return {
        "period": {"start": dates[0], "end": dates[-1], "days": len(dates)},
        "total": round(total, 2),
        "by_service": ranking,
        "anomalies": anomalies,
    }
