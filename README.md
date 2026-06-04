# Morning News

Morning News is an independent public podcast channel for daily market morning briefings.

- Podcast title: `Morning News`
- Public site: `https://Han7712.github.io/morning-news/`
- RSS feed: `https://Han7712.github.io/morning-news/feed.xml`
- Schedule: daily at `04:30 Asia/Hong_Kong`
- Voice: `zh-CN-YunyangNeural`
- Delivery: MP3 + RSS + GitHub Pages

PDF delivery is intentionally not part of this workflow. Markdown is kept only as script, show notes, source archive, and recovery material.

## Content Shape

Each episode is a listening-first market briefing, not a read-aloud report. The tone should sound like a buy-side morning meeting colleague explaining the day's main market line.

The daily automation must perform thorough online research from credible public news and official sources, build a candidate story list, select the 2-4 stories that matter most, and preserve source links in show notes.

## Local Commands

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/python -m pytest -q
```
