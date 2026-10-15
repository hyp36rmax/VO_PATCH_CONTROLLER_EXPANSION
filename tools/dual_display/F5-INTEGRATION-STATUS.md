# F01-P04 private integration status

**Automated integration validated; physical Windows acceptance pending.** The
private distribution uses Pairomaniac's existing Windows patcher and Apply/Restore
workflow. It requires original Retail or Japanese rerelease files. Public patcher
source, Controller Expansion and other branches are unchanged.

## Installation and activation

`tools/experience/build_catalog.py` generates 512 sparse patch recipes: every
combination of the eight optional upstream options for both supported editions.
The distribution adapter verifies original and upstream-patched SHA-256 identities,
reconstructs the integrated image, verifies its final hash and installs its runtime.
Failures roll back affected files. Restore uses upstream backups and restores
previous runtime files; unrelated or user-modified files are preserved. Display
preferences and diagnostic output remain user data.

Normal `v_on.exe` startup selects the saved profile before the retained game entry.
The bounded, CRC-checked activation plan verifies expected bytes, excludes
loader-owned memory, restores page protections and flushes the instruction cache.
It does not replace a running executable. Wrapper identities are generated from
these exact option images; timestamp, image size and code-signature checks remain.

## Configuration

F5 retains the original controls and adds Display. The child dialog uses existing
`player-displays.ini` preferences, transactional OK and non-writing Cancel. Mode,
monitor assignment and aspect changes apply next launch. Process-local presentation
parameters freeze the effective selection for that launch. No second persisted
configuration authority is introduced.

Fresh default installation is Single Display, 16:9. Explicitly disabling upstream
high resolution defaults to Original 4:3 until a saved Display selection overrides
it. Missing monitors use the existing safe fallback without overwriting preferences.
Single Display keeps original Local VS split behavior. Dual Versus separates the
views; Dual Mirror mirrors complete primary presentation, including Local VS.

Both F4 and the startup INI resolution path enforce the same safe-hold policy in
dual mode. Single mode retains original resolution transitions. Dual low-resolution
switching is not claimed. The original split preference is preserved separately
from the effective dedicated-VS composition.

## Diagnostics and evidence boundaries

The passive collector starts before game entry and acknowledges readiness after
opening the game process and recording startup evidence. It never launches the
game. It waits for process exit, records shutdown and exports the bounded local
return archive. On-demand export is also installed. Compression failures preserve
raw logs and leave an obvious return note. No uploads occur. Controller discovery
records metadata, not raw input; it does not establish physical controller behavior.

Internal tests cover all 33 baseline regressions, both-edition patch generation,
Apply/Restore/reapply and failure rollback, startup ABI/protection failures, F4/F5
and split contracts, presentation/movie policies, diagnostic lifecycle and package
integrity. Native API doubles and emulation are not physical Windows acceptance.
Normal startup, actual dialog rendering, monitor transitions, controller input,
movie presentation and process cleanup require the consolidated Windows UAT run.

No push, release, Unified Overlay changes or desktop configuration changes are
part of this milestone.
