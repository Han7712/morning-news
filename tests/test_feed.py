from xml.etree import ElementTree

from morning_news.feed import build_feed_xml


def sample_episode() -> dict[str, object]:
    return {
        "date": "2026-06-04",
        "slug": "rates-oil-ai",
        "title": "Rates, Oil, and AI Capex",
        "summary": "A source-backed market morning briefing.",
        "keywords": ["rates", "oil", "AI capex"],
        "audio_path": "audio/2026-06-04-rates-oil-ai.mp3",
        "script_path": "scripts/2026-06-04-rates-oil-ai.md",
        "show_notes_path": "show_notes/2026-06-04-rates-oil-ai.md",
        "voice": "zh-CN-YunyangNeural",
        "duration_seconds": 640,
        "file_size_bytes": 3840000,
        "main_market_line": "Growth is resilient but oil is raising the inflation cost.",
        "source_count": 9,
        "research_quality": {
            "candidate_count": 10,
            "selected_count": 3,
            "has_rejected_rationale": True,
            "has_credible_sources": True,
            "humanizer_zh_passed": True,
        },
    }


def test_build_feed_xml_contains_morning_news_channel_artwork_and_episode_links() -> None:
    xml = build_feed_xml(
        site_url="https://Han7712.github.io/morning-news/",
        program_title="Morning News",
        episodes=[sample_episode()],
        image_path="cover.png",
    )

    assert "<title>Morning News</title>" in xml
    assert 'url="https://Han7712.github.io/morning-news/audio/2026-06-04-rates-oil-ai.mp3"' in xml
    assert "https://Han7712.github.io/morning-news/scripts/2026-06-04-rates-oil-ai.md" in xml
    assert "https://Han7712.github.io/morning-news/show_notes/2026-06-04-rates-oil-ai.md" in xml
    assert "<itunes:duration>10:40</itunes:duration>" in xml

    root = ElementTree.fromstring(xml)
    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("language") == "zh-cn"
    assert channel.findtext("description") == "Morning News podcast feed"
    image = channel.find("image")
    assert image is not None
    assert image.findtext("url") == "https://Han7712.github.io/morning-news/cover.png"


def test_build_feed_xml_preserves_site_subpath_for_root_relative_paths() -> None:
    episode = sample_episode()
    episode["audio_path"] = "/audio/2026-06-04-rates-oil-ai.mp3"
    episode["script_path"] = "/scripts/2026-06-04-rates-oil-ai.md"
    episode["show_notes_path"] = "/show_notes/2026-06-04-rates-oil-ai.md"

    xml = build_feed_xml(
        site_url="https://Han7712.github.io/morning-news/",
        program_title="Morning News",
        episodes=[episode],
    )

    assert 'url="https://Han7712.github.io/morning-news/audio/2026-06-04-rates-oil-ai.mp3"' in xml
    assert "https://Han7712.github.io/morning-news/show_notes/2026-06-04-rates-oil-ai.md" in xml


def test_build_feed_xml_sorts_newest_episode_first() -> None:
    older = sample_episode()
    older["date"] = "2026-06-03"
    older["slug"] = "older"
    older["title"] = "Older Episode"
    older["audio_path"] = "audio/2026-06-03-older.mp3"
    older["script_path"] = "scripts/2026-06-03-older.md"
    older["show_notes_path"] = "show_notes/2026-06-03-older.md"

    xml = build_feed_xml(
        site_url="https://Han7712.github.io/morning-news/",
        program_title="Morning News",
        episodes=[older, sample_episode()],
    )

    root = ElementTree.fromstring(xml)
    channel = root.find("channel")
    assert channel is not None
    titles = [item.findtext("title") for item in channel.findall("item")]
    assert titles == ["Rates, Oil, and AI Capex", "Older Episode"]
