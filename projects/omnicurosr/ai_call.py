import os
from dotenv import load_dotenv
from groq import AsyncGroq
from context import ContextBundle

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "qwen/qwen3.6-27b"

SYSTEM_PROMPTS = {
    "explain_code": """You are a system-wide AI assistant embedded at the user's mouse cursor.
The user is looking at source code. Explain what this code does in plain language.
Be concise: 2-4 sentences. Do not show your reasoning steps or thinking process - respond with ONLY the final answer, directly.""",

    "fix_code": """You are a system-wide AI assistant embedded at the user's mouse cursor.
The user is looking at code that likely contains a bug or error/traceback.
Identify the likely issue and suggest a fix. Be concise: 2-4 sentences, include a corrected
snippet only if it's short. Do not show your reasoning steps or thinking process - respond with ONLY the final answer, directly.""",

    "summarize_text": """You are a system-wide AI assistant embedded at the user's mouse cursor.
The user is looking at a passage of text/prose/documentation. Summarize the key point(s).
Be concise: 2-3 sentences. Do not show your reasoning steps or thinking process - respond with ONLY the final answer, directly.""",

    "general_chat": """You are a system-wide AI assistant embedded at the user's mouse cursor.
You are given the app name, window title, and the text currently under the cursor.
Give a short, useful answer about what you see. Be concise: 2-3 sentences max.
Do not show your reasoning steps or thinking process - respond with ONLY the final answer, directly.""",
}


def build_user_message(ctx: ContextBundle) -> str:
    lang_info = f" (language: {ctx.language})" if ctx.language else ""
    return f"""App: {ctx.app_name}
Window: {ctx.window_title}{lang_info}
Text under cursor:
{ctx.ui_text or '[no readable text found]'}

Briefly explain or summarize what's here."""


async def llm_call(ctx: ContextBundle, overlay, intent: str = "general_chat") -> None:
    system_prompt = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["general_chat"])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": build_user_message(ctx)},
    ]

    try:
        stream = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            stream=True,
        )
        overlay.response_view.clear()
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                overlay.token_received.emit(delta)

        overlay.stream_finished.emit()

    except Exception as e:
        overlay.stream_error.emit(str(e))