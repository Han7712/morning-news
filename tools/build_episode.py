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
import time
import uuid
from pathlib import Path
from typing import Any

from morning_news.audio_pipeline import extract_spoken_body, mix_intro_with_voice
from morning_news.feed import build_feed_xml
from morning_news.retention import keep_latest_episodes
from morning_news.tts import save_edge_tts
from morning_news.validation import (
    detect_script_violations,
    research_quality_from_show_notes,
    validate_duration_seconds,
    validate_metadata,
    validate_research_notes,
)

PROGRAM_TITLE = "Morning News"
DEFAULT_SITE_URL = "https://Han7712.github.io/morning-news"
RETENTION_LIMIT = 90
DURATION_RE = re.compile(r"estimated duration:\s*([0-9]+(?:\.[0-9]+)?)\s*sec")
DEFAULT_INTRO_BED = "assets/audio/intro-bed.mp3"
LOCK_FILE_NAME = ".morning-news-build.lock"
LOCK_STALE_SECONDS = 2 * 60 * 60


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
    parser.add_argument("--intro-bed", default=DEFAULT_INTRO_BED)
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


class BuildLockError(Exception):
    pass


def acquire_build_lock(lock_path: Path, date: str, slug: str) -> str:
    token = str(uuid.uuid4())
    payload = {
        "token": token,
        "pid": os.getpid(),
        "date": date,
        "slug": slug,
        "created_at": int(time.time()),
    }
    while True:
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False)
                handle.write("\n")
            return token
        except FileExistsError:
            if _lock_is_stale(lock_path):
                lock_path.unlink(missing_ok=True)
                continue
            raise BuildLockError(f"active build lock exists: {lock_path}") from None


def release_build_lock(lock_path: Path, token: str) -> None:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return
    if payload.get("token") == token:
        lock_path.unlink(missing_ok=True)


def _lock_is_stale(lock_path: Path) -> bool:
    try:
        age_seconds = time.time() - lock_path.stat().st_mtime
    except FileNotFoundError:
        return True
    return age_seconds > LOCK_STALE_SECONDS


def validate_episode_identity(metadata_path: Path, slug: str) -> None:
    if not metadata_path.exists():
        return
    try:
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"existing metadata is not valid JSON: {metadata_path}") from error
    existing_slug = existing.get("slug")
    if existing_slug and existing_slug != slug:
        raise ValueError(
            f"same date already has slug {existing_slug!r}; refusing to replace with {slug!r}"
        )


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
    lock_report_path = docs_dir / "reports" / f"{args.date}-build_lock_report.json"
    lock_path = repo_root / LOCK_FILE_NAME
    intro_bed_path = Path(args.intro_bed)
    if not intro_bed_path.is_absolute():
        intro_bed_path = repo_root / intro_bed_path

    for directory in (
        audio_path.parent,
        script_target.parent,
        show_notes_target.parent,
        metadata_path.parent,
        report_path.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    try:
        lock_token = acquire_build_lock(lock_path, args.date, args.slug)
    except BuildLockError as error:
        write_report(lock_report_path, failure_report(args.date, "build_lock", error))
        return 1

    try:
        try:
            validate_episode_identity(metadata_path, args.slug)
        except Exception as error:
            write_report(report_path, failure_report(args.date, "duplicate_episode", error))
            return 2

        script_text = Path(args.script).read_text(encoding="utf-8")
        show_notes_text = Path(args.show_notes).read_text(encoding="utf-8")
        spoken_text = extract_spoken_body(script_text)

        script_violations = detect_script_violations(script_text)
        if not spoken_text:
            script_violations.append("empty_spoken_body")
        if script_violations:
            report = failure_report(
                args.date,
                "script_validation",
                ", ".join(script_violations),
            )
            report["violations"] = script_violations
            write_report(report_path, report)
            return 2

        research_violations = validate_research_notes(
            show_notes_text,
            declared_source_count=args.source_count,
            main_market_line=args.main_market_line,
        )
        if research_violations:
            report = failure_report(
                args.date,
                "research_validation",
                ", ".join(research_violations),
            )
            report["violations"] = research_violations
            write_report(report_path, report)
            return 2

        with tempfile.TemporaryDirectory(prefix="morning-news-build-", dir=docs_dir) as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            staged_voice = tmp_dir / "voice" / f"{asset_stem}-voice.mp3"
            staged_audio = tmp_dir / "audio" / f"{asset_stem}.mp3"
            staged_script = tmp_dir / "scripts" / f"{asset_stem}.md"
            staged_show_notes = tmp_dir / "show_notes" / f"{asset_stem}.md"
            staged_metadata = tmp_dir / "metadata" / f"{args.date}.json"
            staged_feed = tmp_dir / "feed.xml"
            staged_index = tmp_dir / "index.html"

            try:
                try:
                    staged_voice.parent.mkdir(parents=True, exist_ok=True)
                    save_edge_tts(spoken_text, staged_voice, voice=args.voice, rate=args.rate)
                except Exception as error:
                    raise BuildStageError("tts", error) from error

                try:
                    staged_audio.parent.mkdir(parents=True, exist_ok=True)
                    mix_intro_with_voice(staged_voice, intro_bed_path, staged_audio)
                except Exception as error:
                    raise BuildStageError("audio_mix", error) from error

                try:
                    duration_seconds = read_duration_seconds(staged_audio)
                except Exception as error:
                    raise BuildStageError("afinfo", error) from error

                try:
                    validate_duration_seconds(args.date, args.slug, duration_seconds)
                except Exception as error:
                    raise BuildStageError("duration_validation", error) from error

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
                    "research_quality": research_quality_from_show_notes(
                        show_notes_text,
                        declared_source_count=args.source_count,
                    ),
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
            "intro_bed_path": str(intro_bed_path),
            "main_market_line": args.main_market_line,
            "site_url": args.site_url,
        }
        write_report(report_path, report)
        return 0
    finally:
        release_build_lock(lock_path, lock_token)


if __name__ == "__main__":
    raise SystemExit(main())
