"""Registry of every model the SDK knows about, plus mode metadata.

Adding a new model is a one-line dict entry — no other code changes needed.
"""
from __future__ import annotations

from .prompts import (
    GENERAL_PROMPT,
    QGIS_PROMPT,
    SATELLITE_PROMPT,
    CHANGE_PROMPT,
    PARSER_PROMPT,
)


MODELS: dict[str, dict] = {
    "gemini-2.5-flash": {
        "provider": "gemini", "vision": True, "label": "Gemini 2.5 Flash"},
    "gemini-2.5-pro": {
        "provider": "gemini", "vision": True, "label": "Gemini 2.5 Pro"},
    "llama-3.3-70b-versatile": {
        "provider": "groq", "vision": False, "label": "Groq Llama 3.3 70B"},
    "llama-3.1-8b-instant": {
        "provider": "groq", "vision": False, "label": "Groq Llama 3.1 8B"},
    "meta-llama/llama-3.3-70b-instruct:free": {
        "provider": "openrouter", "vision": False, "label": "OR Llama 3.3 70B (free)"},
    "qwen/qwen-2-vl-7b-instruct:free": {
        "provider": "openrouter", "vision": True, "label": "OR Qwen2-VL 7B (free)"},
    "mistralai/mistral-7b-instruct:free": {
        "provider": "openrouter", "vision": False, "label": "OR Mistral 7B (free)"},
}

PROVIDER_KEY: dict[str, str] = {
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

DEFAULT_MODEL_FOR_PROVIDER: dict[str, str] = {
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
}

# Default model per mode (the SDK picks this if caller doesn't override)
DEFAULT_MODEL_FOR_MODE: dict[str, str] = {
    "chat": "gemini-2.5-flash",
    "qgis": "gemini-2.5-flash",
    "analyze_image": "gemini-2.5-flash",
    "detect_changes": "gemini-2.5-flash",
    "parse_address": "gemini-2.5-flash",
}

MODES: dict[str, dict] = {
    "General GIS": {"system": GENERAL_PROMPT, "kind": "chat", "vision": False},
    "QGIS Generator": {"system": QGIS_PROMPT, "kind": "task_to_code", "vision": False},
    "Satellite Q&A": {"system": SATELLITE_PROMPT, "kind": "image_chat", "vision": True},
    "Change Detection": {"system": CHANGE_PROMPT, "kind": "two_image", "vision": True},
    "Address Parser": {"system": PARSER_PROMPT, "kind": "text_to_json", "vision": False},
    "Benchmark": {"system": GENERAL_PROMPT, "kind": "benchmark", "vision": False},
}

MODE_DESCRIPTIONS: dict[str, str] = {
    "General GIS": "Free-form chat with an EPSG-aware GIS expert.",
    "QGIS Generator": "Describe a task → get a PyQGIS script. Auto-flags deprecated APIs and missing CRS.",
    "Satellite Q&A": "Upload an image and ask questions about it. Vision-capable models only.",
    "Change Detection": "Upload BEFORE + AFTER → one-shot change analysis.",
    "Address Parser": "Messy Egyptian (Arabic/English) address → structured JSON. Streaming OFF.",
    "Benchmark": "Sends 3 fixed prompts to all providers. Use this output in DESIGN.md.",
}

SAMPLE_INPUTS: dict[str, str] = {
    "General GIS": "What's the most appropriate projected CRS for measuring areas in the Nile Delta? Justify briefly.",
    "QGIS Generator": (
        "I have two layers loaded in QGIS:\n"
        "- 'roads' (line layer)\n"
        "- 'parcels' (polygon layer)\n\n"
        "Buffer the roads by 50 meters, then find all parcels that intersect "
        "with the buffer. Create a new memory layer called 'affected_parcels' "
        "with the result and add it to the project."
    ),
    "Satellite Q&A": "What land cover types do you see in this image? Estimate percentages.",
    "Change Detection": CHANGE_PROMPT,
    "Address Parser": "12 شارع جامعة الدول العربية، المهندسين، الجيزة",
}

# Public NASA / USGS satellite imagery suitable for vision demos
SAMPLE_IMAGES: dict[str, str] = {
    "Nile Delta (NASA Landsat)": (
        "https://eoimages.gsfc.nasa.gov/images/imagerecords/89000/89656/"
        "niledelta_oli_2017006_lrg.jpg"
    ),
    "Sahara dunes (NASA)": (
        "https://eoimages.gsfc.nasa.gov/images/imagerecords/146000/146353/"
        "ubarisanddune_iss068_lrg.jpg"
    ),
    "Cairo urban sprawl (NASA)": (
        "https://eoimages.gsfc.nasa.gov/images/imagerecords/146000/146120/"
        "cairo_oli_2019357_lrg.jpg"
    ),
}
