from __future__ import annotations

import ctypes
from dataclasses import dataclass

# Buttons
MB_OK = 0x00000000
MB_OKCANCEL = 0x00000001
MB_ABORTRETRYIGNORE = 0x00000002
MB_YESNOCANCEL = 0x00000003
MB_YESNO = 0x00000004
MB_RETRYCANCEL = 0x00000005

# Icons
MB_ICONERROR = 0x00000010
MB_ICONQUESTION = 0x00000020
MB_ICONWARNING = 0x00000030
MB_ICONINFORMATION = 0x00000040

# Other
MB_TOPMOST = 0x00040000

# Return codes
IDOK = 1
IDCANCEL = 2
IDABORT = 3
IDRETRY = 4
IDIGNORE = 5
IDYES = 6
IDNO = 7

RESULT_LABELS = {
    IDOK: "OK",
    IDCANCEL: "Cancel",
    IDABORT: "Abort",
    IDRETRY: "Retry",
    IDIGNORE: "Ignore",
    IDYES: "Yes",
    IDNO: "No",
}


@dataclass(frozen=True)
class MessageBoxConfig:
    title: str
    message: str
    buttons: int
    icon: int
    topmost: bool = False


def show_messagebox(cfg: MessageBoxConfig) -> int:
    # Show a native Windows MessageBox and return the Win32 result code.
    flags = cfg.buttons | cfg.icon | (MB_TOPMOST if cfg.topmost else 0)
    return ctypes.windll.user32.MessageBoxW(0, cfg.message, cfg.title, flags)
