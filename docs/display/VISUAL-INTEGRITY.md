# Private visual integrity probe — D02-V01

The probe supplies bounded static geometry diagnostics to the existing UAT collection path. It does **not** detect live clipping. The user reports S05 1920 startup and 2560 startup/gameplay PASS, initial HUD/camera PASS, and clipping observed at an unknown location. DirectDraw initialization logs do not establish its cause. Measured latency and pacing remain unknown.

## Implemented evidence

`tools/visualprobe.py` is opt-in diagnostic tooling, not a renderer modification. Static reports validate mask meaningful bytes against pitch, A/B viewport-origin addresses against mask/table separation, active canvas and photo-stage ranges, and HUD/viewport containment. Existing D01/S02/S03/S04 tests additionally verify actual generated instructions, rasterizer span execution, projection, relocations, photo sampling and guarded canvas rows. Static snapshots include resolution, viewport, mask/canvas layout and source attribution; no frame or object IDs are fabricated.

Event vocabulary: MASK_BOUNDS, VIEWPORT_BOUNDS, CANVAS_BOUNDS, HUD_BOUNDS, OBJECT_CULLING and RASTERIZER_CLIPPING. Bounds use half-open intervals/rectangles. An out-of-range geometry or memory-access assertion is CONFIRMED_VIOLATION **of that evidence**, not proof of a live defect. A declared ordinary clipping operation is EXPECTED_CLIPPING; unexplained clipping is POTENTIAL_ANOMALY. Missing/malformed bounds or an unexplained object rejection are INSUFFICIENT_EVIDENCE. Valid bounds produce no anomaly event. Every event states STATIC or RUNTIME; no implemented adapter currently produces RUNTIME renderer events. A caller-provided label is not independently verified provenance.

The disabled default records nothing. Enabled storage defaults to 64 events, with a hard capacity limit of 256, bounded source text and integer fields, and a saturating drop count. Serialization occurs outside gameplay. This is a diagnostic Python component, not an allocation-free hot-path logger.

## Runtime observability inventory

Locations are existing source/retail references, not universal addresses; JPRE needs its verified translation. No new live observation hook is enabled.

| Signal / location | Available data | Risk / overhead | Validation method / disposition |
|---|---|---|---|
| Camera/projection: ui.asm `world_a`, `world_b`, `world_state`; D_SAVE_A, projection globals | Saved projection values; not complete camera pose or stable object IDs | Cross-thread/process reads can combine different frame states; debugger pauses on every hit | Inspect translated sites and compare known snapshots in future; complete camera telemetry UNKNOWN |
| Projected bounds: ui.asm `extents`, `rescale`, insert hooks | Temporary polygon min/max and HUD pass context | Per-polygon traps stall render thread; pointer lifetime ends quickly | Existing x86 fixtures validate math; live trapping UNSUITABLE for non-blocking requirement |
| Frustum/object culling: docs/HIRES.md enemy-marker and projection discussion | Marker threshold is known; full object rejection reason/identity is not established | Guessing from rejected submissions misclassifies ordinary culling | Object-level signal UNKNOWN / NOT OBSERVABLE with current verified instrumentation |
| Polygon clipping: retail quad-submit 0x5d79a0 and existing lockline/submit paths | Local clip/submit geometry; not a verified complete clipping decision stream | Multiple renderer paths, dynamic data; no proven low-overhead interception | Requires mapped instruction/lifetime audit first; deferred |
| Rasterizer submission: ui.asm `submit_a`, `submit_b`, insert/rescale paths | Pass ownership and polygon data at entry | High-frequency tracing pauses; no bounded non-blocking adapter verified | Existing emulator tests only; live capture deferred |
| Mask writes: v-on-patcher.py MASK_PACK/MASK_ADVANCE; tools/d01test.py span execution | Verified stride instructions, mask origins, row-pointer layout | Four x86 hardware slots cannot cover all spans; guard pages or instrumentation change execution/timing | Static/generated instruction and x86 bounds tests VERIFIED; live violations NOT OBSERVABLE without new validated mechanism |
| HUD: ui.asm `pre_spread`, `spread_row`, `rescale` | Composition scale/origin, pass gates, temporary vertices | Sampling can catch partial updates; off-screen intermediate vertices are not necessarily defects | Static contract and existing HUD emulator tests VERIFIED; live coherent snapshot deferred |
| Canvas: ui.asm `fit`, `pre`, `post`, `margins_photo`; D_OFF/D_STAGE/D_COPY | Region ownership and copy/sampling loop bounds | Watchpoints miss general writes; full-frame comparison/copy violates scope | Static report plus existing source-bound/canary tests VERIFIED; live overwrite detection deferred |
| DirectDraw startup: existing external observer call/return sites | Requested mode, HRESULT, module and lifecycle | Debugger suspends at each event; acceptable prior startup diagnostic, not non-blocking renderer telemetry | Preserve existing observer unchanged; initialization only, not clipping evidence |

No verified observation point currently satisfies coherent, non-blocking live renderer evidence without a new timing-sensitive mechanism. Unsynchronized ReadProcessMemory samples would be potential anomalies at best and cannot safely confirm a boundary violation. Guard-page exceptions, per-polygon hardware breakpoints, intrusive trampolines and continuous screenshots are unsuitable here. They are not enabled merely to satisfy a telemetry checklist.

## UAT integration

`visualprobe_uat.py SOURCE DESTINATION --diagnostic` requires a new independent destination. It copies the known S05 package, generates four VISUAL-INTEGRITY.json static reports and extends the existing collector's explicit file list. The original UAT files remain unchanged. It regenerates the diagnostic manifest and leaves all game/observer/helper/DLL/INI bytes untouched. No Windows Python installation is required: reports are generated during preparation. Normal builds never call this tool.

The private integration staging tree demonstrates collection wiring only; it is not a new physical-test request. Windows execution of the extended collector remains NEEDS VALIDATION. No clipping correction, new mode, display startup change, controller change, queue, buffer, copy or synchronization is added to gameplay. Runtime renderer overhead from this probe is zero because no live adapter runs; preparation/collection has filesystem and serialization cost outside the render loop. Existing observer overhead remains unchanged.

## Next scope, not started

D02-V02 should first localize the clipping to a scene/state and distinguish authored crop, expected viewport clipping and anomalous missing geometry. Review existing evidence or a later separately authorized consolidated UAT capture. Only then select a specific mapped observation point and prove coherent bounded overhead before enabling it. Object IDs, frames and culling causes remain UNKNOWN until established. Do not infer them from startup logs or static PASS results.
