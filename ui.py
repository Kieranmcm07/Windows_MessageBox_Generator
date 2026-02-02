from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from themes import Theme, THEMES, apply_theme
from winbox import (
    MessageBoxConfig,
    show_messagebox,
    RESULT_LABELS,
    MB_OK,
    MB_OKCANCEL,
    MB_YESNO,
    MB_YESNOCANCEL,
    MB_RETRYCANCEL,
    MB_ABORTRETRYIGNORE,
    MB_ICONERROR,
    MB_ICONWARNING,
    MB_ICONINFORMATION,
    MB_ICONQUESTION,
)

# Optional (only needed if you want URL fallback)
# pip install pillow requests
USE_URL_FALLBACK = False
MASCOT_URL = "https://catbox.moe/pictures/qts/1490418851494.png"


BUTTON_PRESETS = {
    "OK": MB_OK,
    "OK / Cancel": MB_OKCANCEL,
    "Yes / No": MB_YESNO,
    "Yes / No / Cancel": MB_YESNOCANCEL,
    "Retry / Cancel": MB_RETRYCANCEL,
    "Abort / Retry / Ignore": MB_ABORTRETRYIGNORE,
}

ICON_PRESETS = {
    "Error (X)": MB_ICONERROR,
    "Warning (!)": MB_ICONWARNING,
    "Info (i)": MB_ICONINFORMATION,
    "Question (?)": MB_ICONQUESTION,
}


@dataclass
class Assets:
    mascot: tk.PhotoImage | None


def _pick_local_mascot(asset_dir: Path) -> Path | None:
    # Pick a mascot file from assets/.
    # Supports:
    #   - mascot.png (single)
    #   - mascot_*.png (multiple -> random)
    single = asset_dir / "mascot.png"
    if single.exists():
        return single

    choices = sorted(asset_dir.glob("mascot_*.png"))
    if choices:
        return random.choice(choices)

    return None


def _load_local_mascot(asset_dir: Path) -> tk.PhotoImage | None:
    path = _pick_local_mascot(asset_dir)
    if not path:
        return None

    try:
        return tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None


def _load_mascot_from_url(url: str, size: tuple[int, int] = (220, 220)) -> tk.PhotoImage | None:
    # URL loader (optional). Only used if USE_URL_FALLBACK=True.
    # Returns a PhotoImage-like object for Tkinter.
    try:
        import requests
        from io import BytesIO
        from PIL import Image, ImageTk
    except ImportError:
        return None

    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def load_assets(asset_dir: Path) -> Assets:
    mascot = _load_local_mascot(asset_dir)

    # Optional fallback: if no local mascot exists, try URL
    if mascot is None and USE_URL_FALLBACK:
        mascot = _load_mascot_from_url(MASCOT_URL)

    return Assets(mascot=mascot)


class App(ttk.Frame):
    def __init__(self, root: tk.Tk, themes: list[Theme], asset_dir: Path) -> None:
        super().__init__(root)
        self.root = root
        self.themes = themes
        self.asset_dir = asset_dir

        self.assets = load_assets(asset_dir)

        # State
        self.theme_var = tk.StringVar(value=themes[0].name)
        self.title_var = tk.StringVar(value="File already exists")
        self.buttons_var = tk.StringVar(value="Yes / No / Cancel")
        self.icon_var = tk.StringVar(value="Warning (!)")
        self.topmost_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")

        # Keep references so images don't get GC'd
        self.mascot_img = self.assets.mascot
        self.mascot_label: ttk.Label | None = None

        self._build()
        self._wire()

        self._apply_selected_theme()
        self._refresh_preview()
        self._place_mascot()

    def _build(self) -> None:
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # LEFT
        left = ttk.Frame(self, padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(1, weight=1)
        left.rowconfigure(2, weight=1)

        header = ttk.Frame(left)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)

        self.heading_label = ttk.Label(header, text="MessageBox Builder")
        self.heading_label.grid(row=0, column=0, sticky="w")

        ttk.Label(header, text="Theme:").grid(row=0, column=1, sticky="e", padx=(10, 6))
        self.theme_combo = ttk.Combobox(
            header,
            textvariable=self.theme_var,
            values=[t.name for t in self.themes],
            state="readonly",
            width=16,
        )
        self.theme_combo.grid(row=0, column=2, sticky="e")

        ttk.Label(left, text="Title:").grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(left, textvariable=self.title_var).grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(left, text="Message:").grid(row=2, column=0, sticky="nw", pady=(0, 6))
        self.message_text = tk.Text(left, height=8, wrap="word")
        self.message_text.grid(row=2, column=1, sticky="nsew", pady=(0, 6))
        self.message_text.insert("1.0", "A file with this name already exists.\nDo you want to replace it?")

        ttk.Label(left, text="Buttons:").grid(row=3, column=0, sticky="w", pady=(0, 6))
        ttk.Combobox(left, textvariable=self.buttons_var, values=list(BUTTON_PRESETS), state="readonly").grid(
            row=3, column=1, sticky="w", pady=(0, 6)
        )

        ttk.Label(left, text="Icon:").grid(row=4, column=0, sticky="w", pady=(0, 6))
        ttk.Combobox(left, textvariable=self.icon_var, values=list(ICON_PRESETS), state="readonly").grid(
            row=4, column=1, sticky="w", pady=(0, 6)
        )

        ttk.Checkbutton(left, text="Keep dialog on top", variable=self.topmost_var).grid(
            row=5, column=1, sticky="w", pady=(4, 10)
        )

        btn_row = ttk.Frame(left)
        btn_row.grid(row=6, column=1, sticky="e", pady=(6, 0))
        ttk.Button(btn_row, text="Show", command=self._on_show).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btn_row, text="Copy snippet", command=self._on_copy_snippet).grid(row=0, column=1)

        # RIGHT
        right = ttk.Frame(self, padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.preview_heading = ttk.Label(right, text="Preview")
        self.preview_heading.grid(row=0, column=0, sticky="w")

        self.card = ttk.Frame(right, style="Card.TFrame", padding=10)
        self.card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.card.columnconfigure(0, weight=1)
        self.card.rowconfigure(1, weight=1)

        self.preview_title = ttk.Label(self.card, text="")
        self.preview_title.grid(row=0, column=0, sticky="w")

        self.preview_body = tk.Text(self.card, height=10, wrap="word", state="disabled")
        self.preview_body.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self.preview_meta = ttk.Label(self.card, text="")
        self.preview_meta.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Status bar
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(10, 6))
        self.status_bar.grid(row=1, column=0, sticky="ew")

    def _wire(self) -> None:
        self.theme_var.trace_add("write", lambda *_: self._apply_selected_theme())
        self.title_var.trace_add("write", lambda *_: self._refresh_preview())
        self.buttons_var.trace_add("write", lambda *_: self._refresh_preview())
        self.icon_var.trace_add("write", lambda *_: self._refresh_preview())
        self.topmost_var.trace_add("write", lambda *_: self._refresh_preview())
        self.message_text.bind("<KeyRelease>", lambda _e: self._refresh_preview())

    def _apply_selected_theme(self) -> None:
        theme = next((t for t in self.themes if t.name == self.theme_var.get()), self.themes[0])
        apply_theme(self.root, theme)

        # Apply heading fonts to labels we control
        self.heading_label.configure(font=theme.heading_font)
        self.preview_heading.configure(font=theme.heading_font)

        # Card padding feel per theme
        self.card.configure(padding=theme.card_padding)

    def _place_mascot(self) -> None:
        # Pin mascot to bottom-right, like Catbox.
        if not self.mascot_img:
            return

        # Place on root so it sits on top of everything
        self.mascot_label = ttk.Label(self.root, image=self.mascot_img)
        self.mascot_label.place(relx=1.0, rely=1.0, x=-12, y=-12, anchor="se")

        # Little tooltip-style hover text
        def on_enter(_e):
            self.status_var.set("Mascot loaded ✅")

        def on_leave(_e):
            # Don't erase user result if they just clicked a dialog
            if "User clicked:" not in self.status_var.get():
                self.status_var.set("Ready.")

        self.mascot_label.bind("<Enter>", on_enter)
        self.mascot_label.bind("<Leave>", on_leave)

    def _get_cfg(self) -> MessageBoxConfig:
        title = self.title_var.get().strip() or "Message"
        msg = self.message_text.get("1.0", "end").rstrip().strip() or "Hello!"
        buttons = BUTTON_PRESETS[self.buttons_var.get()]
        icon = ICON_PRESETS[self.icon_var.get()]
        return MessageBoxConfig(title=title, message=msg, buttons=buttons, icon=icon, topmost=self.topmost_var.get())

    def _refresh_preview(self) -> None:
        cfg = self._get_cfg()
        self.preview_title.config(text=cfg.title)

        self.preview_body.configure(state="normal")
        self.preview_body.delete("1.0", "end")
        self.preview_body.insert("1.0", cfg.message)
        self.preview_body.configure(state="disabled")

        self.preview_meta.config(
            text=f"{self.buttons_var.get()} • {self.icon_var.get()} • {'Topmost' if cfg.topmost else 'Normal'}"
        )

    def _on_show(self) -> None:
        self.status_var.set("Showing message box...")
        try:
            result = show_messagebox(self._get_cfg())
            self.status_var.set(f"User clicked: {RESULT_LABELS.get(result, f'Code {result}')}")
        except Exception as exc:
            self.status_var.set(f"Error: {exc}")

    def _on_copy_snippet(self) -> None:
        cfg = self._get_cfg()
        snippet = (
            "import ctypes\n\n"
            f"title = {cfg.title!r}\n"
            f"message = {cfg.message!r}\n"
            f"flags = {cfg.buttons} | {cfg.icon}" + (" | 0x00040000\n" if cfg.topmost else "\n") +
            "ctypes.windll.user32.MessageBoxW(0, message, title, flags)\n"
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(snippet)
        self.status_var.set("Copied snippet to clipboard.")
