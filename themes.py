from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

from matplotlib import style


@dataclass(frozen=True)
class Theme:
    name: str
    base_ttk_theme: str
    font: tuple
    heading_font: tuple

    bg: str
    fg: str
    panel: str
    card: str
    border: str
    accent: str
    text_bg: str
    text_fg: str
    muted: str


THEMES: list[Theme] = [
    Theme(
        name="Light",
        base_ttk_theme="vista",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        bg="#F5F6F8",
        fg="#111111",
        panel="#FFFFFF",
        card="#FFFFFF",
        border="#D6D9DE",
        accent="#2B7FFF",
        text_bg="#FFFFFF",
        text_fg="#111111",
        muted="#666666",
    ),
    Theme(
        name="Dark",
        base_ttk_theme="clam",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        bg="#0F1115",
        fg="#E8E8EA",
        panel="#151922",
        card="#111520",
        border="#262C39",
        accent="#7AA2FF",
        text_bg="#0C0F16",
        text_fg="#E8E8EA",
        muted="#A0A6B3",
    ),
    Theme(
        name="Neon",
        base_ttk_theme="clam",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        bg="#070A0F",
        fg="#EAF6FF",
        panel="#0D1220",
        card="#0A1020",
        border="#1B2B46",
        accent="#00D1FF",
        text_bg="#060A12",
        text_fg="#EAF6FF",
        muted="#96B2C5",
    ),
    Theme(
        name="Pink",
        base_ttk_theme="clam",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        bg="#FFF1F6",
        fg="#2B1B23",
        panel="#FFFFFF",
        card="#FFFFFF",
        border="#F2B6CF",
        accent="#FF4DA6",
        text_bg="#FFFFFF",
        text_fg="#2B1B23",
        muted="#7B4B5F",
    ),
    Theme(
        name="Anime Night",
        base_ttk_theme="clam",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        bg="#070913",
        fg="#F0F4FF",
        panel="#0B0F1C",
        card="#0E1528",
        border="#30384F",
        accent="#A78BFA",
        text_bg="#0E1322",
        text_fg="#F0F4FF",
        muted="#B8C0FF",
    ),
]


def apply_theme(root: tk.Tk, theme: Theme) -> None:
    style = ttk.Style(root)
    available = style.theme_names()

    if theme.base_ttk_theme in available:
        style.theme_use(theme.base_ttk_theme)
    else:
        style.theme_use("clam" if "clam" in available else available[0])

    root.option_add("*Font", theme.font)
    root.configure(background=theme.bg)

    style.configure("App.TFrame", background=theme.bg)
    style.configure("Panel.TFrame", background=theme.panel)
    style.configure("Card.TFrame", background=theme.card, relief="solid", borderwidth=1)

    style.configure("TLabel", background=theme.panel, foreground=theme.fg)
    style.configure("Heading.TLabel", background=theme.panel, foreground=theme.fg)
    style.configure("Muted.TLabel", background=theme.panel, foreground=theme.muted)

    style.configure("TButton", padding=7)
    style.configure("Accent.TButton", padding=7)
    style.configure("TPanedwindow", background=theme.bg)
    style.configure("TNotebook", background=theme.bg)
