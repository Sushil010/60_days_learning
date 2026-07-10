from PySide6.QtCore import QObject, Signal
import threading, time


class HotkeySignal(QObject):
    hotkey_pressed = Signal(int, int) 

signaler = HotkeySignal()

def on_hotkey_pressed(x, y):
    print(f"Main thread got it Cursor was at ({x}, {y})")

signaler.hotkey_pressed.connect(on_hotkey_pressed)  
def fake_hotkey_listener():
    time.sleep(2)  
    print("Thread A: hotkey detected, shouting now")
    signaler.hotkey_pressed.emit(500, 300)  

threading.Thread(target=fake_hotkey_listener, daemon=True).start()