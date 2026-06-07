from __future__ import annotations

import asyncio
import re
from pathlib import Path

import edge_tts

TERM_REPLACEMENTS = (
    (re.compile(r"\bS&P\s+Dow\s+Jones\s+Indices\b", re.IGNORECASE), "标普道琼斯指数公司"),
    (re.compile(r"\bS&P\s*500\b", re.IGNORECASE), "标普五百指数"),
    (re.compile(r"\bS&P\b", re.IGNORECASE), "标普"),
    (re.compile(r"\bDow\s+Jones\s+Industrial\s+Average\b", re.IGNORECASE), "道琼斯工业平均指数"),
    (re.compile(r"\bDow\s+Jones\b", re.IGNORECASE), "道琼斯指数"),
    (re.compile(r"\bDow\b", re.IGNORECASE), "道琼斯指数"),
    (re.compile(r"\bNasdaq\b", re.IGNORECASE), "纳斯达克"),
    (re.compile(r"\bRussell\s*2000\b", re.IGNORECASE), "罗素二千指数"),
    (re.compile(r"\bPHLX\b", re.IGNORECASE), "费城半导体指数"),
    (re.compile(r"\bFOMC\b", re.IGNORECASE), "美联储议息会议"),
    (re.compile(r"\bFed\s+hike\s+odds\b", re.IGNORECASE), "美联储加息概率"),
    (re.compile(r"\bFed\b", re.IGNORECASE), "美联储"),
    (re.compile(r"\bBLS\b", re.IGNORECASE), "美国劳工统计局"),
    (re.compile(r"\bAP\b", re.IGNORECASE), "美联社"),
    (re.compile(r"\bECB\b", re.IGNORECASE), "欧洲央行"),
    (re.compile(r"\bHKMA\b", re.IGNORECASE), "香港金管局"),
    (re.compile(r"\bROIC\b", re.IGNORECASE), "投入资本回报率"),
    (re.compile(r"\bECM\b", re.IGNORECASE), "股权资本市场"),
    (re.compile(r"\bHF\b", re.IGNORECASE), "对冲基金"),
    (re.compile(r"\bIB\b", re.IGNORECASE), "投行业务"),
    (re.compile(r"\bReuters-syndicated\b", re.IGNORECASE), "路透转载"),
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
