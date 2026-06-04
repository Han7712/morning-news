# Morning News Podcast Design

## Objective

Build **Morning News** as a new independent public podcast channel for the user's daily market morning briefing.

The new channel replaces the old PDF-facing Morning Finance Briefing delivery. The user-facing deliverable becomes a podcast episode published through GitHub Pages and an RSS feed. Markdown remains only as internal source, show notes, source archive, and recovery material.

## Decisions Already Approved

- Podcast title: `Morning News`
- Repository name: `morning-news`
- Local repository path: `/Users/han/Code/morning-news`
- Public site URL: `https://Han7712.github.io/morning-news/`
- Public RSS feed URL: `https://Han7712.github.io/morning-news/feed.xml`
- Schedule: daily at `02:30 Asia/Hong_Kong`
- User-facing format: MP3 podcast episode through RSS/GitHub Pages
- PDF delivery: stopped, not run as the final delivery path
- Voice: `zh-CN-YunyangNeural`
- Initial voice sample selected by user: `/Users/han/.codex/automations/morning-news/voice_samples/01-yunyang-news-professional.mp3`
- Initial cover candidate generated at: `/Users/han/.codex/generated_images/019e8fd4-6f63-7a93-a8f2-e46c3996b51c/ig_014a6748e67341aa016a2195e3c76c8191bc51471d71834b8b.png`

## Product Positioning

Morning News is a daily finance and markets morning briefing podcast, not a general news show and not a finance concept lesson.

It is separate from `Daily Finance Audio`:

- `Daily Finance Audio` remains an educational finance concept podcast with a curriculum rotation.
- `Morning News` becomes a daily market briefing based on current public news and official materials.

The listener experience should feel like a buy-side morning meeting colleague leaving a concise voice note: informed, market-aware, practical, and calm.

## Content Requirements

Each episode should be built from fresh public news and official materials from the latest 24-48 hours, with a practical investment banking and hedge fund lens.

The script should not be a read-aloud report. It should be written for listening:

- Core tone: "buy-side morning meeting colleague", not professional announcer.
- Length: target 10-11 minutes.
- Script size: target 2,500-3,000 Chinese characters, adjusted after measuring real `zh-CN-YunyangNeural` duration.
- Language: Chinese first; English only for market terms where Chinese translation is less natural.
- Terms allowed when useful: `risk-on`, `higher for longer`, `AI capex`, `soft landing`, `ECM`, `IPO`, `spread`, `duration`.
- Source links: included in show notes and script archive, not spoken as URL text.

The structure must be dynamic:

1. Determine the most important market main line for the day.
2. Use that main line to connect macro data, asset prices, company events, financing, China/Hong Kong, and Asia where relevant.
3. Select 2-4 genuinely important news items for expansion.
4. Do not evenly allocate time across fixed sections when the news flow is uneven.
5. End naturally; do not force a fixed "today's watchlist" segment.

Company-news handling:

- Introduce what the company does before giving figures.
- Explain the company's industry-chain position.
- Explain why markets care about the event.
- Then give revenue, valuation, IPO, capex, or deal figures.

Judgment style:

- Prefer calibrated language: "market may read this as", "I would first treat this as a signal", "the more important point is".
- Avoid overconfident conclusions when events are still developing.
- Avoid the correction-style sentence pattern "不是A，而是B".

## Publishing Architecture

The implementation should reuse the proven Daily Finance Audio architecture where possible, while keeping Morning News as a separate repository and channel.

Expected repository layout:

```text
/Users/han/Code/morning-news/
  content/
    content_spec.md
    state.json
  morning_news/
    feed.py
    retention.py
    tts.py
    validation.py
  tools/
    build_episode.py
  docs/
    audio/
    metadata/
    scripts/
    show_notes/
    reports/
    feed.xml
    index.html
    cover.png
  tests/
```

The build tool should take a dated podcast script and publish a complete episode package:

- MP3 audio under `docs/audio/`
- Script archive under `docs/scripts/`
- Show notes/source links under `docs/show_notes/`
- Episode metadata under `docs/metadata/`
- RSS feed at `docs/feed.xml`
- Index page at `docs/index.html`
- Delivery report under `docs/reports/`

## Daily Automation Flow

The scheduled automation should:

1. Check `Asia/Hong_Kong` date and time.
2. Read Morning News content spec and state.
3. Read safe MorningBriefing context only from the existing whitelist in `/Users/han/Code/codex-personal-automation/config/settings.json`.
4. Avoid sensitive-path materials by filename/path keyword.
5. Search current public news and official materials from the last 24-48 hours.
6. Avoid obvious repetition against recent Morning News state and archived metadata.
7. Draft internal research notes with source links.
8. Convert the research notes into a listening-first podcast script.
9. Build MP3 with `zh-CN-YunyangNeural`.
10. Publish the complete episode package to `docs/`.
11. Run tests.
12. Commit and push to `origin/main`.
13. Verify the live feed returns HTTP success.
14. Verify the live feed body contains the new episode title or GUID.
15. Verify the live MP3 URL returns HTTP success and expected size.

## PDF Replacement Rules

Morning News directly replaces PDF delivery:

- Do not run `run_morning_briefing_delivery.py --pdf-mode auto` as the final delivery step.
- Do not present PDF paths in the final user-facing automation summary.
- Keep Markdown as internal script, show notes, source archive, and recovery material.
- If audio publishing fails, report the failed stage and the preserved local markdown/script paths needed for recovery.

## Verification Requirements

A successful daily run must verify:

- `tools/build_episode.py` exits successfully.
- Delivery report exists and has `ok=true`.
- MP3 exists and `afinfo` can read a positive duration.
- RSS feed XML is regenerated.
- Tests pass.
- Git commit is created.
- Push to GitHub succeeds.
- Public feed URL returns HTTP success.
- Public feed body contains the new episode title or GUID after propagation.
- Public MP3 URL returns HTTP success.

The final automation summary should name:

- Date
- Main market line
- Episode title
- Voice
- Duration
- File size
- Feed URL
- Live verification result
- Commit hash
- Publishing status

## Cover Art

The cover should be square podcast art suitable for Apple Podcasts-style clients and RSS readers.

Direction:

- Title text: `Morning News`
- Optional subtitle: `Daily Market Briefing`
- Visual theme: financial district morning, market data traces, premium professional tone
- Palette: deep navy, charcoal, white, restrained sunrise gold
- Avoid: real-company logos, Apple Podcasts logo, microphone icon, people, clutter, unreadable small text

The generated candidate image should be copied into the repository as `docs/cover.png` during implementation, unless the user selects a different cover before launch.

## Risks and Open Follow-Ups

- GitHub remote creation and first push require confirming or creating a private/public repository target; user approved public feed, so the repository can be public unless the user later says otherwise.
- Apple Podcasts directory submission is separate from RSS feed publishing. The first implementation should make the RSS feed valid and publicly reachable; directory submission can be handled after the feed works.
- `zh-CN-YunyangNeural` duration must be measured on full scripts; target script length may need adjustment after one real build.
- Public feed content can include source links and show notes, so avoid sensitive local context and never include sensitive-path-derived material.
