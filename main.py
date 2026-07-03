import os,asyncio
from dotenv import load_dotenv
from groq import Groq
import ctypes
import time
import mouse
import pyperclip

load_dotenv()

mouse_down_pos = None
MIN_DRAG_DISTANCE = 5  
selected_text_global = None
text_detected_event = asyncio.Event()
main_loop = None

class MouseEvent:
    def __init__(self):
        pass

    def get_selected(self):
        time.sleep(0.1)
        old_clipboard = pyperclip.paste()
        pyperclip.copy("")
        KEYEVENTF_KEYUP = 0x0002
        VK_CONTROL = 0x11
        VK_C = 0x43
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_C, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.1)
        selected_text = pyperclip.paste().strip()
        pyperclip.copy(old_clipboard)
        return selected_text

    def on_mouse_press(self):
        global mouse_down_pos
        mouse_down_pos = mouse.get_position()  

    def on_mouse_release(self):
        global mouse_down_pos, selected_text_global
        if mouse_down_pos is None:
            return

        up_pos = mouse.get_position()
        dx = up_pos[0] - mouse_down_pos[0]
        dy = up_pos[1] - mouse_down_pos[1]
        distance = (dx ** 2 + dy ** 2) ** 0.5

        mouse_down_pos = None  

        if distance < MIN_DRAG_DISTANCE:
            return

        text = self.get_selected()
        if text:
            print(f"\n[Detected Text]: {text[:50]}...")
            selected_text_global = text
            if main_loop:
                main_loop.call_soon_threadsafe(text_detected_event.set)


class LLM_call:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('api'))

    async def summarize_async(self, text):
        print("[AI] Thinking...")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Provide a concise 1-sentence summary of the provided text."},
            {"role": "user", "content": text}
        ]
        
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.5
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"



async def main_pipeline():
    global selected_text_global, main_loop
    main_loop = asyncio.get_running_loop() 
    llm=LLM_call()
    while True:
        # conf1
        await text_detected_event.wait()
        if selected_text_global:
            text_to_process=selected_text_global
            selected_text_global=None
            text_detected_event.clear()
            summary=await llm.summarize_async(text_to_process)

            print(f"Summary: {summary}")


if __name__ == "__main__":
    print("Background text listener active!")
    print("Highlight text anywhere, and it'll be summarized.")
    print("Press Ctrl+C to stop.")

    me = MouseEvent()
    mouse.on_button(me.on_mouse_press, buttons=("left",), types=("down",))
    mouse.on_button(me.on_mouse_release, buttons=("left",), types=("up",))

    try:
        asyncio.run(main_pipeline())
    except KeyboardInterrupt:
        print("\n\nListener stopped.")


# if __name__ == "__main__":
#     print("Background text listener active!")
#     print("Minimize this window, go to your browser, and highlight text...")
#     print("Press Ctrl+C in this terminal to stop.")

#     mouse.on_button(on_mouse_press, buttons=("left",), types=("down",))
#     mouse.on_button(on_mouse_release, buttons=("left",), types=("up",))

#     try:
#         while True:
#             time.sleep(0.1)
#     except KeyboardInterrupt:
#         print("\n\n👋 Listener stopped.")