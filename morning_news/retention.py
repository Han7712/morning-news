from __future__ import annotations

from datetime import date
from typing import Any


def keep_latest_episodes(episodes: list[dict[str, Any]], limit: int = 90) -> list[dict[str, Any]]:
    return sorted(episodes, key=_episode_date)[-limit:]


def _episode_date(episode: dict[str, Any]) -> date:
    return date.fromisoformat(str(episode["date"]))

