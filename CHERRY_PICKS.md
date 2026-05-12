# Cherry-pick catalog

Phase 1 output: bug-fix shortlist from competing forks.

**Survey date:** 2026-05-12

## Sources surveyed

| Source | Status | Verdict |
|---|---|---|
| [FedericoSpada/Custom2kinter](https://github.com/FedericoSpada/Custom2kinter) | ✅ surveyed | 55 non-merge commits since `v5.2.2` — primary cherry-pick source |
| [wipodev/Stukk](https://github.com/wipodev/Stukk) | ❌ 404 | repository deleted or made private as of 2026-05-12 — unavailable; HighDPI cherry-picks must come from another source |
| Hancie123/CustomTkinter | ❌ stale | last commit 2022-10-04 at CTk `4.6.3` — pre-dates v5.2.2 baseline; the 16 stars reflect fork-as-is, not contributions; **nothing to pick** |

## Phase 1b — Hancie123 deferred? — NO

Hancie123 is not deferred — it is **dismissed permanently**. The fork has no work past `v4.6.3` and would only bring backports of changes that upstream already shipped in 5.x.

## Phase 1c — Stukk replacement source needed

Original plan relied on Stukk for HighDPI cherry-picks. With Stukk unavailable, options:

- Custom2kinter's own DPI-related commits (e.g. `9ad9495` dropdown + rescaling, `76a10bd` widget-scaled int values) cover some DPI ground.
- HighDPI improvements may need to be **researched and implemented fresh** in `inspired by` form during Phase 3 if Custom2kinter's coverage proves insufficient.

## Custom2kinter cherry-pick shortlist

Bug fixes likely worth porting (in v5.2.2..master order):

| Commit | Description | ekosystema impact | Worth it? | Proposed tag |
|---|---|---|---|---|
| `db08925` | Improved/fixed `configure()` method for all widgets | **high** (touches every widget's public API) | ✅ very high value, but inspect carefully | `port(rewritten)` likely |
| `8d62feb` | Improved/fixed `cget()` method for all widgets | high (same reason) | ✅ pair with `db08925` | `port(rewritten)` likely |
| `b2bb1e0` | Fix `text_color_disabled` of CTkLabel (#2063) | low | ✅ small surface, easy port | `port(verbatim)` likely |
| `2070277` | Quick fix of set `text_color` operation (#2078) | low | ✅ | `port(verbatim)` likely |
| `907300e` | Scrollbar drag offset (#2158) | low | ✅ | `port(verbatim)` likely |
| `84222ab` | Toplevel custom icon overriding on init (#2162) | med (CTkToplevel = ekosystema base) | ✅ but compat-test | `port(verbatim)` |
| `8ff5d94` | CtkCanvas.coords add return values (#2240) | low | ✅ pure addition | `port(verbatim)` |
| `9ad9495` | Exception destroying dropdown then rescaling (#2246) | med (DPI path) | ✅ DPI safety | `port(verbatim)` |
| `27db1bd` | Improved CTkTabview renaming (#2256) | low | ✅ | `port(verbatim)` |
| `5c77c99` | Fix scrollable frame destroy (#2352) | low | ✅ | `port(verbatim)` |
| `76a10bd` | Widget-scaled int values cast back to int (#2468) | med (DPI scaling math) | ✅ helps Stukk replacement gap | `port(verbatim)` |
| `1ad3c10` | Scrollbar covers borders in ScrollableFrame (#2548) | low | ✅ | `port(verbatim)` |
| `ebd3b71` | Add missing scaling base class destroy in dropdown_menu (#2772) | med (DPI path) | ✅ | `port(verbatim)` |
| `f605aba` | Fix typo causing app slowdown (#2680) | low | ✅ perf win | `port(verbatim)` |
| `f81cd8d` | Reset Minsize for CTkButton (#1931) | low | ✅ | `port(verbatim)` |
| `a0a6496` | Fix `.delete()` to destroy CTkFrame (#1083) | low | ✅ | `port(verbatim)` |
| `c12c9ab` | Improved scroll behavior for CTkScrollableFrame | low | ✅ | inspect first |
| `8c85d9b` | Fixed some bugs with the previous changes | unknown | ⚠ inspect — depends on what "previous changes" were | inspect |
| `73bc7ad` | Recreated 3 Pull Requests that weren't perfect | unknown | ⚠ inspect | inspect |
| `73ca84f` | Improved user experience | unknown | ⚠ inspect (vague label) | inspect |
| `6a5460b` | MouseWheel detection: CTkSlider + CTkScrollbar | low | ✅ but is it bug fix or feature? Inspect | likely `port(verbatim)` |

## Phase 4 wishlist candidates (NOT in Phase 2 cherry-pick — Phase 4 promotion only)

| Commit | Description | Promote to Phase 4? |
|---|---|---|
| `cb7347b` | Added border to CTkLabel | yes — already discussed |
| `f159a25` | Orientation option to CTkSegmentedButton (#2333) | maybe — niche but cheap |
| `cea11a0` | segmented_button_font option to CTkTabview | maybe |
| `b33e220` | New utility methods to all widgets | inspect — could be useful or noise |
| `7bb5610` | New methods to ctk_tabview.py (#1428) | inspect |

## Skipped (out of scope)

| Commit | Reason |
|---|---|
| `a6e0722` Showroom App | Irrelevant — CTkMaker is the Showroom for us |
| `a796f6e` Bump to 5.3.0 | Federico's versioning, conflicts with ours |
| `51b3435` Update CHANGELOG | Federico's CHANGELOG style differs |
| `108ef4c` Auxiliary files for PyPI release | Federico-specific |
| `9a9453a`, `9420ac3`, `db15fe1`, `874503e`, `3986336`, `2e11a1e`, `764a302`, and 10× `Update Readme.md` | Docs/internal Federico changes |

## Effort estimate

- ~17 commits in "✅ port" status — Phase 2 work
- ~4 in "⚠ inspect" — Phase 2 entry triage
- ~5 candidates parked for Phase 4 wishlist

Phase 2 estimate (plan: 3-5 focused days) holds. Phase 1 timebox was 2 days; actual: ~30 minutes (only one fork had work to survey).

## Open questions

- **Stukk replacement:** during Phase 2, if DPI gaps appear, do we research independently (`inspired by`) or shelve until Phase 3? Decide when first DPI gap surfaces.
- **`8c85d9b` "Fixed some bugs with the previous changes"** depends on what the previous changes were — needs `git show` inspection at Phase 2 start.
