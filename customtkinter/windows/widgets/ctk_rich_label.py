"""CTkRichLabel — read-only label-like widget that renders Unity-style
rich-text tags (<b>, <i>, <u>, <color=...>, <size=N>, <bg=...>).

Built on CTkTextbox so we inherit CTk's CTkCanvas-rounded background
(corner_radius, border, fg_color) without re-implementing it. The inner
tk.Text is forced read-only, scrollbars hidden, cursor reset to arrow.
Every chunk renders with an explicit per-tag foreground so the
dark-theme etched ghost effect that `tk.Text` shows in state="disabled"
never applies.

Lives in the ctkmaker-core fork so CTkMaker exports can use
``from customtkinter import CTkRichLabel`` without inlining ~370 lines
of widget+parser code into every generated `.py`.
"""
from __future__ import annotations

import tkinter.font as tkfont
from typing import Optional

from .ctk_textbox import CTkTextbox
from .font import CTkFont
from .utility.rich_text_parser import Chunk, Style, parse


class CTkRichLabel(CTkTextbox):
    """Read-only rich-text label. Call ``set_text(rich_string)`` to
    update the displayed content."""

    def __init__(
        self,
        master,
        text: str = "",
        rich_text: bool = True,
        font: Optional[CTkFont | tuple] = None,
        text_color: str = "#dce4ee",
        fg_color: Optional[str] = "transparent",
        corner_radius: int = 0,
        border_width: int = 0,
        border_color: str = "#565b5e",
        wrap: str = "word",
        width: int = 200,
        height: int = 40,
        **kwargs,
    ):
        super().__init__(
            master,
            width=width,
            height=height,
            font=font,
            text_color=text_color,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=border_color,
            wrap=wrap,
            activate_scrollbars=False,
            **kwargs,
        )

        self._tag_cache: dict[Style, str] = {}
        self._rich_text = ""
        self._rich_text_enabled = bool(rich_text)

        # Read-only + cosmetic. ``insertontime=0`` hides the blinking
        # caret, ``cursor="arrow"`` keeps the mouse pointer from
        # switching to the I-beam (text-edit) cursor over a label, and
        # ``takefocus=0`` removes the widget from the Tab-focus chain.
        self._textbox.configure(
            insertontime=0,
            cursor="arrow",
            takefocus=0,
        )

        if text:
            self.set_text(text)

        # ``state="disabled"`` makes the inner tk.Text read-only without
        # affecting tag-foreground rendering. set_text temporarily flips
        # back to "normal" while inserting.
        self._textbox.configure(state="disabled")

    # ---- public API -------------------------------------------------

    def set_text(self, text: str) -> None:
        """Render the given text. If rich_text is enabled, tags are parsed
        and styled; otherwise the string is shown verbatim."""
        self._rich_text = text
        inner = self._textbox
        # Tag fonts/colors are baked at creation time from the widget's
        # current font + text_color. Drop the cache on every render so
        # property changes (font_size, text_color, bold, …) actually take
        # effect — cached tags would otherwise pin the old values.
        for old_tag in self._tag_cache.values():
            try:
                inner.tag_delete(old_tag)
            except Exception:
                pass
        self._tag_cache.clear()
        inner.configure(state="normal")
        try:
            inner.delete("1.0", "end")
            if self._rich_text_enabled:
                chunks = parse(text, self._compute_base_style())
                for ch in chunks:
                    tag = self._tag_for(ch.style)
                    inner.insert("end", ch.text, tag)
            else:
                tag = self._tag_for(self._compute_base_style())
                inner.insert("end", text, tag)
        finally:
            inner.configure(state="disabled")

    def get_text(self) -> str:
        return self._rich_text

    def set_rich_text_enabled(self, enabled: bool) -> None:
        """Toggle rich-text parsing. Re-renders the current text."""
        new_value = bool(enabled)
        if new_value == self._rich_text_enabled:
            return
        self._rich_text_enabled = new_value
        if self._rich_text:
            self.set_text(self._rich_text)

    def is_rich_text_enabled(self) -> bool:
        return self._rich_text_enabled

    # ---- internals --------------------------------------------------

    def _compute_base_style(self) -> Style:
        # Parser-side base size is in CTk user units so relative
        # sizes (<size=+3>) work consistently with the rest of CTk.
        return Style(size=self._base_size_user_units())

    def _base_size_user_units(self) -> Optional[int]:
        """The size value the user passed (CTk user-unit pixels), or None.
        Reads from CTkTextbox's ``self._font`` so it tracks live changes
        through ``configure(font=…)``."""
        f = getattr(self, "_font", None)
        if isinstance(f, (tuple, list)) and len(f) >= 2:
            try:
                return int(f[1])
            except (ValueError, TypeError):
                return None
        if hasattr(f, "cget"):
            try:
                return int(f.cget("size"))
            except Exception:
                return None
        return None

    def _base_font_actual(self) -> dict:
        """Family/size/weight/slant/underline/overstrike of the inner
        Text widget's current font (already at the visible scale Tk is
        rendering). Suitable to splat into ``tkfont.Font(**...)``."""
        defaults = {
            "family": "TkDefaultFont",
            "size": 13,
            "weight": "normal",
            "slant": "roman",
            "underline": 0,
            "overstrike": 0,
        }
        try:
            spec = self._textbox.cget("font")
            if isinstance(spec, str):
                pf = tkfont.Font(font=spec)
            elif hasattr(spec, "cget"):
                pf = spec
            else:
                return defaults
            return {
                "family": str(pf.cget("family")),
                "size": int(pf.cget("size")),
                "weight": str(pf.cget("weight")),
                "slant": str(pf.cget("slant")),
                "underline": int(pf.cget("underline")),
                "overstrike": int(pf.cget("overstrike")),
            }
        except Exception:
            return defaults

    def _widget_scaling(self) -> float:
        try:
            return float(self._get_widget_scaling())
        except Exception:
            return 1.0

    def _resolve_default_fg(self) -> str:
        """Current widget text color, resolved for the active appearance
        mode (CTkTextbox stores ``self._text_color`` as either a string or
        a ``(light, dark)`` tuple)."""
        tc = getattr(self, "_text_color", None)
        if tc is None:
            return "#dce4ee"
        try:
            return str(self._apply_appearance_mode(tc))
        except Exception:
            if isinstance(tc, (tuple, list)) and tc:
                return str(tc[-1])
            return str(tc)

    def _tag_for(self, style: Style) -> str:
        cached = self._tag_cache.get(style)
        if cached is not None:
            return cached

        name = f"_rich_{len(self._tag_cache)}"
        self._tag_cache[style] = name

        cfg: dict = {
            "foreground": style.color or self._resolve_default_fg(),
        }
        if style.bg is not None:
            cfg["background"] = style.bg

        # Always rebuild the font so the widget-level font_bold/italic/
        # underline/overstrike/family/size all propagate to rich-text
        # chunks. `<b>`/`<i>`/`<u>` only LAYER on top — never strip a
        # widget-level setting.
        base = self._base_font_actual()
        size = (
            -max(1, int(round(style.size * self._widget_scaling())))
            if style.size is not None
            else base["size"]
        )
        cfg["font"] = tkfont.Font(
            family=base["family"],
            size=size,
            weight="bold" if style.bold or base["weight"] == "bold" else "normal",
            slant="italic" if style.italic or base["slant"] == "italic" else "roman",
            underline=1 if style.underline or base["underline"] else 0,
            overstrike=base["overstrike"],
        )

        self._textbox.tag_configure(name, **cfg)
        return name
