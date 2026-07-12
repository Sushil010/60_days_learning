import asyncio, sys
from PySide6.QtWidgets import QApplication
import qasync
from overlay import OverlayWindow
from uitray import TrayManager
from listner import HotkeyListener
from app_detect import get_active_app        
from screen_capture import capture_region    

async def async_main():
    overlay = OverlayWindow()
    tray = TrayManager(overlay)
    tray.show()

    hotkey = HotkeyListener()

    def on_hotkey(x, y):                              
        app_info = get_active_app()
        screenshot_bytes = capture_region(x, y)

        print(f"App: {app_info['name']}")
        print(f"Window: {app_info['title']}")
        print(f"Screenshot size: {len(screenshot_bytes)} bytes")

        overlay.show_at(x, y, f"{app_info['name']}")

    hotkey.hotkey_triggered.connect(on_hotkey)       
    hotkey.start()

    print("OmniCursor running. Press Ctrl+Space anywhere.")
    while True:
        await asyncio.sleep(1)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_until_complete(async_main())

if __name__ == "__main__":
    main()