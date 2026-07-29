import os
from groq import AsyncGroq
from config import GROQ_API_KEY, MODEL_NAME
from windows_uia import get_full_editable_text, set_editable_text

client = AsyncGroq(api_key=GROQ_API_KEY)

EDIT_SYSTEM = """You are a text-editing assistant. You are given the FULL current content
of a text file and an instruction. Return ONLY the new, complete replacement text —
no explanation, no markdown fences, no commentary. Just the raw text that should
replace the entire file content."""


async def edit_file_with_ai(x: int, y: int, instruction: str, overlay):
    data = await get_full_editable_text(x, y)
    original_text = data["text"]
    can_edit = data["can_edit"]

    if not original_text.strip():
        overlay.stream_error.emit("Couldn't read any text from this app to edit.")
        return

    if not can_edit:
        overlay.stream_error.emit("This app doesn't support direct editing. Try Notepad or a similar native text app.")
        return

    overlay.context_label.setText("Editing...")

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": EDIT_SYSTEM},
            {"role": "user", "content": f"Instruction: {instruction}\n\nCurrent content:\n{original_text}"},
        ],
        max_tokens=2048,
    )

    raw = response.choices[0].message.content or ""
    new_text = raw.split("</think>")[-1].strip() if "</think>" in raw else raw.strip()

    success = await set_editable_text(x, y, new_text)

    if success:
        overlay.context_label.setText("File updated — press Esc to dismiss")
        overlay.response_view.setPlainText(f"Applied edit: {instruction}")
    else:
        overlay.stream_error.emit("Read the file, but writing back failed. The app may have lost focus or blocked the edit.")
EDIT_TRIGGER_WORDS = [
    "edit this", "edit the", "rewrite", "replace this", "replace it",
    "update this", "modify this", "change this", "put this into",
    "write this into", "apply this to the file", "summarize this into",
    "make it into", "turn this into",
]

def looks_like_edit_request(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in EDIT_TRIGGER_WORDS)


