"""
Static site builder: Markdown content → HTML pages
"""
import os
import re
import json
import shutil
from datetime import datetime

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content/articles")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs")
STATIC_SRC = os.path.join(os.path.dirname(__file__), "static")
STATIC_DST = os.path.join(OUTPUT_DIR, "static")

from config import SITE, CATEGORIES

ICONS = {
    "investment": "📈",
    "analysis": "🔍",
    "beginners": "📚",
    "news": "📰",
    "vs": "⚖️",
    "history": "🏛️",
}


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text


def md_to_html(md):
    """Basic markdown to HTML converter."""
    html = md
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    # Bold / italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    # Blockquote
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    # Unordered lists
    def convert_ul(m):
        items = re.findall(r'^[-*] (.+)$', m.group(0), re.MULTILINE)
        lis = ''.join(f'<li>{i}</li>' for i in items)
        return f'<ul>{lis}</ul>'
    html = re.sub(r'(^[-*] .+$\n?)+', convert_ul, html, flags=re.MULTILINE)
    # Ordered lists
    def convert_ol(m):
        items = re.findall(r'^\d+\. (.+)$', m.group(0), re.MULTILINE)
        lis = ''.join(f'<li>{i}</li>' for i in items)
        return f'<ol>{lis}</ol>'
    html = re.sub(r'(^\d+\. .+$\n?)+', convert_ol, html, flags=re.MULTILINE)
    # Paragraphs
    blocks = html.split('\n\n')
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith('<h') or block.startswith('<ul') or block.startswith('<ol') or block.startswith('<blockquote'):
            result.append(block)
        else:
            result.append(f'<p>{block}</p>')
    return '\n'.join(result)


def read_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    # Parse front matter
    meta = {}
    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    k, v = line.split(':', 1)
                    meta[k.strip()] = v.strip().strip('"')
            raw = parts[2].strip()
    meta['content'] = raw
    return meta


def build_sidebar(active_slug=None):
    # Collect recent articles
    articles = []
    for f in sorted(os.listdir(CONTENT_DIR), reverse=True)[:6]:
        if f.endswith('.md'):
            try:
                a = read_article(os.path.join(CONTENT_DIR, f))
                a['slug'] = f.replace('.md', '')
                articles.append(a)
            except:
                pass

    recent_links = ''.join(
        f'<li><a href="/articles/{a["slug"]}.html">{a.get("title","")}</a>'
        f'<span>{a.get("category","").title()} · {a.get("date","")}</span></li>'
        for a in articles if a.get('slug') != active_slug
    )

    cat_links = ''.join(
        f'<li><a href="/category-{slug}.html">{name}</a></li>'
        for slug, name in CATEGORIES.items()
    )

    return f"""
    <div class="sidebar-widget price-widget">
      <div class="widget-title">Live Silver Prices</div>
      <div class="price-row">
        <span class="price-label">Silver (XAG/USD)</span>
        <span><span class="price-val" id="ag-usd">Loading...</span> <span class="price-change up" id="ag-chg"></span></span>
      </div>
      <div class="price-row">
        <span class="price-label">Gold (XAU/USD)</span>
        <span><span class="price-val" id="au-usd">Loading...</span></span>
      </div>
      <div class="price-row">
        <span class="price-label">Gold/Silver Ratio</span>
        <span><span class="price-val" id="gsr">Loading...</span></span>
      </div>
      <p style="font-size:0.72rem;color:#555;margin-top:0.75rem;font-family:sans-serif">Prices are indicative. Delayed data.</p>
    </div>

    <div class="ad-slot">Advertisement</div>

    <div class="sidebar-widget">
      <div class="widget-title">Recent Articles</div>
      <ul class="popular-list">{recent_links}</ul>
    </div>

    <div class="sidebar-widget">
      <div class="widget-title">Categories</div>
      <ul class="popular-list">{cat_links}</ul>
    </div>

    <div class="ad-slot">Advertisement</div>
    """


def build_html(title, description, keywords, body, root="", canonical=""):
    with open(os.path.join(os.path.dirname(__file__), "templates/base.html")) as f:
        base = f.read()
    return base.format(
        title=title,
        description=description,
        keywords=keywords,
        body=body,
        root=root,
        canonical=canonical,
    )


def build_article_page(meta, slug):
    content_html = md_to_html(meta.get('content', ''))
    category = meta.get('category', 'analysis')
    category_name = CATEGORIES.get(category, category.title())
    icon = ICONS.get(category, '📄')

    words = len(meta.get('content', '').split())
    read_time = max(1, words // 200)

    sidebar = build_sidebar(active_slug=slug)

    body = f"""
<div class="breadcrumb">
  <a href="/">Home</a><span>›</span>
  <a href="/category-{category}.html">{category_name}</a><span>›</span>
  {meta.get('title','')}
</div>
<div class="article-wrap">
  <article>
    <div class="article-header">
      <span class="card-tag">{category_name}</span>
      <h1>{meta.get('title','')}</h1>
      <p class="excerpt">{meta.get('excerpt','')}</p>
      <div class="article-meta">
        <span>📅 {meta.get('date', datetime.now().strftime('%B %d, %Y'))}</span>
        <span>⏱ {read_time} min read</span>
        <span>✍ {SITE['author']}</span>
      </div>
    </div>

    <div class="ad-slot" style="min-height:90px"><!-- AdSense: Leaderboard --></div>

    <div class="article-body">{content_html}</div>

    <div class="ad-slot" style="min-height:250px"><!-- AdSense: Rectangle --></div>

    <div class="disclaimer">
      <strong>Disclaimer:</strong> The information provided on this site is for educational purposes only and does not constitute financial advice. Always conduct your own research before making investment decisions.
    </div>
  </article>
  <aside class="sidebar">{sidebar}</aside>
</div>
<script src="/static/js/prices.js"></script>
"""
    return build_html(
        title=meta.get('title', ''),
        description=meta.get('excerpt', '')[:160],
        keywords=meta.get('keywords', f"silver, {category}, precious metals, investment"),
        body=body,
        root="/",
        canonical=f"articles/{slug}.html",
    )


def build_index(articles):
    featured = articles[0] if articles else None
    rest = articles[1:]

    featured_html = ""
    if featured:
        icon = ICONS.get(featured.get('category', ''), '📄')
        category_name = CATEGORIES.get(featured.get('category', ''), 'Analysis')
        featured_html = f"""
        <div class="section-title">Featured Article</div>
        <a href="/articles/{featured['slug']}.html" style="display:block;margin-bottom:2rem">
          <div class="featured-card">
            <div class="featured-card-img">{icon}</div>
            <div class="featured-card-body">
              <span class="card-tag">{category_name}</span>
              <h2>{featured.get('title','')}</h2>
              <p>{featured.get('excerpt','')}</p>
              <div class="card-meta">
                <span>📅 {featured.get('date','')}</span>
                <span>⏱ {max(1, len(featured.get('content','').split())//200)} min read</span>
              </div>
            </div>
          </div>
        </a>
        """

    cards = ""
    for a in rest:
        icon = ICONS.get(a.get('category', ''), '📄')
        cat_name = CATEGORIES.get(a.get('category', ''), 'Analysis')
        read_time = max(1, len(a.get('content', '').split()) // 200)
        cards += f"""
        <a href="/articles/{a['slug']}.html" style="display:block">
          <div class="article-card">
            <div>
              <span class="card-tag">{cat_name}</span>
              <h2>{a.get('title','')}</h2>
              <p>{a.get('excerpt','')}</p>
              <div class="card-meta">
                <span>📅 {a.get('date','')}</span>
                <span>⏱ {read_time} min read</span>
              </div>
            </div>
            <div class="article-card-icon">{icon}</div>
          </div>
        </a>
        """

    sidebar = build_sidebar()

    body = f"""
<div class="hero">
  <div class="hero-label">Precious Metals Intelligence</div>
  <h1>Your Complete Guide to<br><span class="highlight">Silver Investing</span></h1>
  <p>Expert analysis, price forecasts, and investment strategies for silver and precious metals investors worldwide.</p>
</div>
<div class="ticker-wrap">
  <div class="ticker" id="ticker">
    <span class="ticker-item"><strong>XAG/USD</strong> <span id="t-ag">—</span></span>
    <span class="ticker-item"><strong>XAU/USD</strong> <span id="t-au">—</span></span>
    <span class="ticker-item"><strong>Gold/Silver Ratio</strong> <span id="t-gsr">—</span></span>
    <span class="ticker-item"><strong>DXY</strong> ~104</span>
    <span class="ticker-item">Silver investing guides · Analysis · Price forecasts</span>
    <span class="ticker-item"><strong>XAG/USD</strong> <span id="t-ag2">—</span></span>
    <span class="ticker-item"><strong>XAU/USD</strong> <span id="t-au2">—</span></span>
    <span class="ticker-item"><strong>Gold/Silver Ratio</strong> <span id="t-gsr2">—</span></span>
  </div>
</div>
<div class="container">
  <main>
    {featured_html}
    <div class="section-title">Latest Articles</div>
    <div class="articles-list">
      <div class="ad-slot" style="min-height:90px"><!-- AdSense --></div>
      {cards}
    </div>
  </main>
  <aside class="sidebar">{sidebar}</aside>
</div>
<script src="/static/js/prices.js"></script>
"""
    return build_html(
        title=SITE['tagline'],
        description=SITE['description'],
        keywords="silver investing, silver price, precious metals, silver forecast, buy silver",
        body=body,
        root="/",
        canonical="",
    )


def build_all():
    # Copy static files
    if os.path.exists(STATIC_DST):
        shutil.rmtree(STATIC_DST)
    shutil.copytree(STATIC_SRC, STATIC_DST)

    # Read all articles
    articles = []
    os.makedirs(CONTENT_DIR, exist_ok=True)
    for f in sorted(os.listdir(CONTENT_DIR), reverse=True):
        if f.endswith('.md'):
            try:
                meta = read_article(os.path.join(CONTENT_DIR, f))
                meta['slug'] = f.replace('.md', '')
                articles.append(meta)
            except Exception as e:
                print(f"  Skip {f}: {e}")

    print(f"Building {len(articles)} articles...")

    # Build article pages
    os.makedirs(os.path.join(OUTPUT_DIR, "articles"), exist_ok=True)
    for meta in articles:
        html = build_article_page(meta, meta['slug'])
        out = os.path.join(OUTPUT_DIR, "articles", f"{meta['slug']}.html")
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)

    # Build index
    index_html = build_index(articles)
    with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)

    print(f"Site built → {OUTPUT_DIR}/")
    print(f"  {len(articles)} articles + index")


if __name__ == "__main__":
    build_all()
