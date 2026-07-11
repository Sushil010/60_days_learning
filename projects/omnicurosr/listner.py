from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal
import threading

class HotkeyListener(QObject):
    # This is Thread A's "shout" — declared once, used by the background thread to emit
    hotkey_triggered = Signal(int, int)

    def __init__(self, combo: str = "<ctrl>+<space>"):
        super().__init__()
        self.combo = combo
        self._thread = None

    def start(self):
        # daemon=True: this thread dies automatically when the app quits,
        # instead of hanging the process open
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        # This entire function runs on Thread A (the waiter). It NEVER touches
        # the UI directly — it only ever calls .emit().
        def on_activate():
            pos = mouse.Controller().position
            x, y = int(pos[0]), int(pos[1])
            self.hotkey_triggered.emit(x, y)   # the shout — safe from any thread

        hotkey = keyboard.GlobalHotKeys({self.combo: on_activate})
        hotkey.run()   # blocks THIS thread forever — fine, it's not the main thread