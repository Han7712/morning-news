# Morning News Daily Automation Prompt

Check the current date and time in `Asia/Hong_Kong`.

Build and publish today's **Morning News** podcast episode from `/Users/han/Code/morning-news`. This workflow replaces the old PDF-facing Morning Finance Briefing delivery. Do not run the PDF delivery runner and do not present a PDF path as a user-facing output.

## Preflight

1. Run `git status --short --branch` in `/Users/han/Code/morning-news`.
2. Confirm the repo is on `main` tracking `origin/main` once a remote exists. If there are unexpected uncommitted changes, stop and report them.
3. Read `content/content_spec.md` and `content/state.json`.
4. Use `selected_voice` and `selected_rate` from `content/state.json`. Expected initial voice is `zh-CN-YunyangNeural` and rate is `+0%`.
5. Read `/Users/han/Code/codex-personal-automation/config/settings.json` for the safe local context whitelist and sensitive path keywords.
6. Do not read or mention any file whose path indicates identity documents, visas, bank statements, certificates, or other sensitive personal materials.

## Research

Perform thorough online research into the latest financial news from the last 24 to 48 hours.

Research quality requirements:

1. Prioritize high-credibility sources: official releases, central banks, statistical agencies, exchanges, company IR, Reuters, Bloomberg where accessible, AP, Financial Times, Wall Street Journal, CNBC, Nikkei Asia, Caixin, South China Morning Post, MarketWatch, Investing.com syndicated Reuters, and reputable regional financial outlets.
2. Include the U.S. market close and after-close headline scan when available at 04:30 HKT.
3. Build a candidate list of 8 to 12 credible source-backed stories when the news flow permits.
4. For each candidate story, capture source URL, timestamp or publication date when visible, source credibility, asset-class relevance, and market / HF / IB relevance.
5. Select 2 to 4 genuinely important stories for the spoken episode.
6. Reject scattered minor items, vague opinion pieces, promotional content, stale topics, low-credibility aggregations, and isolated single-stock moves unless market impact is clearly material.
7. Preserve a rejected-story rationale for tempting but excluded stories.
8. If source evidence is thin or conflicting, say so in the research notes and either exclude the story or present it with calibrated language.

## Script

Write a listening-first Chinese podcast script, not a read-aloud report.

Script requirements:

1. Target 10 to 11 minutes, roughly 2,500 to 3,000 Chinese characters.
2. Tone: buy-side morning meeting colleague, not professional announcer.
3. First determine the day's main market line, then use it to connect macro data, asset prices, company events, financing, China/Hong Kong, and Asia where relevant.
4. Do not use a fixed daily template and do not force a fixed "today's watchlist" ending.
5. Use English only for market terms where Chinese is less natural, such as `risk-on`, `higher for longer`, `AI capex`, `soft landing`, `ECM`, `IPO`, `spread`, and `duration`.
6. For company news, first explain what the company does and why markets care, then give figures.
7. Use calibrated judgment: "market may read this as", "I would first treat this as a signal", "the more important point is".
8. Avoid the correction-style sentence pattern "不是A，而是B".
9. Keep URLs out of the spoken script; preserve source links in show notes.

## Required Draft Files

Create temporary draft files outside `docs/` first:

- Podcast script: `/tmp/morning-news-YYYY-MM-DD-script.md`
- Show notes and research notes: `/tmp/morning-news-YYYY-MM-DD-show-notes.md`

The show notes must include:

- `Main market line: ...`
- `## Candidate Stories`
- `## Selected Stories`
- `## Rejected Stories`
- `## Sources`

## Build

Run `tools/build_episode.py` with the actual date, slug, title, summary, comma-separated keywords, script path, show notes path, voice, rate, main market line, source count, and site URL.

Use this command shape, preserving the attached form for rate values:

```bash
./.venv/bin/python tools/build_episode.py \
  --date YYYY-MM-DD \
  --slug <slug> \
  --title "<episode title>" \
  --summary "<short summary>" \
  --keywords "rates,oil,AI capex" \
  --script /tmp/morning-news-YYYY-MM-DD-script.md \
  --show-notes /tmp/morning-news-YYYY-MM-DD-show-notes.md \
  --voice zh-CN-YunyangNeural \
  --rate=+0% \
  --main-market-line "<main line>" \
  --source-count <number> \
  --site-url https://Han7712.github.io/morning-news
```

## Failure Behavior

If `tools/build_episode.py` fails:

1. Read `docs/reports/YYYY-MM-DD-delivery_report.json` if present.
2. Do not manually edit `docs/feed.xml`.
3. Do not publish a replacement episode as a shortcut.
4. Report the failed stage, failure message, and preserved script/show-notes paths.

## Success Behavior

1. Run `./.venv/bin/python -m pytest -q`.
2. Inspect `docs/reports/YYYY-MM-DD-delivery_report.json` and confirm `ok=true`.
3. Confirm `afinfo` can read a positive duration from the generated MP3.
4. Update `content/state.json` with `last_episode_date`, `last_slug`, recent main line, and recent slugs.
5. Commit all changed files with a concise message including the date and main topic.
6. Push to `origin main`.
7. Verify `https://Han7712.github.io/morning-news/feed.xml` returns HTTP success or report GitHub Pages propagation.
8. After HTTP success, check the feed body for the new episode title or GUID.
9. Verify the live MP3 URL returns HTTP success and expected size when available.

Finish with a concise status report naming the date, main market line, episode title, voice, duration, file size, feed URL, live verification result, commit hash, and publishing status.

