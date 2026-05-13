# ctkmaker-core

A maintained fork of [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (v5.2.2 baseline) with:

- **Composite kwarg sugar** — `widget.configure(font_bold=True, font_size=14, label_enabled=False)` works natively, no helper boilerplate in exported code.
- **Curated bug fixes** — cherry-picked from the active fork landscape (Custom2kinter, Stukk).
- **Drop-in module name** — still `import customtkinter as ctk`. CTkMessagebox, CTkColorPicker, CTkScrollableDropdown, CTkColorPalette work unchanged.

**PyPI:** [`ctkmaker-core`](https://pypi.org/project/ctkmaker-core/)

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

## What's different from vanilla CustomTkinter 5.2.2

Tracked in [`CHANGELOG.md`](CHANGELOG.md) per release. Detailed diff and Precedence Rules per composite live in [`docs/spec/FORK.md`](docs/spec/FORK.md).

## Composite kwargs — quick example

```python
# Vanilla CustomTkinter — build the font yourself
font = ctk.CTkFont(family="Inter", size=14, weight="bold")
label = ctk.CTkLabel(parent, text="Hello", font=font)

# ctkmaker-core — composite kwargs as sugar
label = ctk.CTkLabel(parent, text="Hello", font_family="Inter", font_size=14, font_bold=True)

# Mixed — composite kwargs override the font object's matching attributes
font = ctk.CTkFont(family="Inter", size=14, weight="normal")
label = ctk.CTkLabel(parent, text="Hello", font=font, font_bold=True)
# Result: weight="bold" wins; family + size from font object

# Live update — same shape as native kwargs
label.configure(font_bold=False)
```

Native CTk API stays fully accessible. Composite kwargs are **sugar**, never replacement.

## Platform support

- **Primary target**: Windows 11 (development + manual testing)
- **Linux / macOS**: best-effort until dedicated CI runs land. PRs welcome.

## License

MIT. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE) for attributions to upstream CustomTkinter (Tom Schimansky) and other fork contributors whose work was cherry-picked.

## Project status

Pre-1.0. First release `5.2.2.1`. Develops in parallel with [CTkMaker](https://github.com/kandelucky/ctk_maker) — a visual designer for CustomTkinter UIs.
