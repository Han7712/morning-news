# Morning News Content Spec

Audience: the user wants a practical daily market briefing for investment banking, hedge fund thinking, research reading, and market judgment.

Tone: buy-side morning meeting colleague. Calm, direct, source-aware, and explanatory. Do not sound like a professional announcer and do not read a written report aloud.

Schedule context: episodes are generated at 05:45 Asia/Hong_Kong so the U.S. regular equity-market close and early post-close coverage are usually available.

Length: target 10 to 11 minutes. Start with 2,500 to 3,000 Chinese characters and adjust after measuring full-script duration with `zh-CN-YunyangNeural`.

Voice: `zh-CN-YunyangNeural`.

Language: Chinese first. Use English only for market terms where Chinese is less natural, such as `risk-on`, `higher for longer`, `AI capex`, `soft landing`, `IPO`, `spread`, and `duration`. For TTS-sensitive proper nouns, write the spoken form in Chinese: `S&P 500` -> `标普五百指数`, `Dow` or `Dow Jones` -> `道琼斯指数`, `Nasdaq` -> `纳斯达克`, `Russell 2000` -> `罗素二千指数`, `Fed` -> `美联储`, `ECB` -> `欧洲央行`, `HKMA` -> `香港金管局`, `ECM` -> `股权资本市场`, `HF` -> `对冲基金`, `IB` -> `投行业务`.

Research standard:
- Search current public news and official materials from the last 24 to 48 hours.
- Start from official releases, central banks, statistical agencies, exchanges, company IR, Reuters, Bloomberg where accessible, AP, Financial Times, Wall Street Journal, CNBC, Nikkei Asia, Caixin, South China Morning Post, MarketWatch, Investing.com syndicated Reuters, and reputable regional financial outlets.
- Prefer primary sources for data releases, policy decisions, earnings, and official calendars.
- Prefer wire-quality market coverage for cross-asset reactions, deal news, oil/geopolitics, IPOs, and market closes.
- Use low-quality aggregation only for discovery, not final evidence, unless it clearly syndicates a reputable wire.

Research gate:
- Build an internal candidate list of 8 to 12 credible source-backed stories when the news flow permits.
- For every candidate, record source URL, timestamp or publication date when visible, source credibility, asset-class relevance, and market / HF / IB relevance.
- Select 2 to 4 main stories for the spoken episode.
- Record why each selected story matters today and its market / HF / IB angle.
- Record why tempting but weak stories were rejected when useful.
- Exclude minor isolated stock moves, vague opinion pieces, promotional content, and unconfirmed rumors unless market impact is clear and the uncertainty is explicit.
- Keep an `## Editorial QA` section in show notes covering candidate fields, selected-story relevance, rejected-story rationale, and source-count consistency.

Script structure:
- Do not use a fixed daily template.
- First determine the day's most important market main line.
- Use that main line to connect macro data, asset prices, company events, financing, China/Hong Kong, and Asia when relevant.
- Do not force a fixed "today's watchlist" ending.

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
