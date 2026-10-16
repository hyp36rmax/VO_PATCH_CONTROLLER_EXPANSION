# F04 display configuration storage

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

The authoritative design is [DUX-V1.0](DUX-V1.0.md). This document describes the
current F04 implementation, not additional frozen requirements.

The existing `game/player-displays.ini` is the single display configuration
store. Controller and game configuration remain in their existing files.

| Section / key | Meaning |
|---|---|
| Players / Player1 | Primary display stable identity |
| Players / Player2 | Secondary display stable identity |
| Presentation / Mode | 0 Single, 1 Versus, 2 Mirror |
| Presentation / GameAspect | 0 Original, 1 Widescreen, 2 Ultrawide, 3 Super-ultrawide |

Absent aspect defaults to Widescreen. Legacy explicit display pairs migrate
from the existing MirrorPlayer1 setting; connecting extra monitors alone never
selects dual. Requested settings remain authoritative during temporary fallback.
The launcher's effective selection and physical rectangle are session data,
not another saved configuration authority.

F04 exposes a private launch-time selector for Windows acceptance. Existing
F-key menus remain operational; integrating the expanded display settings into
them is deferred. Future interfaces must reuse the same configuration services.

See the [F04 implementation and validation record](PRIVATE-DUAL-DISPLAY-P05-F04.md)
for profile limitations and physical acceptance status.
