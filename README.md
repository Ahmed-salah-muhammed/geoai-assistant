#  GIS Assistant

> A multi-mode AI helper for GIS engineers. One Streamlit app, six purpose-built modes, three LLM providers — switch on demand.

Built for the **ITI Gen AI course (Day 3 lab)** using the *vibe-coding* methodology: the AI writes the code, the engineer judges the output. The graded artifact is [DESIGN.md](DESIGN.md); the assistant itself is the evidence-generation machine.

---

##  What's inside

| Mode | What it does | Input → Output | Vision? |
|------|--------------|----------------|---------|
|  **General GIS** | Free-form chat with an EPSG-aware analyst | Text → streamed text | — |
|  **QGIS Generator** | Turns a plain-English GIS task into a PyQGIS script | Task → `st.code()` Python | — |
|  **Satellite Q&A** | Upload an image and ask questions about it | Image + text → streamed text |  |
|  **Change Detection** | Before/after pair → one-shot change analysis | 2 images + prompt → text |  |
|  **Address Parser** | Egyptian Arabic/English address → structured JSON | Text → `st.json()` | — |
|  **Benchmark** | Same 3 prompts run across all providers, side-by-side | — → comparison table | — |

The sidebar **auto-filters** providers and models by capability — pick a vision mode and text-only models disappear.

### Extras built on top of the lab requirements

-  **"Try sample"** buttons in every mode so reviewers can demo without typing
- ⬇ **Markdown chat export** — pastes straight into the DESIGN.md test-case section
-  **Debug toggle** — shows the exact payload sent to each provider (pedagogical gold)
-  **Per-session call counter** for Gemini / Groq / OpenRouter — surface cost discipline
-  **Post-generation scans** for QGIS code: deprecated `iface.legendInterface` / `QgsMapLayerRegistry` and missing CRS references on distance/area tasks
-  **Per-mode chat history** so switching modes doesn't wipe context

---

##  Quick start (local)

Prereqs: Python 3.11+ and at least one free API key.

```powershell
# 1. Clone (or open this folder)
cd "ai_assistant"

# 2. Create a virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies + the local Salah SDK (editable mode)
pip install -r requirements.txt
pip install -e .

# 4. Add your API keys
copy .env.example .env
# Edit .env and paste at least ONE of:
#   GOOGLE_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY

# 5. Run
streamlit run app.py
```

The app pops open at <http://localhost:8501>. Keys are resolved in this order: **session input → `st.secrets` → environment variable → `.env`**. You only need keys for the provider(s) you intend to use.

### Free API keys

| Provider | Sign-up | Free tier highlights |
|----------|---------|----------------------|
| **Google Gemini** | <https://aistudio.google.com/app/apikey> | Generous quota, vision-capable, the only provider that ships JSON mode without quirks |
| **Groq** | <https://console.groq.com/keys> | Fastest tokens-per-second on the market (LPU hardware), text-only |
| **OpenRouter** | <https://openrouter.ai/keys> | Gateway to dozens of models with `:free` suffix, including vision options |

---

##  Deploy to Streamlit Cloud

1. **Push the repo to GitHub** (the `.gitignore` already excludes `.env` and `.streamlit/secrets.toml`).
2. Go to **[share.streamlit.io](https://share.streamlit.io) → New app**, point it at your repo and select `app.py`.
3. After the first boot it will warn that keys are missing. Open **Settings → Secrets** and paste:
   ```toml
   GOOGLE_API_KEY = "AI..."
   GROQ_API_KEY = "gsk_..."
   OPENROUTER_API_KEY = "sk-or-..."
   ```
   The template lives at [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example).
4. Done — `get_api_key()` reads `st.secrets` automatically with no code change.

>  **Never commit `secrets.toml` or `.env`.** They are gitignored for a reason. Anyone who clones the repo gets the *.example* files and adds their own.

---

##  Architecture

The app is a **single file** ([app.py](app.py)) on purpose — graders read it in one pass. Sections, top to bottom:

```
┌─────────────────────────────────────────────────────────┐
│  Imports + page config                                  │
├─────────────────────────────────────────────────────────┤
│  get_api_key()  →  session → st.secrets → env → .env    │
├─────────────────────────────────────────────────────────┤
│  System prompts                                          │
│   GENERAL_PROMPT · QGIS_PROMPT · SATELLITE_PROMPT ·     │
│   CHANGE_PROMPT · PARSER_PROMPT (+ JSON schema)         │
├─────────────────────────────────────────────────────────┤
│  MODELS  (flat dict — vision flag per model, not per    │
│           provider; lets OpenRouter's vision and text   │
│           models be filtered independently)             │
│  MODES   (six entries: system / kind / vision needed)   │
│  MODE_DESCRIPTIONS · SAMPLE_INPUTS                      │
├─────────────────────────────────────────────────────────┤
│  Adapters                                               │
│   call_gemini()           ← google.genai (new SDK)      │
│   call_openai_compat()    ← Groq + OpenRouter (same)    │
│   call_model()            ← dispatch + counter          │
│  All return Iterator[str] so st.write_stream just works │
├─────────────────────────────────────────────────────────┤
│  Post-generation scans (deprecated PyQGIS · CRS check)  │
├─────────────────────────────────────────────────────────┤
│  Sidebar UI  (keys · mode · provider · model · temp ·   │
│               editable system prompt · debug · clear)   │
├─────────────────────────────────────────────────────────┤
│  Main area — branches on input_kind:                    │
│   chat · task_to_code · image_chat · two_image ·        │
│   text_to_json · benchmark                              │
└─────────────────────────────────────────────────────────┘
```

### Provider call shapes (cheat sheet)

| Provider | SDK | Client | Call |
|----------|-----|--------|------|
| Gemini | `google.genai` | `genai.Client(api_key=…)` | `client.chats.create(model, config, history).send_message_stream(parts)` |
| Groq | `groq` | `Groq(api_key=…)` | `client.chat.completions.create(model, messages, stream=True)` |
| OpenRouter | `openai` (with base URL override) | `OpenAI(base_url="https://openrouter.ai/api/v1", api_key=…)` | Same shape as Groq |

The two adapters reflect this: Gemini gets its own (chats API + Content/Part types), while Groq + OpenRouter share `call_openai_compat()` because their SDKs are byte-compatible.

---

##  Project files

```
ai_assistant/
├── app.py                            # Streamlit UI (entry point)
├── pages/
│   └── 1_📚_Salah_SDK.py            # Multi-tab SDK documentation page
├── salah_sdk/                        # The underlying Python SDK
│   ├── __init__.py                   #   public exports: SalahClient, MODELS, ...
│   ├── client.py                     #   the SalahClient class
│   ├── _providers.py                 #   Gemini + OpenAI-compat adapters
│   ├── models.py                     #   registry of models / modes / samples
│   ├── prompts.py                    #   all system prompts
│   └── errors.py                     #   SalahError hierarchy
├── pyproject.toml                    # `pip install -e .` makes the SDK importable
├── requirements.txt
├── .env.example                      # Copy → .env, fill in keys
├── .gitignore                        # Excludes .env, secrets.toml
├── .streamlit/
│   └── secrets.toml.example          # Copy → secrets.toml for cloud
├── README.md                         # You are here
└── DESIGN.md                         #  The graded reflection
```

### The Salah SDK

The app is a **thin Streamlit UI on top of a real Python SDK** (`salah_sdk/`).
You can use it directly from any Python script:

```python
from salah_sdk import SalahClient
client = SalahClient.from_env()
print(client.chat("What's the EPSG for Egypt?"))
print(client.parse_address("شارع 9 المعادي القاهرة"))
results = client.benchmark("Best CRS for the Nile Delta?")
```

The **📚 Salah SDK Docs** page (inside the running app — click the link at
the top of the home page) has install, auth, every method's signature,
streaming patterns, error handling, and recipes.

---

##  Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| ` No GOOGLE_API_KEY set` warning | Key missing from all four sources | Type it into the sidebar, or add to `.env` |
| `429 Too Many Requests` | Free-tier rate limit | Wait 60 s, or switch provider |
| Address Parser returns wrapped fences instead of clean JSON | Model ignored `response_mime_type` | The app already strips fences as a fallback; if it persists, lower temperature to 0.1 |
| QGIS code uses `QgsMapLayerRegistry` | Model fell back to QGIS 2 API | The post-scan flags it in red — regenerate with a stricter system prompt |
| Vision mode shows no models | Provider filter excluded everything | OpenRouter Qwen2-VL or Gemini are the only vision options — pick one of those keys |
| `streamlit: command not found` | Venv not activated | `.\.venv\Scripts\Activate.ps1` then retry |

---

##  Notes on the SDK choice

The course notebook ([Day3_GenAI_APIs_GIS_1.ipynb](Day3_GenAI_APIs_GIS_1.ipynb)) uses `google.generativeai`, which Google has now **deprecated**. This app uses the modern replacement, `google.genai`. The semantics are identical — only the import path and client construction differ. If you compare this code to the notebook you will see:

| Concept | Notebook (old) | This app (new) |
|---------|----------------|-----------------|
| Configure | `genai.configure(api_key=…)` | `client = genai.Client(api_key=…)` |
| Construct | `genai.GenerativeModel('gemini-2.5-flash', system_instruction=…)` | `types.GenerateContentConfig(system_instruction=…)` passed to the call |
| Call | `model.generate_content(parts, stream=True)` | `client.chats.create(…).send_message_stream(parts)` |
| Roles | `{'role': 'model', 'parts': [text]}` | `types.Content(role='model', parts=[types.Part(text=…)])` |

---

##  For graders

- Start at [DESIGN.md](DESIGN.md). The code is mechanical; the *reasoning* is what's being assessed.
- The sample buttons + Markdown export are there so you can reproduce any test case in <30 seconds.
- The Benchmark mode generates the cross-provider evidence quoted in DESIGN.md §2.
- The architecture diagram above maps 1:1 to the file's section banners — code should read top-to-bottom with no jumps.
