"""Keyboard fixes for Tk on Windows (primary target) + cross-platform
clipboard / context-menu plumbing for tk.Entry and tk.Text.

Two fixes live here:

1. Windows Unicode keyboard recovery — Tk 8.6 decodes WM_CHAR through the
   ANSI codepage. Characters outside cp1252 (Georgian, Armenian, Devanagari,
   Thai, ...) arrive as '?' even though Windows delivered the proper Unicode
   codepoint. attach_unicode_keyboard_recovery() binds <KeyPress>; when Tk
   delivers char='?'/keysym='??', the handler queries Win32 ToUnicodeEx and
   inserts the recovered character. Paste is unaffected (CF_UNICODETEXT is
   already UTF-16). No-op on macOS / Linux.

2. Cross-platform clipboard shortcut router + right-click context menu —
   Tk's default <Control-c> / <Command-c> bindings match by keysym, so non-
   Latin keyboard layouts (where keysym='??') silently break Copy / Paste /
   Cut / SelectAll. The router falls back to the hardware keycode. Right-
   click on Entry / Text opens a tk.Menu with the four actions.

Both fixes are installed automatically via a monkey-patch on tkinter.Entry
and tkinter.Text __init__ — covering CTk-wrapped widgets and any raw tk.Entry
/ tk.Text created outside CTk (e.g. inline editors in app code).
"""

import sys
import tkinter


# --- Cross-platform clipboard router + right-click menu ---------------------

if sys.platform == "darwin":
    _MODIFIER_KEYPRESS = "<Command-KeyPress>"
    _RIGHT_CLICK_EVENTS = ("<Button-2>", "<Control-Button-1>")
    # macOS kVK_ANSI codes — best-effort, untested on actual Mac hardware.
    # Worst case on Mac is "same as before" (Tk's default Latin-only binding);
    # we never regress because the Latin keysym branch short-circuits below.
    _CLIPBOARD_KEYCODES = {8: "<<Copy>>", 9: "<<Paste>>", 7: "<<Cut>>", 0: "<<SelectAll>>"}
else:
    _MODIFIER_KEYPRESS = "<Control-KeyPress>"
    _RIGHT_CLICK_EVENTS = ("<Button-3>",)
    # Windows VK codes — Linux X11 keycodes differ but match status quo of
    # CTkMaker's previous workaround. Non-Latin Linux users were already
    # unhelped by that code; this is not a regression for them.
    _CLIPBOARD_KEYCODES = {67: "<<Copy>>", 86: "<<Paste>>", 88: "<<Cut>>", 65: "<<SelectAll>>"}


def _on_clipboard_modifier(event):
    # Latin keysym → Tk's default <Control-c>/<Command-c> already fired.
    if event.keysym.lower() in ("v", "c", "x", "a"):
        return None
    action = _CLIPBOARD_KEYCODES.get(event.keycode)
    if action is None:
        return None
    try:
        event.widget.event_generate(action)
    except tkinter.TclError:
        return None
    return "break"


def _on_right_click_popup(event):
    widget = event.widget
    has_sel = False
    try:
        has_sel = bool(widget.selection_present())
    except Exception:
        try:
            has_sel = bool(widget.tag_ranges("sel"))
        except Exception:
            has_sel = False
    menu = tkinter.Menu(widget, tearoff=0)
    menu.add_command(
        label="Cut",
        state="normal" if has_sel else "disabled",
        command=lambda: widget.event_generate("<<Cut>>"),
    )
    menu.add_command(
        label="Copy",
        state="normal" if has_sel else "disabled",
        command=lambda: widget.event_generate("<<Copy>>"),
    )
    menu.add_command(
        label="Paste",
        command=lambda: widget.event_generate("<<Paste>>"),
    )
    menu.add_separator()
    menu.add_command(
        label="Select All",
        command=lambda: widget.event_generate("<<SelectAll>>"),
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


_class_bindings_installed = False


def _install_class_bindings_once(any_widget):
    global _class_bindings_installed
    if _class_bindings_installed:
        return
    _class_bindings_installed = True
    for cls in ("Entry", "Text"):
        any_widget.bind_class(cls, _MODIFIER_KEYPRESS, _on_clipboard_modifier, add=True)
        for evt in _RIGHT_CLICK_EVENTS:
            any_widget.bind_class(cls, evt, _on_right_click_popup, add=True)


# --- Windows-only Unicode keyboard recovery ---------------------------------

if sys.platform.startswith("win"):
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32", use_last_error=True)

    _user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    _user32.GetKeyboardLayout.restype = wintypes.HKL

    _user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    _user32.GetKeyboardState.restype = wintypes.BOOL

    _user32.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HKL]
    _user32.MapVirtualKeyExW.restype = wintypes.UINT

    _user32.ToUnicodeEx.argtypes = [
        wintypes.UINT, wintypes.UINT,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_wchar_p, ctypes.c_int,
        wintypes.UINT, wintypes.HKL,
    ]
    _user32.ToUnicodeEx.restype = ctypes.c_int

    _MAPVK_VK_TO_VSC = 0
    _RECOVERY_ATTR = "_ctk_unicode_recovery_attached"

    def _vk_to_unicode(vk_code):
        state = (ctypes.c_ubyte * 256)()
        if not _user32.GetKeyboardState(state):
            return None
        layout = _user32.GetKeyboardLayout(0)
        scan = _user32.MapVirtualKeyExW(vk_code, _MAPVK_VK_TO_VSC, layout)
        buf = ctypes.create_unicode_buffer(8)
        n = _user32.ToUnicodeEx(vk_code, scan, state, buf, len(buf), 0, layout)
        if n > 0:
            return buf.value[:n]
        return None

    def _on_keypress(event):
        if event.char == "?" and event.keysym == "??":
            try:
                recovered = _vk_to_unicode(event.keycode)
            except Exception:
                return None
            if recovered:
                try:
                    event.widget.insert(event.widget.index("insert"), recovered)
                except Exception:
                    return None
                return "break"
        return None

    def attach_unicode_keyboard_recovery(tk_widget):
        if getattr(tk_widget, _RECOVERY_ATTR, False):
            return
        setattr(tk_widget, _RECOVERY_ATTR, True)
        tk_widget.bind("<KeyPress>", _on_keypress, add=True)

else:
    def attach_unicode_keyboard_recovery(tk_widget):
        pass


# --- Monkey-patch tk.Entry / tk.Text (cross-platform) -----------------------

_orig_entry_init = tkinter.Entry.__init__
_orig_text_init = tkinter.Text.__init__


def _patched_entry_init(self, *args, **kwargs):
    _orig_entry_init(self, *args, **kwargs)
    attach_unicode_keyboard_recovery(self)
    _install_class_bindings_once(self)


def _patched_text_init(self, *args, **kwargs):
    _orig_text_init(self, *args, **kwargs)
    attach_unicode_keyboard_recovery(self)
    _install_class_bindings_once(self)


tkinter.Entry.__init__ = _patched_entry_init
tkinter.Text.__init__ = _patched_text_init
