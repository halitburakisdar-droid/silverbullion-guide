"""
Qwen ile SEO-optimized silver blog içeriği üretici.
"""
import os
import re
import requests
import json
from datetime import datetime

from config import OLLAMA_MODEL, OLLAMA_URL, CONTENT_TOPICS, SITE

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content/articles")

SYSTEM_PROMPT = """You are an expert precious metals analyst and financial writer for SilverBullion.guide.

Write comprehensive, SEO-optimized blog articles about silver investing, precious metals markets, and related topics.

Rules:
- Write in clear, engaging English for a global audience
- Include specific data points, percentages, and facts (use realistic estimates)
- Structure with proper H2 and H3 subheadings
- No fluff — every paragraph must add value
- Target length: 800-1200 words
- Include a strong introduction that hooks the reader
- End with actionable takeaways
- Write as a knowledgeable analyst, not a salesperson
- Do NOT include a title in your output (it's handled separately)
- Start directly with the introduction paragraph"""


def generate_article(title: str, category: str) -> dict:
    slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')
    date = datetime.now().strftime("%B %d, %Y")

    prompt = f"""Write a complete blog article for this title:

Title: {title}
Category: {category}
Site: SilverBullion.guide

Requirements:
- 800-1200 words
- Use ## for H2 subheadings, ### for H3
- Include relevant data and analysis
- SEO-friendly, informative
- Strong opening hook
- Conclude with key takeaways

Generate the article body only (no title, no front matter)."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.75,
            "top_p": 0.9,
            "num_predict": 1500,
        }
    }

    res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
    res.raise_for_status()
    body = res.json()["message"]["content"].strip()

    # Generate excerpt
    excerpt_prompt = f"Write a compelling 1-2 sentence meta description (max 155 chars) for an article titled: '{title}'. Output only the description."
    payload2 = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": excerpt_prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.7, "num_predict": 80}
    }
    res2 = requests.post(f"{OLLAMA_URL}/api/chat", json=payload2, timeout=30)
    excerpt = res2.json()["message"]["content"].strip()[:155]

    # Keywords
    kw_prompt = f"List 6 SEO keywords for: '{title}'. Comma-separated, no explanation."
    payload3 = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": kw_prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.5, "num_predict": 60}
    }
    res3 = requests.post(f"{OLLAMA_URL}/api/chat", json=payload3, timeout=30)
    keywords = res3.json()["message"]["content"].strip()

    return {
        "slug": slug,
        "title": title,
        "category": category,
        "date": date,
        "excerpt": excerpt,
        "keywords": keywords,
        "content": body,
    }


def save_article(article: dict):
    os.makedirs(CONTENT_DIR, exist_ok=True)
    filepath = os.path.join(CONTENT_DIR, f"{article['slug']}.md")

    front_matter = f"""---
title: "{article['title']}"
category: "{article['category']}"
date: "{article['date']}"
excerpt: "{article['excerpt']}"
keywords: "{article['keywords']}"
---
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(front_matter + "\n" + article['content'])

    print(f"  Saved: {article['slug']}.md ({len(article['content'].split())} words)")
    return filepath


def generate_all(limit=None):
    """Generate all articles from CONTENT_TOPICS."""
    topics = CONTENT_TOPICS[:limit] if limit else CONTENT_TOPICS
    generated = []

    for i, (title, category) in enumerate(topics):
        slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')
        filepath = os.path.join(CONTENT_DIR, f"{slug}.md")

        if os.path.exists(filepath):
            print(f"  [{i+1}/{len(topics)}] Skip (exists): {title[:50]}")
            continue

        print(f"  [{i+1}/{len(topics)}] Generating: {title[:60]}...")
        try:
            article = generate_article(title, category)
            save_article(article)
            generated.append(article)
        except Exception as e:
            print(f"  Error: {e}")

    return generated


if __name__ == "__main__":
    print("Generating first 5 articles...\n")
    generate_all(limit=5)
    print("\nDone. Run builder.py to build the site.")
