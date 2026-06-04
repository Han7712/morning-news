import pytest

from morning_news.validation import (
    detect_script_violations,
    research_quality_from_show_notes,
    validate_duration_seconds,
    validate_metadata,
    validate_research_notes,
)


def valid_metadata() -> dict[str, object]:
    return {
        "date": "2026-06-04",
        "slug": "rates-oil-ai",
        "title": "Rates, Oil, and AI Capex",
        "summary": "A source-backed market morning briefing.",
        "keywords": ["rates", "oil", "AI capex"],
        "audio_path": "audio/2026-06-04-rates-oil-ai.mp3",
        "script_path": "scripts/2026-06-04-rates-oil-ai.md",
        "show_notes_path": "show_notes/2026-06-04-rates-oil-ai.md",
        "voice": "zh-CN-YunyangNeural",
        "duration_seconds": 640,
        "file_size_bytes": 3840000,
        "main_market_line": "Growth is resilient but oil is raising the inflation cost.",
        "source_count": 9,
        "research_quality": {
            "candidate_count": 10,
            "selected_count": 3,
            "has_rejected_rationale": True,
            "has_credible_sources": True,
            "humanizer_zh_passed": True,
            "has_candidate_fields": True,
            "has_selected_relevance": True,
            "has_sources_section": True,
            "has_editorial_qa": True,
            "source_url_count": 9,
            "source_count_matches": True,
        },
    }


def test_validate_metadata_accepts_complete_record() -> None:
    validate_metadata(valid_metadata())


def test_validate_metadata_rejects_missing_research_quality() -> None:
    metadata = valid_metadata()
    metadata.pop("research_quality")

    with pytest.raises(ValueError, match="research_quality"):
        validate_metadata(metadata)


def test_validate_metadata_rejects_weak_research_gate() -> None:
    metadata = valid_metadata()
    metadata["research_quality"] = {
        "candidate_count": 2,
        "selected_count": 1,
        "has_rejected_rationale": False,
        "has_credible_sources": True,
        "humanizer_zh_passed": True,
    }

    with pytest.raises(ValueError, match="candidate_count"):
        validate_metadata(metadata)


def test_validate_metadata_rejects_missing_humanizer_zh_pass() -> None:
    metadata = valid_metadata()
    metadata["research_quality"] = {
        "candidate_count": 10,
        "selected_count": 3,
        "has_rejected_rationale": True,
        "has_credible_sources": True,
        "humanizer_zh_passed": False,
    }

    with pytest.raises(ValueError, match="humanizer_zh_passed"):
        validate_metadata(metadata)


def test_validate_metadata_rejects_source_count_mismatch() -> None:
    metadata = valid_metadata()
    research_quality = dict(metadata["research_quality"])  # type: ignore[arg-type]
    research_quality["source_count_matches"] = False
    metadata["research_quality"] = research_quality

    with pytest.raises(ValueError, match="source_count_matches"):
        validate_metadata(metadata)


def good_show_notes() -> str:
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
    return (
        "# Show Notes\n\n"
        "Main market line: Oil and rates are tightening financial conditions.\n\n"
        "## Candidate Stories\n"
        f"{candidates}\n\n"
        "## Selected Stories\n"
        "- Oil and Fed pricing: Why it matters today: it changes inflation breakevens. "
        "Market / HF / IB angle: duration risk and financing windows.\n"
        "- AI capex: Why it matters today: it anchors mega-cap earnings revisions. "
        "Market / HF / IB angle: semis, credit, and equity issuance.\n"
        "- China demand: Why it matters today: it affects Asia risk appetite. "
        "Market / HF / IB angle: HK beta and cross-border flows.\n\n"
        "## Rejected Stories\n"
        "- One-off small-cap move: Rejected because liquidity was thin, source quality was weak, "
        "and the story had no clear cross-asset read-through.\n\n"
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
        f"{sources}\n"
    )


def test_validate_research_notes_accepts_source_backed_editorial_qa() -> None:
    notes = good_show_notes()

    assert validate_research_notes(notes, declared_source_count=9) == []
    quality = research_quality_from_show_notes(notes, declared_source_count=9)
    assert quality["candidate_count"] == 10
    assert quality["selected_count"] == 3
    assert quality["has_candidate_fields"] is True
    assert quality["has_selected_relevance"] is True
    assert quality["has_editorial_qa"] is True
    assert quality["source_url_count"] == 9
    assert quality["source_count_matches"] is True


def test_validate_research_notes_rejects_missing_editorial_qa_and_source_mismatch() -> None:
    notes = good_show_notes().replace(
        "## Editorial QA\n"
        "- Candidate field check: every candidate has source, credibility, asset relevance, "
        "and Market / HF / IB relevance.\n"
        "- Selection check: selected stories support the main market line and explain why they matter today.\n"
        "- Rejected rationale check: rejected stories explain why they were excluded.\n"
        "- Source count check: 9 source URLs are listed below and match CLI source_count.\n\n",
        "",
    )

    violations = validate_research_notes(notes, declared_source_count=8)

    assert "missing_editorial_qa" in violations
    assert "source_count_mismatch" in violations


def test_validate_research_notes_rejects_main_market_line_mismatch() -> None:
    violations = validate_research_notes(
        good_show_notes(),
        declared_source_count=9,
        main_market_line="A totally different market line.",
    )

    assert "main_market_line_mismatch" in violations


def test_validate_research_notes_requires_candidate_source_urls() -> None:
    notes = good_show_notes().replace("https://candidate.example.com/1", "source unavailable")

    violations = validate_research_notes(
        notes,
        declared_source_count=9,
        main_market_line="Oil and rates are tightening financial conditions.",
    )

    assert "malformed_candidate_fields" in violations


def test_validate_duration_seconds_accepts_normal_episode_and_sample_exception() -> None:
    validate_duration_seconds("2026-06-04", "rates-oil-ai", 640)
    validate_duration_seconds("2026-06-03", "sample-oil-rates-ai", 340)


def test_validate_duration_seconds_rejects_short_or_long_normal_episode() -> None:
    with pytest.raises(ValueError, match="below normal range"):
        validate_duration_seconds("2026-06-04", "rates-oil-ai", 340)

    with pytest.raises(ValueError, match="above normal range"):
        validate_duration_seconds("2026-06-04", "rates-oil-ai", 900)


def test_detect_script_violations_catches_style_and_quality_issues() -> None:
    text = (
        "主线：油价和利率让 risk-on 成本上升。\n"
        "这里有一个停顿—需要拦截。\n"
        "这不是简单利好，而是更复杂的信号。\n"
        "Sources: Reuters\n"
    )

    assert detect_script_violations(text) == [
        "dash_break",
        "banned_correction_pattern",
        "script_too_short",
    ]


def test_detect_script_violations_requires_main_line_and_sources() -> None:
    text = "早上好，今天市场仍然在交易增长韧性。"

    assert detect_script_violations(text) == [
        "missing_main_market_line",
        "missing_source_marker",
        "script_too_short",
    ]
