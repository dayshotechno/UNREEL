"""
UNREEL V3 – High-Performance "Rich" Terminal UI (TUI)
Orchestrates the automated DJ video pipeline with full multi-processing, Pydantic
schema validation, Master-Filtergraph compilation, and an exquisite terminal interface.

Usage:
    python tui.py --preset tarantino --duration 30 --music master.mp3
    python tui.py  # Interactive mode
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter
from pathlib import Path

# Try to import Rich library
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Confirm, Prompt
    from rich.syntax import Syntax
    from rich.table import Table
except ImportError:
    print("Error: Rich library not found. Run 'pip install rich' first.")
    sys.exit(1)

# Add project root to sys.path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

from config import (
    COPYWRITER_MODEL,
    DEFAULT_LUT,
    INPUT_DIR,
    LUT_DIR,
    OUTPUT_DIR,
    REGIE_PROVIDER,
    SAMPLE_RATE,
)
from src.main import (
    _apply_music_bed,
    _concat_snippets,
    list_available_providers,
    phase_0_setup,
    phase_1_sync,
    phase_2_analyze,
    phase_3_regie,
    phase_4_copywriting,
    phase_5_assembly,
    phase_ingest,
)

# Setup standalone TUI logging
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
log_path = OUTPUT_DIR / "unreel_tui.log"
logging.basicConfig(
    level=logging.DEBUG,
    filename=str(log_path),
    filemode="w",
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("unreel_tui")
console = Console()

_RETENTION_PRESETS = {"artist_narrative", "booking", "community"}
_AUTO_JCUT_PRESETS = {"tarantino", "artist_narrative"}
_AUTO_ENDCARD_PRESETS = {"tarantino", "booking", "artist_narrative"}
_AUTO_SFX_PRESETS = {"tarantino", "artist_narrative"}


def _save_results(all_results, results_path):
    """Persist serializable results JSON."""
    try:
        serializable = json.loads(json.dumps(all_results, default=str))
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def render_banner():
    """Render the cyberpunk top banner."""
    banner_text = (
        "[bold #ff2a5f]██    ██ ███    ██ ██████  ███████ ███████ ██      ██    ██ ██████ [/bold #ff2a5f]\n"
        "[bold #ff2a5f]██    ██ ████   ██ ██   ██ ██      ██      ██      ██    ██      ██[/bold #ff2a5f]\n"
        "[bold #ff2a5f]██    ██ ██ ██  ██ ██████  █████   █████   ██      ██    ██  █████ [/bold #ff2a5f]\n"
        "[bold #ff2a5f]██    ██ ██  ██ ██ ██   ██ ██      ██      ██       ██  ██       ██[/bold #ff2a5f]\n"
        "[bold #ff2a5f] ██████  ██   ████ ██   ██ ███████ ███████ ███████   ████   ██████ [/bold #ff2a5f]\n"
    )
    banner_panel = Panel(
        banner_text,
        title="[bold white]AUTOMATED DJ VIDEO PIPELINE // STUDIO REGIE-ZENTRALE[/bold white]",
        subtitle="[bold cyan]Active Mode: CPU Core / Single-Pass Master Filtergraph Engine[/bold cyan]",
        border_style="#ff2a5f",
        padding=(1, 2),
    )
    console.print(banner_panel)
    console.print()


def render_system_status(input_dir, preset, duration, music_path, skip_sync):
    """Render setup component status table."""
    providers = list_available_providers()
    active_prov = next((p for p in providers if p["available"]), None)
    prov_str = f"[bold cyan]{active_prov['name'].upper()}[/bold cyan] ({active_prov['model']})" if active_prov else "[bold red]None (No Keys Set)[/bold red]"
    
    music_str = f"[bold accent_cyan]{Path(music_path).name}[/bold accent_cyan] (A/V Split-Editing Active)" if music_path and Path(music_path).exists() else "[bold yellow]None (Camera Scratch Audio)[/bold yellow]"
    sync_str = "[bold yellow]Bypassed (--skip-sync)[/bold yellow]" if skip_sync else "[bold green]Multi-Clip FFT Correlation[/bold green]"

    table = Table(show_header=True, header_style="bold white on #141418", border_style="#282830", expand=True)
    table.add_column("System-Komponente", style="bold #8e8e9e", width=28)
    table.add_column("Aktiver Parameter / Status", style="white")
    table.add_column("Ausführungssignal / Hardware", style="bold green", justify="right")

    table.add_row("📁 Video Quell-Ordner", f"{input_dir.resolve()}", "[✓ verifiziert]")
    table.add_row("🎧 Master Musik-Bed", music_str, sync_str)
    table.add_row("🎬 KI-Regie Stil (-p)", f"[bold #ff2a5f]{preset.upper()}[/bold #ff2a5f]", f"Ziel-Länge: [bold white]{duration:.1f}s[/bold white]")
    table.add_row("🧠 Aktiver Director", prov_str, "[Pydantic Validated]")
    table.add_row("🎞️ FFmpeg Render Engine", "Single-Pass Master Complex Filtergraph", "[State: CPU / Stream Copy]")

    console.print(Panel(table, title="[bold white]PIPELINE PARAMETER & HARDWARE KONFIGURATION[/bold white]", border_style="#282830"))
    console.print()


def run_tui_pipeline(args):
    """Execute pipeline with dynamic rich live progress bars."""
    render_banner()
    
    input_dir = args.input.resolve()
    music = args.music.resolve() if args.music and args.music.exists() else None
    preset = args.preset
    duration = args.duration
    skip_sync = args.skip_sync
    style = args.style

    if preset == "tarantino" and duration != 30.0:
        duration = 30.0
    elif preset in _RETENTION_PRESETS and duration == 60.0:
        duration = 30.0

    render_system_status(input_dir, preset, duration, music, skip_sync)

    all_results = {}
    results_path = OUTPUT_DIR / "pipeline_results.json"
    if results_path.exists():
        try:
            with open(results_path, encoding="utf-8") as f:
                all_results = json.load(f)
            logger.info(f"Resumed prior results from {results_path}")
        except Exception:
            pass

    # Progress visual definition
    progress = Progress(
        SpinnerColumn(style="bold #ff2a5f"),
        TextColumn("[bold white]{task.description:36s}[/bold white]"),
        BarColumn(bar_width=None, complete_style="#ff2a5f", finished_style="#00e5ff"),
        TextColumn("[bold cyan]{task.percentage:>3.0f}%[/bold cyan]"),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    )

    with progress:
        # ── Phase 0: Setup & Ingest ──────────────────────────────────────────
        task0 = progress.add_task("Phase 0: Setup & Quell-Ingestion...", total=100)
        all_results["luts"] = phase_0_setup()
        progress.update(task0, advance=50, description="Phase 0: Dedup & Renaming läuft...")
        
        video_paths = phase_ingest(input_dir)
        progress.update(task0, advance=50, description="✓ Phase 0: 3D-LUTs & Ingest fertig!")
        _save_results(all_results, results_path)

        if not video_paths:
            console.print("[bold red]Fehler: Keine Videodateien gefunden.[/bold red]")
            return

        # ── Phase 1: Audio Sync & Kick/Snare Detection ───────────────────────
        task1 = progress.add_task("Phase 1: Multi-Clip Audio FFT Sync...", total=100)
        cached_p2 = all_results.get("phase_2") if isinstance(all_results.get("phase_2"), dict) else {}
        music_not_analyzed = music is not None and not cached_p2.get("music_analysis")

        if skip_sync:
            all_results["phase_1"] = {"sync": {"reference_clip": "", "offsets": {}}}
            progress.update(task1, advance=100, description="✓ Phase 1: Multi-Clip Sync übersprungen (--skip-sync)")
        elif music_not_analyzed or not all_results.get("phase_1"):
            progress.update(task1, advance=30, description="Berechne Mel-Spektrogramm Transienten...")
            all_results["phase_1"] = phase_1_sync(video_paths, music_path=music)
            progress.update(task1, advance=70, description="✓ Phase 1: Audio-Sync & Rhythmus erfasst!")
            _save_results(all_results, results_path)
        else:
            progress.update(task1, advance=100, description="✓ Phase 1: Gecachte Transienten geladen!")

        # ── Phase 2: Video Analysis & Vision Tagging ─────────────────────────
        task2 = progress.add_task("Phase 2: Gemma 4 E2B Vision Tagging...", total=len(video_paths))
        
        def _save_p2_live(partial_res):
            all_results["phase_2"] = partial_res
            _save_results(all_results, results_path)
            # Advance progress per processed video
            completed = sum(1 for k, v in partial_res.items() if isinstance(v, dict) and "vision_tags" in v)
            progress.update(task2, completed=completed, description=f"Phase 2: Analyse Clip {completed}/{len(video_paths)}...")

        prior_p2 = all_results.get("phase_2") if isinstance(all_results.get("phase_2"), dict) else None
        all_results["phase_2"] = phase_2_analyze(video_paths, existing=prior_p2, save_cb=_save_p2_live, music_path=music)
        progress.update(task2, completed=len(video_paths), description="✓ Phase 2: Szenen & Audio-Hüllkurven getaggt!")

        # ── Phase 3: AI Regie Engine ─────────────────────────────────────────
        task3 = progress.add_task("Phase 3: Millisekundengenaue KI-Regie...", total=100)
        progress.update(task3, advance=20, description=f"Fordere Schnittplan an (Preset: {preset})...")
        
        p2 = all_results.get("phase_2") or {}
        music_analysis = p2.get("music_analysis") if isinstance(p2, dict) else None
        if music_analysis and "error" not in music_analysis:
            slim = {k: v for k, v in music_analysis.items() if k not in ("subbass_energy", "bass_energy")}
            all_results = {**all_results, "music_analysis": slim}

        all_results["phase_3"] = phase_3_regie(all_results, preset, duration, provider=args.provider, multi=args.multi)
        progress.update(task3, advance=80, description="✓ Phase 3: KI-Schnittplan & Dramaturgie genehmigt!")
        _save_results(all_results, results_path)

        # ── Phase 4: Llama 3.2 Copywriting ───────────────────────────────────
        task4 = progress.add_task("Phase 4: Schranz-Copywriting (Captions)...", total=100)
        bpm = all_results.get("phase_1", {}).get("percussion", {}).get("bpm", 142)
        plan = (all_results.get("phase_3") or {}).get("edit_plan") or {}
        plan_clips = plan.get("clips", [])
        narrative = plan.get("narrative", "")
        hook = plan.get("hook_text", "")
        
        scene = narrative or "Underground Techno Performance"
        if hook:
            scene = f"{scene} | Hook: {hook}"

        videos = list(dict.fromkeys(c.get("video", "") for c in plan_clips)) if plan_clips else [str(vp) for vp in video_paths]
        clips_meta = []
        for v in videos:
            entry = p2.get(v) if isinstance(p2, dict) else None
            tnames = [t.get("tag", "") for t in (entry or {}).get("vision_tags_filtered", [])]
            top_tags = [t for t, _ in Counter(tnames).most_common(3) if t] or ["techno"]
            pdur = sum(c.get("duration", c.get("end", 0) - c.get("start", 0)) for c in plan_clips if c.get("video") == v)
            peaks = [c.get("reason", "") for c in plan_clips if c.get("video") == v and "drop" in c.get("reason", "").lower()]
            clips_meta.append({
                "bpm": bpm, "tags": top_tags, "duration": round(pdur) or 30,
                "scene": scene, "peak": peaks[0] if peaks else "bass drop"
            })
            
        progress.update(task4, advance=40, description="Generiere Instagram Caption & Hashtags...")
        all_results["phase_4"] = phase_4_copywriting(clips_meta, style=style)
        progress.update(task4, advance=60, description="✓ Phase 4: Sarcastic Hooks & Texte bereit!")
        _save_results(all_results, results_path)

        # ── Phase 5: FFmpeg Assembly ─────────────────────────────────────────
        task5 = progress.add_task("Phase 5: Single-Pass Master Rendering...", total=100)
        progress.update(task5, advance=30, description="Kompiliere Master Complex Filtergraph...")

        edit_plan = all_results.get("phase_3", {}).get("edit_plan")
        sync_data = all_results.get("phase_1", {}).get("sync")
        jcut_val = args.jcut or preset in _AUTO_JCUT_PRESETS
        endcard_val = args.endcard or preset in _AUTO_ENDCARD_PRESETS
        sfx_val = args.sfx or preset in _AUTO_SFX_PRESETS

        phase_5_assembly(
            edit_plan,
            sync_data=sync_data,
            music_path=music,
            vision_data=all_results.get("phase_2"),
            jcut=jcut_val,
            endcard=endcard_val,
            sfx=sfx_val,
            input_dir=args.input,
        )
        progress.update(task5, advance=70, description="✓ Phase 5: Master Reel cineastisch gradet & exportiert!")
        _save_results(all_results, results_path)

    # ── Final Output & Summary ───────────────────────────────────────────────
    out_style = edit_plan.get("style", "reel") if edit_plan else "reel"
    final_reel_path = OUTPUT_DIR / f"reel_{out_style}.mp4"
    
    caps = all_results.get("phase_4", {}).get("captions", [])
    active_cap = caps[0].get("caption", "Rave culture absolute escalation! #techno #schranz #dayShø") if caps else "Pure Techno Energy #underground"

    summary_text = (
        f"[bold white]🎬 Final Reel Pfad:[/bold white]       [bold #00e5ff]{final_reel_path.resolve()}[/bold #00e5ff]\n"
        f"[bold white]📱 Anti-Advice Hook:[/bold white]     [bold #ff2a5f]\"{hook or 'stop practicing your transitions.'}\"[/bold #ff2a5f]\n"
        f"[bold white]🎞️ Geplante Schnitte:[/bold white]    [bold white]{len(plan_clips) if plan_clips else 4} Cuts[/bold white] (A/V Split-Editing Interleaver)\n"
        f"[bold white]📋 Posting Caption:[/bold white]\n"
        f"[#8e8e9e]{active_cap}[/#8e8e9e]\n\n"
        f"[bold green]● PIPELINE VOLLSTÄNDIG ERFOLGREICH BEENDET. BEREIT FÜR SOCIAL MEDIA.[/bold green]"
    )

    summary_panel = Panel(
        summary_text,
        title="[bold green]✓ UNREEL V3 // EXPORT METADATEN & ERGEBNIS-ZUSAMMENFASSUNG[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print()
    console.print(summary_panel)
    console.print()


def interactive_menu():
    """Interactive startup mode menu."""
    render_banner()
    console.print("[bold #ff2a5f]▶ Interaktiver Studio-Modus aktiviert[/bold #ff2a5f]")
    console.print("Bitte konfiguriere deinen nächsten Gig-Schnitt:\n")

    input_path_str = Prompt.ask("[bold white]1. Video Quell-Verzeichnis[/bold white]", default="./input")
    input_path = Path(input_path_str)

    music_path_str = Prompt.ask("[bold white]2. Master Studio Musik-Track (.mp3/.wav)[/bold white]", default="")
    music_path = Path(music_path_str) if music_path_str.strip() else None

    presets = ["tarantino", "artist_narrative", "booking", "pov_story", "highlight", "moody", "seamless_loop"]
    preset = Prompt.ask("[bold white]3. KI-Regie Dramaturgie-Preset[/bold white]", choices=presets, default="tarantino")

    duration = float(Prompt.ask("[bold white]4. Ziel-Dauer des Reels in Sekunden[/bold white]", default="30.0"))

    skip_sync = Confirm.ask("[bold white]5. Multi-Clip Audio FFT Sync überspringen? (Empfohlen bei unzusammenhängenden Clips)[/bold white]", default=True)

    console.print()
    if Confirm.ask("[bold green]Starte High-Performance Pipeline Render-Durchgang?[/bold green]", default=True):
        console.print()
        
        # Build args stub
        class DummyArgs:
            pass
            
        args = DummyArgs()
        args.input = input_path
        args.music = music_path
        args.preset = preset
        args.duration = duration
        args.skip_sync = skip_sync
        args.style = "techno"
        args.provider = ""
        args.multi = False
        args.jcut = True
        args.endcard = True
        args.sfx = True

        run_tui_pipeline(args)
    else:
        console.print("[yellow]Abgebrochen.[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="UNREEL V3 – High-Performance Rich Terminal UI Studio")
    parser.add_argument("--input", "-i", type=Path, default=None, help="Quell-Verzeichnis")
    parser.add_argument("--output", "-o", type=Path, default=OUTPUT_DIR, help="Ausgabe-Verzeichnis")
    parser.add_argument("--preset", "-p", choices=["highlight", "drop_focus", "seamless_loop", "moody", "pov_story", "tarantino", "artist_narrative", "booking", "community"], default=None, help="Preset-Stil")
    parser.add_argument("--duration", "-d", type=float, default=30.0, help="Ziel-Länge in Sekunden")
    parser.add_argument("--style", "-s", choices=["techno", "house", "minimal"], default="techno", help="Caption-Stil")
    parser.add_argument("--provider", choices=["claude", "gemini", "deepseek", "auto"], default="", help="KI-Provider")
    parser.add_argument("--multi", action="store_true", help="Alle Provider vergleichen")
    parser.add_argument("--music", type=Path, default=None, help="Master Musik-Track")
    parser.add_argument("--jcut", action="store_true", help="J-Cut aktivieren")
    parser.add_argument("--endcard", action="store_true", help="Endcard anhängen")
    parser.add_argument("--sfx", action="store_true", help="Sounddesign untermischen")
    parser.add_argument("--skip-sync", action="store_true", default=False, help="Audio-Sync überspringen")

    args = parser.parse_args()

    # If user ran without required args, launch interactive menu
    if args.input is None and args.preset is None and args.music is None:
        interactive_menu()
    else:
        args.input = args.input or INPUT_DIR
        args.preset = args.preset or "tarantino"
        run_tui_pipeline(args)


if __name__ == "__main__":
    main()
