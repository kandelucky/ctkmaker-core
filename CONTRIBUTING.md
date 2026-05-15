# Contributing — ctkmaker-core

Conventions for maintaining the fork. See also [ROADMAP.md](ROADMAP.md) for current status + Sacred contracts + architecture quick-map, and [CHANGELOG.md](CHANGELOG.md) for per-release detail.

## Design philosophy — export cleanliness

The fork's primary purpose is keeping CTkMaker's exported `.py` scripts clean. **Anything an exported script needs at runtime lives here** — runtime widget classes, runtime helpers, monkey-patches, font registration. Exports `import customtkinter` and reach those APIs natively, instead of CTkMaker inlining them via `inspect.getsource` or string-literal emission in `app/io/code_exporter/runtime_helpers.py`.

When adding a new runtime entity (widget, helper, behavior wiring) for CTkMaker:

1. Does exported code use it at runtime? → **fork**, at `customtkinter/windows/widgets/ctk_<name>.py` or `customtkinter/contrib/`
2. Editor-only (selection state, canvas drag, undo, statusbar tooltip)? → **stays in CTkMaker `app/`**
3. Export-time property rename (`border_enabled` → `border_width=0`)? → **stays in CTkMaker exporter**

This rule supersedes the older "skip clean public-API features" framing — clean public-API features that exported code uses still belong here, because the alternative is inline bloat in every exported file.

## Tag naming

Release tags use prefix `ctkmaker-core-v<version>` — e.g. `ctkmaker-core-v5.4.15`. Federico's upstream Custom2kinter remote (`custom2kinter`) is fetched into the same local repo and uses plain `v<version>` tags (e.g. `v5.3.0`), which would collide if we used semver alone.

**Why:** When the upstream `custom2kinter` remote was fetched to read Federico's audit commits, his `v5.3.0` tag came in and locked that name. The prefix convention (2026-05-13) keeps upstream tags accessible without forcing rename.

**How to apply:** Future fork releases tag as `ctkmaker-core-v<version>`. GitHub release URLs follow: `https://github.com/kandelucky/ctkmaker-core/releases/tag/ctkmaker-core-v<version>`.

Track A (5.2.2.X 4-segment) shipped before this convention was set — those use PEP 440 segments without prefix and don't collide because Federico has no 5.2.2.X tags.

## Version bump discipline

**Default = patch bump (`x.x.Z`), not minor bump (`x.Y.0`).** Single-widget kwarg additions, bug fixes, and most feature additions are patch-level. Minor bumps are reserved for semantic UX shifts (e.g. CHANGELOG [5.3.0] — "Button fires on release"-level changes) or when the user explicitly requests one.

**Why:** Minor-bump overuse inflates version numbers artificially; patch bumps more accurately reflect change scale.

**How to apply:** When shipping a fork change, increment the patch segment in CHANGELOG entry + `__fork_version__` + tag. Minor bump only on user request or semantic UX shift.

## Windows dark titlebar — `winfo_id()` gotcha

On Windows, a Tk toplevel's `winfo_id()` returns an **inner `TkChild` window with no caption** (WS_CAPTION unset). The decorated frame that DWM styles (class `TkTopLevel`, has caption) is its **parent** — `GetParent(winfo_id())`. This holds for both `tk.Tk` roots and `tk.Toplevel`.

So `DwmSetWindowAttribute(..., DWMWA_USE_IMMERSIVE_DARK_MODE, ...)` must be called on `GetParent(winfo_id())`, with a fallback to `winfo_id()` if GetParent yields 0. Calling it on `winfo_id()` directly is a silent no-op on the titlebar.

Fixed in `5.4.13` (2026-05-14): `_windows_titlebar_hwnd()` helper in `customtkinter/windows/ctk_tk.py` + `ctk_toplevel.py`, used by both `_windows_reapply_titlebar_color` and the existing `_windows_set_titlebar_color`. Any future DWM attribute code in the fork must go through this helper, not `winfo_id()` directly.

## Cherry-picking from `custom2kinter` — recurring conflict shapes

When porting upstream Federico audit commits to ctkmaker-core, four conflict shapes have recurred during Track B (6 commits with 10+ conflicts). Match the incoming conflict to one of the shapes below and apply the documented resolution. Verify with smoke test + Sacred-contract spot check.

### Shape 1 — Federico's superset vs our earlier rewrite

When Federico's version is a broader rewrite of code our earlier port (e.g. 8c85d9b) already touched: **take Federico's superset, preserve any clarifying comments from our version.**

Example: `ctk_scrollbar.py::_mouse_scroll_event` — our 8c85d9b had Linux `event.num` branch; Federico's 6a5460b restructured win/darwin/else + no-command path. Took his structure, kept our `# Linux uses event.num` comment.

### Shape 2 — Our defensive guard vs his plain version

When we previously added a defensive guard (hasattr / type check) and Federico's version drops it: **keep our guard, drop his plain version.**

Example: `ctk_tk.py` + `ctk_toplevel.py::set_focus` — 8c85d9b's `hasattr(event.widget, "focus_set")` function vs Federico's `lambda event: event.widget.focus_set()`. Kept the function (CTk Menu has no `focus_set`).

### Shape 3 — Both versions added different fields in the same block

When both sides extended the same `__init__` or block with different additions: **combine — keep both.**

Example: `ctk_combobox.py::__init__` — ours added `justify=justify` (A.2 #2), Federico's added `_close_on_next_click: bool = False`. Kept both.

### Shape 4 — Auto-merge created duplication

When git's auto-merge produced a duplicate statement (one from each side at different positions): **dedupe, keep the one positioned per the later commit's intent.**

Example: `ctk_optionmenu.py::_open_dropdown_menu` — Federico set `_close_on_next_click = True` BEFORE `open()`, our 8c85d9b set it AFTER. Kept AFTER (so it doesn't misfire if `open()` raises).

### Always drop

`customtkinter/__init__.py` Showroom block — already removed from fork; drop any incoming Showroom diffs entirely.
