import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3.6-27b")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen/qwen3.6-27b")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "qwen/qwen3.6-27b")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "qwen/qwen3.6-27b")
MAX_TOKENS = 1024

HOTKEY = os.getenv("HOTKEY", "ctrl+space")

OVERLAY_WIDTH = 520
OVERLAY_HEIGHT = 400
OVERLAY_CORNER_RADIUS = 16

MIN_TEXT_LENGTH = 20
UIA_TIMEOUT_SEC = 1.5


SKIP_UIA_APPS = {"Code.exe"}