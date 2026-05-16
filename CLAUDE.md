# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Scope of This Directory

This is the **`ai_assistant`** workspace inside the broader ITI Gen AI course (`Vibe Coding/`). It is **distinct from the sibling district-enrichment lab** governed by [../CLAUDE.md](../CLAUDE.md):

- The parent `CLAUDE.md` covers the GeoPandas / spatial-join lab (`enrich_districts.py`).
- This directory covers **Day 3: AI-Powered GIS — APIs + Vibe Coding** and is where the student builds the **AI-powered GIS Assistant** lab deliverable (Part 4 of the notebook).

When the user is working in this folder, default to the Day-3 context (LLM APIs, Streamlit, multimodal) — not the spatial-join lab.

---

## Current Contents

- [Day3_GenAI_APIs_GIS_1.ipynb](Day3_GenAI_APIs_GIS_1.ipynb) — 77-cell instructor notebook. Four parts:
  1. **Concepts** (no code) — why APIs, anatomy of an LLM call, provider landscape
  2. **Live vibe-coding** — Gemini first call → streaming → system prompt → error handling → multi-turn → switching to Groq / OpenRouter → multimodal (image + JSON mode + change detection)
  3. **GIS applications** — Egyptian address parser (Arabic/English structured extraction), Streamlit satellite-image Q&A app, PyQGIS script generator
  4. **Lab brief** — the deliverable described below
- [.vscode/settings.json](.vscode/settings.json) — pins the Python interpreter to `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3`. Reuse it; do not switch interpreters without asking.

The Streamlit app itself does not yet exist as a `.py` file — the starter is embedded as a string in cell 68 of the notebook.

---

## The Lab Deliverable (what work in this folder is leading toward)

An **AI-powered GIS Assistant** as a Streamlit app. Specialty is the student's choice (QGIS script helper, satellite Q&A, address parser, metadata generator, etc.).

**Mandatory features** (from notebook cell 64):
- Streamlit UI: sidebar settings + main chat area
- API-key input with `type="password"`
- At least 2 selectable models (e.g., Gemini Flash + Pro)
- Customizable system prompt with specialty presets
- Temperature slider
- **Streaming** responses
- Chat history persisted in `st.session_state`

**Repository layout the lab expects:**
```
app.py              # Streamlit app
requirements.txt
README.md           # setup + screenshots + demo gif
.env.example
.gitignore          # must exclude .env
DESIGN.md           # graded artifact — see below
```

**`DESIGN.md` is where most points are scored**, not the code. It must cover: system-prompt rationale, provider/model choice + tradeoffs, test cases with reflection, and acknowledged limitations.

**Grading weights** (notebook cell 66): System Prompt Quality 25% · Provider Selection Reasoning 15% · Test Cases Thoughtfulness 25% · Limitations Awareness (remainder).

---

## API Conventions Used Throughout the Notebook

Three providers are demonstrated; the student may pick any. Patterns to preserve when writing new code:

| Provider | SDK import | Client construction | Call site |
|---|---|---|---|
| Gemini | `import google.generativeai as genai` | `genai.configure(api_key=...)` then `genai.GenerativeModel('gemini-2.5-flash', system_instruction=...)` | `model.generate_content(prompt, stream=True)` |
| Groq | `from groq import Groq` | `Groq(api_key=...)` | `client.chat.completions.create(model='llama-3.3-70b-versatile', messages=[...])` |
| OpenRouter | `from openai import OpenAI` | `OpenAI(base_url='https://openrouter.ai/api/v1', api_key=...)` | same as OpenAI; model e.g. `'meta-llama/llama-3.3-70b-instruct:free'` |

Gemini quirks the notebook explicitly calls out (don't "fix" these — they're correct):
- Role `'model'` (not `'assistant'`), key `'parts'` (not `'content'`).
- System prompt goes into `GenerativeModel(system_instruction=...)`, not the message list.
- For JSON output use `response_mime_type='application/json'` in `generation_config`.
- Chat history via `model.start_chat(history=...)` then `chat.send_message(latest)`.

**API-key helper.** Cell 2 defines `get_api_key(key_name, display_name=None)` which resolves from (in order) in-memory cache → Colab Secrets → env vars → `.env` → `getpass` prompt. Always reuse it; do not introduce a second key-loading path. Keys live in the module-level `_API_KEYS` dict and are cleared by `clear_api_keys()` (cell 75).

---

## GIS-Specific Failure Modes the Notebook Flags

Cell 62 (Pitfall section) lists failure modes that should shape any system prompt or output verification:

- **CRS drift.** LLMs default to EPSG:4326 even when the data is projected. If the user's question involves buffers, distances, or area, the system prompt must demand explicit CRS handling, and generated PyQGIS code must be reviewed for it.
- **Hallucinated PyQGIS APIs.** The model sometimes emits QGIS 2 / deprecated calls (e.g., `iface.legendInterface()`). Prefer `qgis.core` + `processing.run(...)`.
- **Pixel-level precision.** LLMs are weak at exact pixel counts and strong at narrative. For change detection, feed them NDVI-diff *results*, not raw before/after images.
- **Estimation vs. classification.** Multimodal "land cover %" is an estimate — never treat as a classified product.

The "Defensive Vibe Coding" workflow (cell 61) — read → small sample → visual check → real dataset — should be reflected in any test cases written for `DESIGN.md`.

---

## Common Commands

The notebook runs the install commands inline; outside the notebook the equivalents are:

```powershell
# Install SDKs (the notebook uses --upgrade pip + per-provider installs)
pip install google-generativeai groq openai streamlit pillow requests

# Launch the eventual Streamlit app
streamlit run app.py

# Open the notebook in VS Code (interpreter is already pinned via .vscode/settings.json)
# — or — convert it to a script for diffing
jupyter nbconvert --to script Day3_GenAI_APIs_GIS_1.ipynb
```

No test suite, linter, or build step is configured in this directory.

---

## Methodology Inheritance

The parent project's **Vibe Coding methodology** (see [../CLAUDE.md](../CLAUDE.md) §"Vibe Coding Methodology — The Process") still applies in spirit when the student treats the assistant build as a methodology exercise:

- Plan before code; demand explicit approval.
- Don't propose improvements / error handling / edge cases the brief didn't ask for.
- Evidence before claims — for the assistant lab, "evidence" means screenshots, test-case transcripts, and the `DESIGN.md` limitations section.

The hard-numerical rules from the parent CLAUDE.md (the 3 gap schools, EPSG:32636, the verification one-liner) are **not** relevant here — those belong to the sibling enrichment lab.
