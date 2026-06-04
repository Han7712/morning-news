from __future__ import annotations

import re
from typing import Any

BANNED_CORRECTION_RE = re.compile("不" + "是" + r".{0,80}?" + "而" + "是")
DASH_BREAK_CHARS = {chr(0x2014), chr(0x2013), chr(0x2015)}
REQUIRED_METADATA_FIELDS = {
    "date",
    "slug",
    "title",
    "summary",
    "keywords",
    "audio_path",
    "script_path",
    "show_notes_path",
    "voice",
    "duration_seconds",
    "file_size_bytes",
    "main_market_line",
    "source_count",
    "research_quality",
}


def detect_script_violations(text: str, min_chars: int = 1500) -> list[str]:
    violations: list[str] = []

    if any(char in text for char in DASH_BREAK_CHARS):
        violations.append("dash_break")
    if BANNED_CORRECTION_RE.search(text):
        violations.append("banned_correction_pattern")
    if not _has_main_market_line(text):
        violations.append("missing_main_market_line")
    if not _has_source_marker(text):
        violations.append("missing_source_marker")
    if len(_chinese_and_ascii_body(text)) < min_chars:
        violations.append("script_too_short")

    return violations


def validate_metadata(metadata: dict[str, Any]) -> None:
    missing_fields = REQUIRED_METADATA_FIELDS - metadata.keys()
    if missing_fields:
        raise ValueError(f"Missing required metadata fields: {', '.join(sorted(missing_fields))}")

    keywords = metadata["keywords"]
    if not isinstance(keywords, list) or not keywords:
        raise ValueError("Metadata keywords must be a nonempty list")

    for field in ("duration_seconds", "file_size_bytes", "source_count"):
        value = metadata[field]
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"Metadata {field} must be positive")

    if not str(metadata["main_market_line"]).strip():
        raise ValueError("Metadata main_market_line must be nonempty")

    research_quality = metadata["research_quality"]
    if not isinstance(research_quality, dict):
        raise ValueError("Metadata research_quality must be an object")

    candidate_count = research_quality.get("candidate_count")
    if not isinstance(candidate_count, int) or candidate_count < 8:
        raise ValueError("Metadata research_quality.candidate_count must be at least 8")

    selected_count = research_quality.get("selected_count")
    if not isinstance(selected_count, int) or not 2 <= selected_count <= 4:
        raise ValueError("Metadata research_quality.selected_count must be between 2 and 4")

    if research_quality.get("has_credible_sources") is not True:
        raise ValueError("Metadata research_quality.has_credible_sources must be true")

    if research_quality.get("has_rejected_rationale") is not True:
        raise ValueError("Metadata research_quality.has_rejected_rationale must be true")


def _has_main_market_line(text: str) -> bool:
    lowered = text.lower()
    return "主线" in text or "main market line" in lowered


def _has_source_marker(text: str) -> bool:
    lowered = text.lower()
    return "sources:" in lowered or "source:" in lowered or "来源" in text


def _chinese_and_ascii_body(text: str) -> str:
    return re.sub(r"\s+", "", text)

