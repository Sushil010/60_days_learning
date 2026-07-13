import uiautomation as auto
from concurrent.futures import ThreadPoolExecutor
import asyncio

_executor = ThreadPoolExecutor(max_workers=1)

def _blocking_read(x: int, y: int) -> dict:
    control = auto.ControlFromPoint(x, y)
    if control is None:
        return {"text": "", "control_type": "unknown"}

    text = ""
    try:
        tp = control.GetTextPattern()
        if tp:
            text = tp.DocumentRange.GetText(500)
    except Exception:
        pass

    if not text:
        try:
            vp = control.GetValuePattern()
            if vp:
                text = vp.Value
        except Exception:
            pass

    if not text:
        try:
            text = control.Name
        except Exception:
            pass

    return {
        "text": text.strip()[:2000],
        "control_type": control.ControlTypeName
    }

async def read_ui_text(x: int, y: int) -> dict:
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(_executor, _blocking_read, x, y)
    try:
        return await asyncio.wait_for(future, timeout=1.5)
    except asyncio.TimeoutError:
        return {"text": "", "control_type": "timeout"}
    except Exception as e:
        return {"text": "", "control_type": "error"}