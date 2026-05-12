# Changelog

All notable changes to **ctkmaker-core** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) 4-segment
release versioning, tracking the upstream CustomTkinter baseline (`5.2.2`).

## [Unreleased] — 5.3.0

Track B in progress — Federico's `configure()`/`cget()` audit triad
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
