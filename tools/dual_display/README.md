# Private dual-display presentation

Status: **implementation checkpoint; NOT UAT-ready**. The D3D9 extension builds,
but actual Windows game-frame delivery has not been executed. Do not distribute
the internal DLL as an accepted dual-display package.

## Components

| File | Responsibility |
|---|---|
| `inventory.h` | Shared D04-P01 Windows discovery and saved identity reader |
| `displays.c` | Existing P1/P2 assignment interface and persistence |
| `layout.h` | Fixed left/right sources and 16:9 destination containment |
| `presentation.h` | Existing uploaded game texture to two additional D3D9 swap chains |
| `build_wrapper.py` | Isolated build from the exact pinned wrapper revision |
| `test_layout.c` | Host geometry, identity and invalid-assignment tests |
| `test_presentation.c`, `presentation_test_api.h` | Production lifecycle with fault-injected API doubles |

The extension is enabled only by `VO_DUAL_DISPLAY=1`. It reads
`player-displays.ini` beside the game executable, using the same monitor device
paths as setup. Setup must reside there to edit that configuration. Missing
saved identities are not silently reassigned. Defaults select the primary
monitor for P1 and a separate active monitor for P2.

`QueryDisplayConfig` inventories active paths, with bounded retries for display
changes. Geometry uses physical desktop coordinates, including negative and
vertical positions. Monitor dimensions, rational refresh, rotation and identity
remain available through setup's `--list` output. Enumeration and Windows INI
round-trip execution still need native validation.

## Backend contract

Pinned cnc-ddraw: `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.

`build_wrapper.py` extracts that exact Git tree into a new directory, adds the
three private headers and applies checked, single-match integration edits to
`render_d3d9.c`. It does not edit the pinned checkout or any game executable.
Python 3.12+, an i686 Windows C compiler and windres are required. Example:

```text
python build_wrapper.py PINNED_CHECKOUT NEW_BUILD_DIRECTORY --cc CLANG_PATH --windres WINDRES_PATH
```

The existing renderer uploads the primary surface under its existing locks.
Only successful texture unlocks mark an uploaded texture available. Immediately
before the original device Present, the extension samples that same texture
into P1 `(0,0,1920,1080)` and P2 `(1920,0,1920,1080)`. Texture coordinates use
allocated texture dimensions, not an assumed 3840-wide texture. Both target
draws finish before either target presents. Point sampling prevents filtering
across the player boundary; mixed-resolution scaling may therefore look less
smooth than the original filtered presentation.

The extension makes two GPU draws and two sequential presents, without CPU
readback or an additional application frame queue. The original composed-window
render/present remains active for fallback. This costs additional GPU work and
can add driver/compositor buffering. Cross-adapter behavior and latency are
unknown; identical source texture ownership does not guarantee synchronized
physical scanout.

Output windows belong to the render thread, use no-activate/tool-window styles,
and are shown without activation only while the original game owns foreground
focus. They hide on focus loss/minimize. No keyboard/controller hooks are added.
Window messages are pumped while waiting for frames, using bounded waits only
when output windows exist.

Display changes, output closure, missing identities and graphics failures disable
the extra outputs for that render-thread lifetime. Reset releases additional
swap chains, target references and the saved state block first. Original render
target/state/stream 0 are restored after output drawing. A restoration failure
requests normal game closure because continuing with unknown graphics state is
unsafe. These policies have host tests; their Windows behavior is not yet proven.

At render-thread exit, windows are destroyed by their owning thread and a compact
`D04-P02-presentation.log` is appended beside the executable. It records uploads,
draw iterations, successful present pairs, fallback, HRESULT, identities and
rectangles. There are no per-frame disk writes. This internal logger is not yet
a verified automatic UAT collector and cannot guarantee a log after a crash.

## Verification boundary

Host tests exercise production lifecycle code through API doubles, including
28 graphics-call failures. They do not execute Windows, D3D9 or a real game
session. The inherited original-renderer flush tests use synthetic primitive
records; they likewise do not establish actual game-frame delivery to monitors.

The missing acceptance gate is a Windows integration run that verifies real game
content at both targets, plus focus/reset/disconnect behavior. No ready-to-run UAT
ZIP has been produced at this checkpoint. The original D03-P04 package remains
unchanged. See [the engineering record](../../docs/display/PRIVATE-DUAL-DISPLAY.md).
