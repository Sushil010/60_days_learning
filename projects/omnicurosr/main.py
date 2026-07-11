import asyncio, sys
from PySide6.QtWidgets import QApplication
import qasync
from overlay import OverlayWindow
from uitray import TrayManager
from listner import HotkeyListener  

async def async_main():
    overlay = OverlayWindow()
    tray = TrayManager(overlay)
    tray.show()

    hotkey = HotkeyListener()
    hotkey.hotkey_triggered.connect(
        lambda x, y: overlay.show_at(x, y, "Listening")
    )
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