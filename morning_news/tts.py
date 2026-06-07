from __future__ import annotations

import asyncio
import re
from pathlib import Path

import edge_tts

TERM_REPLACEMENTS = (
    (re.compile(r"\bS&P\s+Dow\s+Jones\s+Indices\b", re.IGNORECASE), "标普道琼斯指数公司"),
    (re.compile(r"\bS&P\s*500\b", re.IGNORECASE), "标普500指数"),
    (re.compile(r"\bS&P\s+指数", re.IGNORECASE), "标普指数"),
    (re.compile(r"\bS&P\b", re.IGNORECASE), "标普"),
    (re.compile(r"\bDow\s+Jones\s+Industrial\s+Average\b", re.IGNORECASE), "道指"),
    (re.compile(r"\bDow\s+Jones\b", re.IGNORECASE), "道指"),
    (re.compile(r"\bDow\b", re.IGNORECASE), "道指"),
    (re.compile(r"\bHF\b", re.IGNORECASE), "hedge fund"),
)


def normalize_tts_text(text: str) -> str:
    normalized = text
    for pattern, replacement in TERM_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


async def _save_edge_tts(
    text: str,
    output_path: Path,
    voice: str,
    rate: str,
    volume: str,
    pitch: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text=normalize_tts_text(text),
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )
    await communicate.save(str(output_path))


def save_edge_tts(
    text: str,
    output_path: Path,
    voice: str,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> None:
    asyncio.run(_save_edge_tts(text, output_path, voice, rate, volume, pitch))
