from __future__ import annotations

from pathlib import Path
import tkinter as tk

from ui import App
from themes import THEMES


def main() -> None:
    root = tk.Tk()
    root.title("MessageBox Builder")
    root.minsize(820, 460)

    asset_dir = Path(__file__).parent / "assets"
    App(root, themes=THEMES, asset_dir=asset_dir)

    root.mainloop()


if __name__ == "__main__":
    main()
