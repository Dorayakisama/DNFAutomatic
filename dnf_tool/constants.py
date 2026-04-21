import sys
from pathlib import Path


TARGET_TIERS = (
    "Bronze 4",
    "Silver 1",
    "Silver 2",
    "Silver 3",
    "Silver 4",
    "Gold 1",
    "Gold 2",
    "Gold 3",
    "Gold 4",
    "Platinum",
    "Diamond",
)

TARGET_TIER_LABELS = {
    "Bronze 4": "青铜4",
    "Silver 1": "白银1",
    "Silver 2": "白银2",
    "Silver 3": "白银3",
    "Silver 4": "白银4",
    "Gold 1": "黄金1",
    "Gold 2": "黄金2",
    "Gold 3": "黄金3",
    "Gold 4": "黄金4",
    "Platinum": "白金",
    "Diamond": "钻石",
}

DEFAULT_STOP_HOTKEY = "F8"
STOP_HOTKEY_PRESETS = (
    "F8",
    "F9",
    "F10",
    "Ctrl+Shift+Q",
    "Ctrl+Alt+S",
    "Ctrl+Alt+X",
)

RANK_VALUES = {
    "Bronze 4": 0,
    "Silver 1": 1,
    "Silver 2": 2,
    "Silver 3": 3,
    "Silver 4": 4,
    "Gold 1": 5,
    "Gold 2": 6,
    "Gold 3": 7,
    "Gold 4": 8,
    "Platinum": 9,
    "Diamond": 10,
    "Teranite": 11,
}

def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        external_resource_root = executable_dir / "resource"
        if external_resource_root.exists():
            return executable_dir

        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root)

        return executable_dir

    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
RESOURCE_ROOT = PROJECT_ROOT / "resource"
RANK_IMAGE_DIR = RESOURCE_ROOT / "rank_image"
SYSTEM_IMAGE_DIR = RESOURCE_ROOT / "sys_image"
ICON_FILE = RESOURCE_ROOT / "icon.ico"
WINDOWS_APP_ID = "dnf.auto.down.rank.tool"

SYSTEM_TEMPLATE_CANDIDATES = {
    "start": ("game_start.png",),
    "matching_in_progress": (
        "searching_img.png",
    ),
    "vs": (
        "vs_image.png",
    ),
}

MATCH_THRESHOLDS = {
    "rank": 0.90,
    "system": 0.88,
}

POLL_INTERVALS = {
    "default": 1.0,
    "matching": 1.0,
    "vs": 1.0,
    "round_end": 1.0,
}

TIMEOUTS = {
    "matching_in_progress": 12.0,
}
