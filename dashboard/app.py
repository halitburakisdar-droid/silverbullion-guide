"""
SilverBullion.guide - Local Dashboard
Access at http://localhost:8888
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

BLOG_DIR = Path(__file__).parent.parent
LOG_DIR = BLOG_DIR / "logs"
STATUS_FILE = LOG_DIR / "status.json"
CONTENT_DIR = BLOG_DIR / "content/articles"
DOCS_DIR = BLOG_DIR / "docs"


def get_status():
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text())
        except:
            pass

    articles = len(list(CONTENT_DIR.glob("*.md"))) if CONTENT_DIR.exists() else 0
    built = len(list(DOCS_DIR.glob("articles/*.html"))) if DOCS_DIR.exists() else 0

    log_tail = ""
    log_file = LOG_DIR / "orchestrator.log"
    if log_file.exists():
        lines = log_file.read_text().split('\n')
        log_tail = '\n'.join(lines[-20:])

    return {
        **status,
        "articles": articles,
        "built_pages": built,
        "log_tail": log_tail,
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="60">
<title>SilverBullion.guide — Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:#0d0d1a;color:#d0d0e0;padding:1.5rem;min-height:100vh}}
h1{{font-size:1.4rem;color:#C0C0C0;margin-bottom:0.25rem}}
.sub{{color:#666;font-size:0.82rem;margin-bottom:2rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-bottom:2rem}}
.card{{background:#13132b;border:1px solid rgba(192,192,192,0.12);border-radius:10px;padding:1.25rem}}
.card-label{{font-size:0.72rem;text-transform:uppercase;letter-spacing:1.5px;color:#666;margin-bottom:0.5rem}}
.card-val{{font-size:2rem;font-weight:700;color:#C0C0C0;line-height:1}}
.card-val.green{{color:#4caf50}}
.card-val.gold{{color:#C9A84C}}
.card-sub{{font-size:0.78rem;color:#555;margin-top:0.35rem}}
.section{{background:#13132b;border:1px solid rgba(192,192,192,0.12);border-radius:10px;padding:1.25rem;margin-bottom:1rem}}
.section h2{{font-size:0.78rem;text-transform:uppercase;letter-spacing:1.5px;color:#888;margin-bottom:1rem}}
.log{{font-family:monospace;font-size:0.78rem;color:#888;white-space:pre-wrap;max-height:300px;overflow-y:auto;line-height:1.5}}
.btn{{background:#1a1a35;border:1px solid rgba(192,192,192,0.2);color:#C0C0C0;padding:0.5rem 1.25rem;border-radius:6px;cursor:pointer;font-size:0.85rem;margin-right:0.5rem;text-decoration:none;display:inline-block}}
.btn:hover{{background:#252550;border-color:#C0C0C0}}
.btn.danger{{border-color:rgba(255,80,80,0.3);color:#ff6666}}
.status-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}}
.dot-green{{background:#4caf50}}
.dot-yellow{{background:#ffc107}}
.dot-red{{background:#f44336}}
table{{width:100%;border-collapse:collapse;font-size:0.85rem}}
td,th{{padding:0.5rem 0.75rem;text-align:left;border-bottom:1px solid rgba(255,255,255,0.04)}}
th{{color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px}}
td:first-child{{color:#C0C0C0}}
.nav{{display:flex;gap:0.5rem;margin-bottom:2rem}}
</style>
</head>
<body>
<h1>◈ SilverBullion.guide</h1>
<p class="sub">Dashboard — Auto-refreshes every 60s — {now}</p>

<div class="nav">
  <a class="btn" href="?action=build" onclick="return confirm('Build site now?')">⚡ Build Site</a>
  <a class="btn" href="?action=generate" onclick="return confirm('Generate new article?')">✍ Generate Article</a>
  <a class="btn" href="?action=deploy" onclick="return confirm('Deploy to GitHub?')">🚀 Deploy</a>
  <a class="btn" href="/docs/index.html" target="_blank">🌐 Preview Site</a>
</div>

<div class="grid">
  <div class="card">
    <div class="card-label">Articles Written</div>
    <div class="card-val gold">{articles}</div>
    <div class="card-sub">of 25 planned topics</div>
  </div>
  <div class="card">
    <div class="card-label">Pages Built</div>
    <div class="card-val">{built_pages}</div>
    <div class="card-sub">HTML pages generated</div>
  </div>
  <div class="card">
    <div class="card-label">Site Status</div>
    <div class="card-val green" style="font-size:1.1rem;margin-top:0.3rem">
      <span class="status-dot dot-{build_dot}"></span>{build_status}
    </div>
    <div class="card-sub">Last: {last_build}</div>
  </div>
  <div class="card">
    <div class="card-label">SEO Issues</div>
    <div class="card-val {seo_color}">{seo_issues}</div>
    <div class="card-sub">Last check: {last_seo}</div>
  </div>
  <div class="card">
    <div class="card-label">Last Deploy</div>
    <div class="card-val" style="font-size:0.9rem;margin-top:0.5rem">{last_deploy}</div>
    <div class="card-sub">GitHub Pages</div>
  </div>
  <div class="card">
    <div class="card-label">Adsense Status</div>
    <div class="card-val" style="font-size:0.9rem;color:#ffc107;margin-top:0.5rem">Pending</div>
    <div class="card-sub">Need 10+ articles to apply</div>
  </div>
</div>

<div class="section">
  <h2>Content Pipeline</h2>
  <table>
    <tr><th>#</th><th>Title</th><th>Category</th><th>Status</th></tr>
    {article_rows}
  </table>
</div>

<div class="section">
  <h2>System Log (last 20 lines)</h2>
  <div class="log">{log_tail}</div>
</div>

</body>
</html>"""


def get_article_rows():
    from config import CONTENT_TOPICS
    rows = ""
    for i, (title, cat) in enumerate(CONTENT_TOPICS):
        import re
        slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')
        exists = (CONTENT_DIR / f"{slug}.md").exists()
        status = '<span style="color:#4caf50">✓ Done</span>' if exists else '<span style="color:#555">⏳ Queued</span>'
        rows += f"<tr><td>{i+1}</td><td>{title}</td><td>{cat}</td><td>{status}</td></tr>\n"
    return rows


def run_action(action: str):
    """Run a manual action."""
    if action == "build":
        subprocess.Popen(["python3", str(BLOG_DIR / "builder.py")], cwd=str(BLOG_DIR))
    elif action == "generate":
        subprocess.Popen(["python3", str(BLOG_DIR / "content_generator.py")], cwd=str(BLOG_DIR))
    elif action == "deploy":
        from agent.orchestrator import task_deploy
        task_deploy()


class DashHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if 'action' in params:
            action = params['action'][0]
            run_action(action)
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            return

        # Serve docs files
        if parsed.path.startswith('/docs/'):
            file_path = BLOG_DIR / parsed.path[1:]
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                ct = 'text/css' if str(file_path).endswith('.css') else \
                     'application/javascript' if str(file_path).endswith('.js') else 'text/html'
                self.send_header('Content-Type', ct + '; charset=utf-8')
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return

        s = get_status()
        html = HTML.format(
            now=s.get("now", ""),
            articles=s.get("articles", 0),
            built_pages=s.get("built_pages", 0),
            build_dot="green" if s.get("build_ok") else "red",
            build_status="Online" if s.get("build_ok") else "Building",
            last_build=s.get("last_build", "Never")[:16] if s.get("last_build") else "Never",
            seo_issues=s.get("seo_issues", "—"),
            seo_color="green" if s.get("seo_issues", 1) == 0 else "gold",
            last_seo=s.get("last_seo_check", "Never")[:16] if s.get("last_seo_check") else "Never",
            last_deploy=s.get("last_deploy", "Not yet")[:16] if s.get("last_deploy") else "Not yet",
            article_rows=get_article_rows(),
            log_tail=s.get("log_tail", "No logs yet"),
        )

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, *args):
        pass


def run():
    port = 8888
    server = HTTPServer(("127.0.0.1", port), DashHandler)
    print(f"Dashboard: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
