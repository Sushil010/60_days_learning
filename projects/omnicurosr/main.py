import asyncio, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import qasync
from overlay import OverlayWindow
from uitray import TrayManager
from listner import HotkeyListener
from context import gather_context
from ai_call import llm_call
from intent_router import classify_intent

async def async_main():
    overlay = OverlayWindow()
    tray = TrayManager(overlay)
    tray.show()

    overlay.last_ctx = None

    hotkey = HotkeyListener()

    async def on_hotkey(x, y):
        ctx = await gather_context(x, y)
        overlay.last_ctx = ctx

        intent_result = await classify_intent(ctx)
        mode = "vision" if ctx.should_use_vision else "text"

        print(f"[{ctx.app_name}] {mode} · {intent_result.intent} "
              f"(confidence: {intent_result.confidence}) · {ctx.timing['total']}ms")

        overlay.show_at(x, y, f"{ctx.app_name} · {mode} · {intent_result.intent}")

        await llm_call(ctx, overlay, intent_result.intent)

    def on_hotkey_wrapper(x, y):
        task = asyncio.create_task(on_hotkey(x, y))
        overlay.current_task = task

    async def run_followup(question: str):
        ctx = overlay.last_ctx
        if ctx is None:
            return

        overlay.show_at(ctx.cursor_x, ctx.cursor_y, "Following up...")

        ctx.ui_text = f"{ctx.ui_text}\n\n[Follow-up question: {question}]"

        intent_result = await classify_intent(ctx)
        print(f"Follow-up: {intent_result.intent} (confidence: {intent_result.confidence})")

        await llm_call(ctx, overlay, intent_result.intent)

    def handle_followup(question: str):
        task = asyncio.create_task(run_followup(question))
        overlay.current_task = task

    overlay.on_followup = handle_followup

    hotkey.hotkey_triggered.connect(on_hotkey_wrapper)
    hotkey.start()

    print("OmniCursor running. Press Ctrl+Space anywhere.")
    print("Press Ctrl+C in this terminal to quit.")
    while True:
        await asyncio.sleep(1)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        with loop:
            loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        print("\nShutting down OmniCursor...")
        app.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()