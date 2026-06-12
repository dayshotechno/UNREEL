"""
UNREEL – Text-Backend-Abstraktion (Copywriter)

Selbes Muster wie vision_backends.py, aber für reine TEXT-Modelle
(Dateinamen + Instagram-Captions). Zwei austauschbare Implementierungen:

    - OllamaTextBackend → läuft überall, wo Ollama läuft (alter CPU-Rechner)
    - MLXTextBackend    → Apple Silicon, schnell, via mlx-lm

Umgeschaltet per ENV (TEXT_BACKEND="mlx" | "ollama").

Schnittstelle bewusst minimal: complete(prompt, temperature) -> str.
Das ersetzt das hardcodierte _query_ollama() in copywriter.py.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TextBackend(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        """Schickt `prompt` ans Modell, gibt den (gestrippten) Antworttext zurück."""

    def unload(self) -> None:
        """Optional: Modell aus dem RAM entladen (wichtig auf 16 GB)."""


# ---------------------------------------------------------------------------
# Backend 1: Ollama (Bestand)
# ---------------------------------------------------------------------------

class OllamaTextBackend(TextBackend):
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

    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        try:
            import ollama
        except ImportError:
            logger.warning("ollama package not installed. pip install ollama")
            return ""
        try:
            response = ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.warning("Ollama text error: %s", e)
            return ""


# ---------------------------------------------------------------------------
# Backend 2: MLX-LM (Apple Silicon)
# ---------------------------------------------------------------------------

class MLXTextBackend(TextBackend):
    """
    Text-Generierung via mlx-lm. Modell lazy geladen, unload() gibt RAM frei.

    API-Hinweis (recherchiert): neuere mlx-lm-Versionen nehmen `temperature`
    NICHT mehr direkt in generate(), sondern erwarten einen `sampler`
    (mlx_lm.sample_utils.make_sampler). Wir bauen den Sampler und probieren
    versionsrobust beide Aufruf-Varianten.
    """
    name = "mlx"

    def __init__(self, model: str, max_tokens: int = 256):
        self._model_id = model
        self._max_tokens = max_tokens
        self._model = None
        self._tokenizer = None

    def is_available(self) -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("mlx_lm") is not None
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from mlx_lm import load
        logger.info("Lade MLX-LM Textmodell: %s (einmalig)…", self._model_id)
        self._model, self._tokenizer = load(self._model_id)

    def complete(self, prompt: str, temperature: float = 0.7) -> str:
        from mlx_lm import generate
        self._ensure_loaded()

        # Chat-Template anwenden (alle Instruct-Modelle erwarten das).
        messages = [{"role": "user", "content": prompt}]
        try:
            formatted = self._tokenizer.apply_chat_template(
                messages, add_generation_prompt=True
            )
        except Exception:
            formatted = prompt  # Fallback für Tokenizer ohne Chat-Template

        # Sampler bauen (neuere API). Fällt auf direkten temperature-Call zurück.
        try:
            from mlx_lm.sample_utils import make_sampler
            sampler = make_sampler(temp=temperature)
            try:
                out = generate(self._model, self._tokenizer, prompt=formatted,
                               max_tokens=self._max_tokens, sampler=sampler,
                               verbose=False)
            except TypeError:
                # noch neuere/ältere Signatur ohne 'sampler'-kw
                out = generate(self._model, self._tokenizer, formatted,
                               max_tokens=self._max_tokens, verbose=False)
        except ImportError:
            # sehr alte mlx-lm: temperature direkt
            out = generate(self._model, self._tokenizer, prompt=formatted,
                           max_tokens=self._max_tokens, temp=temperature,
                           verbose=False)

        text = out if isinstance(out, str) else getattr(out, "text", str(out))
        return text.strip()

    def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()
            logger.info("MLX-LM Textmodell entladen, Speicher freigegeben.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_text_backend() -> TextBackend:
    """
    ENV-Keys (Defaults):
        TEXT_BACKEND    = "ollama" | "mlx"                   (default: "ollama")
        MLX_TEXT_MODEL  = "mlx-community/Qwen2.5-7B-Instruct-4bit"
        OLLAMA_HOST, COPYWRITER_MODEL  (für das Ollama-Backend)
    """
    backend = os.environ.get("TEXT_BACKEND", "ollama").lower()

    if backend == "mlx":
        model = os.environ.get(
            "MLX_TEXT_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit"
        )
        return MLXTextBackend(model=model)

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("COPYWRITER_MODEL", "llama3.2")
    return OllamaTextBackend(host=host, model=model)
