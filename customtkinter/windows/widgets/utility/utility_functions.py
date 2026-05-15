import tkinter
from typing import Optional, Union, Tuple, Dict


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


# ----------------------------------------------------------------------
# Unity-style colour math
# ----------------------------------------------------------------------
#
# Unity's UI Button.ColorBlock multiplies the Image component's RGB by a
# per-state tint and a Color Multiplier (each channel clamped to 0..1).
# The default tints encode the standard look:
#
#     Normal       (255, 255, 255, 255) — no tint
#     Highlighted  (245, 245, 245, 255) — slight dim
#     Pressed      (200, 200, 200, 255) — more dim
#     Disabled     (200, 200, 200, 128) — dim + half alpha
#
# The functions below port that math to hex strings so descriptors can
# derive a full per-state palette from a single "Normal" colour plus three
# tint multipliers, instead of asking the user to pick each state colour
# manually. Tk has no widget alpha, so the disabled half-alpha is faked by
# blending the tinted result toward the surface colour (`fade_color`).
#
# Hex-only by design. Named-colour callers should resolve to hex first
# (e.g. via `widget.winfo_rgb`) before calling these helpers.


def _parse_hex(color: str) -> Tuple[int, int, int]:
    """Hex string (``#rgb`` or ``#rrggbb``) → ``(r, g, b)`` in 0..255."""
    s = color.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"expected #rrggbb hex, got {color!r}")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _to_hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    )


def tint_color(base: str, tint: str, multiplier: float = 1.0) -> str:
    """Unity ColorBlock math: ``result = base × tint × multiplier`` per channel.

    Each channel is normalised to 0..1, multiplied, then clamped and re-mapped
    to 0..255. Use this to derive a state colour from a "Normal" base and a
    tint that encodes the relative state shift (white = no change, gray = dim,
    etc.). ``multiplier`` is Unity's Color Multiplier slider (1..5 in Unity);
    values above 1 amplify the difference between Normal and other states.
    """
    br, bg, bb = _parse_hex(base)
    tr, tg, tb = _parse_hex(tint)
    r = (br / 255.0) * (tr / 255.0) * multiplier
    g = (bg / 255.0) * (tg / 255.0) * multiplier
    b = (bb / 255.0) * (tb / 255.0) * multiplier
    return _to_hex(
        round(max(0.0, min(1.0, r)) * 255),
        round(max(0.0, min(1.0, g)) * 255),
        round(max(0.0, min(1.0, b)) * 255),
    )


def fade_color(color: str, alpha: float, toward: str) -> str:
    """Blend ``color`` ``alpha`` of the way *into itself* and the rest into
    ``toward`` — fakes Tk-incompatible widget alpha compositing.

    ``alpha=1.0`` returns ``color`` unchanged; ``alpha=0.0`` returns ``toward``;
    ``alpha=0.5`` is the midpoint. Used to mimic Unity's half-alpha disabled
    tint by blending the tinted state colour toward the surface colour.
    """
    fr, fg, fb = _parse_hex(color)
    br, bg, bb = _parse_hex(toward)
    return _to_hex(
        round(fr * alpha + br * (1 - alpha)),
        round(fg * alpha + bg * (1 - alpha)),
        round(fb * alpha + bb * (1 - alpha)),
    )


def derive_state_colors(
    normal: str,
    hover_tint: str = "#f5f5f5",
    pressed_tint: str = "#c8c8c8",
    disabled_tint: str = "#c8c8c8",
    multiplier: float = 1.0,
    disabled_fade: bool = False,
    surface: Optional[str] = None,
    disabled_alpha: float = 0.5,
) -> Dict[str, str]:
    """Resolve a four-state palette (normal/hover/pressed/disabled) from one
    base colour and three Unity-style tints.

    Returns a dict with keys ``"normal"``, ``"hover"``, ``"pressed"``,
    ``"disabled"``. ``normal`` echoes the base unchanged (no math); the others
    apply ``tint_color`` with the given multiplier. When ``disabled_fade``
    is set and a ``surface`` colour is provided, the disabled result is then
    blended toward ``surface`` by ``disabled_alpha`` — emulating the half-alpha
    component of Unity's default disabled tint.
    """
    result = {
        "normal": normal,
        "hover": tint_color(normal, hover_tint, multiplier),
        "pressed": tint_color(normal, pressed_tint, multiplier),
        "disabled": tint_color(normal, disabled_tint, multiplier),
    }
    if disabled_fade and surface is not None:
        result["disabled"] = fade_color(result["disabled"], disabled_alpha, surface)
    return result
