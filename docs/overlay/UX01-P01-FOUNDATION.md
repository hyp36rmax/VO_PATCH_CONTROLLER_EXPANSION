# Unified Overlay foundation — private P01-F02

The six-entry menu adds optional access during verified title, attract-demo and
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
original reset chord retain their destinations. Native Start is consumed solely
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
rendering path and pre-flip seam. The existing frame renderer draws while already
paused; no simulation clock, overlay window or separate display system is added.

GDI drawing is explicitly flushed before releasing the composed surface. The
pinned wrapper's ReleaseDC does not flush GDI's per-thread batch; the flush closes
that CPU-drawing/publication race. The regression models delayed drawing and
rejects an unflushed surface. Physical confirmation that this eliminates the
reported flicker remains pending.

Single centers the bounded panel in the selected source aspect; Versus confines
it to P1; Complete Mirror presents the same composed image on both displays.
Text scales uniformly. Mouse mapping retains the existing output/source fit.
Cursor visibility increments are balanced on dismissal and recovery.

Focus loss, unavailable drawing surfaces, movie entry and legacy F-key access
release overlay ownership. No focus stealing, window recreation, forced resume,
movie lifecycle change or automatic reopening is introduced. Keyboard and mouse
remain usable if P1 disconnects. Display fallback remains unchanged.

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

No continuous raw input or new diagnostic file is collected.

## Evidence boundaries

| Area | Status |
|---|---|
| Original controller source and profile preservation | VERIFIED by source pins and regressions |
| Runtime state, navigation, input filtering and recovery logic | VERIFIED with production-code API doubles |
| Retail/JPRE patch guards, keyboard seam, stack/register/flags | VERIFIED by x86 emulation |
| Layout bounds, mouse routing, GDI flush order | VERIFIED with production-code harnesses |
| Physical Raphnet selection and all controller behavior | NEEDS VALIDATION against this candidate |
| Actual Windows flicker, focus, cursor and multi-monitor presentation | NEEDS VALIDATION |
| Exact state sequence that caused the reported F7 failure | UNKNOWN; no physical trace supplied |
| Configuration pages | Not implemented |

Automated results are not physical game acceptance.
