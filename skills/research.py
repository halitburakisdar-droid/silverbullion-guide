"""
SKILL: research_trending_topics
Güncel finans/gümüş trendlerini RSS + sentiment ile toplar.
Qwen'e context olarak verilir.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import requests
import feedparser
from datetime import datetime
from pathlib import Path

RESEARCH_DIR = Path(__file__).parent.parent / "research"
RESEARCH_DIR.mkdir(exist_ok=True)

RSS_FEEDS = {
    "Reuters": "https://feeds.reuters.com/reuters/businessNews",
    "ZeroHedge": "https://feeds.feedburner.com/zerohedge/feed",
    "FRED Blog": "https://fredblog.stlouisfed.org/feed/",
    "IMF Blog": "https://www.imf.org/en/News/rss",
    "Kitco": "https://www.kitco.com/rss/",
    "SilverSeek": "https://silverseek.com/rss.xml",
    "GoldSeek": "https://goldseek.com/rss.xml",
}

SILVER_KEYWORDS = [
    "silver", "gold", "precious metals", "inflation", "fed", "interest rate",
    "dollar", "commodities", "mining", "bullion", "XAG", "XAU", "COMEX",
    "recession", "debt", "treasury", "bond", "yield", "central bank",
    "solar", "semiconductor", "green energy", "industrial demand",
    "de-dollarization", "BRICS", "China", "geopolitical"
]


def fetch_trending(max_items=15) -> list:
    results = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")[:200]
                text = (title + " " + summary).lower()
                score = sum(1 for kw in SILVER_KEYWORDS if kw in text)
                if score > 0:
                    results.append({
                        "source": source,
                        "title": title,
                        "summary": summary,
                        "score": score,
                        "link": entry.get("link", "")
                    })
        except:
            pass

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_items]


def get_fear_greed() -> dict:
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = r.json()
        score = data["fear_and_greed"]["score"]
        rating = data["fear_and_greed"]["rating"]
        return {"score": round(float(score), 1), "rating": rating}
    except:
        return {"score": None, "rating": "unknown"}


def run() -> dict:
    print("Researching trending topics...")
    headlines = fetch_trending()
    fg = get_fear_greed()

    output = {
        "timestamp": datetime.now().isoformat(),
        "fear_greed": fg,
        "top_headlines": headlines,
        "context_for_llm": build_context(headlines, fg)
    }

    out_file = RESEARCH_DIR / "latest_research.json"
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Research saved: {len(headlines)} headlines, F&G: {fg['score']} ({fg['rating']})")
    return output


def build_context(headlines, fg) -> str:
    lines = []
    if fg["score"]:
        lines.append(f"Market Sentiment: {fg['score']}/100 — {fg['rating'].upper()}")
    lines.append("\nTOP TRENDING HEADLINES:")
    for h in headlines[:8]:
        lines.append(f"- {h['title']} ({h['source']})")
    return "\n".join(lines)


def get_latest_context() -> str:
    """Return cached research context for LLM."""
    f = RESEARCH_DIR / "latest_research.json"
    if f.exists():
        data = json.loads(f.read_text())
        return data.get("context_for_llm", "")
    return run()["context_for_llm"]


if __name__ == "__main__":
    result = run()
    print("\n" + result["context_for_llm"])
