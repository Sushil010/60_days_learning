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

    hotkey = HotkeyListener()

    async def on_hotkey(x, y):
        ctx = await gather_context(x, y)

        print(f"App: {ctx.app_name}")
        print(f"Window: {ctx.window_title}")
        print(f"UI text: {ctx.ui_text[:100]}")
        print(f"Control type: {ctx.control_type}")
        print(f"Language: {ctx.language}")
        print(f"Using vision: {ctx.should_use_vision}")
        if ctx.screenshot_bytes:
            print(f"Screenshot size: {len(ctx.screenshot_bytes)} bytes")

        t = ctx.timing
        print(f"Timing: app={t['app_detect']}ms | uia={t['uia_read']}ms | "
              f"screenshot={t['screenshot']}ms | profile={t['profile']}ms | "
              f"TOTAL={t['total']}ms")

        intent_result = await classify_intent(ctx)
        print(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence})")

        mode = "vision" if ctx.should_use_vision else "text"
        overlay.show_at(x, y, f"{ctx.app_name} · {mode} · {intent_result.intent}")

        await llm_call(ctx, overlay, intent_result.intent)   

    def on_hotkey_wrapper(x, y):
        asyncio.create_task(on_hotkey(x, y))

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