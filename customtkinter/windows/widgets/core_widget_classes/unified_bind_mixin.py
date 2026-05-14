""" UnifiedBindMixin — make a composite CTk widget's public ``bind()`` behave
as if the widget were a single Tk widget, not a (canvas + inner label[s])
composite.

Why this exists
---------------
Upstream customtkinter routes ``bind()`` to every sub-widget unconditionally
(``CTkLabel.bind`` dual-binds canvas + label, ``CTkButton.bind`` triple-binds
canvas + text_label + image_label). Practical consequences:

- ``<Enter>`` / ``<Leave>`` fire when the cursor crosses the bbox of *any*
  sub-widget — moving from the canvas's rounded corner into the inner label's
  text bbox emits Leave (canvas) + Enter (label). 2-3x per logical transition.
- ``<Configure>`` / ``<Map>`` / ``<Unmap>`` fire once per sub-widget (each with
  that sub-widget's geometry), never the outer Frame's logical size.
- ``cursor="..."`` set via ``configure`` lands only on the inner label — the
  rounded-corner area keeps the default cursor.

This mixin dispatches ``bind()`` by event class:

  ===========================  ==========================================
  Event class                  routing
  ===========================  ==========================================
  Hover ``<Enter>`` ``<Leave>`` state-tracked router + after_idle leave
                               debounce + winfo_containing re-check
  ``<Motion>``                 dual-bound, deduped by ``event.time``
  Geometry ``<Configure>``     outer Frame only (``tkinter.Misc.bind``)
  ``<Map>`` ``<Unmap>``
  Focus / Key                  the focus receiver only
  Click / MouseWheel           dual-bound, deduped by ``event.time``
  Fallback (Visibility, ...)   upstream-style dual-bind
  ===========================  ==========================================

opt-in vs default-on
--------------------
Routing is gated by ``self._unified_bind`` (the host widget's ``unified_bind``
kwarg, default ``False``). When ``False`` the ``bind()`` / ``unbind()`` here are
byte-identical to the upstream dual-bind — same calls, same ``None`` return.
When ``True``, ``bind()`` returns a funcid token and routing is active.

Internal relay handlers register lazily on the first user ``bind()`` for that
event class, so a widget that never calls ``bind()`` pays no runtime cost.

Host contract
-------------
The host widget must implement ``_unified_bind_targets()`` returning::

    {
        "canvas":       <the inner CTkCanvas>,
        "inner_label":  <the public inner label, or None>,
        "focus_target": <the sub-widget that receives focus/key events>,
        "all_targets":  <tuple of every sub-widget vanilla would dual-bind,
                         non-None — canvas first>,
        "outer":        <the outer Frame (usually self)>,
    }

and call ``self._init_unified_bind(enabled)`` once, after its sub-widgets
exist. The host's ``configure()`` / ``cget()`` should delegate the
``unified_bind`` option to ``_set_unified_bind`` / ``self._unified_bind``.

Scope: currently adopted by CTkLabel only. CTkButton / CTkSwitch / CTkSlider
can adopt later by implementing ``_unified_bind_targets()`` — no change here.
"""
import tkinter
from typing import Callable, Optional


class UnifiedBindMixin:
    """ Unified ``bind()`` routing for composite CTk widgets. See module docstring. """

    _HOVER_EVENTS = frozenset({"<enter>", "<leave>"})
    _GEOMETRY_EVENTS = frozenset({"<configure>", "<map>", "<unmap>"})
    _FOCUS_EVENTS = frozenset({"<focusin>", "<focusout>"})
    _KEY_EVENTS = frozenset({"<keypress>", "<keyrelease>"})
    _DEDUP_EVENTS = frozenset({
        "<button-1>", "<button-2>", "<button-3>",
        "<buttonrelease-1>", "<buttonrelease-2>", "<buttonrelease-3>",
        "<double-button-1>", "<double-button-2>", "<double-button-3>",
        "<mousewheel>",
    })

    # ----- host contract --------------------------------------------------

    def _unified_bind_targets(self) -> dict:
        """ host widgets must override — see module docstring for the shape """
        raise NotImplementedError(
            f"{type(self).__name__} uses UnifiedBindMixin but does not "
            f"implement _unified_bind_targets()")

    def _init_unified_bind(self, enabled: bool):
        """ called once by the host __init__, after its sub-widgets exist """
        self._unified_bind = bool(enabled)
        self._ub_funcid_counter = 0
        self._ub_registry = {}                       # funcid -> {category, sequence, cleanup}
        self._ub_hover_handlers = {"<enter>": [], "<leave>": []}  # seq -> [(funcid, command)]
        self._ub_motion_handlers = []                # [(funcid, command)]
        self._ub_dedup_handlers = {}                 # seq_lower -> [(funcid, command)]
        self._ub_internal_hover_bound = False
        self._ub_internal_motion_bound = False
        self._ub_inside = False
        if self._unified_bind:
            self._unified_bind_enable_side_effects()

    # ----- public inner-widget API ----------------------------------------

    @property
    def inner_canvas(self):
        """ the inner CTkCanvas — stable reference across CTk versions """
        return self._unified_bind_targets()["canvas"]

    @property
    def inner_label(self):
        """ the public inner label — stable reference; may be None for widgets
        whose label is created on demand (e.g. a CTkButton with no text) """
        return self._unified_bind_targets()["inner_label"]

    # ----- unified_bind option lifecycle ----------------------------------

    def _set_unified_bind(self, enabled: bool):
        """ host configure() delegates the ``unified_bind`` option here.

        Toggling only affects binds made *after* the toggle — binds already
        registered keep the routing mode they were created in. Turning the
        option off does not revert the cursor / takefocus side effects. """
        enabled = bool(enabled)
        was = self._unified_bind
        self._unified_bind = enabled
        if enabled and not was:
            self._unified_bind_enable_side_effects()

    def _unified_bind_enable_side_effects(self):
        """ cursor mirror + take the canvas out of Tab traversal so focus lands
        on the inner label. Idempotent. """
        targets = self._unified_bind_targets()
        # Canvas's default ``takefocus=""`` defers to Tk's heuristic, which
        # includes any widget with class-level key bindings — Canvas has them,
        # so without this a unified widget needs two Tab presses per move.
        try:
            targets["canvas"].configure(takefocus=0)
        except Exception:
            pass
        self._mirror_cursor_to_canvas()

    def _mirror_cursor_to_canvas(self):
        """ copy the inner label's cursor onto the canvas so the rounded-corner
        area shows the same cursor as the text area """
        targets = self._unified_bind_targets()
        label = targets["inner_label"]
        if label is None:
            return
        try:
            cursor = label.cget("cursor")
        except Exception:
            return
        try:
            targets["canvas"].configure(cursor=cursor)
        except Exception:
            pass

    # ----- bind / unbind --------------------------------------------------

    def bind(self, sequence: str = None, command: Callable = None, add: str = True):
        """ unified ``bind()`` — routes by event class when ``unified_bind`` is
        on, otherwise byte-identical to the upstream dual-bind.

        Returns a funcid token (pass to ``unbind``) for routed binds; returns
        ``None`` for the vanilla path, matching upstream. """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")

        if not getattr(self, "_unified_bind", False) or sequence is None or command is None:
            # vanilla dual-bind — byte-identical to upstream CTk*.bind
            for target in self._unified_bind_targets()["all_targets"]:
                target.bind(sequence, command, add=True)
            return None

        seq = sequence.lower()
        if seq in self._HOVER_EVENTS:
            return self._ub_bind_hover(seq, sequence, command)
        if seq.startswith("<motion"):
            return self._ub_bind_motion(sequence, command)
        if seq in self._GEOMETRY_EVENTS:
            return self._ub_bind_geometry(sequence, command)
        if seq in self._FOCUS_EVENTS or seq in self._KEY_EVENTS:
            return self._ub_bind_focus(sequence, command)
        if seq in self._DEDUP_EVENTS:
            return self._ub_bind_dedup(seq, sequence, command)
        return self._ub_bind_fallback(sequence, command)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """ remove a binding. ``unbind(seq, funcid)`` removes that one routed
        bind; ``unbind(seq)`` removes every routed bind for that sequence.

        On the vanilla path (``unified_bind`` off) this mirrors upstream — it
        rejects a funcid and removes all callbacks for the sequence. """
        if not getattr(self, "_unified_bind", False):
            if funcid is not None:
                raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                                 " tkinter and its not clear whether the internal callbacks will be unbinded or not")
            for target in self._unified_bind_targets()["all_targets"]:
                target.unbind(sequence, None)
            return

        if funcid is not None:
            entry = self._ub_registry.pop(funcid, None)
            if entry is not None:
                entry["cleanup"]()
            return

        # funcid is None — remove every routed bind matching the sequence
        seq_lower = sequence.lower() if sequence is not None else None
        for fid, entry in tuple(self._ub_registry.items()):
            if sequence is None or entry["sequence"].lower() == seq_lower:
                entry["cleanup"]()
                self._ub_registry.pop(fid, None)

    # ----- registry helpers ----------------------------------------------

    def _ub_new_funcid(self) -> str:
        self._ub_funcid_counter += 1
        return f"ub#{self._ub_funcid_counter}"

    def _ub_register(self, funcid: str, category: str, sequence: str, cleanup: Callable):
        self._ub_registry[funcid] = {"category": category, "sequence": sequence, "cleanup": cleanup}

    # ----- hover routing --------------------------------------------------

    def _ub_bind_hover(self, seq: str, sequence: str, command: Callable) -> str:
        self._ensure_internal_hover()
        funcid = self._ub_new_funcid()
        self._ub_hover_handlers[seq].append((funcid, command))

        def cleanup():
            self._ub_hover_handlers[seq] = [
                h for h in self._ub_hover_handlers[seq] if h[0] != funcid]

        self._ub_register(funcid, "hover", sequence, cleanup)
        return funcid

    def _ensure_internal_hover(self):
        if self._ub_internal_hover_bound:
            return
        self._ub_internal_hover_bound = True
        for target in self._unified_bind_targets()["all_targets"]:
            target.bind("<Enter>", self._ub_on_internal_enter, add=True)
            target.bind("<Leave>", self._ub_on_internal_leave, add=True)

    def _ub_on_internal_enter(self, event):
        if self._ub_inside:
            return
        self._ub_inside = True
        self._ub_fire_hover("<enter>", event)

    def _ub_on_internal_leave(self, event):
        # The cursor may just be moving canvas <-> label. Defer one idle tick
        # and re-check the actual top widget under the pointer.
        self.after_idle(self._ub_check_truly_left)

    def _ub_check_truly_left(self):
        if not self._ub_inside:
            return
        try:
            x, y = self.winfo_pointerxy()
            under = self.winfo_containing(x, y)
        except Exception:
            return
        targets = self._unified_bind_targets()
        if under is self or under in targets["all_targets"]:
            return
        self._ub_inside = False
        self._ub_fire_hover("<leave>", None)

    def _ub_fire_hover(self, seq: str, event):
        # <leave> is synthesised from an idle re-check, so its handlers receive
        # event=None — user callbacks for <Leave> must tolerate that.
        for funcid, command in tuple(self._ub_hover_handlers[seq]):
            command(event)

    # ----- motion routing -------------------------------------------------

    def _ub_bind_motion(self, sequence: str, command: Callable) -> str:
        self._ensure_internal_motion()
        funcid = self._ub_new_funcid()
        self._ub_motion_handlers.append((funcid, command))

        def cleanup():
            self._ub_motion_handlers[:] = [
                h for h in self._ub_motion_handlers if h[0] != funcid]

        self._ub_register(funcid, "motion", sequence, cleanup)
        return funcid

    def _ensure_internal_motion(self):
        if self._ub_internal_motion_bound:
            return
        self._ub_internal_motion_bound = True
        last_time = [0]

        def relay(event):
            t = getattr(event, "time", 0)
            if t == last_time[0]:
                return
            last_time[0] = t
            for funcid, command in tuple(self._ub_motion_handlers):
                command(event)

        for target in self._unified_bind_targets()["all_targets"]:
            target.bind("<Motion>", relay, add=True)

    # ----- click / wheel dedup -------------------------------------------

    def _ub_bind_dedup(self, seq: str, sequence: str, command: Callable) -> str:
        handlers = self._ensure_internal_dedup(seq, sequence)
        funcid = self._ub_new_funcid()
        handlers.append((funcid, command))

        def cleanup():
            handlers[:] = [h for h in handlers if h[0] != funcid]

        self._ub_register(funcid, "dedup", sequence, cleanup)
        return funcid

    def _ensure_internal_dedup(self, seq: str, sequence: str) -> list:
        handlers = self._ub_dedup_handlers.get(seq)
        if handlers is not None:
            return handlers
        handlers = []
        self._ub_dedup_handlers[seq] = handlers
        last_time = [0]

        def relay(event):
            t = getattr(event, "time", 0)
            if t == last_time[0]:
                return
            last_time[0] = t
            for funcid, command in tuple(handlers):
                command(event)

        for target in self._unified_bind_targets()["all_targets"]:
            target.bind(sequence, relay, add=True)
        return handlers

    # ----- geometry / focus / fallback (direct binds) --------------------

    def _ub_bind_geometry(self, sequence: str, command: Callable) -> str:
        # Bypass this very ``bind`` override (which would dual-bind) by going
        # through ``tkinter.Misc.bind`` on the outer Frame directly, so the
        # event fires once for the outer Frame's real geometry.
        outer = self._unified_bind_targets()["outer"]
        internal = tkinter.Misc.bind(outer, sequence, command, add=True)
        funcid = self._ub_new_funcid()

        def cleanup():
            try:
                tkinter.Misc.unbind(outer, sequence, internal)
            except Exception:
                pass

        self._ub_register(funcid, "geometry", sequence, cleanup)
        return funcid

    def _ub_bind_focus(self, sequence: str, command: Callable) -> str:
        target = self._unified_bind_targets()["focus_target"]
        internal = target.bind(sequence, command, add=True)
        funcid = self._ub_new_funcid()

        def cleanup():
            try:
                target.unbind(sequence, internal)
            except Exception:
                pass

        self._ub_register(funcid, "focus", sequence, cleanup)
        return funcid

    def _ub_bind_fallback(self, sequence: str, command: Callable) -> str:
        # Sequences we don't explicitly classify (Visibility, Activate, ...) —
        # preserve the upstream dual-bind so behaviour never regresses.
        pairs = []
        for target in self._unified_bind_targets()["all_targets"]:
            pairs.append((target, target.bind(sequence, command, add=True)))
        funcid = self._ub_new_funcid()

        def cleanup():
            for target, internal in pairs:
                try:
                    target.unbind(sequence, internal)
                except Exception:
                    pass

        self._ub_register(funcid, "fallback", sequence, cleanup)
        return funcid
