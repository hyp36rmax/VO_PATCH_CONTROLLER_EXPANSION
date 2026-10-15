# UX01-R03 — Approved Input Contract

Authority: project owner's UX01-P01 clarification. This records the approved
interaction contract; it does not claim implementation or physical validation.

| Input | Approved behavior |
|---|---|
| Controller Start | Primary overlay activation during gameplay |
| Start during P1/P2 assignment | Preserve deterministic controller selection |
| Start while overlay is open | Close overlay and resume, where supported |
| Left Twin-Stick lever | Navigate menu |
| Existing menu accept | Confirm selection |
| Mouse | Full navigation, selection, and scrolling |
| Keyboard | Arrow keys, Enter, Escape |
| F10 | Secondary shortcut, pending conflict validation |
| F11 | Fallback access |
| Original F-key menus | Preserved |

One press performs one action. Assignment precedes stock menu handling, which
precedes supported gameplay activation. Input must be released before overlay
navigation is armed. P1 owns controller navigation; keyboard and mouse remain
available. Existing F7 profiles and assignment are authoritative.

## Approved native Raphnet exception

**VERIFIED:** `asm/raphnet.asm:pollkeys` maps native `VON_START` to the stock
accept/skip key (Space), while `VON_PAUSE` maps to F3. The native input tick also
uses `VON_START` for the menu accept slot. Consequently, making Start always
close an open overlay also consumes the existing confirm control for these
profiles. A new trigger mapping cannot be inferred from this contract.

**Approved exception:** for native Raphnet profiles, physical Pause toggles the
overlay and physical Start confirms. This retains their existing separate
accept/pause semantics. Other profiles retain Start-to-toggle.
