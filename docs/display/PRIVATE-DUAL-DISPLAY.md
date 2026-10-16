# D04-P02 dual-display implementation checkpoint

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

Status: **BLOCKED for UAT delivery**, implementation retained for validation.
Starting private HEAD: `735f453b5b594c2c1c0031d3d0b841c43d22076a`.
Controller Expansion baseline: `73639a4d369dba02c97842906828f588ee4602f5`.
Wrapper base: `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.

## Implementation

One existing D03-P04 game instance supplies the 3840×1080 surface. The private
D3D9 extension draws its uploaded texture to two windowed swap chains, with the
left/right 1920×1080 sources fitted independently into assigned physical monitor
rectangles. Existing monitor discovery, persistent device paths and selection UI
are shared by setup and runtime. Game binaries, renderer passes, cameras,
controllers and DirectDraw call sites are unchanged.

Both draws consume the same uploaded texture before sequential presents. There
is no second simulation, CPU readback or new application frame queue. The normal
composed output remains available for fallback. Additional draws/presents and
possible driver/compositor buffering remain; latency, cross-adapter operation
and synchronized physical scanout are **UNKNOWN**.

Windows are created/destroyed on the render thread, do not request focus, and
hide when the game loses foreground focus or is minimized. Display change or
failed output initialization disables dual presentation for that render-thread
lifetime. Graphics resources are released before reset; original target and
state are restored after drawing. Failure to restore requests normal game close.
Active Windows recovery remains **NEEDS VALIDATION**.

Two Direct3D requirements inform the implementation:
[additional swap chains must be released before reset](https://learn.microsoft.com/en-us/windows/win32/direct3d9/lost-devices),
and [DrawPrimitiveUP clears stream 0](https://learn.microsoft.com/en-us/windows/win32/api/d3d9/nf-d3d9-idirect3ddevice9-drawprimitiveup).
The extension explicitly handles both.

## Validation record

| Gate | Status | Evidence / boundary |
|---|---|---|
| Private wrapper and setup compilation | VERIFIED | Windows i686 cross-build; original wrapper warning retained |
| Source rectangles and geometry | VERIFIED | 36 mixed-size pairs, negative/vertical positions, stable-ID reorder, missing/duplicate/clone rejection |
| Lifecycle, same-texture ownership, UV routing | VERIFIED (host model) | Production code with API doubles; 28 injected graphics failures; focus, disconnect, reset and teardown |
| Retail/JPRE and controller suite | VERIFIED | Existing check suite succeeds; GUI execution skipped internally because Tk is unavailable; CI-only tree check skipped locally |
| D03-P04 state transitions | VERIFIED | 7,128 emulated transitions per edition |
| Original primitive flush isolation | VERIFIED (bounded) | 192 original flush executions with synthetic primitive/material records |
| Single-player image preservation | VERIFIED | Six stamped 1920/2560/3840 Retail/JPRE images match prior checkpoint |
| D03-P04 control package preservation | VERIFIED | ZIP and unpacked manifest unchanged |
| Windows enumeration and INI persistence | NEEDS VALIDATION | Shared code compiles; native APIs not executed here |
| Actual game-frame content at both targets | BLOCKED | No Windows execution environment or captured live-frame integration evidence available |
| Focus, disconnect, reset, exit on Windows | NEEDS VALIDATION | Host fault injection is not native lifecycle acceptance |
| Physical cameras/HUD/targeting/controller ownership | NEEDS VALIDATION | No D04 physical result supplied |

## Delivery decision

No D04-P02 UAT ZIP, launcher pair or automatic return archive is released.
The new internal DLL is an implementation artifact, not a validated candidate.
The mandatory real-game-frame integration gate cannot be satisfied by the host
API doubles or synthetic primitive tests. No claim is made that cnc-ddraw cannot
support the design; this is a validation blocker.

The next gate at this checkpoint was D04-P02 Windows integration and lifecycle
validation using one ready-to-run package and automatic collection of
`RETURN-THIS-D04-P02.zip`. Manual DLL copying, configuration edits and backend
selection were excluded from the test procedure.

Only private display tooling/documentation changed. No public branch, controller
implementation, main, Unified Overlay, camera selection or game simulation was
modified. Nothing was pushed or published.

Build and test details are in [tools/dual_display](../../tools/dual_display/README.md).
