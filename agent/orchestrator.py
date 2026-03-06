"""
SilverBullion.guide - Agent Orchestrator
CEO-level coordination of all site operations.
Runs 24/7 on Mac Mini. Zero external API cost.
"""
import os
import sys
import json
import time
import schedule
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "orchestrator.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("orchestrator")

BLOG_DIR = Path(__file__).parent.parent
CONTENT_DIR = BLOG_DIR / "content/articles"
DOCS_DIR = BLOG_DIR / "docs"
STATUS_FILE = LOG_DIR / "status.json"


def update_status(key, value):
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text())
        except:
            pass
    status[key] = value
    status["last_update"] = datetime.now().isoformat()
    STATUS_FILE.write_text(json.dumps(status, indent=2))


def count_articles():
    if not CONTENT_DIR.exists():
        return 0
    return len(list(CONTENT_DIR.glob("*.md")))


def run_script(script: str, label: str) -> bool:
    log.info(f"Running: {label}")
    try:
        result = subprocess.run(
            ["python3", str(BLOG_DIR / script)],
            capture_output=True, text=True, timeout=600,
            cwd=str(BLOG_DIR)
        )
        if result.returncode == 0:
            log.info(f"OK: {label}")
            return True
        else:
            log.error(f"FAIL: {label}\n{result.stderr[:500]}")
            return False
    except Exception as e:
        log.error(f"ERROR: {label}: {e}")
        return False


# ── TASKS ──────────────────────────────────────────────

def task_generate_content():
    """Generate 1-2 new articles daily."""
    log.info("TASK: Content generation")
    count_before = count_articles()
    run_script("content_generator.py", "content generator")
    count_after = count_articles()
    new = count_after - count_before
    log.info(f"Content: +{new} articles (total: {count_after})")
    update_status("total_articles", count_after)
    update_status("last_content_run", datetime.now().isoformat())

    if new > 0:
        task_build_site()


def task_build_site():
    """Build static HTML from markdown."""
    log.info("TASK: Build site")
    ok = run_script("builder.py", "site builder")
    update_status("last_build", datetime.now().isoformat())
    update_status("build_ok", ok)

    if ok:
        task_deploy()


def task_deploy():
    """Git add, commit, push to GitHub Pages."""
    log.info("TASK: Deploy")
    try:
        docs = str(DOCS_DIR)
        subprocess.run(["git", "add", "docs/"], cwd=str(BLOG_DIR), check=True)
        msg = f"auto: update site {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(BLOG_DIR), capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout + result.stderr:
            log.info("Deploy: nothing new to commit")
            return
        subprocess.run(["git", "push"], cwd=str(BLOG_DIR), check=True)
        log.info("Deploy: pushed to GitHub Pages")
        update_status("last_deploy", datetime.now().isoformat())
    except subprocess.CalledProcessError as e:
        log.warning(f"Deploy skipped (git not configured yet): {e}")


def task_research():
    """Skill: research_trending_topics — güncel haberleri topla."""
    log.info("TASK: Research trending topics")
    try:
        from skills.research import run as research_run
        result = research_run()
        update_status("last_research", datetime.now().isoformat())
        update_status("research_headlines", len(result.get("top_headlines", [])))
        log.info(f"Research: {len(result.get('top_headlines', []))} headlines, F&G: {result.get('fear_greed', {}).get('score')}")
    except Exception as e:
        log.error(f"Research error: {e}")


def task_create_visual():
    """Skill: create_visual_content — haftalık görsel üretimi."""
    log.info("TASK: Create visual content")
    try:
        from skills.research import get_latest_context
        from skills.image_creator import create_for_topic
        import re
        context = get_latest_context()
        lines = [l for l in context.split('\n') if l.startswith('-')]
        topic = lines[0].replace('- ', '')[:80] if lines else "silver price analysis"
        path = create_for_topic(topic)
        update_status("last_visual", datetime.now().isoformat())
        log.info(f"Visual created: {path}")
    except Exception as e:
        log.error(f"Visual creation error: {e}")


def task_seo_check():
    """Basic SEO health check."""
    log.info("TASK: SEO check")
    articles = list(CONTENT_DIR.glob("*.md"))
    issues = []
    for f in articles:
        content = f.read_text(encoding='utf-8')
        if 'excerpt: ""' in content or 'excerpt: ' not in content:
            issues.append(f"Missing excerpt: {f.name}")
    update_status("seo_issues", len(issues))
    update_status("last_seo_check", datetime.now().isoformat())
    if issues:
        log.warning(f"SEO issues: {len(issues)}")


def task_update_dashboard():
    """Update dashboard metrics."""
    articles = count_articles()
    built = len(list(DOCS_DIR.glob("articles/*.html"))) if DOCS_DIR.exists() else 0
    update_status("total_articles", articles)
    update_status("built_pages", built)
    log.info(f"Dashboard: {articles} articles, {built} built pages")


# ── SCHEDULE ───────────────────────────────────────────

def setup_schedule():
    # Content: 2x per day
    schedule.every().day.at("07:00").do(task_generate_content)
    schedule.every().day.at("19:00").do(task_generate_content)

    # Build on startup and after content
    schedule.every().day.at("07:30").do(task_build_site)
    schedule.every().day.at("19:30").do(task_build_site)

    # Research: 3x daily
    schedule.every().day.at("06:00").do(task_research)
    schedule.every().day.at("12:00").do(task_research)
    schedule.every().day.at("18:00").do(task_research)

    # SEO check daily
    schedule.every().day.at("06:30").do(task_seo_check)

    # Weekly visual creation
    schedule.every().monday.at("09:00").do(task_create_visual)
    schedule.every().thursday.at("09:00").do(task_create_visual)

    # Dashboard every hour
    schedule.every().hour.do(task_update_dashboard)

    log.info("Schedule configured:")
    log.info("  06:00 / 12:00 / 18:00 — Research (trending topics)")
    log.info("  07:00 / 19:00 — Content generation (Qwen)")
    log.info("  07:30 / 19:30 — Build & deploy (GitHub Pages)")
    log.info("  06:30 — SEO check")
    log.info("  Mon & Thu 09:00 — Visual creation (Pollinations.ai)")
    log.info("  Every hour — Dashboard update")


def run():
    log.info("=" * 50)
    log.info("SilverBullion.guide Orchestrator STARTED")
    log.info("=" * 50)

    setup_schedule()
    task_update_dashboard()

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            log.info("Orchestrator stopped.")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run()
