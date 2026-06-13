"""
UNREEL V3 – Main CLI Entry Point (Orchestrator)
Orchestrates the full DJ video pipeline: ingest → sync → analyze → regie → export.
Supports multi-provider AI regie (Claude, Gemini, DeepSeek).

Usage:
    python -m src.main --input ./input --preset highlight --duration 60
    python -m src.main --input ./input --preset seamless_loop --duration 30
    python -m src.main --input ./input --provider gemini --phase regie
    python -m src.main --input ./input --provider deepseek --multi
    python -m src.main --input ./input --phase sync        # Run only Phase 1
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add project root to path for imports (V3 modules live at the repo root)
# src/main.py is in src/, so root is parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    INPUT_DIR, OUTPUT_DIR, LUT_DIR, DEFAULT_LUT,
    SAMPLE_RATE, COPYWRITER_MODEL, GEMMA_MODEL,
    REGIE_PROVIDER, REEL_FPS,
)
from lut_generator import generate_all_luts, get_lut_path
from audio_sync import sync_all_clips
from kick_snare_detector import detect_kicks_snares, get_beat_grid
from analyzer.vision_engine import tag_video_frames, filter_unusable
from analyzer.copywriter import generate_caption, generate_filename, batch_process, save_captions
from regie_engine import (
    generate_edit_plan,
    generate_multi_plan,
    create_seamless_loop_plan,
    list_available_providers,
)
from ingest import ingest_directory

logger = logging.getLogger("unreel")


# ---------------------------------------------------------------------------
# Pipeline Phases
# ---------------------------------------------------------------------------

def phase_ingest(input_dir):
    """Phase 0: Duplikate entfernen + nach UNREEL_<timestamp> umbenennen."""
    logger.info("Phase 0: Ingestion & Renaming")
    result = ingest_directory(input_dir)
    return [Path(p) for p in result.final_files]


def phase_0_setup():
    """Phase 0: Generate LUTs if they don't exist."""
    logger.info("=" * 60)
    logger.info("PHASE 0: Setup – Generating LUTs")
    logger.info("=" * 60)

    luts = generate_all_luts()
    for name, path in luts.items():
        logger.info(f"  ✓ {name}: {path}")
    return luts


def phase_1_sync(video_paths: list[Path]) -> dict:
    """Phase 1: Audio Cross-Correlation Sync + Kick/Snare Detection."""
    logger.info("=" * 60)
    logger.info("PHASE 1: Audio Sync & Percussion Detection")
    logger.info("=" * 60)

    result = {}

    # Audio sync (only if multiple clips)
    if len(video_paths) >= 2:
        sync_result = sync_all_clips(
            [str(p) for p in video_paths],
            sr=SAMPLE_RATE,
            output_path=OUTPUT_DIR / "audio_sync.json",
        )
        result["sync"] = sync_result.to_dict()
        ref_path = sync_result.reference_clip
    else:
        ref_path = str(video_paths[0])
        result["sync"] = {"reference_clip": ref_path, "offsets": {ref_path: 0.0}}

    # Kick/Snare detection on reference clip
    logger.info("\nDetecting kicks & snares on reference clip...")
    percussion = detect_kicks_snares(ref_path, sr=SAMPLE_RATE)
    percussion.save(OUTPUT_DIR / "percussion_map.json")
    result["percussion"] = percussion.to_dict()
    result["beat_grid"] = get_beat_grid(percussion)

    logger.info(f"\n  Reference: {Path(ref_path).name}")
    logger.info(f"  BPM: {percussion.bpm:.1f}")
    logger.info(f"  Kicks: {len(percussion.kicks)}")
    logger.info(f"  Snares: {len(percussion.snares)}")

    return result


def _video_signature(video_path: str) -> list[int | None] | None:
    """
    Cheap visual signature: dHash of five frames spread across the clip.
    Used to detect near-duplicate clips before the expensive vision tagging.
    Five positions (not three) so that mostly-dark club footage still yields
    enough informative (non-uniform) frames for a confident comparison.
    None if the duration can't be probed.
    """
    from analyzer.frame_hasher import dhash
    duration = _probe_duration(Path(video_path))
    if duration <= 0:
        return None
    return [dhash(video_path, duration * f) for f in (0.15, 0.35, 0.5, 0.65, 0.85)]


def _find_visual_twin(sig: list, known_sigs: dict[str, list]) -> str | None:
    """
    Return the path of an already-tagged clip that is visually near-identical
    to `sig`, or None. Conservative: ALL comparable frame positions must be
    within the hamming threshold, and at least two must be comparable —
    false positives would propagate wrong tags into the edit plan.

    Calibrated on real footage: re-encoded duplicates differ by <=7 bits,
    different scenes by >=16, so threshold 10 sits safely in the gap.
    Near-uniform frames (e.g. black strobe-off moments, popcount < 4) carry
    no information and would match across unrelated night clips, so they
    don't count as comparable.
    """
    from analyzer.frame_hasher import hamming
    threshold = 10

    def informative(h: int | None) -> bool:
        return h is not None and bin(h).count("1") >= 4

    for path, other in known_sigs.items():
        comparable = 0
        match = True
        for a, b in zip(sig, other):
            if not informative(a) or not informative(b):
                continue
            comparable += 1
            if hamming(a, b) > threshold:
                match = False
                break
        if match and comparable >= 2:
            return path
    return None


def phase_2_analyze(video_paths: list[Path], existing: dict | None = None, save_cb=None) -> dict:
    """Phase 2: Video Analysis + Vision Tagging.

    Resumable: clips already present in `existing` are skipped, and `save_cb(result)`
    is invoked after each clip so an interruption (sleep/kill) never loses progress.
    Near-duplicate clips (3-frame dHash signature) inherit the tags of their
    visual twin instead of going through Gemma again.
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: Video Analysis & Vision Tagging")
    logger.info("=" * 60)

    result = dict(existing) if existing else {}
    total = len(video_paths)

    # Signatures of already-tagged clips (for the duplicate pre-filter)
    known_sigs: dict[str, list] = {
        p: e["dhash_sig"] for p, e in result.items()
        if isinstance(e, dict) and e.get("dhash_sig")
    }

    for i, vp in enumerate(video_paths, 1):
        vp_str = str(vp)
        if vp_str in result and "vision_tags" in result[vp_str]:
            # Backfill signature for entries from before the pre-filter existed
            if vp_str not in known_sigs:
                sig = _video_signature(vp_str)
                if sig:
                    result[vp_str]["dhash_sig"] = sig
                    known_sigs[vp_str] = sig
            logger.info(f"\n[{i}/{total}] Skipping {vp.name} (already tagged)")
            continue

        # Pre-filter: visually near-identical to an already-tagged clip?
        sig = _video_signature(vp_str)
        twin = _find_visual_twin(sig, known_sigs) if sig else None
        if twin is not None:
            twin_entry = result[twin]
            result[vp_str] = {
                "vision_tags": twin_entry.get("vision_tags", []),
                "vision_tags_filtered": twin_entry.get("vision_tags_filtered", []),
                "tag_count": twin_entry.get("tag_count", 0),
                "usable_count": twin_entry.get("usable_count", 0),
                "duplicate_of": twin,
                "dhash_sig": sig,
            }
            logger.info(f"\n[{i}/{total}] {vp.name}: visual duplicate of "
                        f"{Path(twin).name} – inheriting tags (Gemma skipped)")
            if save_cb is not None:
                save_cb(result)
            continue

        logger.info(f"\n[{i}/{total}] Analyzing {vp.name}...")

        # Vision tagging via Gemma 4. A single unreadable/corrupt clip must
        # NOT kill the whole run – mark it empty and carry on.
        logger.info("  Running vision tagging (Gemma 4 E2B)...")
        try:
            tags = tag_video_frames(vp_str)
        except Exception as e:
            logger.error(f"  ✗ Tagging failed for {vp.name} ({e}) – skipping clip")
            result[vp_str] = {
                "vision_tags": [],
                "vision_tags_filtered": [],
                "tag_count": 0,
                "usable_count": 0,
                "error": str(e),
                "dhash_sig": sig,
            }
            if save_cb is not None:
                save_cb(result)
            continue

        filtered = filter_unusable(tags)

        result[vp_str] = {
            "vision_tags": [t.to_dict() for t in tags],
            "vision_tags_filtered": [t.to_dict() for t in filtered],
            "tag_count": len(tags),
            "usable_count": len(filtered),
            "dhash_sig": sig,
        }
        if sig:
            known_sigs[vp_str] = sig

        logger.info(f"  Tags: {len(tags)} total, {len(filtered)} usable")
        for t in filtered[:5]:
            logger.info(f"    t={t.time:.1f}s  {t.tag}  ({t.confidence:.2f})")

        # Persist after every clip so progress survives interruptions
        if save_cb is not None:
            save_cb(result)

    return result


def phase_3_regie(
    analysis_data: dict,
    preset: str,
    duration: float,
    provider: str = "",
    multi: bool = False,
) -> dict:
    """
    Phase 3: AI Regie – Multi-provider edit plan generation.
    Supports Claude Fable 5, Gemini 3.1 Pro, and DeepSeek V4 Pro.
    """
    logger.info("=" * 60)
    logger.info("PHASE 3: AI Regie – Generating Edit Plan")
    logger.info("=" * 60)

    # Show provider status
    providers = list_available_providers()
    available = [p for p in providers if p["available"]]
    logger.info(f"  Available providers: {', '.join(p['name'] for p in available) or 'none'}")

    if not available:
        logger.warning("No AI provider available – skipping Regie phase")
        logger.warning(
            "Set at least one API key in .env:\n"
            "  ANTHROPIC_API_KEY=...  (Claude Fable 5)\n"
            "  GEMINI_API_KEY=...     (Gemini 3.1 Pro)\n"
            "  DEEPSEEK_API_KEY=...   (DeepSeek V4 Pro)"
        )
        return {"edit_plan": None, "skipped": True, "reason": "no_api_key"}

    # Real source durations → the planner stops scheduling cuts past a clip's
    # end (the verifier additionally clamps, but informed plans cut better).
    p2 = analysis_data.get("phase_2") or {}
    durations = {}
    for vp_str, entry in p2.items():
        if isinstance(entry, dict):
            d = _probe_duration(Path(vp_str))
            if d > 0:
                durations[Path(vp_str).name] = round(d, 2)
    if durations:
        analysis_data = {**analysis_data, "clip_durations": durations}

    # Seamless loop (algorithmic, no AI needed)
    if preset == "seamless_loop":
        videos = list(analysis_data.get("sync", {}).get("offsets", {}).keys())
        if videos:
            plan = create_seamless_loop_plan(videos[0], 5.0, 5.0 + duration)
            plan.save(OUTPUT_DIR / "edit_plan.json")
            result = plan.to_dict()
            logger.info(f"\n  Seamless Loop Plan: {len(plan.clips)} clips, {plan.total_duration:.1f}s")
            return {"edit_plan": result}
        else:
            logger.error("No videos available for seamless loop")
            return {"edit_plan": None}

    # Multi-provider mode: generate from all available providers
    if multi:
        logger.info("  Mode: MULTI-PROVIDER (generating plans from all available AIs)")
        try:
            plans = generate_multi_plan(
                analysis_data,
                preset=preset,
                duration=duration,
            )
        except RuntimeError as e:
            logger.error(f"Multi-provider generation failed: {e}")
            return {"edit_plan": None, "skipped": True, "reason": str(e)}

        # Save all plans
        all_plans = {}
        for name, plan in plans.items():
            plan.save(OUTPUT_DIR / f"edit_plan_{name}.json")
            all_plans[name] = plan.to_dict()
            logger.info(f"\n  [{name.upper()}] {plan.model_used}")
            logger.info(f"    {len(plan.clips)} clips, {plan.total_duration:.1f}s, "
                        f"generated in {plan.generation_time_s:.1f}s")
            logger.info(f"    Narrative: {plan.narrative}")

        # Use the first provider's plan as the default
        primary = list(plans.values())[0]
        primary.save(OUTPUT_DIR / "edit_plan.json")

        return {"edit_plan": primary.to_dict(), "all_plans": all_plans}

    # Single provider mode
    try:
        plan = generate_edit_plan(
            analysis_data,
            preset=preset,
            duration=duration,
            provider=provider,
            output_path=OUTPUT_DIR / "edit_plan.json",
        )
    except ValueError as e:
        logger.error(f"Provider error: {e}")
        return {"edit_plan": None, "skipped": True, "reason": str(e)}

    result = plan.to_dict()

    logger.info(f"\n  Edit Plan by {plan.provider_used} ({plan.model_used})")
    logger.info(f"  {len(plan.clips)} clips, {plan.total_duration:.1f}s, "
                f"generated in {plan.generation_time_s:.1f}s")
    logger.info(f"  Narrative: {plan.narrative}")
    if plan.hook_text:
        logger.info(f'  Anti-advice hook (first ~3s): "{plan.hook_text}"')

    for i, clip in enumerate(plan.clips):
        phase = f"  [{clip.phase}]" if clip.phase else ""
        logger.info(f"    [{i + 1:02d}] {Path(clip.video).name}  "
                     f"{clip.start:.3f}s → {clip.end:.3f}s  ({clip.duration:.1f}s)  {clip.transition}{phase}")

    return {"edit_plan": result}


def phase_4_copywriting(clips_metadata: list[dict], style: str = "techno") -> dict:
    """Phase 4: Llama 3.2 Copywriting – filenames and captions."""
    logger.info("=" * 60)
    logger.info("PHASE 4: Copywriting – Filenames & Captions")
    logger.info("=" * 60)

    results = batch_process(clips_metadata, style=style, model=COPYWRITER_MODEL)
    save_captions(results, OUTPUT_DIR / "captions.json")

    for r in results:
        logger.info(f"  {r.filename}.mp4")
        logger.info(f"    → {r.caption[:80]}...")

    return {
        "captions": [r.to_dict() for r in results],
        "count": len(results),
    }


# Serializes YOLO inference (the shared model instance is not thread-safe)
# and the tracking-cache file when snippets are exported in parallel.
_TRACKING_LOCK = threading.Lock()


def _tracked_x_center(video: str, start: float, end: float) -> float | None:
    """
    Cached JIT auto-framing: average x-position of the main person in the
    clip window. Results are persisted in output/tracking_cache.json so
    variant runs and re-exports skip YOLO entirely for known windows.
    """
    cache_path = OUTPUT_DIR / "tracking_cache.json"
    key = f"{Path(video).name}|{start:.3f}|{end:.3f}"

    with _TRACKING_LOCK:
        cache: dict = {}
        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        if key in cache:
            logger.info("       → (cached)")
            return cache[key]  # may be None (= no subject found)

        from analyzer.tracking_engine import sample_x_center
        avg_x = sample_x_center(video, start_time=start, end_time=end, samples=10, imgsz=640)

        cache[key] = avg_x
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except OSError as e:
            logger.warning(f"Could not write tracking cache: {e}")
        return avg_x


def phase_5_assembly(
    edit_plan: dict | None,
    sync_data: dict | None = None,
    music_path: Path | None = None,
    vision_data: dict | None = None,
) -> None:
    """Phase 5: FFmpeg Assembly – Export with 3D-LUT, VFX, and optional master audio.

    If `music_path` is given, a chosen music track is laid over the finished
    reel (original audio replaced), with the track's drop aligned to the reel's
    energy peak (derived from `vision_data`).
    """
    logger.info("=" * 60)
    logger.info("PHASE 5: FFmpeg Assembly & Color Grading")
    logger.info("=" * 60)

    # Fallback: Edit-Plan aus Datei laden, falls nicht übergeben
    if edit_plan is None:
        edit_plan_path = OUTPUT_DIR / "edit_plan.json"
        if edit_plan_path.exists():
            try:
                with open(edit_plan_path, encoding="utf-8") as f:
                    edit_plan = json.load(f)
                logger.info(f"Loaded edit plan from {edit_plan_path}")
            except Exception as e:
                logger.error(f"Could not load edit plan: {e}")
                return
        else:
            logger.warning("No edit plan available – skipping assembly")
            logger.info("Tip: Set an AI provider API key to generate edit plans")
            return

    clips = edit_plan.get("clips", [])
    if not clips:
        logger.warning("Empty edit plan – nothing to assemble")
        return

    logger.info(f"Assembling {len(clips)} clips...")

    # Export snippets in parallel: encodes are independent FFmpeg processes,
    # so a small worker pool overlaps tracking + encoding. Results keep plan
    # order via their index. Worker count via EXPORT_WORKERS (default 3).
    workers = max(1, int(os.environ.get("EXPORT_WORKERS", "3")))
    results: dict[int, Path] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_export_one_snippet, i, clip, sync_data): i
            for i, clip in enumerate(clips)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                path = fut.result()
                if path is not None:
                    results[idx] = path
            except Exception as e:
                logger.error(f"  [{idx + 1:02d}] ✗ Export worker error: {e}")

    exported_snippets = [results[i] for i in sorted(results)]  # plan order

    # Final step: stitch the snippets into ONE reel, in plan order
    final_reel: Path | None = None
    if len(exported_snippets) >= 2:
        final_reel = _concat_snippets(exported_snippets, style=edit_plan.get("style", "reel"))
    elif len(exported_snippets) == 1:
        final_reel = exported_snippets[0]
        logger.info("Only one snippet exported – skipping concat (snippet IS the reel)")
    else:
        logger.warning("No snippets exported – nothing to concatenate")

    # Optional: lay a chosen music track over the finished reel
    if music_path is not None and final_reel is not None:
        _apply_music_bed(Path(final_reel), Path(music_path), clips, vision_data)


def _export_one_snippet(i: int, clip: dict, sync_data: dict | None) -> Path | None:
    """Export a single edit-plan clip to output/snippet_<idx>_<stem>.mp4.

    Thread-safe: YOLO tracking and its cache are serialized via _TRACKING_LOCK
    inside _tracked_x_center; the FFmpeg encode runs fully parallel.
    Returns the snippet path, or None on failure.
    """
    video = clip.get("video", "")
    start = clip.get("start", 0)
    end = clip.get("end", 0)
    lut = clip.get("lut", DEFAULT_LUT)
    vfx = clip.get("vfx", "none")
    slow_mo = clip.get("slow_mo", False)
    slow_mo_factor = clip.get("slow_mo_factor", 1.0)
    crop = clip.get("crop", "9:16")

    if not Path(video).exists():
        logger.warning(f"  Source not found: {video}")
        return None

    # Master Audio Sync Logic
    master_audio = None
    offset = 0.0
    if sync_data:
        ref_clip = sync_data.get("reference_clip", "")
        AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif"}
        if Path(ref_clip).suffix.lower() in AUDIO_EXTENSIONS:
            master_audio = ref_clip
            offset = sync_data.get("offsets", {}).get(video, 0.0)

    # Build FFmpeg filter chain
    vf_parts = []

    # Slow motion (applied first in chain)
    if slow_mo and slow_mo_factor > 1.0:
        vf_parts.append(f"setpts=PTS*{slow_mo_factor}")

    # Beat-reactive VFX: flash (brightness pop on the cut)
    # eq brightness range is [-1, 1]; 1.5 blew the frame out to pure white.
    if vfx == "flash":
        vf_parts.append("eq=brightness=0.4:enable='between(t,0,0.2)'")

    # Crop for 9:16 (mit JIT Auto-Framing, gecacht)
    if crop == "9:16":
        crop_x_expr = "(iw-ih*9/16)/2"  # Standard Center-Crop
        try:
            logger.info(f"  [{i + 1:02d}] JIT Auto-Framing: Tracking {Path(video).name} ({start:.1f}s - {end:.1f}s)...")
            avg_x = _tracked_x_center(video, start, end)
            if avg_x is not None:
                crop_x_expr = f"max(0,min(iw-ih*9/16,iw*{avg_x:.3f}-(ih*9/16)/2))"
                logger.info(f"       → Subject tracked at x_center={avg_x:.2f}. Dynamic crop applied.")
            else:
                logger.info(f"       → No subject found. Using center crop.")
        except Exception as e:
            logger.warning(f"       → JIT Auto-Framing failed: {e}. Using center crop.")

        # Escape commas: in an FFmpeg filtergraph a bare comma separates
        # filters, so min()/max() args would otherwise be torn apart.
        crop_x_expr = crop_x_expr.replace(",", "\\,")
        vf_parts.append(f"crop=ih*9/16:ih:{crop_x_expr}:0")
        vf_parts.append("scale=1080:1920")

        # Beat-reactive VFX: pump (zoom punch decaying over 0.3 s).
        # zoompan does not support the `enable` timeline option, so this
        # uses a per-frame scale + centered crop back to 1080x1920 instead.
        # Placed after the 9:16 crop so the frame size is known and the
        # image is not distorted.
        if vfx == "pump":
            zoom = "(1+0.05*max(0\\,1-t/0.3))"
            vf_parts.append(
                f"scale=w='trunc(1080*{zoom}/2)*2':h='trunc(1920*{zoom}/2)*2':eval=frame"
            )
            vf_parts.append("crop=1080:1920")

    # 3D-LUT color grading – relativer Pfad mit Forward-Slashes für FFmpeg
    lut_path = LUT_DIR / f"{lut}.cube"
    if lut_path.exists():
        rel_path = os.path.relpath(lut_path).replace("\\", "/")
        vf_parts.append(f"lut3d={rel_path}")
    else:
        logger.warning(f"  LUT not found: {lut_path}, using default")
        default_path = LUT_DIR / f"{DEFAULT_LUT}.cube"
        if default_path.exists():
            rel_path = os.path.relpath(default_path).replace("\\", "/")
            vf_parts.append(f"lut3d={rel_path}")

    # Beat-reactive VFX: glitch (machine-like black-frame stutter at the cut).
    # Three ~2-frame black bursts in the first 0.24s – the "single-digit frame
    # dropout" look for day→night transitions. Single quotes protect the commas
    # in the enable expression (same as flash). Placed last so the black frames
    # override the graded image.
    if vfx == "glitch":
        vf_parts.append(
            "drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:"
            "enable='between(t,0,0.04)+between(t,0.1,0.14)+between(t,0.2,0.24)'"
        )

    # Normalize fps as the LAST filter so every snippet shares identical
    # video parameters (fps/pix_fmt/resolution) – this lets the final
    # concat stream-copy instead of re-encoding the whole reel.
    vf_parts.append(f"fps={REEL_FPS}")
    vf = ",".join(vf_parts)

    output_name = f"snippet_{i + 1:03d}_{Path(video).stem}.mp4"
    output_path = OUTPUT_DIR / output_name

    # Uniform encode params (audio too: mixed sample rates/channel counts
    # would break audio stream-copy concat).
    encode_params = [
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
    ]

    # Build FFmpeg command
    if master_audio and Path(master_audio).exists():
        # Extract video from video clip, audio from master audio (synchronized)
        master_start = max(0.0, start + offset)
        master_end = max(0.0, end + offset)
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(video),
            "-ss", f"{master_start:.3f}", "-to", f"{master_end:.3f}", "-i", str(master_audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            *encode_params,
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-to", f"{end:.3f}",
            "-i", str(video),
            "-vf", vf,
            *encode_params,
            "-movflags", "+faststart",
            str(output_path),
        ]

    logger.info(f"  [{i + 1:02d}] {Path(video).name} → {output_name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            size_kb = output_path.stat().st_size / 1024
            logger.info(f"  [{i + 1:02d}] ✓ Exported ({size_kb:.0f} KB)")
            return output_path
        logger.error(f"  [{i + 1:02d}] ✗ FFmpeg error: {result.stderr.strip()[-400:]}")
    except subprocess.TimeoutExpired:
        logger.error(f"  [{i + 1:02d}] ✗ Timeout exporting clip")
    except Exception as e:
        logger.error(f"  [{i + 1:02d}] ✗ Error: {e}")
    return None


def _concat_snippets(snippets: list[Path], style: str = "reel") -> Path | None:
    """
    Concatenate exported snippets into the final reel (output/reel_<style>.mp4).

    Re-encodes at a uniform frame rate: source clips recorded in slow-mo (e.g.
    120 fps phone footage) produce snippets with mixed fps, which breaks
    stream-copy concat timing.
    """
    output_path = OUTPUT_DIR / f"reel_{style}.mp4"
    list_path = OUTPUT_DIR / "concat_list.txt"

    # concat demuxer list; single quotes in paths escaped per FFmpeg syntax
    lines = [f"file '{str(p.resolve()).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"
             for p in snippets]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    logger.info(f"Concatenating {len(snippets)} snippets → {output_path.name}")

    # Fast path: snippets are exported with uniform fps/pix_fmt/resolution,
    # so the concat demuxer can stream-copy (seconds instead of minutes, and
    # no second encode generation degrading quality). Verify uniformity first
    # because mismatched streams would silently produce a broken file.
    if _snippets_uniform(snippets):
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"  ✓ Final reel (stream copy): {output_path} ({size_mb:.1f} MB)")
                return output_path
            logger.warning(f"  Stream-copy concat failed, falling back to re-encode: {result.stderr[-200:]}")
        except Exception as e:
            logger.warning(f"  Stream-copy concat error ({e}), falling back to re-encode")
    else:
        logger.info("  Snippets not uniform (mixed fps/resolution) – re-encoding concat")

    # Fallback: re-encode (slow on CPU – a full 90 s reel needs >10 min)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-vf", f"fps={REEL_FPS}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ Final reel: {output_path} ({size_mb:.1f} MB)")
            return output_path
        logger.error(f"  ✗ Concat failed: {result.stderr[-300:]}")
    except subprocess.TimeoutExpired:
        logger.error("  ✗ Timeout concatenating reel")
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
    return None


def _snippets_uniform(snippets: list[Path]) -> bool:
    """True if all snippets share codec, resolution, fps and audio params."""
    signatures = set()
    for p in snippets:
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-show_entries", "stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
                 "-of", "csv=p=0", str(p)],
                capture_output=True, text=True, timeout=30,
            )
            if out.returncode != 0:
                return False
            signatures.add(out.stdout.strip())
        except Exception:
            return False
    return len(signatures) == 1


# ---------------------------------------------------------------------------
# Music overlay (energy-aligned background track)
# ---------------------------------------------------------------------------

# Tag → energy bonus (mirrors the highlight taxonomy in CLAUDE.md).
_TAG_ENERGY = {
    "CROWD_ENERGY": 0.8, "LIGHT_SHOW": 0.5, "DJ_SETUP": 0.3,
    "BREAKDOWN": 0.2, "TRANSITION": 0.1,
    "BACKSTAGE": 0.0, "ARRIVAL": 0.0, "PACKDOWN": 0.0, "UNUSABLE": -1.0,
}


def _clip_reel_duration(clip: dict) -> float:
    """Duration this clip occupies in the final reel (slow-mo stretches it)."""
    dur = float(clip.get("end", 0)) - float(clip.get("start", 0))
    if clip.get("slow_mo") and float(clip.get("slow_mo_factor", 1.0)) > 1.0:
        dur *= float(clip["slow_mo_factor"])
    return max(0.0, dur)


def _score_clip_energy(clip: dict, vision_data: dict | None) -> float:
    """Energy proxy for a clip from its source's vision tags."""
    if not vision_data:
        return 0.0
    entry = vision_data.get(clip.get("video", "")) or {}
    tags = entry.get("vision_tags_filtered") or entry.get("vision_tags") or []
    return sum(_TAG_ENERGY.get(t.get("tag", ""), 0.0) for t in tags)


def _reel_peak_time(clips: list[dict], vision_data: dict | None) -> tuple[float, float]:
    """
    (peak_time, total_duration) on the FINAL reel timeline.

    Peak = midpoint of the highest-energy clip. Falls back to a clip whose
    reason/transition mentions a drop/peak, then to 62 % of the reel.
    """
    if not clips:
        return 0.0, 0.0

    starts, durs, scores = [], [], []
    t = 0.0
    for c in clips:
        d = _clip_reel_duration(c)
        starts.append(t)
        durs.append(d)
        scores.append(_score_clip_energy(c, vision_data))
        t += d
    total = t

    best = max(range(len(clips)), key=lambda i: scores[i])
    if scores[best] > 0:
        return starts[best] + durs[best] / 2, total

    for i, c in enumerate(clips):
        text = f"{c.get('reason', '')} {c.get('transition', '')}".lower()
        if "drop" in text or "peak" in text:
            return starts[i] + durs[i] / 2, total

    return 0.62 * total, total


def _find_music_drop(music_path: Path, sr: int = 22050) -> float:
    """
    Self-contained drop detection: time of the steepest sustained rise in
    sub-200 Hz (bass) energy. Uses only librosa + numpy (no V2 config).
    """
    import numpy as np
    import librosa

    y, _ = librosa.load(str(music_path), sr=sr, mono=True)
    n_fft, hop = 2048, 512
    spec = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    bass = spec[freqs < 200].mean(axis=0)
    if bass.size < 4:
        return 0.0

    win = max(1, int(0.5 * sr / hop))  # ~0.5 s smoothing
    bass_s = np.convolve(bass, np.ones(win) / win, mode="same")
    deriv = np.diff(bass_s)
    times = librosa.frames_to_time(np.arange(len(deriv)), sr=sr, hop_length=hop)

    lo, hi = int(0.05 * len(deriv)), int(0.95 * len(deriv))  # trim edges
    if hi <= lo:
        return 0.0
    idx = lo + int(np.argmax(deriv[lo:hi]))
    return float(times[idx])


def _probe_duration(path: Path) -> float:
    """Media duration in seconds via ffprobe (0.0 on failure)."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def _apply_music_bed(
    reel_path: Path, music_path: Path,
    clips: list[dict], vision_data: dict | None,
) -> None:
    """
    Replace the reel's audio with `music_path`, aligning the track's drop to
    the reel's energy peak. Adds a 1.5 s fade-out. Edits `reel_path` in place.
    """
    if not music_path.exists():
        logger.warning(f"Music file not found: {music_path} – keeping original audio")
        return

    reel_dur = _probe_duration(reel_path)
    if reel_dur <= 0:
        logger.error("Could not probe reel duration – skipping music overlay")
        return

    peak_t, _ = _reel_peak_time(clips, vision_data)
    try:
        drop_t = _find_music_drop(music_path)
    except Exception as e:
        logger.warning(f"Drop detection failed ({e}); starting music at 0:00")
        drop_t = 0.0
    music_start = max(0.0, drop_t - peak_t)

    music_dur = _probe_duration(music_path)
    if music_dur and (music_dur - music_start) < reel_dur:
        logger.warning(
            f"Music ({music_dur:.0f}s, from {music_start:.1f}s) is shorter than the "
            f"reel ({reel_dur:.0f}s) – the tail will be silent/cut."
        )

    logger.info(
        f"🎵 Music overlay: drop@{drop_t:.1f}s → reel peak@{peak_t:.1f}s  "
        f"(track starts at {music_start:.1f}s)"
    )

    fade_start = max(0.0, reel_dur - 1.5)
    tmp_path = reel_path.with_name(reel_path.stem + "_music.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(reel_path),
        "-ss", f"{music_start:.3f}", "-i", str(music_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-af", f"afade=t=out:st={fade_start:.3f}:d=1.5",
        "-shortest", "-movflags", "+faststart",
        str(tmp_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            tmp_path.replace(reel_path)
            logger.info(f"  ✓ Music applied → {reel_path.name}")
        else:
            logger.error(f"  ✗ Music overlay failed: {result.stderr.strip()[-400:]}")
            tmp_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"  ✗ Music overlay error: {e}")
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    input_dir: Path = INPUT_DIR,
    preset: str = "highlight",
    duration: float = 60.0,
    phases: list[str] | None = None,
    style: str = "techno",
    provider: str = "",
    multi: bool = False,
    music: Path | None = None,
):
    """Run the complete UNREEL V3 pipeline."""
    # Ensure directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Phase 0: Ingestion & Renaming (Dedup + UNREEL_<timestamp>) yields the clip list
    video_paths = phase_ingest(input_dir)

    if not video_paths:
        logger.error(f"No video files found in {input_dir}")
        logger.info("Place your DJ footage in the 'input/' directory and re-run.")
        return

    logger.info(f"UNREEL V3 – Found {len(video_paths)} video(s)")
    for vp in video_paths:
        logger.info(f"  {vp.name}")

    # Show provider status at start
    providers = list_available_providers()
    logger.info("\n📡 AI Providers:")
    for p in providers:
        status = "✅" if p["available"] else "❌"
        logger.info(f"  {status} {p['name']:10s}  {p['model']}")

    all_results = {}
    results_path = OUTPUT_DIR / "pipeline_results.json"

    def _save_progress():
        """Persist results after each phase so a later crash never loses work."""
        serializable = json.loads(json.dumps(all_results, default=str))
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

    # Resume: ALWAYS seed from the last saved run when present. The expensive,
    # preset-independent analysis (audio sync, vision tagging) is then reused
    # across runs — only the preset-dependent phases (regie/copy/export) re-run.
    # A full run no longer wipes prior vision tags by starting from scratch.
    if results_path.exists():
        try:
            with open(results_path, encoding="utf-8") as f:
                all_results = json.load(f)
            logger.info(f"Resumed prior results from {results_path}")
        except Exception as e:
            logger.warning(f"Could not load prior results ({e}); starting fresh")

    # Phase 0: Setup (always run)
    if phases is None or "setup" in phases:
        all_results["luts"] = phase_0_setup()

    # Phase 1: Audio Sync + Kick/Snare (preset-independent → reuse cache).
    # Explicitly requesting --phase sync/analyze forces a recompute; a full
    # run reuses cached results if present.
    sync_requested = phases is not None and ("sync" in phases or "analyze" in phases)
    if sync_requested or (phases is None and not all_results.get("phase_1")):
        all_results["phase_1"] = phase_1_sync(video_paths)
        _save_progress()
    elif all_results.get("phase_1"):
        logger.info("✓ Reusing cached audio sync (phase_1)")

    # Phase 2: Video Analysis + Vision (resumable, saves after each clip)
    if phases is None or "vision" in phases or "analyze" in phases:
        prior_p2 = all_results.get("phase_2") if isinstance(all_results.get("phase_2"), dict) else None

        def _save_phase2(partial):
            all_results["phase_2"] = partial
            _save_progress()

        all_results["phase_2"] = phase_2_analyze(video_paths, existing=prior_p2, save_cb=_save_phase2)
        _save_progress()

    # Phase 3: AI Regie (multi-provider)
    if phases is None or "regie" in phases:
        all_results["phase_3"] = phase_3_regie(
            all_results, preset, duration,
            provider=provider,
            multi=multi,
        )
        _save_progress()

    # Phase 4: Copywriting – fed with REAL analysis data: vision tags from
    # phase 2, narrative/hook from the edit plan, true clip durations.
    # Only the videos actually used in the plan are processed (not all input).
    if phases is None or "copy" in phases:
        bpm = all_results.get("phase_1", {}).get("percussion", {}).get("bpm", 140)
        p2 = all_results.get("phase_2") or {}
        plan = (all_results.get("phase_3") or {}).get("edit_plan") or {}
        plan_clips = plan.get("clips", [])
        narrative = plan.get("narrative", "")
        hook = plan.get("hook_text", "")
        scene = narrative or "DJ performance"
        if hook:
            scene = f"{scene} | Hook: {hook}"

        # Unique source videos in plan order; fall back to all inputs if no plan
        videos = list(dict.fromkeys(c.get("video", "") for c in plan_clips)) \
            if plan_clips else [str(vp) for vp in video_paths]

        clips_meta = []
        for v in videos:
            entry = p2.get(v) if isinstance(p2, dict) else None
            tag_names = [t.get("tag", "") for t in (entry or {}).get("vision_tags_filtered", [])]
            top_tags = [t for t, _ in Counter(tag_names).most_common(3) if t] or ["techno"]
            plan_dur = sum(
                c.get("duration", c.get("end", 0) - c.get("start", 0))
                for c in plan_clips if c.get("video") == v
            )
            peaks = [c.get("reason", "") for c in plan_clips
                     if c.get("video") == v and "drop" in c.get("reason", "").lower()]
            clips_meta.append({
                "bpm": bpm,
                "tags": top_tags,
                "duration": round(plan_dur) or 30,
                "scene": scene,
                "peak": peaks[0] if peaks else "bass drop",
            })
        all_results["phase_4"] = phase_4_copywriting(clips_meta, style=style)
        _save_progress()

    # Phase 5: Assembly
    if phases is None or "export" in phases:
        edit_plan = all_results.get("phase_3", {}).get("edit_plan")
        sync_data = all_results.get("phase_1", {}).get("sync")
        phase_5_assembly(
            edit_plan,
            sync_data=sync_data,
            music_path=music,
            vision_data=all_results.get("phase_2"),
        )

    # Final save
    _save_progress()

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info(f"Results: {results_path}")
    logger.info(f"Output:  {OUTPUT_DIR}/")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="UNREEL V3 – Automated DJ Video Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --input ./input --preset highlight --duration 60
  python -m src.main --input ./input --preset seamless_loop --duration 30
  python -m src.main --input ./input --provider gemini --phase regie
  python -m src.main --input ./input --provider deepseek --multi
  python -m src.main --input ./input --phase sync
  python -m src.main --luts
""",
    )

    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=INPUT_DIR,
        help="Input directory with video files (default: ./input)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--preset", "-p",
        choices=["highlight", "drop_focus", "seamless_loop", "moody", "pov_story", "tarantino"],
        default="highlight",
        help="Edit preset style (default: highlight)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=60.0,
        help="Target reel duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--style", "-s",
        choices=["techno", "house", "minimal"],
        default="techno",
        help="Music style for captions (default: techno)",
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "gemini", "deepseek", "auto"],
        default="",
        help="AI provider for regie phase (default: auto-detect from .env)",
    )
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Generate edit plans from ALL available AI providers for comparison",
    )
    parser.add_argument(
        "--music",
        type=Path,
        default=None,
        help="Lay a music track over the final reel (replaces original audio). "
             "The track's drop is auto-aligned to the reel's energy peak.",
    )
    parser.add_argument(
        "--phase",
        nargs="*",
        choices=["setup", "sync", "vision", "regie", "copy", "export", "analyze"],
        help="Run specific phases only (analyze = sync+vision)",
    )
    parser.add_argument(
        "--luts",
        action="store_true",
        help="Generate LUT files only and exit",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Logging setup
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Generate LUTs only
    if args.luts:
        phase_0_setup()
        return

    # Run pipeline with CLI-provided paths
    run_pipeline(
        input_dir=args.input,
        preset=args.preset,
        duration=args.duration,
        phases=args.phase,
        style=args.style,
        provider=args.provider,
        multi=args.multi,
        music=args.music,
    )


if __name__ == "__main__":
    main()
