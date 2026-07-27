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

def _blocking_get_full_text(x: int, y: int):
    control = auto.ControlFromPoint(x, y)
    if control is None:
        return {"text": "", "can_edit": False}

    text = ""
    can_edit = False
    try:
        vp = control.GetValuePattern()
        if vp:
            text = vp.Value
            can_edit = True   
    except Exception:
        pass

    if not text:
        try:
            tp = control.GetTextPattern()
            if tp:
                text = tp.DocumentRange.GetText(-1)  
        except Exception:
            pass

    return {"text": text.strip(), "can_edit": can_edit}


def _blocking_set_text(x: int, y: int, new_text: str):
    control = auto.ControlFromPoint(x, y)
    if control is None:
        return False
    try:
        vp = control.GetValuePattern()
        if vp:
            vp.SetValue(new_text)
            return True
    except Exception:
        pass
    return False


async def get_full_editable_text(x: int, y: int) -> dict:
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(_executor, _blocking_get_full_text, x, y)
    try:
        return await asyncio.wait_for(future, timeout=UIA_TIMEOUT_SEC)
    except (asyncio.TimeoutError, Exception):
        return {"text": "", "can_edit": False}


async def set_editable_text(x: int, y: int, new_text: str) -> bool:
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(_executor, _blocking_set_text, x, y, new_text)
    try:
        return await asyncio.wait_for(future, timeout=UIA_TIMEOUT_SEC)
    except (asyncio.TimeoutError, Exception):
        return False