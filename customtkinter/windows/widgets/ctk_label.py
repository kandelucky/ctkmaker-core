import tkinter
import tkinter.font
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .image import CTkImage
from .utility import pop_from_dict_by_set, check_kwargs_empty


# autofit (font_autofit=True): smallest font size the binary search will shrink to
_AUTOFIT_MIN_SIZE = 6


class CTkLabel(CTkBaseClass):
    """
    Label with rounded corners. Default is fg_color=None (transparent fg_color).
    For detailed information check out the documentation.

    state argument will probably be removed because it has no effect
    """

    # attributes that are passed to and managed by the tkinter entry only:
    _valid_tk_label_attributes = {"cursor", "justify", "padx", "pady",
                                  "textvariable", "state", "takefocus", "underline"}

    def __init__(self,
                 master: Any,
                 width: int = 0,
                 height: int = 28,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,
                 full_circle: bool = False,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,

                 text: str = "CTkLabel",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 font_autofit: bool = False,
                 image: Union[CTkImage, None] = None,
                 image_color: Optional[Union[str, Tuple[str, str]]] = None,
                 image_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 compound: str = "center",
                 anchor: str = "center",  # label anchor: center, n, e, s, w
                 wraplength: int = 0,
                 font_wrap: bool = False,
                 **kwargs):

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # color
        self._fg_color = ThemeManager.theme["CTkLabel"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._border_color: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkLabel"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._text_color = ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(text_color)

        if text_color_disabled is None:
            if "text_color_disabled" in ThemeManager.theme["CTkLabel"]:
                self._text_color_disabled = ThemeManager.theme["CTkLabel"]["text_color_disabled"]
            else:
                self._text_color_disabled = self._text_color
        else:
            self._text_color_disabled = self._check_color_type(text_color_disabled)

        # shape
        self._corner_radius = ThemeManager.theme["CTkLabel"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width: int = ThemeManager.theme["CTkLabel"]["border_width"] if border_width is None else border_width
        # full_circle: when True, _create_grid() zeroes the inner label's horizontal padx
        # instead of reserving min(corner_radius, height/2) — for pill / full-circle labels
        # (2*corner_radius >= width) that padx would otherwise eat the whole width and push
        # the outer Frame to grow. The canvas draw path still uses the real _corner_radius,
        # so the visible rounded shape is unchanged. Strictly additive: default False is
        # byte-identical to vanilla.
        self._full_circle: bool = full_circle

        # text
        self._anchor = anchor
        self._text = text
        self._wraplength = wraplength
        self._font_wrap = font_wrap
        self._last_applied_wraplength: Optional[int] = None

        # image
        self._image = self._check_image_type(image)
        self._compound = compound
        if isinstance(self._image, CTkImage):
            self._image.add_configure_callback(self._update_image)
        # image_color / image_color_disabled default to None — no theme fallback, so an
        # unconfigured label shows the image untinted (stock behaviour). image_color tints
        # the image; image_color_disabled overrides it while the label state is "disabled".
        self._image_color: Optional[Union[str, Tuple[str, str]]] = None if image_color is None else self._check_color_type(image_color)
        self._image_color_disabled: Optional[Union[str, Tuple[str, str]]] = None if image_color_disabled is None else self._check_color_type(image_color_disabled)

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # font autofit: shrink the text to fit the available space. Width mode (bounded
        # width, no wrapping) fits the text width; height mode (wraplength set) wraps the
        # text and fits the wrapped block's height; auto-grow with no wrapping is a no-op.
        # _autofit_font is private, so the shared CTkFont is never mutated.
        self._font_autofit: bool = font_autofit
        self._autofit_font: Optional[tkinter.font.Font] = None
        self._autofit_last_constraint: Optional[tuple] = None
        self._autofit_after_id: Optional[str] = None

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._label = tkinter.Label(master=self,
                                    highlightthickness=0,
                                    padx=0,
                                    pady=0,
                                    borderwidth=0,
                                    anchor=self._anchor,
                                    compound=self._compound,
                                    wraplength=self._apply_widget_scaling(self._wraplength),
                                    text=self._text,
                                    font=self._apply_font_scaling(self._font))
        self._label.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes))

        check_kwargs_empty(kwargs, raise_error=True)

        self._create_grid()
        self._update_image()
        self._draw()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width), height=self._apply_widget_scaling(self._desired_height))
        self._label.configure(font=self._apply_font_scaling(self._font))
        self._update_wraplength()
        if self._font_autofit:
            self._apply_autofit_now()

        self._create_grid()
        self._update_image()
        self._draw(no_color_updates=True)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._update_image()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid()
        self._draw()

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        if self._font_autofit:
            self._apply_autofit_now()
        else:
            self._label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nswe")

    # ----- text wrapping --------------------------------------------------

    def _is_wrapping(self) -> bool:
        """ True when the label wraps text — an explicit wraplength, or font_wrap
        deriving one from the label's own (bounded) width """
        return self._wraplength != 0 or (self._font_wrap and self._desired_width > 0)

    def _effective_wraplength(self) -> int:
        """ scaled wraplength handed to the inner tk.Label. With font_wrap on, no
        explicit wraplength and a bounded width, derive it from the label's current
        inner width so the text wraps to the widget; otherwise the configured
        wraplength (0 = no wrap), byte-identical to vanilla. """
        if self._font_wrap and self._wraplength == 0 and self._desired_width > 0:
            scaled_w = self._apply_widget_scaling(self._current_width)
            scaled_padx = self._apply_widget_scaling(min(self._corner_radius, round(self._current_height / 2)))
            return round(max(scaled_w - 2 * scaled_padx, 1))
        return round(self._apply_widget_scaling(self._wraplength))

    def _update_wraplength(self):
        """ push the effective wraplength to the inner label, skipping no-op writes
        so a font_wrap reflow can't feed back into an endless <Configure> loop """
        value = self._effective_wraplength()
        if value != self._last_applied_wraplength:
            self._last_applied_wraplength = value
            self._label.configure(wraplength=value)

    # ----- font autofit ---------------------------------------------------

    def _font_configured_size(self) -> int:
        """ the configured (ceiling) font size in px — autofit never grows past this """
        if isinstance(self._font, CTkFont):
            return abs(self._font.cget("size"))
        return abs(self._font[1])

    def _autofit_base_font_kwargs(self) -> dict:
        """ family / style of the configured font, for the private measurement font """
        if isinstance(self._font, CTkFont):
            return {"family": self._font.cget("family"),
                    "weight": self._font.cget("weight"),
                    "slant": self._font.cget("slant"),
                    "underline": self._font.cget("underline"),
                    "overstrike": self._font.cget("overstrike")}
        tokens = [str(t).lower() for t in self._font[2:]]
        return {"family": self._font[0],
                "weight": "bold" if "bold" in tokens else "normal",
                "slant": "italic" if "italic" in tokens else "roman",
                "underline": "underline" in tokens,
                "overstrike": "overstrike" in tokens}

    def _autofit_constraint(self) -> tuple:
        """ the active autofit constraint as (mode, available_px, wrap_px):
          - "width"  — bounded width, no wrapping: fit the text width into available_px
          - "height" — wrapping (explicit wraplength or font_wrap): wrap at wrap_px,
                       fit the wrapped block's height into available_px
          - None     — autofit does not apply (auto-grow width, no wrapping)
        px values are rounded ints so the change-guard can compare exactly. """
        if self._is_wrapping():
            scaled_h = self._apply_widget_scaling(self._current_height)
            scaled_border = self._apply_widget_scaling(self._border_width)
            available = round(max(scaled_h - 2 * scaled_border, 1.0))
            return "height", available, self._effective_wraplength()
        if self._desired_width > 0:
            scaled_w = self._apply_widget_scaling(self._current_width)
            scaled_padx = self._apply_widget_scaling(min(self._corner_radius, round(self._current_height / 2)))
            return "width", round(max(scaled_w - 2 * scaled_padx, 1.0)), None
        return None, None, None

    @staticmethod
    def _count_wrapped_lines(font: tkinter.font.Font, text: str, wrap_px: float) -> int:
        """ approximate tkinter's word-wrap line count: greedy break on spaces, honour
        explicit newlines, a word wider than wrap_px takes its own (overflowing) line """
        total = 0
        for paragraph in text.split("\n"):
            if not paragraph:
                total += 1  # a blank line still occupies a line
                continue
            line = ""
            for word in paragraph.split(" "):
                candidate = word if not line else line + " " + word
                if not line or font.measure(candidate) <= wrap_px:
                    line = candidate
                else:
                    total += 1
                    line = word
            total += 1  # the paragraph's final (or only) line
        return max(total, 1)

    def _refit_font(self, mode: str, available: float, wrap_px: Optional[float]):
        """ binary-search the largest size <= configured size that satisfies the
        constraint — text width (mode="width") or wrapped block height (mode="height") """
        text = self._label.cget("text")
        if not text:
            return

        ceiling = self._font_configured_size()
        scaling = self._get_widget_scaling()
        if self._autofit_font is None:
            self._autofit_font = tkinter.font.Font()
        self._autofit_font.configure(**self._autofit_base_font_kwargs())

        def fits(size: int) -> bool:
            self._autofit_font.configure(size=-abs(round(size * scaling)))
            if mode == "width":
                return self._autofit_font.measure(text) <= available
            lines = self._count_wrapped_lines(self._autofit_font, text, wrap_px)
            return lines * self._autofit_font.metrics("linespace") <= available

        if fits(ceiling):
            best = ceiling
        else:
            lo, hi = min(_AUTOFIT_MIN_SIZE, ceiling), ceiling
            best = lo
            while lo <= hi:
                mid = (lo + hi) // 2
                if fits(mid):
                    best, lo = mid, mid + 1
                else:
                    hi = mid - 1

        self._autofit_font.configure(size=-abs(round(best * scaling)))
        self._label.configure(font=self._autofit_font)

    def _apply_autofit_now(self):
        """ refit synchronously (used when text / font / wraplength / scaling changed) """
        constraint = self._autofit_constraint()
        self._autofit_last_constraint = constraint
        mode, available, wrap_px = constraint
        if mode is None:
            # autofit not applicable (auto-grow width, no wrapping) — show configured size
            self._label.configure(font=self._apply_font_scaling(self._font))
        else:
            self._refit_font(mode, available, wrap_px)

    def _schedule_refit(self, force: bool = False):
        """ debounced refit — coalesces the burst of _draw calls during a resize """
        if not self._font_autofit:
            return
        if force:
            self._autofit_last_constraint = None
        if self._autofit_after_id is not None:
            return
        self._autofit_after_id = self.after_idle(self._do_scheduled_refit)

    def _do_scheduled_refit(self):
        self._autofit_after_id = None
        if not self._font_autofit:
            return
        constraint = self._autofit_constraint()
        mode, available, wrap_px = constraint
        if mode is None:
            self._label.configure(font=self._apply_font_scaling(self._font))
            self._autofit_last_constraint = constraint
            return
        # infinite-loop guard: only refit when the constraint really changed
        if constraint == self._autofit_last_constraint:
            return
        self._autofit_last_constraint = constraint
        self._refit_font(mode, available, wrap_px)

    def _get_image_tint(self) -> Optional[Union[str, Tuple[str, str]]]:
        """ active image tint: image_color_disabled while the label state is "disabled"
        (when set), otherwise image_color. Returns None when no tint is configured — the
        image renders as authored. Only applies to CTkImage; a raw PhotoImage can't be
        tinted. """
        if self._image_color_disabled is not None and str(self._label.cget("state")) == tkinter.DISABLED:
            return self._image_color_disabled
        return self._image_color

    def _update_image(self):
        if isinstance(self._image, CTkImage):
            self._label.configure(image=self._image.create_scaled_photo_image(self._get_widget_scaling(),
                                                                              self._get_appearance_mode(),
                                                                              tint_override=self._get_image_tint()))
        elif self._image is not None:
            self._label.configure(image=self._image)

    def destroy(self):
        if self._autofit_after_id is not None:
            self.after_cancel(self._autofit_after_id)
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        if isinstance(self._image, CTkImage):
            self._image.remove_configure_callback(self._update_image)
        super().destroy()

    def _create_grid(self):
        """ configure grid system (1x1) """

        text_label_grid_sticky = self._anchor if self._anchor != "center" else ""
        # full_circle: zero the inner label's horizontal padx so it can use the full
        # inner width. Vanilla path (default) reserves min(corner_radius, height/2).
        if self._full_circle:
            grid_padx = 0
        else:
            grid_padx = self._apply_widget_scaling(min(self._corner_radius, round(self._current_height / 2)))
        self._label.grid(row=0, column=0, sticky=text_label_grid_sticky, padx=grid_padx)

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            # set color for the button border parts (outline)
            self._canvas.itemconfig("border_parts",
                                    outline=self._apply_appearance_mode(self._border_color),
                                    fill=self._apply_appearance_mode(self._border_color))

            # set color for inner parts
            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._bg_color),
                                        fill=self._apply_appearance_mode(self._bg_color))

                self._label.configure(fg=self._apply_appearance_mode(self._text_color),
                                      disabledforeground=self._apply_appearance_mode(self._text_color_disabled),
                                      bg=self._apply_appearance_mode(self._bg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._fg_color),
                                        fill=self._apply_appearance_mode(self._fg_color))

                self._label.configure(fg=self._apply_appearance_mode(self._text_color),
                                      disabledforeground=self._apply_appearance_mode(self._text_color_disabled),
                                      bg=self._apply_appearance_mode(self._fg_color))

        # font_wrap: the available width may have changed — re-derive the
        # wraplength so the text re-wraps to the widget on resize
        self._update_wraplength()

        # autofit: the available width may have changed — re-fit on idle
        # (debounced, guarded against no-op resizes)
        if self._font_autofit:
            self._schedule_refit()

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._create_grid()
            require_redraw = True

        if "full_circle" in kwargs:
            self._full_circle = kwargs.pop("full_circle")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "font_autofit" in kwargs:
            self._font_autofit = kwargs.pop("font_autofit")
            if self._font_autofit:
                self._schedule_refit(force=True)
            else:
                # autofit off — restore the configured size (drop any autofit shrink)
                self._label.configure(font=self._apply_font_scaling(self._font))
                self._autofit_last_constraint = None

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._label.configure(text=self._text)
            if self._font_autofit:
                self._schedule_refit(force=True)  # size unchanged, text did — force

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "image" in kwargs:
            if isinstance(self._image, CTkImage):
                self._image.remove_configure_callback(self._update_image)
            self._image = self._check_image_type(kwargs.pop("image"))
            if isinstance(self._image, CTkImage):
                self._image.add_configure_callback(self._update_image)
            self._update_image()

        if "compound" in kwargs:
            self._compound = kwargs.pop("compound")
            self._label.configure(compound=self._compound)

        if "anchor" in kwargs:
            self._anchor = kwargs.pop("anchor")
            self._label.configure(anchor=self._anchor)
            self._create_grid()

        if "wraplength" in kwargs:
            self._wraplength = kwargs.pop("wraplength")
            self._update_wraplength()
            if self._font_autofit:
                # wraplength toggles whether autofit applies at all — force a re-evaluation
                self._schedule_refit(force=True)

        if "font_wrap" in kwargs:
            self._font_wrap = kwargs.pop("font_wrap")
            self._update_wraplength()
            if self._font_autofit:
                # font_wrap toggles whether the label wraps — re-evaluate autofit mode
                self._schedule_refit(force=True)

        if "image_color" in kwargs:
            new_value = kwargs.pop("image_color")
            self._image_color = None if new_value is None else self._check_color_type(new_value)
            self._update_image()  # no-op when there is no image

        if "image_color_disabled" in kwargs:
            new_value = kwargs.pop("image_color_disabled")
            self._image_color_disabled = None if new_value is None else self._check_color_type(new_value)
            self._update_image()

        # "state" is a tkinter.Label attribute (see _valid_tk_label_attributes); refresh the
        # image tint after it's applied so a disabled state live-swaps to image_color_disabled
        state_changed = "state" in kwargs

        self._label.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes))  # configure tkinter.Label

        if state_changed:
            self._update_image()

        super().configure(require_redraw=require_redraw, **kwargs)  # configure CTkBaseClass

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "full_circle":
            return self._full_circle

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "font_autofit":
            return self._font_autofit
        elif attribute_name == "image":
            return self._image
        elif attribute_name == "image_color":
            return self._image_color
        elif attribute_name == "image_color_disabled":
            return self._image_color_disabled
        elif attribute_name == "compound":
            return self._compound
        elif attribute_name == "anchor":
            return self._anchor
        elif attribute_name == "wraplength":
            return self._wraplength
        elif attribute_name == "font_wrap":
            return self._font_wrap

        elif attribute_name in self._valid_tk_label_attributes:
            return self._label.cget(attribute_name)  # cget of tkinter.Label
        else:
            return super().cget(attribute_name)  # cget of CTkBaseClass

    def bind(self, sequence: str = None, command: Callable = None, add: str = True):
        """ called on the tkinter.Label and tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        self._label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        self._label.unbind(sequence, None)

    def focus(self):
        return self._label.focus()

    def focus_set(self):
        return self._label.focus_set()

    def focus_force(self):
        return self._label.focus_force()
