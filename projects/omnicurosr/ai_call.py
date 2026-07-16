import os
from dotenv import load_dotenv
from groq import Groq
from context import ContextBundle

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "qwen/qwen3.6-27b"

SYSTEM_PROMPT = """You are a system-wide AI assistant embedded at the user's mouse cursor.
You are given the app name, window title, and the text currently under the cursor.
Give a short, useful answer about what you see. Be concise: 2-3 sentences max, no preamble."""


def build_user_message(ctx: ContextBundle):
    lang_info = f" (language: {ctx.language})" if ctx.language else ""
    return f"""App: {ctx.app_name}
Window: {ctx.window_title}{lang_info}
Text under cursor:
{ctx.ui_text or '[no readable text found]'}

Briefly explain or summarize what's here."""

def llm_call(ctx: ContextBundle):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(ctx)},
    ]

    response = client.chat.completions.create(
        messages=messages,
        model=MODEL_NAME,
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    import asyncio
    from context import gather_context

    async def test():
        ctx = await gather_context(500, 500)   
        print(llm_call(ctx))

    asyncio.run(test())