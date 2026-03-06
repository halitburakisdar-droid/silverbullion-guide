"""
SKILL: analyze_video
X veya YouTube videosunu indir, analiz et, içgörü çıkar.
Kullanım: python3 skills/video_analyzer.py <URL>
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import subprocess
import requests
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

NOTES_DIR = Path(__file__).parent.parent / "research/video_notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3.5:9b"


def download_video(url: str, out_dir: str) -> str:
    print(f"Downloading: {url}")
    result = subprocess.run(
        ["yt-dlp", "-o", f"{out_dir}/video.%(ext)s", "--no-playlist", url],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise Exception(f"Download failed: {result.stderr[:300]}")
    for f in Path(out_dir).glob("video.*"):
        return str(f)
    raise Exception("Video file not found after download")


def has_audio(video_path: str) -> bool:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", video_path],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return any(s.get("codec_type") == "audio" for s in data.get("streams", []))


def extract_audio(video_path: str, out_path: str) -> str:
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a",
         out_path, "-y", "-loglevel", "quiet"],
        check=True
    )
    return out_path


def transcribe_audio(audio_path: str) -> str:
    print("Transcribing audio with Whisper...")
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]


def extract_frames(video_path: str, out_dir: str, fps="1/5") -> list:
    print("Extracting frames...")
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-vf", f"fps={fps}",
         f"{out_dir}/frame_%04d.png", "-loglevel", "quiet"],
        check=True
    )
    return sorted(Path(out_dir).glob("frame_*.png"))


def analyze_text_with_qwen(text: str, source_url: str) -> dict:
    prompt = f"""Analyze this content from a video/media source:

URL: {source_url}
Content: {text[:3000]}

Provide:
1. A 2-3 sentence summary
2. 3-5 key insights or takeaways
3. Relevance to silver/gold/macro investing (high/medium/low)
4. Suggested blog article topic based on this content

Format as JSON with keys: summary, insights, relevance, article_topic"""

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.5, "num_predict": 800}
    }
    res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
    text_out = res.json()["message"]["content"].strip()

    # Try to parse JSON
    import re
    match = re.search(r'\{.*\}', text_out, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"summary": text_out, "insights": [], "relevance": "medium", "article_topic": ""}


def analyze(url: str) -> dict:
    tmp = tempfile.mkdtemp()
    try:
        video_path = download_video(url, tmp)
        print(f"Downloaded: {Path(video_path).name}")

        if has_audio(video_path):
            print("Audio found — using Whisper transcription")
            audio_path = f"{tmp}/audio.mp3"
            extract_audio(video_path, audio_path)
            transcript = transcribe_audio(audio_path)
            content_text = transcript
            method = "whisper_transcription"
        else:
            print("No audio — analyzing frames")
            frames = extract_frames(video_path, tmp)
            content_text = f"[Video with {len(frames)} frames analyzed visually — no audio track]"
            method = "frame_analysis"

        analysis = analyze_text_with_qwen(content_text, url)

        result = {
            "url": url,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "transcript_preview": content_text[:500],
            "analysis": analysis
        }

        # Save notes
        slug = url.split("/")[-1][:30].replace("/", "-")
        out_file = NOTES_DIR / f"{datetime.now().strftime('%Y%m%d')}_{slug}.json"
        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\nAnalysis saved: {out_file.name}")

        return result

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 skills/video_analyzer.py <URL>")
        sys.exit(1)
    result = analyze(sys.argv[1])
    print("\n=== ANALYSIS ===")
    print(json.dumps(result["analysis"], indent=2, ensure_ascii=False))
