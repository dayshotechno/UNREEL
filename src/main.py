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
from copywriter import generate_caption, generate_filename, batch_process, save_captions
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


def phase_2_analyze(video_paths: list[Path], existing: dict | None = None, save_cb=None) -> dict:
    """Phase 2: Video Analysis + Vision Tagging.

    Resumable: clips already present in `existing` are skipped, and `save_cb(result)`
    is invoked after each clip so an interruption (sleep/kill) never loses progress.
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: Video Analysis & Vision Tagging")
    logger.info("=" * 60)

    result = dict(existing) if existing else {}
    total = len(video_paths)

    for i, vp in enumerate(video_paths, 1):
        if str(vp) in result and "vision_tags" in result[str(vp)]:
            logger.info(f"\n[{i}/{total}] Skipping {vp.name} (already tagged)")
            continue

        logger.info(f"\n[{i}/{total}] Analyzing {vp.name}...")

        # Vision tagging via Gemma 4
        logger.info("  Running vision tagging (Gemma 4 E2B)...")
        tags = tag_video_frames(str(vp))
        filtered = filter_unusable(tags)

        result[str(vp)] = {
            "vision_tags": [t.to_dict() for t in tags],
            "vision_tags_filtered": [t.to_dict() for t in filtered],
            "tag_count": len(tags),
            "usable_count": len(filtered),
        }

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


def phase_5_assembly(edit_plan: dict | None) -> None:
    """Phase 5: FFmpeg Assembly – Export with 3D-LUT and effects."""
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

    exported_snippets: list[Path] = []  # in plan order, for final concat

    for i, clip in enumerate(clips):
        video = clip.get("video", "")
        start = clip.get("start", 0)
        end = clip.get("end", 0)
        lut = clip.get("lut", DEFAULT_LUT)
        slow_mo = clip.get("slow_mo", False)
        slow_mo_factor = clip.get("slow_mo_factor", 1.0)
        crop = clip.get("crop", "9:16")

        if not Path(video).exists():
            logger.warning(f"  Source not found: {video}")
            continue

        # Build FFmpeg filter chain
        vf_parts = []

        # Slow motion (applied first in chain)
        if slow_mo and slow_mo_factor > 1.0:
            vf_parts.append(f"setpts=PTS*{slow_mo_factor}")

        # Crop for 9:16
        if crop == "9:16":
            vf_parts.append("crop=ih*9/16:ih")
            vf_parts.append("scale=1080:1920")

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

        vf = ",".join(vf_parts)

        output_name = f"snippet_{i + 1:03d}_{Path(video).stem}.mp4"
        output_path = OUTPUT_DIR / output_name

        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-to", f"{end:.3f}",
            "-i", str(video),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        logger.info(f"  [{i + 1:02d}] {Path(video).name} → {output_name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                size_kb = output_path.stat().st_size / 1024
                logger.info(f"       ✓ Exported ({size_kb:.0f} KB)")
                exported_snippets.append(output_path)
            else:
                logger.error(f"       ✗ FFmpeg error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            logger.error(f"       ✗ Timeout exporting clip")
        except Exception as e:
            logger.error(f"       ✗ Error: {e}")

    # Final step: stitch the snippets into ONE reel, in plan order
    if len(exported_snippets) >= 2:
        _concat_snippets(exported_snippets, style=edit_plan.get("style", "reel"))
    elif len(exported_snippets) == 1:
        logger.info("Only one snippet exported – skipping concat (snippet IS the reel)")
    else:
        logger.warning("No snippets exported – nothing to concatenate")


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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
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

    # Resume: when running only a SUBSET of phases, seed from the last saved run
    # so downstream phases (e.g. regie) can reuse prior analysis without recomputing.
    if phases is not None and results_path.exists():
        try:
            with open(results_path, encoding="utf-8") as f:
                all_results = json.load(f)
            logger.info(f"Resumed prior results from {results_path}")
        except Exception as e:
            logger.warning(f"Could not load prior results ({e}); starting fresh")

    # Phase 0: Setup (always run)
    if phases is None or "setup" in phases:
        all_results["luts"] = phase_0_setup()

    # Phase 1: Audio Sync + Kick/Snare
    if phases is None or "sync" in phases or "analyze" in phases:
        all_results["phase_1"] = phase_1_sync(video_paths)
        _save_progress()

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

    # Phase 4: Copywriting
    if phases is None or "copy" in phases:
        clips_meta = []
        for vp in video_paths:
            clips_meta.append({
                "bpm": all_results.get("phase_1", {}).get("percussion", {}).get("bpm", 140),
                "tags": ["techno"],
                "duration": 30,
            })
        all_results["phase_4"] = phase_4_copywriting(clips_meta, style=style)
        _save_progress()

    # Phase 5: Assembly
    if phases is None or "export" in phases:
        edit_plan = all_results.get("phase_3", {}).get("edit_plan")
        phase_5_assembly(edit_plan)

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
        choices=["highlight", "drop_focus", "seamless_loop", "moody", "pov_story"],
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
    )


if __name__ == "__main__":
    main()
