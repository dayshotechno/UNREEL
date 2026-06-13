"""
UNREEL V3 – Configuration
All settings loaded from environment variables or .env file.
NEVER hardcode secrets or API keys.
"""

import os
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LUT_DIR = BASE_DIR / "luts"
LUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Ingestion (Phase 0)
# ---------------------------------------------------------------------------
# Source folder ingestion scans (= the pipeline input dir by default).
VIDEO_SOURCE_DIR = INPUT_DIR
# Video and Audio extensions ingestion/the pipeline accept (matched case-insensitively).
SUPPORTED_EXTENSIONS = [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mp3", ".wav", ".flac", ".aiff", ".aif"]

# ---------------------------------------------------------------------------
# Audio Analysis
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100
# V2 analysis modules (audio_analyzer, highlight_engine) reference these names.
AUDIO_SAMPLE_RATE = SAMPLE_RATE  # alias kept for the V2 analyzer modules
HOP_LENGTH = 512                 # librosa STFT/onset hop (≈11.6 ms @ 44.1 kHz)
ENERGY_THRESHOLD_PERCENTILE = 75  # energy-peak gate used by analyze_audio
BASS_FREQ_MAX = 200              # Hz – upper bound of the bass/kick band
BUILDUP_WINDOW_SEC = 4.0         # window for buildup/drop energy ramp detection
MIN_DROP_ENERGY_RATIO = 1.8      # bass energy jump factor that counts as a drop
TEMP_DIR = OUTPUT_DIR            # scratch dir for extracted per-clip audio (.wav)
AUDIO_SYNC_OUTPUT = OUTPUT_DIR / "audio_sync.json"
PERCUSSION_OUTPUT = OUTPUT_DIR / "percussion_map.json"

# ---------------------------------------------------------------------------
# LUT Color Grading
# ---------------------------------------------------------------------------

DEFAULT_LUT = os.environ.get("DEFAULT_LUT", "underground_dark")
AVAILABLE_LUTS = ["underground_dark", "vhs_analog", "neon_nights"]

# ---------------------------------------------------------------------------
# Ollama (Local AI Models)
# ---------------------------------------------------------------------------

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
COPYWRITER_MODEL = os.environ.get("COPYWRITER_MODEL", "llama3.2")

# --- Lokale KI: Backend-Auswahl (ollama | mlx) ---
VISION_BACKEND = os.environ.get("VISION_BACKEND", "ollama")
TEXT_BACKEND   = os.environ.get("TEXT_BACKEND", "ollama")

# --- MLX-Modelle (Apple Silicon) ---
MLX_VISION_MODEL = os.environ.get(
    "MLX_VISION_MODEL", "mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
MLX_TEXT_MODEL   = os.environ.get(
    "MLX_TEXT_MODEL",   "mlx-community/Qwen2.5-7B-Instruct-4bit")
# Optional: Frames pro VLM-Aufruf (nur für multi-image-fähige Modelle > 1 setzen)
MLX_VISION_FRAMES_PER_CALL = int(
    os.environ.get("MLX_VISION_FRAMES_PER_CALL", "1") or 1)

# --- Lokaler Regie-Provider (Opt-in; wird in Phase E benutzt) ---
LOCAL_REGIE_ENGINE = os.environ.get("LOCAL_REGIE_ENGINE", "ollama")  # ollama | mlx
LOCAL_REGIE_MODEL  = os.environ.get("LOCAL_REGIE_MODEL", "qwen3.5:9b")

# ---------------------------------------------------------------------------
# Regie Engine – Multi-Provider AI Configuration
# ---------------------------------------------------------------------------
# Active provider: "claude", "gemini", "deepseek", or "auto"
# "auto" tries providers in order: claude → gemini → deepseek

REGIE_PROVIDER = os.environ.get("REGIE_PROVIDER", "auto")

# --- Anthropic (Claude Fable 5) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-fable-5")

# --- Google Gemini 3.1 Pro ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

# --- DeepSeek V4 Pro ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# Provider priority order for "auto" mode
REGIE_PROVIDER_FALLBACK_ORDER = ["deepseek", "claude", "gemini"]

# ---------------------------------------------------------------------------
# Highlight Scoring Weights (adjusted to include vision)
# ---------------------------------------------------------------------------

WEIGHT_MOTION = 0.25
WEIGHT_AUDIO = 0.25
WEIGHT_SCENE = 0.20
WEIGHT_LIGHT = 0.15
WEIGHT_VISION_TAGS = 0.15

# Vision tag bonus scores
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

# ---------------------------------------------------------------------------
# Export Settings
# ---------------------------------------------------------------------------

REEL_WIDTH = 1080
REEL_HEIGHT = 1920
REEL_FPS = 30
REEL_BITRATE = "4M"
H264_PRESET = "fast"
H264_CRF = 23

# Slow-Mo threshold
SLOW_MO_MOTION_THRESHOLD = 0.8
SLOW_MO_FACTOR = 2.0

# ---------------------------------------------------------------------------
# Vision Engine
# ---------------------------------------------------------------------------

VISION_SAMPLE_INTERVAL = 5  # seconds between frame samples
VISION_BATCH_SIZE = 4
VISION_CONFIDENCE_THRESHOLD = 0.3
