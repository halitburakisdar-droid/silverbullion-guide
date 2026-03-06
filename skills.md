# Agent Skills Library
## SilverBullion.guide + X Content Agent

---

## SKILL: research_trending_topics
**Trigger:** Daily at 06:00 and 18:00
**Steps:**
1. Fetch RSS feeds from major financial news sources
2. Fetch Fear & Greed Index
3. Extract top silver/gold/macro keywords
4. Score by relevance and recency
5. Return top 5 topics for content generation

**Script:** `skills/research.py`

---

## SKILL: generate_blog_article
**Trigger:** After research, 2x daily
**Steps:**
1. Take trending topic from research output
2. Check if article already exists (skip if yes)
3. Generate 1000+ word article with Qwen3.5:9b
4. Generate SEO excerpt and keywords
5. Save as markdown to content/articles/
6. Trigger site build

**Script:** `content_generator.py`

---

## SKILL: build_and_deploy
**Trigger:** After new article generated
**Steps:**
1. Run builder.py (markdown → HTML)
2. Git add docs/
3. Git commit with timestamp
4. Git push to GitHub Pages

**Script:** `builder.py` + git commands

---

## SKILL: analyze_video
**Trigger:** On demand (URL provided)
**Steps:**
1. Download video with yt-dlp
2. Check audio stream with ffprobe
3. If audio: extract MP3 → run Whisper transcription
4. If no audio: extract frames every 5s → analyze with Qwen vision
5. Generate summary and key insights
6. Save to research/video_notes/

**Script:** `skills/video_analyzer.py`

---

## SKILL: create_visual_content
**Trigger:** Weekly, for X posts
**Steps:**
1. Get trending topic from research
2. Generate quote/stat/insight with Qwen
3. Create image via Pollinations.ai (free, no API key)
4. Save to assets/images/

**Script:** `skills/image_creator.py`

---

## SKILL: x_content_post (Browser)
**Trigger:** 6x daily via scheduler
**Steps:**
1. Generate content with Qwen (tweet format)
2. Optionally attach image
3. Open X.com with saved Playwright session
4. Post tweet via browser automation

**Script:** `x_agent/poster_browser.py`

---

## SKILL: update_skills
**Trigger:** After any new workflow is established
**Steps:**
1. Document new skill in this file
2. Create or update corresponding script
3. Register in orchestrator schedule

**Script:** Manual / CEO (Claude Code)
