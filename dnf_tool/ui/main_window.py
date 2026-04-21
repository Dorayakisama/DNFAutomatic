from __future__ import annotations

import ctypes
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from dnf_tool.constants import (
    DEFAULT_STOP_HOTKEY,
    ICON_FILE,
    STOP_HOTKEY_PRESETS,
    TARGET_TIERS,
    TARGET_TIER_LABELS,
    WINDOWS_APP_ID,
)
from dnf_tool.models import AutomationRequest
from dnf_tool.services.controller import AutomationController
from dnf_tool.services.hotkey import GlobalHotkeyListener


DISPLAY_TO_TARGET_TIER = {
    label: tier for tier, label in TARGET_TIER_LABELS.items()
}


class DnfAutomationApp:
    """Main desktop window for the DNF automation tool."""

    def __init__(self) -> None:
        self._set_windows_app_id()
        self.root = tk.Tk()
        self._configure_window_icon()
        self.root.title("DNF 自动掉分工具")
        self.root.geometry("1080x760")
        self.root.minsize(980, 700)
        self.root.configure(bg="#0d1321")

        self.target_tier_var = tk.StringVar(value=TARGET_TIER_LABELS[TARGET_TIERS[0]])
        self.additional_runs_var = tk.StringVar(value="0")
        self.stop_hotkey_var = tk.StringVar(value=DEFAULT_STOP_HOTKEY)
        self.is_running_var = tk.BooleanVar(value=False)
        self._current_stop_hotkey = DEFAULT_STOP_HOTKEY

        self.controller = AutomationController(
            logger=self.append_log,
            popup=self.show_popup,
            set_running_state=self.set_running_state,
        )
        self.global_hotkey_listener = GlobalHotkeyListener(
            callback=self._stop_from_hotkey,
            logger=self.append_log,
            hotkey=self.stop_hotkey_var.get(),
        )

        self._configure_styles()
        self._build_layout()
        self.global_hotkey_listener.start()
        self._current_stop_hotkey = self.global_hotkey_listener.hotkey
        self.stop_hotkey_var.set(self._current_stop_hotkey)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        self.root.mainloop()

    def _set_windows_app_id(self) -> None:
        if hasattr(ctypes, "windll"):
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                WINDOWS_APP_ID
            )

    def _configure_window_icon(self) -> None:
        if not ICON_FILE.exists():
            return

        try:
            icon_image = Image.open(ICON_FILE)
            self._window_icon_images = []
            for size in (16, 32, 48, 64):
                resized = icon_image.copy()
                resized.thumbnail((size, size))
                self._window_icon_images.append(ImageTk.PhotoImage(resized))

            self.root.iconphoto(True, *self._window_icon_images)
        except Exception:
            try:
                self.root.iconbitmap(default=str(ICON_FILE))
            except tk.TclError:
                pass

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            ".",
            background="#0d1321",
            foreground="#e7ecf5",
            fieldbackground="#101a2b",
            font=("Segoe UI", 10),
        )
        style.configure(
            "AppTitle.TLabel",
            background="#0d1321",
            foreground="#f7fafc",
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "SectionTitle.TLabel",
            background="#151f33",
            foreground="#f7fafc",
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "Body.TLabel",
            background="#151f33",
            foreground="#c3d0e6",
            font=("Segoe UI", 10),
        )
        style.configure(
            "FieldLabel.TLabel",
            background="#151f33",
            foreground="#d7e0ef",
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 11),
            padding=(20, 12),
            background="#ff7a18",
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#ff8f39"), ("pressed", "#e56a0a")],
            foreground=[("disabled", "#f5f5f5")],
        )
        style.configure(
            "Modern.TCombobox",
            arrowsize=16,
            padding=8,
            fieldbackground="#101a2b",
            foreground="#f7fafc",
            bordercolor="#2b3750",
            lightcolor="#101a2b",
            darkcolor="#101a2b",
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", "#101a2b")],
            selectbackground=[("readonly", "#101a2b")],
            selectforeground=[("readonly", "#f7fafc")],
        )
        style.configure(
            "Modern.Vertical.TScrollbar",
            background="#253250",
            troughcolor="#0d1321",
            arrowcolor="#d7e0ef",
            bordercolor="#0d1321",
        )

    def _build_layout(self) -> None:
        outer = tk.Frame(self.root, bg="#0d1321", padx=28, pady=26)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg="#0d1321")
        header.pack(fill="x", pady=(0, 18))

        ttk.Label(
            header,
            text="DNF 自动掉分工具",
            style="AppTitle.TLabel",
        ).pack(anchor="w")

        content = tk.Frame(outer, bg="#0d1321")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=0)
        content.rowconfigure(1, weight=1)

        control_card = self._create_card(content, row=0, column=0, sticky="new")
        instructions_card = self._create_card(content, row=0, column=1, sticky="new")
        console_card = self._create_card(
            content,
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
        )

        self._build_control_section(control_card)
        self._build_instructions_section(instructions_card)
        self._build_console_section(console_card)

    def _create_card(
        self,
        parent: tk.Widget,
        *,
        row: int,
        column: int,
        rowspan: int = 1,
        columnspan: int = 1,
        sticky: str = "nsew",
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg="#151f33",
            bd=0,
            highlightthickness=1,
            highlightbackground="#22304b",
            padx=22,
            pady=20,
        )
        card.grid(
            row=row,
            column=column,
            rowspan=rowspan,
            columnspan=columnspan,
            sticky=sticky,
            padx=10,
            pady=10,
        )
        return card

    def _build_control_section(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text="自动掉分设置", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        field_group = tk.Frame(parent, bg="#151f33")
        field_group.grid(row=1, column=0, sticky="ew")
        field_group.columnconfigure(0, weight=1)
        field_group.columnconfigure(1, weight=1)

        tier_frame = tk.Frame(field_group, bg="#151f33")
        tier_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 14))

        ttk.Label(tier_frame, text="目标段位", style="FieldLabel.TLabel").pack(
            anchor="w", pady=(0, 8)
        )

        tier_dropdown = ttk.Combobox(
            tier_frame,
            textvariable=self.target_tier_var,
            values=[TARGET_TIER_LABELS[tier] for tier in TARGET_TIERS],
            state="readonly",
            style="Modern.TCombobox",
            height=len(TARGET_TIERS),
        )
        tier_dropdown.pack(fill="x")

        runs_frame = tk.Frame(field_group, bg="#151f33")
        runs_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 14))

        ttk.Label(
            runs_frame,
            text="达到目标段位后额外匹配场数",
            style="FieldLabel.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        validate_command = (self.root.register(self._validate_runs_input), "%P")

        runs_entry = tk.Entry(
            runs_frame,
            textvariable=self.additional_runs_var,
            bg="#101a2b",
            fg="#f7fafc",
            insertbackground="#f7fafc",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#2b3750",
            highlightcolor="#ff7a18",
            font=("Segoe UI", 11),
            validate="key",
            validatecommand=validate_command,
        )
        runs_entry.pack(fill="x", ipady=10)

        hotkey_frame = tk.Frame(field_group, bg="#151f33")
        hotkey_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        hotkey_frame.columnconfigure(0, weight=1)

        ttk.Label(
            hotkey_frame,
            text="终止快捷键",
            style="FieldLabel.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        self.stop_hotkey_entry = ttk.Combobox(
            hotkey_frame,
            textvariable=self.stop_hotkey_var,
            values=STOP_HOTKEY_PRESETS,
            state="normal",
            style="Modern.TCombobox",
        )
        self.stop_hotkey_entry.pack(fill="x")
        self.stop_hotkey_entry.bind("<<ComboboxSelected>>", self._apply_stop_hotkey)
        self.stop_hotkey_entry.bind("<FocusOut>", self._apply_stop_hotkey)
        self.stop_hotkey_entry.bind("<Return>", self._apply_stop_hotkey)

        hint = tk.Label(
            parent,
            text="终止快捷键支持 A-Z、0-9、F1-F12，例如 F8 或 Ctrl+Shift+Q。",
            bg="#151f33",
            fg="#8fa3c7",
            font=("Segoe UI", 9),
        )
        hint.grid(row=2, column=0, sticky="w", pady=(10, 22))

        self.start_button = ttk.Button(
            parent,
            text="开始",
            style="Primary.TButton",
            command=self._on_start,
        )
        self.start_button.grid(row=3, column=0, sticky="w")

    def _build_instructions_section(self, parent: tk.Frame) -> None:
        ttk.Label(parent, text="使用说明", style="SectionTitle.TLabel").pack(
            anchor="w"
        )

        instructions = (
            "1. 选择目标段位。\n"
            "2. 输入额外场数；如果不需要，保持为 0 即可。\n"
            "3. 在“终止快捷键”中设置你想用的停止快捷键。\n"
            "4. 点击“开始”。\n"
            "5. 运行中再次点击“Running...”或按所选快捷键，可手动停止自动化。"
        )

        instructions_box = tk.Label(
            parent,
            text=instructions,
            bg="#101a2b",
            fg="#e7ecf5",
            justify="left",
            anchor="nw",
            padx=16,
            pady=16,
            font=("Segoe UI", 10),
            # wraplength=300,
        )
        instructions_box.pack(fill="both", expand=True)

    def _build_console_section(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(parent, text="控制台输出", style="SectionTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        console_frame = tk.Frame(
            parent,
            bg="#101a2b",
            highlightthickness=1,
            highlightbackground="#22304b",
        )
        console_frame.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.console = tk.Text(
            console_frame,
            bg="#101a2b",
            fg="#dce6f7",
            insertbackground="#ffffff",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=14,
            pady=14,
            state="disabled",
        )
        self.console.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            console_frame,
            orient="vertical",
            command=self.console.yview,
            style="Modern.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.console.configure(yscrollcommand=scrollbar.set)

        self.append_log("控制台已初始化，等待开始自动化。")

    def _validate_runs_input(self, proposed_value: str) -> bool:
        return proposed_value.isdigit() or proposed_value == ""

    def _apply_stop_hotkey(self, _event: tk.Event | None = None) -> str | None:
        proposed_hotkey = self.stop_hotkey_var.get().strip()
        if not proposed_hotkey:
            self.stop_hotkey_var.set(self._current_stop_hotkey)
            return "break" if _event is not None else None

        try:
            normalized_hotkey = self.global_hotkey_listener.set_hotkey(proposed_hotkey)
        except ValueError as exc:
            self.show_popup("快捷键无效", str(exc), "warning")
            self.stop_hotkey_var.set(self._current_stop_hotkey)
            return "break" if _event is not None else None

        if normalized_hotkey != self._current_stop_hotkey:
            self._current_stop_hotkey = normalized_hotkey
            self.stop_hotkey_var.set(normalized_hotkey)
            self.append_log(f"终止快捷键已更新为 {normalized_hotkey}。")

        return "break" if _event is not None else None

    def _on_start(self) -> None:
        if self.is_running_var.get():
            self.append_log("Running... 按钮被点击，正在手动停止自动化。")
            self.controller.stop()
            return

        raw_runs = self.additional_runs_var.get().strip()
        if not raw_runs.isdigit():
            messagebox.showerror(
                "输入无效",
                "额外场数必须是 0 或正整数。",
                parent=self.root,
            )
            return

        try:
            self._apply_stop_hotkey()
        except Exception:
            return

        request = AutomationRequest(
            target_tier=DISPLAY_TO_TARGET_TIER[self.target_tier_var.get()],
            additional_runs=int(raw_runs),
        )
        self.controller.start(request)

    def append_log(self, message: str) -> None:
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.append_log, message)
            return

        self.console.configure(state="normal")
        self.console.insert("end", f"{message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def show_popup(self, title: str, message: str, level: str = "info") -> None:
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.show_popup, title, message, level)
            return

        if level == "warning":
            messagebox.showwarning(title, message, parent=self.root)
        elif level == "error":
            messagebox.showerror(title, message, parent=self.root)
        else:
            messagebox.showinfo(title, message, parent=self.root)

    def set_running_state(self, is_running: bool) -> None:
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.set_running_state, is_running)
            return

        self.is_running_var.set(is_running)
        if is_running:
            self.start_button.configure(text="Running...", state="normal")
        else:
            self.start_button.configure(text="开始", state="normal")

    def _stop_from_hotkey(self) -> None:
        self.root.after(0, self._handle_stop_hotkey)

    def _handle_stop_hotkey(self) -> None:
        if self.controller.is_running:
            self.append_log(
                f"检测到终止快捷键 {self._current_stop_hotkey}，正在停止自动化。"
            )
            self.controller.stop()
        else:
            self.append_log(
                f"检测到终止快捷键 {self._current_stop_hotkey}，但当前没有正在运行的自动化。"
            )

    def _on_close(self) -> None:
        self.global_hotkey_listener.stop()
        self.controller.stop()
        self.root.destroy()
