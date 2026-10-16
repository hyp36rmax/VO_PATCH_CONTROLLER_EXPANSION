# D04-P02B Windows integration candidate

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

Starting HEAD: `3cdf6624dd57e71a8592530bb8a9f162aed7711a`.
Pinned cnc-ddraw: `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.
Status: **private UAT candidate; Windows and physical acceptance NEEDS VALIDATION**.

## Integration corrections

The dual-mode configuration explicitly selects D3D9; `auto` could otherwise
select a backend without the private output path. Surface locking is enabled
for the dual candidate, using the wrapper's existing DirectDraw Lock/Unlock
critical section. The upload path tries that lock without blocking while holding
the global wrapper lock. Contention releases the global lock, requeues the frame
notification and sleeps 1 ms before retrying. This avoids a lock-order deadlock
and losing the final frame notification. Original game calls remain unchanged.

The uploaded texture generation is recorded separately for each successful output
Present. Both targets draw the same texture before either presents. P1 samples
(0,0,1920,1080), P2 samples (1920,0,1920,1080). No CPU framebuffer readback or
second game instance is introduced. Sequential presents cannot guarantee matching
physical scanout times; a failed second present can briefly leave unequal output
generations before fallback hides both windows. Latency remains UNKNOWN.

D04-P02 lifecycle policy remains: no-activate render-thread windows, hide on loss
of game focus, disable dual output after display changes/failures, release extra
resources before reset, restore original drawing state and destroy windows on
render-thread exit. Restoration failure requests normal game closure. These
paths are tested with API doubles; native runtime behavior is pending.

## Launch and collection

One ZIP contains the dual candidate and a byte-identical D03-P04 Local VS control.
Both reuse the existing external observer and game identity. The dual launcher
runs display discovery and the existing assignment UI, then automatically starts
the observer/game. Cancelled selection stops launch. Saved monitor paths persist.
A named mutex and process check prevent another package/game session from being
launched concurrently. These are launch checks, not global input interception.

The final archive is `RETURN-THIS-D04-P02B.zip`. It contains startup/exception/module
logs, presentation generation counts, assignments, launch status, INI configuration
and hashes; no game assets or captured memory. Collection runs after normal exit,
launch failure or cancelled selection. A crash may prevent the render-thread log,
so missing logs remain visible in collection status. Windows process launch,
PowerShell collection and filesystem error behavior still need execution tests.

Launchers contain actual CRLF line endings. The older control package's launcher
text is not reused. Controller settings are allowed to change between runs without
invalidating immutable executable/DLL checks.

## Evidence

| Check | Status | Boundary |
|---|---|---|
| Windows wrapper/setup cross-build | VERIFIED | i386 PE files; not Windows execution |
| Dependency/import inspection | VERIFIED | System/API-set imports; no extra compiler runtime DLL dependency |
| Existing display/controller suite | VERIFIED | 33 reported passes; GUI internally skipped for missing Tk, CI-only tree check skipped |
| D03 transition emulation | VERIFIED | 7,128 states per edition |
| Original flush isolation | VERIFIED | 192 bounded executions; synthetic primitive records |
| Geometry/assignment policy | VERIFIED | 36 size pairs and identity/availability/clone cases |
| Graphics lifecycle faults | VERIFIED (host doubles) | 28 failure points plus frame generation ownership |
| Native display discovery and INI persistence | NEEDS VALIDATION | Shared implementation cross-built; real Windows APIs unexecuted |
| Game/helper/control preservation | VERIFIED | Byte comparisons and prior image hashes |
| Relocation/package CRC and hashes | VERIFIED | Extracted into a path with spaces and non-ASCII characters |
| PowerShell launcher/collector | NEEDS VALIDATION | Static and bounded archive-subset checks only |
| Live content at both physical targets | NEEDS VALIDATION | No Windows environment available on the build host |
| Latency, driver buffering, cross-adapter behavior | UNKNOWN | Requires physical observation/instrumentation |

No actual-frame GPU delivery pass or native lifecycle pass is claimed. The
D04-P02B brief permits an experimental UAT candidate after applicable internal
checks, with these boundaries explicit.

## Consolidated UAT

Extract once. Launch `START-DUAL-DISPLAY.cmd`, select displays and save, then select
original Local VS. Check P1/P2 monitor identity, 16:9 composition, independent
cameras, HUD/targeting and controller ownership. Observe pacing/responsiveness,
Alt+Tab and minimize/restore. Exit and confirm both outputs disappear. Run
`START-LOCAL-VS-CONTROL.cmd` for comparison, then return the automatically selected
archive with observations. Fallback to one composed window is not dual-output
success. The package required no manual configuration edits or DLL copying.

The next milestone remains D04-P02B acceptance and corrections supported by its
results. D04-P03 is not started. No controller/game/camera code, public branch,
main or Unified Overlay is changed. Nothing is pushed or published.
