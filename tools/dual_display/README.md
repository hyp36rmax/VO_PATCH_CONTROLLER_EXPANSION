# Private dual-display presentation

Status: **D04-P02B-LF01 launcher/log correction; Windows retest pending**.
The D3D9 extension and launch/collection integration pass applicable host checks.
Cross-compilation and API doubles do not establish Windows or physical results.

## Components

| File | Responsibility |
|---|---|
| `inventory.h` | Shared D04-P01 Windows discovery and saved identity reader |
| `displays.c` | Existing P1/P2 assignment interface and persistence |
| `layout.h` | Fixed left/right sources and 16:9 destination containment |
| `presentation.h` | Existing uploaded game texture to two additional D3D9 swap chains |
| `build_wrapper.py` | Isolated build from the exact pinned wrapper revision |
| `package.py`, `verify_package.py` | Self-contained candidate assembly and static integrity/relocation checks |
| `Launch.ps1`, `Collect-Results.ps1` | Single-session launch, assignment UI and automatic diagnostic archive |
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

The dual candidate explicitly selects D3D9 and enables the existing surface-lock
option. The game holds that lock from DirectDraw Lock through Unlock; the existing
renderer uploads the primary surface only after acquiring it. A nonblocking
acquisition avoids waiting for the game while holding the wrapper global lock.
On contention it drops the global lock, requeues its semaphore, sleeps 1 ms and
retries, so the final unlock notification cannot be lost. This can add latency.
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
`D04-P02B-presentation.log` is appended beside the executable. It records per-output uploaded generations, uploads,
draw iterations, successful present pairs, fallback, HRESULT, identities and
rectangles. There are no per-frame disk writes. The retained external observer also records module loading, exceptions and process
exit. The PowerShell collector gathers both logs, assignments and launch status
into `RETURN-THIS-D04-P02B-LF01.zip`. Missing logs are explicit failures to obtain
evidence, never success. The collector has static/model checks; Windows execution
and crash-path delivery remain pending.

## Verification boundary

Host tests exercise production lifecycle code through API doubles, including
28 graphics-call failures. They do not execute Windows, D3D9 or a real game
session. The inherited original-renderer flush tests use synthetic primitive
records; they likewise do not establish actual game-frame delivery to monitors.

The next gate is the consolidated Windows UAT session: real game content at both
targets, focus/reset/disconnect behavior, cameras, HUD/targeting, controller
ownership, responsiveness and clean exit. Actual game-frame GPU delivery is
NEEDS VALIDATION, not inferred from host doubles. The D03-P04 control assets and
observer are byte-identical. The dual mode changes only wrapper/configuration and
adds setup; game binaries and controller files remain unchanged.

Launch either `START-DUAL-DISPLAY.cmd` or `START-LOCAL-VS-CONTROL.cmd` from the
extracted candidate. The former runs existing display selection and then the
observer/game. Cancellation does not start the game. A named mutex plus an
existing-game check prevents duplicate package sessions. Relative paths support
relocation; controller INIs are deliberately mutable across launches while DLLs
and executable hashes remain checked. No manual DLL copying or INI editing is
required.

See [the D04-P02B record](../../docs/display/PRIVATE-DUAL-DISPLAY-P02B.md) and the
[historical D04-P02 checkpoint](../../docs/display/PRIVATE-DUAL-DISPLAY.md).

## LF01 launcher correction

The assignment utility is now `DISPLAY-ASSIGN.exe` with an embedded `asInvoker`
manifest. The previous 32-bit `DISPLAY-SETUP.exe` had no execution-level manifest,
meeting Windows installer-detection criteria. This is the identified packaging
defect; the original physical failure did not retain an exact failing-process
trace. Launch now logs each process path, arguments, working directory, exit code
and native errors without requesting elevation or changing compatibility policy.

Collection first copies diagnostics into timestamped subfolders of
`RETURN-THIS-D04-P02B-LF01`, then explicitly loads both compression assemblies.
A ZIP failure leaves that folder and original logs intact. Collection occurs after
launch/session completion and is not a game-start dependency. The wrapper, game,
controller helper, observer and renderer configuration are unchanged from P02B.
See [the LF01 record](../../docs/display/PRIVATE-DUAL-DISPLAY-LF01.md).
