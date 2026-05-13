# ctkmaker-core

The CustomTkinter runtime that powers [CTkMaker](https://github.com/kandelucky/ctk_maker) — a visual designer for CustomTkinter UIs.

It's a fork of [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (v5.2.2 baseline). What lands here is driven by what CTkMaker needs — this isn't a general-purpose alternative to upstream, just a focused runtime that anyone is welcome to install and use.

**PyPI:** [`ctkmaker-core`](https://pypi.org/project/ctkmaker-core/)

## What it gives you over CustomTkinter 5.2.2

- **Curated bug fixes** — cherry-picked from the active fork landscape (Custom2kinter, ToastyToast25, upstream PRs).
- **Drop-in module name** — still `import customtkinter as ctk`. CTkMessagebox, CTkColorPicker, CTkScrollableDropdown, CTkColorPalette work unchanged.

Per-release changes tracked in [`CHANGELOG.md`](CHANGELOG.md).

## Installation

```bash
pip uninstall customtkinter   # if installed — both share the customtkinter module name
pip install ctkmaker-core
```

```python
import customtkinter as ctk
print(ctk.__fork__)          # "ctkmaker-core"
print(ctk.__fork_version__)  # "5.3.1"
print(ctk.__version__)       # "5.2.2"  (upstream baseline)
```

## Platform support

- **Primary target**: Windows 11 (development + manual testing).
- **Linux / macOS**: best-effort. Bug reports welcome via issues; feature direction follows CTkMaker.

## License

MIT. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE) for attributions to upstream CustomTkinter (Tom Schimansky) and other fork contributors whose work was cherry-picked.

## Project status

Pre-1.0. CTkMaker is the primary consumer and drives the roadmap.
