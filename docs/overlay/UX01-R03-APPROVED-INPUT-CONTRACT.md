# Unified Overlay input contract — F03 revision

> Historical P01/F03 checkpoint. The placeholder-page limitations below were
> superseded by settings integration. See the [current implementation index](README.md)
> for later changes and separate physical acceptance requirements.

The UX01-P01-F02 acceptance brief supersedes P01's Start activation and native
Raphnet Pause-toggle exception. Configuration pages remain outside this milestone.

| Input | Approved behavior |
|---|---|
| ESC, eligible title/attract/gameplay | Open; Back from a placeholder page; close at root |
| Controller Start, overlay closed | Original game and Controller Expansion behavior |
| XInput/Tanita Start, overlay open | Original Pause/Resume; relinquish overlay before original F3 handler |
| Native Raphnet Start, overlay open | Existing menu confirmation only |
| Native Raphnet Pause | Original F3 behavior; never activates overlay |
| P1 left lever / existing menu directions | Navigate; use current F7 bindings and ownership |
| Existing menu accept | Select, including visible BACK and RESUME |
| Keyboard | Arrows and Enter; ESC uses a separate release/press gate |
| Mouse | Hover, click and scrolling where needed |
| P2 | Cannot change the overlay; original gameplay inputs remain available |
| F11 | Original Extras, with additive fallback overlay access |
| F10 | Unassigned |
| Other F-keys | Original functions retained |

Overlay availability is limited to verified non-video title, attract-demo and
offline match states. Movie ESC, confirmation and skip remain original. No
activation is queued across video playback. Opening and closing never call
GPAUSE or GRESUME; existing pause state remains under game authority.
Only a fresh confirmed EXIT TO TITLE may call original GRESUME, allowing the
original negative-mode reset tick to run. CANCEL returns to the overlay. The
five-button soft-reset shortcut is disabled; individual buttons are preserved.

Assignment and capture stay in the unchanged Controller Expansion helper.
Raphnet DC B3 and Saturn B8 remain Start. No new mappings, device discovery,
controller configuration or controller-to-ESC translation are introduced.
