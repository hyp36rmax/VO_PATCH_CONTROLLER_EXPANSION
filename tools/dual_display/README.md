# Private dual-display presentation

D04-P05 implements three-phase presentation on the physically validated D04-P03
backend. New phase behavior and the new setup option **NEED WINDOWS VALIDATION**.
See [the P05 record](../../docs/display/PRIVATE-DUAL-DISPLAY-P05.md).

| Phase | Display 1 | Display 2 |
|---|---|---|
| Primary only | Complete 3840×1080 source | Black |
| Local VS shared | Complete source | Same complete source |
| Local VS gameplay | Left 1920×1080 viewport | Right viewport, or optional mirror of left |

Each source is contained and centered independently on its assigned monitor.
Shared 32:9 content is letterboxed on 16:9 displays; no centered-HUD crop is used.
The persistent secondary gameplay option defaults to Player 2. It is available
in the existing monitor assignment UI; monitor IDs and controller ownership are
unchanged. Unknown game identity falls back to original P03 routing, ignoring
the mirror option. An unrecognized state retains the last verified policy.

## Implementation

| Files | Responsibility |
|---|---|
| `inventory.h`, `displays.c` | Discovery, stable assignments, saved gameplay option |
| `layout.h`, `policy.h` | Aspect containment and three-phase routing |
| `state_bridge.c`, `state_bridge.h`, `game_profiles.h` | Read-only original-state capture at primary-surface unlock |
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
surface locking. Policy is captured before primary Unlock publishes the frame;
the texture upload copies policy while holding that same surface lock. Each
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
added. The game, helper, observer and original control assets remain unchanged.

## Delivery and evidence

Run `START-DUAL-DISPLAY.cmd`; choose monitors and secondary gameplay mode. The
control launcher retains the original D03-P04 package. No elevation, manual DLL
copying, INI editing or compilation is required. Return `RETURN-THIS-D04-P05.zip`.
If compression fails, its corresponding folder retains the collected logs.

`D04-P02B-presentation.log` retains its inherited name for collection. It adds
phase totals, mirror mode, unknown-state count and the last unknown input fields.
The external observer continues to record module loading, exceptions and exit.
Host API doubles, cross-compilation and package checks do not establish physical
phase transitions, native UI persistence, scanout timing or movie visibility.

Historical records: [P02B](../../docs/display/PRIVATE-DUAL-DISPLAY-P02B.md),
[LF01](../../docs/display/PRIVATE-DUAL-DISPLAY-LF01.md),
[P03](../../docs/display/PRIVATE-DUAL-DISPLAY-P03.md),
[P04 composition audit](../../docs/display/PRIVATE-DUAL-DISPLAY-P04.md).
