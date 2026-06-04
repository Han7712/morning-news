from morning_news.retention import keep_latest_episodes


def test_keep_latest_episodes_keeps_newest_limit() -> None:
    episodes = [
        {
            "date": f"2026-06-{day:02d}",
            "title": f"Episode {day}",
        }
        for day in range(1, 11)
    ]

    kept = keep_latest_episodes(episodes, limit=3)

    assert [episode["date"] for episode in kept] == [
        "2026-06-08",
        "2026-06-09",
        "2026-06-10",
    ]


def test_keep_latest_episodes_sorts_input_before_trimming() -> None:
    episodes = [
        {"date": "2026-06-03", "title": "Three"},
        {"date": "2026-06-01", "title": "One"},
        {"date": "2026-06-02", "title": "Two"},
    ]

    kept = keep_latest_episodes(episodes, limit=2)

    assert [episode["date"] for episode in kept] == ["2026-06-02", "2026-06-03"]

