from cost_agent import analyzer, demo_data, reporter


def _summary():
    return analyzer.summarize(demo_data.generate(days=30))


def test_basic_report_contains_key_facts():
    summary = _summary()
    report = reporter.basic_report(summary)

    assert f"USD {summary['total']:.2f}" in report
    assert summary["by_service"][0]["service"] in report
    assert demo_data.ANOMALY_SERVICE in report


def test_generate_report_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = reporter.generate_report(_summary())
    assert "Relatório básico" in report


def test_prompt_carries_summary_data():
    summary = _summary()
    prompt = reporter.build_prompt(summary)
    assert "FinOps" in prompt
    assert summary["by_service"][0]["service"] in prompt
