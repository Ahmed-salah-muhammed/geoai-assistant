# DESIGN.md — GIS Assistant

> **This is the graded artifact.** The AI wrote the code in [app.py](app.py). This document is where you prove you *understood* what the AI did and where it falls short.
>
> Rubric weights (lab brief, notebook cell 66):
> | Section | Weight |
> |---|---|
> | 1. System Prompts | 25% |
> | 2. Provider & Model Choice | 15% |
> | 3. Test Cases | 25% |
> | 4. Limitations | 35% |

Each section below explains *what good answers look like* — but the content is yours to write. The rubric penalizes checkbox-filling and rewards specific, evidence-backed reasoning.

---

## 1. System Prompts (25%)

The system prompts live as constants in [app.py](app.py) (`GENERAL_PROMPT`, `QGIS_PROMPT`, `SATELLITE_PROMPT`, `CHANGE_PROMPT`, `PARSER_PROMPT`). They were ported from the course notebook but you customized them through the sidebar's editable text area during testing.

**For each mode, answer:**

1. **Why these exact words?** Quote at least one phrase from each prompt and explain what behaviour it forces.
2. **What edge case did you discover that the prompt now handles?** (e.g., "the model used to default to EPSG:4326 even when the task was projected; I added 'always cite the EPSG code' and it now references the correct projected CRS.")
3. **What did you remove and why?** If you trimmed any line from the notebook's version, justify it.

> Tip: paste the prompt verbatim, then bullet your reasoning beneath. Don't paraphrase.

---

## 2. Provider & Model Choice (15%)

The app exposes three providers (Gemini, Groq, OpenRouter) and seven models. Your job: defend the mapping.

**For each mode, answer:**

1. **Which model is your default and why?** Reference at least one *latency number* from the Benchmark mode and one *qualitative observation* (e.g., "Groq Llama 3.3 70B answered the CRS question in 0.7 s vs Gemini's 2.1 s, but Gemini's answer cited the right EPSG code unprompted").
2. **What did you give up?** The free tier costs nothing in money — what does it cost in capability? (Rate limits, missing vision, context window, JSON-mode reliability…)
3. **When does the right choice flip?** Name one scenario where a different provider would be the right call.

> Tip: the sidebar shows a session-wide call counter — note it before you run the benchmark, then again after, to confirm the per-mode billing footprint.

---

## 3. Test Cases (25%)

This is the section that catches most students. The rubric rewards *revealing* cases — inputs that surface a failure or an interesting edge — over happy-path cases.

**Provide five or more cases, mixing happy paths and failures.** Use this format per case:

```
### Case N — <one-line description>
- Mode: <name>
- Model: <provider/model>
- Temperature: <value>
- Input: <verbatim, including the system prompt if you edited it>
- Output: <verbatim — paste the full assistant response>
- Verdict: PASS / PARTIAL / FAIL
- Why: <one paragraph. What did this case reveal about the prompt, the
  model, or the assumptions you didn't realize you were making?>
```

**Required coverage:**
- At least one **PASS** case where the assistant exceeded your expectations
- At least one **FAIL** case where the assistant produced confidently wrong output (hallucination, CRS confusion, deprecated PyQGIS API, wrong language in the address parse)
- At least one case from **each input shape**: chat, image, JSON, code

> Tip: every chat-style mode has a `⬇️ Export chat as Markdown` button. Click it and paste the export directly into this section — saves typing and preserves the exact telemetry caption (model · latency · token estimate).

---

## 4. Limitations (35%)

This is the heaviest-weighted section. The rubric does **not** want a generic "AI can be wrong sometimes" — it wants *specific, named gaps* you can point at.

**Cover at least four of these. Be specific:**

| Category | What to say |
|---|---|
| **GIS knowledge** | One CRS / projection / coordinate confusion you saw the model make. What was the input and what did it claim? |
| **PyQGIS hallucination** | Did the QGIS Generator emit any function that doesn't exist, or a deprecated one (`iface.legendInterface`, `QgsMapLayerRegistry`)? The app's post-scan flags these — did it catch every instance? |
| **Vision precision** | Where did the model over-claim from the satellite image? Did it invent percentages, place names, or features that aren't in the pixels? |
| **JSON-mode failures** | Did the address parser ever return malformed JSON, mix Arabic/English in the wrong field, or pick the wrong governorate? |
| **Provider-specific quirks** | Did Groq cut off a response at `max_tokens`? Did OpenRouter's free tier return 429s? Did Gemini's safety filter block anything? |
| **Things you deliberately skipped** | What did you decide not to handle, and *why*? (Persistent storage? Authentication? Multi-image conversations? Geocoding API integration?) Don't apologize — defend the scope. |

> Tip: write this section *after* the test cases. The failures you noted above are the raw material — Limitations is where you generalize from them.

---

## Self-check before submitting

Run through this list. If any item is "no", go back and address it.

- [ ] I cited at least one **verbatim quote** from each system prompt
- [ ] I cited at least one **specific latency number** from the Benchmark mode
- [ ] I have at least **one PASS and one FAIL** test case
- [ ] My Limitations section names **specific functions, EPSG codes, or model names** — no generic "the AI sometimes hallucinates"
- [ ] I described what I **deliberately did not build** and why (scope discipline)
- [ ] I attached **screenshots** of at least three modes to a `docs/` folder and linked them from the test cases
- [ ] My reflection answers *why*, not just *what*

---

*Reviewer note: don't grade this document by length. Grade it by whether the writer could defend each claim if challenged in person.*
