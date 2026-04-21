from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import ImageGrab

from dnf_tool.constants import RANK_IMAGE_DIR, RANK_VALUES, SYSTEM_IMAGE_DIR, SYSTEM_TEMPLATE_CANDIDATES
from dnf_tool.models import TemplateMatch


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


RANK_FILE_ALIASES = {
    _normalize_name("Copper4"): "Bronze 4",
    _normalize_name("Iron1"): "Silver 1",
    _normalize_name("Iron2"): "Silver 2",
    _normalize_name("Iron3"): "Silver 3",
    _normalize_name("Iron4"): "Silver 4",
    _normalize_name("Golden1"): "Gold 1",
    _normalize_name("Golden2"): "Gold 2",
    _normalize_name("Golden3"): "Gold 3",
    _normalize_name("Golden4"): "Gold 4",
    _normalize_name("Platinum"): "Platinum",
    _normalize_name("Diamond"): "Diamond",
    _normalize_name("Terra"): "Teranite",
}


@dataclass(frozen=True, slots=True)
class LoadedTemplate:
    label: str
    path: Path
    image: np.ndarray
    width: int
    height: int


class ScreenVisionService:
    """Loads template images and performs screen matching/clicking."""

    def __init__(self, logger) -> None:
        self._logger = logger
        self._rank_templates = self._load_rank_templates()
        self._system_templates = self._load_system_templates()

    def validate_resources(self) -> list[str]:
        issues: list[str] = []

        if not RANK_IMAGE_DIR.exists():
            issues.append(f"Missing folder: {RANK_IMAGE_DIR}")
        elif not self._rank_templates:
            issues.append(
                "No usable rank templates were loaded from resource/rank_image/."
            )

        if not SYSTEM_IMAGE_DIR.exists():
            issues.append(f"Missing folder: {SYSTEM_IMAGE_DIR}")
        else:
            for logical_name in SYSTEM_TEMPLATE_CANDIDATES:
                if not self._system_templates.get(logical_name):
                    issues.append(
                        "Missing system template for "
                        f"'{logical_name}' in resource/sys_image/."
                    )

        return issues

    def detect_rank(self, threshold: float) -> TemplateMatch | None:
        screen = self._capture_screen()
        return self._match_best(screen, self._rank_templates, threshold)

    def find_system_target(self, name: str, threshold: float) -> TemplateMatch | None:
        screen = self._capture_screen()
        return self._match_best(screen, self._system_templates.get(name, []), threshold)

    def click_match(self, match: TemplateMatch) -> None:
        x, y = match.center
        self._set_cursor_position(x, y)
        time.sleep(0.05)
        self._left_click()
        self._logger(f"Clicked at screen position ({x}, {y}) with native mouse input.")

    def _capture_screen(self) -> np.ndarray:
        screenshot = ImageGrab.grab(all_screens=True)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def _match_best(
        self,
        screen: np.ndarray,
        templates: list[LoadedTemplate],
        threshold: float,
    ) -> TemplateMatch | None:
        best_match: TemplateMatch | None = None

        for template in templates:
            if template.width > screen.shape[1] or template.height > screen.shape[0]:
                continue

            result = cv2.matchTemplate(screen, template.image, cv2.TM_CCOEFF_NORMED)
            _, max_value, _, max_location = cv2.minMaxLoc(result)
            if max_value < threshold:
                continue

            match = TemplateMatch(
                label=template.label,
                confidence=float(max_value),
                left=int(max_location[0]),
                top=int(max_location[1]),
                width=template.width,
                height=template.height,
            )
            if best_match is None or match.confidence > best_match.confidence:
                best_match = match

        return best_match

    def _load_rank_templates(self) -> list[LoadedTemplate]:
        if not RANK_IMAGE_DIR.exists():
            return []

        templates: list[LoadedTemplate] = []
        for path in sorted(RANK_IMAGE_DIR.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                continue

            rank_name = RANK_FILE_ALIASES.get(_normalize_name(path.stem))
            if rank_name is None:
                self._logger(
                    f"Skipping unrecognized rank template filename: {path.name}"
                )
                continue

            image = self._read_image(path)
            if image is None:
                continue

            templates.append(
                LoadedTemplate(
                    label=rank_name,
                    path=path,
                    image=image,
                    width=image.shape[1],
                    height=image.shape[0],
                )
            )

        return templates

    def _load_system_templates(self) -> dict[str, list[LoadedTemplate]]:
        loaded: dict[str, list[LoadedTemplate]] = {
            key: [] for key in SYSTEM_TEMPLATE_CANDIDATES
        }
        if not SYSTEM_IMAGE_DIR.exists():
            return loaded

        for logical_name, candidate_files in SYSTEM_TEMPLATE_CANDIDATES.items():
            for filename in candidate_files:
                path = SYSTEM_IMAGE_DIR / filename
                if not path.exists() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
                    continue

                image = self._read_image(path)
                if image is None:
                    continue

                loaded[logical_name].append(
                    LoadedTemplate(
                        label=logical_name,
                        path=path,
                        image=image,
                        width=image.shape[1],
                        height=image.shape[0],
                    )
                )

        return loaded

    def _read_image(self, path: Path) -> np.ndarray | None:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            self._logger(f"Failed to load template image: {path}")
            return None
        return image

    def _set_cursor_position(self, x: int, y: int) -> None:
        ctypes.windll.user32.SetCursorPos(int(x), int(y))

    def _left_click(self) -> None:
        mouse_event = ctypes.windll.user32.mouse_event
        left_down = 0x0002
        left_up = 0x0004
        mouse_event(left_down, 0, 0, 0, 0)
        time.sleep(0.02)
        mouse_event(left_up, 0, 0, 0, 0)
