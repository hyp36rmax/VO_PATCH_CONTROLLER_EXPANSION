# Unified Overlay foundation — private P01

P01 adds a main menu to offline gameplay. It does not replace the patcher,
legacy F-key menus, controller assignment, or configuration authorities.
Physical Windows acceptance is pending.

## Controls

| Input | Behavior |
|---|---|
| Assigned P1 Start | Pause and open; close and resume after release |
| Native Raphnet Pause / Start | Pause toggles; Start confirms |
| P1 left lever / existing directions | Navigate using the current F7 profile |
| Existing menu accept | Select |
| Keyboard | Arrows, Enter, Escape |
| Mouse | Hover, click, wheel when the list scrolls; visible Back and Resume |
| F11 Extras | Additive “Unified Overlay (gameplay)...” entry |
| F10 | Not enabled; Windows menu conflict validation remains pending |
| Existing F-keys | Original functions retained |

The existing shoulder/trigger soft-reset chord passes through unchanged.
Assignment takes priority over activation. Pending assignment presses are consumed
by the original helper; the overlay waits for assigned participants and a fresh
press. P2 cannot navigate the overlay. Keyboard and mouse remain available if P1
disconnects. Start, levers, buttons, and triggers must return to neutral before
controller navigation is armed. Back retains its existing game camera behavior;
no new hardware-specific Back binding is assigned.

CONTROLLERS, DISPLAY, GRAPHICS, GAME SETTINGS, and EXTRAS show an explicit
private-build unavailable notice. Back returns to the main menu; Resume closes.
Configuration pages are outside this milestone.

## Integration

The original `vontanita.dll`, its source, assignment dialogs, and capture logic
remain unchanged. A private `voinputux.dll` forwards the existing APIs and offers
returned, already-owned samples to `vooverlay.dll`. There is no second controller
polling loop. Directional bindings and deadzones are read from the existing F7
condition tables. Claimed input is withheld from gameplay only during the queued
open, open, and release-drain transaction.

A guarded `.vouo` section connects the existing message pump, game window
procedure, inactive rendering path, and pre-flip presentation seam. Every replaced
site is checked against known original or selected upstream patch bytes.
`GPAUSE(0)` and `GRESUME` retain pause authority; the overlay opens only after the
original inactive flag is set and its drawing surface is available. Supported
activation is limited to offline gameplay states accepted by the game's own
availability predicate. Unsupported states keep stock Start behavior.

DLL/export failure preserves the original pump and pause behavior. Drawing
failure or focus loss relinquishes UI input ownership. A drawing failure retains
stock pause for F3 recovery. Existing F-key dialogs relinquish overlay ownership
before their original handlers run; F3 sees the original paused state.

The paused frame uses the existing game rendering routine. The overlay draws a
bounded panel into its back surface; no new simulation clock or timer is created.
Single centers within the selected source profile. Versus confines the panel to
the P1 half. Complete Mirror presents the same composed image on both outputs.
Output-window mouse coordinates use the existing fitted source rectangles, and
Single mouse events pass through cnc-ddraw's original coordinate conversion.

## Configuration and diagnostics

P01 adds no configuration keys. Display settings remain in the established
`player-displays.ini` authority, and controller settings remain with the existing
F7 implementation. Future pages must use these same authorities.

Diagnostics remain Off by default. When enabled, the existing bounded local
`events.jsonl` sink accepts `overlay_lifecycle` with a numeric code only:

| Code | Event |
|---|---|
| 1 | Opened after pause verification |
| 2 | Resumed or handed back to a legacy menu |
| 3 | Initialization/drawing unavailable |
| 4 | Focus/window/pause ownership released |

No raw inputs, device identifiers, new log files, or automatic uploads are added.
Existing explicit export and retention rules apply.

## Evidence boundaries

| Area | Status |
|---|---|
| Controller helper preservation | VERIFIED by unchanged source/binary pins and baseline regressions |
| Menu state, input forwarding, original binding interpretation | VERIFIED by host tests executing production code with API doubles |
| Retail/JPRE hook identity and calling conventions | VERIFIED by x86 emulation |
| Layout bounds and output mouse routing | VERIFIED by production-code harnesses |
| Pause/render/focus behavior on Windows | NEEDS VALIDATION |
| Readability and actual mouse alignment on physical displays | NEEDS VALIDATION |
| F10 coexistence with Windows menu activation | NEEDS VALIDATION; not implemented |
| Configuration pages | Intentionally not implemented |

Host and emulation results are not physical game acceptance. Use only the
consolidated private UAT package for the next Windows run.
