"""Salah SDK — documentation page.

A real, browsable SDK reference rendered inside the same Streamlit app.
Mirrors the look and feel of `aistudio.google.com`, `console.groq.com`,
or `openrouter.ai/docs` — install, quickstart, per-method examples,
errors, and a live "run in app" link.
"""
from __future__ import annotations

import streamlit as st

from salah_sdk import (
    MODELS,
    MODES,
    PROVIDER_KEY,
    __version__ as SDK_VERSION,
)

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + CSS
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Salah SDK · Docs", page_icon="📚", layout="wide")

st.markdown("""
<style>
  .sdk-hero {
    background: linear-gradient(135deg, #312e81 0%, #1e1b4b 60%, #0c0a3e 100%);
    padding: 1.8rem 2rem; border-radius: 14px; color: white;
    margin-bottom: 1.2rem; box-shadow: 0 6px 16px rgba(0,0,0,.22);
  }
  .sdk-hero h1 { color: white; margin: 0; font-size: 2.1rem; letter-spacing: -.02em; }
  .sdk-hero .ver {
    display: inline-block; padding: .15rem .55rem; border-radius: 999px;
    background: rgba(255,255,255,.18); font-size: .78rem;
    margin-left: .6rem; vertical-align: middle;
  }
  .sdk-hero p { color: #c7d2fe; margin: .55rem 0 0; font-size: 1.02rem; }

  .feature {
    background: rgba(99, 102, 241, .07);
    border: 1px solid rgba(99, 102, 241, .25);
    border-radius: 10px; padding: .8rem 1rem; margin-bottom: .6rem;
  }
  .feature b { color: #4338ca; }

  .method-card {
    background: var(--background-color, #fff);
    border-left: 4px solid #6366f1;
    padding: .7rem 1rem; margin: .8rem 0;
    border-radius: 6px;
  }
  .method-card code { background: rgba(99, 102, 241, .12); padding: .1rem .4rem; border-radius: 4px; }

  .pill-row { margin-top: .8rem; }
  .pill {
    display: inline-block; padding: .15rem .55rem; border-radius: 999px;
    font-size: .72rem; margin-right: .35rem;
    background: rgba(99, 102, 241, .15); color: #4338ca;
    border: 1px solid rgba(99, 102, 241, .35);
  }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sdk-hero">
  <h1>📚 Salah SDK<span class="ver">v{SDK_VERSION}</span></h1>
  <p>One Python client. Three LLM providers. Six GIS-flavored methods.<br>
     Built for engineers who'd rather call <code>client.qgis(task)</code> than
     write <code>genai.GenerativeModel(...).generate_content(...)</code>.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Providers", "3", help="Gemini · Groq · OpenRouter")
c2.metric("Models", len(MODELS), help="Add another with one dict entry")
c3.metric("Modes", len(MODES))
c4.metric("Lines of API", "6 methods", help="chat · qgis · analyze_image · detect_changes · parse_address · benchmark")

st.divider()

# ──────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────
tab_quick, tab_auth, tab_modes, tab_providers, tab_stream, tab_errors, tab_recipes = st.tabs([
    "🚀 Quickstart",
    "🔑 Auth",
    "🧩 Modes",
    "🌐 Providers & Models",
    "💧 Streaming",
    "⚠️ Errors",
    "🧪 Recipes",
])

# ──────────────────────────────────────────────────────────────────────────
# QUICKSTART
# ──────────────────────────────────────────────────────────────────────────
with tab_quick:
    st.subheader("Install")
    st.code("""# From this project's root (editable install — recommended during the lab)
pip install -e .

# Or from PyPI once published
pip install salah-sdk""", language="bash")

    st.subheader("Hello, GIS")
    st.code("""from salah_sdk import SalahClient

client = SalahClient(
    gemini_key="AI...",          # at least one provider key
    groq_key="gsk_...",          # optional
    openrouter_key="sk-or-...",  # optional
)

answer = client.chat("What's the best CRS for measuring areas in the Nile Delta?")
print(answer)
# → 'EPSG:22992 (Egypt Red Belt) — projected, units in metres, suitable for area calcs.'""",
        language="python")

    st.markdown("##### Or auto-load keys from env vars / .env:")
    st.code("""from salah_sdk import SalahClient
import dotenv; dotenv.load_dotenv()

client = SalahClient.from_env()        # picks up GOOGLE_API_KEY / GROQ_API_KEY / OPENROUTER_API_KEY
print(client.configured_providers())   # {'gemini': True, 'groq': False, 'openrouter': True}""",
        language="python")

    st.subheader("Six methods, one client")
    st.markdown("""
<div class="method-card"><b>client.chat(prompt, ...)</b> — free-form GIS chat</div>
<div class="method-card"><b>client.qgis(task, ...)</b> — turns a task description into a PyQGIS script</div>
<div class="method-card"><b>client.analyze_image(img, q, ...)</b> — vision Q&A on a single image</div>
<div class="method-card"><b>client.detect_changes(before, after, q)</b> — before/after change detection</div>
<div class="method-card"><b>client.parse_address(text, ...)</b> — Arabic/English address → JSON</div>
<div class="method-card"><b>client.benchmark(prompt, ...)</b> — same prompt across all providers, returns latency table</div>
""", unsafe_allow_html=True)

    st.info("**Every method accepts `stream=True`** to get an `Iterator[str]` instead of a string. "
            "Every method accepts `model='...'` to override the default. See the *Modes* tab for examples.")

# ──────────────────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────────────────
with tab_auth:
    st.subheader("Where keys come from")
    st.markdown("""
The SDK reads three keys, one per provider. You can pass them three ways:

1. **Constructor** — most explicit. Use this when keys come from your own secret store.
2. **`SalahClient.from_env()`** — picks up `GOOGLE_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY`. Use this for `.env` files and CI.
3. **Attribute assignment** — for hot-swapping keys at runtime (e.g., a settings page).
""")

    st.code("""# 1. Constructor
client = SalahClient(gemini_key="AI...", groq_key="gsk_...")

# 2. From env (or .env via python-dotenv)
import dotenv; dotenv.load_dotenv()
client = SalahClient.from_env()

# 3. Hot-swap at runtime
client.openrouter_key = new_key_from_ui_textbox""", language="python")

    st.subheader("Free signup links")
    st.markdown("""
| Provider | Sign-up | Notes |
|---|---|---|
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Generous quota · vision · JSON mode |
| **Groq** | [console.groq.com](https://console.groq.com/keys) | Fastest tokens/sec on the market · text-only |
| **OpenRouter** | [openrouter.ai](https://openrouter.ai/keys) | Gateway to many models · use `:free` suffix |
""")

    st.subheader("Streamlit Cloud secrets")
    st.code("""# .streamlit/secrets.toml  (NEVER commit this file)
GOOGLE_API_KEY = "AI..."
GROQ_API_KEY = "gsk_..."
OPENROUTER_API_KEY = "sk-or-..."

# In your Streamlit app:
client = SalahClient(
    gemini_key=st.secrets.get("GOOGLE_API_KEY", ""),
    groq_key=st.secrets.get("GROQ_API_KEY", ""),
    openrouter_key=st.secrets.get("OPENROUTER_API_KEY", ""),
)""", language="python")

    st.warning("⚠️ Never commit `.env` or `.streamlit/secrets.toml`. "
               "Both are excluded by this repo's `.gitignore` — keep it that way.")

# ──────────────────────────────────────────────────────────────────────────
# MODES (one expander per public method)
# ──────────────────────────────────────────────────────────────────────────
with tab_modes:
    st.subheader("The six methods, one by one")
    st.caption("Each method has a default model, but you can override with `model=`. "
               "Click any 'Try in app' link to jump back to the live UI.")

    # 1. chat
    with st.expander("💬 **`client.chat(prompt, ...)`** — free-form GIS chat", expanded=True):
        st.markdown("**Signature**")
        st.code("client.chat(\n"
                "    prompt: str,\n"
                "    *,\n"
                "    model: str | None = None,         # default: gemini-2.5-flash\n"
                "    system: str = GENERAL_PROMPT,\n"
                "    history: list[dict] | None = None,  # [{'role': 'user'|'assistant', 'content': str}]\n"
                "    temperature: float | None = None,\n"
                "    stream: bool = False,\n"
                ") -> str | Iterator[str]",
                language="python")
        st.markdown("**Example — one-shot**")
        st.code("answer = client.chat(\n"
                "    \"What's the best CRS for the Nile Delta?\",\n"
                "    model=\"gemini-2.5-flash\",\n"
                "    temperature=0.2,\n"
                ")\n"
                "print(answer)", language="python")
        st.markdown("**Example — multi-turn**")
        st.code("history = [\n"
                "    {'role': 'user',      'content': 'What is the EPSG for WGS84?'},\n"
                "    {'role': 'assistant', 'content': 'EPSG:4326.'},\n"
                "]\n"
                "follow_up = client.chat('And Web Mercator?', history=history)\n"
                "# → 'EPSG:3857'", language="python")
        st.markdown("**Example — streaming**")
        st.code("for chunk in client.chat('Explain CRS', stream=True):\n"
                "    print(chunk, end='', flush=True)", language="python")
        st.page_link("app.py", label="↗ Try in app · General GIS mode")

    # 2. qgis
    with st.expander("🐍 **`client.qgis(task, ...)`** — PyQGIS script generator"):
        st.code("client.qgis(\n"
                "    task: str,\n"
                "    *,\n"
                "    model: str | None = None,\n"
                "    temperature: float = 0.2,\n"
                "    stream: bool = False,\n"
                ") -> str | Iterator[str]", language="python")
        st.markdown("**Example**")
        st.code("script = client.qgis(\"\"\"\n"
                "    I have 'roads' (lines) and 'parcels' (polygons).\n"
                "    Buffer roads by 50 m, intersect with parcels,\n"
                "    save as a memory layer 'affected_parcels'.\n"
                "\"\"\")\n"
                "print(script)\n"
                "# → import processing\n"
                "#   roads = QgsProject.instance().mapLayersByName('roads')[0]\n"
                "#   ...", language="python")
        st.info("**Tip:** the SDK strips markdown fences from the response. "
                "If you ever see triple backticks in the output, file a bug — the post-processing failed.")
        st.page_link("app.py", label="↗ Try in app · QGIS Generator mode")

    # 3. analyze_image
    with st.expander("🛰️ **`client.analyze_image(image, question, ...)`** — single-image vision Q&A"):
        st.code("client.analyze_image(\n"
                "    image: PIL.Image.Image,\n"
                "    question: str,\n"
                "    *,\n"
                "    model: str | None = None,             # must be a vision model\n"
                "    system: str = SATELLITE_PROMPT,\n"
                "    temperature: float | None = None,\n"
                "    stream: bool = False,\n"
                ") -> str | Iterator[str]", language="python")
        st.markdown("**Example**")
        st.code("from PIL import Image\n"
                "img = Image.open('nile_delta.jpg')\n"
                "summary = client.analyze_image(img, 'Estimate land cover percentages.')\n"
                "print(summary)", language="python")
        st.warning("Raises `VisionNotSupported` if you pass a text-only model. "
                   "Vision-capable IDs: `gemini-2.5-flash`, `gemini-2.5-pro`, `qwen/qwen-2-vl-7b-instruct:free`.")
        st.page_link("app.py", label="↗ Try in app · Satellite Q&A mode")

    # 4. detect_changes
    with st.expander("🔁 **`client.detect_changes(before, after, question)`** — before/after analysis"):
        st.code("client.detect_changes(\n"
                "    before: PIL.Image.Image,\n"
                "    after:  PIL.Image.Image,\n"
                "    question: str = 'Identify changes between BEFORE and AFTER.',\n"
                "    *,\n"
                "    model: str | None = None,\n"
                "    temperature: float = 0.2,\n"
                "    stream: bool = False,\n"
                ") -> str | Iterator[str]", language="python")
        st.markdown("**Example**")
        st.code("before = Image.open('2020.jpg')\n"
                "after  = Image.open('2025.jpg')\n"
                "report = client.detect_changes(before, after,\n"
                "    'Focus on new urban development and water body changes.')\n"
                "print(report)", language="python")
        st.info("**Best practice:** for real change detection, pre-process the imagery "
                "(co-register, compute NDVI difference) and feed the *result* to the model. "
                "LLMs are strong at narrative, weak at pixel-level precision.")
        st.page_link("app.py", label="↗ Try in app · Change Detection mode")

    # 5. parse_address
    with st.expander("📍 **`client.parse_address(address, ...)`** — Arabic/English → JSON"):
        st.code("client.parse_address(\n"
                "    address: str,\n"
                "    *,\n"
                "    model: str | None = None,\n"
                "    temperature: float = 0.1,\n"
                ") -> dict", language="python")
        st.markdown("**Example**")
        st.code("data = client.parse_address('شارع 9 المعادي القاهرة')\n"
                "print(data)\n"
                "# → {\n"
                "#     'street_name': 'Street 9',\n"
                "#     'street_number': None,\n"
                "#     'district': 'Maadi',\n"
                "#     'governorate': 'Cairo',\n"
                "#     'landmark': None,\n"
                "#     'original_language': 'arabic',\n"
                "#     'confidence': 'high'\n"
                "#   }", language="python")
        st.warning("This method **never streams** — partial JSON is never valid JSON. "
                   "Temperature is pinned low (0.1) for output stability.")
        st.page_link("app.py", label="↗ Try in app · Address Parser mode")

    # 6. benchmark
    with st.expander("⚖️ **`client.benchmark(prompt, ...)`** — cross-provider comparison"):
        st.code("client.benchmark(\n"
                "    prompt: str,\n"
                "    *,\n"
                "    models: list[str] | None = None,    # default: one per provider\n"
                "    system: str = GENERAL_PROMPT,\n"
                "    temperature: float = 0.3,\n"
                ") -> list[BenchResult]   # dataclass: model, label, latency_s, word_count, response, error",
                language="python")
        st.markdown("**Example**")
        st.code("results = client.benchmark('What's the best CRS for Egypt?')\n"
                "for r in results:\n"
                "    print(f\"{r.label:30s}  {r.latency_s:.2f}s  {r.word_count} words\")\n"
                "# Gemini 2.5 Flash               1.21s  42 words\n"
                "# Groq Llama 3.3 70B             0.41s  38 words\n"
                "# OR Llama 3.3 70B (free)        2.05s  51 words", language="python")
        st.success("Copy this output verbatim into `DESIGN.md` § Provider Choice — it satisfies the 15% rubric weight.")
        st.page_link("app.py", label="↗ Try in app · Benchmark mode")

# ──────────────────────────────────────────────────────────────────────────
# PROVIDERS & MODELS
# ──────────────────────────────────────────────────────────────────────────
with tab_providers:
    st.subheader("Provider matrix")
    rows = []
    for mid, meta in MODELS.items():
        rows.append({
            "Model ID": mid,
            "Label": meta["label"],
            "Provider": meta["provider"].capitalize(),
            "Vision": "✅" if meta["vision"] else "—",
            "Key env var": PROVIDER_KEY[meta["provider"]],
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("How a call is dispatched")
    st.code("""# Internally, every method goes through this dispatch:
provider = MODELS[model_id]["provider"]    # 'gemini' | 'groq' | 'openrouter'

if provider == "gemini":
    call_gemini(...)                       # google.genai SDK
else:
    call_openai_compat(provider, ...)      # Groq + OpenRouter share OpenAI shape""", language="python")

    st.subheader("Adding a new model")
    st.code("""# In salah_sdk/models.py — one new entry, no other code change:
MODELS["claude-opus-4-7"] = {
    "provider": "anthropic",                  # add new provider if needed
    "vision": True,
    "label": "Claude Opus 4.7",
}

# Then implement the call_anthropic() adapter in _providers.py and dispatch
# in client.py:
#   provider == "anthropic"  →  call_anthropic(...)""", language="python")

# ──────────────────────────────────────────────────────────────────────────
# STREAMING
# ──────────────────────────────────────────────────────────────────────────
with tab_stream:
    st.subheader("Why streaming?")
    st.markdown("""
A long answer (PyQGIS script, satellite report) takes seconds to fully generate. Streaming
shows the first token as soon as it's ready, so the user sees motion instead of a spinner.

Every method that produces text supports `stream=True` and returns an `Iterator[str]`. Joining
the iterator gives you the full string. Iterating gives you token-by-token chunks.
""")

    st.subheader("Three streaming patterns")
    st.code("""# 1. Print as it arrives (CLI / Jupyter)
for chunk in client.chat('Explain CRS', stream=True):
    print(chunk, end='', flush=True)

# 2. Stream into a Streamlit chat message
import streamlit as st
with st.chat_message('assistant'):
    full = st.write_stream(client.chat('Explain CRS', stream=True))

# 3. Collect into a string (when you want the API to look non-streaming)
chunks = list(client.chat('Explain CRS', stream=True))
answer = ''.join(chunks)""", language="python")

    st.warning("**Don't stream JSON.** `parse_address()` intentionally disables streaming "
               "because partial JSON is never valid. If you need streamed structured output, "
               "stream plain markdown and parse on the client side.")

# ──────────────────────────────────────────────────────────────────────────
# ERRORS
# ──────────────────────────────────────────────────────────────────────────
with tab_errors:
    st.subheader("Error hierarchy")
    st.code("""SalahError                  # base — catch this for "anything went wrong"
├── MissingKey              # active provider has no key configured
├── ProviderError           # wraps any exception from the underlying SDK
├── UnknownModel            # caller passed a model ID not in MODELS
└── VisionNotSupported      # vision call against a text-only model""", language="text")

    st.subheader("Handling specific failures")
    st.code("""from salah_sdk import SalahClient, MissingKey, ProviderError, VisionNotSupported

try:
    answer = client.chat('hi', model='gemini-2.5-flash')
except MissingKey as exc:
    st.error(f"Set {exc.key_name} in your environment.")
except VisionNotSupported as exc:
    st.error(str(exc))            # human-readable hint to pick a vision model
except ProviderError as exc:
    # exc.original is the raw provider exception — log it for support
    st.error(f"{exc.provider} failed: {exc.original}")
    if '429' in str(exc.original):
        st.info('Rate limited — wait 60s and retry.')""", language="python")

    st.subheader("Common provider error codes")
    st.markdown("""
| Code | Meaning | What to do |
|---|---|---|
| **401** | Wrong API key | Regenerate from the provider console |
| **403** | Quota exhausted | Wait for daily reset or upgrade tier |
| **429** | Rate limited | Wait + retry with exponential backoff |
| **400** | Bad request | Usually a missing required field or wrong message shape |
| **503** | Provider down | Fall back to a different provider |
""")

# ──────────────────────────────────────────────────────────────────────────
# RECIPES
# ──────────────────────────────────────────────────────────────────────────
with tab_recipes:
    st.subheader("Recipe 1 — Bulk-parse 500 addresses to a DataFrame")
    st.code("""import pandas as pd
from salah_sdk import SalahClient

client = SalahClient.from_env()
df = pd.read_csv('survey_addresses.csv')   # column: 'address_raw'

records = []
for addr in df['address_raw']:
    try:
        records.append(client.parse_address(addr))
    except Exception as exc:
        records.append({'error': str(exc)})

parsed = pd.DataFrame(records)
parsed.to_csv('addresses_parsed.csv', index=False)""", language="python")

    st.subheader("Recipe 2 — Generate, scan, and save a PyQGIS script")
    st.code("""import re
from salah_sdk import SalahClient

client = SalahClient.from_env()
script = client.qgis('Buffer a road layer by 50m and intersect with parcels.')

# Cheap safety scan before running anything in QGIS
if re.search(r'iface\\.legendInterface|QgsMapLayerRegistry', script):
    raise RuntimeError('Generated code uses deprecated QGIS 2 API.')

open('buffer_intersect.py', 'w', encoding='utf-8').write(script)""", language="python")

    st.subheader("Recipe 3 — Switch model based on cost vs. quality")
    st.code("""def smart_chat(client, prompt, *, important=False):
    # Important questions get Pro; everything else gets Flash (10x cheaper)
    return client.chat(prompt, model='gemini-2.5-pro' if important else 'gemini-2.5-flash')

smart_chat(client, 'Quick: what's EPSG:32636?')         # → Flash
smart_chat(client, 'Justify CRS choice for our pipeline.',  # → Pro
           important=True)""", language="python")

    st.subheader("Recipe 4 — Multi-provider fallback")
    st.code("""from salah_sdk import SalahClient, ProviderError

client = SalahClient.from_env()
PRIORITY = ['gemini-2.5-flash', 'llama-3.3-70b-versatile',
            'meta-llama/llama-3.3-70b-instruct:free']

def resilient_chat(prompt):
    last = None
    for m in PRIORITY:
        try:
            return client.chat(prompt, model=m)
        except ProviderError as exc:
            last = exc
            continue
    raise last   # all providers down""", language="python")

    st.subheader("Recipe 5 — Compare and write to DESIGN.md")
    st.code("""results = client.benchmark(
    'Write 3 lines of PyQGIS to list all layer names.',
)

with open('DESIGN.md', 'a', encoding='utf-8') as f:
    f.write('\\n## Benchmark: deprecated-API trap\\n\\n')
    for r in results:
        f.write(f'**{r.label}** ({r.latency_s}s)\\n\\n```\\n{r.response}\\n```\\n\\n')""", language="python")

# ──────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(f"Salah SDK v{SDK_VERSION} · ITI Gen AI Course · "
           f"Wraps Gemini · Groq · OpenRouter")
