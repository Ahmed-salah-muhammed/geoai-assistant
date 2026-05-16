"""Low-level provider adapters used by SalahClient.

Two adapters, not three:
  call_gemini()         - Google's google.genai SDK
  call_openai_compat()  - Groq + OpenRouter (both speak OpenAI's protocol)

Each adapter returns Iterator[str] regardless of `stream=`. The client
joins the chunks for non-stream callers.
"""
from __future__ import annotations

import base64
import io
from typing import Iterator

from PIL import Image

from .errors import MissingKey, ProviderError


def _pil_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def call_gemini(
    api_key: str,
    model_id: str,
    system: str | None,
    history: list[dict],
    user_msg: str,
    temperature: float,
    images: list[Image.Image] | None = None,
    stream: bool = True,
    json_mode: bool = False,
) -> Iterator[str]:
    if not api_key:
        raise MissingKey("gemini", "GOOGLE_API_KEY")

    from google import genai
    from google.genai import types

    try:
        client = genai.Client(api_key=api_key)

        cfg_kwargs = {"temperature": temperature}
        if system:
            cfg_kwargs["system_instruction"] = system
        if json_mode:
            cfg_kwargs["response_mime_type"] = "application/json"
        config = types.GenerateContentConfig(**cfg_kwargs)

        gemini_history = [
            types.Content(
                role=("model" if m["role"] == "assistant" else "user"),
                parts=[types.Part(text=m["content"])],
            )
            for m in history
        ]

        parts: list = [user_msg]
        if images:
            parts.extend(images)

        chat = client.chats.create(model=model_id, config=config, history=gemini_history)

        if stream:
            for chunk in chat.send_message_stream(parts):
                if chunk.text:
                    yield chunk.text
        else:
            resp = chat.send_message(parts)
            yield resp.text or ""
    except (MissingKey, ProviderError):
        raise
    except Exception as exc:
        raise ProviderError("gemini", exc) from exc


def call_openai_compat(
    provider: str,
    api_key: str,
    model_id: str,
    system: str | None,
    history: list[dict],
    user_msg: str,
    temperature: float,
    images: list[Image.Image] | None = None,
    stream: bool = True,
    json_mode: bool = False,
) -> Iterator[str]:
    if provider == "groq":
        if not api_key:
            raise MissingKey("groq", "GROQ_API_KEY")
        from groq import Groq
        client = Groq(api_key=api_key)
    else:  # openrouter
        if not api_key:
            raise MissingKey("openrouter", "OPENROUTER_API_KEY")
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/iti-gen-ai/salah-sdk",
                "X-Title": "Salah SDK",
            },
        )

    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(history)

        if images:
            content: list[dict] = [{"type": "text", "text": user_msg}]
            for img in images:
                b64 = _pil_to_b64(img)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                })
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_msg})

        kwargs = {"model": model_id, "messages": messages, "temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        if stream:
            resp = client.chat.completions.create(stream=True, **kwargs)
            for chunk in resp:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        else:
            resp = client.chat.completions.create(**kwargs)
            yield resp.choices[0].message.content or ""
    except (MissingKey, ProviderError):
        raise
    except Exception as exc:
        raise ProviderError(provider, exc) from exc
