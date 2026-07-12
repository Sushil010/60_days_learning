import mss
from PIL import Image
import io

def capture_region(cursor_x, cursor_y, width=800, height=600):
    with mss.mss() as sct:
        left = max(0, cursor_x - width // 2)
        top = max(0, cursor_y - height // 2)
        monitor = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(monitor)

    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return buf.getvalue()   