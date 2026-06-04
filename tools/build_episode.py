#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from morning_news.feed import build_feed_xml
from morning_news.retention import keep_latest_episodes
from morning_news.tts import save_edge_tts
from morning_news.validation import detect_script_violations, validate_metadata

PROGRAM_TITLE = "Morning News"
DEFAULT_SITE_URL = "https://Han7712.github.io/morning-news"
RETENTION_LIMIT = 90
DURATION_RE = re.compile(r"estimated duration:\s*([0-9]+(?:\.[0-9]+)?)\s*sec")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Morning News podcast episode.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--keywords", required=True, help="Comma separated keywords")
    parser.add_argument("--script", required=True, help="Path to podcast script markdown")
    parser.add_argument("--show-notes", required=True, help="Path to source-backed show notes markdown")
    parser.add_argument("--voice", required=True)
    parser.add_argument("--rate", default="+0%")
    parser.add_argument("--main-market-line", required=True)
    parser.add_argument("--source-count", required=True, type=int)
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL)
    return parser.parse_args()


def read_duration_seconds(path: Path) -> int:
    result = subprocess.run(
        ["afinfo", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_afinfo_duration_seconds(result.stdout)


def parse_afinfo_duration_seconds(output: str) -> int:
    match = DURATION_RE.search(output)
    if not match:
        raise ValueError("afinfo output is missing estimated duration")
    return max(1, int(float(match.group(1))))


def load_existing_metadata(metadata_dir: Path) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    for path in sorted(metadata_dir.glob("*.json")):
        episodes.append(json.loads(path.read_text(encoding="utf-8")))
    return episodes


def collect_episodes_with_metadata(
    metadata_dir: Path,
    current_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    episodes = [
        episode
        for episode in load_existing_metadata(metadata_dir)
        if episode.get("date") != current_metadata["date"]
    ]
    episodes.append(current_metadata)
    return keep_latest_episodes(episodes, RETENTION_LIMIT)


def write_index(
    site_url: str,
    episodes: list[dict[str, Any]],
    target: Path,
    cover_image_path: str | None = None,
) -> None:
    rows = []
    for episode in sorted(episodes, key=lambda item: str(item["date"]), reverse=True):
        audio_path = html.escape(str(episode["audio_path"]), quote=True)
        script_path = html.escape(str(episode["script_path"]), quote=True)
        show_notes_path = html.escape(str(episode["show_notes_path"]), quote=True)
        title = html.escape(str(episode["title"]))
        episode_date = html.escape(str(episode["date"]))
        rows.append(
            f'<li><a href="{audio_path}">{episode_date} {title}</a> '
            f'<a href="{script_path}">script</a> '
            f'<a href="{show_notes_path}">show notes</a></li>'
        )

    feed_url = html.escape(f"{site_url.rstrip('/')}/feed.xml", quote=True)
    cover_rows = []
    if cover_image_path:
        cover_src = html.escape(cover_image_path, quote=True)
        cover_rows.append(f'<p><img src="{cover_src}" alt="Morning News cover"></p>')
    html_text = "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            "<title>Morning News</title>",
            f'<link rel="alternate" type="application/rss+xml" title="Morning News" href="{feed_url}">',
            "</head>",
            "<body>",
            "<h1>Morning News</h1>",
            *cover_rows,
            f'<p><a href="{feed_url}">Podcast RSS Feed</a></p>',
            "<ol>",
            *rows,
            "</ol>",
            "</body>",
            "</html>",
            "",
        ]
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8")


def write_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))


def failure_report(date: str, stage: str, error: BaseException | str) -> dict[str, Any]:
    return {
        "ok": False,
        "date": date,
        "stage": stage,
        "error_type": type(error).__name__ if isinstance(error, BaseException) else "ValidationError",
        "message": str(error),
        "preserve_existing": getattr(error, "rollback_succeeded", True),
    }


def publish_staged_files(staged_outputs: list[tuple[Path, Path]]) -> None:
    common_root = staged_outputs[0][1].parents[1]
    with tempfile.TemporaryDirectory(
        prefix="morning-news-publish-backup-",
        dir=common_root,
    ) as backup_dir_name:
        backup_dir = Path(backup_dir_name)
        backups: list[tuple[Path, Path | None]] = []

        try:
            for index, (_staged_path, final_path) in enumerate(staged_outputs):
                final_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path = None
                if final_path.exists():
                    backup_path = backup_dir / f"{index}.bak"
                    shutil.copy2(final_path, backup_path)
                backups.append((final_path, backup_path))

            for staged_path, final_path in staged_outputs:
                os.replace(staged_path, final_path)
        except Exception as error:
            rollback_succeeded = restore_backups(backups)
            raise PublishError(error, rollback_succeeded) from error


def restore_backups(backups: list[tuple[Path, Path | None]]) -> bool:
    rollback_succeeded = True
    for final_path, backup_path in reversed(backups):
        try:
            if backup_path is None:
                if final_path.exists():
                    final_path.unlink()
            else:
                os.replace(backup_path, final_path)
        except Exception:
            rollback_succeeded = False
    return rollback_succeeded


def research_quality_from_show_notes(show_notes: str) -> dict[str, Any]:
    candidate_count = _section_bullet_count(show_notes, "Candidate Stories")
    selected_count = _section_bullet_count(show_notes, "Selected Stories")
    rejected_count = _section_bullet_count(show_notes, "Rejected Stories")
    source_links = re.findall(r"https?://\S+", show_notes)
    return {
        "candidate_count": candidate_count,
        "selected_count": selected_count,
        "has_rejected_rationale": rejected_count > 0,
        "has_credible_sources": len(source_links) >= 2,
        "humanizer_zh_passed": _has_humanizer_zh_pass(show_notes),
    }


def validate_research_notes(show_notes: str) -> list[str]:
    quality = research_quality_from_show_notes(show_notes)
    violations: list[str] = []
    if quality["candidate_count"] < 8:
        violations.append("candidate_count")
    if not 2 <= quality["selected_count"] <= 4:
        violations.append("selected_count")
    if not quality["has_rejected_rationale"]:
        violations.append("missing_rejected_rationale")
    if not quality["has_credible_sources"]:
        violations.append("missing_credible_source_links")
    if not quality["humanizer_zh_passed"]:
        violations.append("missing_humanizer_zh_pass")
    if "Main market line:" not in show_notes and "主线" not in show_notes:
        violations.append("missing_main_market_line")
    return violations


def _section_bullet_count(markdown: str, section_title: str) -> int:
    section_body = _section_body(markdown, section_title)
    if section_body is None:
        return 0
    return len(re.findall(r"^\s*[-*]\s+", section_body, flags=re.MULTILINE))


def _section_body(markdown: str, section_title: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(section_title)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    if not match:
        return None
    return match.group(1)


def _has_humanizer_zh_pass(show_notes: str) -> bool:
    section_body = _section_body(show_notes, "Humanizer-zh Pass")
    if section_body is None:
        return False
    lowered = section_body.lower()
    return "humanizer-zh" in lowered and "skill.md" in lowered


class BuildStageError(Exception):
    def __init__(self, stage: str, cause: BaseException) -> None:
        super().__init__(str(cause))
        self.stage = stage
        self.cause = cause


class PublishError(Exception):
    def __init__(self, cause: BaseException, rollback_succeeded: bool) -> None:
        super().__init__(str(cause))
        self.rollback_succeeded = rollback_succeeded


def main() -> int:
    args = parse_args()

    repo_root = Path.cwd()
    docs_dir = repo_root / "docs"
    asset_stem = f"{args.date}-{args.slug}"
    audio_path = docs_dir / "audio" / f"{asset_stem}.mp3"
    script_target = docs_dir / "scripts" / f"{asset_stem}.md"
    show_notes_target = docs_dir / "show_notes" / f"{asset_stem}.md"
    metadata_path = docs_dir / "metadata" / f"{args.date}.json"
    feed_path = docs_dir / "feed.xml"
    index_path = docs_dir / "index.html"
    cover_path = docs_dir / "cover.png"
    cover_image_path = "cover.png" if cover_path.exists() else None
    report_path = docs_dir / "reports" / f"{args.date}-delivery_report.json"

    for directory in (
        audio_path.parent,
        script_target.parent,
        show_notes_target.parent,
        metadata_path.parent,
        report_path.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    script_text = Path(args.script).read_text(encoding="utf-8")
    show_notes_text = Path(args.show_notes).read_text(encoding="utf-8")

    script_violations = detect_script_violations(script_text)
    if script_violations:
        report = failure_report(args.date, "script_validation", ", ".join(script_violations))
        report["violations"] = script_violations
        write_report(report_path, report)
        return 2

    research_violations = validate_research_notes(show_notes_text)
    if research_violations:
        report = failure_report(args.date, "research_validation", ", ".join(research_violations))
        report["violations"] = research_violations
        write_report(report_path, report)
        return 2

    with tempfile.TemporaryDirectory(prefix="morning-news-build-", dir=docs_dir) as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        staged_audio = tmp_dir / "audio" / f"{asset_stem}.mp3"
        staged_script = tmp_dir / "scripts" / f"{asset_stem}.md"
        staged_show_notes = tmp_dir / "show_notes" / f"{asset_stem}.md"
        staged_metadata = tmp_dir / "metadata" / f"{args.date}.json"
        staged_feed = tmp_dir / "feed.xml"
        staged_index = tmp_dir / "index.html"

        try:
            try:
                staged_audio.parent.mkdir(parents=True, exist_ok=True)
                save_edge_tts(script_text, staged_audio, voice=args.voice, rate=args.rate)
            except Exception as error:
                raise BuildStageError("tts", error) from error

            try:
                duration_seconds = read_duration_seconds(staged_audio)
            except Exception as error:
                raise BuildStageError("afinfo", error) from error

            metadata = {
                "date": args.date,
                "slug": args.slug,
                "title": args.title,
                "summary": args.summary,
                "keywords": [
                    item.strip() for item in args.keywords.split(",") if item.strip()
                ],
                "audio_path": f"audio/{asset_stem}.mp3",
                "script_path": f"scripts/{asset_stem}.md",
                "show_notes_path": f"show_notes/{asset_stem}.md",
                "voice": args.voice,
                "duration_seconds": duration_seconds,
                "file_size_bytes": staged_audio.stat().st_size,
                "main_market_line": args.main_market_line,
                "source_count": args.source_count,
                "research_quality": research_quality_from_show_notes(show_notes_text),
            }

            try:
                validate_metadata(metadata)
            except Exception as error:
                raise BuildStageError("metadata_validation", error) from error

            try:
                episodes = collect_episodes_with_metadata(docs_dir / "metadata", metadata)
                feed_xml = build_feed_xml(
                    args.site_url,
                    PROGRAM_TITLE,
                    episodes,
                    image_path=cover_image_path,
                )
            except Exception as error:
                raise BuildStageError("feed_generation", error) from error

            try:
                staged_script.parent.mkdir(parents=True, exist_ok=True)
                staged_script.write_text(script_text, encoding="utf-8")
                staged_show_notes.parent.mkdir(parents=True, exist_ok=True)
                staged_show_notes.write_text(show_notes_text, encoding="utf-8")
                staged_metadata.parent.mkdir(parents=True, exist_ok=True)
                staged_metadata.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                staged_feed.write_text(feed_xml, encoding="utf-8")
            except Exception as error:
                raise BuildStageError("staged_file_write", error) from error

            try:
                write_index(
                    args.site_url,
                    episodes,
                    staged_index,
                    cover_image_path=cover_image_path,
                )
            except Exception as error:
                raise BuildStageError("index_generation", error) from error

            try:
                publish_staged_files(
                    [
                        (staged_audio, audio_path),
                        (staged_script, script_target),
                        (staged_show_notes, show_notes_target),
                        (staged_metadata, metadata_path),
                        (staged_feed, feed_path),
                        (staged_index, index_path),
                    ]
                )
            except Exception as error:
                raise BuildStageError("publish", error) from error
        except BuildStageError as error:
            write_report(report_path, failure_report(args.date, error.stage, error.cause))
            return 1

    report = {
        "ok": True,
        "date": args.date,
        "audio_path": str(audio_path),
        "script_path": str(script_target),
        "show_notes_path": str(show_notes_target),
        "metadata_path": str(metadata_path),
        "feed_path": str(feed_path),
        "index_path": str(index_path),
        "duration_seconds": duration_seconds,
        "file_size_bytes": audio_path.stat().st_size,
        "voice": args.voice,
        "rate": args.rate,
        "main_market_line": args.main_market_line,
        "site_url": args.site_url,
    }
    write_report(report_path, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
