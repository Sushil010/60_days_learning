import os
from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel
from typing import Literal

from context import ContextBundle

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
ROUTER_MODEL = "qwen/qwen3.6-27b"


class IntentResult(BaseModel):
    intent: Literal[
        "explain_code",
        "summarize_text",
        "fix_code",
        "general_chat",
    ]
    confidence: float


ROUTER_SYSTEM = """You are an intent classifier for a system-wide AI assistant.
Given the app name, language (if known), and text under the cursor, classify what
the user most likely needs. Respond ONLY with a single-line JSON object matching this exact shape:
{"intent": "explain_code" | "summarize_text" | "fix_code" | "general_chat", "confidence": 0.0-1.0}

CRITICAL RULES:
- Output must be a single JSON object on one line and nothing else.
- Do NOT provide analysis, reasoning, step-by-step, or any tags like <think>.
- Do NOT include markdown, code fences, or explanatory text.
- If unsure, return {"intent": "general_chat", "confidence": 0.0}.

Guidelines:
- If the text looks like source code, choose `explain_code` (or `fix_code` if it clearly contains an error/traceback).
- If the text is prose/documentation/an article, choose `summarize_text`.
- If there's no useful text, choose `general_chat` with low confidence.
"""


async def classify_intent(ctx: 'ContextBundle') -> IntentResult:
    content = f"""App: {ctx.app_name}
Language: {ctx.language}
Text under cursor: {ctx.ui_text[:500]}"""

    response = await client.chat.completions.create(
        model=ROUTER_MODEL,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM},
            {"role": "user", "content": content},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_tokens=1024,
    )

    import json

    raw = getattr(response.choices[0].message, "content", "")
    if not raw or not raw.strip():
        raise RuntimeError(f"Empty model response: {response!r}")

    cleaned = raw.replace("```json", "").replace("```", "")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end+1]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        followup = await client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You receive an assistant output and must return ONLY the corresponding JSON object with keys \"intent\" and \"confidence\". Do not add text."},
                {"role": "user", "content": f"Assistant output:\n{raw}"},
            ],
            temperature=0,
            max_tokens=80,
        )

        follow_raw = getattr(followup.choices[0].message, "content", "")
        follow_clean = follow_raw.replace("```json", "").replace("```", "").strip()
        start = follow_clean.find("{")
        end = follow_clean.rfind("}")
        if start != -1 and end != -1:
            follow_clean = follow_clean[start:end+1]

        try:
            data = json.loads(follow_clean)
        except Exception:
            raise RuntimeError(f"Failed to parse JSON from model response. Raw: {raw!r} Followup: {follow_raw!r}") from e

    return IntentResult(**data)