# Private intro-movie window observer

Historical F03B diagnostic. The findings below describe the investigation before
the later [F03C visibility correction](../../docs/display/PRIVATE-DUAL-DISPLAY-P05-F03C.md).

F03B observes the unchanged F02 game externally. It opens and flushes its own
log before launching `game/v_on.exe` with an explicit executable path and working
directory. There is no debugger, injection, target memory access, input hook,
window mutation, desktop-mode change or elevation. The observer's own manifest
uses per-monitor DPI awareness so measurements do not depend on DPI virtualization.

Every 250 ms it enumerates top-level windows in Z order and recursively enumerates
the target process's children. Records include process/thread identity, window
class/title, structural parent/owner, sibling order, root, visibility/iconic/cloaked
state, style flags, screen/client bounds, foreground and target-thread active HWND,
and nearest monitor device/bounds/primary flag. Saved player assignment is copied
from the recorded physical-test evidence and included in collected results.

Presentation windows have explicit role hints from their known class/title.
Movie class and active game-window hints remain candidates, not asserted identities.
`POSSIBLE_COVER` identifies visible overlapping top-level windows above the target's
root. It does not account for opaque regions, transparency, DWM composition or
pixels. It never proves decoded video is visible. Other processes' titles are
not recorded. Child sibling order is preserved separately; it is not reduced to
an unsupported occlusion claim.

Appearance/disappearance timestamps mean first/last observation, not exact
creation/destruction or movie/menu state changes. Incomplete enumeration suppresses
disappearance inference. HWND reuse and windows shorter than the sample interval
remain limitations. End-of-process records test whether last-observed handles
still exist; a surviving/reused handle is not automatically an orphan game window.

Limits: 256 target windows, 256 stored top-level windows, 1024 enumerated top-level
windows per sample, 14,400 samples and 16 MiB logging. Limits/errors are recorded.
After a capture limit the observer waits for process exit without further sampling.
It closes its process/thread handles and log; it never terminates the game.

## Build and validation

Use `build.py OUTPUT --cc I686_CLANG --windres I686_WINDRES` and `package.py` with
the preserved F02 package and assignment-evidence ZIP. `verify.py PACKAGE
--readobj LLVM_READOBJ` runs the sanitized host model, binary capability checks,
original-file hashes, manifest/collector contracts and relocated ZIP extraction.
Host tests and PE inspection are not native Windows execution tests.

The private session is extraction → `START-MOVIE-OBSERVATION.cmd` → let movie
begin and wait about 10 seconds → skip normally → confirm menu → exit.
The ten-second instruction is a user observation interval, never a classifier.
Return `RETURN-THIS-D04-P05-F03B.zip`. Raw logs remain if compression fails.
No movie correction is included. Root cause and correction remain UNKNOWN until
returned evidence is reviewed; window metadata may still leave framebuffer bypass
or the native decoder's exact drawing API unresolved.
