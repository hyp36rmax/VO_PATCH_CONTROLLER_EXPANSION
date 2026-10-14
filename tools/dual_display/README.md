# Private display assignment preparation

Status: setup and geometry implemented; presentation backend NOT IMPLEMENTED.
No game launch or dual-display runtime integration is provided.

`displays.c` uses QueryDisplayConfig active paths, target monitor device paths,
GDI current modes and monitor primary flags. It reports coordinates, dimensions,
refresh numerator/denominator, rotation and availability. It retries inventory
races up to three times and rejects incomplete/oversized inventories rather
than silently routing an incomplete list. Windows execution is pending.

The two display selectors save monitor device paths beside the setup executable.
Default selection is primary for P1 and a distinct active display for P2.
Missing saved identities require reassignment; no silent ID substitution.
A display-change message closes setup rather than saving stale choices.
`--list` prints discovery and assignment status without opening setup.

`layout.h` contains host-testable routing policy. Sources remain the existing
1920×1080 left/right rectangles. Destinations use integer 16:9 containment in
each monitor's physical desktop rectangle. Negative coordinates and vertical
arrangements are supported. Failure leaves outputs unchanged. Fallback results
are decisions only: no running presentation backend consumes them yet.

Build setup with an i686 Windows compiler using `-municode -luser32`.
Compile/run `test_layout.c` with C11 and address/undefined-behavior sanitizers.
No game/controller/wrapper binaries are changed.

## Presentation dependency

Pinned cnc-ddraw 279a057ee7e1e4d584b56141c014ab01f3c6ee6d has one output
window/device in its D3D9 path. `d3d9_render_main` uploads the primary surface
under its existing locks, releases those locks, draws and calls device Present.
Its failed Present path sends WM_D3D9DEVICELOST to the original game window.

A compatible extension could reuse that uploaded texture for two source
rectangles and additional swap chains. It still needs explicit ownership of
output windows, device/reset/teardown state, input focus, and recovery to the
original output. Same-texture sequential presents would share a frame but
would not guarantee simultaneous physical scanout or zero extra latency.

No extension has been installed or tested. Capturing the existing composed
window would instead lose source resolution and require a separate copy/capture
path; it was not substituted for proper source routing. No unsafe candidate
or dual-display UAT ZIP is produced. The D03-P04 control remains unchanged.
