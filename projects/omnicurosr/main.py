import asyncio, sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import qasync
from overlay import OverlayWindow
from uitray import TrayManager
from listner import HotkeyListener
from app_detect import get_active_app
from screen_capture import capture_region
from windows_uia import read_ui_text

async def async_main():
    overlay = OverlayWindow()
    tray = TrayManager(overlay)
    tray.show()

    hotkey = HotkeyListener()

    async def on_hotkey(x, y):
        app_info = get_active_app()
        screenshot_bytes = capture_region(x, y)
        ui_data = await read_ui_text(x, y)

        print(f"App: {app_info['name']}")
        print(f"Window: {app_info['title']}")
        print(f"Screenshot size: {len(screenshot_bytes)} bytes")
        print(f"UI text: {ui_data['text'][:100]}")
        print(f"Control type: {ui_data['control_type']}")

        overlay.show_at(x, y, f"{app_info['name']}")

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