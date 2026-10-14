# Private dual-display presentation

F03C adds a dual-only, verified-movie-window visibility gate. It temporarily hides
the covering P1 output and restores it on observed movie-window lifecycle changes.
See [the F03C record](../../docs/display/PRIVATE-DUAL-DISPLAY-P05-F03C.md).
Physical movie visibility remains **NEEDS VALIDATION**.

D04-P05-F02 uses upstream 1920 shared composition inside the existing 3840×1080
buffer. F02 is physically validated.
See [the F02 record](../../docs/display/PRIVATE-DUAL-DISPLAY-P05-F02.md).

| Phase | Display 1 | Display 2 |
|---|---|---|
| Primary only | Regenerated 1920×1080 shared source | Black |
| Local VS shared | Shared source | Same shared source |
| Local VS gameplay | Left 1920×1080 viewport | Right viewport, or optional mirror of left |

Each source is contained and centered independently on its assigned monitor.
Shared artwork is recomposed using upstream geometry, not cropped from the wide
frame. Original 4:3 content remains governed by upstream layout within the source.
The persistent secondary gameplay option defaults to Player 2. It is available
in the existing monitor assignment UI; monitor IDs and controller ownership are
unchanged. Unknown, invalid, unsupported or uninitialized observations mirror the full
source without assuming gameplay. The mirror gameplay option is ignored in this
explicit fallback. Valid gameplay retains the P03 rectangles.

## Implementation

| Files | Responsibility |
|---|---|
| `inventory.h`, `displays.c` | Discovery, stable assignments, saved gameplay option |
| `layout.h`, `policy.h` | Aspect containment and three-phase routing |
| `state_bridge.c`, `state_bridge.h`, `game_profiles.h` | Read-only original-state capture at primary Flip / direct primary Unlock |
| `build_shared_assets.py` | Generate the isolated shared image and matching observer |
| `build_profiles.py` | Reproduce edition-specific identity and address tables |
| `presentation.h` | Texture-generation policy, output draws and window lifecycle |
| `build_wrapper.py` | Isolated build of the pinned wrapper plus private extension |
| `package.py`, `verify_package.py`, `verify_phases.py` | Assembly, identity/locking checks, hashes and relocation |
| `Launch.ps1`, `Collect-Results.ps1` | Normal launch and automatic diagnostic collection |
| `test_layout.c`, `test_presentation.c`, `test_phases.c`, `test_bridge.c` | Host geometry, lifecycle, routing and bridge tests |

The pinned wrapper remains `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.
Build into a new directory with Python 3.12+, an i686 Windows compiler and windres:

```text
python build_wrapper.py PINNED_CHECKOUT NEW_BUILD_DIRECTORY --cc CLANG_PATH --windres WINDRES_PATH
```

The extension is enabled only by `VO_DUAL_DISPLAY=1`. It reads
`player-displays.ini` beside the game. The private launcher selects D3D9 and
surface locking. Policy is captured after primary Flip swaps the completed backbuffer under the
wrapper global lock. Direct primary Unlock remains supported under that same
global lock. The texture upload copies policy while holding the global lock. Each
texture keeps its own policy until its next successful upload. The existing
nonblocking lock retry avoids holding the global lock while waiting on the game.

Both outputs consume the same uploaded texture generation. No second simulation,
CPU readback, extra full-frame queue or per-frame disk logging is added. Presents
are sequential, not synchronized scanout. Driver/compositor buffering and mixed
refresh rates can add latency. The black output is cleared on each presented
frame because its swapchain uses discard semantics; it does not draw the game.
No per-transition resources are allocated.

P03 foreground ownership, no-activate windows, focus hiding, stacking repair,
reset/disconnect fallback, state restoration and render-thread teardown remain.
The original game window stays active for input and fallback. No input hooks are
added. The helper and original control assets remain unchanged. The dual executable
changes only non-split width operands and their F4 primary entries; the observer
is rebuilt with its matching executable hash.

## Delivery and evidence

Run `START-DUAL-DISPLAY.cmd`; choose monitors and secondary gameplay mode. The
control launcher retains the original D03-P04 package. No elevation, manual DLL
copying, INI editing or compilation is required. Return `RETURN-THIS-D04-P05-F03C.zip`.
If compression fails, its corresponding folder retains the collected logs.

`D04-P02B-presentation.log` retains its inherited name for collection. It adds
phase totals, mirror mode, read validity, identity/RVAs, capture-path counts, last
observed fields and up to 64 transition records. Rendering performs no disk writes.
The external observer continues to record module loading, exceptions and exit.
Host API doubles, cross-compilation and package checks do not establish physical
phase transitions, native UI persistence, scanout timing or movie visibility.

Historical records: [P02B](../../docs/display/PRIVATE-DUAL-DISPLAY-P02B.md),
[LF01](../../docs/display/PRIVATE-DUAL-DISPLAY-LF01.md),
[P03](../../docs/display/PRIVATE-DUAL-DISPLAY-P03.md),
[P04 composition audit](../../docs/display/PRIVATE-DUAL-DISPLAY-P04.md).

F04 adds an opt-in mode-aware package using `package_modes.py` and
`build_wrapper.py --mode-aware`. See [the F04 record](../../docs/display/PRIVATE-DUAL-DISPLAY-P05-F04.md)
and [DUX-V1.0 configuration contract](../../docs/display/DUX-V1.0.md).
The original F03C package/build path remains available for recovery.

[F04A](../../docs/display/PRIVATE-DUAL-DISPLAY-P05-F04A.md) adds explicit, disposable Single/Versus/Mirror test sessions and strict dual failure reporting. F04 movie presentation is preserved.
