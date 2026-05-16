"""GIS Assistant — multi-mode Streamlit app powered by the Salah SDK.

The heavy lifting (provider adapters, system prompts, model registry,
mode definitions) lives in the `salah_sdk` package. This file is the
Streamlit UI on top.

Mandatory features (lab brief, notebook cell 64):
  sidebar + main chat, password API key input, >=2 model choices,
  customizable system prompt with presets, temperature slider,
  streaming, chat history in session_state.
"""

from __future__ import annotations

import io
import json
import os
import re
import time

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from salah_sdk import (
    MODE_DESCRIPTIONS,
    MODELS,
    MODES,
    PARSER_SCHEMA,
    PROVIDER_KEY,
    SAMPLE_INPUTS,
    __version__ as SDK_VERSION,
)
from salah_sdk._providers import call_gemini, call_openai_compat
from salah_sdk.models import SAMPLE_IMAGES

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GIS Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
  .hero {
    background: linear-gradient(135deg, #0f766e 0%, #134e4a 60%, #0c4a6e 100%);
    padding: 1.6rem 1.8rem; border-radius: 14px; color: white;
    margin-bottom: 1rem; box-shadow: 0 6px 16px rgba(0,0,0,.18);
  }
  .hero h1 { color: white; margin: 0 0 .3rem 0; font-size: 1.9rem; }
  .hero p  { color: #d1fae5; margin: 0; font-size: 1rem; }

  .pill {
    display: inline-flex; align-items: center; gap: .35rem;
    padding: .2rem .55rem; border-radius: 999px;
    font-size: .78rem; margin-right: .35rem; margin-bottom: .25rem;
    border: 1px solid rgba(120,120,120,.25);
  }
  .pill.ok    { background: #ecfdf5; color: #065f46; border-color: #6ee7b7; }
  .pill.miss  { background: #fef2f2; color: #991b1b; border-color: #fca5a5; }
  .pill .dot  { width: 8px; height: 8px; border-radius: 50%; }
  .pill.ok   .dot { background: #10b981; }
  .pill.miss .dot { background: #ef4444; }

  .footer {
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;
    color: #6b7280; font-size: .82rem; text-align: center;
  }
  .footer a { color: #0f766e; text-decoration: none; }
  .footer a:hover { text-decoration: underline; }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────
# API KEY HELPER  (precedence: session → st.secrets → env/.env)
# ──────────────────────────────────────────────────────────────────────────
KEY_NAMES = ("GOOGLE_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY")


def get_api_key(name: str) -> str:
    if name in st.session_state.get("_keys", {}):
        return st.session_state["_keys"][name] or ""
    try:
        v = st.secrets.get(name)
        if v:
            return v
    except Exception:
        pass
    return os.environ.get(name, "")


# ──────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────
st.session_state.setdefault("_keys", {})
st.session_state.setdefault("histories", {m: [] for m in MODES})
st.session_state.setdefault("images", {})
st.session_state.setdefault("benchmark_cache", None)
st.session_state.setdefault("call_counts", {"gemini": 0, "groq": 0, "openrouter": 0})


# ──────────────────────────────────────────────────────────────────────────
# HERO + TOP-OF-PAGE NAV
# ──────────────────────────────────────────────────────────────────────────
configured = {p: bool(get_api_key(PROVIDER_KEY[p])) for p in PROVIDER_KEY}
pills_html = " ".join(
    [
        f'<span class="pill {"ok" if configured[p] else "miss"}">'
        f'<span class="dot"></span>{p.capitalize()}</span>'
        for p in ("gemini", "groq", "openrouter")
    ]
)

st.markdown(
    f"""
<div class="hero">
  <h1> GIS Assistant</h1>
  <p>Six AI-powered modes for GIS engineers. Powered by the <strong>Salah SDK</strong>.</p>
  <div style="margin-top:.6rem">{pills_html}</div>
</div>
""",
    unsafe_allow_html=True,
)

nav_a, nav_b, nav_c, _ = st.columns([1.4, 1.4, 1.4, 4])
with nav_a:
    st.page_link(
        "pages/1_📚_Salah_SDK.py",
        label=" Salah SDK Docs",
        help="API reference + code examples",
    )
with nav_b:
    if st.button(
        "⚖️ Quick benchmark", use_container_width=True, help="Jump to benchmark mode"
    ):
        st.session_state["_jump_to_mode"] = "Benchmark"
        st.rerun()
with nav_c:
    if st.button("🧹 Reset session", use_container_width=True):
        for k in ("histories", "images", "benchmark_cache", "call_counts", "_keys"):
            st.session_state.pop(k, None)
        st.rerun()

if not any(configured.values()):
    st.info(
        "👋 **Welcome!** No API keys detected. Add at least one in the sidebar — "
        "all three providers offer a free tier. The 📚 SDK Docs page has full instructions.",
        icon="🔑",
    )


# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    with st.expander("🔑 API Keys", expanded=not any(configured.values())):
        for key_name in KEY_NAMES:
            current = get_api_key(key_name)
            val = st.text_input(
                key_name,
                type="password",
                value=current,
                help="Resolved from session > st.secrets > env > .env > this input.",
            )
            st.session_state["_keys"][key_name] = val

    default_mode_idx = 0
    if (jt := st.session_state.pop("_jump_to_mode", None)) in MODES:
        default_mode_idx = list(MODES.keys()).index(jt)
    mode_name = st.selectbox("Mode", list(MODES.keys()), index=default_mode_idx)
    mode = MODES[mode_name]
    st.caption(MODE_DESCRIPTIONS[mode_name])

    candidate_models = [
        mid
        for mid, meta in MODELS.items()
        if (meta["vision"] if mode["vision"] else True)
    ]
    if mode["vision"]:
        hidden = [m for m in MODELS if not MODELS[m]["vision"]]
        if hidden:
            st.caption(f"_{len(hidden)} text-only models hidden — vision mode_")

    available_providers = sorted({MODELS[m]["provider"] for m in candidate_models})
    provider = st.selectbox(
        "Provider", available_providers, format_func=lambda p: p.capitalize()
    )
    provider_models = [m for m in candidate_models if MODELS[m]["provider"] == provider]
    model_id = st.selectbox(
        "Model",
        provider_models,
        format_func=lambda m: MODELS[m]["label"],
    )

    temperature = st.slider("Temperature", 0.0, 2.0, 0.3, 0.1)

    system_prompt = st.text_area(
        "System Prompt",
        value=mode["system"],
        height=200,
        help="Pre-filled from the mode preset. Edit freely — this is the heart of the assistant.",
    )

    debug = st.checkbox("🔍 Debug: show raw payload")

    st.divider()
    cc = st.session_state["call_counts"]
    st.caption(
        f"📊 Calls this session — Gemini: {cc['gemini']} · "
        f"Groq: {cc['groq']} · OpenRouter: {cc['openrouter']}"
    )

    c1, c2 = st.columns(2)
    if c1.button("Clear this mode"):
        st.session_state["histories"][mode_name] = []
        st.session_state["images"].pop(mode_name, None)
        st.rerun()
    if c2.button("Clear all"):
        st.session_state["histories"] = {m: [] for m in MODES}
        st.session_state["images"] = {}
        st.session_state["benchmark_cache"] = None
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────
# Pre-flight
# ──────────────────────────────────────────────────────────────────────────
required_key = PROVIDER_KEY[provider]
if not get_api_key(required_key):
    st.warning(
        f"🔑 No `{required_key}` set. Add it in the sidebar before sending requests."
    )


# ──────────────────────────────────────────────────────────────────────────
# CALL DISPATCH (wraps SDK adapters + Streamlit-side counter)
# ──────────────────────────────────────────────────────────────────────────
def call_model(
    model_id,
    system,
    history,
    user_msg,
    temperature,
    images=None,
    stream=True,
    json_mode=False,
):
    provider = MODELS[model_id]["provider"]
    st.session_state["call_counts"][provider] += 1
    if provider == "gemini":
        return call_gemini(
            get_api_key("GOOGLE_API_KEY"),
            model_id,
            system,
            history,
            user_msg,
            temperature,
            images,
            stream,
            json_mode,
        )
    return call_openai_compat(
        provider,
        get_api_key(PROVIDER_KEY[provider]),
        model_id,
        system,
        history,
        user_msg,
        temperature,
        images,
        stream,
        json_mode,
    )


# ──────────────────────────────────────────────────────────────────────────
# POST-GENERATION SCANS  (GIS-specific failure modes from CLAUDE.md)
# ──────────────────────────────────────────────────────────────────────────
DEPRECATED_QGIS_PATTERNS = [
    r"iface\.legendInterface",
    r"QgsMapLayerRegistry",
    r"qgis\.utils\.iface\.activeLayer\(\)\.featureCount",
]
SPATIAL_KEYWORDS = re.compile(r"\b(buffer|distance|area|meter|metres?|km|kilom)", re.I)
CRS_REFS = re.compile(r"setCrs|QgsCoordinateReferenceSystem|transformContext")


def scan_qgis_output(task: str, code: str):
    if re.search("|".join(DEPRECATED_QGIS_PATTERNS), code):
        st.error(
            "⚠️ Generated code uses **deprecated QGIS 2 API**. "
            "`iface.legendInterface()` / `QgsMapLayerRegistry` were removed in QGIS 3. "
            "Ask the model to use the modern PyQGIS API."
        )
    if SPATIAL_KEYWORDS.search(task) and not CRS_REFS.search(code):
        st.warning(
            "⚠️ The task mentions distance/area but the script does **not reference any CRS**. "
            "Verify before running on projected data — LLMs default to EPSG:4326."
        )


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def render_debug(payload: dict):
    if debug:
        with st.expander("🔍 Raw payload sent to the provider"):
            st.json(payload)


def stream_and_record(history_key, user_msg, images=None, stream=True, json_mode=False):
    history = st.session_state["histories"][history_key]
    render_debug(
        {
            "model": model_id,
            "temperature": temperature,
            "system": system_prompt,
            "history_turns": len(history),
            "user_msg": user_msg,
            "n_images": len(images) if images else 0,
            "stream": stream,
            "json_mode": json_mode,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_msg)
    history.append({"role": "user", "content": user_msg})

    with st.chat_message("assistant"):
        start = time.time()
        try:
            it = call_model(
                model_id,
                system_prompt,
                history[:-1],
                user_msg,
                temperature,
                images=images,
                stream=stream,
                json_mode=json_mode,
            )
            if stream:
                full = st.write_stream(it)
            else:
                full = "".join(it)
                st.markdown(full)
        except Exception as exc:
            st.error(f"⚠️ {type(exc).__name__}: {exc}")
            history.pop()
            return None
        elapsed = time.time() - start
        words = len(full.split()) if isinstance(full, str) else 0
        st.caption(
            f"🤖 {MODELS[model_id]['label']} · ⏱ {elapsed:.2f}s · ≈{words} tokens"
        )

    history.append({"role": "assistant", "content": full})
    return full


def replay_history(history_key, show_image=False):
    if show_image and history_key in st.session_state["images"]:
        st.image(
            st.session_state["images"][history_key],
            width=320,
            caption="📎 attached image (visible to every turn)",
        )
    for m in st.session_state["histories"][history_key]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


def history_as_markdown(mode_name: str) -> str:
    lines = [
        f"# Chat export — {mode_name}",
        "",
        f"Model: {MODELS[model_id]['label']} · Temperature: {temperature}",
        "",
        "## System prompt",
        "",
        "```",
        system_prompt,
        "```",
        "",
        "## Conversation",
        "",
    ]
    for m in st.session_state["histories"][mode_name]:
        role = "🧑 You" if m["role"] == "user" else "🤖 Assistant"
        lines += [f"### {role}", "", m["content"], ""]
    return "\n".join(lines)


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_sample_image(url: str) -> bytes:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.content


def sample_image_gallery(mode_key: str):
    st.caption("Or load a public sample image:")
    cols = st.columns(len(SAMPLE_IMAGES))
    for col, (name, url) in zip(cols, SAMPLE_IMAGES.items()):
        with col:
            if st.button(
                name, key=f"sample_{mode_key}_{name}", use_container_width=True
            ):
                try:
                    data = fetch_sample_image(url)
                    st.session_state["images"][mode_key] = Image.open(io.BytesIO(data))
                    st.rerun()
                except Exception as exc:
                    st.error(f"Couldn't load sample: {exc}")


# ──────────────────────────────────────────────────────────────────────────
# MAIN AREA — branch on mode kind
# ──────────────────────────────────────────────────────────────────────────
kind = mode["kind"]

if kind == "chat":
    tools_l, tools_r = st.columns([1, 1])
    if tools_l.button("💡 Try the sample question"):
        stream_and_record(mode_name, SAMPLE_INPUTS[mode_name])
    if st.session_state["histories"][mode_name]:
        tools_r.download_button(
            "⬇️ Export chat as Markdown",
            data=history_as_markdown(mode_name),
            file_name=f"chat_{mode_name.lower().replace(' ', '_')}.md",
            mime="text/markdown",
        )
    replay_history(mode_name)
    if prompt := st.chat_input("Ask anything about GIS..."):
        stream_and_record(mode_name, prompt)

elif kind == "task_to_code":
    st.subheader("🐍 QGIS Script Generator")
    if st.button("💡 Load sample task"):
        st.session_state["qgis_task_input"] = SAMPLE_INPUTS[mode_name]
    task = st.text_area(
        "Describe the GIS task",
        height=160,
        key="qgis_task_input",
        placeholder=(
            "Example: Buffer roads by 50 meters, find intersecting parcels, "
            "save as a new memory layer."
        ),
    )
    if st.button("Generate script", type="primary", disabled=not task):
        render_debug(
            {
                "model": model_id,
                "temperature": temperature,
                "system": system_prompt,
                "task": task,
            }
        )
        start = time.time()
        try:
            it = call_model(
                model_id, system_prompt, [], task, temperature, stream=False
            )
            code = "".join(it)
        except Exception as exc:
            st.error(f"⚠️ {type(exc).__name__}: {exc}")
            st.stop()
        elapsed = time.time() - start
        code = re.sub(
            r"^```(?:python)?\s*|\s*```$", "", code.strip(), flags=re.MULTILINE
        )
        st.code(code, language="python")
        st.caption(
            f"🤖 {MODELS[model_id]['label']} · ⏱ {elapsed:.2f}s · ≈{len(code.split())} tokens"
        )
        st.download_button(
            "⬇️ Save script",
            data=code,
            file_name="generated_qgis_script.py",
            mime="text/x-python",
        )
        scan_qgis_output(task, code)

elif kind == "image_chat":
    col_img, col_chat = st.columns([1, 1])
    with col_img:
        uploaded = st.file_uploader(
            "📤 Upload satellite / aerial image", type=["png", "jpg", "jpeg"]
        )
        if uploaded:
            st.session_state["images"][mode_name] = Image.open(uploaded)
        if mode_name in st.session_state["images"]:
            st.image(st.session_state["images"][mode_name], use_container_width=True)
        else:
            st.info("Upload an image, or pick a public sample below.")
        sample_image_gallery(mode_name)

    with col_chat:
        tools_l, tools_r = st.columns([1, 1])
        sample_disabled = mode_name not in st.session_state["images"]
        if tools_l.button(
            "💡 Try the sample question",
            disabled=sample_disabled,
            help="Upload or pick an image first" if sample_disabled else None,
        ):
            stream_and_record(
                mode_name,
                SAMPLE_INPUTS[mode_name],
                images=[st.session_state["images"][mode_name]],
            )
        if st.session_state["histories"][mode_name]:
            tools_r.download_button(
                "⬇️ Export chat as Markdown",
                data=history_as_markdown(mode_name),
                file_name=f"chat_{mode_name.lower().replace(' ', '_')}.md",
                mime="text/markdown",
            )
        replay_history(mode_name, show_image=False)
        if prompt := st.chat_input("Ask about the image..."):
            img = st.session_state["images"].get(mode_name)
            if img is None:
                st.error("Upload an image first.")
            else:
                stream_and_record(mode_name, prompt, images=[img])

elif kind == "two_image":
    from salah_sdk.prompts import CHANGE_PROMPT as _CHANGE_PROMPT_DEFAULT

    st.subheader("🛰️ Change Detection")
    c1, c2 = st.columns(2)
    with c1:
        before = st.file_uploader(
            "BEFORE image", type=["png", "jpg", "jpeg"], key="before"
        )
        if before:
            img_b = Image.open(before)
            st.image(img_b, caption="BEFORE", use_container_width=True)
    with c2:
        after = st.file_uploader(
            "AFTER image", type=["png", "jpg", "jpeg"], key="after"
        )
        if after:
            img_a = Image.open(after)
            st.image(img_a, caption="AFTER", use_container_width=True)

    question = st.text_area(
        "Question / instruction", value=_CHANGE_PROMPT_DEFAULT, height=140
    )
    if st.button("Analyze changes", type="primary", disabled=not (before and after)):
        img_b = Image.open(before)
        img_a = Image.open(after)
        render_debug(
            {
                "model": model_id,
                "temperature": temperature,
                "system": system_prompt,
                "question": question,
            }
        )
        start = time.time()
        try:
            it = call_model(
                model_id,
                system_prompt,
                [],
                question,
                temperature,
                images=[img_b, img_a],
                stream=True,
            )
            full = st.write_stream(it)
        except Exception as exc:
            st.error(f"⚠️ {type(exc).__name__}: {exc}")
            st.stop()
        elapsed = time.time() - start
        st.caption(
            f"🤖 {MODELS[model_id]['label']} · ⏱ {elapsed:.2f}s · ≈{len(full.split())} tokens"
        )

elif kind == "text_to_json":
    st.subheader("📍 Address Parser")
    st.caption("Streaming is OFF for this mode — JSON must arrive complete.")
    if st.button("💡 Load sample address"):
        st.session_state["address_input"] = SAMPLE_INPUTS[mode_name]
    address = st.text_area(
        "Address (Arabic / English / mixed)",
        height=120,
        key="address_input",
        placeholder="شارع 9 المعادي القاهرة",
    )
    if st.button("Parse", type="primary", disabled=not address):
        user_msg = (
            f"Address: {address}\n\nReturn JSON with this schema:\n{PARSER_SCHEMA}"
        )
        render_debug(
            {
                "model": model_id,
                "temperature": temperature,
                "system": system_prompt,
                "user_msg": user_msg,
            }
        )
        start = time.time()
        try:
            it = call_model(
                model_id,
                system_prompt,
                [],
                user_msg,
                temperature,
                stream=False,
                json_mode=True,
            )
            raw = "".join(it)
        except Exception as exc:
            st.error(f"⚠️ {type(exc).__name__}: {exc}")
            st.stop()
        elapsed = time.time() - start
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(
                r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE
            ).strip()
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                st.error("Model did not return valid JSON.")
                st.code(raw)
                st.stop()
        st.json(data)
        st.caption(f"🤖 {MODELS[model_id]['label']} · ⏱ {elapsed:.2f}s")
        st.download_button(
            "⬇️ Save JSON",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name="parsed_address.json",
            mime="application/json",
        )

elif kind == "benchmark":
    st.subheader("⚖️ Benchmark: same prompt across providers")
    st.caption("Sends N×3 API calls (one per provider). Cached until 'Clear all'.")

    BENCH_PROMPTS = [
        (
            "CRS knowledge",
            "What's the best CRS for buffering features in the Nile Delta? Be brief, cite EPSG.",
        ),
        (
            "Deprecated API trap",
            "Write 3 lines of PyQGIS to list all layer names in the current project.",
        ),
        (
            "Address parse",
            "Parse this address into JSON {street, district, governorate}: شارع 9 المعادي القاهرة",
        ),
    ]
    DEFAULT_BENCH_MODELS = [
        "gemini-2.5-flash",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-3.3-70b-instruct:free",
    ]

    if st.button("Run benchmark", type="primary"):
        rows = []
        with st.spinner("Querying providers..."):
            for prompt_label, prompt in BENCH_PROMPTS:
                for m in DEFAULT_BENCH_MODELS:
                    if not get_api_key(PROVIDER_KEY[MODELS[m]["provider"]]):
                        rows.append(
                            {
                                "prompt": prompt_label,
                                "model": MODELS[m]["label"],
                                "latency_s": None,
                                "tokens": None,
                                "response": "(missing API key)",
                            }
                        )
                        continue
                    start = time.time()
                    try:
                        text = "".join(
                            call_model(m, system_prompt, [], prompt, 0.3, stream=False)
                        )
                    except Exception as exc:
                        text = f"⚠️ {type(exc).__name__}: {exc}"
                    rows.append(
                        {
                            "prompt": prompt_label,
                            "model": MODELS[m]["label"],
                            "latency_s": round(time.time() - start, 2),
                            "tokens": len(text.split()),
                            "response": text,
                        }
                    )
        st.session_state["benchmark_cache"] = rows

    rows = st.session_state.get("benchmark_cache")
    if rows:
        st.dataframe(
            [{k: v for k, v in r.items() if k != "response"} for r in rows],
            use_container_width=True,
        )
        for label, _ in BENCH_PROMPTS:
            with st.expander(f"📄 Responses — {label}"):
                for r in [r for r in rows if r["prompt"] == label]:
                    st.markdown(f"**{r['model']}** — {r['latency_s']}s")
                    st.markdown(r["response"])
                    st.divider()
        st.download_button(
            "⬇️ Download benchmark as Markdown",
            data="\n\n".join(
                f"## {r['prompt']} — {r['model']} ({r['latency_s']}s)\n\n{r['response']}"
                for r in rows
            ),
            file_name="benchmark_results.md",
            mime="text/markdown",
        )


# ──────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="footer">
  Built with the <strong>Salah SDK v{SDK_VERSION}</strong> · ITI Gen AI Course · Day 3 Lab<br>
  <a href="https://aistudio.google.com">Gemini</a> ·
  <a href="https://console.groq.com">Groq</a> ·
  <a href="https://openrouter.ai">OpenRouter</a>
</div>
""",
    unsafe_allow_html=True,
)
