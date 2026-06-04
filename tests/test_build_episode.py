import json
from pathlib import Path

from tools import build_episode


def long_script(tmp_path: Path) -> Path:
    path = tmp_path / "script.md"
    paragraph = (
        "主线：美国增长还没有明显掉下去，但油价和成本压力又开始回来。"
        "这会影响美债收益率、风险偏好和科技股估值。"
        "市场可能会把它理解为 higher for longer 的风险重新抬头。"
        "Broadcom 的 AI capex 线索也说明数据中心资本开支仍在扩张。"
    )
    path.write_text(
        "# Morning News 2026-06-04\n\n"
        + "\n\n".join([paragraph] * 25)
        + "\n\nSources: Reuters, Federal Reserve, Broadcom IR\n",
        encoding="utf-8",
    )
    return path


def valid_show_notes(tmp_path: Path) -> Path:
    path = tmp_path / "show_notes.md"
    candidates = "\n".join(
        [
            f"- Candidate {idx}: Reuters source https://example.com/{idx} ; credibility: wire; relevance: rates"
            for idx in range(1, 11)
        ]
    )
    path.write_text(
        "# Show Notes\n\n"
        "Main market line: Growth is resilient but oil is raising the inflation cost.\n\n"
        "## Candidate Stories\n"
        f"{candidates}\n\n"
        "## Selected Stories\n"
        "- Fed and oil: why it matters today; market / HF / IB angle: rates and margins.\n"
        "- Broadcom AI capex: why it matters today; market / HF / IB angle: semis and financing.\n"
        "- China services: why it matters today; market / HF / IB angle: HK tech risk appetite.\n\n"
        "## Rejected Stories\n"
        "- Minor single-stock move rejected because impact was narrow and low-credibility.\n\n"
        "## Humanizer-zh Pass\n"
        "- Applied `/Users/han/.agents/skills/humanizer-zh/SKILL.md` after the first script draft.\n"
        "- Revised formulaic transitions and sentence rhythm before TTS.\n\n"
        "## Sources\n"
        "- Reuters: https://example.com/reuters\n"
        "- Federal Reserve: https://example.com/fed\n",
        encoding="utf-8",
    )
    return path


def configure_cli(
    monkeypatch,
    tmp_path: Path,
    script_path: Path,
    show_notes_path: Path,
    *extra_args: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "build_episode.py",
            "--date",
            "2026-06-04",
            "--slug",
            "rates-oil-ai",
            "--title",
            "Rates, Oil, and AI Capex",
            "--summary",
            "A source-backed market morning briefing.",
            "--keywords",
            "rates,oil,AI capex",
            "--script",
            str(script_path),
            "--show-notes",
            str(show_notes_path),
            "--voice",
            "zh-CN-YunyangNeural",
            "--rate=+0%",
            "--main-market-line",
            "Growth is resilient but oil is raising the inflation cost.",
            "--source-count",
            "9",
            "--site-url",
            "https://Han7712.github.io/morning-news",
            *extra_args,
        ],
    )


def test_successful_build_publishes_complete_episode_package(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    def fake_tts(_text: str, output_path: Path, **_kwargs) -> None:
        output_path.write_bytes(b"audio bytes")

    monkeypatch.setattr(build_episode, "save_edge_tts", fake_tts)
    monkeypatch.setattr(build_episode, "read_duration_seconds", lambda _path: 640)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    metadata = json.loads(
        (tmp_path / "docs/metadata/2026-06-04.json").read_text(encoding="utf-8")
    )
    assert exit_code == 0
    assert report["ok"] is True
    assert report["audio_path"].endswith("docs/audio/2026-06-04-rates-oil-ai.mp3")
    assert report["show_notes_path"].endswith("docs/show_notes/2026-06-04-rates-oil-ai.md")
    assert metadata["show_notes_path"] == "show_notes/2026-06-04-rates-oil-ai.md"
    assert metadata["main_market_line"] == "Growth is resilient but oil is raising the inflation cost."
    assert metadata["research_quality"]["candidate_count"] == 10
    assert metadata["research_quality"]["selected_count"] == 3
    assert metadata["research_quality"]["humanizer_zh_passed"] is True
    assert (tmp_path / "docs/feed.xml").read_text(encoding="utf-8").count("<item>") == 1
    index_html = (tmp_path / "docs/index.html").read_text(encoding="utf-8")
    assert 'rel="alternate" type="application/rss+xml"' in index_html
    assert "https://Han7712.github.io/morning-news/feed.xml" in index_html
    assert "show_notes/2026-06-04-rates-oil-ai.md" in index_html


def test_style_failure_writes_report_and_preserves_existing_feed(tmp_path: Path, monkeypatch) -> None:
    script_path = tmp_path / "bad_script.md"
    script_path.write_text("主线：短稿。\n这不是A，而是B。\nSources: Reuters", encoding="utf-8")
    show_notes_path = valid_show_notes(tmp_path)
    feed_path = tmp_path / "docs/feed.xml"
    feed_path.parent.mkdir(parents=True)
    feed_path.write_text("<rss>existing</rss>", encoding="utf-8")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 2
    assert report["ok"] is False
    assert report["stage"] == "script_validation"
    assert feed_path.read_text(encoding="utf-8") == "<rss>existing</rss>"


def test_research_failure_writes_report_before_tts(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = tmp_path / "weak_notes.md"
    show_notes_path.write_text("## Candidate Stories\n- one https://example.com\n", encoding="utf-8")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 2
    assert report["ok"] is False
    assert report["stage"] == "research_validation"


def test_research_failure_requires_humanizer_zh_pass(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    notes = show_notes_path.read_text(encoding="utf-8")
    notes = notes.replace(
        "## Humanizer-zh Pass\n"
        "- Applied `/Users/han/.agents/skills/humanizer-zh/SKILL.md` after the first script draft.\n"
        "- Revised formulaic transitions and sentence rhythm before TTS.\n\n",
        "",
    )
    show_notes_path.write_text(notes, encoding="utf-8")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 2
    assert report["ok"] is False
    assert report["stage"] == "research_validation"
    assert "missing_humanizer_zh_pass" in report["message"]


def test_tts_failure_preserves_existing_audio(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    audio_path = tmp_path / "docs/audio/2026-06-04-rates-oil-ai.mp3"
    audio_path.parent.mkdir(parents=True)
    audio_path.write_bytes(b"existing audio")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    def fail_tts(*_args, **_kwargs) -> None:
        raise RuntimeError("tts unavailable")

    monkeypatch.setattr(build_episode, "save_edge_tts", fail_tts)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 1
    assert report["ok"] is False
    assert report["stage"] == "tts"
    assert audio_path.read_bytes() == b"existing audio"


def test_rate_argument_accepts_attached_negative_value(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path, "--rate=-5%")

    args = build_episode.parse_args()

    assert args.rate == "-5%"
