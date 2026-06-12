"""
UNREEL – Lokaler Regie-Provider (zusätzliche Option, Cloud bleibt Default)

Fügt der regie_engine einen vierten Provider `local` hinzu, der dem
bestehenden RegieProvider-Protocol entspricht
(name, model_id, is_available(), call(...)).

ZWEI BACKENDS, per ENV wählbar (LOCAL_REGIE_ENGINE):

  "ollama" (Default) – nutzt Ollamas eingebautes `format=<json-schema>`
                       (XGrammar). Braucht laufenden Ollama-Dienst + Modell.

  "mlx"             – reines mlx-lm via `outlines` (from_mlxlm + output_type).
                      KEIN Ollama nötig. Outlines erzwingt schema-konformes JSON
                      durch constrained decoding (Schema→Regex→Token-Masking).

Hintergrund: Die Regie ist die anspruchsvollste KI-Aufgabe (langer JSON-Input +
Reasoning + striktes JSON-Output). Kleine lokale Modelle liefern OHNE
Schema-Constraint unzuverlässiges JSON. Beide Backends erzwingen daher gültiges
JSON – das lokale Äquivalent zum `response_format={"type":"json_object"}` des
DeepSeek-Providers.

ENV/config:
    LOCAL_REGIE_ENGINE  = "ollama" | "mlx"   (default: "ollama")
    LOCAL_REGIE_MODEL   = je nach Engine:
                            ollama: "qwen3.5:9b"
                            mlx:    "mlx-community/Qwen2.5-7B-Instruct-4bit"
    OLLAMA_HOST         (nur für ollama-Engine; bereits vorhanden)
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

# --- EditPlan-Schema (JSON-Schema-Dict, für die Ollama-Engine) --------------
# Felder matchen EditClip/EditPlan der regie_engine exakt.
EDIT_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "video": {"type": "string"},
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "transition": {"type": "string"},
                    "reason": {"type": "string"},
                    "crop": {"type": "string"},
                    "lut": {"type": "string"},
                    "vfx": {"type": "string"},
                    "slow_mo": {"type": "boolean"},
                    "slow_mo_factor": {"type": "number"},
                    "phase": {"type": "string"},
                },
                "required": ["video", "start", "end"],
            },
        },
        "narrative": {"type": "string"},
        "hook_text": {"type": "string"},
        "total_duration": {"type": "number"},
    },
    "required": ["clips"],
}


def _default_model(engine: str) -> str:
    if engine == "mlx":
        return os.environ.get(
            "LOCAL_REGIE_MODEL", "mlx-community/Qwen2.5-7B-Instruct-4bit"
        )
    return os.environ.get("LOCAL_REGIE_MODEL", "qwen3.5:9b")


class LocalMLXProvider:
    """
    Lokaler Regie-Provider. Backend (ollama|mlx) per ENV LOCAL_REGIE_ENGINE.
    Erfüllt dasselbe Protocol wie ClaudeProvider/DeepSeekProvider.
    """

    def __init__(self, model: str | None = None, engine: str | None = None,
                 host: str | None = None):
        self._engine = (engine or os.environ.get("LOCAL_REGIE_ENGINE", "ollama")).lower()
        self._model = model or _default_model(self._engine)
        self._host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self._mlx_model = None      # lazy (nur mlx-Engine)
        self._mlx_tokenizer = None

    @property
    def name(self) -> str:
        return "local"

    @property
    def model_id(self) -> str:
        return self._model

    # ---- Verfügbarkeit -----------------------------------------------------
    def is_available(self) -> bool:
        if self._engine == "mlx":
            return self._mlx_available()
        return self._ollama_available()

    def _ollama_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status != 200:
                    return False
                tags = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return False
        names = [m.get("name", "") for m in tags.get("models", [])]
        base = self._model.split(":")[0]
        return any(n == self._model or n.startswith(base) for n in names)

    def _mlx_available(self) -> bool:
        try:
            import importlib.util
            return (importlib.util.find_spec("mlx_lm") is not None
                    and importlib.util.find_spec("outlines") is not None)
        except Exception:
            return False

    # ---- Aufruf ------------------------------------------------------------
    def call(self, system_prompt: str, user_data: str,
             temperature: float = 0.4, max_tokens: int = 8192) -> str:
        if self._engine == "mlx":
            return self._call_mlx(system_prompt, user_data, temperature, max_tokens)
        return self._call_ollama(system_prompt, user_data, temperature, max_tokens)

    def _call_ollama(self, system_prompt, user_data, temperature, max_tokens) -> str:
        try:
            import ollama
        except ImportError:
            raise ImportError("ollama not installed. Run: pip install ollama")

        logger.info("  → Calling %s (local/ollama, schema-constrained)…", self._model)
        client = ollama.Client(host=self._host)
        response = client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data},
            ],
            format=EDIT_PLAN_SCHEMA,
            options={"temperature": temperature, "num_predict": max_tokens,
                     "num_ctx": 8192},
        )
        return response["message"]["content"]

    def _call_mlx(self, system_prompt, user_data, temperature, max_tokens) -> str:
        """
        Reines mlx-lm via outlines. Erzwingt EditPlan-konformes JSON ohne Ollama.
        Outlines nimmt ein Pydantic-Modell als output_type; wir bauen es einmal.
        """
        try:
            import mlx_lm
            import outlines
        except ImportError:
            raise ImportError(
                "mlx engine needs: pip install \"outlines[mlxlm]\" mlx-lm"
            )

        logger.info("  → Calling %s (local/mlx via outlines, schema-constrained)…",
                    self._model)

        if self._mlx_model is None:
            self._mlx_model = outlines.from_mlxlm(*mlx_lm.load(self._model))

        # Pydantic-Schema für outlines (entspricht EDIT_PLAN_SCHEMA).
        from pydantic import BaseModel, Field

        class _EditClip(BaseModel):
            video: str
            start: float
            end: float
            transition: str = "cut"
            reason: str = ""
            crop: str = "9:16"
            lut: str = "underground_dark"
            vfx: str = "none"
            slow_mo: bool = False
            slow_mo_factor: float = 1.0
            phase: str = ""

        class _EditPlan(BaseModel):
            clips: list[_EditClip]
            narrative: str = ""
            hook_text: str = ""
            total_duration: float = 0.0

        # Chat-artiger Prompt: System + Daten in einen String (mlx-lm Tokenizer
        # mit Chat-Template wäre schöner, aber outlines nimmt hier den Prompt).
        prompt = f"{system_prompt}\n\n{user_data}\n\nReturn ONLY the JSON edit plan."
        result = self._mlx_model(prompt, output_type=_EditPlan,
                                 max_tokens=max_tokens)
        # outlines liefert bereits einen JSON-String (schema-konform).
        return result if isinstance(result, str) else json.dumps(result)

    def unload(self) -> None:
        self._mlx_model = None
        self._mlx_tokenizer = None
        try:
            import gc
            import mlx.core as mx
            gc.collect()
            mx.clear_cache()
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    p = LocalMLXProvider()
    print(f"name={p.name} engine={p._engine} model={p.model_id}")
    print(f"available={p.is_available()}")
    print(f"schema keys={list(EDIT_PLAN_SCHEMA['properties'])}")
