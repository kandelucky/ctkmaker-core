"""Unity3D-style rich-text parser used by CTkRichLabel.

Supported tags:
    <b> </b>                bold
    <i> </i>                italic
    <u> </u>                underline
    <color=...>             foreground (named or #hex)
    <bg=...>                background (named or #hex)
    <size=N>                absolute pixel size
    <size=+N|-N>            size relative to enclosing style
    <noparse> </noparse>    everything inside is shown verbatim

Lenient: anything the parser doesn't recognize as a valid tag-pair
is rendered as literal text — `<color=banana>`, `<xyz>`, `</nope>`,
unclosed openers, and a stray `3 < 5` all just appear as written. No
entity escaping is needed; use `<noparse>` when you want a
valid-looking tag-pair to render literally.

Partial-overlap recovery: when a closing tag is not at the top of the
stack, the matching opener is removed wherever it sits and the tags
above it stay open. Example: `<b>aa<i>bb</b>cc</i>` →
    aa = bold
    bb = bold + italic
    cc = italic

Strictness on unclosed openers: a `<b>` with no matching `</b>` later in
the stream renders literally (the `<b>` text appears, no styling). This
keeps the parser predictable — no "silent style applied to everything
that follows" surprises.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

COLOR_MAP: dict[str, str] = {
    "red": "#ff0000",
    "green": "#00ff00",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "white": "#ffffff",
    "black": "#000000",
    "gray": "#808080",
    "grey": "#808080",
    "orange": "#ffa500",
    "purple": "#800080",
    "pink": "#ffc0cb",
    "brown": "#a52a2a",
}

_TAG_RE = re.compile(r"<(/?)(\w+)(?:=([^>]*))?>")
_NOPARSE_CLOSE = "</noparse>"


@dataclass(frozen=True)
class Style:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None
    size: Optional[int] = None
    bg: Optional[str] = None


@dataclass
class Chunk:
    text: str
    style: Style


def parse_color(value: str) -> Optional[str]:
    """Normalize a color value to '#rrggbb'. None if unparseable."""
    if not value:
        return None
    v = value.strip()
    if v.startswith("#"):
        h = v[1:]
        if all(c in "0123456789abcdefABCDEF" for c in h):
            if len(h) == 3:
                return "#" + "".join(c * 2 for c in h).lower()
            if len(h) == 6:
                return "#" + h.lower()
        return None
    return COLOR_MAP.get(v.lower())


def _apply_tag(current: Style, tag: str, value: Optional[str]) -> Optional[Style]:
    tag = tag.lower()
    if tag == "b":
        return replace(current, bold=True)
    if tag == "i":
        return replace(current, italic=True)
    if tag == "u":
        return replace(current, underline=True)
    if tag == "color":
        c = parse_color(value or "")
        if c is None:
            return None
        return replace(current, color=c)
    if tag == "bg":
        c = parse_color(value or "")
        if c is None:
            return None
        return replace(current, bg=c)
    if tag == "size":
        if not value:
            return None
        v = value.strip()
        sign = v[0] if v and v[0] in "+-" else None
        digits = v[1:] if sign else v
        try:
            n = int(digits)
        except ValueError:
            return None
        if sign is None:
            if n <= 0:
                return None
            return replace(current, size=n)
        base = current.size if current.size is not None else 13
        new_size = base + n if sign == "+" else base - n
        return replace(current, size=max(1, new_size))
    return None


def _find_valid_pairs(text: str, base_style: Style) -> tuple[set[int], set[int]]:
    """Pass 1 — walk all tags (skipping noparse content) and identify
    which opener/closer positions actually pair up. Returns
    (valid_opener_starts, valid_closer_starts).

    An opener is valid iff it is well-formed AND a matching closer of the
    same tag name appears later (using stack-based pairing — closer pops
    the most recent matching opener, supporting partial-overlap).
    Anything else (malformed openers, unmatched closers, unclosed
    openers) stays out of the sets and will render as literal text in
    Pass 2.
    """
    valid_opener_starts: set[int] = set()
    valid_closer_starts: set[int] = set()

    stack: list[tuple[str, int]] = []
    pos = 0
    while pos < len(text):
        m = _TAG_RE.search(text, pos)
        if m is None:
            break
        pos = m.end()

        is_close = bool(m.group(1))
        tag = m.group(2).lower()
        value = m.group(3)

        if tag == "noparse":
            if not is_close:
                close_idx = text.find(_NOPARSE_CLOSE, pos)
                if close_idx == -1:
                    break
                pos = close_idx + len(_NOPARSE_CLOSE)
            continue

        if is_close:
            idx = None
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == tag:
                    idx = i
                    break
            if idx is None:
                continue
            opener_start = stack.pop(idx)[1]
            valid_opener_starts.add(opener_start)
            valid_closer_starts.add(m.start())
        else:
            if _apply_tag(base_style, tag, value) is None:
                continue
            stack.append((tag, m.start()))

    return valid_opener_starts, valid_closer_starts


def parse(text: str, base_style: Optional[Style] = None) -> list[Chunk]:
    """Parse rich-text into styled chunks.

    Adjacent chunks with identical styles are merged. Unknown, malformed,
    or unclosed tags are emitted verbatim as literal text.
    """
    if base_style is None:
        base_style = Style()

    valid_opener_starts, valid_closer_starts = _find_valid_pairs(text, base_style)

    chunks: list[Chunk] = []
    style_stack: list[tuple[str, Optional[str]]] = []
    pos = 0

    def current_style() -> Style:
        s = base_style
        for tag, value in style_stack:
            ns = _apply_tag(s, tag, value)
            if ns is not None:
                s = ns
        return s

    def emit(literal: str) -> None:
        if not literal:
            return
        s = current_style()
        if chunks and chunks[-1].style == s:
            chunks[-1] = Chunk(chunks[-1].text + literal, s)
        else:
            chunks.append(Chunk(literal, s))

    while pos < len(text):
        m = _TAG_RE.search(text, pos)
        if m is None:
            emit(text[pos:])
            break

        emit(text[pos:m.start()])
        full_match = m.group(0)
        is_close = bool(m.group(1))
        tag = m.group(2).lower()
        value = m.group(3)
        tag_start = m.start()
        pos = m.end()

        if tag == "noparse":
            if not is_close:
                close_idx = text.find(_NOPARSE_CLOSE, pos)
                if close_idx == -1:
                    emit(text[pos:])
                    break
                emit(text[pos:close_idx])
                pos = close_idx + len(_NOPARSE_CLOSE)
            # stray </noparse> outside a block is silently dropped.
            continue

        if is_close:
            if tag_start not in valid_closer_starts:
                emit(full_match)
                continue
            for i in range(len(style_stack) - 1, -1, -1):
                if style_stack[i][0] == tag:
                    style_stack.pop(i)
                    break
        else:
            if tag_start not in valid_opener_starts:
                emit(full_match)
                continue
            style_stack.append((tag, value))

    return chunks
