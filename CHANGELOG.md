# Changelog

All notable changes to **ctkmaker-core** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) 4-segment
release versioning, tracking the upstream CustomTkinter baseline (`5.2.2`).

## [5.4.9] — 2026-05-14

### Added

- **[Added]** `CTkTabview` — `tab_stretch` kwarg (default `False`). When
  `True`, the tab strip (the internal `CTkSegmentedButton`) is gridded
  `sticky="nsew"` instead of the anchor-derived `ns` / `nsw` / `nse`, so
  it fills the full width of the TabView; the segmented button is also
  switched to `dynamic_resizing=False` so it holds that stretched width
  instead of collapsing back to its content size, and its existing
  equal-weight column grid then shares the width across the tabs.
  `_set_grid_segmented_button()` is the single grid-writing site and is
  now `tab_stretch`-aware — only the `sticky` value changes; row
  placement is untouched, so a top/bottom anchor (`n` / `s`) still
  positions the strip correctly alongside `tab_stretch`. Horizontal
  anchor is overridden by the full-width strip, as expected. Full kwarg
  lifecycle (`__init__` / `configure()` / `cget()`);
  `configure(tab_stretch=...)` re-grids live. `tab_stretch=False` stays
  byte-identical to vanilla. CTkMaker currently does this editor-side
  with an `_apply_tab_stretch()` re-grid crutch — this is the
  runtime-native equivalent.

## [5.4.8] — 2026-05-14

### Added

- **[Added]** `CTkLabel` — `font_autofit` height mode for wrapped text.
  5.4.7 handled only the width-bounded, non-wrapping case; with
  `wraplength` set, `font_autofit` was a deliberate no-op. `CTkLabel`
  autofit now selects one of two modes: **width mode** (`wraplength == 0`,
  `width > 0`) fits the text width into the label's inner width
  (unchanged from 5.4.7); **height mode** (`wraplength != 0`) wraps the
  text at `wraplength` and fits the wrapped block's height into the
  label's inner height; an auto-grow label with no wrapping stays a
  no-op. Height mode counts wrapped lines with a greedy word-wrap
  approximation of tkinter's own algorithm (breaks on spaces, honours
  explicit newlines, an over-long word takes its own overflowing line),
  then keeps the largest size whose `lines * linespace` fits the
  available height — computed on the private measurement font, with no
  `update_idletasks` / reflow. The internal change-guard now tracks the
  full constraint tuple `(mode, available_px, wrap_px)` with px values
  rounded to ints, so a width or height resize or a `wraplength` change
  all re-fit while a no-op resize still short-circuits.
  `font_autofit=False` stays byte-identical to vanilla, and a width-mode
  label behaves exactly as in 5.4.7.

## [5.4.7] — 2026-05-14

### Added

- **[Added]** `CTkButton` / `CTkLabel` — `font_autofit` kwarg (default
  `False`). When `True`, the widget binary-searches the largest font
  size `<=` the configured size that fits the available space; the
  configured size is the ceiling — autofit only shrinks, never grows —
  and it will not shrink below `_AUTOFIT_MIN_SIZE` (6 px), so extremely
  long text settles at that floor and overflows rather than collapsing.
  This release covers width-mode fitting: `CTkButton` fits the text
  width into the button's inner width; `CTkLabel` does the same when it
  has a bounded width (`width > 0`) and no wrapping (`wraplength == 0`),
  and is a no-op otherwise (wrapping added in 5.4.8). Measurement runs
  in scaled space on a private `tkinter.font.Font`, so it is DPI-correct
  and the — possibly shared — `CTkFont` is never mutated; that same
  private font is also what gets rendered. Re-fit triggers: text / font
  / `font_autofit` change, widget resize, and scaling change; resize
  re-fits are debounced through `after_idle` and guarded by the last
  measured available width, so the `<Configure>` → refit → `<Configure>`
  path cannot loop, and a pending refit is cancelled on `destroy()`.
  Full kwarg lifecycle (`__init__` / `configure()` / `cget()`); switching
  `font_autofit` back to `False` restores the configured size. CTkMaker
  currently computes a fitted size editor-side in its descriptor
  `compute_derived()` — this is the runtime-native equivalent.

## [5.4.6] — 2026-05-14

### Added

- **[Added]** `CTkEntry` / `CTkSlider` / `CTkButton` — visual disabled
  palette. New `*_disabled` colour kwargs: `CTkEntry` gains `fg_color_disabled`,
  `border_color_disabled`, `text_color_disabled`; `CTkSlider` gains
  `fg_color_disabled` (track), `progress_color_disabled`,
  `button_color_disabled`; `CTkButton` gains `fg_color_disabled` and
  `border_color_disabled` (`text_color_disabled` already existed — unchanged).
  Each defaults to `None`, and `None` means **auto-derive**: at draw time the
  widget blends the matching enabled colour ~50% toward its `bg_color` via the
  new `derive_disabled_color()` helper (`customtkinter/.../utility/`), so a
  disabled widget is always visibly dimmed with zero config — including on
  custom colours, where a theme key could not help. An explicit `*_disabled`
  kwarg bypasses the derive and is used verbatim. Hex / named colours and
  `(light, dark)` tuples are supported (resolved through
  `_apply_appearance_mode`). Full kwarg lifecycle (`__init__` / `configure()` /
  `cget()`); `configure(state=...)` live-swaps the palette (`CTkEntry.configure`
  now triggers a redraw on state change). Replaces the hardcoded disabled-colour
  constants in CTkMaker's `transform_properties()`.

### Changed

- **[Changed]** `CTkEntry` / `CTkSlider` / `CTkButton` — **default behaviour
  change (visible).** A widget with `state="disabled"` is now rendered with a
  dimmed palette instead of looking identical to its enabled state. Previously
  `CTkEntry` reused the enabled `fg_color` / `text_color` for
  `disabledbackground` / `disabledforeground`, `CTkSlider` changed only the
  cursor, and `CTkButton` kept `fg_color` / `border_color` at full brightness
  while disabled. This is an intentional improvement, not a regression — but
  vanilla CustomTkinter consumers will see disabled widgets dim where they did
  not before. Enabled-state rendering is byte-identical; pass an explicit
  `*_disabled` colour to opt out of the auto-derived dimming. `CTkButton`'s
  theme-backed `text_color_disabled` default is unchanged.

## [5.4.5] — 2026-05-14

### Added

- **[Added]** `CTkButton` / `CTkLabel` — `image_color` and
  `image_color_disabled` kwargs. `image_color` tints the widget's image;
  `image_color_disabled` overrides it while the widget is disabled and
  reverts on the way back to normal. Both default to `None` (no theme
  fallback — an unconfigured widget shows the image as authored); hex /
  named colours and `(light, dark)` tuples supported.
  `CTkImage.create_scaled_photo_image()` gains a `tint_override` argument
  so a widget can request a one-off tint without mutating a — possibly
  shared — `CTkImage`; the photo-image cache keys on the resolved tint so
  each (widget, state) pairing still renders once. A new
  `_get_image_tint()` picks `image_color` vs `image_color_disabled` from
  the current state; `configure(state=...)` re-runs it for a live tint
  swap. Full kwarg lifecycle (`__init__` / `configure()` / `cget()`).
  `image=None` with `image_color` set is a no-op; `image_color` is
  independent of the Batch A `text_color_hover` / `text_color_pressed`
  path. Step 2 of the image-tint batch (Step 1 — `CTkImage.tint_color` —
  shipped in 5.4.4) — replaces the CTkMaker editor-side PIL recolour in
  `_build_image()` and the exporter `_tint_image()` helper.

## [5.4.4] — 2026-05-14

### Added

- **[Added]** `CTkImage` — `tint_color` and `preserve_aspect` kwargs.
  `tint_color` recolours every non-transparent pixel to a solid colour
  while keeping the source alpha (icon → silhouette); accepts a hex or
  named colour, or a `(light, dark)` tuple resolved per appearance mode.
  `preserve_aspect` (default `False` — legacy stretch) scales the image
  by its smaller side and centres it on a transparent letterbox canvas.
  `_fit_image()` / `_tint_image()` run after `_get_scaled_size()` so the
  maths happens in DPI-scaled space; the photo-image cache key gains the
  resolved tint colour so each colour renders once, and `configure()` of
  either kwarg drops the caches. Full kwarg lifecycle (`__init__` /
  `configure()` / `cget()`). Defaults (`tint_color=None`,
  `preserve_aspect=False`) keep the render path byte-identical to vanilla.
  Step 1 of the image-tint batch — replaces the CTkMaker editor-side PIL
  recolour in `_build_image()`; the `CTkButton` / `CTkLabel` `image_color`
  widget kwargs that build on it land in Step 2.

## [5.4.3] — 2026-05-14

### Changed

- **[Changed]** `CTkCheckBox` / `CTkRadioButton` / `CTkSwitch` —
  `_create_grid()` now sets the label's `anchor` to match
  `text_position` (`"right"` → `w`, `"left"` → `e`, `"top"` /
  `"bottom"` → `center`) instead of leaving it at the stock `w`. Keeps
  the text visually aligned toward the box on every side; required so
  the CTkMaker editor can drop its `_reposition_text` crutch with no
  visual change.

## [5.4.2] — 2026-05-14

### Added

- **[Added]** `CTkCheckBox` / `CTkRadioButton` / `CTkSwitch` —
  `text_position` (`"right"` default / `"left"` / `"top"` / `"bottom"`)
  and `text_spacing` (px gap between box and label, default `6`,
  DPI-scaled) kwargs. The stock layout hard-coded the label to grid
  column 2; a new `_create_grid()` is the single source of truth for the
  box / spacer / label layout, called from `__init__`, `configure()`,
  `_set_scaling()` and `_update_font()`. Full kwarg lifecycle
  (`__init__` / `configure()` / `cget()`); `configure(text_position=...)`
  live re-grids. `text_position="right"` + default `text_spacing`
  reproduces the stock 1x3 grid byte-for-byte; `text=""` collapses the
  label cell (no label, no spacer); an invalid `text_position` raises
  `ValueError`. Replaces the CTkMaker editor-side `apply_state()`
  re-grid crutch.

## [5.4.1] — 2026-05-14

### Added

- **[Added]** `CTkButton` — `text_color_hover` / `text_color_pressed`
  kwargs that swap the button's text colour on hover and on press. Both
  default to `None` (stock behaviour preserved — text colour never
  changes); tuple `(light, dark)` colours supported like `hover_color`.
  Full kwarg lifecycle (`__init__` / `configure()` / `cget()`);
  `configure(...=None)` opts back out. A new `_update_text_color()` is
  the single source of truth for the text-label fg (priority:
  disabled > pressed > hover > base), and `_draw()` routes through it so
  a redraw mid-hover/press no longer resets the in-flight colour. The
  pressed colour is gated on the pointer being over the button, so
  dragging off a held button drops it — matching the cancelled click.
  Replaces the CTkMaker editor-side hover crutch and the exporter
  `_auto_hover_text` helper.

## [5.4.0] — 2026-05-14

### Added

- **[Added]** Non-Latin keyboard input recovery on Windows
  (`customtkinter/windows/widgets/utility/win_keyboard.py`). Tk 8.6
  decodes `WM_CHAR` through the cp1252 ANSI codepage, so non-Latin
  scripts (Georgian, Armenian, Devanagari, Thai, …) arrived as `?`. A
  `<KeyPress>` hook queries Win32 `ToUnicodeEx` with the active layout
  and inserts the real codepoint.
- **[Added]** Cross-platform clipboard shortcut router + right-click
  context menu (Cut / Copy / Paste / Select All) for `Entry` / `Text`.
  Tk matches `<Control-c>` etc. by keysym, so non-Latin layouts
  (`keysym='??'`) silently broke clipboard shortcuts; the router falls
  back to the hardware keycode. Both installed via a monkey-patch on
  `tkinter.Entry/Text.__init__`, covering raw tk and CTk-wrapped widgets.

### Changed

- **[Changed]** Default fonts swapped off the bundled Roboto (no Georgian
  glyphs, no real Bold face — `CTkFont(weight="bold")` fell back to
  synthetic bold). Theme JSONs (blue / dark-blue / green / gold) now
  default to Segoe UI on Windows, SF Pro on macOS, Noto Sans on Linux;
  `ctk_tk.py` reconfigures Tk's named fonts to Segoe UI on Windows so
  tk-native widgets, menus and tooltips render non-Latin text
  consistently. The Roboto faces are no longer bundled or loaded.

## [5.3.2] — 2026-05-13

### Fixed

- **[Fixed]** Deferred `after()` focus restore in `CTkToplevel`,
  `CTk`, and `CTkInputDialog` no longer crashes with `bad window path
  name` when the saved widget was destroyed before the callback fires.
  New `safe_focus()` helper guards with `winfo_exists()` + `TclError`.

## [5.3.1] — 2026-05-13

### Removed

- **[Removed]** CTkToplevel's bundled-icon override on Windows. Dropped
  the entire mechanism on the Toplevel side: `_iconbitmap_method_called`
  flag, scheduled `self.after(200, self._windows_set_titlebar_icon)` call,
  `wm_iconbitmap` / `iconbitmap` flag-setting wrappers, and the
  `_windows_set_titlebar_icon` method itself. The fork no longer paints
  `CustomTkinter_icon_Windows.ico` onto dialog windows. The equivalent
  mechanism on `CTk` (root) is unchanged.

### Fixed

- **[Fixed]** Dialog windows now inherit the host application's icon set
  via root `iconbitmap(default=...)` instead of being overridden by the
  CTk-bundled placeholder. Tk's native default-icon inheritance was
  previously stomped 200 ms after each Toplevel construction; that
  override is gone. Resolves the CTkMaker-side workaround
  (`_patch_ctk_toplevel_icon` monkey patch in `main.py`) which is no
  longer needed — helper_elimination plan item #6 now satisfied at the
  fork level.

## [5.3.0] — 2026-05-13

Track B complete — Federico's `configure()`/`cget()` audit triad
(`db08925` + `8d62feb` + `8c85d9b`) and UX polish commits. Major
version bump signals semantic UX changes (Button fires on release,
Entry/Textbox focus loss, Combo/Option close on dropdown re-click).

### Added

- **[Added]** Utility methods for inspecting / manipulating selected
  state on widgets — Federico's `b33e220`:
  - `CTkComboBox.index([value])` — returns the index of the current or
    given value
  - `CTkOptionMenu.index([value])` — same shape
  - `CTkSegmentedButton.index([value])` + `len()` — segment helpers
  - `CTkTabview.get([index])` — extended (optional `index` param;
    no-arg returns the active tab as before) + new `index([name])`
    and `len()`
  - `CTkEntry.set(string)` — clears and inserts in one call (mirrors
    `CTkTextbox.set`)
  - `CTkCheckBox.set(state, from_variable_callback=False)` and
    `CTkSwitch.set(state, ...)` — signature gained internal-use kwarg;
    public 1-arg call unchanged
  - `CTkSlider.get()` return type narrowed to `float`

  `port(verbatim)` from
  [`b33e220`](https://github.com/FedericoSpada/Custom2kinter/commit/b33e220)
  by Federico Spada. Showroom-context whitespace change in `__init__.py`
  dropped during conflict resolution. Closes upstream #1862.
- **[Added]** Border support for `CTkLabel` — Federico's `cb7347b`.
  New constructor kwargs `border_width` and `border_color` (defaults
  hidden — `border_width: 0`). Adds matching `configure()` / `cget()`
  handlers; `_draw()` now passes the real border width to
  `draw_rounded_rect_with_border` (was hardcoded to `0`). Theme defaults
  injected into `blue`/`dark-blue`/`green` (`border_color:
  ["#979DA2", "#565B5E"]`). Backward-compatible: existing labels render
  identically because the default `border_width` is `0`. `port(verbatim)`
  from [`cb7347b`](https://github.com/FedericoSpada/Custom2kinter/commit/cb7347b)
  by Federico Spada. Closes upstream #2612.
- **[Added]** Mousewheel scroll detection for `CTkSlider` — Federico's
  `6a5460b` (co-authored Saul Velazquez). New constructor kwarg
  `scroll_step: Optional[Union[int, float]] = None` controls per-tick
  delta (default derived from `number_of_steps`, or `1/20` if unset).
  `_create_bindings` now wires `<Button-4>` / `<Button-5>` on Linux and
  `<MouseWheel>` elsewhere. Internal refactor extracts `_update_value()`
  from `_clicked()` (DRY for the new mousewheel path). The `scroll_step`
  configure/cget handlers added speculatively in `db08925` now have a
  real backing attribute. Closes upstream #2388.
- **[Added]** No-command visual scroll path for `CTkScrollbar` — same
  commit. When the scrollbar is instantiated without a `command`,
  mousewheel events still update `_start_value` / `_end_value`
  visually (in 20 steps across the empty range) so the widget is
  responsive on its own. Replaces upstream PR #2365.
- **[Added]** `gold` color theme — Federico's `73bc7ad`. New built-in
  theme registered in `ThemeManager._built_in_themes`. Use via
  `ctk.set_default_color_theme("gold")`.
- **[Added]** `DropdownMenu.close()` and `DropdownMenu.is_open()` —
  Federico's `73ca84f`. New internal helpers used by `CTkComboBox` /
  `CTkOptionMenu` to detect and dismiss dropdowns. `is_open()` returns
  `bool(self.winfo_viewable())`; `close()` calls `self.unpost()`.

### Changed

- **[Changed]** `configure()` audit for all widgets — Federico's
  `db08925`. Reorders existing kwarg handlers for consistency across
  widgets, introduces a `require_new_state` flag pattern in CheckBox/
  Switch/RadioButton, allows `configure(image="")` to clear image
  without warning (`_check_image_type` now accepts `""` as None).
  Adds live-configure for previously init-only properties:
  - CTkCheckBox: `onvalue`, `offvalue`
  - CTkSwitch: `onvalue`, `offvalue`
  - CTkRadioButton: `value`
  - CTkSlider: `scroll_step` (also gains a `cget` handler)
  - DropdownMenu: `min_character_width`

  Also: blue theme CheckBox `hover_color` darkened for visibility
  (was matching `fg_color` when checked). `port(verbatim)` from
  [`db08925`](https://github.com/FedericoSpada/Custom2kinter/commit/db08925)
  by Federico Spada (co-authored Shubham25dec, fred Jose Diaz).
  Closes upstream #1215, #1750, #2494; replaces stale PRs #2412, #2719.
- **[Changed]** `cget()` audit for all widgets — Federico's `8d62feb`.
  Adds missing cget handlers across all widgets and standardizes
  attribute names/positions. New cget handlers:
  - CTkRadioButton: `command`
  - CTkSegmentedButton: `background_corner_colors`, `state`
  - CTkSlider: `orientation`
  - CTkScrollbar: `button_color`, `button_hover_color`
  - CTkScrollableFrame: `orientation`
  - CTkTextbox: `activate_scrollbars`, `scrollbar_button_color`,
    `scrollbar_button_hover_color`
  - CTkImage: `dark_image`, `size`
  - DropdownMenu: `values` now returns a defensive `copy.copy(...)`

  **Breaking:** `CTkScrollbar.cget("scrollbar_color")` and
  `cget("scrollbar_hover_color")` now raise `ValueError` — use the
  canonical `button_color` / `button_hover_color`. Verified that
  neither CTkMessagebox, CTkColorPicker, nor CTkMaker codebases
  reference the old names. `port(verbatim)` from
  [`8d62feb`](https://github.com/FedericoSpada/Custom2kinter/commit/8d62feb)
  by Federico Spada — DropdownMenu conflict resolved by keeping our
  prior `justify` handler alongside Federico's defensive copy.
  Closes upstream #1212, #2615, #2756.
- **[Changed]** `CTkButton` anchor now propagates to inner `_text_label`
  and `_image_label` — Federico's `73bc7ad`. Previously the button's
  `anchor` kwarg only affected the inner Label's placement within the
  button; now the Label's own text/image anchor also follows the kwarg.
  Visual effect appears when the Label is wider than its content
  (image+text compound, wraplength, fixed-width buttons).
  `configure(anchor=...)` propagates to both inner labels live.
  CircleButton inherits transparently (override touches `_create_grid`
  only).
- **[Changed]** Removed dead `sweetkind` entry from
  `ThemeManager._built_in_themes` — same commit. No `sweetkind.json`
  shipped in this repo so no behavior change; just cleanup.
- **[Changed]** Theme file cosmetic normalization — same commit.
  `blue`/`green`: whitespace standardization after `text_color":`;
  `dark-blue`: hex color case (`#3a7ebf` → `#3A7EBF` etc). Pure
  cosmetic, no rendering difference.
- **[Changed]** ⚠ **Semantic UX**: `CTkButton` fires `command` on mouse
  release, not press — Federico's `73ca84f`. Bindings switch from
  `<Button-1>` to `<ButtonRelease-1>`; the private handler is renamed
  `_clicked` → `_on_release` and guarded by a new `_mouse_inside` flag
  (tracked via `_on_enter` / `_on_leave`). Users can now cancel a click
  by dragging away before release — matches browser / OS button UX.
  Internal-only method rename (no external callers in ekosystema or
  CTkMaker, verified). CircleButton inherits the new semantics
  transparently. The `8c85d9b` `set_focus` hasattr-guarded function on
  `CTk` / `CTkToplevel` is preserved over Federico's plain
  `lambda event: event.widget.focus_set()`. Closes upstream #2126,
  #2257, #2722. Replaces upstream PRs #2251, #2736.

### Deprecated

_(None.)_

### Removed

_(None.)_

### Fixed

- **[Fixed]** Federico's mandatory regression follow-up to `db08925` /
  `8d62feb` — `8c85d9b`. Fixes:
  - `CTk` / `CTkToplevel`: `bind_all("<Button-1>", ...)` for focus
    transfer (the `73ca84f` UX feature) brought forward and hasattr-
    guarded so click on a widget without `focus_set` (e.g. a native
    Menu) no longer raises `AttributeError`
  - `CTkScrollbar._mouse_scroll_event`: Linux path now uses `event.num`
    (Button-4 up, Button-5 down) instead of `event.delta` which is 0
    on Linux. `port(rewritten)` — Federico's diff had an indentation
    bug; cleaned up
  - `DrawEngine.DRAWING_METHODS` class var added
    (`["polygon_shapes", "font_shapes", "circle_shapes"]`)
  - `CTkComboBox._open_dropdown_menu` / `CTkOptionMenu._open_dropdown_menu`:
    `_close_on_next_click = True` now set AFTER `open()` (was before —
    could misfire if `open()` had side effects)
  - `ThemeManager`: injects missing `CTkLabel.border_width=0` and
    `border_color=["black","white"]` into legacy theme files (forward-
    compat with the `cb7347b` Label border feature pending in Track B.2)

  Mostly `port(verbatim)`; `ctk_scrollbar.py` is `port(rewritten)`.
  Showroom changes in `__init__.py` (28 lines) and Federico's own
  CHANGELOG edits intentionally dropped during conflict resolution.
- **[Fixed]** `CTkScrollbar` mousewheel detection on Linux — `6a5460b`.
  Completes the partial fix from `8c85d9b`: not only does the event
  handler branch on `event.num`, but `_create_bindings` now wires
  `<Button-4>` / `<Button-5>` on Linux (was binding `<MouseWheel>`
  which never fires there). The prior `8c85d9b` rewrite of
  `_mouse_scroll_event` is superseded by Federico's broader version
  (adds darwin branch + no-command path). `port(verbatim)` from
  [`6a5460b`](https://github.com/FedericoSpada/Custom2kinter/commit/6a5460b);
  single conflict in `_mouse_scroll_event` resolved by taking
  Federico's superset (kept the `event.num` clarifying comment).
  Closes upstream #2777.
- **[Fixed]** Nested `CTkScrollableFrame` mousewheel double-firing —
  Federico's `c12c9ab`. When a scrollable frame contains another
  scrollable widget (`CTkScrollableFrame`, `CTkSlider`, `CTkTextbox`,
  `CTkScrollbar`), the outer frame no longer scrolls while the cursor
  is over the inner widget. Renames internal helper
  `check_if_master_is_canvas` → `_check_if_valid_scroll` (no external
  callers in ekosystema or CTkMaker — verified). New isinstance branches
  defer to children of the listed widget classes; nested
  `CTkScrollableFrame` is detected via `widget._parent_canvas` identity
  comparison. `port(verbatim)` from
  [`c12c9ab`](https://github.com/FedericoSpada/Custom2kinter/commit/c12c9ab).
- **[Fixed]** `CTkEntry.textvariable` trace leak — Federico's `73bc7ad`.
  `destroy()` now removes the textvariable trace before super destroy;
  `configure(textvariable=other_var)` properly removes the old trace
  before adding the new one (was leaving the previous trace attached,
  causing callbacks to fire on stale entries). Closes upstream #1981,
  #2743. Replaces upstream PRs #2077, #2173, #2741. `port(verbatim)`
  from [`73bc7ad`](https://github.com/FedericoSpada/Custom2kinter/commit/73bc7ad)
  by Federico Spada (co-authored federicomassi, Pedro Perdigão, Nerogar).
- **[Fixed]** Clicking a `CTkComboBox` / `CTkOptionMenu` entry while
  the dropdown is already open now closes the dropdown — Federico's
  `73ca84f`. Previously, hover-then-click could leave the dropdown
  stuck open. New `_close_on_next_click` flag (set after
  `_open_dropdown_menu`, synced on `_on_enter` via
  `DropdownMenu.is_open()`) branches `_clicked` into open vs close
  paths. The `8c85d9b` fix for setting the flag AFTER `open()` (not
  before) is preserved on top of Federico's mechanism. Closes upstream
  #2386. `port(verbatim)` from
  [`73ca84f`](https://github.com/FedericoSpada/Custom2kinter/commit/73ca84f)
  by Federico Spada (co-authored Jan Görl, Rivka Sternbuch). Showroom
  changes in `__init__.py` dropped during conflict resolution per
  established workflow.
- **[Fixed]** `CTkToplevel` no longer overrides user-supplied
  `iconbitmap()` 200 ms after init — upstream PR#2162 (`84222ab` by
  timgdx). Removes the redundant inline
  `self.after(200, lambda: self.iconbitmap(CustomTkinter_icon))` call
  from `__init__` that bypassed the `_iconbitmap_method_called`
  sentinel; flips the sentinel to start `False` (was `True`, inverted);
  adds a missing `iconbitmap()` override alongside `wm_iconbitmap()`
  so both calling conventions flip the sentinel. After this, the
  canonical `_windows_set_titlebar_icon` helper (also scheduled at
  +200 ms) correctly defers to user-set icons. CTkMaker's
  `_patch_ctk_toplevel_icon` race-timing workaround (schedules icon
  at +250 ms) continues to work unchanged — last write still wins.
  Closes upstream #1511, #2160. `port(verbatim)` from
  [`84222ab`](https://github.com/TomSchimansky/CustomTkinter/commit/84222ab).

### Security

_(None.)_

---

## [5.2.2.1] — 2026-05-12

First release — Track A complete: 26 cherry-picks landed, 2 skipped for
ToastyToast25 `2d04a57` infrastructure dependencies. Tagged `v5.2.2.1`.

### Added

- Initial fork release based on CustomTkinter `v5.2.2` (Tom Schimansky, 2023).
- Fork identifier markers in `customtkinter/__init__.py`: `__fork__ = "ctkmaker-core"`, `__fork_version__ = "5.2.2.1"`. Debugging aid so users (and bug reports) can verify which library is loaded.
- `LICENSE` consolidating upstream MIT + fork additions copyright.
- `NOTICE` with detailed attribution table for cherry-pick sources.
- `pyproject.toml` (PEP 621) with PyPI name `ctkmaker-core`, Python module name `customtkinter`.
- **[Added]** `segmented_button_font` option on `CTkTabview` — accepts
  `CTkFont` or tuple, configurable at init and via `configure()` —
  `port(verbatim)` from
  [`cea11a0`](https://github.com/FedericoSpada/Custom2kinter/commit/cea11a0)
  by bibo.
- **[Added]** `orientation` option on `CTkSegmentedButton` (`"horizontal"`
  default, `"vertical"` opt-in) — switches grid layout and corner-color
  routing. **Init-only** (no `configure()` handler in fork; requires
  widget recreation to change). `port(verbatim)` from
  [`f159a25`](https://github.com/FedericoSpada/Custom2kinter/commit/f159a25)
  by Philip Nelson, originally upstream PR#2333.
- **[Added]** `CTk.save_geometry()` / `CTk.restore_geometry(str)` —
  DPI-independent geometry persistence. `save_geometry` returns the
  current geometry in logical (unscaled) coordinates; `restore_geometry`
  clamps to current screen bounds (ensures at least 100px visible),
  re-fits within `_min_width`/`_min_height`, and centers if no position
  was saved. `port(verbatim)` from
  [`c65fb05`](https://github.com/ToastyToast25/CustomTkinter/commit/c65fb05)
  by ToastyToast25. Closes issue #2647 family (geometry restore after
  DPI/monitor change).

### Changed

- PyPI distribution name: `ctkmaker-core` (was: `customtkinter` upstream). Python `import` name unchanged — `import customtkinter as ctk` works the same.

### Deprecated

_(None yet — composite-kwarg aliases like `label_enabled`/`button_enabled` land in a later release with a one-release-grace deprecation window tied to CTkMaker production migration.)_

### Removed

_(None)_

### Fixed

- **[Fixed]** `CTkLabel.text_color_disabled` now reads its own theme key
  (was reading `text_color` due to a typo) — `port(verbatim)` from
  [`b2bb1e0`](https://github.com/FedericoSpada/Custom2kinter/commit/b2bb1e0)
  by Soli Como, originally upstream PR#2063.
- **[Fixed]** `CTkInputDialog._text_color` copy-paste typo (was assigning
  `button_hover_color`) — `port(verbatim)` from
  [`2070277`](https://github.com/FedericoSpada/Custom2kinter/commit/2070277)
  by Alex McPherson, originally upstream PR#2078.
- **[Fixed]** `CTkButton` outer-grid minsize now resets to `0` when only
  text or only image is present (was leaving stale minsize from prior
  configuration) — `port(verbatim)` from
  [`f81cd8d`](https://github.com/FedericoSpada/Custom2kinter/commit/f81cd8d)
  by Logan Cederlof, originally upstream PR#1931. Closes issue #1899.
- **[Fixed]** `CTkCanvas.coords()` now returns Tkinter's coordinate list
  (was discarded by the override) — `port(verbatim)` from
  [`8ff5d94`](https://github.com/FedericoSpada/Custom2kinter/commit/8ff5d94)
  by DerSchinken, originally upstream PR#2240. Closes issue #1419.
- **[Fixed]** `CTkTabview.delete(name)` now destroys the underlying
  `CTkFrame` instead of just hiding it (was a memory leak — frame +
  children remained alive after delete) — `port(verbatim)` from
  [`a0a6496`](https://github.com/FedericoSpada/Custom2kinter/commit/a0a6496)
  by ElectricCandlelight, originally upstream PR#1083. Closes issue #1046.
- **[Fixed]** `CTkScrollableFrame` scrollbar no longer covers the parent
  frame's border (added `_border_width + 1` padding on the border-facing
  side of the scrollbar grid) — `port(verbatim)` from
  [`1ad3c10`](https://github.com/FedericoSpada/Custom2kinter/commit/1ad3c10)
  by Dipesh Samrāwat, originally upstream PR#2548.
- **[Fixed]** `CTkTabview.rename(old, new)` now (a) replaces the name
  in-place in `_name_list` instead of removing + appending (preserves
  tab order) and (b) updates `_current_name` if the active tab was
  renamed (previously broke the active-tab frame connection) —
  `port(verbatim)` from
  [`27db1bd`](https://github.com/FedericoSpada/Custom2kinter/commit/27db1bd)
  by Jan Görl, originally upstream PR#2256.
- **[Fixed]** `CTkScrollableFrame.destroy()` now also destroys the internal
  `_parent_frame` (was leaking the CTkFrame holding canvas + scrollbar) —
  `port(verbatim)` from
  [`5c77c99`](https://github.com/FedericoSpada/Custom2kinter/commit/5c77c99)
  by Jeremiah, originally upstream PR#2352.
- **[Fixed]** `CTkScrollbar` now preserves the grab-point offset when
  dragging the handle (was jumping to put click at handle center,
  losing the grab position). Track-clicks outside the handle still
  jump to the click position. `port(verbatim)` from
  [`907300e`](https://github.com/FedericoSpada/Custom2kinter/commit/907300e)
  by timgdx, originally upstream PR#2158.
- **[Fixed]** `CTkScrollableFrame` mouse wheel scrolling now works on
  Linux (binds `<Button-4>`/`<Button-5>` + uses `event.num` for delta +
  `xscrollincrement=30/yscrollincrement=30`). Windows/macOS unchanged.
  `port(verbatim)` from
  [`344b30e`](https://github.com/TomSchimansky/CustomTkinter/commit/344b30e)
  by Tom Schimansky (upstream unmerged). Closes upstream issue #1356.
- **[Fixed]** `FontManager` Linux font installer now sets `0o644` perms
  on the destination after copy and short-circuits when the destination
  already exists and is readable. Fresh fix (no source port). Closes
  upstream [issue #2693](https://github.com/TomSchimansky/CustomTkinter/issues/2693).
- **[Fixed]** `CTkComboBox` `justify` kwarg now also applies to the
  dropdown menu items (was Entry-only — dropdown stayed left-justified).
  `DropdownMenu` gains a `justify` kwarg + configure/cget handler;
  default `"left"` keeps existing behavior. Fresh fix (no source port).
  Closes upstream [issue #2759](https://github.com/TomSchimansky/CustomTkinter/issues/2759).
- **[Fixed]** Inner `CTkCanvas` widgets on `CTkButton`, `CTkCheckBox`,
  `CTkSwitch`, `CTkEntry` no longer accept keyboard focus (was breaking
  Tab traversal — focus landed on the invisible canvas). `takefocus=False`
  set at construction. `CTkLabel` intentionally not patched here (its
  Canvas can be handled at the consumer layer). Fresh fix (no source
  port). Closes upstream [issue #2803](https://github.com/TomSchimansky/CustomTkinter/issues/2803).
- **[Fixed]** `DropdownMenu` now flips above the parent widget when the
  default position would extend past the screen bottom. Estimates
  dropdown height from item count; only flips when sufficient space
  exists above. Silent fallback to default position on errors.
  `port(verbatim)` from
  [`a7979a3`](https://github.com/ToastyToast25/CustomTkinter/commit/a7979a3)
  by ToastyToast25.
- **[Fixed]** `DrawEngine` progress-bar rendering at small dimensions and
  vertical orientation — clamps `inner_corner_radius` to fit within
  inner dimensions (prevents collapsed polygons); adds width check
  (not just height) when deciding whether to create extra corner ovals
  / rectangle_2 (fixes vertical progress bars where width < 2 *
  inner_corner_radius caused overlapping geometry). `port(verbatim)` from
  [`92cd651`](https://github.com/ToastyToast25/CustomTkinter/commit/92cd651)
  by ToastyToast25.
- **[Fixed]** `destroy()` resource leaks across `CTkButton`, `CTkLabel`,
  `CTkProgressBar`, `CTkTextbox`, `CTkScrollableFrame` — cleans CTkImage
  configure callbacks (Button/Label), cancels pending `after()` loops
  (ProgressBar animation, Textbox scrollbar check), unbinds global
  mouse-wheel + Shift bindings (ScrollableFrame). Prevents Tcl
  "invalid command name" errors and leaked callback references in
  long-lived apps with widget churn. `port(verbatim)` from
  [`0834df3`](https://github.com/ToastyToast25/CustomTkinter/commit/0834df3)
  by ToastyToast25.
- **[Added]** PyInstaller hook (`customtkinter/_pyinstaller/`) registering
  `darkdetect` platform submodules as hidden imports and collecting
  customtkinter data files (themes, icons, fonts). Auto-discovered via
  the `pyinstaller40` entry-point in `pyproject.toml`. Fixes frozen-app
  startup `ImportError` for `darkdetect._windows_detect` etc.
  `port(verbatim)` (hook source) from
  [`8ca1537`](https://github.com/ToastyToast25/CustomTkinter/commit/8ca1537)
  by ToastyToast25; entry-point declaration adapted from setup.cfg to
  pyproject.toml.
- **[Fixed]** Dark titlebar on Windows now targets the Tk window's HWND
  directly via `self.winfo_id()` (was `GetParent(winfo_id())` which
  could return the wrong handle or NULL depending on window ownership).
  Applied in both `CTk` and `CTkToplevel`. `port(rewritten)` from
  [upstream PR#2764](https://github.com/TomSchimansky/CustomTkinter/pull/2764)
  by chinmay-varier — extracted semantic 1-line change from a diff that
  also reformatted indentation and added wintypes wrappers.
- **[Fixed]** Linux-only rendering smoothness in `DrawEngine` — defaults
  `preferred_drawing_method` to `"circle_shapes"` on Linux; uses finer
  rounding steps (`0.25` for circle_shapes, `1.25x` for polygon_shapes);
  shaves 0.5px corner_radius and 0.2px border_width when drawing rounded
  rects with border on Linux. Windows/macOS paths unchanged.
  `port(verbatim)` from
  [upstream PR#2646](https://github.com/TomSchimansky/CustomTkinter/pull/2646)
  by Arritmic. (Companion font-manager commit `a691a21` from the same PR
  intentionally skipped — overlaps with our fresh fix for #2693.)
- **[Added]** macOS custom font support in `FontManager.load_font()` —
  new `darwin_font_path = "~/Library/Fonts/"` class variable and a
  Darwin branch that mirrors the Linux fresh-fix pattern (exists+
  readable skip, copy, `chmod 0o644`). `port(rewritten)` from
  [upstream PR#2575](https://github.com/TomSchimansky/CustomTkinter/pull/2575)
  by Khalmurad — adapted macOS support only; PR's `copy_fonts()` helper
  intentionally skipped (would regress the Linux `#2693` fix).
- **[Added]** `selectforeground` and `selectbackground` kwargs on
  `CTkComboBox`, `CTkEntry`, and `CTkTextbox` — control the selected
  text colors. CTkComboBox has dedicated constructor + configure/cget
  handlers; CTkEntry/CTkTextbox pass through to the underlying tkinter
  widget via their `_valid_tk_*_attributes` sets. Defaults preserve
  current behavior (`None`/theme fallback). `port(verbatim)` from
  [upstream PR#2341](https://github.com/TomSchimansky/CustomTkinter/pull/2341)
  by kr8589 (Aleksey).
- **[Fixed]** `CTkFrame` inside `CTkScrollableFrame` now uses
  `top_fg_color` (the visually-stacked theme variant), matching
  `CTkFrame`-inside-`CTkFrame` nesting. Was inheriting the parent's
  color, making nested frames visually invisible. `port(verbatim)` from
  [upstream PR#1298](https://github.com/TomSchimansky/CustomTkinter/pull/1298)
  by Yivi64 (Yahia).
- **[Added]** `auto_hide_scrollbar: bool = False` kwarg on
  `CTkScrollableFrame`. When True, scrollbar hides when content fits
  and reappears on overflow. Default `False` preserves existing
  always-visible behavior. `port(rewritten)` from
  [upstream PR#2539](https://github.com/TomSchimansky/CustomTkinter/pull/2539)
  by HelloWorld-er — gated behind opt-in kwarg (PR enabled by default,
  which would silently change UX).

### Security

_(None)_

---

## Attribution tags

Each fix or feature ported from another fork is tagged in its commit message and listed below per release as one of:

| Tag | Meaning |
|---|---|
| `port(verbatim)` | Applied as-is, attribution to original author |
| `port(rewritten)` | Reimplemented for clarity, attribution to original idea |
| `inspired by` | Concept borrowed, implementation fully ours |
