# Morning News Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and launch the independent public Morning News podcast channel with MP3 generation, RSS publishing, research/script quality gates, GitHub Pages output, and a daily 04:30 HKT automation.

**Architecture:** This is a separate Python package and GitHub Pages repository modeled on the existing Daily Finance Audio pipeline, but with Morning News-specific content rules, show notes, research quality metadata, and a separate RSS feed. The build CLI stages all generated files, validates content and metadata, publishes with rollback, writes a delivery report, and leaves PDF delivery out of the flow.

**Tech Stack:** Python 3.11+, pytest, edge-tts, GitHub Pages static `/docs` output, RSS 2.0 with iTunes podcast tags, macOS `afinfo` for MP3 duration verification.

---

### Task 1: Project Scaffold and Content Contract

**Files:**
- Create: `/Users/han/Code/morning-news/pyproject.toml`
- Create: `/Users/han/Code/morning-news/.gitignore`
- Create: `/Users/han/Code/morning-news/README.md`
- Create: `/Users/han/Code/morning-news/content/content_spec.md`
- Create: `/Users/han/Code/morning-news/content/state.json`
- Create: `/Users/han/Code/morning-news/morning_news/__init__.py`
- Create directories under `/Users/han/Code/morning-news/docs/`
- Copy cover candidate to `/Users/han/Code/morning-news/docs/cover.png`

- [ ] **Step 1: Create scaffold files**

Create the Python package, content contract, state file, docs output directories, and cover asset. The content spec must include 04:30 HKT, `zh-CN-YunyangNeural`, 10-11 minute target, 2,500-3,000 Chinese character target, high-quality online research, dynamic structure, and no PDF delivery.

- [ ] **Step 2: Verify package metadata**

Run: `python3 -m pip install -e .`

Expected: package installs successfully or reports missing dependencies that can be added to `pyproject.toml`.

- [ ] **Step 3: Commit scaffold**

Run:

```bash
git add .gitignore README.md pyproject.toml content morning_news docs
git commit -m "Scaffold Morning News podcast project"
```

### Task 2: Core Podcast Modules with Tests

**Files:**
- Create: `/Users/han/Code/morning-news/tests/test_feed.py`
- Create: `/Users/han/Code/morning-news/tests/test_validation.py`
- Create: `/Users/han/Code/morning-news/tests/test_retention.py`
- Create: `/Users/han/Code/morning-news/tests/test_tts.py`
- Create: `/Users/han/Code/morning-news/morning_news/feed.py`
- Create: `/Users/han/Code/morning-news/morning_news/validation.py`
- Create: `/Users/han/Code/morning-news/morning_news/retention.py`
- Create: `/Users/han/Code/morning-news/morning_news/tts.py`

- [ ] **Step 1: Write failing tests**

Tests must cover:

- RSS feed includes channel title `Morning News`, cover image, enclosure, script/show-notes links, iTunes duration, and preserves GitHub Pages subpath.
- Metadata validation requires date, slug, title, summary, keywords, audio path, script path, show notes path, voice, duration, file size, main market line, source count, and research quality fields.
- Script validation blocks dash-break punctuation, the banned correction pattern, missing source markers, missing main market line, and too-short scripts.
- Retention keeps the newest 90 episodes.
- TTS wrapper calls EdgeTTS with voice/rate parameters.

- [ ] **Step 2: Run tests and confirm red**

Run: `python3 -m pytest -q`

Expected: tests fail because the modules do not exist yet.

- [ ] **Step 3: Implement modules**

Implement minimal reusable modules:

- `feed.py`: RSS 2.0 + iTunes tags, HK 04:30 publish time, absolute URL handling.
- `validation.py`: metadata validation and content quality helpers.
- `retention.py`: newest-N retention.
- `tts.py`: EdgeTTS MP3 writer.

- [ ] **Step 4: Run tests and confirm green**

Run: `python3 -m pytest -q`

Expected: tests pass.

- [ ] **Step 5: Commit modules**

Run:

```bash
git add morning_news tests
git commit -m "Add Morning News podcast core"
```

### Task 3: Build Episode CLI with Show Notes and Rollback

**Files:**
- Create: `/Users/han/Code/morning-news/tools/build_episode.py`
- Create: `/Users/han/Code/morning-news/tests/test_build_episode.py`

- [ ] **Step 1: Write failing build tests**

Tests must cover:

- Successful build stages MP3, script, show notes, metadata, feed, index, and report.
- Failure during style/research validation writes a failure report and preserves existing feed/audio.
- Failure during TTS or duration read writes a failure report and preserves existing artifacts.
- Same-date rerun replaces all output files consistently.
- Negative `--rate=-5%` style argument is accepted.

- [ ] **Step 2: Run tests and confirm red**

Run: `python3 -m pytest tests/test_build_episode.py -q`

Expected: tests fail because `tools/build_episode.py` does not exist.

- [ ] **Step 3: Implement build CLI**

Implement CLI arguments:

```text
--date
--slug
--title
--summary
--keywords
--script
--show-notes
--voice
--rate
--main-market-line
--source-count
--site-url
```

The CLI should publish:

- `docs/audio/YYYY-MM-DD-slug.mp3`
- `docs/scripts/YYYY-MM-DD-slug.md`
- `docs/show_notes/YYYY-MM-DD-slug.md`
- `docs/metadata/YYYY-MM-DD.json`
- `docs/feed.xml`
- `docs/index.html`
- `docs/reports/YYYY-MM-DD-delivery_report.json`

- [ ] **Step 4: Run tests and confirm green**

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit build CLI**

Run:

```bash
git add tools tests morning_news
git commit -m "Add Morning News episode builder"
```

### Task 4: Automation Prompt, Memory, and Local Run Script

**Files:**
- Create: `/Users/han/.codex/automations/morning-news/automation.toml`
- Create: `/Users/han/.codex/automations/morning-news/memory.md`
- Create: `/Users/han/Code/morning-news/tools/draft_prompt.md`
- Update: `/Users/han/Code/morning-news/README.md`

- [ ] **Step 1: Create automation prompt assets**

Create an automation prompt that requires:

- HK time check.
- Daily `04:30 Asia/Hong_Kong` run.
- Thorough online research from credible public and official sources.
- 8-12 candidate story list when possible.
- Selected and rejected story rationale.
- 2-4 spoken main stories.
- Dynamic main line.
- Script quality check before TTS.
- `zh-CN-YunyangNeural`.
- No PDF delivery.
- Build, tests, commit, push, live feed body check, live MP3 check.

- [ ] **Step 2: Create local automation files**

Create `/Users/han/.codex/automations/morning-news/automation.toml` with status active and RRULE daily at 04:30 HKT.

- [ ] **Step 3: Commit repo prompt docs**

Run:

```bash
git add README.md tools/draft_prompt.md
git commit -m "Document Morning News automation workflow"
```

### Task 5: Launch Repository and Verify

**Files:**
- Remote: GitHub repository `Han7712/morning-news`

- [ ] **Step 1: Run full tests**

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Verify cover and sample assets**

Run:

```bash
test -s docs/cover.png
file docs/cover.png
```

Expected: `docs/cover.png` exists and is a PNG image.

- [ ] **Step 3: Create public GitHub repository if needed**

Use `gh repo view Han7712/morning-news` to check whether it exists. If missing, create it public with `gh repo create Han7712/morning-news --public --source=. --remote=origin --push`.

- [ ] **Step 4: Push current branch**

Run:

```bash
git push -u origin main
```

Expected: push succeeds.

- [ ] **Step 5: Verify repository status**

Run:

```bash
git status --short --branch
git remote -v
```

Expected: clean `main` branch tracking `origin/main`.

### Task 6: Completion Verification

**Files:**
- Repository and automation files created above.

- [ ] **Step 1: Run final verification**

Run:

```bash
python3 -m pytest -q
git status --short --branch
test -f /Users/han/.codex/automations/morning-news/automation.toml
test -f /Users/han/.codex/automations/morning-news/memory.md
```

Expected: tests pass, repository clean, automation files exist.

- [ ] **Step 2: Report remaining launch caveat**

If GitHub Pages is not yet enabled for `/docs`, report that as the remaining manual/GitHub-side setup step. If the repo creation/push succeeds but Pages is not live immediately, report propagation status rather than claiming playback is live.
