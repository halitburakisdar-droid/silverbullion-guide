"""
SKILL: create_visual_content
Trend konular için görsel oluşturur.
Pollinations.ai kullanır — ücretsiz, API key gerekmez.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
import urllib.parse
from pathlib import Path
from datetime import datetime

IMAGES_DIR = Path(__file__).parent.parent / "assets/images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3.5:9b"


def generate_image_prompt(topic: str) -> str:
    """Qwen ile görsel prompt üret."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": f"""Create a short image generation prompt for this financial/silver investing topic:
Topic: {topic}

Requirements:
- Professional, clean infographic style
- Dark background with silver and gold tones
- No text in image
- Suitable for financial blog
- 10-15 words max

Output only the prompt, nothing else."""}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.7, "num_predict": 60}
    }
    res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=30)
    return res.json()["message"]["content"].strip()


def create_image(prompt: str, filename: str = None) -> str:
    """Pollinations.ai ile görsel oluştur (ücretsiz)."""
    full_prompt = f"{prompt}, professional financial infographic, dark background, silver gold colors, high quality"
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=630&nologo=true"

    print(f"Generating image: {prompt[:60]}...")
    res = requests.get(url, timeout=60)
    res.raise_for_status()

    if not filename:
        filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

    out_path = IMAGES_DIR / filename
    out_path.write_bytes(res.content)
    print(f"Image saved: {out_path}")
    return str(out_path)


def create_for_topic(topic: str) -> str:
    """Konu için otomatik görsel üret."""
    img_prompt = generate_image_prompt(topic)
    slug = topic.lower().replace(" ", "-")[:40]
    filename = f"{datetime.now().strftime('%Y%m%d')}_{slug}.jpg"
    return create_image(img_prompt, filename)


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "silver price forecast 2025"
    path = create_for_topic(topic)
    print(f"Done: {path}")
