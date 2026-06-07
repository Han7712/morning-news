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


def test_save_edge_tts_normalizes_market_terms_for_pronunciation(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    class FakeCommunicate:
        def __init__(self, **kwargs: object) -> None:
            calls.append(kwargs)

        async def save(self, path: str) -> None:
            Path(path).write_bytes(b"audio")

    monkeypatch.setattr(tts.edge_tts, "Communicate", FakeCommunicate)

    output = tmp_path / "voice.mp3"
    tts.save_edge_tts(
        "S&P 500 跌了，Dow 跌 695 点，S&P Dow Jones Indices 没有改规则，Fed hike odds 和 S&P 指数规则也要读清楚。",
        output,
        voice="zh-CN-YunyangNeural",
    )

    assert calls[0]["text"] == (
        "标普五百指数 跌了，道琼斯指数 跌 695 点，"
        "标普道琼斯指数公司 没有改规则，美联储加息概率 和 标普 指数规则也要读清楚。"
    )
