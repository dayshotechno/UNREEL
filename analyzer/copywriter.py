"""
UNREEL V3 – Copywriter Engine (Llama 3.2 / Qwen 3 via Ollama)
Generates filenames and Instagram captions for DJ video clips using a local
lightweight LLM. Runs entirely on CPU with 30+ tokens/sec.

Usage:
    from analyzer.copywriter import generate_caption, generate_filename, batch_process
"""

import json
import logging
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from analyzer.text_backends import get_text_backend

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_text_backend = None

def _get_text_backend():
    global _text_backend
    if _text_backend is None:
        _text_backend = get_text_backend()
    return _text_backend

FILENAME_PROMPT = """Generate a short, descriptive filename for a DJ video clip.
Rules:
- Max 40 characters
- lowercase with underscores only
- Format: adjective_scene_detail
- No special chars, no spaces, no numbers at start

Clip info:
- BPM: {bpm}
- Tags: {tags}
- Peak moment: {peak}
- Duration: {duration}s

Respond with ONLY the filename, nothing else. Example: dark_bassline_crowd_eruption"""

CAPTION_PROMPT = """Write an Instagram caption for a techno DJ video.
Rules:
- Max 200 characters
- Style: Hard Techno / Schranz / Underground
- Include 5-8 relevant hashtags
- Authentic, not cheesy
- Can use emojis sparingly

Clip info:
- BPM: {bpm}
- Tags: {tags}
- Scene: {scene}
- Vibe: {vibe}

Respond with ONLY the caption text, nothing else."""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CopyResult:
    filename: str
    caption: str

    def to_dict(self) -> dict:
        return {"filename": self.filename, "caption": self.caption}


# ---------------------------------------------------------------------------
# Backend interaction
# ---------------------------------------------------------------------------

def _query_llm(prompt: str, temperature: float = 0.7) -> str:
    """Send a prompt to the local text backend and return the response text."""
    try:
        return _get_text_backend().complete(prompt, temperature=temperature)
    except Exception as e:
        logger.warning(f"Text backend copywriting error: {e}")
        return ""


def _clean_filename(raw: str) -> str:
    """Sanitize a generated filename."""
    # Remove quotes, extra whitespace
    cleaned = raw.strip().strip('"\'`')
    # Replace spaces/hyphens with underscores
    cleaned = re.sub(r"[\s\-]+", "_", cleaned)
    # Remove anything that's not alphanumeric or underscore
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned.lower())
    # Truncate
    cleaned = cleaned[:40]
    # Remove trailing underscores
    cleaned = cleaned.strip("_")
    return cleaned or "unnamed_clip"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_filename(
    clip_metadata: dict,
    model: str = "",
) -> str:
    """
    Generate a descriptive filename for a DJ clip.
    
    Args:
        clip_metadata: Dict with keys like 'bpm', 'tags', 'peak', 'duration'
    
    Returns:
        Clean filename string (e.g., 'dark_bassline_crowd_eruption')
    """
    prompt = FILENAME_PROMPT.format(
        bpm=clip_metadata.get("bpm", "unknown"),
        tags=", ".join(clip_metadata.get("tags", ["techno"])),
        peak=clip_metadata.get("peak", "bass drop"),
        duration=clip_metadata.get("duration", 30),
    )

    raw = _query_llm(prompt, temperature=0.5)
    filename = _clean_filename(raw)

    if not filename or filename == "unnamed_clip":
        # Fallback: build from metadata
        bpm = clip_metadata.get("bpm", 140)
        tag = clip_metadata.get("tags", ["techno"])[0].lower()
        filename = f"techno_{tag}_{bpm}bpm"

    logger.info(f"Generated filename: {filename}")
    return filename


def generate_caption(
    clip_metadata: dict,
    style: str = "techno",
    model: str = "",
) -> str:
    """
    Generate an Instagram caption for a DJ video clip.
    
    Args:
        clip_metadata: Dict with keys like 'bpm', 'tags', 'scene', 'vibe'
        style: Style preset ('techno', 'house', 'minimal')
    
    Returns:
        Caption string with hashtags
    """
    vibe_map = {
        "techno": "dark, underground, raw energy",
        "house": "groovy, uplifting, soulful",
        "minimal": "deep, hypnotic, subtle",
    }

    prompt = CAPTION_PROMPT.format(
        bpm=clip_metadata.get("bpm", "unknown"),
        tags=", ".join(clip_metadata.get("tags", ["techno"])),
        scene=clip_metadata.get("scene", "DJ performance"),
        vibe=vibe_map.get(style, vibe_map["techno"]),
    )

    caption = _query_llm(prompt, temperature=0.8)

    if not caption:
        # Fallback caption
        caption = (
            "When the bass hits different at 2am 🔊⚡ "
            f"#techno #hardtechno #schranz #djlife #raveCulture #underground"
        )

    # Ensure it's not too long for Instagram
    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    logger.info(f"Generated caption ({len(caption)} chars)")
    return caption


def batch_process(
    clips: list[dict],
    style: str = "techno",
    model: str = "",
) -> list[CopyResult]:
    """
    Process multiple clips and generate filenames + captions.
    
    Args:
        clips: List of clip metadata dicts
        style: Caption style preset
    
    Returns:
        List of CopyResult objects
    """
    results = []

    for i, clip_meta in enumerate(clips):
        logger.info(f"Copywriting clip {i + 1}/{len(clips)}...")
        filename = generate_filename(clip_meta, model=model)
        caption = generate_caption(clip_meta, style=style, model=model)
        results.append(CopyResult(filename=filename, caption=caption))

    return results


def save_captions(results: list[CopyResult], output_path: Path) -> None:
    """Save caption results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [{"filename": r.filename, "caption": r.caption} for r in results]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(results)} captions to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.copywriter <command> [args]")
        print("  Commands: filename <bpm> <tags> | caption <bpm> <tags> | demo")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "demo":
        demo_meta = {"bpm": 145, "tags": ["CROWD_ENERGY", "DROP"], "peak": "bass drop", "duration": 30}
        print("Demo copywriting:\n")
        fn = generate_filename(demo_meta)
        cap = generate_caption(demo_meta)
        print(f"Filename: {fn}")
        print(f"Caption:  {cap}")
    elif cmd == "filename" and len(sys.argv) >= 4:
        meta = {"bpm": sys.argv[2], "tags": sys.argv[3:], "peak": "drop"}
        print(generate_filename(meta))
    elif cmd == "caption" and len(sys.argv) >= 4:
        meta = {"bpm": sys.argv[2], "tags": sys.argv[3:], "scene": "DJ set"}
        print(generate_caption(meta))
    else:
        print("Unknown command or missing args")
