from __future__ import annotations

from pathlib import Path
import tkinter as tk

from ui import App
from themes import THEMES


def terminal() -> None:
    print("MessageBox Builder has exited. You can view any print statements here.")



def main() -> None:
    root = tk.Tk()
    root.attributes("-alpha", 1.0)
    root.title("MessageBox Builder")
    # Bigger default window so the two-pane layout doesn't feel cramped.
    root.geometry("1020x620")
    root.minsize(980, 560)

    # Prefer ./assets but fall back to the script folder so the app still runs
    # if you haven't created the assets directory yet.
    asset_dir = Path(__file__).parent / "assets"
    if not asset_dir.exists():
        asset_dir = Path(__file__).parent
    App(root, themes=THEMES, asset_dir=asset_dir)

    root.mainloop()


if __name__ == "__main__":
    main()
    terminal()
