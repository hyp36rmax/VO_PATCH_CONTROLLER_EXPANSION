# D04-P03 independent P1 presentation candidate

Previous private HEAD: `d33104b1eac615601bad60d50c9cca3634768b85`.
Wrapper base remains `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.
Status: internal checks VERIFIED; corrected physical P1 output NEEDS VALIDATION.

## Physical evidence recovered

The user's LF01 return archive reports successful discovery, assignment and
observer exits. Two presentation lifetimes recorded 426 and 12,812 successful
pairs, no fallback, HRESULT zero and equal final P1/P2 generations. Sources were
exactly (0,0,1920,1080) and (1920,0,1920,1080). Destinations were the 2560×1440
laptop at (0,0) and 1920×1080 external display at (2560,0).

The user confirms working Local VS and independent P2 on the external display,
while the laptop showed the combined frame. The return logs establish successful
render/present calls, not visible window order. No successful dual-display
screenshot was located in the supplied review directory; the visual finding is
attributed to the user's report.

## Smallest correction

The original wrapper can raise the combined input/game window, including topmost
paths. Both extra outputs were only raised with HWND_TOP, and visibility returned
early once they had been shown. That policy could leave the correctly rendered
P1 window behind the original combined output. This is a source-supported stacking
defect consistent with the physical result; the old log did not capture the exact
Windows Z order.

P1 now uses HWND_TOPMOST with SWP_NOACTIVATE. While the original game has foreground
focus, enumeration stops at the first of P1 and the original game window. A stacking
inversion re-raises P1; correct order causes no additional positioning call. P2's
HWND_TOP policy and all texture/source/draw/present operations remain unchanged.
The original game window is not hidden, moved, reparented or used as a replacement
presentation target. Keyboard/controller focus stays with that original window.

[Microsoft's SetWindowPos contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos)
distinguishes topmost placement from activation. The existing focus-loss/minimize
policy hides outputs, preventing P1 from deliberately remaining above other apps.
Native focus races and window behavior remain part of physical acceptance.

## Preservation and validation

| Item | Status / boundary |
|---|---|
| P2 on external display, mixed resolutions | Physical LF01 result reported by user; preserved implementation |
| P1/P2 source and GPU presentation code | VERIFIED source-identical from initialization through cleanup |
| P1 stacking, re-raise, no redundant positioning | VERIFIED with production-code API doubles |
| Original window untouched, focus, minimize/restore | VERIFIED with API doubles; Windows retest pending |
| Mixed geometry | VERIFIED with 36 size pairs, including 2560×1440 / 1920×1080 |
| Fault handling / frame generation | Existing 28 graphics failure points and generation checks retained |
| Retail/JPRE/controllers | Existing regression suite; GUI internally skipped where Tk unavailable |
| Game/helper/observer/configuration | Byte-preserved relative to LF01; only private dual DLL changes |
| Single-player images | Six generated 1920/2560/3840 images remain byte-identical |
| Physical corrected P1 / P2 regression | NEEDS VALIDATION |
| Latency / scanout alignment | UNKNOWN; no timing measurement or perfect-sync claim |

Both outputs still draw from the same uploaded generation before sequential
presents. The correction adds a window-order query and a reposition only when
needed, without GPU work, CPU framebuffer readback or an extra frame queue.
Recovery, display disconnect and teardown use the existing implementation.

## Consolidated acceptance

Extract `D04-P03-PRIVATE-UAT.zip`; launch `START-DUAL-DISPLAY.cmd` normally. Verify
P1-only laptop and P2-only external output, 16:9 framing, independent cameras,
player-specific HUD/targeting, controllers, no visible combined image during Local
VS, Alt+Tab/minimize/restore, responsiveness and clean shutdown. Run the retained
Local VS control if comparison is needed. Return `RETURN-THIS-D04-P03.zip`, or its
same-named raw-log folder if compression fails. No administrator privileges or
manual configuration changes are requested.

Startup/menu rendering and existing source-routing policy are unchanged. Revealing
P1's previously obscured window may expose the current split treatment of shared
screens; menu usability must be observed. Mirrored attract/shared presentation is
not implemented. Future shared presentation should show the same centered content
on both displays and transition using the original game's presentation state,
not a new state machine.

Next milestone: physical P03 acceptance and evidence-based corrections. No public
push, main/Controller Expansion changes, Unified Overlay or mirrored attract work.
