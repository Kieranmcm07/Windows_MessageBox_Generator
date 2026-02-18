from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageTk, ImageOps

from themes import Theme, apply_theme
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

MESSAGE_PRESETS: dict[str, tuple[str, str, str, str]] = {
    "File already exists": (
        "File already exists",
        "A file with this name already exists.\nDo you want to replace it?",
        "Yes / No / Cancel",
        "Warning (!)",
    ),
    "Permission denied": (
        "Access denied",
        "You do not have permission to perform this action.",
        "OK",
        "Error (X)",
    ),
    "Operation completed": (
        "Done",
        "The operation completed successfully.",
        "OK",
        "Info (i)",
    ),
    "Are you sure?": (
        "Confirm",
        "Are you sure you want to continue?",
        "Yes / No",
        "Question (?)",
    ),
}


# ---------------- Batch (.bat) generator ----------------

_DOTNET_BUTTONS = {
    MB_OK: "OK",
    MB_OKCANCEL: "OKCancel",
    MB_YESNO: "YesNo",
    MB_YESNOCANCEL: "YesNoCancel",
    MB_RETRYCANCEL: "RetryCancel",
    MB_ABORTRETRYIGNORE: "AbortRetryIgnore",
}

_DOTNET_ICONS = {
    0: "None",
    MB_ICONERROR: "Error",
    MB_ICONWARNING: "Warning",
    MB_ICONINFORMATION: "Information",
    MB_ICONQUESTION: "Question",
}


def _escape_for_batch_echo(line: str) -> str:
    # Escape caret first
    line = line.replace("^", "^^")

    # Escape parentheses (THIS was breaking your batch block)
    line = line.replace("(", "^(")
    line = line.replace(")", "^)")

    # Escape other special CMD characters
    line = line.replace("&", "^&")
    line = line.replace("<", "^<")
    line = line.replace(">", "^>")
    line = line.replace("|", "^|")

    return line



def build_bat_script(cfg: "MessageBoxConfig") -> str:
    """Return a self-contained .bat script that shows an equivalent MessageBox.

    Uses PowerShell + System.Windows.Forms for parity with Win32 MessageBox flags.
    Writes a temporary .ps1 to preserve newlines and avoid quoting issues.
    """
    buttons = _DOTNET_BUTTONS.get(cfg.buttons, "OK")
    icon = _DOTNET_ICONS.get(cfg.icon, "None")
    topmost = "$true" if cfg.topmost else "$false"

    title_lines = cfg.title.splitlines() or [""]
    msg_lines = cfg.message.splitlines() or [""]

    ps_lines: list[str] = []
    ps_lines.append("Add-Type -AssemblyName System.Windows.Forms")
    ps_lines.append("$title = @'")
    ps_lines.extend(title_lines)
    ps_lines.append("'@")
    ps_lines.append("$message = @'")
    ps_lines.extend(msg_lines)
    ps_lines.append("'@")
    ps_lines.append(f"$buttons = [System.Windows.Forms.MessageBoxButtons]::{buttons}")
    ps_lines.append(f"$icon = [System.Windows.Forms.MessageBoxIcon]::{icon}")
    ps_lines.append("# Create a hidden owner window so we can use TopMost when requested")
    ps_lines.append("$owner = New-Object System.Windows.Forms.Form")
    ps_lines.append("$owner.ShowInTaskbar = $false")
    ps_lines.append("$owner.Opacity = 0")
    ps_lines.append("$owner.StartPosition = 'Manual'")
    ps_lines.append("$owner.Location = New-Object System.Drawing.Point(-32000,-32000)")
    ps_lines.append(f"$owner.TopMost = {topmost}")
    ps_lines.append("$owner.Add_Shown({ $owner.Hide() })")
    ps_lines.append("$null = $owner.Show()  # ensures handle exists")
    ps_lines.append("$result = [System.Windows.Forms.MessageBox]::Show($owner, $message, $title, $buttons, $icon)")
    ps_lines.append("$owner.Close()")
    ps_lines.append(
        "switch ($result.ToString()) {"\
        " 'OK' { exit 1 }"\
        " 'Cancel' { exit 2 }"\
        " 'Abort' { exit 3 }"\
        " 'Retry' { exit 4 }"\
        " 'Ignore' { exit 5 }"\
        " 'Yes' { exit 6 }"\
        " 'No' { exit 7 }"\
        " default { exit 0 }"\
        "}"
    )

    bat: list[str] = []
    bat.append("@echo off")
    bat.append("setlocal EnableExtensions")
    bat.append("set \"ps1=%temp%\\msgbox_builder_%random%_%random%.ps1\"")
    bat.append("(")
    for line in ps_lines:
        if line == "":
            bat.append("  echo(")
        else:
            bat.append(f"  echo {_escape_for_batch_echo(line)}")
    bat.append(") > \"%ps1%\"")
    bat.append("powershell -NoProfile -ExecutionPolicy Bypass -File \"%ps1%\"")
    bat.append("set \"rc=%errorlevel%\"")
    bat.append("del /q \"%ps1%\" >nul 2>&1")
    bat.append("echo.")
    bat.append("echo Exit code: %rc%")
    bat.append("pause")
    bat.append("exit /b %rc%")

    return "\n".join(bat) + "\n"


@dataclass
class Assets:
    mascot: tk.PhotoImage | None


def _list_mascots(asset_dir: Path) -> list[Path]:
    single = asset_dir / "mascot.png"
    if single.exists():
        return [single]
    return sorted(asset_dir.glob("mascot_*.png"))


def _load_photo(path: Path) -> tk.PhotoImage | None:
    try:
        return tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None


def load_assets(asset_dir: Path) -> Assets:
    mascots = _list_mascots(asset_dir)
    if not mascots:
        return Assets(mascot=None)
    picked = random.choice(mascots)
    return Assets(mascot=_load_photo(picked))


class App(ttk.Frame):
    def __init__(self, root: tk.Tk, themes: list[Theme], asset_dir: Path) -> None:
        super().__init__(root, style="App.TFrame")
        self.root = root
        self.themes = themes
        self.asset_dir = asset_dir
        self.theme: Theme = themes[0]

        self.assets = load_assets(asset_dir)

        # Wallpaper system state
        self._bg_after_id = None
        self._wall_choice: Path | None = None
        self._root_wall_photo = None


        # State
        self.theme_var = tk.StringVar(value=themes[0].name)
        self.preset_var = tk.StringVar(value="File already exists")
        self.title_var = tk.StringVar(value="File already exists")
        self.buttons_var = tk.StringVar(value="Yes / No / Cancel")
        self.icon_var = tk.StringVar(value="Warning (!)")
        self.topmost_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready.")

        # Images
        self.mascot_img = self.assets.mascot
        self.mascot_label: ttk.Label | None = None

        # History
        self.history: list[str] = []

        self._build()
        self._wire()
        self._apply_selected_theme()
        self._apply_preset()
        self._refresh_preview()
        self._refresh_batch()
        self._place_mascot()
        self._apply_wallpaper_for_theme()

    # ---------------- Wallpaper helpers ----------------
    def _next_wallpaper(self) -> None:
        if self.theme.name != "Anime Night":
            self.status_var.set("Switch to 'Anime Night' to use wallpapers.")
            return

        choices = self._bg_paths()
        if not choices:
            self.status_var.set("No wallpapers found in assets/backgrounds/")
            return

        if len(choices) == 1:
            self._wall_choice = choices[0]
        else:
            current = self._wall_choice
            pool = [p for p in choices if p != current]
            self._wall_choice = random.choice(pool)

        self._apply_wallpaper_for_theme()


    def _bg_paths(self) -> list[Path]:
        bg_dir = self.asset_dir / "backgrounds"
        if not bg_dir.exists():
            return []
        choices = sorted(bg_dir.glob("anime_bg_*.png"))
        if not choices:
            choices = (
                sorted(bg_dir.glob("*.png"))
                + sorted(bg_dir.glob("*.jpg"))
                + sorted(bg_dir.glob("*.jpeg"))
            )
        return choices

    def _make_wallpaper_photo(self, path: Path, size: tuple[int, int], overlay_alpha: int) -> ImageTk.PhotoImage | None:
        try:
            img = Image.open(path).convert("RGBA")
            img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)
            overlay = Image.new("RGBA", size, (0, 0, 0, overlay_alpha))
            img = Image.alpha_composite(img, overlay)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _schedule_bg_redraw(self) -> None:
        if self._bg_after_id is not None:
            self.root.after_cancel(self._bg_after_id)
        self._bg_after_id = self.root.after(120, self._apply_wallpaper_for_theme)

    def _apply_wallpaper_for_theme(self) -> None:
        # Only show wallpaper in Anime Night theme
        if self.theme.name != "Anime Night":
            if hasattr(self, "root_wall_label"):
                self.root_wall_label.configure(image="")
                self._root_wall_photo = None
            self._wall_choice = None
            return

        choices = self._bg_paths()
        if not choices:
            self.status_var.set("No backgrounds found in assets/backgrounds/")
            return

        # Keep stable until user changes wallpaper
        if self._wall_choice not in choices:
            self._wall_choice = random.choice(choices)
        bg_path = self._wall_choice

        # Full window wallpaper (covers entire window)
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w < 200 or h < 200:
            self.root.after(120, self._apply_wallpaper_for_theme)
            return

        photo = self._make_wallpaper_photo(bg_path, (w, h), overlay_alpha=0)
        if photo:
            self._root_wall_photo = photo
            self.root_wall_label.configure(image=self._root_wall_photo)

        self.status_var.set(f"Wallpaper: {bg_path.name}")


    # ---------------- UI build ----------------

    def _build(self) -> None:
        self.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.root_wall_label = tk.Label(self.root, bd=0)
        self.root_wall_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.root_wall_label.lower()
        self.lift()

        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        for seq in ("<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"):
            paned.bind(seq, lambda e: "break")
        # ---- LEFT container (wallpaper + inset panel) ----
        left_container = tk.Frame(paned, bd=0, highlightthickness=0)
        paned.add(left_container, weight=2)

        left_inset = ttk.Frame(left_container, style="Panel.TFrame", padding=12)
        left_inset.place(x=40, y=40, relwidth=1, relheight=1, width=-80, height=-80)

        # ---- RIGHT container (wallpaper + inset panel) ----
        right_container = tk.Frame(paned, bd=0, highlightthickness=0)
        paned.add(right_container, weight=3)

        # Prevent panes collapsing so widgets don't overlap when the window is resized.
        try:
            paned.paneconfigure(left_container, minsize=380)
            paned.paneconfigure(right_container, minsize=460)
        except Exception:
            # Older Tk builds may not support minsize on panes.
            pass


        right_inset = ttk.Frame(right_container, style="Panel.TFrame", padding=12)
        right_inset.place(x=40, y=40, relwidth=1, relheight=1, width=-80, height=-80)

        # Build the UI into inset frames
        left = left_inset
        right = right_inset

        self._left_container = left_container
        self._right_container = right_container

        # LEFT layout
        left.columnconfigure(1, weight=1)
        left.rowconfigure(3, weight=1)

        header = ttk.Frame(left, style="Panel.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)

        self.heading_label = ttk.Label(header, text="MessageBox Builder", style="Heading.TLabel")
        self.heading_label.grid(row=0, column=0, sticky="w")

        ttk.Label(header, text="Theme:", style="Muted.TLabel").grid(row=0, column=1, sticky="e", padx=(10, 6))
        self.theme_combo = ttk.Combobox(
            header,
            textvariable=self.theme_var,
            values=[t.name for t in self.themes],
            state="readonly",
            width=12,
        )
        self.theme_combo.grid(row=0, column=2, sticky="e")

        ttk.Label(left, text="Preset:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.preset_combo = ttk.Combobox(
            left,
            textvariable=self.preset_var,
            values=list(MESSAGE_PRESETS.keys()),
            state="readonly",
        )
        self.preset_combo.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(left, text="Title:", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(left, textvariable=self.title_var).grid(row=2, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(left, text="Message:", style="Muted.TLabel").grid(row=3, column=0, sticky="nw", pady=(0, 6))
        self.message_text = ScrolledText(left, height=9, wrap="word", highlightthickness=1)
        self.message_text.grid(row=3, column=1, sticky="nsew", pady=(0, 6))

        # Use a 2-row layout so it never squashes into the right pane.
        row4 = ttk.Frame(left, style="Panel.TFrame")
        row4.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        row4.columnconfigure(1, weight=1)
        row4.columnconfigure(3, weight=1)

        ttk.Label(row4, text="Buttons:", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 6))
        ttk.Combobox(
            row4,
            textvariable=self.buttons_var,
            values=list(BUTTON_PRESETS),
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(row4, text="Icon:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 6))
        ttk.Combobox(
            row4,
            textvariable=self.icon_var,
            values=list(ICON_PRESETS),
            state="readonly",
        ).grid(row=1, column=1, sticky="ew")

        ttk.Checkbutton(left, text="Keep dialog on top", variable=self.topmost_var).grid(
            row=5, column=1, sticky="w", pady=(6, 10)
        )

        actions = ttk.Frame(left, style="Panel.TFrame")
        actions.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)

        # Make buttons wrap instead of overlapping when the window is narrow.
        row_a = ttk.Frame(actions, style="Panel.TFrame")
        row_a.grid(row=0, column=0, sticky="ew")
        row_a.columnconfigure((0, 1, 2), weight=1)
        ttk.Button(row_a, text="Show", style="Accent.TButton", command=self._on_show).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(row_a, text="Copy Python", command=self._on_copy_snippet).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(row_a, text="Copy .bat", command=self._on_copy_bat).grid(row=0, column=2, sticky="ew")

        row_b = ttk.Frame(actions, style="Panel.TFrame")
        row_b.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        row_b.columnconfigure((0, 1, 2, 3), weight=1)
        ttk.Button(row_b, text="Export JSON", command=self._export_json).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(row_b, text="Import JSON", command=self._import_json).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(row_b, text="Save .bat", command=self._save_bat).grid(row=0, column=2, sticky="ew", padx=(0, 8))
        ttk.Button(row_b, text="New wallpaper", command=self._next_wallpaper).grid(row=0, column=3, sticky="ew")


        # RIGHT tabs
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self.tabs = ttk.Notebook(right)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        # Preview tab
        self.preview_tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=10)
        self.preview_tab.columnconfigure(0, weight=1)
        self.preview_tab.rowconfigure(1, weight=1)
        self.tabs.add(self.preview_tab, text="Preview")

        self.preview_heading = ttk.Label(self.preview_tab, text="Preview", style="Heading.TLabel")
        self.preview_heading.grid(row=0, column=0, sticky="w")

        self.card = ttk.Frame(self.preview_tab, style="Card.TFrame", padding=12)
        self.card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        # Two columns: text on the left, mascot on the right (no overlap).
        self.card.columnconfigure(0, weight=1)
        self.card.columnconfigure(1, weight=0)
        self.card.rowconfigure(1, weight=1)

        self.preview_title = ttk.Label(self.card, text="")
        self.preview_title.grid(row=0, column=0, sticky="w")

        self.preview_body = tk.Text(self.card, height=10, wrap="word", state="disabled", highlightthickness=1)
        self.preview_body.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        self.preview_meta = ttk.Label(self.card, text="", style="Muted.TLabel")
        self.preview_meta.grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Mascot lives inside the preview card so it never blocks text or buttons.
        self.mascot_slot = ttk.Frame(self.card, style="Card.TFrame")
        self.mascot_slot.grid(row=0, column=1, rowspan=3, sticky="se", padx=(14, 0))

        # History tab
        self.history_tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=10)
        self.history_tab.columnconfigure(0, weight=1)
        self.history_tab.rowconfigure(1, weight=1)
        self.tabs.add(self.history_tab, text="History")

        ttk.Label(self.history_tab, text="History", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.history_list = tk.Listbox(self.history_tab, height=10)
        self.history_list.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        hist_btns = ttk.Frame(self.history_tab, style="Panel.TFrame")
        hist_btns.grid(row=2, column=0, sticky="e", pady=(10, 0))
        ttk.Button(hist_btns, text="Clear", command=self._clear_history).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(hist_btns, text="Copy selected", command=self._copy_history_selected).grid(row=0, column=1)

        # About tab
        self.about_tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=10)
        self.tabs.add(self.about_tab, text="About")
        ttk.Label(self.about_tab, text="About", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            self.about_tab,
            text="Tip: put backgrounds in assets/backgrounds/ as anime_bg_*.png\nMascots: assets/mascot_*.png",
            style="Muted.TLabel",
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        # Batch tab
        self.batch_tab = ttk.Frame(self.tabs, style="Panel.TFrame", padding=10)
        self.batch_tab.columnconfigure(0, weight=1)
        self.batch_tab.rowconfigure(1, weight=1)
        self.tabs.add(self.batch_tab, text="Batch (.bat)")

        ttk.Label(self.batch_tab, text="Batch (.bat)", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.batch_text = ScrolledText(self.batch_tab, wrap="none", height=10, highlightthickness=1)
        self.batch_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.batch_text.configure(state="disabled")

        b_btns = ttk.Frame(self.batch_tab, style="Panel.TFrame")
        b_btns.grid(row=2, column=0, sticky="e", pady=(10, 0))
        ttk.Button(b_btns, text="Copy .bat", command=self._on_copy_bat).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(b_btns, text="Save .bat", command=self._save_bat).grid(row=0, column=1)

        # Status bar (on root, below the main frame)
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor="w", padding=(12, 6))
        self.status_bar.grid(row=1, column=0, sticky="ew")
        self.status_bar.lift()


    def _wire(self) -> None:
        self.theme_var.trace_add("write", lambda *_: self._apply_selected_theme())
        self.preset_var.trace_add("write", lambda *_: self._apply_preset())
        self.root.bind("<Control-r>", lambda _e: self._next_wallpaper())
        self.title_var.trace_add("write", lambda *_: self._refresh_preview())
        self.buttons_var.trace_add("write", lambda *_: self._refresh_preview())
        self.icon_var.trace_add("write", lambda *_: self._refresh_preview())
        self.topmost_var.trace_add("write", lambda *_: self._refresh_preview())
        self.title_var.trace_add("write", lambda *_: self._refresh_batch())
        self.buttons_var.trace_add("write", lambda *_: self._refresh_batch())
        self.icon_var.trace_add("write", lambda *_: self._refresh_batch())
        self.topmost_var.trace_add("write", lambda *_: self._refresh_batch())
        self.message_text.bind("<KeyRelease>", lambda _e: (self._refresh_preview(), self._refresh_batch()))

        self.root.bind("<Configure>", lambda _e: self._schedule_bg_redraw())

    # ---------------- Theme / styling ----------------

    def _apply_selected_theme(self) -> None:
        self.theme = next((t for t in self.themes if t.name == self.theme_var.get()), self.themes[0])
        apply_theme(self.root, self.theme)

        self.heading_label.configure(font=self.theme.heading_font)
        self.preview_heading.configure(font=self.theme.heading_font)

        # ScrolledText is a Text subclass
        self._apply_text_theme(self.message_text)
        self._apply_text_theme(self.preview_body)
        self._apply_text_theme(self.batch_text)
        self._apply_listbox_theme(self.history_list)

        # wallpaper is separate
        self._apply_wallpaper_for_theme()

    def _apply_text_theme(self, widget: tk.Text) -> None:
        widget.configure(
            bg=self.theme.text_bg,
            fg=self.theme.text_fg,
            insertbackground=self.theme.text_fg,
            highlightbackground=self.theme.border,
            highlightcolor=self.theme.accent,
        )

    def _apply_listbox_theme(self, widget: tk.Listbox) -> None:
        widget.configure(
            bg=self.theme.text_bg,
            fg=self.theme.text_fg,
            highlightthickness=1,
            highlightbackground=self.theme.border,
            highlightcolor=self.theme.accent,
            selectbackground=self.theme.accent,
        )

    # ---------------- Presets ----------------

    def _apply_preset(self) -> None:
        key = self.preset_var.get()
        if key not in MESSAGE_PRESETS:
            return

        title, msg, buttons, icon = MESSAGE_PRESETS[key]
        self.title_var.set(title)
        self.buttons_var.set(buttons)
        self.icon_var.set(icon)

        self.message_text.delete("1.0", "end")
        self.message_text.insert("1.0", msg)

        self._refresh_preview()

    # ---------------- Mascot ----------------

    def _place_mascot(self) -> None:
        if not self.mascot_img:
            return

        # Put the mascot in the preview card sidebar so it never covers text.
        parent = getattr(self, "mascot_slot", self)
        self.mascot_label = ttk.Label(parent, image=self.mascot_img)
        self.mascot_label.grid(row=0, column=0, sticky="se")

    def _random_mascot(self) -> None:
        mascots = _list_mascots(self.asset_dir)
        if not mascots:
            self.status_var.set("No mascots found in assets/")
            return

        picked = random.choice(mascots)
        new_img = _load_photo(picked)
        if not new_img:
            self.status_var.set("Could not load that mascot image.")
            return

        self.mascot_img = new_img
        if self.mascot_label:
            self.mascot_label.configure(image=self.mascot_img)
        else:
            self._place_mascot()

        self.status_var.set(f"Mascot: {picked.name}")

    # ---------------- Core logic ----------------

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

    def _refresh_batch(self) -> None:
        cfg = self._get_cfg()
        script = build_bat_script(cfg)
        self.batch_text.configure(state="normal")
        self.batch_text.delete("1.0", "end")
        self.batch_text.insert("1.0", script)
        self.batch_text.configure(state="disabled")

    def _on_show(self) -> None:
        cfg = self._get_cfg()
        self.status_var.set("Showing message box...")

        try:
            result = show_messagebox(cfg)
            clicked = RESULT_LABELS.get(result, f"Code {result}")
            self.status_var.set(f"User clicked: {clicked}")

            stamp = datetime.now().strftime("%H:%M:%S")
            line = f"[{stamp}] {cfg.title} | {self.icon_var.get()} | {self.buttons_var.get()} -> {clicked}"
            self._add_history(line)

        except Exception as exc:
            self.status_var.set(f"Error: {exc}")

    def _on_copy_snippet(self) -> None:
        cfg = self._get_cfg()
        flags_line = f"flags = {cfg.buttons} | {cfg.icon}"
        if cfg.topmost:
            flags_line += " | 0x00040000"

        snippet = (
            "import ctypes\n\n"
            f"title = {cfg.title!r}\n"
            f"message = {cfg.message!r}\n"
            f"{flags_line}\n"
            "ctypes.windll.user32.MessageBoxW(0, message, title, flags)\n"
        )

        self.root.clipboard_clear()
        self.root.clipboard_append(snippet)
        self.status_var.set("Copied snippet to clipboard.")

    def _on_copy_bat(self) -> None:
        cfg = self._get_cfg()
        script = build_bat_script(cfg)
        self.root.clipboard_clear()
        self.root.clipboard_append(script)
        self.status_var.set("Copied .bat script to clipboard.")

    def _save_bat(self) -> None:
        cfg = self._get_cfg()
        script = build_bat_script(cfg)
        path = filedialog.asksaveasfilename(
            title="Save .bat",
            defaultextension=".bat",
            filetypes=[("Batch files", "*.bat")],
        )
        if not path:
            return
        Path(path).write_text(script, encoding="utf-8")
        self.status_var.set("Saved .bat script.")

    # ---------------- History / JSON ----------------

    def _add_history(self, line: str) -> None:
        self.history.append(line)
        self.history_list.insert("end", line)

    def _clear_history(self) -> None:
        self.history.clear()
        self.history_list.delete(0, "end")
        self.status_var.set("History cleared.")

    def _copy_history_selected(self) -> None:
        sel = self.history_list.curselection()
        if not sel:
            self.status_var.set("No history item selected.")
            return
        text = self.history_list.get(sel[0])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_var.set("Copied selected history item.")

    def _export_json(self) -> None:
        cfg = self._get_cfg()
        data = {
            "title": cfg.title,
            "message": cfg.message,
            "buttons": self.buttons_var.get(),
            "icon": self.icon_var.get(),
            "topmost": cfg.topmost,
            "theme": self.theme.name,
            "preset": self.preset_var.get(),
        }

        path = filedialog.asksaveasfilename(
            title="Export config",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return

        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.status_var.set("Exported config JSON.")

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(
            title="Import config",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return

        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.title_var.set(data.get("title", "Message"))
            self.buttons_var.set(data.get("buttons", "OK"))
            self.icon_var.set(data.get("icon", "Info (i)"))
            self.topmost_var.set(bool(data.get("topmost", False)))

            theme_name = data.get("theme")
            if theme_name:
                self.theme_var.set(theme_name)

            self.message_text.delete("1.0", "end")
            self.message_text.insert("1.0", data.get("message", "Hello!"))

            self._refresh_preview()
            self.status_var.set("Imported config JSON.")
        except Exception as exc:
            messagebox.showerror("Import failed", f"Could not import JSON:\n{exc}")
