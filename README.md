# Morning News

Morning News is an independent public podcast channel for daily market morning briefings.

- Podcast title: `Morning News`
- Public site: `https://Han7712.github.io/morning-news/`
- RSS feed: `https://Han7712.github.io/morning-news/feed.xml`
- Schedule: daily at `05:45 Asia/Hong_Kong`
- Voice: `zh-CN-YunyangNeural`
- Delivery: MP3 + RSS + GitHub Pages

PDF delivery is intentionally not part of this workflow. Markdown is kept only as script, show notes, source archive, and recovery material.

## Content Shape

Each episode is a listening-first market briefing, not a read-aloud report. The tone should sound like a buy-side morning meeting colleague explaining the day's main market line.

The daily automation must perform thorough online research from credible public news and official sources, build a candidate story list, select the 2-4 stories that matter most, and preserve source links in show notes. Show notes must also include an `## Editorial QA` section covering candidate fields, selected-story relevance, rejected-story rationale, and source-count consistency.

The episode must not repeat recent topics without material new information. Before selecting stories, review `content/state.json` recent main lines and recent slugs, and skim recent show notes when needed. If nonfarm payrolls, Broadcom, AI capex, Hong Kong account scrutiny, oil supply, or any other recent theme appears again, document the new data, new price action, new policy step, new company disclosure, or new market implication. If there is no increment, reject the story or use it only as brief context. Show notes must include `## Freshness and Repetition Check`.

When high-quality financial headlines are thin, broaden the search into adjacent business-relevant areas before reusing stale material: politics, geopolitics, regulation, trade, technology policy, supply chains, energy security, credit, ECM/IPO/M&A, China/Hong Kong policy, Asia regional markets, and other international events with a credible market or business transmission channel. If the tape is still thin, use the compact duration profile instead of padding.

After the first script draft is complete, run it through `humanizer-zh` before TTS/build. Use `/Users/han/.agents/skills/humanizer-zh/SKILL.md` when the skill is not surfaced directly by the runtime. The show notes must include a `## Humanizer-zh Pass` section naming the skill path and summarizing the natural-language edits; the builder treats that as a required publishing gate.

Before TTS, the builder extracts a clean spoken body from the script archive so research notes, source URLs, headings, and markdown links are not read aloud. The generated voice track is mixed with `assets/audio/intro-bed.mp3`, with the voice fading in over the opening music bed.

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
  --duration-profile normal \
  --intro-bed assets/audio/intro-bed.mp3 \
  --site-url https://Han7712.github.io/morning-news
```

Use `--duration-profile compact` only for documented thin-news days. Compact episodes target roughly 7 to 9.5 minutes and still require the same source, freshness, humanizer, and editorial QA gates.

## Automation

The working Codex automation memory lives at:

`/Users/han/.codex/automations/morning-news-2/memory.md`

It is scheduled for daily `05:45 Asia/Hong_Kong` and requires thorough online research, freshness and repetition QA, candidate story QA, selected/rejected rationale, humanizer-zh pass, duration validation, MP3/RSS publishing, tests, commit/push, and live feed verification.
