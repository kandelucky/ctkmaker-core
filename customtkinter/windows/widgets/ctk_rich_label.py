"""CTkRichLabel — read-only label-like widget that renders Unity-style
rich-text tags (<b>, <i>, <u>, <color=...>, <size=N>, <bg=...>,
<noparse>).

Thin subclass of CTkTextbox with ``rich_text=True`` forced on. The
parent class owns all parsing + tag-cache logic (added in 5.6); this
class just hides the caret, disables the text-input cursor / focus,
and flips state to "disabled" once the initial content lands.

Lives in the ctkmaker-core fork so CTkMaker exports can use
``from customtkinter import CTkRichLabel`` without inlining widget +
parser source into every generated `.py`.
"""
from __future__ import annotations

from typing import Optional

from .ctk_textbox import CTkTextbox
from .font import CTkFont


class CTkRichLabel(CTkTextbox):
    """Read-only rich-text label. Call ``set_text(rich_string)`` to
    update the displayed content."""

    def __init__(
        self,
        master,
        text: str = "",
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
        # CTkRichLabel is always rich — drop any stray rich_text in
        # **kwargs so super() doesn't get the kwarg twice when the
        # descriptor forwards it.
        kwargs.pop("rich_text", None)
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
            rich_text=True,
            **kwargs,
        )

        # Read-only + cosmetic. ``insertontime=0`` hides the blinking
        # caret, ``cursor="arrow"`` keeps the mouse pointer from
        # switching to the I-beam over a label, and ``takefocus=0``
        # removes the widget from the Tab-focus chain.
        self._textbox.configure(
            insertontime=0,
            cursor="arrow",
            takefocus=0,
        )

        if text:
            self.set_text(text)

        # state="disabled" makes the inner tk.Text read-only without
        # affecting tag-foreground rendering. set_rich_text temporarily
        # flips back to "normal" while inserting.
        self._textbox.configure(state="disabled")

    def set_text(self, text: str) -> None:
        """Alias for ``set_rich_text`` — CTkRichLabel-specific public API."""
        self.set_rich_text(text)

    def get_text(self) -> str:
        return self._rich_text
