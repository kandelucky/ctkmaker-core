"""Project font registration helper.

Exposes ``register_project_fonts(root, fonts_dir)`` so applications can
register bundled `.ttf` / `.otf` / `.ttc` files with the Tk root, making
``CTkFont(family=...)`` lookups resolve project-bundled families.

Soft dependency on ``tkextrafont``: if the package isn't installed, the
function is a no-op and bundled fonts won't load — system / Tk-default
fonts continue to render normally. This is intentional so a slim install
without ``tkextrafont`` still runs.

Primary consumer: CTkMaker's code exporter, which emits a single call
to this function at app startup instead of inlining the loader body
into every exported `.py` file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


_FONT_SUFFIXES = (".ttf", ".otf", ".ttc")


def register_project_fonts(root, fonts_dir: Union[str, "os.PathLike[str]"]) -> int:
    """Load every ``.ttf`` / ``.otf`` / ``.ttc`` in *fonts_dir* against *root*.

    Returns the number of font files successfully registered. A return of
    0 means either *fonts_dir* did not exist, ``tkextrafont`` was not
    installed, or no recognised font files were found — none of which
    raise.

    Parameters
    ----------
    root :
        The Tk root (``ctk.CTk`` / ``tk.Tk``) the fonts should attach to.
        Subsequent ``CTkFont(family=...)`` lookups created against this
        root (or any Toplevel sharing it) will find the registered
        families.
    fonts_dir :
        Directory containing the font files. Files at any deeper nesting
        are ignored — pass a flat folder.
    """
    path = Path(fonts_dir)
    if not path.exists():
        return 0
    try:
        from tkextrafont import Font  # type: ignore[import-not-found]
    except ImportError:
        return 0
    loaded = 0
    for entry in sorted(path.iterdir()):
        if entry.suffix.lower() in _FONT_SUFFIXES:
            try:
                Font(root, file=str(entry))
                loaded += 1
            except Exception:
                # A single corrupt file shouldn't prevent the rest from
                # loading. Soft-fail per file.
                pass
    return loaded
