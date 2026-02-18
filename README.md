# 🪟 Windows MessageBox Generator

A fully featured **GUI MessageBox builder** for Windows built with
**Tkinter + ctypes**.\
Design native Win32 message boxes, preview them, export configs, and
generate `.bat` scripts automatically.

------------------------------------------------------------------------

## ✨ Features

-   🖥️ Native Windows MessageBox (via `ctypes`)
-   🎨 Multiple UI themes (Light, Dark, Neon, Pink, Anime Night)
-   🖼️ Wallpaper system (Anime Night mode)
-   🧍 Random mascot support (`assets/mascot_*.png`)
-   📜 History logging
-   💾 Export / Import JSON configs
-   📋 Copy ready-to-use Python snippet
-   📦 Generate full `.bat` script (PowerShell-backed)
-   🔝 Optional TopMost flag
-   🧠 Preset message templates

------------------------------------------------------------------------

## 📁 Project Structure

    Windows_MessageBox_Generator/
    ├── assets/
    │   └── backgrounds/
    ├── configs/
    ├── main.py
    ├── ui.py
    ├── themes.py
    ├── winbox.py
    └── CREDITS.txt

------------------------------------------------------------------------

## 🚀 How To Run

### Requirements

-   Python 3.10+
-   Windows OS (required for native MessageBox)
-   Pillow

Install dependencies:

    pip install pillow

Run:

    python main.py

------------------------------------------------------------------------

## 📦 Batch Script Generator

Generates a fully self-contained `.bat` file using PowerShell +\
`System.Windows.Forms.MessageBox`.

-   Proper newline handling
-   Proper escaping for CMD
-   Returns correct exit codes
-   Supports TopMost owner window

------------------------------------------------------------------------

## 🎨 Themes

Included themes:

-   Light
-   Dark
-   Neon
-   Pink
-   Anime Night (with dynamic wallpapers)

Anime Night loads wallpapers from:

    assets/backgrounds/anime_bg_*.png

------------------------------------------------------------------------

## 💾 JSON Config Export Example

``` json
{
  "title": "Access denied",
  "message": "You do not have permission to perform this action.",
  "buttons": "OK",
  "icon": "Error (X)",
  "topmost": false,
  "theme": "Dark",
  "preset": "Permission denied"
}
```

------------------------------------------------------------------------

## 🧑‍💻 Author

Built by **Nokky07**
