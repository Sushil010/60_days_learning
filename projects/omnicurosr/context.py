import time                                          
from dataclasses import dataclass, field            
from typing import Optional

from app_detect import get_active_app
from screen_capture import capture_region
from windows_uia import read_ui_text
from config import MIN_TEXT_LENGTH, SKIP_UIA_APPS   


@dataclass
class ContextBundle:
    app_name: str
    window_title: str
    ui_text: str
    control_type: str
    screenshot_bytes: Optional[bytes]
    should_use_vision: bool
    cursor_x: int
    cursor_y: int
    language: Optional[str] = None
    timing: dict = field(default_factory=dict)    
    user_question: Optional[str] = None  

def needs_vision(ui_text: str):
    return len(ui_text.strip()) < MIN_TEXT_LENGTH


async def gather_context(cursor_x: int, cursor_y: int):
    t0 = time.perf_counter()                          

    app_info = get_active_app()
    t1 = time.perf_counter()          

    if app_info["name"] in SKIP_UIA_APPS:    
        ui_data = {"text": "", "control_type": "skipped-known-unreliable"}
    else:
        ui_data = await read_ui_text(cursor_x, cursor_y)
    t2 = time.perf_counter()                                     

    ui_text = ui_data.get("text", "")
    vision_needed = needs_vision(ui_text)

    screenshot_bytes = capture_region(cursor_x, cursor_y) if vision_needed else None
    t3 = time.perf_counter()                          

    ctx = ContextBundle(
        app_name=app_info["name"],
        window_title=app_info["title"],
        ui_text=ui_text,
        control_type=ui_data.get("control_type", ""),
        screenshot_bytes=screenshot_bytes,
        should_use_vision=vision_needed,
        cursor_x=cursor_x,
        cursor_y=cursor_y,
    )

    from app_profiles import apply_profile
    ctx = apply_profile(ctx)
    t4 = time.perf_counter()                         
    ctx.timing = {                                     
        "app_detect": round((t1 - t0) * 1000, 1),
        "uia_read": round((t2 - t1) * 1000, 1),
        "screenshot": round((t3 - t2) * 1000, 1),
        "profile": round((t4 - t3) * 1000, 1),
        "total": round((t4 - t0) * 1000, 1),
    }

    return ctx