# Private HUD and presentation contract

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

D02-S04 connects the existing D01 HUD cap to the D02 resolution contract. It deliberately preserves generated game images, compositor instructions, projection, controller behavior and display startup. Research dimensions describe policy; they do not authorize new modes.

## Composition and integer boundaries

`presentation_geometry()` consumes `resolution_geometry()` and separates the visible viewport, centered HUD rectangle, original 640×480 HUD frame, world-indicator rectangle and logical/active canvas width. Policy calculations use exact fractions. The installed D01 spread cap is derived from the difference between the HUD composition width and the scaled 640-wide frame: `(1920 - 1440) / 2 = 240`. A nonintegral installed cap is rejected, not truncated.

Runtime placement remains authoritative in `asm/ui.asm`: `fit` multiplies by the existing 16.16 scale, shifts down, centers with an arithmetic shift and clips. Polygon positioning additionally uses x87 rounding. These are distinct encodings, not a promise that every rational bound is an integer pixel. No generated floating-point value changed.

| Internal mode | HUD width | HUD origin X | Intended 1P spread | Pre-3D logical columns | Admission |
|---|---:|---:|---:|---:|---|
| 640×480 | 640 | 0 | 0 | 640 | Existing; default-F4 caveat |
| 1024×768 | 1024 | 0 | 0 | 640 | Existing; default-F4 caveat |
| 1280×720 | 1280 | 0 | 160 | 854 | Existing |
| 1920×1080 | 1920 | 0 | 240 | 854 | Existing |
| 2560×1080 | 1920 | 320 | 240 | 1138 | D01 |
| 3440×1440 | 2560 | 440 | 320 | 1146 | Research only |
| 3840×1080 | 1920 | 960 | 240 | 1706 | Research only |
| 5120×1440 | 2560 | 1280 | 320 | 1706 | Research only |

HUD Y remains zero at the composition level, height remains the visible height, and the established HUD frame scale/vertical placement is unchanged. Physical output is independent: 2560×1080 contained on a 2560×1440 desktop has 180-pixel top/bottom bars; matching output aspect would have none. Future 32:9 rendering remains unvalidated.

## D_SPREAD audit

`pre_spread` applies only in the post-3D phase of a round, excludes result/continue sub-states 0xd/0xe, and takes the smaller fitted left/right inset capped by `D_SPREADMAX`. The installed cap remains 240 only for D01-2560; all other existing modes retain their historical unrestricted cap and runtime gates. Research spread values above are not installed into unsupported modes or split layouts.

| Element | Existing rule | S04 treatment |
|---|---|---|
| Timer box/digits | Top band, left of split column; move left by spread | Preserved |
| PLAYER/ENEMY and health bars | Center group using `D_BARDX`, scaled from HUD units | Preserved |
| TOTAL time | Lower rows/right columns move right by spread | Preserved |
| Weapon strips/reticle | Other passes; no timer/bar offset | Preserved |
| Enemy marker and off-screen arrow | Visible-width bounds and horizontal bearing window; vertical bounds unchanged | Full viewport, not HUD rectangle |
| Lock-on line | Existing dedicated geometry correction | Preserved |

For 4:3 the inset is zero. Existing 16:9 spread is unchanged. D01-2560 uses a centered 16:9 HUD even though its world spans the complete width. Wider future modes need the policy cap integrated and tested explicitly. The current marker threshold is sized for the 1P view; the documented split-view late-arrow limitation is not corrected here.

## Pre-3D classification

Classification describes source behavior, not complete visual acceptance. The detailed implementation record remains in [HIRES.md](../HIRES.md).

| Content | Classification | Existing policy / evidence boundary |
|---|---|---|
| Startup logos | PRESERVED | Center authored content; flat/black margins; complete boot sequence needs UAT |
| Title screen | PRESERVED | Original authored block proportions; margin rules avoid extending logo tiles |
| Machine selection | PRESERVED | Text/HUD passes preserve proportions; photo and 3D hangar paths have separate rules |
| Hangar geometry/background | EXPANDABLE | Existing 3D window/projection widening, not image stretching |
| Static/noise | EXPANDABLE | Repeat complete tile fields at their original period |
| Encounter grid | EXPANDABLE | Continue complete rows from the tile ring; authored foreground remains proportional |
| Photo backdrops | PRESERVED | Uniform cover scaling from staged 496×384 picture; centered crop, not stretch |
| Transitions | EXPANDABLE / UNKNOWN | Known full-width damage/wipe paths exist; all transition states are not visually validated |
| Results/continue | PRESERVED / UNKNOWN | Existing state-specific composition and spread exclusions; complete visual coverage pending |
| Credits | PRESERVED | Existing roll/band clipping and moon-card correction; full roll still needs wider-mode UAT |
| World-relative indicators | WORLD-RELATIVE | Actual viewport bounds; do not apply the centered HUD origin |

The existing photo cover policy crops increasingly at wider aspects. This is an explicit tradeoff, not a no-crop claim. S04 preserves it because no evidence justifies redesigning accepted behavior. A future change to contain/letterbox photos requires a separate visual decision. No assets are replaced, stretched or regenerated.

## Canvas ownership and work bounds

The unchanged layout has 4096-byte rows, 480 rows per region and 2048-pixel allocation capacity. D_OFF, D_STAGE and D_COPY retain their S03 addresses and 1,966,080-byte regions, preceded by a guard region. Pre-3D logical width is `((480 * width // height) + 1) & ~1`; active width is separately capped to capacity. Post-3D HUD composition remains a 640-column canvas. Allocated row padding is not visible artwork.

Photo staging copies only 496×384; the uniform 16.16 sampling step is the smaller source/destination ratio, with centered source origin. New tests check all source sample bounds and final active-row/staging addresses across the eight research cases. Existing x86 execution checks exercise the 2560 compositor, HUD/reticle, photo paths and four-region canaries. No extra buffer, copy, render queue, synchronization or runtime geometry calculation is introduced.

## Evidence and remaining gates

VERIFIED: S05 physical evidence confirms successful wrapped 1920 and 2560 initialization; 2560 reached gameplay. Returned logs resolve methods to local ddraw.dll and finish normally (3 calls at 1920, 9 at 2560). The preserved gameplay screenshot shows the centered composition and letterboxing. HUD was accepted; camera, input response and pacing appeared normal. The screenshot's instantaneous FPS overlay does not measure frame pacing or latency.

NEEDS VALIDATION: complete boot/title/select/hangar/encounter/transition/results/credits sequences, photo crop acceptability, HUD/marker behavior throughout gameplay, and later integrated visual UAT. Measured latency and frame pacing remain UNKNOWN.

BLOCKED: default F4 pairing from 4:3 to the default 16:9 alternate retains the known three aspect-dependent hangar-site mismatch. Same-size 4:3 alternates remain the regression comparison path. No new dependency or correction is introduced by S04.

`tools/presentationtest.py` adds the composition/bounds checks and complete Retail/JPRE image comparisons against S03. Existing D01/S02/S03 tests remain authoritative for renderer, relocation, mask, canvas and controller preservation.
