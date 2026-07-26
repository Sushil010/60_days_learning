import os
from dotenv import load_dotenv
from groq import AsyncGroq
from pydantic import BaseModel
from typing import Literal
from config import GROQ_API_KEY, CRITIC_MODEL


load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
CRITIC_MODEL = CRITIC_MODEL
client = AsyncGroq(api_key=GROQ_API_KEY)

CRITIC_INTENTS = {"explain_code", "fix_code"}   

CRITIC_SYSTEM = """You are a strict quality reviewer for an AI assistant.
Given the original text the assistant was looking at, and the assistant's answer,
judge if the answer is grounded in that text (not making up function names, bugs,
or details that aren't actually present).
Respond ONLY with JSON: {"verdict": "accept" | "revise", "reason": "short reason"}"""


class CriticVerdict(BaseModel):
    verdict: Literal["accept", "revise"]
    reason: str


async def verify(original_text: str, draft_answer: str, intent: str) -> CriticVerdict:
    if intent not in CRITIC_INTENTS:
        return CriticVerdict(verdict="accept", reason="skipped - not a critic-checked intent")

    if not original_text.strip():
        return CriticVerdict(verdict="accept", reason="skipped - no original text to check against")

    content = f"""Original text:
{original_text[:800]}

Assistant's answer:
{draft_answer[:800]}"""

    try:
        response = await client.chat.completions.create(
            model=CRITIC_MODEL,
            messages=[
                {"role": "system", "content": CRITIC_SYSTEM},
                {"role": "user", "content": content},
            ],
            temperature=0,
            response_format={"type": "json_object"},
            max_tokens=1024,
        )

        raw = response.choices[0].message.content or ""
        cleaned = raw.split("</think>")[-1] if "</think>" in raw else raw
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        cleaned = cleaned[start:end+1] if start != -1 and end != -1 else cleaned

        import json
        data = json.loads(cleaned)
        return CriticVerdict(**data)

    except Exception as e:
        # If the critic itself fails, don't block the user's answer - just accept silently
        return CriticVerdict(verdict="accept", reason=f"critic error: {e}")