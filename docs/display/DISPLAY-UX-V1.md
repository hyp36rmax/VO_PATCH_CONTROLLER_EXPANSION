# DUX-V1.0 — display configuration contract

Recovered from the frozen project planning record; implemented incrementally.
F04 adds launch-time selection. F-key integration and Unified Overlay are deferred.

| Setting or condition | Contract |
|---|---|
| Fresh installation | Single Display; Widescreen (16:9) |
| One active monitor | Single Display; preserve any unavailable dual preference |
| Two or more active monitors | Offer Single, Dual — Versus, Dual — Mirror; do not auto-enable dual |
| Primary / secondary | Persistent stable display identities; reject duplicate/overlapping dual outputs |
| Game aspect | Explicit saved preference; never inferred from physical width alone |
| Presentation | Contain source aspect in each current desktop; no Windows mode change |
| Missing display/profile | Resolve a temporary compatible selection; retain requested values |
| Changes | Apply at next launch; no unvalidated live switching |
| Configuration authority | Existing `game/player-displays.ini`, consumed by shared resolution services |
| Controller configuration | Existing game/controller files; unchanged |

`[Players] Player1/Player2` retain the existing stable IDs. `[Presentation] Mode`
is 0 Single, 1 Versus, 2 Mirror; `GameAspect` is 0 Original, 1 Widescreen,
2 Ultrawide, 3 Super-ultrawide. These numeric values are implementation details.
Absent aspect defaults to Widescreen. Legacy explicit pairs migrate from the
existing MirrorPlayer1 setting; connecting extra monitors alone never selects dual.
Requested settings remain authoritative. The launcher's effective selection and
physical rectangle are session data, not another saved configuration authority.

| Phase | Display 1 | Display 2 |
|---|---|---|
| Startup / movie / main menu | Original presentation | Black |
| Local VS selection / pre-fight | Shared composition | Mirrored shared composition |
| Versus gameplay | P1 | P2 |
| Mirror gameplay | P1 | P1 |
| Return to menu | Original presentation | Black |

The existing F-key menus remain operational. Later integration must reuse this
configuration model; no second settings store or overlay implementation is added.
