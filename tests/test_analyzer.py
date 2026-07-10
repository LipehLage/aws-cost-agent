from cost_agent import analyzer, demo_data


def test_summarize_totals_match_records():
    records = demo_data.generate(days=30)
    summary = analyzer.summarize(records)

    assert summary["period"]["days"] == 30
    assert summary["total"] == round(sum(r["amount"] for r in records), 2)
    # ranking cobre todos os serviços e vem ordenado do maior para o menor
    assert len(summary["by_service"]) == len(demo_data.BASELINE)
    totals = [item["total"] for item in summary["by_service"]]
    assert totals == sorted(totals, reverse=True)


def test_summarize_detects_planted_anomaly():
    records = demo_data.generate(days=30)
    summary = analyzer.summarize(records)

    services = [a["service"] for a in summary["anomalies"]]
    assert demo_data.ANOMALY_SERVICE in services
    top = summary["anomalies"][0]
    assert top["growth_pct"] >= analyzer.GROWTH_THRESHOLD * 100


def test_summarize_empty_input():
    summary = analyzer.summarize([])
    assert summary["total"] == 0.0
    assert summary["by_service"] == []
    assert summary["anomalies"] == []
