from pathlib import Path

import pytest

from morning_news import audio_pipeline


def test_extract_spoken_body_removes_archive_sections_links_and_raw_urls() -> None:
    markdown = """---
title: Morning News
---
# Morning News

## Research QA
- Candidate: Reuters https://example.com/research

## Spoken Script
主线：今天市场在交易 growth resilience 和 oil inflation risk。

第一段会引用 [Fed statement](https://example.com/fed)，但口播不应该读出链接。
Sources: Reuters, Federal Reserve

## Sources
- Reuters: https://example.com/reuters
"""

    spoken = audio_pipeline.extract_spoken_body(markdown)

    assert "主线" in spoken
    assert "growth resilience" in spoken
    assert "Fed statement" in spoken
    assert "https://" not in spoken
    assert "Sources" not in spoken
    assert "Research QA" not in spoken
    assert "##" not in spoken


def test_extract_spoken_body_falls_back_to_markdown_body_until_sources() -> None:
    markdown = """# Morning News

主线：风险资产继续交易降息预期。

## Sources
- Reuters: https://example.com/reuters
"""

    spoken = audio_pipeline.extract_spoken_body(markdown)

    assert spoken == "主线：风险资产继续交易降息预期。"


def test_mix_intro_with_voice_invokes_ffmpeg_with_music_bed_and_voice_fade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    voice_path = tmp_path / "voice.mp3"
    intro_path = tmp_path / "intro.mp3"
    output_path = tmp_path / "mixed.mp3"
    voice_path.write_bytes(b"voice")
    intro_path.write_bytes(b"intro")
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> object:
        calls.append(cmd)
        output_path.write_bytes(b"mixed")
        return object()

    monkeypatch.setattr(audio_pipeline.shutil, "which", lambda _name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(audio_pipeline.subprocess, "run", fake_run)

    audio_pipeline.mix_intro_with_voice(voice_path, intro_path, output_path)

    assert output_path.read_bytes() == b"mixed"
    command = " ".join(calls[0])
    assert "adelay=2500|2500" in command
    assert "afade=t=in:st=2.5:d=2.5" in command
    assert "amix=inputs=2:duration=longest" in command


def test_mix_intro_with_voice_requires_existing_intro_bed(tmp_path: Path) -> None:
    voice_path = tmp_path / "voice.mp3"
    voice_path.write_bytes(b"voice")

    with pytest.raises(FileNotFoundError, match="intro bed"):
        audio_pipeline.mix_intro_with_voice(
            voice_path,
            tmp_path / "missing-intro.mp3",
            tmp_path / "mixed.mp3",
        )
