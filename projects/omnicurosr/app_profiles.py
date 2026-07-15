import re
from context import ContextBundle

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
}


def vscode_profile(ctx: ContextBundle) :
    match = re.search(r"(\.\w+)\s*[-—]", ctx.window_title)
    if match:
        ext = match.group(1).lower()
        ctx.language = EXTENSION_TO_LANGUAGE.get(ext, "unknown")
    else:
        ctx.language = "unknown"
    return ctx


def browser_profile(ctx: ContextBundle):
    ctx.language = None
    return ctx


def visual_app_profile(ctx: ContextBundle):
    ctx.should_use_vision = True
    ctx.language = None
    return ctx


def generic_profile(ctx: ContextBundle):
    ctx.language = None
    return ctx


APP_PROFILES = {
    "Code.exe": vscode_profile,
    "chrome.exe": browser_profile,
    "brave.exe": browser_profile,
    "firefox.exe": browser_profile,
    "msedge.exe": browser_profile,
    "Photoshop.exe": visual_app_profile,
    "Figma.exe": visual_app_profile,
}


def apply_profile(ctx: ContextBundle):
    profile_fn = APP_PROFILES.get(ctx.app_name, generic_profile)
    return profile_fn(ctx)