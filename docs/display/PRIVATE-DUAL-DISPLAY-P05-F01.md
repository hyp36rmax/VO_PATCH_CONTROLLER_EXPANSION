# D04-P05-F01 state capture correction

**VERIFIED:** missing Flip capture, deterministic reproduction, targeted correction
and host regressions. **NEEDS VALIDATION:** corrected Windows presentation.
Starting HEAD: `13c402c7e513bd948ff05b6a54f2470a271eeb70`.

## Physical evidence and root cause

The returned P05 archive matches the committed candidate and its packaged game,
wrapper and controller-helper hashes. It records two render lifetimes of 341 and
4306 presented pairs. Every pair used primary-only; errors were zero. The
maintainer reports combined gameplay on Display 1 and black Display 2.

P05 captured state only when the unlocked surface equaled `g_ddraw.primary`.
The original game renders into a distinct attached backbuffer, unlocks it, then
calls primary Flip. P05 had no Flip capture. Consequently those completed game
frames could never refresh its state snapshot. An initial or earlier primary-only
sample remained in use while the renderer successfully uploaded new pixels.

The log's `last_unknown_*` fields are not last observed state values. With zero
unknown samples, their zeros are default storage, not evidence of successful reads.
P05 did not log capture counts, so its physical log cannot distinguish no capture
from an early primary capture that was never updated. Both share the verified
missing-Flip defect. The exact committed P05 bridge reproduces the no-capture case
with a deterministic event fixture derived from the original dispatcher.

## Edition verification

| Source | Retail VA | JPRE VA |
|---|---:|---:|
| Backbuffer interface variable | `0x1ae5f5c` | `0x1ae0c18` |
| Primary interface variable | `0x1ae5f40` | `0x1ae0c34` |
| Original render driver | `0x5c80df` | `0x5c29ae` |
| Primary Flip call | `0x5c650d` | `0x5c0ddc` |
| Loop mode | `0x6bc94c` | `0x6b86ac` |
| P1 mode | `0x1ae3594` | `0x1adcdf0` |
| Split flag | `0x6bc948` | `0x6b86a8` |
| Private producer D_SHOW | `0x36bbe88` | `0x36b5e88` |

Module base is `0x400000`; subtract it for RVAs, also recorded at runtime. The
existing address tables regenerate byte-for-byte from both verified images.
Original instructions prove GetAttachedSurface supplies the distinct backbuffer,
its render driver calls Lock/Unlock, then the dispatcher calls primary Flip with
no intervening function call. This reuses the D03-R02/R03 findings.

The loop/mode/split semantics and producer `D_SHOW` are unchanged. Mode 4 covers
match selection and play; `D_SHOW` chooses shared versus split using the existing
round predicate. F01 does not add a competing substate table. Exact visible entry,
completion and return timing remain physical acceptance gates.

## Correction and observation validity

The isolated wrapper build adds capture inside `dds_Flip`, after exchanging the
primary/backbuffer storage and before releasing `g_ddraw.cs`. Texture upload reads
that policy under the same global lock, preserving pixel-generation ownership.
Direct primary Unlock still captures under the global lock for that alternate
path. No game instruction, camera, controller, renderer ordering or frame buffer
allocation changes. The pinned wrapper revision remains unchanged.

Identity validation uses safe bounded self-process reads for DOS/PE headers,
base/timestamp/image size and the expected private frame-entry signature. Each
state field is read separately with a validity bit. Failed reads cannot become
zero-valued successful samples. The initial policy is UNKNOWN.

| Observation | Classification / handling |
|---|---|
| Valid local loop 1, mode 4, split 1, D_SHOW 0 | Independent gameplay, optional Mirror P1 |
| Same local state with D_SHOW 1/2 | Shared mirroring |
| Valid supported non-local/non-match state | Primary-only |
| All four readable fields zero | UNINITIALIZED; full-frame fallback |
| Missing field read | INVALID_READ; full-frame fallback |
| Identity mismatch | UNSUPPORTED_EXECUTABLE; full-frame fallback |
| Unsupported/inconsistent field values | UNKNOWN_STATE; full-frame fallback |
| No producer capture yet | UNINITIALIZED/UNKNOWN; full-frame fallback |

Fallback mirrors the complete 3840×1080 frame, ignoring the gameplay mirror option;
it does not force independent gameplay in menus or claim successful detection.
A later valid capture restores normal classification. Unsupported identity stays
in fallback for that process lifetime. Invalid reads after identity succeeds are
retried at subsequent publication boundaries.

Diagnostics retain raw fields and read masks, identity and RVAs, Flip/Unlock counts,
classification, status/reason, phase totals, source/destination rectangles, window
presence/visibility and graphics HRESULT. A fixed 64-entry transition array logs
at most the first 64 transitions and reports total transitions. Logging occurs at
render-thread teardown under the global lock, with no per-frame disk writes.

## Validation and delivery

The exact old bridge reproduces the missed-callback failure. Production bridge
API-double tests cover initial UNKNOWN, valid phase transitions, partial failed
reads, identity rejection, uninitialized zeros, recovery through Flip and bounded
trace overflow. These fixtures are not claimed as observed Windows state samples.
Original Retail/JPRE dispatcher verification and regenerated identity tables pass.

Existing P03 routing/focus/lifecycle and 28 graphics-failure cases pass, as do
three-phase/Mirror P1, 64 mixed geometry pairs, source containment and generation
retention tests. The 33-check project suite, existing producer transitions and
bounded original renderer isolation pass. Existing game/helper images are retained;
package validation checks hashes, i386 imports, relocation and collection behavior.
No test assertion was removed to make unsupported observations appear valid; the
old UNKNOWN-gameplay expectation is replaced by the required full-shared fallback.

Use the single F01 private UAT ZIP and its included checklist. Return
`RETURN-THIS-D04-P05-F01.zip`, or the raw folder if compression fails. Verify
startup/black secondary, Local VS selection/pre-fight mirroring, independent
play, Mirror P1, return-to-menu, mixed displays, controller ownership and exit.
Movie visibility remains the known non-blocking limitation; no decoder changed.

The next milestone is this consolidated physical acceptance run. Nothing is pushed
or published; main, public Controller-Expansion and Unified Overlay remain untouched.
