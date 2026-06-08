# Morning News Content Spec

Audience: the user wants a practical daily market briefing for investment banking, hedge fund thinking, research reading, and market judgment.

Tone: buy-side morning meeting colleague. Calm, direct, source-aware, and explanatory. Do not sound like a professional announcer and do not read a written report aloud.

Schedule context: episodes are generated at 05:45 Asia/Hong_Kong so the U.S. regular equity-market close and early post-close coverage are usually available.

Length: target 10 to 11 minutes on normal news-flow days. Start with 2,500 to 3,000 Chinese characters and adjust after measuring full-script duration with `zh-CN-YunyangNeural`. If fresh, material headlines are genuinely thin after a broadened search, do not pad the episode by repeating stale points. Use the compact duration profile, target roughly 7 to 9.5 minutes, and document the thin-news judgment in show notes.

Voice: `zh-CN-YunyangNeural`.

Language: Chinese first. Keep professional finance terms in the form a market professional would naturally say them, such as `risk-on`, `higher for longer`, `AI capex`, `soft landing`, `IPO`, `ECM`, `ROIC`, `ECB`, `HKMA`, `Nasdaq`, `spread`, and `duration`. For TTS-sensitive terms, use or allow the spoken form: `S&P 500` -> `标普500指数`, standalone `S&P` -> `标普`, `Dow` or `Dow Jones` -> `道指`, and `HF` -> `hedge fund`. Do not over-translate common finance acronyms.

Research standard:
- Search current public news and official materials from the last 24 to 48 hours.
- Start from official releases, central banks, statistical agencies, exchanges, company IR, Reuters, Bloomberg where accessible, AP, Financial Times, Wall Street Journal, CNBC, Nikkei Asia, Caixin, South China Morning Post, MarketWatch, Investing.com syndicated Reuters, and reputable regional financial outlets.
- Prefer primary sources for data releases, policy decisions, earnings, and official calendars.
- Prefer wire-quality market coverage for cross-asset reactions, deal news, oil/geopolitics, IPOs, and market closes.
- Use low-quality aggregation only for discovery, not final evidence, unless it clearly syndicates a reputable wire.

Research gate:
- Build an internal candidate list of 8 to 12 credible source-backed stories when the news flow permits.
- For every candidate, record source URL, timestamp or publication date when visible, source credibility, asset-class relevance, and market / HF / IB relevance.
- Before final selection, review `content/state.json` recent main lines and recent slugs, plus the latest local show notes when needed, to identify repeated themes.
- For any candidate that overlaps a recent episode theme, record the material new information, new price action, new policy step, new company disclosure, or new market implication. If there is no material increment, reject it or mention it only as brief context.
- When the market-news tape is quiet, broaden the search before repeating old material. Eligible broader topics include business, politics, geopolitics, regulation, trade, technology policy, supply chains, energy security, credit, ECM/IPO/M&A, China/Hong Kong policy, Asia regional markets, and international events with a credible market or business transmission channel.
- Select 2 to 4 main stories for the spoken episode.
- Record why each selected story matters today and its market / HF / IB angle.
- Record why tempting but weak stories were rejected when useful.
- Exclude minor isolated stock moves, vague opinion pieces, promotional content, and unconfirmed rumors unless market impact is clear and the uncertainty is explicit.
- Do not reuse a prior main line, headline pairing, or company/data combination just to fill the target duration.
- Keep an `## Editorial QA` section in show notes covering candidate fields, selected-story relevance, rejected-story rationale, and source-count consistency.
- Keep an `## Freshness and Repetition Check` section in show notes covering recent-topic review, overlap decisions, material increments for repeated themes, broadened-search categories used on quiet days, and confirmation that the script was not padded with stale material.

Script structure:
- Do not use a fixed daily template.
- First determine the day's most important market main line.
- Use that main line to connect macro data, asset prices, company events, financing, China/Hong Kong, and Asia when relevant.
- Do not force a fixed "today's watchlist" ending.
- If a prior topic remains important but has no fresh increment, say it once as context and move on. The episode should prioritize new information, changed interpretation, or a wider but still market-relevant business story.
- On thin-news days, a shorter, sharper episode is preferred over a full-length script that repeats the same nonfarm-payrolls, Broadcom, AI capex, or similar prior points without new evidence.

Humanizer pass:
- After the first script draft is complete and before TTS/build, run the script through `humanizer-zh`.
- Preferred skill source: `/Users/han/.agents/skills/humanizer-zh/SKILL.md`.
- Keep the factual claims, figures, source-backed caveats, and market logic intact.
- Revise formulaic transitions, overly symmetrical sentence structures, generic AI phrases, inflated significance language, and stiff report-style phrasing.
- Preserve a `## Humanizer-zh Pass` section in show notes that names the skill path and summarizes the edits. The builder refuses to publish if this audit section is missing.

Company-news rule:
- Introduce what the company does before giving figures.
- Explain its industry-chain position.
- Explain why markets care.
- Then give revenue, valuation, IPO, capex, or deal figures.

Judgment style:
- Prefer calibrated phrases such as "market may read this as", "I would first treat this as a signal", and "the more important point is".
- Avoid overconfident conclusions while events are still developing.
- Avoid the correction-style sentence pattern "不是A，而是B".

Source handling:
- Source links belong in show notes and script archive.
- Do not speak URLs in the episode.

Audio handling:
- TTS should receive only the clean spoken body, not headings, markdown links, research notes, or source URLs.
- The final MP3 should include the standard `assets/audio/intro-bed.mp3` music bed, with the music fading down before the voice enters at normal volume.
- Normal production episodes must pass the duration gate: target 10 to 11 minutes, with the builder allowing a 9:30 to 12:00 operational band.
