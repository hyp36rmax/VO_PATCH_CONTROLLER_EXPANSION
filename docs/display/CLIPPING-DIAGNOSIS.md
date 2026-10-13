# D02-V02 — visual clipping investigation

**Outcome C: ROOT CAUSE UNRESOLVED.** The user observed clipping during S05 2560 gameplay, but its location, affected object/layer, camera state and reproducibility are unknown. No rendering correction is justified. This audit preserves the implementation and narrows specific hypotheses without claiming to reproduce the physical defect.

## Evidence inventory

The accessible display outputs and review folder contain one distinct gameplay image, `Virtual On 2560x1080P (2026-10-13_13-46-03).jpg`, also preserved in S04 evidence. It is 2559×1439, showing a READY moment, a central player machine, a raised structure/ramps over water, centered HUD and black top/bottom presentation bands. Camera parameters, stage identity and exact frame are not established. The image does not clearly identify the reported clipping. No coordinates or missing-object designation can be assigned reliably.

No 1920 gameplay screenshot, matched-scene pair or video was found in those evidence locations. Wrapper project flag icons are not gameplay evidence. The screenshot filename and proportions are consistent with the accepted 2560 presentation, but are not an exact framebuffer dump. It cannot establish temporal popping or compare culling across camera angles.

S04's preserved wrapped logs record 1920/2560 successful DirectDraw calls and normal exits. S05 physical outcomes supplied in the task establish 1920 startup PASS; 2560 startup/gameplay PASS; initial HUD/camera PASS; clipping OBSERVED. These are separate evidence records. Initialization logs cannot localize clipping; the image's instantaneous FPS counter does not measure pacing or input latency.

## Renderer path and observation limits

Addresses below identify Retail source/disassembly references; JPRE translations are validated by existing patch/relocation tests, not assumed numerically identical.

| Stage | Source / relevant state | Finding and limits |
|---|---|---|
| Camera/projection | `build_sites`, projection setups 0x51444d/0x5cc39d; SCALE/ASPECT; ui.asm world_a/world_b | Height-derived scale preserves vertical framing; horizontal extent grows. Complete camera pose is not recorded. |
| Visibility/culling | Stage selector 0x5be1d0/0x422f20; authored direction codes | Known solid/meshed model selection is yaw-dependent, not a complete screen-space frustum test. Full object rejection paths remain unaudited. |
| Geometry submission | SUBMIT_A 0x514576 / SUBMIT_B 0x5cc4c6; HUD pass ownership | Existing hooks restore world or HUD projection. Pool limits remain finite; no overflow evidence from the reported run. |
| Polygon clipping | Retail 0x5d3430 onward; 0x5d3461 Y test, 0x5d34de X test | Inspected quad boundary code compares against FB_H/FB_W globals, not fixed 640. This is one path, not proof about every clipper. |
| Clip reprojection | Retail 0x5d2fcc and related sites; asm/lockline.asm | Existing correction distinguishes 2D aspect from 3D focal scale. Near-plane/subdivision paths exist; no failing input was captured. |
| Rasterization | MASK_PACK/MASK_ADVANCE, generated spans | Existing D01 x86 tests verify packed pitch, MMX consumers and row advancement. Not exhaustive for every polygon/span input. |
| Coverage mask | resolution_geometry/mask_layout/mask_origin | 2560 meaningful row: 320 bytes; allocation pitch: 512; 1080 rows: 552960 bytes; adjacent row table: 4320 bytes. |
| Framebuffer | FB_PITCH/FB_W/FB_H and row origins | Real surface pitch is distinct from width and canvas pitch; existing padded-pitch tests pass. Runtime surface corruption is not observed. |
| Presentation | pinned cnc-ddraw dd_SetDisplayMode and render paths | Internal dimensions separate from desktop, aspect maintained. Accepted configuration is unchanged; this does not rule out all backend/driver artifacts. |

## Frustum and culling

VERIFIED: enemy marker X thresholds expand from focal-space ±256 according to visible width; its bearing window also expands while vertical limits remain unchanged. At 2560 this is approximately ±455.111 and bearing threshold 0x1f22. These are **marker** rules, not proof of whole-object visibility.

Stage solid/meshed selection retains fixed widened windows: 0x5800 with doubled compare 0xb000 on four-way cases, and 0x4800/0x9000 on eight-way cases. Both 1920 and 2560 use these same constants. A wider view can expose more geometry while this authored yaw policy remains fixed. That is a candidate for scene-dependent appearance changes, not evidence of incorrect rejection. Normal transparency/occlusion/gameplay hiding must be distinguished from a defect.

The machine-select hangar has separate angular bounds (stock 31.57/28.43 degrees, widened using aspect margin) and intentional shading of side machines whose textures are unavailable. This applies to selection, not automatically to gameplay clipping. No complete object/frustum rejection stream or stable object identifiers are available. Whether an actually visible object is incorrectly rejected remains UNKNOWN.

## Polygon edges, conversions and synthetic test

At Retail 0x5d34de, the inspected instruction sequence uses unsigned `jb` for coordinates below the supplied positive extent, then signed `jl` to identify negative coordinates; remaining coordinates receive the opposite-edge bit. Negative signed values appear large unsigned, so the second branch is intentional. The Y group uses the same branch structure. Its width load at 0x5d34b5 reads FB_W; the earlier Y load reads FB_H.

`tools/clippingtest.py` verifies the original byte sequence and executes it under Unicorn for 128 cases across eight research dimensions: -32768, -1, zero, one, extent-1, extent, extent+1 and 32767, for both extents. All produce the expected boundary code. Only the inspected Retail fragment is exercised; JPRE full-path equivalence and actual object rejection are not inferred from this test.

Projection/clip reprojection uses floating-point values and integer conversion. The inspected reciprocal-table range tests (0x43000000 / 0x45fff800) concern positive floating-point depth, not a screen-width limit. Other polygon paths and extreme transformed values are not exhaustively proved. Existing HUD rescale reads signed 16-bit vertex fields: 5120-wide positive screen coordinates fit that representation, but transformed/offscreen coordinates can be larger. No universal safe-width threshold follows from that fact.

## Mask and canvas boundaries

The ten packed-stride sites, 24 row advances, four EDX stride sites, row-table initialization/clear, padding canaries and renderer-B origins remain covered by D01's real-instruction tests. At 2560, horizontal half origin is 160 mask bytes, not half of the padded stride; vertical half origin is 540×512. Focused V02 checks cover bits 31/32, 63/64 and the last visible bit, first/last rows, and row-table separation.

No failing consumer was identified. These tests reduce the likelihood of the specific fixed-stride/origin mechanisms they cover; they cannot disprove a missed consumer or content-dependent span fault. The V01 static probe correctly reports no static violation and insufficient runtime evidence.

The 4096-byte canvas pitch, 2048-column capacity and D_OFF/D_STAGE/D_COPY remain separate from visible width. Logical widths across the eight cases are 640, 640, 854, 854, 1138, 1146, 1706 and 1706. All fit the allocation; fitting does not authorize an unsupported mode. The even-rounded logical width exceeds capacity once floor(480W/H) reaches 2049; that is a canvas research constraint, not the observed clipping threshold.

## HUD, artwork and aspect implications

The accepted 2560 HUD is centered in 1920 pixels at x=320; the world and world-relative markers use all 2560 pixels. Letterboxing on the 2560×1440 desktop and intentional HUD containment are not clipping defects. Photo backdrops use uniform cover scaling from 496×384: vertical content is cropped increasingly as the canvas widens. Sampling bounds pass; no anisotropic stretch is introduced by that path. Title/encounter tiling, hangar draw and transitions have different rules and need separate visual attribution.

4:3 and 16:9 preserve their established behavior. 21:9 D01 has physical startup/gameplay evidence but incomplete visual coverage. The 3440 and both 32:9 cases are GEOMETRY DERIVED only. Wider views may expose authored hiding, pool limits, transformed-coordinate range or undiscovered consumers; none is RUNTIME VERIFIED at those modes. The known 4:3/default-F4 three-hangar-site mismatch is unchanged, with no demonstrated dependency on this startup-successful clipping report.

## Ranked hypotheses and decision

This is a **triage order**, not measured likelihood; the missing location prevents a defensible probability ranking.

1. Scene-specific authored containment/crop or stage solid/meshed selection mistaken for missing geometry. Source mechanisms exist; whether the observed scene uses them is unknown.
2. Object visibility/rejection rule not widened with the view. Plausible but no identified failing object or rejection instruction.
3. Polygon clipping/subdivision or transient projection/pass mismatch. One edge fragment passes; other paths and actual input remain unknown.
4. Content-dependent rasterizer/mask consumer or allocation corruption. Known stride/origin mechanisms pass targeted tests; coverage is not exhaustive.
5. Framebuffer/presentation artifact. Accepted aspect-preserving output and successful initialization weaken a generic startup explanation, but do not prove pixel correctness for all frames.

Outcome C; low root-cause confidence. **Smallest justified correction: none.** Changing frustum constants, mask pitch, HUD, wrapper or clipper without a matching reproduction is UNSUITABLE.

Minimum future evidence: identify whether the defect affects gameplay geometry, a marker/HUD element or authored artwork; a marked frame or short existing clip with scene/camera/movement context; whether it occurs at a screen edge, near camera, or during a transition. A 1920 comparison is useful only if scene and camera can be shown equivalent. This is an evidence specification for a later approved milestone, not a request to run Windows now.

D02-V03 recommendation: localize the reported defect first, then trace one implicated path and reproduce its mechanism before proposing a correction. No live instrumentation or next-sprint work is started.
