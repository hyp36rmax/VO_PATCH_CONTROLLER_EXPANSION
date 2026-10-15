# Unified Overlay foundation — private P01-F03

The seven-entry menu adds optional access during verified title, attract-demo and
offline gameplay states. Installation, controller profiles and configuration
remain with their existing authorities. Physical Windows acceptance is pending.

## Controls and availability

| Input | Behavior |
|---|---|
| ESC | Open, Back from a placeholder page, close at root; release before repress |
| Controller Start / native Pause | Original game behavior; never activates overlay |
| P1 left lever / existing directions | Navigate using the current F7 profile |
| Existing accept | Select, including BACK and RESUME; native Raphnet uses Start |
| Keyboard | Arrows and Enter |
| Mouse | Hover, click, scroll when necessary; visible BACK and RESUME |
| F11 Extras | Additive “Unified Overlay...” fallback |
| F10 | Unassigned |
| Original F-keys | Relinquish overlay and run the original handler |

CONTROLLERS, DISPLAY, GRAPHICS, GAME SETTINGS and EXTRAS display an explicit
unavailable notice. Their BACK and RESUME controls are selectable with P1
navigation. No configuration pages are implemented.

| Original state | Overlay policy |
|---|---|
| Attract machine 1, substates 6 / 23 | Title prompt eligible |
| Attract machine 1, substate 17 | Title menu eligible |
| Attract machine 1, substate 7 | Automated match eligible |
| Match machine 4, substates 8–12 | Offline Solo / Local VS eligible |
| Movie flag bit 0 set | Excluded; original movie controls pass through |
| Network mode 2, startup and other states | Excluded |

Title and demo states follow the original dispatcher documented in
`asm/titlever.asm`; match states follow the original input predicate. No delay
or resolution heuristic determines eligibility. Transitions between eligible
states retain the menu. Entering an ineligible state dismisses it without
queuing a later reopen.

## Input and pause ownership

The original `vontanita.dll`, source, claim dialogs, release-before-press policy,
and capture logic remain unchanged. `voinputux.dll` forwards each original API
call once. Closed or ineligible overlay input is untouched. Only assigned P1
samples enter menu navigation; P2 input is not suppressed.

While open or awaiting navigation release, only P1 directions and existing
accept are filtered. XInput Start, native Pause, unrelated controls and the
individual reset-chord buttons retain their destinations. The five-button reset
detector is bypassed in generated private images; its underlying reset remains available. Native Start is consumed solely
as existing confirmation inside the explicitly opened overlay. No controller
button posts ESC or an activation request.

A guarded seam after P1's original DirectInput read clears only arrows, Enter
and ESC from that player's key buffer while the menu owns input. It preserves
the original read/reacquire path, compare flags, other keys and P2 buffer.
Keyboard navigation samples are edge-gated; ESC messages are processed separately
before accelerator dispatch, avoiding duplicate asynchronous ESC processing.

Overlay visibility is independent of the inactive flag. Neither open nor close
calls GPAUSE/GRESUME. A running game continues running; a paused game remains
paused. Selecting RESUME dismisses the menu without changing the pre-existing
pause state. F3/Start retains the game's original Pause/Resume operation.

## Presentation and recovery

The guarded `.vouo` bridge retains the original pump, window procedure, inactive
rendering path and pre-flip seam. The inactive hook calls the original idle exactly once and preserves its return
value. It never invokes FRAME or Flip. No simulation clock, overlay window or
separate display system is added.

GDI drawing is explicitly flushed before releasing the composed surface. The
pinned wrapper's ReleaseDC does not flush GDI's per-thread batch; the flush closes
that CPU-drawing/publication race. The regression models delayed drawing and
rejects an unflushed surface. The user confirmed active-gameplay overlay presentation without flicker in F02.
The remaining paused-only conflict was forcing FRAME/Flip while the original
pause screen draws on PRIMARY without flipping. F03 composes on PRIMARY after
the original pause drawing, within the same surface lock used by the pinned
D3D9 upload. A retained bitmap restores the clean image before each paused draw
and on dismissal. A clean pre-overlay backbuffer capture prevents an overlay
from becoming baked into the frozen image when Start pauses active gameplay.
The bitmap is reused while the source surface is unchanged. Missing synchronization
or drawing resources release overlay ownership. Physical F03 acceptance remains pending.

Single centers the bounded panel in the selected source aspect; Versus confines
it to P1; Complete Mirror presents the same composed image on both displays.
Text scales uniformly. Mouse mapping retains the existing output/source fit.
Cursor visibility increments are balanced on dismissal and recovery.

Focus loss, unavailable drawing surfaces, movie entry and legacy F-key access
release overlay ownership. No focus stealing, window recreation, forced resume,
movie lifecycle change or automatic reopening is introduced. Keyboard and mouse
remain usable if P1 disconnects. Display fallback remains unchanged.

## Exit to Title

The root entries are CONTROLLERS, DISPLAY, GRAPHICS, GAME SETTINGS, EXTRAS,
RESUME and EXIT TO TITLE. Exit opens a confirmation with CANCEL selected,
“Return to the title screen?” and “Current match progress will be lost.”
A fresh keyboard/controller press or mouse click is required. Cancel returns
to the root; confirmation releases navigation ownership before requesting reset.

Exit is enabled only in eligible offline match states (mode 4, substates 8–12,
game mode 0/1). Title and attract keep the entry disabled; network mode 2 remains
excluded. Eligibility is checked again at confirmation and after input release.

The original negative-mode dispatch calls original teardown then boot. F03 sets
MODE to -1, calls original CDSTOP, and sets MODE2 to -1 for Local VS, matching
upstream reset semantics. It does not call teardown directly, restart the process,
or replace controller initialization or display restoration. A confirmed paused
exit calls original GRESUME first because the inactive loop does not tick the
state machine; reset is rejected if the original surface guard refuses resume.
This exception does not apply to normal overlay opening, Back or Resume.

The guarded PADX edit jumps around only the chord detector to its existing key
dispatcher. LB/RB/LT/RT/Start retain individual behavior, including Start pause.
Upstream controller source and profile maps are unchanged.

## Configuration and diagnostics

Display settings remain in `player-displays.ini`; controller settings remain
with F7. Future overlay pages must use these same authorities.

Diagnostics default to Off. Existing restart, immediate Off, explicit export,
retention and no-upload rules remain unchanged. The bounded `overlay_lifecycle`
event contains only a numeric code:

| Code | Meaning |
|---|---|
| 1 | Opened |
| 2 | Dismissed or handed to an original menu |
| 3 | Drawing unavailable |
| 4 | Focus/window/eligibility ownership released |
| 5 | Opened while originally paused |
| 6 | Exit confirmation opened |
| 7 | Original reset requested |
| 8 | Title state observed after reset |
| 9 | Reset rejected |
| 10 | Paused presentation recovery |
| 11 | Opened while originally running |

No continuous raw input or new diagnostic file is collected.

## Evidence boundaries

| Area | Status |
|---|---|
| Original controller source and profile preservation | VERIFIED by source pins and regressions |
| Runtime state, navigation, input filtering and recovery logic | VERIFIED with production-code API doubles |
| Retail/JPRE patch guards, keyboard seam, stack/register/flags | VERIFIED by x86 emulation |
| Layout bounds, mouse routing, GDI flush order | VERIFIED with production-code harnesses |
| Physical Raphnet selection and all controller behavior | NEEDS VALIDATION against this candidate |
| Actual F03 Windows flicker, title reset, audio/controller/display recovery | NEEDS VALIDATION |
| Exact state sequence that caused the reported F7 failure | UNKNOWN; no physical trace supplied |
| Configuration pages | Not implemented |

Automated results are not physical game acceptance.
