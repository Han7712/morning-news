from __future__ import annotations

import re
from typing import Any

BANNED_CORRECTION_RE = re.compile("不" + "是" + r".{0,80}?" + "而" + "是")
DASH_BREAK_CHARS = {chr(0x2014), chr(0x2013), chr(0x2015)}
NORMAL_DURATION_MIN_SECONDS = 570
NORMAL_DURATION_MAX_SECONDS = 720
COMPACT_DURATION_MIN_SECONDS = 420
COMPACT_DURATION_MAX_SECONDS = NORMAL_DURATION_MIN_SECONDS
SAMPLE_DURATION_EXCEPTIONS = {("2026-06-03", "sample-oil-rates-ai")}
URL_RE = re.compile(r"https?://[^\s)>]+")
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
    "duration_profile",
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

    if metadata["duration_profile"] not in {"normal", "compact"}:
        raise ValueError("Metadata duration_profile must be normal or compact")

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

    if research_quality.get("humanizer_zh_passed") is not True:
        raise ValueError("Metadata research_quality.humanizer_zh_passed must be true")

    if research_quality.get("has_candidate_fields") is not True:
        raise ValueError("Metadata research_quality.has_candidate_fields must be true")

    if research_quality.get("has_selected_relevance") is not True:
        raise ValueError("Metadata research_quality.has_selected_relevance must be true")

    if research_quality.get("has_sources_section") is not True:
        raise ValueError("Metadata research_quality.has_sources_section must be true")

    if research_quality.get("has_editorial_qa") is not True:
        raise ValueError("Metadata research_quality.has_editorial_qa must be true")

    if research_quality.get("has_freshness_check") is not True:
        raise ValueError("Metadata research_quality.has_freshness_check must be true")

    source_url_count = research_quality.get("source_url_count")
    if not isinstance(source_url_count, int) or source_url_count < 2:
        raise ValueError("Metadata research_quality.source_url_count must be at least 2")

    if research_quality.get("source_count_matches") is not True:
        raise ValueError("Metadata research_quality.source_count_matches must be true")


def validate_duration_seconds(
    date: str,
    slug: str,
    duration_seconds: int,
    duration_profile: str = "normal",
) -> None:
    if (date, slug) in SAMPLE_DURATION_EXCEPTIONS:
        return

    if duration_profile == "compact":
        min_seconds = COMPACT_DURATION_MIN_SECONDS
        max_seconds = COMPACT_DURATION_MAX_SECONDS
    elif duration_profile == "normal":
        min_seconds = NORMAL_DURATION_MIN_SECONDS
        max_seconds = NORMAL_DURATION_MAX_SECONDS
    else:
        raise ValueError(f"unknown duration_profile: {duration_profile}")

    if duration_seconds < min_seconds:
        raise ValueError(
            f"duration_seconds below {duration_profile} range: {duration_seconds} < "
            f"{min_seconds}"
        )
    if duration_seconds > max_seconds:
        raise ValueError(
            f"duration_seconds above {duration_profile} range: {duration_seconds} > "
            f"{max_seconds}"
        )


def research_quality_from_show_notes(
    show_notes: str,
    declared_source_count: int | None = None,
) -> dict[str, Any]:
    candidate_bullets = _section_bullets(show_notes, "Candidate Stories")
    selected_bullets = _section_bullets(show_notes, "Selected Stories")
    rejected_bullets = _section_bullets(show_notes, "Rejected Stories")
    sources_body = _section_body(show_notes, "Sources")
    source_urls = _unique_urls(sources_body or "")
    has_sources_section = sources_body is not None
    source_count_matches = (
        declared_source_count is None or len(source_urls) == declared_source_count
    )
    return {
        "candidate_count": len(candidate_bullets),
        "selected_count": len(selected_bullets),
        "rejected_count": len(rejected_bullets),
        "has_rejected_rationale": _has_rejected_rationale(rejected_bullets),
        "has_credible_sources": has_sources_section and len(source_urls) >= 2,
        "humanizer_zh_passed": _has_humanizer_zh_pass(show_notes),
        "has_candidate_fields": _has_candidate_fields(candidate_bullets),
        "has_selected_relevance": _has_selected_relevance(selected_bullets),
        "has_sources_section": has_sources_section,
        "has_editorial_qa": _has_editorial_qa(show_notes),
        "has_freshness_check": _has_freshness_check(show_notes),
        "source_url_count": len(source_urls),
        "source_count_matches": source_count_matches,
    }


def validate_research_notes(
    show_notes: str,
    declared_source_count: int | None = None,
    main_market_line: str | None = None,
) -> list[str]:
    quality = research_quality_from_show_notes(show_notes, declared_source_count)
    violations: list[str] = []
    if quality["candidate_count"] < 8:
        violations.append("candidate_count")
    if not quality["has_candidate_fields"]:
        violations.append("malformed_candidate_fields")
    if not 2 <= quality["selected_count"] <= 4:
        violations.append("selected_count")
    if not quality["has_selected_relevance"]:
        violations.append("weak_selected_relevance")
    if quality["rejected_count"] == 0:
        violations.append("missing_rejected_rationale")
    elif not quality["has_rejected_rationale"]:
        violations.append("weak_rejected_rationale")
    if not quality["has_credible_sources"]:
        violations.append("missing_credible_source_links")
    if not quality["has_sources_section"]:
        violations.append("missing_sources_section")
    if not quality["source_count_matches"]:
        violations.append("source_count_mismatch")
    if not quality["humanizer_zh_passed"]:
        violations.append("missing_humanizer_zh_pass")
    if not quality["has_editorial_qa"]:
        violations.append("missing_editorial_qa")
    if not quality["has_freshness_check"]:
        violations.append("missing_freshness_check")
    if not _has_main_market_line(show_notes):
        violations.append("missing_main_market_line")
    if main_market_line and not _main_market_line_matches(show_notes, main_market_line):
        violations.append("main_market_line_mismatch")
    return violations


def _has_main_market_line(text: str) -> bool:
    lowered = text.lower()
    return "主线" in text or "main market line" in lowered


def _has_source_marker(text: str) -> bool:
    lowered = text.lower()
    return "sources:" in lowered or "source:" in lowered or "来源" in text


def _chinese_and_ascii_body(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _section_body(markdown: str, section_title: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(section_title)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return None
    return match.group(1)


def _section_bullets(markdown: str, section_title: str) -> list[str]:
    body = _section_body(markdown, section_title)
    if body is None:
        return []

    bullets: list[str] = []
    current: list[str] = []
    for line in body.splitlines():
        if re.match(r"^\s*[-*]\s+", line):
            if current:
                bullets.append(" ".join(current).strip())
            current = [re.sub(r"^\s*[-*]\s+", "", line).strip()]
        elif current and line.startswith((" ", "\t")):
            current.append(line.strip())
    if current:
        bullets.append(" ".join(current).strip())
    return [bullet for bullet in bullets if bullet]


def _unique_urls(text: str) -> list[str]:
    urls = []
    seen = set()
    for match in URL_RE.findall(text):
        url = match.rstrip(".,;")
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls


def _has_humanizer_zh_pass(show_notes: str) -> bool:
    section_body = _section_body(show_notes, "Humanizer-zh Pass")
    if section_body is None:
        return False
    lowered = section_body.lower()
    return "humanizer-zh" in lowered and "skill.md" in lowered


def _has_candidate_fields(candidate_bullets: list[str]) -> bool:
    if not candidate_bullets:
        return False
    for bullet in candidate_bullets:
        lowered = bullet.lower()
        if URL_RE.search(bullet) is None:
            return False
        if "credibility" not in lowered and "可信" not in bullet and "source quality" not in lowered:
            return False
        if "asset relevance" not in lowered and "资产" not in bullet:
            return False
        if "market / hf / ib" not in lowered and "market/hf/ib" not in lowered:
            return False
    return True


def _has_selected_relevance(selected_bullets: list[str]) -> bool:
    if not selected_bullets:
        return False
    for bullet in selected_bullets:
        lowered = bullet.lower()
        if "why it matters today" not in lowered and "为什么重要" not in bullet:
            return False
        if "market / hf / ib" not in lowered and "market/hf/ib" not in lowered:
            return False
    return True


def _has_rejected_rationale(rejected_bullets: list[str]) -> bool:
    if not rejected_bullets:
        return False
    rationale_markers = (
        "rejected because",
        "because",
        "rationale",
        "not selected",
        "剔除",
        "排除",
        "理由",
    )
    for bullet in rejected_bullets:
        lowered = bullet.lower()
        if len(bullet) < 60 or not any(marker in lowered or marker in bullet for marker in rationale_markers):
            return False
    return True


def _has_editorial_qa(show_notes: str) -> bool:
    section_body = _section_body(show_notes, "Editorial QA")
    if section_body is None:
        return False
    lowered = section_body.lower()
    return (
        ("candidate" in lowered or "候选" in section_body)
        and ("selection" in lowered or "selected" in lowered or "筛选" in section_body)
        and ("reject" in lowered or "rationale" in lowered or "排除" in section_body)
        and ("source count" in lowered or "source-count" in lowered or "来源数量" in section_body)
    )


def _has_freshness_check(show_notes: str) -> bool:
    section_body = _section_body(show_notes, "Freshness and Repetition Check")
    if section_body is None:
        return False
    lowered = section_body.lower()
    return (
        ("recent" in lowered or "近期" in section_body or "state.json" in lowered)
        and ("overlap" in lowered or "重复" in section_body or "重合" in section_body)
        and (
            "material increment" in lowered
            or "new increment" in lowered
            or "新增" in section_body
            or "增量" in section_body
        )
        and (
            "broaden" in lowered
            or "wider" in lowered
            or "拓宽" in section_body
            or "扩大" in section_body
        )
        and (
            "padding" in lowered
            or "not padded" in lowered
            or "不凑" in section_body
            or "不填充" in section_body
            or "不硬凑" in section_body
        )
    )


def _main_market_line_matches(show_notes: str, main_market_line: str) -> bool:
    declared = _declared_main_market_line(show_notes)
    if not declared:
        return False
    declared_normalized = _normalize_for_match(declared)
    expected_normalized = _normalize_for_match(main_market_line)
    if not declared_normalized or not expected_normalized:
        return False
    return (
        declared_normalized == expected_normalized
        or declared_normalized in expected_normalized
        or expected_normalized in declared_normalized
    )


def _declared_main_market_line(show_notes: str) -> str | None:
    patterns = (
        r"(?im)^\s*Main market line\s*:\s*(.+?)\s*$",
        r"(?m)^\s*主线\s*[:：]\s*(.+?)\s*$",
    )
    for pattern in patterns:
        match = re.search(pattern, show_notes)
        if match:
            return match.group(1).strip()
    return None


def _normalize_for_match(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value).lower()
