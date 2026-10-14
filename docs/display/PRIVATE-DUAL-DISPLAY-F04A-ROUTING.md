# F04A Local VS routing recovery

Baseline: `221e5ccd843a27c6b3263387270a89a2108ec80f`.

## Findings

**VERIFIED:** explicit dual UAT previously rejected a missing secondary monitor,
contrary to the clarified recovery contract. The new launch resolver uses the
existing mode/profile selector to recover before executable selection. It reports
requested/effective modes and reason flags. The temporary configuration contains
the effective mode; saved mode, aspect and monitor identities remain intact.
The launcher accepts a mode mismatch only for a reported unavailable-dual-to-Single
transition. The game starts the selected Single executable with dual output off.

**UNKNOWN:** root cause of the reported physical P1 duplication. Current internal
routing tests produce P1/P2 for Versus and P1/P1 only for Mirror. Single bypasses
the dual presentation path. No returned runtime evidence accompanying this brief
establishes the selected mode, producer phase or sampled source at the failure.
Do not claim that the physical duplication is fixed by the recovery change.

## Preserved behavior

All game profiles, movie assets/geometry, state classifier, camera ownership,
controller code and wrapper binary are unchanged. Original horizontal/vertical
Local VS layouts remain in the Single images. The dual image retains its fixed
independent halves; only explicit Mirror chooses the first half twice.
Single aspect selection remains independent of physical output size.

Dual failure after initialization requests ordinary closure rather than continuing
a dual framebuffer as a claimed Single recovery. Recovery is resolved on the next
launch; runtime profile switching is not introduced. This now applies to saved
launches as well as explicit UAT sessions.

## Verification boundaries

The mode/aspect/monitor test matrix covers prelaunch fallback, immutable saved
preferences, mixed displays, phase transitions and source ownership. Existing
strict resolver tests remain unchanged; the new launch resolver composes strict
selection with reported recovery. Existing baseline and presentation tests remain.
Executable identity proves no renderer/controller/gameplay patch was introduced;
it does not demonstrate physical camera output or independent hardware input.

Windows acceptance remains **NEEDS VALIDATION**, including original split-screen,
Versus, Mirror, missing-secondary recovery, controls, movie, focus and shutdown.
This is a safe recovery candidate, not a confirmed P1-duplication correction.
