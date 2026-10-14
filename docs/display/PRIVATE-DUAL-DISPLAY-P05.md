# D04-P05 three-phase dual-display presentation

Implementation and host validation: **VERIFIED**. Physical Windows acceptance:
**NEEDS VALIDATION**. Starting private HEAD:
`1d0147f46b3d24e13f0d0583a6347271f6cc4d51`.

The prior P03 independent-output implementation is physically validated according
to the maintainer's report. Its game executable and control package remain intact.
P04 established that the centered HUD rectangle is not the shared content boundary;
P05 presents the complete 3840×1080 frame instead of changing producer geometry.

## State and frame ownership

The read-only bridge consumes the original loop mode, P1 mode, split flag and
existing `frame_setup` result (`D_SHOW`). Retail addresses are `0x6bc94c`,
`0x1ae3594`, `0x6bc948`, and private UI section + `0x1e88`; the JPRE equivalents
are generated from the existing verified port map. The executable base, timestamp,
image size and 32-byte private frame-entry signature must match before dereference.
The launcher additionally verifies the full packaged executable hash.

| Original producer state | Output policy |
|---|---|
| Loop not local two-player, or mode not match/selection (4) | Primary only |
| Local loop 1, mode 4, split enabled, `D_SHOW` 1 or 2 | Local VS shared |
| Same local state with `D_SHOW` 0 | Local VS gameplay |
| Unsupported identity | P03 independent routing; no mirror override |
| Unrecognized field range or inconsistent local split state | Retain last verified policy and record the unknown fields |

The original loop-mode definition is documented in `docs/MAP.md`. Original Retail
`0x56673d` sets loop 0/1/2 for single/local/network; the selection path at
`0x44b600` invokes the local switch and sets split. Existing `asm/ui.asm` and
`docs/HIRES.md` establish mode 4 shared selection/pre-fight and per-frame round
selection. P05 consumes that producer decision rather than reproducing its
substate list. Exact visible transition timing and every exit path still require
Windows acceptance; static inspection is not a claim of physical success.

The wrapper captures policy on primary-surface Unlock while the producer still
owns the surface lock, before publishing the update. The existing renderer copies
that policy during successful texture upload under the same surface lock. Rendering
uses the uploaded texture's retained policy, not later live game state. Unknown
states are counted; last unknown loop/mode/split/show values are reported at exit.

## Composition and gameplay option

Primary-only and shared phases use `(0,0,3840,1080)` without crop. Primary-only
clears the secondary swapchain to black. Shared mirrors the full source. The two
output windows initialize with the existing first completed-frame path; the
wrapper does not disable a monitor or change the desktop during game startup.

Gameplay retains P1 `(0,0,1920,1080)` and P2 `(1920,0,1920,1080)`. The existing
assignment UI now saves **Secondary gameplay display: Player 2 / Mirror Player 1**
under `[Presentation] MirrorPlayer1`, default 0. Mirror changes only the secondary
source rectangle during gameplay. P2 simulation, cameras and input continue.

Aspect containment operates separately for both sources and monitor geometries.
A full 32:9 shared source has letterboxing on a 16:9 monitor. This preserves the
existing rendered composition and adds no new artwork distortion or cropping;
it does not undo any original game's authored crop. No camera/projection change,
new aspect controls or generated-game-image change is made.

## Validation and limits

- Existing 33-check Retail/JPRE suite reports pass; the CI-only tree check skips.
  Host GUI tests do not establish Windows execution.
- Existing 7128 producer transitions per edition and 192 bounded renderer flush
  cases pass. Their synthetic scope is unchanged.
- All six single-player Retail/JPRE 1920/2560/3840 images retain P03 hashes.
- Existing 64 mixed-geometry pairs and presentation lifecycle/fault tests pass.
- New production-code tests cover phase transitions, full shared UVs/source,
  secondary black, Mirror P1, retained texture policy, mixed aspects, unknown-state
  holding and executable-signature rejection. Graphics faults are injected in
  each phase. These use API doubles, not a Windows GPU.
- Package checks cover identity/address signature, capture/upload lock ordering,
  byte-identical control/game/helper, i386 imports, relocation with spaces/Unicode,
  ZIP CRC/hashes, unchanged launcher and preserved collector failure behavior.

Both outputs draw the same generation before sequential presents. No scanout
synchronization, zero-latency or cross-adapter performance claim is made. P03 focus,
window stacking, shutdown, display-change fallback and controller code are retained.

Movie visibility remains **UNKNOWN / NEEDS VALIDATION**: the maintainer reports
working audio and skip but no picture. No decoder or separate video path is changed.
A movie that bypasses the completed primary surface remains outside this routing.

## Consolidated acceptance

Use the single D04-P05 private package. Verify primary-only startup/menu and black
secondary; mirrored Local VS selection/pre-fight; independent gameplay; return to
shared/menu; then relaunch with Mirror Player 1 and verify persistence, continued
P2 control, mixed-display proportions, focus/minimize/restore and clean closure.
Return `RETURN-THIS-D04-P05.zip` and observations. The raw return folder survives
compression failure. The unchanged local-VS control is included for comparison.

The next milestone is physical D04-P05 acceptance and narrowly scoped corrections
for confirmed defects. No public push, release, main/Controller-Expansion changes,
Unified Overlay or spectator camera work is included.
