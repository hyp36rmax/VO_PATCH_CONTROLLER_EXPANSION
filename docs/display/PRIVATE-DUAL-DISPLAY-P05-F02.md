# D04-P05-F02 — desktop compatibility and shared composition

Status: **VERIFIED internally; NEEDS VALIDATION on Windows**. Private only.
Baseline: `09ff7f8aa74284820e6de88a5b56e6b0bef4217c` (F01, physically validated
by the owner). Pinned cnc-ddraw: `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.

## Geometry contract

The game allocates 3840×1080×16. That is an internal surface, not a physical
monitor requirement. Native discovery supplies each monitor's current desktop
size, coordinates, refresh, primary flag and stable identity. Existing assignment
storage, window focus/lifecycle and controller ownership remain unchanged.

| State | Source 1 | Source 2 |
|---|---|---|
| Primary only | Recomputed shared 1920×1080 at (0,0) | Black |
| Local VS selection | Same shared source | Same shared source |
| Local VS gameplay | (0,0,1920,1080) | (1920,0,1920,1080), optionally P1 |
| Invalid/unknown/unsupported | Full 3840×1080 fallback | Same full fallback |

Each source is contained and centered independently at the assigned desktop
size. Letterbox/pillarbox bars are cleared; source proportions are preserved.
The backend retains one uploaded texture generation and sequential presents.
Different refresh rates are allowed; scanout synchronization and latency are
not measured or guaranteed.

## Isolated shared-image correction

The old 3840-wide shared canvas placed its approximately 3838-pixel background
across the full source. Extracting its center would discard artwork. The new
private generator instead reuses the original non-split viewport setup with the
same width operands as upstream 1920. The existing UI compositor then computes
its canvas, photo fit and HUD placement from that viewport. No separate aspect
control, new renderer, or output stretching is introduced.

| Retail file operand | F01 value | F02 value | Use |
|---|---:|---:|---|
| `0x1c7da5` | 3840 | 1920 | Full non-split viewport width |
| `0x1c7d77` | 3840 | 1920 | Normal/inset horizontal extent |
| `0x1c7d68` | 2976 | 1488 | Normal/inset viewport width |

JPRE uses the existing verified port map. Only these three operands and their
three primary-mode F4 table values change. Alternate F4 values, split branches,
pitch, masks, allocation, renderer code and controller code are unchanged.
Normal/inset and full layouts retain upstream behavior; 4:3 artwork/HUD remains
inside the upstream 1920 composition. The original 1920/2560/3840 generators
and F01 control executable remain byte-identical.

The read-only state bridge now identifies the corrected viewport instruction
rather than the old frame shim. An F01 executable cannot be mistaken for the new
shared layout. Flip-boundary capture, locking, generation association and unknown
fallback are unchanged. The external observer changes only its two expected
SHA-256 literals and is rebuilt for the new dual executable.

## Current desktop preservation

Pinned cnc-ddraw normally calls `ChangeDisplaySettings(NULL,0)` before reading
the initial desktop mode. That can reset a current mode to registry defaults.
The private build skips this one reset when windowed and `VO_DUAL_DISPLAY=1`;
all other wrapper users retain the pinned behavior. It then reads the current
mode through the existing query. Output swapchains remain windowed and use each
monitor's desktop dimensions. No custom mode, EDID change or elevation is used.
The existing borderless configuration and focus/close paths are retained.

## Evidence boundaries

| Check | Result |
|---|---|
| F01 physical evidence | Owner validated; returned log includes primary/shared/gameplay and matched P1/P2 generations on 2560×1440 + 1920×1080 |
| Retail/JPRE viewport and actual UI canvas | Shared matches upstream 1920; gameplay matches F01 in the bounded emulation matrix |
| Generated-byte isolation | Only the six documented operands differ from the dedicated VS image |
| Original renderer flush isolation | Synthetic solid/textured quads/triangles remain within their player halves |
| Physical output geometry | Host tests cover mixed sizes/aspects, negative/vertical positions and bounds |
| Desktop mode preservation | Actual query block executed with API doubles, including failed-query fallback |
| Lifecycle/focus/faults | Production presentation code tested with host API doubles |
| Native F02 execution, complete visuals, physical inputs | NEEDS VALIDATION |

## Private delivery

Extract `D04-P05-F02-PRIVATE-UAT.zip`, run `START-DUAL-DISPLAY.cmd`, choose outputs
and complete the enclosed consolidated checks. `START-LOCAL-VS-CONTROL.cmd`
retains the original D03-P04 comparison. Return the automatically collected
`RETURN-THIS-D04-P05-F02.zip` and observations; raw logs remain if compression
fails. No manual file copying, INI edits, commands or administrator rights.

Validate shared composition and transitions, independent gameplay, mixed
outputs, original controls, Mirror P1, return to menu, focus and shutdown.
F02 physical acceptance is the next gate; no further feature milestone begins
before that evidence is reviewed. No public branch or release is changed.
