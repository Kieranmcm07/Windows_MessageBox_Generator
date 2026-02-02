from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk


@dataclass(frozen=True)
class Theme:
    name: str
    base_ttk_theme: str
    font: tuple
    heading_font: tuple
    card_padding: int


THEMES = [
    Theme(
        name="Windows Clean",
        base_ttk_theme="vista",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        card_padding=12,
    ),
    Theme(
        name="Minimal Dev",
        base_ttk_theme="clam",
        font=("Consolas", 10),
        heading_font=("Consolas", 13, "bold"),
        card_padding=10,
    ),
    Theme(
        name="Neon Gamer",
        base_ttk_theme="clam",
        font=("Segoe UI", 10),
        heading_font=("Segoe UI", 13, "bold"),
        card_padding=12,
    ),
]


def apply_theme(root: tk.Tk, theme: Theme) -> None:
    style = ttk.Style(root)
    available = style.theme_names()

    if theme.base_ttk_theme in available:
        style.theme_use(theme.base_ttk_theme)
    else:
        style.theme_use("clam" if "clam" in available else available[0])

    # A simple global font
    root.option_add("*Font", theme.font)

    # Card styling
    style.configure("Card.TFrame", relief="ridge", borderwidth=2 if theme.name == "Neon Gamer" else 1)

    # Small vibe differences (ttk is limited, but this helps)
    if theme.name == "Neon Gamer":
        style.configure("TButton", padding=7)
        style.configure("TLabel", padding=2)
    else:
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=1)
