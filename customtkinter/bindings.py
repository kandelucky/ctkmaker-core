"""Live variable-binding helpers for CTkMaker-exported applications.

These helpers used to be inlined verbatim into every CTkMaker-exported
`.py` file via the editor's ``auto_trace_templates.py``. Moving them
here keeps generated code thin — exports import the relevant helper(s)
from ``customtkinter`` and call them, instead of carrying 200-300 lines
of duplicated runtime code.

Each ``bind_var_to_*`` subscribes a ``tk.*Var`` to a write trace and
mirrors the variable's value into a CTkMaker widget's native CTk
configuration (``configure(prop=...)`` for direct properties; custom
rebuilders for composites that CTk doesn't expose as a single
``configure`` kwarg, such as font weight/size).

Maker-only conventions consumed:
- ``widget._maker_label_tint`` — dict ``{"color", "color_disabled",
  "enabled"}`` placed on a CTkLabel at construction time so the tint
  helpers can re-resolve which tint to apply on enable / disable
  toggles.
- ``widget._ctkmaker_fixed`` / ``_ctkmaker_min`` / ``_ctkmaker_image``
  — attributes on flex-pack children read by ``balance_pack`` to
  honour user-locked sizes, content floors, and CTkImage size sync.

These attributes are set by CTkMaker's exporter; the fork module reads
them via ``getattr`` so widgets that lack them stay safe.
"""

from __future__ import annotations

import tkinter.font as _tkfont
from typing import Any

from .windows.widgets.font import CTkFont


def bind_var_to_widget(var, widget, prop: str) -> None:
    """Mirror ``var.get()`` into ``widget.configure(prop=…)`` on every
    write. Initial sync on attach so the widget paints the var's current
    value even if the constructor kwarg already set it to the same
    literal.
    """
    def _update(*_):
        widget.configure(**{prop: var.get()})
    var.trace_add("write", _update)
    _update()


def bind_var_to_textbox(var, tb) -> None:
    """Mirror ``var.get()`` into a CTkTextbox's content via
    delete+insert. CTkTextbox has no ``textvariable=`` support, so
    every change rewrites the whole buffer.
    """
    def _update(*_):
        tb.delete("1.0", "end")
        tb.insert("1.0", var.get())
    var.trace_add("write", _update)
    _update()


def bind_var_to_font(var, widget, attr: str) -> None:
    """Rebuild ``widget``'s CTkFont when ``var`` changes — for
    ``font_bold`` / ``font_italic`` / ``font_size`` / ``font_family`` /
    ``font_underline`` / ``font_overstrike`` bindings. ``attr`` is the
    CTkFont kwarg name to update; the other five attributes are
    preserved so a bold toggle doesn't also reset size or italic.
    """
    def _update(*_):
        current = widget.cget("font")
        kwargs = dict(
            family=current.cget("family"),
            size=current.cget("size"),
            weight=current.cget("weight"),
            slant=current.cget("slant"),
            underline=current.cget("underline"),
            overstrike=current.cget("overstrike"),
        )
        value = var.get()
        if attr == "weight":
            kwargs["weight"] = "bold" if value else "normal"
        elif attr == "slant":
            kwargs["slant"] = "italic" if value else "roman"
        elif attr == "size":
            kwargs["size"] = int(value)
        elif attr == "family":
            kwargs["family"] = str(value)
        elif attr == "underline":
            kwargs["underline"] = bool(value)
        elif attr == "overstrike":
            kwargs["overstrike"] = bool(value)
        else:
            return
        widget.configure(font=CTkFont(**kwargs))
    var.trace_add("write", _update)
    _update()


def bind_var_to_state(var, widget) -> None:
    """Map ``var.get()`` (bool) to ``widget.configure(state=…)``.
    True → "normal", False → "disabled". Used for ``button_enabled``
    bindings where the variable type is bool but CTk's kwarg is a
    string enum.
    """
    def _update(*_):
        widget.configure(state="normal" if bool(var.get()) else "disabled")
    var.trace_add("write", _update)
    _update()


def bind_var_to_label_enabled(var, widget, color_on, color_off) -> None:
    """Map ``var.get()`` (bool) to a CTkLabel text_color swap. True →
    ``color_on``, False → ``color_off``. Also re-resolves
    ``image_color`` from ``widget._maker_label_tint`` when present so a
    tinted icon follows the enabled flag.
    """
    def _update(*_):
        enabled = bool(var.get())
        widget.configure(text_color=color_on if enabled else color_off)
        s = getattr(widget, "_maker_label_tint", None)
        if s is not None:
            s["enabled"] = enabled
            active = (
                s["color_disabled"]
                if (not enabled and s["color_disabled"])
                else s["color"]
            )
            try:
                widget.configure(image_color=active)
            except Exception:
                pass
    var.trace_add("write", _update)
    _update()


def bind_var_to_font_wrap(var, widget) -> None:
    """Map ``var.get()`` (bool) to a CTkLabel wraplength swap. True →
    derive ``wraplength`` from the widget's current width (minus 8px
    breathing room); False → ``wraplength=0`` (no wrap).
    """
    def _update(*_):
        if var.get():
            try:
                w = int(widget.cget("width") or 100)
            except (TypeError, ValueError):
                w = 100
            widget.configure(wraplength=max(1, w - 8))
        else:
            widget.configure(wraplength=0)
    var.trace_add("write", _update)
    _update()


def bind_var_to_place_coord(var, widget, axis: str) -> None:
    """Map ``var.get()`` (int / float) to ``widget.place_configure(x=…)``
    or ``place_configure(y=…)`` depending on ``axis``. No-op for widgets
    not using place layout (``place_configure`` on a non-place widget
    silently does nothing).
    """
    def _update(*_):
        try:
            val = int(var.get())
        except (TypeError, ValueError):
            return
        try:
            widget.place_configure(**{axis: val})
        except Exception:
            pass
    var.trace_add("write", _update)
    _update()


def _maker_ctkimage(widget) -> Any:
    """Return the widget's CTkImage, or None when it has no CTkImage."""
    # Local import: CTkImage lives deep in the package, and avoiding a
    # top-level import here lets bindings.py be imported by tools that
    # don't initialise the image subsystem.
    from .windows.widgets.image import CTkImage
    try:
        img = widget.cget("image")
    except Exception:
        return None
    return img if isinstance(img, CTkImage) else None


def bind_var_to_image_path(var, widget) -> None:
    """Map ``var.get()`` (str path) to the widget's CTkImage source —
    reopens the PIL file and swaps light/dark images on the existing
    CTkImage, keeping its size + preserve_aspect.
    """
    from PIL import Image as _PILImage

    def _update(*_):
        img = _maker_ctkimage(widget)
        path = var.get() or ""
        if img is None or not path:
            return
        try:
            src = _PILImage.open(path)
            img.configure(light_image=src, dark_image=src)
        except Exception:
            pass
    var.trace_add("write", _update)
    _update()


def bind_var_to_image_size(var, widget, axis: str) -> None:
    """Map ``var.get()`` (int) to one axis of the widget's CTkImage
    size. ``axis`` is ``"width"`` or ``"height"``.
    """
    def _update(*_):
        img = _maker_ctkimage(widget)
        if img is None:
            return
        try:
            new = max(1, int(var.get()))
        except (TypeError, ValueError):
            return
        w, h = img.cget("size")
        img.configure(size=(new, h) if axis == "width" else (w, new))
    var.trace_add("write", _update)
    _update()


def bind_var_to_preserve_aspect(var, widget) -> None:
    """Map ``var.get()`` (bool) to the widget's CTkImage
    ``preserve_aspect`` — contain-fit vs stretch.
    """
    def _update(*_):
        img = _maker_ctkimage(widget)
        if img is not None:
            img.configure(preserve_aspect=bool(var.get()))
    var.trace_add("write", _update)
    _update()


def bind_var_to_image_color(var, widget) -> None:
    """Map ``var.get()`` to the widget's native ``image_color`` kwarg.
    "" / "transparent" clear the tint.
    """
    def _update(*_):
        c = var.get() or None
        if c == "transparent":
            c = None
        try:
            widget.configure(image_color=c)
        except Exception:
            pass
    var.trace_add("write", _update)
    _update()


def bind_var_to_image_color_disabled(var, widget) -> None:
    """Map ``var.get()`` to the widget's native ``image_color_disabled``
    kwarg (CTkButton only — CTkLabel resolves its disabled tint via
    ``bind_var_to_label_image_tint`` because CTkLabel has no native
    ``image_color_disabled`` kwarg).
    """
    def _update(*_):
        c = var.get() or None
        if c == "transparent":
            c = None
        try:
            widget.configure(image_color_disabled=c)
        except Exception:
            pass
    var.trace_add("write", _update)
    _update()


def bind_var_to_label_image_tint(var, widget, key: str) -> None:
    """CTkLabel-only — ``image_color`` / ``image_color_disabled`` bound
    to a var. The label has no native ``image_color_disabled`` kwarg, so
    re-resolve the active tint through ``widget._maker_label_tint``:
    disabled + a disabled colour → that colour, else the normal colour.
    ``key`` is ``"color"`` or ``"color_disabled"``.
    """
    def _update(*_):
        s = getattr(widget, "_maker_label_tint", None)
        if s is None:
            return
        c = var.get() or None
        s[key] = None if c == "transparent" else c
        active = (
            s["color_disabled"]
            if (not s["enabled"] and s["color_disabled"])
            else s["color"]
        )
        try:
            widget.configure(image_color=active)
        except Exception:
            pass
    var.trace_add("write", _update)
    _update()


def bind_var_to_font_autofit(var, widget, size_off: int) -> None:
    """Map ``var.get()`` (bool) to CTkLabel font-size autofit. True →
    binary-search the largest font size that fits the widget's current
    text inside its current width/height. False → restore the original
    ``size_off`` captured at construction.
    """
    def _wrap_lines(font, text, max_w):
        lines = []
        for paragraph in str(text).split("\n"):
            if not paragraph:
                lines.append("")
                continue
            cur = ""
            for word in paragraph.split(" "):
                trial = word if not cur else cur + " " + word
                if font.measure(trial) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines or [""]

    def _compute(text, width, height, bold, wrap):
        avail_w = max(10, int(width) - 12)
        avail_h = max(10, int(height) - 4)
        weight = "bold" if bold else "normal"
        lo, hi, best = 6, 96, 6
        while lo <= hi:
            mid = (lo + hi) // 2
            try:
                f = _tkfont.Font(size=mid, weight=weight)
                line_h = f.metrics("linespace")
                if wrap:
                    lns = _wrap_lines(f, text, avail_w)
                    tw = max((f.measure(L) for L in lns), default=0)
                    th = line_h * len(lns)
                else:
                    tw = f.measure(text)
                    th = line_h
            except Exception:
                return 13
            if tw <= avail_w and th <= avail_h:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return best

    def _rebuild_font(new_size):
        current = widget.cget("font")
        widget.configure(font=CTkFont(
            family=current.cget("family"),
            size=int(new_size),
            weight=current.cget("weight"),
            slant=current.cget("slant"),
            underline=current.cget("underline"),
            overstrike=current.cget("overstrike"),
        ))

    def _update(*_):
        if var.get():
            try:
                text = widget.cget("text") or ""
                width = int(widget.cget("width") or 100)
                height = int(widget.cget("height") or 28)
                current_font = widget.cget("font")
                bold = current_font.cget("weight") == "bold"
                wrap = int(widget.cget("wraplength") or 0) > 0
            except Exception:
                return
            _rebuild_font(_compute(text, width, height, bold, wrap))
        else:
            _rebuild_font(size_off)
    var.trace_add("write", _update)
    _update()


def balance_pack(container, axis: str) -> None:
    """Flex-shrink pack children along ``axis`` ("width" or "height")
    when the container drops below the sum of their nominal sizes.
    Honours ``_ctkmaker_fixed=True`` (skip — keeps the user-locked
    size) and ``_ctkmaker_min`` (per-child content floor so text + icon
    never clip). Mirrors CTkMaker's canvas preview hbox/vbox auto-shrink
    semantics so the exported app matches the editor.

    All math runs in CTk's widget-scaling units, not raw pixels —
    ``configure(width=N)`` on a CTk widget multiplies N by the
    container's DPI scaling factor before resizing the underlying tk
    widget, so feeding raw winfo_width() in would over-allocate on
    hi-DPI displays (e.g. 1.5x scaling renders an 80-CTk-unit button at
    120 raw px; mixing the two units leaves later siblings starved at
    1 px).
    """
    children = container.pack_slaves()
    if not children:
        return
    # CTkScrollableFrame is itself the inner tk.Frame; its winfo_*
    # returns the grown content size, so flex math against it never
    # shrinks anything. Read from the outer ``_parent_canvas`` instead
    # when present — that's the actual viewport.
    size_source = getattr(container, "_parent_canvas", None) or container
    if axis == "width":
        raw_size = size_source.winfo_width()
        pad_key = "padx"
    else:
        raw_size = size_source.winfo_height()
        pad_key = "pady"
    if raw_size <= 1:
        return
    # CTk's root window doesn't expose ``_get_widget_scaling`` — only
    # nested CTkBaseClass widgets do — so ask the first scaling-aware
    # child instead. Falls back to 1.0 for pure-tk parents.
    scale = 1.0
    try:
        scale = float(container._get_widget_scaling())
    except (AttributeError, Exception):
        for c in children:
            try:
                scale = float(c._get_widget_scaling())
                break
            except (AttributeError, Exception):
                continue
    if scale <= 0:
        scale = 1.0
    container_size = int(raw_size / scale)
    spacing_total = 0
    fixed_total = 0
    grow_kids = []
    for c in children:
        try:
            info = c.pack_info()
        except Exception:
            continue
        pad = info.get(pad_key, 0)
        if isinstance(pad, tuple):
            spacing_raw = int(pad[0]) + int(pad[1])
        else:
            spacing_raw = int(pad) * 2
        spacing_total += int(spacing_raw / scale)
        if getattr(c, "_ctkmaker_fixed", False):
            try:
                fixed_total += int(c.cget(axis))
            except Exception:
                fixed_total += int(
                    (c.winfo_reqwidth() if axis == "width"
                     else c.winfo_reqheight()) / scale,
                )
        else:
            grow_kids.append(c)
    if not grow_kids:
        return
    avail = max(1, container_size - fixed_total - spacing_total)
    slot = max(1, avail // len(grow_kids))
    for c in grow_kids:
        floor = getattr(c, "_ctkmaker_min", 1)
        target = max(floor, slot)
        # Image (CTkLabel + CTkImage) needs the embedded CTkImage
        # resized explicitly — configuring the label alone leaves the
        # picture at its constructor-time size.
        if getattr(c, "_ctkmaker_image", False):
            ctk_img = getattr(c, "_image", None)
            if ctk_img is not None:
                try:
                    cur_size = ctk_img.cget("size")
                    if axis == "width":
                        ctk_img.configure(size=(target, cur_size[1]))
                    else:
                        ctk_img.configure(size=(cur_size[0], target))
                except Exception:
                    pass
        try:
            c.configure(**{axis: target})
        except Exception:
            pass
