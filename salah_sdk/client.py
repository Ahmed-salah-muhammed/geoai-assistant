"""SalahClient — the public façade of the Salah SDK.

One class, six methods, three providers. Pure Python — Streamlit-agnostic.

Example:
    >>> from salah_sdk import SalahClient
    >>> client = SalahClient.from_env()           # reads GOOGLE_API_KEY etc.
    >>> client.chat("What's the EPSG for Cairo?")
    'EPSG:22992 (Egypt Red Belt)...'
    >>> for chunk in client.chat("Stream me", stream=True):
    ...     print(chunk, end="")
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Iterator

from PIL import Image

from ._providers import call_gemini, call_openai_compat
from .errors import UnknownModel, VisionNotSupported
from .models import (
    DEFAULT_MODEL_FOR_MODE,
    MODELS,
    PROVIDER_KEY,
)
from .prompts import (
    GENERAL_PROMPT,
    PARSER_PROMPT,
    PARSER_SCHEMA,
    QGIS_PROMPT,
    SATELLITE_PROMPT,
)


@dataclass
class BenchResult:
    """One row in a benchmark run."""
    model: str
    label: str
    latency_s: float
    word_count: int
    response: str
    error: str | None = None


@dataclass
class SalahClient:
    """Unified client for Gemini · Groq · OpenRouter with GIS-specific methods.

    Keys are resolved at construction time. You can also pass them later
    via attribute assignment.
    """
    gemini_key: str = ""
    groq_key: str = ""
    openrouter_key: str = ""
    default_temperature: float = 0.3
    call_counts: dict[str, int] = field(default_factory=lambda: {
        "gemini": 0, "groq": 0, "openrouter": 0,
    })

    # ────────────────────────────────────────────────────────────────────
    # Construction helpers
    # ────────────────────────────────────────────────────────────────────
    @classmethod
    def from_env(cls, **overrides) -> "SalahClient":
        """Build a client from `GOOGLE_API_KEY` / `GROQ_API_KEY` /
        `OPENROUTER_API_KEY` environment variables. Overrides win."""
        return cls(
            gemini_key=overrides.pop("gemini_key", os.environ.get("GOOGLE_API_KEY", "")),
            groq_key=overrides.pop("groq_key", os.environ.get("GROQ_API_KEY", "")),
            openrouter_key=overrides.pop("openrouter_key", os.environ.get("OPENROUTER_API_KEY", "")),
            **overrides,
        )

    # ────────────────────────────────────────────────────────────────────
    # Core call — every method funnels through here
    # ────────────────────────────────────────────────────────────────────
    def _key_for(self, provider: str) -> str:
        return {
            "gemini": self.gemini_key,
            "groq": self.groq_key,
            "openrouter": self.openrouter_key,
        }[provider]

    def _resolve_model(self, model: str | None, mode_key: str,
                       require_vision: bool = False) -> str:
        m = model or DEFAULT_MODEL_FOR_MODE.get(mode_key, "gemini-2.5-flash")
        if m not in MODELS:
            raise UnknownModel(f"Unknown model '{m}'. Known: {list(MODELS)}")
        if require_vision and not MODELS[m]["vision"]:
            raise VisionNotSupported(
                f"Model '{m}' is text-only. Pick a vision model "
                f"(gemini-*, qwen/qwen-2-vl-7b-instruct:free)."
            )
        return m

    def _call(self, model_id, system, history, user_msg, temperature,
              images=None, stream=True, json_mode=False) -> Iterator[str]:
        provider = MODELS[model_id]["provider"]
        self.call_counts[provider] += 1
        if provider == "gemini":
            return call_gemini(self.gemini_key, model_id, system, history,
                               user_msg, temperature, images, stream, json_mode)
        return call_openai_compat(
            provider, self._key_for(provider), model_id, system, history,
            user_msg, temperature, images, stream, json_mode,
        )

    # ────────────────────────────────────────────────────────────────────
    # Public methods — one per mode
    # ────────────────────────────────────────────────────────────────────
    def chat(self, prompt: str, *, model: str | None = None,
             system: str = GENERAL_PROMPT, history: list[dict] | None = None,
             temperature: float | None = None, stream: bool = False) -> str | Iterator[str]:
        """Free-form GIS chat.

        history items: ``[{"role": "user"|"assistant", "content": str}, ...]``
        Returns a string if ``stream=False``, else an Iterator[str].
        """
        m = self._resolve_model(model, "chat")
        t = self.default_temperature if temperature is None else temperature
        it = self._call(m, system, history or [], prompt, t, stream=stream)
        return it if stream else "".join(it)

    def qgis(self, task: str, *, model: str | None = None,
             temperature: float = 0.2, stream: bool = False) -> str | Iterator[str]:
        """Turn a task description into a PyQGIS script. Code fences stripped."""
        m = self._resolve_model(model, "qgis")
        it = self._call(m, QGIS_PROMPT, [], task, temperature, stream=stream)
        if stream:
            return it
        code = "".join(it)
        return re.sub(r"^```(?:python)?\s*|\s*```$", "", code.strip(),
                      flags=re.MULTILINE)

    def analyze_image(self, image: Image.Image, question: str, *,
                      model: str | None = None,
                      system: str = SATELLITE_PROMPT,
                      temperature: float | None = None,
                      stream: bool = False) -> str | Iterator[str]:
        """Ask a vision model about a single image."""
        m = self._resolve_model(model, "analyze_image", require_vision=True)
        t = self.default_temperature if temperature is None else temperature
        it = self._call(m, system, [], question, t, images=[image], stream=stream)
        return it if stream else "".join(it)

    def detect_changes(self, before: Image.Image, after: Image.Image,
                       question: str = "Identify changes between BEFORE and AFTER.", *,
                       model: str | None = None, temperature: float = 0.2,
                       stream: bool = False) -> str | Iterator[str]:
        """One-shot change-detection on a before/after pair."""
        m = self._resolve_model(model, "detect_changes", require_vision=True)
        it = self._call(m, SATELLITE_PROMPT, [], question, temperature,
                        images=[before, after], stream=stream)
        return it if stream else "".join(it)

    def parse_address(self, address: str, *, model: str | None = None,
                      temperature: float = 0.1) -> dict:
        """Parse a messy Arabic/English Egyptian address into structured JSON.

        Streaming is intentionally disabled: partial JSON is never valid.
        """
        m = self._resolve_model(model, "parse_address")
        user_msg = f"Address: {address}\n\nReturn JSON with this schema:\n{PARSER_SCHEMA}"
        raw = "".join(self._call(m, PARSER_PROMPT, [], user_msg, temperature,
                                 stream=False, json_mode=True))
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(),
                             flags=re.MULTILINE).strip()
            return json.loads(cleaned)  # raises if still bad — let it propagate

    def benchmark(self, prompt: str, *, models: list[str] | None = None,
                  system: str = GENERAL_PROMPT,
                  temperature: float = 0.3) -> list[BenchResult]:
        """Run the same prompt across a list of models. Default = one per provider."""
        if models is None:
            models = ["gemini-2.5-flash",
                      "llama-3.3-70b-versatile",
                      "meta-llama/llama-3.3-70b-instruct:free"]
        results: list[BenchResult] = []
        for mid in models:
            self._resolve_model(mid, "chat")  # validates
            label = MODELS[mid]["label"]
            start = time.time()
            try:
                text = "".join(self._call(mid, system, [], prompt, temperature, stream=False))
                err: str | None = None
            except Exception as exc:
                text = ""
                err = f"{type(exc).__name__}: {exc}"
            results.append(BenchResult(
                model=mid, label=label,
                latency_s=round(time.time() - start, 2),
                word_count=len(text.split()),
                response=text or (err or ""), error=err,
            ))
        return results

    # ────────────────────────────────────────────────────────────────────
    # Introspection helpers
    # ────────────────────────────────────────────────────────────────────
    def configured_providers(self) -> dict[str, bool]:
        """Return {provider_name: has_key} for each provider."""
        return {
            "gemini": bool(self.gemini_key),
            "groq": bool(self.groq_key),
            "openrouter": bool(self.openrouter_key),
        }
