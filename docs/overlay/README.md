# Unified Overlay implementation and history

Unified-Overlay-Menu-Expansion is the active development branch. It is separate
from the Controllers + Display Expansion prerelease on Experience. Source
inspection establishes implementation, not physical Windows acceptance.

## Current implementation

| Area | Evidence at `a824e30f160f3c9949647265669c54682c5b911c` | Status |
|---|---|---|
| Settings pages | [pages.c](../../tools/unified_overlay/pages.c) contains Controllers, Display, Graphics, Game Settings and Extras, with conditional profile editors and confirmation pages | VERIFIED by source inspection |
| Controller profiles | [controller_settings.c](../../tools/unified_overlay/controller_settings.c) validates both pending profiles before saving; assignment uses the existing input path | VERIFIED by source inspection |
| Original settings | [native_settings.c](../../tools/unified_overlay/native_settings.c) adapts original graphics and game settings; edited game-setting fields merge into a fresh snapshot | VERIFIED by source inspection |
| Display persistence | Display Apply calls the existing display bridge and reports next-launch activation; Local VS split uses the original settings adapter | VERIFIED by source inspection |
| Input ownership | [runtime.c](../../tools/unified_overlay/runtime.c) and [input_bridge.c](../../tools/unified_overlay/input_bridge.c) connect activation, navigation and assignment; original F-key access remains available | VERIFIED by source inspection |
| Paused composition | [paused.c](../../tools/unified_overlay/paused.c) contains the later paused-frame implementation; the original flicker investigation remains in the foundation record | VERIFIED by source inspection; physical acceptance NEEDS VALIDATION |
| Full interface parity and hardware acceptance | Source inspection alone cannot establish complete Windows acceptance for this commit | NEEDS VALIDATION |

The [frozen R04 layouts](UX01-R04-APPROVED-LAYOUTS.md) specify the intended
interface. They are not a completion certificate. The implementation resolves
R04's provisional graphics texture labels to Machine(1P), Machine(2P) and Effects.
Display mode and aspect selection use the existing display configuration authority;
no independent overlay display format is introduced.

## Engineering evolution

| Checkpoint | Finding or change |
|---|---|
| Older Unified-Overlay, `e4a2a501dd0f6dd5ca4cf5ac843875199c07662a` | Preserved ancestor of the active branch; no obsolete implementation needs to be merged again |
| `da551d2` | Activation, navigation and rendering synchronization corrections |
| `06b261f` | Paused presentation correction and Exit to Title integration |
| `c7a0996` | Settings integration and the frozen R04 interface record |
| `59e3ce1` | Direct settings actions and controller assignment integration |
| `a824e30` | Controller profile selection and assignment input routing corrections |

The [P01 foundation](UX01-P01-FOUNDATION.md) preserves the failed and corrected
rendering approaches, input suppression, state eligibility and reset findings.
Its unavailable configuration pages describe that checkpoint only. The
[F03 input contract](UX01-R03-APPROVED-INPUT-CONTRACT.md) records the change from
Start activation to ESC while preserving original controller Start behavior.
Later configuration integration does not erase that decision or its evidence.

Physical F02 testing confirmed active-gameplay presentation without flicker.
That result does not certify later paused composition, settings persistence,
controller assignment or all R04 pages. These require exact-build Windows
validation, including original F-key recovery and cancellation of pending edits.
