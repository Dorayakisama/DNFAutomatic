from __future__ import annotations

import ctypes
import threading
from collections.abc import Callable
from ctypes import wintypes


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 1

FUNCTION_KEY_CODES = {
    f"F{index}": 0x6F + index for index in range(1, 13)
}


class GlobalHotkeyListener:
    """Registers a configurable global hotkey on Windows."""

    def __init__(
        self,
        callback: Callable[[], None],
        logger: Callable[[str], None],
        hotkey: str,
    ) -> None:
        self._callback = callback
        self._logger = logger
        self._hotkey = self.normalize_hotkey(hotkey)
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._registered = False
        self._ready = threading.Event()

    @property
    def hotkey(self) -> str:
        return self._hotkey

    def start(self) -> None:
        if self._thread is not None:
            return

        self._thread = threading.Thread(
            target=self._message_loop,
            name="dnf-global-hotkey",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def set_hotkey(self, hotkey: str) -> str:
        normalized = self.normalize_hotkey(hotkey)
        if normalized == self._hotkey:
            return normalized

        was_running = self._thread is not None
        if was_running:
            self.stop()

        self._hotkey = normalized

        if was_running:
            self.start()

        return normalized

    def stop(self) -> None:
        if self._thread is None:
            return

        if self._thread_id is not None:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

        self._thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = None
        self._registered = False
        self._ready.clear()

    def _message_loop(self) -> None:
        modifiers, vk_code = self._parse_hotkey(self._hotkey)
        self._thread_id = kernel32.GetCurrentThreadId()
        registered = bool(
            user32.RegisterHotKey(
                None,
                HOTKEY_ID,
                modifiers | MOD_NOREPEAT,
                vk_code,
            )
        )
        self._registered = registered
        self._ready.set()

        if not registered:
            self._logger(
                f"Warning: Global shortcut '{self._hotkey}' could not be registered. "
                "It may already be in use by another program."
            )
            return

        self._logger(
            f"Global shortcut registered: {self._hotkey} stops automation."
        )

        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) != 0:
            if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                self._callback()

            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))

        user32.UnregisterHotKey(None, HOTKEY_ID)

    @classmethod
    def normalize_hotkey(cls, hotkey: str) -> str:
        modifiers, vk_code = cls._parse_hotkey(hotkey)
        parts: list[str] = []
        if modifiers & MOD_CONTROL:
            parts.append("Ctrl")
        if modifiers & MOD_ALT:
            parts.append("Alt")
        if modifiers & MOD_SHIFT:
            parts.append("Shift")
        parts.append(cls._format_vk_code(vk_code))
        return "+".join(parts)

    @classmethod
    def _parse_hotkey(cls, hotkey: str) -> tuple[int, int]:
        if not hotkey or not hotkey.strip():
            raise ValueError("终止快捷键不能为空。")

        modifiers = 0
        key_code: int | None = None

        tokens = [token.strip() for token in hotkey.split("+") if token.strip()]
        if not tokens:
            raise ValueError("终止快捷键不能为空。")

        for token in tokens:
            upper_token = token.upper()
            if upper_token in {"CTRL", "CONTROL"}:
                modifiers |= MOD_CONTROL
                continue
            if upper_token == "ALT":
                modifiers |= MOD_ALT
                continue
            if upper_token == "SHIFT":
                modifiers |= MOD_SHIFT
                continue
            if key_code is not None:
                raise ValueError("终止快捷键只能包含一个主按键。")
            key_code = cls._parse_key_token(upper_token)

        if key_code is None:
            raise ValueError("终止快捷键缺少主按键。")

        if modifiers == 0 and not cls._is_function_key(key_code):
            raise ValueError("不带修饰键时，仅支持 F1-F12 作为终止快捷键。")

        return modifiers, key_code

    @staticmethod
    def _parse_key_token(token: str) -> int:
        if token in FUNCTION_KEY_CODES:
            return FUNCTION_KEY_CODES[token]
        if len(token) == 1 and token.isalpha():
            return ord(token)
        if len(token) == 1 and token.isdigit():
            return ord(token)
        raise ValueError(
            "仅支持 A-Z、0-9 或 F1-F12 作为终止快捷键主按键。"
        )

    @staticmethod
    def _is_function_key(vk_code: int) -> bool:
        return vk_code in FUNCTION_KEY_CODES.values()

    @staticmethod
    def _format_vk_code(vk_code: int) -> str:
        for label, code in FUNCTION_KEY_CODES.items():
            if code == vk_code:
                return label
        return chr(vk_code).upper()
