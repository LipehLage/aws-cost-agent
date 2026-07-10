from cost_agent.__main__ import main


def test_cli_demo_prints_report(capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    exit_code = main(["--demo"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "Relatório de custos AWS" in out


def test_cli_demo_writes_output_file(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    target = tmp_path / "report.md"
    exit_code = main(["--demo", "-o", str(target)])

    assert exit_code == 0
    assert "Relatório de custos AWS" in target.read_text(encoding="utf-8")
