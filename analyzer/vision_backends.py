"""
UNREEL – Vision-Backend-Abstraktion

Problem (aus dem Audit): vision_engine.py spricht Ollama HARDCODIERT an.
Lösung: eine dünne Backend-Schicht. Dieselbe `tag_frames()`-Schnittstelle,
zwei austauschbare Implementierungen:

    - OllamaVisionBackend  → läuft überall, wo Ollama läuft (alter CPU-Rechner)
    - MLXVisionBackend     → Apple Silicon, schnell, via mlx-vlm

Umgeschaltet wird per config/ENV (VISION_BACKEND="mlx" | "ollama").
So läuft DASSELBE Repo auf beiden Maschinen ohne Fork.

Das Backend bekommt rohe Frames (timestamp, jpeg_bytes) + einen Prompt und
liefert den ROHEN Text der Modellantwort zurück. Das JSON-Parsing/Validieren
bleibt in vision_engine.py (eine Stelle, backend-unabhängig).
"""

from __future__ import annotations

import base64
import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VisionBackend(ABC):
    """Gemeinsame Schnittstelle für alle Vision-Backends."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """True, wenn das Backend einsatzbereit ist (Modell/Dienst vorhanden)."""

    @abstractmethod
    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        """
        Schickt `frames` (Liste aus (timestamp, jpeg_bytes)) zusammen mit
        `prompt` ans Modell und gibt den ROHEN Antworttext zurück.
        """

    def unload(self) -> None:
        """Optional: Modell aus dem RAM entladen (wichtig auf 16 GB)."""


# ---------------------------------------------------------------------------
# Backend 1: Ollama (Bestand – CPU/alte Maschine)
# ---------------------------------------------------------------------------

class OllamaVisionBackend(VisionBackend):
    name = "ollama"

    def __init__(self, host: str, model: str):
        self._host = host
        self._model = model

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import ollama
        images = [base64.b64encode(b).decode("utf-8") for _, b in frames]
        response = ollama.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt, "images": images}],
            options={"temperature": 0.3},
        )
        return response["message"]["content"]


# ---------------------------------------------------------------------------
# Backend 2: MLX-VLM (Apple Silicon)
# ---------------------------------------------------------------------------

class MLXVisionBackend(VisionBackend):
    """
    Vision-Tagging via mlx-vlm (Apple Silicon).
    Modell wird LAZY geladen (erst beim ersten Aufruf) und kann via unload()
    wieder freigegeben werden – entscheidend auf 16 GB unified memory, damit
    danach das Text-/Caption-Modell Platz hat.

    MULTI-IMAGE:
    `frames_per_call` steuert, wie viele Frames pro Modellaufruf gebündelt
    werden. mlx-vlm unterstützt Multi-Image offiziell für Qwen2-VL, Pixtral
    und llava-interleaved. Bei Qwen2.5-VL ist Multi-Image NICHT offiziell
    gelistet – dort lieber bei frames_per_call=1 bleiben oder vorsichtig testen.
    Default 1 = robust für jedes Modell.
    """
    name = "mlx"

    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 512,
        frames_per_call: int = 1,
    ):
        self._model_id = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._frames_per_call = max(1, int(frames_per_call))
        self._model = None
        self._processor = None
        self._config = None

    def is_available(self) -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("mlx_vlm") is not None
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from mlx_vlm import load
        from mlx_vlm.utils import load_config
        logger.info("Lade MLX-VLM Modell: %s (einmalig)…", self._model_id)
        self._model, self._processor = load(self._model_id)
        # config liegt je nach Version am Modell oder via load_config vor.
        self._config = getattr(self._model, "config", None) or load_config(self._model_id)

    def _generate(self, formatted_prompt: str, image_paths: list[str]) -> str:
        """
        Versionsrobuster generate()-Aufruf.

        ACHTUNG: die Argument-Reihenfolge von mlx_vlm.generate() hat sich
        zwischen Versionen geändert:
            ältere:  generate(model, processor, images, prompt, ...)
            neuere:  generate(model, processor, prompt, images, ...)
        Außerdem nehmen neuere Versionen `temperature` NICHT mehr direkt,
        sondern erwarten den Default oder einen sampler. Wir versuchen die
        gängigen Signaturen der Reihe nach.
        """
        from mlx_vlm import generate

        attempts = [
            # neuere Signatur, mit temperature
            lambda: generate(self._model, self._processor, formatted_prompt,
                             image_paths, max_tokens=self._max_tokens,
                             temperature=self._temperature, verbose=False),
            # neuere Signatur, ohne temperature
            lambda: generate(self._model, self._processor, formatted_prompt,
                             image_paths, max_tokens=self._max_tokens, verbose=False),
            # ältere Signatur (images vor prompt)
            lambda: generate(self._model, self._processor, image_paths,
                             formatted_prompt, max_tokens=self._max_tokens, verbose=False),
        ]
        last_err = None
        for call in attempts:
            try:
                out = call()
                # neuere Versionen geben evtl. ein Result-Objekt statt str zurück
                return out if isinstance(out, str) else getattr(out, "text", str(out))
            except TypeError as e:
                last_err = e
                continue
        raise RuntimeError(f"mlx_vlm.generate() Signatur nicht erkannt: {last_err}")

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        """
        Bündelt Frames zu Gruppen der Größe `frames_per_call`, ruft das Modell
        je Gruppe auf und konkateniert die Roh-Antworten. vision_engine.py
        parst danach jede Teil-Antwort (Parsing ist robust gegen mehrere
        JSON-Blöcke).
        """
        import os
        import tempfile
        from mlx_vlm.prompt_utils import apply_chat_template

        self._ensure_loaded()
        out_parts: list[str] = []
        step = self._frames_per_call

        for i in range(0, len(frames), step):
            group = frames[i:i + step]
            tmp_paths: list[str] = []
            try:
                for _, jpeg in group:
                    fd, path = tempfile.mkstemp(suffix=".jpg")
                    with os.fdopen(fd, "wb") as fh:
                        fh.write(jpeg)
                    tmp_paths.append(path)

                index_hint = "\n".join(
                    f"- Image {j + 1}: frame at t={ts:.1f}s"
                    for j, (ts, _) in enumerate(group)
                )
                group_prompt = (
                    f"{prompt}\n\nThe images are provided in this order; "
                    f"use the matching timestamp as the 'time' value:\n{index_hint}"
                )
                formatted = apply_chat_template(
                    self._processor, self._config, group_prompt,
                    num_images=len(tmp_paths),
                )
                out_parts.append(self._generate(formatted, tmp_paths))
            finally:
                for p in tmp_paths:
                    try:
                        os.remove(p)
                    except OSError:
                        pass

        return "\n".join(out_parts)

    def unload(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()  # gibt MLX-GPU-Speicher frei
            logger.info("MLX-VLM Modell entladen, Speicher freigegeben.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Backend 3: Gemini (Cloud – stark & schnell, batch-fähig)
# ---------------------------------------------------------------------------

class GeminiVisionBackend(VisionBackend):
    """
    Vision-Tagging über die Google-Gemini-Cloud (default gemini-2.5-flash).

    Gemini ist nativ multimodal und nimmt mehrere Bilder pro Aufruf entgegen –
    eine ganze Frame-Gruppe geht in EINEM Request raus. Stärker als die lokalen
    Modelle (weniger Fehl-Tags) und auf Cloud-GPUs deutlich schneller als
    CPU/MLX. `response_mime_type=application/json` erzwingt sauberes JSON.

    Privatsphäre-Hinweis: die Frames verlassen den Rechner. Bewusst per
    VISION_BACKEND=gemini opt-in, Default bleibt lokal.
    """
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash",
                 temperature: float = 0.3):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import importlib.util
            return importlib.util.find_spec("google.generativeai") is not None
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(
            model_name=self._model,
            generation_config=genai.types.GenerationConfig(
                temperature=self._temperature,
                response_mime_type="application/json",
            ),
        )
        # One request: prompt text followed by all frames as inline JPEG blobs.
        parts: list = [prompt]
        for _, jpeg in frames:
            parts.append({"mime_type": "image/jpeg", "data": jpeg})

        response = model.generate_content(parts)
        return response.text


# ---------------------------------------------------------------------------
# Backend 4: Claude (Cloud – Fallback, ebenfalls multimodal)
# ---------------------------------------------------------------------------

class ClaudeVisionBackend(VisionBackend):
    """
    Vision-Tagging über Anthropic Claude. Fallback/Alternative zu Gemini.
    Das Modell muss Bild-Input unterstützen (Claude-Vision-fähige Modelle).
    Fable 5 may emit a thinking block first, so only text blocks are read.
    """
    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-fable-5",
                 temperature: float = 0.3, max_tokens: int = 2048):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import importlib.util
            return importlib.util.find_spec("anthropic") is not None
        except Exception:
            return False

    def describe_frames(self, prompt: str, frames: list[tuple[float, bytes]]) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        content: list = []
        for _, jpeg in frames:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.b64encode(jpeg).decode("utf-8"),
                },
            })
        content.append({"type": "text", "text": prompt})

        params = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": content}],
            temperature=self._temperature,
        )
        try:
            response = client.messages.create(**params)
        except anthropic.BadRequestError as exc:
            if "temperature" in str(exc).lower():
                params.pop("temperature", None)
                response = client.messages.create(**params)
            else:
                raise
        return "".join(
            b.text for b in response.content
            if getattr(b, "type", None) == "text"
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_vision_backend() -> VisionBackend:
    """
    Wählt das Backend nach config/ENV.

    Erwartete config/ENV-Keys (mit Defaults):
        VISION_BACKEND   = "ollama" | "mlx" | "gemini" | "claude"  (default: "ollama")
        MLX_VISION_MODEL = z.B. "mlx-community/Qwen2.5-VL-7B-Instruct-4bit"
        OLLAMA_HOST, GEMMA_MODEL          (für das Ollama-Backend)
        GEMINI_API_KEY, GEMINI_VISION_MODEL  (default: gemini-2.5-flash)
        ANTHROPIC_API_KEY, CLAUDE_VISION_MODEL
    """
    backend = os.environ.get("VISION_BACKEND", "ollama").lower()

    if backend == "gemini":
        key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("GEMINI_VISION_MODEL", "gemini-2.5-flash")
        return GeminiVisionBackend(api_key=key, model=model)

    if backend == "claude":
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        model = os.environ.get("CLAUDE_VISION_MODEL", "claude-fable-5")
        return ClaudeVisionBackend(api_key=key, model=model)

    if backend == "mlx":
        model = os.environ.get(
            "MLX_VISION_MODEL",
            "mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
        )
        # frames_per_call=1 ist der sichere Default. Für offiziell multi-image-
        # fähige Modelle (Qwen2-VL, Pixtral, llava-interleaved) kann man via
        # MLX_VISION_FRAMES_PER_CALL z.B. 4 setzen → weniger Aufrufe, schneller.
        fpc = int(os.environ.get("MLX_VISION_FRAMES_PER_CALL", "1") or 1)
        return MLXVisionBackend(model=model, frames_per_call=fpc)

    # Default: Ollama
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("GEMMA_MODEL", "gemma4:e2b")
    return OllamaVisionBackend(host=host, model=model)
