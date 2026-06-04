from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from email.utils import format_datetime
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree

from morning_news.validation import validate_metadata

ITUNES_NAMESPACE = "http://www.itunes.com/dtds/podcast-1.0.dtd"
CONTENT_NAMESPACE = "http://purl.org/rss/1.0/modules/content/"
HONG_KONG_TZ = timezone(timedelta(hours=8))
EPISODE_PUB_TIME = time(5, 45)

ElementTree.register_namespace("itunes", ITUNES_NAMESPACE)
ElementTree.register_namespace("content", CONTENT_NAMESPACE)


def build_feed_xml(
    site_url: str,
    program_title: str,
    episodes: list[dict[str, Any]],
    image_path: str | None = None,
) -> str:
    rss = ElementTree.Element("rss", {"version": "2.0"})
    channel = ElementTree.SubElement(rss, "channel")
    channel_link = _absolute_url(site_url, "")

    _add_text(channel, "title", program_title)
    _add_text(channel, "language", "zh-cn")
    _add_text(channel, "link", channel_link)
    _add_text(channel, "description", f"{program_title} podcast feed")
    _add_text(channel, _itunes_tag("author"), "Han")
    _add_text(channel, _itunes_tag("summary"), f"{program_title} podcast feed")
    _add_text(channel, _itunes_tag("explicit"), "false")
    _add_text(channel, _itunes_tag("type"), "episodic")
    category = ElementTree.SubElement(channel, _itunes_tag("category"), {"text": "Business"})
    ElementTree.SubElement(category, _itunes_tag("category"), {"text": "Investing"})
    if image_path:
        image_url = _absolute_url(site_url, image_path)
        ElementTree.SubElement(channel, _itunes_tag("image"), {"href": image_url})
        image = ElementTree.SubElement(channel, "image")
        _add_text(image, "url", image_url)
        _add_text(image, "title", program_title)
        _add_text(image, "link", channel_link)
    _add_text(channel, "lastBuildDate", format_datetime(datetime.now(timezone.utc)))

    for episode in sorted(episodes, key=_episode_date, reverse=True):
        validate_metadata(episode)
        _add_item(channel, site_url, episode)

    body = ElementTree.tostring(rss, encoding="unicode", short_empty_elements=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


def _add_item(channel: ElementTree.Element, site_url: str, episode: dict[str, Any]) -> None:
    script_url = _absolute_url(site_url, str(episode["script_path"]))
    show_notes_url = _absolute_url(site_url, str(episode["show_notes_path"]))
    audio_url = _absolute_url(site_url, str(episode["audio_path"]))
    description = f"{episode['summary']}\n\nShow notes: {show_notes_url}"

    item = ElementTree.SubElement(channel, "item")
    _add_text(item, "title", str(episode["title"]))
    _add_text(item, "description", description)
    _add_text(item, _content_tag("encoded"), description)
    _add_text(item, _itunes_tag("summary"), str(episode["summary"]))
    _add_text(item, "pubDate", format_datetime(_episode_pub_datetime(episode)))
    _add_text(item, "guid", show_notes_url, {"isPermaLink": "true"})
    _add_text(item, "link", script_url)
    ElementTree.SubElement(
        item,
        "enclosure",
        {
            "url": audio_url,
            "length": str(episode["file_size_bytes"]),
            "type": "audio/mpeg",
        },
    )
    _add_text(item, _itunes_tag("duration"), _format_duration(episode["duration_seconds"]))
    _add_text(item, _itunes_tag("keywords"), ", ".join(map(str, episode["keywords"])))


def _add_text(
    parent: ElementTree.Element,
    tag: str,
    text: str,
    attributes: dict[str, str] | None = None,
) -> ElementTree.Element:
    element = ElementTree.SubElement(parent, tag, attributes or {})
    element.text = text
    return element


def _absolute_url(site_url: str, path: str) -> str:
    base = site_url.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def _episode_date(episode: dict[str, Any]) -> date:
    return date.fromisoformat(str(episode["date"]))


def _episode_pub_datetime(episode: dict[str, Any]) -> datetime:
    return datetime.combine(_episode_date(episode), EPISODE_PUB_TIME, HONG_KONG_TZ)


def _format_duration(duration_seconds: object) -> str:
    total_seconds = int(duration_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _itunes_tag(name: str) -> str:
    return f"{{{ITUNES_NAMESPACE}}}{name}"


def _content_tag(name: str) -> str:
    return f"{{{CONTENT_NAMESPACE}}}{name}"
