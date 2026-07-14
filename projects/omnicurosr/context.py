from dataclasses import dataclass
from typing import Optional

from app_detect import get_active_app
from screen_capture import capture_region
from windows_uia import read_ui_text

MIN_TEXT_LENGTH = 20


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


def needs_vision(ui_text: str):
    return len(ui_text.strip()) < MIN_TEXT_LENGTH


async def gather_context(cursor_x: int, cursor_y: int):
    app_info = get_active_app()
    ui_data = await read_ui_text(cursor_x, cursor_y)

    ui_text = ui_data.get("text", "")
    vision_needed = needs_vision(ui_text)


    screenshot_bytes = capture_region(cursor_x, cursor_y) if vision_needed else None

    return ContextBundle(
        app_name=app_info["name"],
        window_title=app_info["title"],
        ui_text=ui_text,
        control_type=ui_data.get("control_type", ""),
        screenshot_bytes=screenshot_bytes,
        should_use_vision=vision_needed,
        cursor_x=cursor_x,
        cursor_y=cursor_y,
    )