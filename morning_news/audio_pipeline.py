from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

FRONT_MATTER_RE = re.compile(r"\A---\s*\n[\s\S]*?\n---\s*\n?", re.MULTILINE)
FENCED_BLOCK_RE = re.compile(r"```[\s\S]*?```")
SPOKEN_SECTION_RE = re.compile(
    r"^##\s+(?:Spoken Script|Spoken Body|口播正文|播客正文)\s*$([\s\S]*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.IGNORECASE,
)
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
RAW_URL_RE = re.compile(r"https?://[^\s)>]+")
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
STOP_HEADINGS = {
    "sources",
    "source",
    "references",
    "research qa",
    "candidate stories",
    "selected stories",
    "rejected stories",
    "humanizer-zh pass",
    "editorial qa",
}


def extract_spoken_body(markdown: str) -> str:
    text = FRONT_MATTER_RE.sub("", markdown)
    text = FENCED_BLOCK_RE.sub("", text)
    spoken_match = SPOKEN_SECTION_RE.search(text)
    if spoken_match:
        text = spoken_match.group(1)

    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading_match = HEADING_RE.match(line)
        if heading_match:
            heading = heading_match.group(1).strip().lower()
            if heading in STOP_HEADINGS:
                break
            continue

        stripped = line.strip()
        lowered = stripped.lower()
        if (
            lowered.startswith("sources:")
            or lowered.startswith("source:")
            or stripped.startswith("来源")
            or stripped.startswith("参考来源")
        ):
            break
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = MARKDOWN_IMAGE_RE.sub(r"\1", cleaned)
    cleaned = MARKDOWN_LINK_RE.sub(r"\1", cleaned)
    cleaned = RAW_URL_RE.sub("", cleaned)
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*>\s?", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"(?m)^\s*\d+\.\s+", "", cleaned)
    return _collapse_blank_lines(cleaned)


def mix_intro_with_voice(
    voice_path: Path,
    intro_path: Path,
    output_path: Path,
    ffmpeg_path: str | None = None,
) -> None:
    if not voice_path.exists():
        raise FileNotFoundError(f"voice audio not found: {voice_path}")
    if not intro_path.exists():
        raise FileNotFoundError(f"intro bed not found: {intro_path}")

    ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    if ffmpeg is None:
        raise FileNotFoundError("ffmpeg is required for intro bed mixing")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:a]volume=0.42,afade=t=out:st=5.2:d=1.2[intro];"
        "[1:a]adelay=6700|6700[voice];"
        "[intro][voice]amix=inputs=2:duration=longest:dropout_transition=1[a]"
    )
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(intro_path),
        "-i",
        str(voice_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[a]",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output_path),
    ]
    subprocess.run(command, capture_output=True, text=True, check=True)
    if not output_path.exists():
        raise RuntimeError(f"ffmpeg did not create mixed audio: {output_path}")


def _collapse_blank_lines(text: str) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs).strip()
