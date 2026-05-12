# Changelog

All notable changes to **ctkmaker-core** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) 4-segment
release versioning, tracking the upstream CustomTkinter baseline (`5.2.2`).

## [Unreleased] — 5.2.2.1

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
