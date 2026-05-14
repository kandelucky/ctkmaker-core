import tkinter


def safe_focus(widget) -> None:
    """Focus ``widget`` if it still exists. Used by deferred ``after``
    callbacks (titlebar withdraw+deiconify focus restore, input dialog
    focus delay) where the saved widget may have been destroyed before
    the callback fires — e.g. inline editors that commit + destroy on
    ``<FocusOut>`` when the spawning dialog steals focus.
    """
    try:
        if widget.winfo_exists():
            widget.focus()
    except tkinter.TclError:
        pass


def pop_from_dict_by_set(dictionary: dict, valid_keys: set) -> dict:
    """ remove and create new dict with key value pairs of dictionary, where key is in valid_keys """
    new_dictionary = {}

    for key in list(dictionary.keys()):
        if key in valid_keys:
            new_dictionary[key] = dictionary.pop(key)

    return new_dictionary


def check_kwargs_empty(kwargs_dict, raise_error=False) -> bool:
    """ returns True if kwargs are empty, False otherwise, raises error if not empty """

    if len(kwargs_dict) > 0:
        if raise_error:
            raise ValueError(f"{list(kwargs_dict.keys())} are not supported arguments. Look at the documentation for supported arguments.")
        else:
            return True
    else:
        return False


def derive_disabled_color(widget, explicit_color, base_color, bg_color, blend: float = 0.5):
    """ Resolve the colour a widget should paint while ``state="disabled"``.

    If ``explicit_color`` is set (a ``*_disabled`` kwarg was passed) it wins untouched.
    Otherwise the colour is auto-derived by blending ``base_color`` ~``blend`` of the way
    toward ``bg_color`` — so a disabled widget is always visibly dimmed with zero config,
    even on custom colours.

    ``explicit_color`` / ``base_color`` / ``bg_color`` may each be a single Tk colour or a
    ``(light, dark)`` tuple; the auto-derived result is always a ``(light, dark)`` tuple so
    it round-trips through ``_apply_appearance_mode``. A ``"transparent"`` base is returned
    unchanged so the widget's existing transparent-handling branches still apply.
    ``widget.winfo_rgb`` resolves any Tk colour name (hex, ``"gray20"``, ``"red"``, ...).
    """
    if explicit_color is not None:
        return explicit_color
    if base_color == "transparent":
        return "transparent"

    def _as_pair(color):
        if isinstance(color, (tuple, list)):
            return color[0], color[1]
        return color, color

    base_light, base_dark = _as_pair(base_color)
    bg_light, bg_dark = _as_pair(bg_color)

    def _blend(src, dst):
        if dst == "transparent":
            return src  # nothing meaningful to blend toward
        src_rgb = widget.winfo_rgb(src)
        dst_rgb = widget.winfo_rgb(dst)
        channels = tuple((round(s + (d - s) * blend)) >> 8 for s, d in zip(src_rgb, dst_rgb))
        return "#{:02x}{:02x}{:02x}".format(*channels)

    return (_blend(base_light, bg_light), _blend(base_dark, bg_dark))
