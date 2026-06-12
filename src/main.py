#!/usr/bin/env python3
"""UNREEL V3 – CLI entry point & pipeline orchestrator."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
LUT_DIR = BASE_DIR / "luts"
DEFAULT_LUT = "underground_dark"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase 5 – FFmpeg Assembly & Export
# ---------------------------------------------------------------------------
def phase_5_assembly(edit_plan: dict | None) -> None:
    """Phase 5: FFmpeg Assembly & Export with 3D-LUT and effects."""
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
            logger.info(
                "Tip: Run the regie phase first (--phase regie) "
                "or provide an edit_plan.json"
            )
            return

    if not edit_plan:
        logger.warning("No edit plan available – skipping assembly")
        logger.info("Tip: Set an AI provider API key to generate edit plans")
        return

    # Build FFmpeg filter chain
    vf_parts = []

    # 9:16 crop
    vf_parts.append("crop=ih*9/16:ih,scale=1080:1920")

    # 3D-LUT color grading – relativer Pfad mit Forward-Slashes für FFmpeg
    lut = edit_plan.get("lut", DEFAULT_LUT)
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

    # Slow‑motion for high‑motion clips
    slow_mo = edit_plan.get("slow_mo", False)
    if slow_mo:
        factor = edit_plan.get("slow_mo_factor", 2.0)
        vf_parts.append(f"setpts=PTS*{factor}")

    filter_complex = ",".join(vf_parts)

    # Input / output paths
    input_path = edit_plan.get("input", "")
    output_filename = edit_plan.get("output", "final_reel.mp4")
    output_path = OUTPUT_DIR / output_filename

    # Build command
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        str(output_path),
    ]

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Export finished: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Parse arguments and run the requested pipeline phase."""
    import argparse

    parser = argparse.ArgumentParser(description="UNREEL V3 Pipeline")
    parser.add_argument("--input", type=str, help="Input file or directory")
    parser.add_argument("--phase", type=str, default="assembly",
                        help="Pipeline phase to run (assembly, sync, vision, regie, copywriter)")
    parser.add_argument("--preset", type=str, default="highlight",
                        help="Edit plan preset (highlight, drop_focus, seamless_loop, moody, pov_story)")
    parser.add_argument("--duration", type=int, default=60,
                        help="Target duration in seconds")
    parser.add_argument("--provider", type=str, default="auto",
                        help="AI provider (auto, claude, gemini, deepseek)")
    parser.add_argument("--multi", action="store_true",
                        help="Run all available providers for A/B comparison")
    parser.add_argument("--luts", action="store_true",
                        help="Generate LUT files only")
    args = parser.parse_args()

    if args.luts:
        # Generate LUTs (placeholder – actual generation in lut_generator.py)
        logger.info("LUT generation requested – run `python -m analyzer.lut_generator`")
        return

    if args.phase == "assembly":
        # For now, load a dummy edit plan or from file
        edit_plan_path = OUTPUT_DIR / "edit_plan.json"
        edit_plan = None
        if edit_plan_path.exists():
            try:
                with open(edit_plan_path, encoding="utf-8") as f:
                    edit_plan = json.load(f)
            except Exception:
                pass
        phase_5_assembly(edit_plan)
    else:
        logger.info(f"Phase '{args.phase}' not implemented in this entry point.")


if __name__ == "__main__":
    main()
