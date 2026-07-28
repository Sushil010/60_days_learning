import pythoncom; pythoncom.CoInitialize()
import uiautomation as auto
from pynput import mouse
import time

print("Hover over Notepad text capturing in 5s")
time.sleep(5)
pos = mouse.Controller().position
control = auto.ControlFromPoint(int(pos[0]), int(pos[1]))
vp = control.GetValuePattern()
vp.SetValue("Rewritten By AI")