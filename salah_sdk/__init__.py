"""Salah SDK — a unified Python client for GIS-flavored LLM calls.

>>> from salah_sdk import SalahClient
>>> client = SalahClient(gemini_key="...", groq_key="...")
>>> client.chat("What's the EPSG for Egypt?")
'EPSG:22992 (Egypt Red Belt) ...'

The SDK wraps three providers (Gemini · Groq · OpenRouter) behind one client
and ships six GIS-specific methods:

  chat(prompt, ...)            -> free-form text answer
  qgis(task, ...)              -> a PyQGIS script
  analyze_image(img, q, ...)   -> satellite image analysis (vision)
  detect_changes(a, b, q)      -> before/after pair analysis (vision)
  parse_address(text, ...)     -> structured JSON of an Egyptian address
  benchmark(prompt, ...)       -> {model_id: BenchResult} across providers

Every method accepts `stream=True` to get an `Iterator[str]` instead of a
string. Every method accepts `model=` to override the default. Errors are
raised as `SalahError` subclasses.
"""

from .client import SalahClient
from .errors import SalahError, MissingKey, ProviderError
from .models import MODELS, MODES, PROVIDER_KEY, MODE_DESCRIPTIONS, SAMPLE_INPUTS
from .prompts import (
    GENERAL_PROMPT,
    QGIS_PROMPT,
    SATELLITE_PROMPT,
    CHANGE_PROMPT,
    PARSER_PROMPT,
    PARSER_SCHEMA,
)

__version__ = "0.1.0"

__all__ = [
    "SalahClient",
    "SalahError",
    "MissingKey",
    "ProviderError",
    "MODELS",
    "MODES",
    "PROVIDER_KEY",
    "MODE_DESCRIPTIONS",
    "SAMPLE_INPUTS",
    "GENERAL_PROMPT",
    "QGIS_PROMPT",
    "SATELLITE_PROMPT",
    "CHANGE_PROMPT",
    "PARSER_PROMPT",
    "PARSER_SCHEMA",
    "__version__",
]
