import pytest

from morning_news.validation import (
    detect_script_violations,
    validate_metadata,
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
    }

    with pytest.raises(ValueError, match="candidate_count"):
        validate_metadata(metadata)


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

