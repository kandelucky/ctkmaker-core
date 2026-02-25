"""PyInstaller hook for customtkinter.

Ensures darkdetect submodules (platform-specific backends) are included
and customtkinter data files (themes, icons, fonts) are collected.
"""

from PyInstaller.utils.hooks import collect_data_files

# darkdetect uses platform-specific submodules that PyInstaller's
# static analysis cannot detect (they're imported conditionally at runtime).
hiddenimports = [
    "darkdetect",
    "darkdetect._dummy",
    "darkdetect._linux_detect",
    "darkdetect._mac_detect",
    "darkdetect._windows_detect",
]

# Collect all non-Python data files (themes, icons, fonts)
datas = collect_data_files("customtkinter")
