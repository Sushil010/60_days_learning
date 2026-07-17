import os
from dotenv import load_dotenv
from groq import AsyncGroq          
from context import ContextBundle

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))   

MODEL_NAME = "qwen/qwen3.6-27b"

SYSTEM_PROMPT = """You are a system-wide AI assistant embedded at the user's mouse cursor.
You are given the app name, window title, and the text currently under the cursor.
Give a short, useful answer about what you see. Be concise: 2-3 sentences max.
Do not show your reasoning steps or thinking process - respond with ONLY the final answer, directly."""


def build_user_message(ctx: ContextBundle):
    lang_info = f" (language: {ctx.language})" if ctx.language else ""
    return f"""App: {ctx.app_name}
Window: {ctx.window_title}{lang_info}
Text under cursor:
{ctx.ui_text or '[no readable text found]'}

Briefly explain or summarize what's here."""


async def llm_call(ctx: ContextBundle, overlay):        
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(ctx)},
    ]

    try:
        stream = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            stream=True
        )
        overlay.response_view.clear()
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                overlay.token_received.emit(delta)

        overlay.stream_finished.emit()

    except Exception as e:
        overlay.stream_error.emit(str(e))

