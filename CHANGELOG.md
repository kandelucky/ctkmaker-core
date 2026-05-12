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
