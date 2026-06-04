from pathlib import Path

from morning_news import tts


def test_save_edge_tts_passes_voice_rate_volume_and_pitch(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class FakeCommunicate:
        def __init__(self, **kwargs: object) -> None:
            calls.append(kwargs)

        async def save(self, path: str) -> None:
            Path(path).write_bytes(b"audio")

    monkeypatch.setattr(tts.edge_tts, "Communicate", FakeCommunicate)

    output = tmp_path / "voice.mp3"
    tts.save_edge_tts(
        "早上好",
        output,
        voice="zh-CN-YunyangNeural",
        rate="+0%",
        volume="+0%",
        pitch="+0Hz",
    )

    assert output.read_bytes() == b"audio"
    assert calls == [
        {
            "text": "早上好",
            "voice": "zh-CN-YunyangNeural",
            "rate": "+0%",
            "volume": "+0%",
            "pitch": "+0Hz",
        }
    ]

