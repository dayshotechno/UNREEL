"""
UNREEL V3 – Vision Engine (Gemma 4 E2B Scene Tagging)
Uses a local multimodal model via Ollama to analyze video frames and assign
semantic tags for DJ event footage.

Usage:
    from analyzer.vision_engine import tag_video_frames
    tags = tag_video_frames("input/clip1.mov")
    # → [{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "..."}]
"""

import json
import logging
import base64
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import cv2
from analyzer.vision_backends import get_vision_backend

logger = logging.getLogger(__name__)

_vision_backend = None

def _get_vision_backend():
    global _vision_backend
    if _vision_backend is None:
        _vision_backend = get_vision_backend()
    return _vision_backend

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SAMPLE_INTERVAL_SEC = 5  # Sample a frame every N seconds
BATCH_SIZE = 4  # Send N frames per API call for efficiency
CONFIDENCE_THRESHOLD = 0.3

VALID_TAGS = [
    "CROWD_ENERGY",
    "DJ_SETUP",
    "LIGHT_SHOW",
    "TRANSITION",
    "BREAKDOWN",
    "BACKSTAGE",
    "ARRIVAL",
    "PACKDOWN",
    "UNUSABLE",
]

TAG_BONUS_SCORES = {
    "CROWD_ENERGY": 0.8,
    "LIGHT_SHOW": 0.5,
    "DJ_SETUP": 0.3,
    "TRANSITION": 0.1,
    "BREAKDOWN": 0.2,
    "BACKSTAGE": 0.0,
    "ARRIVAL": 0.0,    # Story-only (pov_story "before"); no highlight bonus
    "PACKDOWN": 0.0,   # Story-only (pov_story "after"); no highlight bonus
    "UNUSABLE": -1.0,
}

SYSTEM_PROMPT = """You are a professional video analyst specializing in electronic music events.
Analyze the provided DJ event frames and classify each one.

For EACH frame, provide:
- "time": the timestamp in seconds (float)
- "tag": exactly one of: CROWD_ENERGY, DJ_SETUP, LIGHT_SHOW, TRANSITION, BREAKDOWN, BACKSTAGE, ARRIVAL, PACKDOWN, UNUSABLE
- "confidence": your confidence level from 0.0 to 1.0
- "description": a brief German description (max 20 words)

Guidelines:
- CROWD_ENERGY: Audience dancing, hands up, crowd visible and active
- DJ_SETUP: Focus on DJ equipment, decks, mixer, laptop
- LIGHT_SHOW: Dominant light effects, lasers, strobes, visuals
- TRANSITION: DJ switching tracks, calm between sections
- BREAKDOWN: Musical breakdown, calmer moment, less movement
- BACKSTAGE: Behind the scenes, non-performance areas (generic, not clearly arrival/packdown)
- ARRIVAL: BEFORE the set — arriving at the venue, loading in gear, getting ready, soundcheck, empty room filling up, walking to the booth
- PACKDOWN: AFTER the set — last track ending, packing up gear, crowd leaving, empty floor, lights on, the quiet afterwards
- UNUSABLE: Blurry, too dark, pointless footage

Respond ONLY with valid JSON. No markdown fences. Format:
[{"time": 5.0, "tag": "CROWD_ENERGY", "confidence": 0.9, "description": "Crowd geht ab bei Drop"}]
"""

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FrameTag:
    time: float
    tag: str
    confidence: float
    description: str

    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "tag": self.tag,
            "confidence": self.confidence,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_sample_frames(
    video_path: str | Path,
    interval_sec: float = SAMPLE_INTERVAL_SEC,
) -> list[tuple[float, bytes]]:
    """
    Extract frames from a video at regular intervals.
    Returns list of (timestamp_seconds, jpeg_bytes).
    """
    path = str(video_path)
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        raise IOError(f"Cannot open video: {path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    interval_frames = int(fps * interval_sec)
    samples: list[tuple[float, bytes]] = []

    logger.info(f"Extracting frames from {Path(path).name} "
                f"({duration:.1f}s, every {interval_sec}s ≈ {int(duration / interval_sec)} frames)")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % interval_frames == 0:
            timestamp = frame_idx / fps
            # Encode as JPEG for smaller payload
            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            samples.append((timestamp, jpeg.tobytes()))

        frame_idx += 1

    cap.release()
    logger.info(f"  Extracted {len(samples)} sample frames")
    return samples


# ---------------------------------------------------------------------------
# API interaction
# ---------------------------------------------------------------------------

def _analyze_frames_batch(
    frames: list[tuple[float, bytes]],
    model: str = "",
) -> list[FrameTag]:
    """
    Send a batch of frames to the Ollama multimodal model for analysis.
    Uses the ollama Python library (pip install ollama).
    """
    # Build the message format
    frame_index = "\n".join(
        f"- Image {i + 1}: frame at t={timestamp:.1f}s"
        for i, (timestamp, _) in enumerate(frames)
    )
    user_text = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Analyze these {len(frames)} frames. The images are provided in this order, "
        f"use the matching timestamp as the 'time' value:\n"
        f"{frame_index}"
    )

    try:
        raw = _get_vision_backend().describe_frames(user_text, frames)
    except Exception as e:
        logger.warning(f"Vision backend API error: {e}")
        return []

    # Parse JSON from response
    try:
        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # The model may emit one JSON array per image (concatenated), a single
        # array, or a bare object. Decode every top-level JSON value and flatten.
        parsed = []
        decoder = json.JSONDecoder()
        idx, n = 0, len(cleaned)
        while idx < n:
            while idx < n and cleaned[idx] in " \t\r\n,":
                idx += 1
            if idx >= n:
                break
            try:
                value, end = decoder.raw_decode(cleaned, idx)
            except json.JSONDecodeError:
                break
            if isinstance(value, list):
                parsed.extend(value)
            elif isinstance(value, dict):
                parsed.append(value)
            idx = end

        if not parsed:
            logger.warning(f"No JSON parsed from vision response.\nRaw: {raw[:200]}")
            return []

        tags = []
        for entry in parsed:
            tag = entry.get("tag", "UNUSABLE")
            if tag not in VALID_TAGS:
                tag = "UNUSABLE"
            tags.append(FrameTag(
                time=float(entry.get("time", 0)),
                tag=tag,
                confidence=float(entry.get("confidence", 0.5)),
                description=entry.get("description", ""),
            ))
        return tags

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse vision response: {e}\nRaw: {raw[:200]}")
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tag_video_frames(
    video_path: str | Path,
    sample_interval_sec: float = SAMPLE_INTERVAL_SEC,
    model: str = "",
) -> list[FrameTag]:
    """
    Analyze a video file and return semantic tags for sampled frames.
    
    Falls back gracefully if backend is not available (returns empty list).
    """
    if not _get_vision_backend().is_available():
        logger.warning("Vision backend not available. Skipping vision tagging.")
        return []

    # Extract sample frames
    frames = extract_sample_frames(video_path, interval_sec=sample_interval_sec)
    if not frames:
        return []

    # Process in batches
    all_tags: list[FrameTag] = []
    for i in range(0, len(frames), BATCH_SIZE):
        batch = frames[i : i + BATCH_SIZE]
        logger.info(f"  Analyzing batch {i // BATCH_SIZE + 1}/{(len(frames) + BATCH_SIZE - 1) // BATCH_SIZE}...")
        tags = _analyze_frames_batch(batch, model=model)
        all_tags.extend(tags)

    _get_vision_backend().unload()
    logger.info(f"  Got {len(all_tags)} tags from vision model")
    return all_tags


def filter_unusable(tags: list[FrameTag], min_confidence: float = CONFIDENCE_THRESHOLD) -> list[FrameTag]:
    """Remove UNUSABLE tags and low-confidence entries."""
    return [t for t in tags if t.tag != "UNUSABLE" and t.confidence >= min_confidence]


def get_tag_scores(tags: list[FrameTag]) -> dict[str, float]:
    """
    Convert tags to a score dictionary for the highlight engine.
    Returns {timestamp_range_key: bonus_score}.
    """
    scores = {}
    for tag in tags:
        key = f"{tag.time:.1f}"
        scores[key] = scores.get(key, 0.0) + TAG_BONUS_SCORES.get(tag.tag, 0.0) * tag.confidence
    return scores


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m analyzer.vision_engine <video_path>")
        sys.exit(1)

    video = sys.argv[1]
    print(f"Analyzing {video}...")

    tags = tag_video_frames(video)
    for t in tags:
        print(f"  t={t.time:6.1f}s  {t.tag:15s}  conf={t.confidence:.2f}  {t.description}")

    print(f"\nFiltered (unusable removed):")
    filtered = filter_unusable(tags)
    for t in filtered:
        print(f"  t={t.time:6.1f}s  {t.tag:15s}  conf={t.confidence:.2f}")
