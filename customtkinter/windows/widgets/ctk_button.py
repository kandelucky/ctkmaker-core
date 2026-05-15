import tkinter
import tkinter.font
import sys
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .image import CTkImage
from .utility import derive_disabled_color


# autofit (font_autofit=True): smallest font size the binary search will shrink to
_AUTOFIT_MIN_SIZE = 6


class CTkButton(CTkBaseClass):
    """
    Button with rounded corners, border, hover effect, image support, click command and textvariable.
    For detailed information check out the documentation.
    """

    _image_label_spacing: int = 6

    def __init__(self,
                 master: Any,
                 width: int = 140,
                 height: int = 28,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,
                 border_spacing: int = 2,
                 full_circle: bool = False,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 pressed_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 fg_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_hover: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_pressed: Optional[Union[str, Tuple[str, str]]] = None,

                 background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None,
                 round_width_to_even_numbers: bool = True,
                 round_height_to_even_numbers: bool = True,

                 text: str = "CTkButton",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 font_autofit: bool = False,
                 textvariable: Union[tkinter.Variable, None] = None,
                 image: Union[CTkImage, "ImageTk.PhotoImage", None] = None,
                 image_color: Optional[Union[str, Tuple[str, str]]] = None,
                 image_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 state: str = "normal",
                 hover: bool = True,
                 command: Union[Callable[[], Any], None] = None,
                 compound: str = "left",
                 anchor: str = "center",
                 **kwargs):

        # transfer basic functionality (bg_color, size, appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # shape
        self._corner_radius: int = ThemeManager.theme["CTkButton"]["corner_radius"] if corner_radius is None else corner_radius
        self._corner_radius = min(self._corner_radius, round(self._current_height / 2))
        self._border_width: int = ThemeManager.theme["CTkButton"]["border_width"] if border_width is None else border_width
        self._border_spacing: int = border_spacing
        # full_circle: when True, _create_grid() stops reserving corner_radius worth of
        # space on the outer columns — for pill / full-circle buttons (2*corner_radius >=
        # width) that reservation would otherwise eat the whole width and push the outer
        # Frame to grow. The canvas draw path still uses the real _corner_radius, so the
        # visible rounded shape is unchanged. Strictly additive: default False is
        # byte-identical to vanilla.
        self._full_circle: bool = full_circle

        # color
        self._fg_color: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkButton"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._hover_color: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None else self._check_color_type(hover_color)
        # pressed_color defaults to None — no theme fallback. When unset the button keeps
        # the stock click-animation flash (leave→enter via fg_color); when set the canvas
        # holds this colour for as long as mouse button 1 is down inside the button.
        self._pressed_color: Optional[Union[str, Tuple[str, str]]] = None if pressed_color is None else self._check_color_type(pressed_color)
        self._border_color: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkButton"]["border_color"] if border_color is None else self._check_color_type(border_color)
        # fg_color_disabled / border_color_disabled default to None — no theme fallback, so an
        # unconfigured button auto-derives a dimmed colour from the enabled colour in _draw().
        # text_color_disabled keeps its theme-backed default below (unchanged, backward compat).
        self._fg_color_disabled: Optional[Union[str, Tuple[str, str]]] = None if fg_color_disabled is None else self._check_color_type(fg_color_disabled, transparency=True)
        self._border_color_disabled: Optional[Union[str, Tuple[str, str]]] = None if border_color_disabled is None else self._check_color_type(border_color_disabled)
        self._text_color: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkButton"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._text_color_disabled: Union[str, Tuple[str, str]] = ThemeManager.theme["CTkButton"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)
        # text_color_hover / text_color_pressed default to None — no theme fallback, so an
        # unconfigured button keeps the stock behaviour (text colour never swaps on hover/press)
        self._text_color_hover: Optional[Union[str, Tuple[str, str]]] = None if text_color_hover is None else self._check_color_type(text_color_hover)
        self._text_color_pressed: Optional[Union[str, Tuple[str, str]]] = None if text_color_pressed is None else self._check_color_type(text_color_pressed)

        # rendering options
        self._background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = background_corner_colors  # rendering options for DrawEngine
        self._round_width_to_even_numbers: bool = round_width_to_even_numbers  # rendering options for DrawEngine
        self._round_height_to_even_numbers: bool = round_height_to_even_numbers  # rendering options for DrawEngine

        # text, font
        self._text = text
        self._text_label: Union[tkinter.Label, None] = None
        self._textvariable: tkinter.Variable = textvariable
        self._font: Union[tuple, CTkFont] = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # font autofit: shrink the text to fit the available width (never grows above the
        # configured size). _autofit_font is a private tkinter.font.Font used for both
        # measuring and rendering, so the (possibly shared) CTkFont is never mutated.
        self._font_autofit: bool = font_autofit
        self._autofit_font: Optional[tkinter.font.Font] = None
        self._autofit_last_width: Optional[float] = None
        self._autofit_after_id: Optional[str] = None

        # image
        self._image = self._check_image_type(image)
        self._image_label: Union[tkinter.Label, None] = None
        if isinstance(self._image, CTkImage):
            self._image.add_configure_callback(self._update_image)
        # image_color / image_color_disabled default to None — no theme fallback, so an
        # unconfigured button shows the image untinted (stock behaviour). image_color
        # tints the image; image_color_disabled overrides it while state="disabled".
        self._image_color: Optional[Union[str, Tuple[str, str]]] = None if image_color is None else self._check_color_type(image_color)
        self._image_color_disabled: Optional[Union[str, Tuple[str, str]]] = None if image_color_disabled is None else self._check_color_type(image_color_disabled)

        # other
        self._state: str = state
        self._hover: bool = hover
        self._command: Callable = command
        self._compound: str = compound
        self._anchor: str = anchor
        self._click_animation_running: bool = False
        self._mouse_inside: bool = False
        self._mouse_pressed: bool = False

        # canvas and draw engine
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 takefocus=False,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")
        self._draw_engine = DrawEngine(self._canvas)
        self._draw_engine.set_round_to_even_numbers(self._round_width_to_even_numbers, self._round_height_to_even_numbers)  # rendering options

        # configure cursor and initial draw
        self._create_bindings()
        self._set_cursor()
        self._draw()

    def _create_bindings(self, sequence: Optional[str] = None):
        """ set necessary bindings for functionality of widget, will overwrite other bindings """

        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)

            if self._text_label is not None:
                self._text_label.bind("<Enter>", self._on_enter)
            if self._image_label is not None:
                self._image_label.bind("<Enter>", self._on_enter)

        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)

            if self._text_label is not None:
                self._text_label.bind("<Leave>", self._on_leave)
            if self._image_label is not None:
                self._image_label.bind("<Leave>", self._on_leave)

        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self._on_press)

            if self._text_label is not None:
                self._text_label.bind("<Button-1>", self._on_press)
            if self._image_label is not None:
                self._image_label.bind("<Button-1>", self._on_press)

        if sequence is None or sequence == "<ButtonRelease-1>":
            self._canvas.bind("<ButtonRelease-1>", self._on_release)

            if self._text_label is not None:
                self._text_label.bind("<ButtonRelease-1>", self._on_release)
            if self._image_label is not None:
                self._image_label.bind("<ButtonRelease-1>", self._on_release)

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._create_grid()

        if self._text_label is not None:
            if self._font_autofit:
                self._apply_autofit_now()
            else:
                self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._update_image()

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._update_image()

    def _set_dimensions(self, width: int = None, height: int = None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        if self._text_label is not None:
            if self._font_autofit:
                self._apply_autofit_now()
            else:
                self._text_label.configure(font=self._apply_font_scaling(self._font))

            # Workaround to force grid to be resized when text changes size.
            # Otherwise grid will lag and only resizes if other mouse action occurs.
            self._canvas.grid_forget()
            self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")

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

    def _autofit_available_width(self) -> float:
        """ width (scaled px) the text may occupy: button width minus the corner/border
        padding columns, the image and the image-text spacing """
        scaled_total = self._apply_widget_scaling(self._current_width)
        scaled_pad = self._apply_widget_scaling(max(self._corner_radius, self._border_width + 1, self._border_spacing))
        available = scaled_total - 2 * scaled_pad
        if self._image_label is not None and self._compound in ("left", "right"):
            available -= self._image_label.winfo_reqwidth()
            if self._text_label is not None:
                available -= self._apply_widget_scaling(self._image_label_spacing)
        return max(available, 1.0)

    def _refit_font(self, available_width: float):
        """ binary-search the largest size <= configured size whose text fits available_width """
        if self._text_label is None:
            return
        text = self._text_label.cget("text")
        if not text:
            return

        ceiling = self._font_configured_size()
        scaling = self._get_widget_scaling()
        if self._autofit_font is None:
            self._autofit_font = tkinter.font.Font()
        self._autofit_font.configure(**self._autofit_base_font_kwargs())

        def fits(size: int) -> bool:
            self._autofit_font.configure(size=-abs(round(size * scaling)))
            return self._autofit_font.measure(text) <= available_width

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
        self._text_label.configure(font=self._autofit_font)

    def _apply_autofit_now(self):
        """ refit synchronously (used when text / font / scaling changed) """
        if self._text_label is None:
            return
        available = self._autofit_available_width()
        self._autofit_last_width = available
        self._refit_font(available)

    def _schedule_refit(self, force: bool = False):
        """ debounced refit — coalesces the burst of _draw calls during a resize """
        if not self._font_autofit or self._text_label is None:
            return
        if force:
            self._autofit_last_width = None
        if self._autofit_after_id is not None:
            return
        self._autofit_after_id = self.after_idle(self._do_scheduled_refit)

    def _do_scheduled_refit(self):
        self._autofit_after_id = None
        if not self._font_autofit or self._text_label is None:
            return
        available = self._autofit_available_width()
        # infinite-loop guard: only refit when the available width really changed
        if self._autofit_last_width is not None and abs(available - self._autofit_last_width) < 0.5:
            return
        self._autofit_last_width = available
        self._refit_font(available)

    def _get_image_tint(self) -> Optional[Union[str, Tuple[str, str]]]:
        """ active image tint: image_color_disabled while the button is disabled (when set),
        otherwise image_color. Returns None when no tint is configured — the image renders
        as authored. Only applies to CTkImage; a raw PhotoImage can't be tinted. """
        if self._state == tkinter.DISABLED and self._image_color_disabled is not None:
            return self._image_color_disabled
        return self._image_color

    def _update_image(self):
        if self._image_label is not None:
            if isinstance(self._image, CTkImage):
                self._image_label.configure(image=self._image.create_scaled_photo_image(self._get_widget_scaling(),
                                                                                        self._get_appearance_mode(),
                                                                                        tint_override=self._get_image_tint()))
            elif self._image is not None:
                self._image_label.configure(image=self._image)

    def destroy(self):
        if self._autofit_after_id is not None:
            self.after_cancel(self._autofit_after_id)
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        if isinstance(self._image, CTkImage):
            self._image.remove_configure_callback(self._update_image)
        super().destroy()

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if self._background_corner_colors is not None:
            self._draw_engine.draw_background_corners(self._apply_widget_scaling(self._current_width),
                                                      self._apply_widget_scaling(self._current_height))
            self._canvas.itemconfig("background_corner_top_left", fill=self._apply_appearance_mode(self._background_corner_colors[0]))
            self._canvas.itemconfig("background_corner_top_right", fill=self._apply_appearance_mode(self._background_corner_colors[1]))
            self._canvas.itemconfig("background_corner_bottom_right", fill=self._apply_appearance_mode(self._background_corner_colors[2]))
            self._canvas.itemconfig("background_corner_bottom_left", fill=self._apply_appearance_mode(self._background_corner_colors[3]))
        else:
            self._canvas.delete("background_parts")

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._corner_radius),
                                                                              self._apply_widget_scaling(self._border_width))

        # effective fg / border palette — while disabled, swap in the *_disabled colours
        # (auto-derived as a dimmed blend of the enabled colours when the kwargs are left
        # at None). Computed at function scope so the text/image label backgrounds below
        # use the same colour as the inner_parts canvas fill.
        if self._state == tkinter.DISABLED:
            fg_color = derive_disabled_color(self, self._fg_color_disabled, self._fg_color, self._bg_color)
            border_color = derive_disabled_color(self, self._border_color_disabled, self._border_color, self._bg_color)
        else:
            fg_color = self._fg_color
            border_color = self._border_color

        if no_color_updates is False or requires_recoloring:

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            # set color for the button border parts (outline)
            self._canvas.itemconfig("border_parts",
                                    outline=self._apply_appearance_mode(border_color),
                                    fill=self._apply_appearance_mode(border_color))

            # set color for inner button parts
            if fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._bg_color),
                                        fill=self._apply_appearance_mode(self._bg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(fg_color),
                                        fill=self._apply_appearance_mode(fg_color))

        # create text label if text given
        if self._text is not None and self._text != "":

            if self._text_label is None:
                self._text_label = tkinter.Label(master=self,
                                                 font=self._apply_font_scaling(self._font),
                                                 text=self._text,
                                                 anchor=self._anchor,
                                                 padx=0,
                                                 pady=0,
                                                 borderwidth=1,
                                                 textvariable=self._textvariable)
                self._create_grid()

                self._text_label.bind("<Enter>", self._on_enter)
                self._text_label.bind("<Leave>", self._on_leave)
                self._text_label.bind("<Button-1>", self._on_press)
                self._text_label.bind("<ButtonRelease-1>", self._on_release)
                self._text_label.bind("<ButtonRelease-1>", self._on_release)

            if no_color_updates is False:
                # set text_label fg color (text / hover / pressed / disabled — single source of truth,
                # so a redraw triggered mid-hover/press keeps the in-flight colour instead of resetting it)
                self._update_text_color()

                if self._apply_appearance_mode(fg_color) == "transparent":
                    self._text_label.configure(bg=self._apply_appearance_mode(self._bg_color))
                else:
                    self._text_label.configure(bg=self._apply_appearance_mode(fg_color))

        else:
            # delete text_label if no text given
            if self._text_label is not None:
                self._text_label.destroy()
                self._text_label = None
                self._create_grid()

        # create image label if image given
        if self._image is not None:

            if self._image_label is None:
                self._image_label = tkinter.Label(master=self, anchor=self._anchor)
                self._update_image()  # set image
                self._create_grid()

                self._image_label.bind("<Enter>", self._on_enter)
                self._image_label.bind("<Leave>", self._on_leave)
                self._image_label.bind("<Button-1>", self._on_press)
                self._image_label.bind("<ButtonRelease-1>", self._on_release)
                self._image_label.bind("<ButtonRelease-1>", self._on_release)

            if no_color_updates is False:
                # set image_label bg color (background color of label)
                if self._apply_appearance_mode(fg_color) == "transparent":
                    self._image_label.configure(bg=self._apply_appearance_mode(self._bg_color))
                else:
                    self._image_label.configure(bg=self._apply_appearance_mode(fg_color))

        else:
            # delete text_label if no text given
            if self._image_label is not None:
                self._image_label.destroy()
                self._image_label = None
                self._create_grid()

        # autofit: the text label may have just been (re)created or the available width
        # may have changed — re-fit on idle (debounced, guarded against no-op resizes)
        if self._font_autofit and self._text_label is not None:
            self._schedule_refit()

    def _create_grid(self):
        """ configure grid system (5x5) """

        # Outer rows and columns have weight of 1000 to overpower the rows and columns of the label and image with weight 1.
        # Rows and columns of image and label need weight of 1 to collapse in case of missing space on the button,
        # so image and label need sticky option to stick together in the center, and therefore outer rows and columns
        # need weight of 100 in case of other anchor than center.
        n_padding_weight, s_padding_weight, e_padding_weight, w_padding_weight = 1000, 1000, 1000, 1000
        if self._anchor != "center":
            if "n" in self._anchor:
                n_padding_weight, s_padding_weight = 0, 1000
            if "s" in self._anchor:
                n_padding_weight, s_padding_weight = 1000, 0
            if "e" in self._anchor:
                e_padding_weight, w_padding_weight = 1000, 0
            if "w" in self._anchor:
                e_padding_weight, w_padding_weight = 0, 1000

        scaled_minsize_rows = self._apply_widget_scaling(max(self._border_width + 1, self._border_spacing))
        # full_circle: drop _corner_radius from the outer-column minsize so the
        # rounded-corner area is no longer reserved as off-limits for content
        # (border space is still reserved). Vanilla path (default) is unchanged.
        if self._full_circle:
            scaled_minsize_columns = self._apply_widget_scaling(max(self._border_width + 1, self._border_spacing))
        else:
            scaled_minsize_columns = self._apply_widget_scaling(max(self._corner_radius, self._border_width + 1, self._border_spacing))

        self.grid_rowconfigure(0, weight=n_padding_weight, minsize=scaled_minsize_rows)
        self.grid_rowconfigure(4, weight=s_padding_weight, minsize=scaled_minsize_rows)
        self.grid_columnconfigure(0, weight=e_padding_weight, minsize=scaled_minsize_columns)
        self.grid_columnconfigure(4, weight=w_padding_weight, minsize=scaled_minsize_columns)

        if self._compound in ("right", "left"):
            self.grid_rowconfigure(2, weight=1)
            if self._image_label is not None and self._text_label is not None:
                self.grid_columnconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._image_label_spacing))
            else:
                self.grid_columnconfigure(2, weight=0, minsize=0)

            self.grid_rowconfigure((1, 3), weight=0)
            self.grid_columnconfigure((1, 3), weight=1)
        else:
            self.grid_columnconfigure(2, weight=1)
            if self._image_label is not None and self._text_label is not None:
                self.grid_rowconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._image_label_spacing))
            else:
                self.grid_rowconfigure(2, weight=0, minsize=0)

            self.grid_columnconfigure((1, 3), weight=0)
            self.grid_rowconfigure((1, 3), weight=1)

        if self._compound == "right":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=3, sticky="w")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=1, sticky="e")
        elif self._compound == "left":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=1, sticky="e")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=3, sticky="w")
        elif self._compound == "top":
            if self._image_label is not None:
                self._image_label.grid(row=1, column=2, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=3, column=2, sticky="n")
        elif self._compound == "bottom":
            if self._image_label is not None:
                self._image_label.grid(row=3, column=2, sticky="n")
            if self._text_label is not None:
                self._text_label.grid(row=1, column=2, sticky="s")

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._create_grid()
            require_redraw = True

        if "border_spacing" in kwargs:
            self._border_spacing = kwargs.pop("border_spacing")
            self._create_grid()
            require_redraw = True

        if "full_circle" in kwargs:
            self._full_circle = kwargs.pop("full_circle")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "pressed_color" in kwargs:
            new_value = kwargs.pop("pressed_color")
            self._pressed_color = None if new_value is None else self._check_color_type(new_value)
            # No redraw needed — pressed colour only renders during _on_press.

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "fg_color_disabled" in kwargs:
            new_value = kwargs.pop("fg_color_disabled")
            self._fg_color_disabled = None if new_value is None else self._check_color_type(new_value, transparency=True)
            require_redraw = True

        if "border_color_disabled" in kwargs:
            new_value = kwargs.pop("border_color_disabled")
            self._border_color_disabled = None if new_value is None else self._check_color_type(new_value)
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "text_color_hover" in kwargs:
            new_value = kwargs.pop("text_color_hover")
            self._text_color_hover = None if new_value is None else self._check_color_type(new_value)
            require_redraw = True

        if "text_color_pressed" in kwargs:
            new_value = kwargs.pop("text_color_pressed")
            self._text_color_pressed = None if new_value is None else self._check_color_type(new_value)
            require_redraw = True

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_redraw = True

        if "font_autofit" in kwargs:
            self._font_autofit = kwargs.pop("font_autofit")
            if self._font_autofit:
                self._schedule_refit(force=True)
            elif self._text_label is not None:
                # autofit off — restore the configured size (drop any autofit shrink)
                self._text_label.configure(font=self._apply_font_scaling(self._font))
                self._autofit_last_width = None

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            if self._text_label is None:
                require_redraw = True  # text_label will be created in .draw()
            else:
                self._text_label.configure(text=self._text)
                if self._font_autofit:
                    self._schedule_refit(force=True)  # width unchanged, text did — force

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            if self._text_label is not None:
                self._text_label.configure(textvariable=self._textvariable)

        if "image" in kwargs:
            if isinstance(self._image, CTkImage):
                self._image.remove_configure_callback(self._update_image)
            self._image = self._check_image_type(kwargs.pop("image"))
            if isinstance(self._image, CTkImage):
                self._image.add_configure_callback(self._update_image)
            if self._image_label is not None:
                self._update_image()
            else:
                require_redraw = True

        if "image_color" in kwargs:
            new_value = kwargs.pop("image_color")
            self._image_color = None if new_value is None else self._check_color_type(new_value)
            self._update_image()  # no-op when there is no image label

        if "image_color_disabled" in kwargs:
            new_value = kwargs.pop("image_color_disabled")
            self._image_color_disabled = None if new_value is None else self._check_color_type(new_value)
            self._update_image()

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            self._update_image()  # live-swap the image tint (image_color <-> image_color_disabled)
            require_redraw = True

        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")
            self._set_cursor()

        if "compound" in kwargs:
            self._compound = kwargs.pop("compound")
            require_redraw = True

        if "anchor" in kwargs:
            self._anchor = kwargs.pop("anchor")
            if self._text_label is not None:
                self._text_label.configure(anchor=self._anchor)
            if self._image_label is not None:
                self._image_label.configure(anchor=self._anchor)
            self._create_grid()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "border_spacing":
            return self._border_spacing
        elif attribute_name == "full_circle":
            return self._full_circle

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "pressed_color":
            return self._pressed_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "fg_color_disabled":
            return self._fg_color_disabled
        elif attribute_name == "border_color_disabled":
            return self._border_color_disabled
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled
        elif attribute_name == "text_color_hover":
            return self._text_color_hover
        elif attribute_name == "text_color_pressed":
            return self._text_color_pressed
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "font_autofit":
            return self._font_autofit
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "image":
            return self._image
        elif attribute_name == "image_color":
            return self._image_color
        elif attribute_name == "image_color_disabled":
            return self._image_color_disabled
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "compound":
            return self._compound
        elif attribute_name == "anchor":
            return self._anchor

        else:
            return super().cget(attribute_name)

    def _set_cursor(self):
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                if sys.platform == "darwin" and self._command is not None:
                    self.configure(cursor="arrow")
                elif sys.platform.startswith("win") and self._command is not None:
                    self.configure(cursor="arrow")

            elif self._state == tkinter.NORMAL:
                if sys.platform == "darwin" and self._command is not None:
                    self.configure(cursor="pointinghand")
                elif sys.platform.startswith("win") and self._command is not None:
                    self.configure(cursor="hand2")

    def _update_text_color(self):
        """ apply the correct colour to _text_label — single source of truth for the label fg.

        Priority: disabled state wins, then an active press while the pointer is over the
        button (text_color_pressed), then hover (text_color_hover), otherwise the resting
        text_color. The press branch is gated on _mouse_inside so dragging off a held button
        drops the pressed colour — mirroring the click being cancelled (no _command on an
        off-widget release). text_color_hover / text_color_pressed are opt-in: when None the
        corresponding branch is skipped, so stock CTkButton behaviour is preserved. """
        if self._text_label is None:
            return

        if self._state == tkinter.DISABLED:
            color = self._text_color_disabled
        elif self._mouse_pressed and self._mouse_inside and self._text_color_pressed is not None:
            color = self._text_color_pressed
        elif self._mouse_inside and self._hover and self._text_color_hover is not None:
            color = self._text_color_hover
        else:
            color = self._text_color

        self._text_label.configure(fg=self._apply_appearance_mode(color))

    def _on_enter(self, event=None):
        self._mouse_inside = True
        # self-heal: if the pointer re-enters without mouse button 1 held, a prior
        # <ButtonRelease-1> must have been lost (e.g. a broken grab) — clear the stale
        # press flag. event is None only for the internal _click_animation re-entry,
        # where _on_release has already cleared the flag, so skipping the check is safe.
        if event is not None and not (event.state & 0x0100):
            self._mouse_pressed = False
        if self._hover is True and self._state == "normal":
            if self._hover_color is None:
                inner_parts_color = self._fg_color
            else:
                inner_parts_color = self._hover_color

            # set color of inner button parts to hover color
            self._canvas.itemconfig("inner_parts",
                                    outline=self._apply_appearance_mode(inner_parts_color),
                                    fill=self._apply_appearance_mode(inner_parts_color))

            # set text_label bg color to button hover color
            if self._text_label is not None:
                self._text_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

            # set image_label bg color to button hover color
            if self._image_label is not None:
                self._image_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

        # text colour follows hover/press state — runs regardless of self._hover / state so a
        # disabled or hover-disabled button still settles on the right resting colour
        self._update_text_color()

    def _on_leave(self, event=None):
        self._mouse_inside = False
        self._click_animation_running = False

        # resting fill — while disabled, settle on the dimmed disabled fg (auto-derived
        # when fg_color_disabled is None) instead of the bright enabled fg_color
        if self._state == tkinter.DISABLED:
            fg_color = derive_disabled_color(self, self._fg_color_disabled, self._fg_color, self._bg_color)
        else:
            fg_color = self._fg_color

        if fg_color == "transparent":
            inner_parts_color = self._bg_color
        else:
            inner_parts_color = fg_color

        # set color of inner button parts
        self._canvas.itemconfig("inner_parts",
                                outline=self._apply_appearance_mode(inner_parts_color),
                                fill=self._apply_appearance_mode(inner_parts_color))

        # set text_label bg color (label color)
        if self._text_label is not None:
            self._text_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

        # set image_label bg color (image bg color)
        if self._image_label is not None:
            self._image_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

        self._update_text_color()

    def _click_animation(self):
        if self._click_animation_running:
            self._on_enter()

    def _on_press(self, event=None):
        if self._state != tkinter.DISABLED:
            self._mouse_pressed = True
            self._update_text_color()
            # press visual — when pressed_color is set, hold this colour on the canvas
            # for the duration of the press. _on_release's leave→enter flow paints the
            # resting colour back when the user lifts the mouse button.
            if self._pressed_color is not None:
                pressed = self._apply_appearance_mode(self._pressed_color)
                self._canvas.itemconfig("inner_parts", outline=pressed, fill=pressed)
                if self._text_label is not None:
                    self._text_label.configure(bg=pressed)
                if self._image_label is not None:
                    self._image_label.configure(bg=pressed)

    def _on_release(self, event=None):
        self._mouse_pressed = False
        if self._mouse_inside and self._state != tkinter.DISABLED:
            # click animation: change color with .on_leave() and back to normal after 100ms with click_animation()
            # _on_leave() also refreshes the text colour; the deferred _on_enter() (via
            # _click_animation) then restores text_color_hover while the cursor stays on the button
            self._on_leave()
            self._click_animation_running = True
            self.after(100, self._click_animation)

            if self._command is not None:
                self._command()
        else:
            # released off the widget (or disabled) — no blink animation, just settle the text colour
            self._update_text_color()

    def invoke(self):
        """ calls command function if button is not disabled """
        if self._state != tkinter.DISABLED:
            if self._command is not None:
                return self._command()

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

        if self._text_label is not None:
            self._text_label.bind(sequence, command, add=True)
        if self._image_label is not None:
            self._image_label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)

        if self._text_label is not None:
            self._text_label.unbind(sequence, None)
        if self._image_label is not None:
            self._image_label.unbind(sequence, None)

        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def focus(self):
        return self._text_label.focus()

    def focus_set(self):
        return self._text_label.focus_set()

    def focus_force(self):
        return self._text_label.focus_force()
