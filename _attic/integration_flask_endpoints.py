"""
UNREEL V3 – Flask API Integration Patches (Multi-Provider)
These are the endpoint additions for your existing Flask app.py.
Copy these routes into your existing application.

Changes from v1:
  - Multi-provider AI regie (Claude, Gemini, DeepSeek)
  - Provider selection via ?provider= query param
  - Multi-provider comparison endpoint
"""


# ---------------------------------------------------------------------------
# GET /api/providers
# List available AI providers and their status.
# ---------------------------------------------------------------------------

"""
@app.route("/api/providers", methods=["GET"])
def api_providers():
    from regie_engine import list_available_providers
    return jsonify({"providers": list_available_providers()})
"""


# ---------------------------------------------------------------------------
# POST /api/sync/compute
# Compute audio sync offsets for all videos in the input directory.
# ---------------------------------------------------------------------------

"""
@app.route("/api/sync/compute", methods=["POST"])
def api_sync_compute():
    from audio_sync import sync_all_clips
    from kick_snare_detector import detect_kicks_snares
    from config import INPUT_DIR, OUTPUT_DIR

    video_paths = sorted([
        str(p) for p in INPUT_DIR.glob("*")
        if p.suffix.lower() in {".mov", ".mp4", ".avi", ".mkv"}
    ])

    if len(video_paths) < 2:
        return jsonify({"error": "Need at least 2 clips for sync"}), 400

    def _run_sync():
        result = sync_all_clips(video_paths, output_path=OUTPUT_DIR / "audio_sync.json")
        percussion = detect_kicks_snares(result.reference_clip)
        percussion.save(OUTPUT_DIR / "percussion_map.json")

    import threading
    thread = threading.Thread(target=_run_sync)
    thread.start()

    return jsonify({"status": "sync_started", "clip_count": len(video_paths)})
"""


# ---------------------------------------------------------------------------
# POST /api/export/ai_reel
# Generate an AI-directed reel using the specified provider.
# ---------------------------------------------------------------------------

"""
@app.route("/api/export/ai_reel", methods=["POST"])
def api_ai_reel():
    from regie_engine import generate_edit_plan, generate_multi_plan
    from config import OUTPUT_DIR

    data = request.json or {}
    duration = data.get("duration", 60)
    style = data.get("style", "highlight")
    target_bpm = data.get("target_bpm", 0)
    provider = data.get("provider", "auto")  # "claude", "gemini", "deepseek", "auto"
    multi = data.get("multi", False)         # Generate from all providers

    analysis_path = OUTPUT_DIR / "pipeline_results.json"
    if not analysis_path.exists():
        return jsonify({"error": "Run analysis first"}), 400

    with open(analysis_path) as f:
        analysis = json.load(f)

    try:
        if multi:
            plans = generate_multi_plan(analysis, preset=style, duration=duration)
            result = {
                name: plan.to_dict()
                for name, plan in plans.items()
            }
            return jsonify({"status": "multi_complete", "plans": result})

        plan = generate_edit_plan(
            analysis,
            preset=style,
            duration=duration,
            target_bpm=target_bpm,
            provider=provider,
            output_path=OUTPUT_DIR / "edit_plan.json",
        )
        return jsonify(plan.to_dict())

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
"""


# ---------------------------------------------------------------------------
# POST /api/captions/generate
# Generate captions for all exported files.
# ---------------------------------------------------------------------------

"""
@app.route("/api/captions/generate", methods=["POST"])
def api_captions_generate():
    from copywriter import batch_process, save_captions
    from config import OUTPUT_DIR

    data = request.json or {}
    style = data.get("style", "techno")

    clips = []
    for p in sorted(OUTPUT_DIR.glob("snippet_*.mp4")):
        clips.append({
            "filename": p.name,
            "tags": ["techno"],
            "bpm": 140,
            "duration": 10,
        })

    if not clips:
        return jsonify({"error": "No exported clips found"}), 400

    results = batch_process(clips, style=style)
    save_captions(results, OUTPUT_DIR / "captions.json")

    return jsonify({"captions": [r.to_dict() for r in results]})
"""
