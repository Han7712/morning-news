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
            "- Candidate {idx}: Source: Reuters https://candidate.example.com/{idx}; "
            "Credibility: tier-1 public source; Asset relevance: rates, FX, equities; "
            "Market / HF / IB relevance: affects rates books and financing windows.".format(
                idx=idx
            )
            for idx in range(1, 11)
        ]
    )
    sources = "\n".join(
        [
            f"- Source {idx}: https://sources.example.com/{idx}"
            for idx in range(1, 10)
        ]
    )
    path.write_text(
        "# Show Notes\n\n"
        "Main market line: Growth is resilient but oil is raising the inflation cost.\n\n"
        "## Candidate Stories\n"
        f"{candidates}\n\n"
        "## Selected Stories\n"
        "- Fed and oil: Why it matters today: inflation breakevens are moving. "
        "Market / HF / IB angle: rates and margins.\n"
        "- Broadcom AI capex: Why it matters today: AI spending still supports earnings revisions. "
        "Market / HF / IB angle: semis and financing.\n"
        "- China services: Why it matters today: Asia risk appetite can reprice quickly. "
        "Market / HF / IB angle: HK tech risk appetite.\n\n"
        "## Rejected Stories\n"
        "- Minor single-stock move: Rejected because impact was narrow, source quality was weak, "
        "and it had no cross-asset read-through.\n\n"
        "## Freshness and Repetition Check\n"
        "- Recent-topic review: checked content/state.json recent main lines and recent slugs.\n"
        "- Overlap decisions: Broadcom and AI capex overlap was allowed only with a new market read-through.\n"
        "- Material increment: repeated macro context was tied to new pricing and financing implications.\n"
        "- Broadened search: reviewed geopolitics, regulation, credit, ECM, Asia, and business policy headlines.\n"
        "- Padding check: script was not padded with stale material to reach the duration target.\n\n"
        "## Humanizer-zh Pass\n"
        "- Applied `/Users/han/.agents/skills/humanizer-zh/SKILL.md` after the first script draft.\n"
        "- Revised formulaic transitions and sentence rhythm before TTS.\n\n"
        "## Editorial QA\n"
        "- Candidate field check: every candidate has source, credibility, asset relevance, "
        "and Market / HF / IB relevance.\n"
        "- Selection check: selected stories support the main market line and explain why they matter today.\n"
        "- Rejected rationale check: rejected stories explain why they were excluded.\n"
        "- Source count check: 9 source URLs are listed below and match CLI source_count.\n\n"
        "## Sources\n"
        f"{sources}\n",
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
    spoken_inputs: list[str] = []

    def fake_tts(text: str, output_path: Path, **_kwargs) -> None:
        spoken_inputs.append(text)
        output_path.write_bytes(b"audio bytes")

    def fake_mix(_voice_path: Path, _intro_path: Path, output_path: Path) -> None:
        output_path.write_bytes(b"mixed audio bytes")

    monkeypatch.setattr(build_episode, "save_edge_tts", fake_tts)
    monkeypatch.setattr(build_episode, "mix_intro_with_voice", fake_mix)
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
    assert metadata["research_quality"]["has_editorial_qa"] is True
    assert metadata["research_quality"]["has_freshness_check"] is True
    assert metadata["research_quality"]["source_count_matches"] is True
    assert (tmp_path / "docs/feed.xml").read_text(encoding="utf-8").count("<item>") == 1
    assert "Sources:" not in spoken_inputs[0]
    assert "# Morning News" not in spoken_inputs[0]
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


def test_audio_mix_failure_preserves_existing_audio(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    audio_path = tmp_path / "docs/audio/2026-06-04-rates-oil-ai.mp3"
    audio_path.parent.mkdir(parents=True)
    audio_path.write_bytes(b"existing audio")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    monkeypatch.setattr(
        build_episode,
        "save_edge_tts",
        lambda _text, output_path, **_kwargs: output_path.write_bytes(b"voice"),
    )

    def fail_mix(*_args, **_kwargs) -> None:
        raise RuntimeError("ffmpeg unavailable")

    monkeypatch.setattr(build_episode, "mix_intro_with_voice", fail_mix)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 1
    assert report["ok"] is False
    assert report["stage"] == "audio_mix"
    assert audio_path.read_bytes() == b"existing audio"


def test_duration_gate_failure_preserves_existing_feed(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    feed_path = tmp_path / "docs/feed.xml"
    feed_path.parent.mkdir(parents=True)
    feed_path.write_text("<rss>existing</rss>", encoding="utf-8")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    monkeypatch.setattr(
        build_episode,
        "save_edge_tts",
        lambda _text, output_path, **_kwargs: output_path.write_bytes(b"voice"),
    )
    monkeypatch.setattr(
        build_episode,
        "mix_intro_with_voice",
        lambda _voice_path, _intro_path, output_path: output_path.write_bytes(b"mixed"),
    )
    monkeypatch.setattr(build_episode, "read_duration_seconds", lambda _path: 340)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 1
    assert report["ok"] is False
    assert report["stage"] == "duration_validation"
    assert feed_path.read_text(encoding="utf-8") == "<rss>existing</rss>"


def test_compact_duration_profile_accepts_thin_news_episode(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    configure_cli(
        monkeypatch,
        tmp_path,
        script_path,
        show_notes_path,
        "--duration-profile",
        "compact",
    )

    monkeypatch.setattr(
        build_episode,
        "save_edge_tts",
        lambda _text, output_path, **_kwargs: output_path.write_bytes(b"voice"),
    )
    monkeypatch.setattr(
        build_episode,
        "mix_intro_with_voice",
        lambda _voice_path, _intro_path, output_path: output_path.write_bytes(b"mixed"),
    )
    monkeypatch.setattr(build_episode, "read_duration_seconds", lambda _path: 500)

    exit_code = build_episode.main()

    metadata = json.loads(
        (tmp_path / "docs/metadata/2026-06-04.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 0
    assert metadata["duration_profile"] == "compact"
    assert report["duration_profile"] == "compact"
    assert report["duration_seconds"] == 500


def test_same_date_different_slug_is_rejected_before_tts(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    metadata_dir = tmp_path / "docs/metadata"
    metadata_dir.mkdir(parents=True)
    (metadata_dir / "2026-06-04.json").write_text(
        json.dumps({"date": "2026-06-04", "slug": "other-slug"}) + "\n",
        encoding="utf-8",
    )
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    def fail_if_called(*_args, **_kwargs) -> None:
        raise AssertionError("TTS should not run after duplicate slug validation")

    monkeypatch.setattr(build_episode, "save_edge_tts", fail_if_called)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-delivery_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 2
    assert report["ok"] is False
    assert report["stage"] == "duplicate_episode"


def test_active_build_lock_is_rejected_before_tts(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    (tmp_path / ".morning-news-build.lock").write_text("active\n", encoding="utf-8")
    delivery_report_path = tmp_path / "docs/reports/2026-06-04-delivery_report.json"
    delivery_report_path.parent.mkdir(parents=True)
    delivery_report_path.write_text('{"ok": true, "date": "2026-06-04"}\n', encoding="utf-8")
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path)

    def fail_if_called(*_args, **_kwargs) -> None:
        raise AssertionError("TTS should not run when lock is active")

    monkeypatch.setattr(build_episode, "save_edge_tts", fail_if_called)

    exit_code = build_episode.main()

    report = json.loads(
        (tmp_path / "docs/reports/2026-06-04-build_lock_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert exit_code == 1
    assert report["ok"] is False
    assert report["stage"] == "build_lock"
    assert json.loads(delivery_report_path.read_text(encoding="utf-8"))["ok"] is True


def test_release_build_lock_preserves_new_owner_lock(tmp_path: Path) -> None:
    lock_path = tmp_path / ".morning-news-build.lock"
    lock_path.write_text('{"token": "new-owner"}\n', encoding="utf-8")

    build_episode.release_build_lock(lock_path, "old-owner")

    assert lock_path.exists()


def test_rate_argument_accepts_attached_negative_value(tmp_path: Path, monkeypatch) -> None:
    script_path = long_script(tmp_path)
    show_notes_path = valid_show_notes(tmp_path)
    configure_cli(monkeypatch, tmp_path, script_path, show_notes_path, "--rate=-5%")

    args = build_episode.parse_args()

    assert args.rate == "-5%"
