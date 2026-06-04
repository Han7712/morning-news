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

After the first script draft is complete, run it through `humanizer-zh` before TTS/build. Use `/Users/han/.agents/skills/humanizer-zh/SKILL.md` when the skill is not surfaced directly by the runtime. The show notes must include a `## Humanizer-zh Pass` section naming the skill path and summarizing the natural-language edits; the builder treats that as a required publishing gate.

## Local Commands

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/python -m pytest -q
```

## Build an Episode

Draft the script and show notes outside `docs/`, then run `tools/build_episode.py`. The builder validates script style and research quality before it writes audio, feed, metadata, and index files.

```bash
./.venv/bin/python tools/build_episode.py \
  --date 2026-06-04 \
  --slug rates-oil-ai \
  --title "Rates, Oil, and AI Capex" \
  --summary "A source-backed market morning briefing." \
  --keywords "rates,oil,AI capex" \
  --script /tmp/morning-news-2026-06-04-script.md \
  --show-notes /tmp/morning-news-2026-06-04-show-notes.md \
  --voice zh-CN-YunyangNeural \
  --rate=+0% \
  --main-market-line "Growth is resilient but oil is raising the inflation cost." \
  --source-count 9 \
  --site-url https://Han7712.github.io/morning-news
```

## Automation

The local Codex automation prompt lives at:

`/Users/han/.codex/automations/morning-news/automation.toml`

It is scheduled for daily `04:30 Asia/Hong_Kong` and requires thorough online research, candidate story QA, selected/rejected rationale, MP3/RSS publishing, tests, commit/push, and live feed verification.
