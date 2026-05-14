import tkinter
import sys
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkCheckBox(CTkBaseClass):
    """
    Checkbox with rounded corners, border, variable support and hover effect.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: Any,
                 width: int = 100,
                 height: int = 24,
                 checkbox_width: int = 24,
                 checkbox_height: int = 24,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 checkmark_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,

                 text: str = "CTkCheckBox",
                 text_position: str = "right",
                 text_spacing: int = 6,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 textvariable: Union[tkinter.Variable, None] = None,
                 state: str = tkinter.NORMAL,
                 hover: bool = True,
                 command: Union[Callable[[], Any], None] = None,
                 onvalue: Union[int, str] = 1,
                 offvalue: Union[int, str] = 0,
                 variable: Union[tkinter.Variable, None] = None,
                 **kwargs):

        # validate before super().__init__() registers the widget with tk —
        # raising afterwards leaves a half-built widget parented to master
        # that crashes on destroy()
        if text_position not in ("right", "left", "top", "bottom"):
            raise ValueError(f"text_position must be 'right', 'left', 'top' or 'bottom', not {text_position!r}")

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # dimensions
        self._checkbox_width = checkbox_width
        self._checkbox_height = checkbox_height

        # color
        self._fg_color = ThemeManager.theme["CTkCheckBox"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._hover_color = ThemeManager.theme["CTkCheckBox"]["hover_color"] if hover_color is None else self._check_color_type(hover_color)
        self._border_color = ThemeManager.theme["CTkCheckBox"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._checkmark_color = ThemeManager.theme["CTkCheckBox"]["checkmark_color"] if checkmark_color is None else self._check_color_type(checkmark_color)

        # shape
        self._corner_radius = ThemeManager.theme["CTkCheckBox"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkCheckBox"]["border_width"] if border_width is None else border_width

        # text
        self._text = text
        self._text_position = text_position  # validated at the top of __init__
        self._text_spacing = text_spacing
        self._text_label: Union[tkinter.Label, None] = None
        self._text_color = ThemeManager.theme["CTkCheckBox"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._text_color_disabled = ThemeManager.theme["CTkCheckBox"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # callback and hover functionality
        self._command = command
        self._state = state
        self._hover = hover
        self._check_state = False

        self._onvalue = onvalue
        self._offvalue = offvalue
        self._variable: tkinter.Variable = variable
        self._variable_callback_blocked = False
        self._textvariable: tkinter.Variable = textvariable
        self._variable_callback_name = None

        # widgets — laid out by _create_grid() (text_position-aware)
        self._bg_canvas = CTkCanvas(master=self,
                                    highlightthickness=0,
                                    takefocus=False,
                                    width=self._apply_widget_scaling(self._desired_width),
                                    height=self._apply_widget_scaling(self._desired_height))

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 takefocus=False,
                                 width=self._apply_widget_scaling(self._checkbox_width),
                                 height=self._apply_widget_scaling(self._checkbox_height))
        self._draw_engine = DrawEngine(self._canvas)

        self._text_label = tkinter.Label(master=self,
                                         bd=0,
                                         padx=0,
                                         pady=0,
                                         text=self._text,
                                         justify=tkinter.LEFT,
                                         font=self._apply_font_scaling(self._font),
                                         textvariable=self._textvariable)
        self._text_label["anchor"] = "w"

        self._create_grid()

        # register variable callback and set state according to variable
        if self._variable is not None and self._variable != "":
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._check_state = True if self._variable.get() == self._onvalue else False

        self._create_bindings()
        self._set_cursor()
        self._draw()

    def _create_bindings(self, sequence: Optional[str] = None):
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self.toggle)
            self._text_label.bind("<Button-1>", self.toggle)

    def _create_grid(self):
        """ Lay out box / spacer / label per text_position + text_spacing.

        Single source of truth for the widget's grid — called from
        __init__, configure(), _set_scaling() and _update_font().
        text_position="right" with the default text_spacing reproduces the
        stock CustomTkinter 1x3 layout. An empty text collapses the label
        cell entirely (no label widget, no spacer). """
        spacing = self._apply_widget_scaling(self._text_spacing)
        has_text = bool(self._text)

        # Reset every slot we might touch so a re-grid coming from a
        # different text_position leaves no stale weight / minsize behind.
        for i in range(3):
            self.grid_columnconfigure(i, weight=0, minsize=0)
            self.grid_rowconfigure(i, weight=0, minsize=0)
        self._bg_canvas.grid_forget()
        self._canvas.grid_forget()
        self._text_label.grid_forget()

        if self._text_position in ("right", "left"):
            # box + label share row 0 across three columns; the label
            # column carries the stretch weight, the spacer sits between.
            self.grid_rowconfigure(0, weight=1)
            box_col, label_col = (0, 2) if self._text_position == "right" else (2, 0)
            label_sticky = "w" if self._text_position == "right" else "e"
            self.grid_columnconfigure(label_col, weight=1)
            self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")
            self._canvas.grid(row=0, column=box_col, sticky="e")
            if has_text:
                self.grid_columnconfigure(1, weight=0, minsize=spacing)
                self._text_label.grid(row=0, column=label_col, sticky=label_sticky)
                self._text_label["anchor"] = label_sticky
        else:
            # box + label share column 0 across three rows; the label
            # row carries the stretch weight, the spacer sits between.
            self.grid_columnconfigure(0, weight=1)
            box_row, label_row = (2, 0) if self._text_position == "top" else (0, 2)
            label_sticky = "s" if self._text_position == "top" else "n"
            self.grid_rowconfigure(label_row, weight=1)
            self._bg_canvas.grid(row=0, column=0, rowspan=3, sticky="nswe")
            self._canvas.grid(row=box_row, column=0, sticky="")
            if has_text:
                self.grid_rowconfigure(1, weight=0, minsize=spacing)
                self._text_label.grid(row=label_row, column=0, sticky="")
                self._text_label["anchor"] = "center"

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._create_grid()
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._canvas.delete("checkmark")
        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))
        self._canvas.configure(width=self._apply_widget_scaling(self._checkbox_width),
                               height=self._apply_widget_scaling(self._checkbox_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int = None, height: int = None):
        super()._set_dimensions(width, height)

        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        if self._text_label is not None:
            self._text_label.configure(font=self._apply_font_scaling(self._font))

            # Workaround to force grid to be resized when text changes size.
            # Otherwise grid will lag and only resizes if other mouse action occurs.
            # _create_grid() re-runs the full (text_position-aware) layout,
            # which includes the grid_forget()/grid() the workaround relies on.
            self._create_grid()

    def destroy(self):
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        super().destroy()

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring_1 = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._checkbox_width),
                                                                                self._apply_widget_scaling(self._checkbox_height),
                                                                                self._apply_widget_scaling(self._corner_radius),
                                                                                self._apply_widget_scaling(self._border_width))

        if self._check_state is True:
            requires_recoloring_2 = self._draw_engine.draw_checkmark(self._apply_widget_scaling(self._checkbox_width),
                                                                     self._apply_widget_scaling(self._checkbox_height),
                                                                     self._apply_widget_scaling(self._checkbox_height * 0.58))
        else:
            requires_recoloring_2 = False
            self._canvas.delete("checkmark")

        if no_color_updates is False or requires_recoloring_1 or requires_recoloring_2:
            self._bg_canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            if self._check_state is True:
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._fg_color),
                                        fill=self._apply_appearance_mode(self._fg_color))
                self._canvas.itemconfig("border_parts",
                                        outline=self._apply_appearance_mode(self._fg_color),
                                        fill=self._apply_appearance_mode(self._fg_color))

                if "create_line" in self._canvas.gettags("checkmark"):
                    self._canvas.itemconfig("checkmark", fill=self._apply_appearance_mode(self._checkmark_color))
                else:
                    self._canvas.itemconfig("checkmark", fill=self._apply_appearance_mode(self._checkmark_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._bg_color),
                                        fill=self._apply_appearance_mode(self._bg_color))
                self._canvas.itemconfig("border_parts",
                                        outline=self._apply_appearance_mode(self._border_color),
                                        fill=self._apply_appearance_mode(self._border_color))

            if self._state == tkinter.DISABLED:
                self._text_label.configure(fg=(self._apply_appearance_mode(self._text_color_disabled)))
            else:
                self._text_label.configure(fg=self._apply_appearance_mode(self._text_color))

            self._text_label.configure(bg=self._apply_appearance_mode(self._bg_color))

    def configure(self, require_redraw=False, **kwargs):
        require_new_state = False

        if "checkbox_width" in kwargs:
            self._checkbox_width = kwargs.pop("checkbox_width")
            self._canvas.configure(width=self._apply_widget_scaling(self._checkbox_width))
            require_redraw = True

        if "checkbox_height" in kwargs:
            self._checkbox_height = kwargs.pop("checkbox_height")
            self._canvas.configure(height=self._apply_widget_scaling(self._checkbox_height))
            require_redraw = True

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "checkmark_color" in kwargs:
            self._checkmark_color = self._check_color_type(kwargs.pop("checkmark_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "text" in kwargs:
            new_text = kwargs.pop("text")
            # an empty text collapses the label cell, so toggling emptiness
            # has to re-run the layout
            text_emptiness_changed = bool(new_text) != bool(self._text)
            self._text = new_text
            self._text_label.configure(text=self._text)
            if text_emptiness_changed:
                self._create_grid()

        if "text_position" in kwargs:
            new_position = kwargs.pop("text_position")
            if new_position not in ("right", "left", "top", "bottom"):
                raise ValueError(f"text_position must be 'right', 'left', 'top' or 'bottom', not {new_position!r}")
            self._text_position = new_position
            self._create_grid()

        if "text_spacing" in kwargs:
            self._text_spacing = kwargs.pop("text_spacing")
            self._create_grid()

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
            require_new_state = True

        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")
            require_new_state = True

        if "variable" in kwargs:
            if self._variable is not None and self._variable != "":
                self._variable.trace_remove("write", self._variable_callback_name)  # remove old variable callback
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                require_new_state = True

        if require_new_state and self._variable is not None and self._variable != "":
            self._check_state = True if self._variable.get() == self._onvalue else False
            require_redraw = True
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "checkbox_width":
            return self._checkbox_width
        elif attribute_name == "checkbox_height":
            return self._checkbox_height
        elif attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "checkmark_color":
            return self._checkmark_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "text_position":
            return self._text_position
        elif attribute_name == "text_spacing":
            return self._text_spacing
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "onvalue":
            return self._onvalue
        elif attribute_name == "offvalue":
            return self._offvalue
        elif attribute_name == "variable":
            return self._variable

        else:
            return super().cget(attribute_name)

    def _set_cursor(self):
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")

            elif self._state == tkinter.NORMAL:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="pointinghand")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="pointinghand")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="hand2")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="hand2")

    def _on_enter(self, event=0):
        if self._hover is True and self._state == tkinter.NORMAL:
            if self._check_state is True:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._hover_color),
                                        outline=self._apply_appearance_mode(self._hover_color))
                self._canvas.itemconfig("border_parts",
                                        fill=self._apply_appearance_mode(self._hover_color),
                                        outline=self._apply_appearance_mode(self._hover_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._hover_color),
                                        outline=self._apply_appearance_mode(self._hover_color))

    def _on_leave(self, event=0):
        if self._check_state is True:
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._fg_color),
                                    outline=self._apply_appearance_mode(self._fg_color))
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._fg_color),
                                    outline=self._apply_appearance_mode(self._fg_color))
        else:
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._bg_color),
                                    outline=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            if self._variable.get() == self._onvalue:
                self.select(from_variable_callback=True)
            elif self._variable.get() == self._offvalue:
                self.deselect(from_variable_callback=True)
    
    def set(self, state: bool, from_variable_callback=False):
        self._check_state = state
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._onvalue if self._check_state is True else self._offvalue)
            self._variable_callback_blocked = False

    def toggle(self, event=0):
        if self._state == tkinter.NORMAL:
            self.set(not self._check_state)

            if self._command is not None:
                self._command()

    def select(self, from_variable_callback=False):
        self.set(True, from_variable_callback)

    def deselect(self, from_variable_callback=False):
        self.set(False, from_variable_callback)

    def get(self) -> Union[int, str]:
        return self._onvalue if self._check_state is True else self._offvalue

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        self._text_label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        self._text_label.unbind(sequence, None)
        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def focus(self):
        return self._text_label.focus()

    def focus_set(self):
        return self._text_label.focus_set()

    def focus_force(self):
        return self._text_label.focus_force()
