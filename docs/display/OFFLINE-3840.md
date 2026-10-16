# D03-P01 — offline 3840×1080 single-player proof

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

3840×1080 generation is available only through `tools/engineering3840.py --private-proof`. It loads a separate patcher module and opts that instance into `_PRIVATE_3840`. Ordinary UI, CLI, configuration, environment and normal module loads do not enable it. No public resolution list changes. 3440×1440, 5120×1440 and other unapproved dimensions remain rejected. This is not a Windows handoff or local VS implementation.

## Geometry and consumers

| Quantity | Verified generated/derived value |
|---|---:|
| Visible size / minimum 16-bit row | 3840×1080 / 7680 bytes |
| Minimum visible framebuffer | 8,294,400 bytes |
| Mask words / meaningful row bytes / padded pitch | 120 / 480 / 512 |
| Mask allocation / adjacent row table | 552,960 / 4,320 bytes |
| Right-half mask origin / vertical-half origin | 240 / 276,480 bytes |
| Canvas pitch / rows / capacity | 4096 / 480 / 2048 columns |
| Pre-3D logical/active canvas width | 1706 columns |
| HUD composition / horizontal origin | 1920×1080 / 960 |
| HUD spread cap / existing scale | 240 / 2.25 |
| Marker X bounds / bearing | approximately ±682.6667 / 0x2753 |

The ten packed sites retain `b4 02 90`. Tests execute original entry instructions with framebuffer pitches 7680, 7744 and 8192, verify registers/flags, follow MMX unpacking and test signed multiply-add row addressing. Both editions also execute row-table initialization, mask clear and all 24 row advances, with guard sentinels and all four EDX stride sites checked. A/B origin generation remains tied to visible width, not padded pitch.

Retail/JPRE images generate deterministically with no skipped patches. Every UI relocation is checked against the edition map. Actual world projection entry points retain `(1645.3125, 2.7421875, 1350)` for their mapped components at 1080 height. Existing vertical scale is unchanged; mode-width geometry expands world coverage rather than resampling a 1920 frame. F4 table application to 1280×720 and back is exercised internally; Windows surface recreation is not emulated. The unrelated 4:3/default-F4 hangar mismatch is preserved.

## Newly isolated composition limitation

The first 3840 photo test failed its old full-width-fill expectation. Investigation found **integer composition rounding**, not a mask overrun: 1706×2.25 = 3838.5, truncated by the existing fixed-point fit to 3838 destination pixels, centered with one pixel remaining at each side. In the synthetic zero-filled surface those columns remain black. They need not always be black with different prior contents.

The test now explicitly verifies the one-pixel inset, untouched outer columns and all sampled pixels within the active image. Original 1920/2560 checks retain their zero-inset expectations. No renderer rounding, canvas allocation, artwork or sampling algorithm changed. This is a known offline visual limitation, not full-bleed photo acceptance and not an explanation of the older unlocalized 2560 clipping report.

Retail x86 compositor tests cover both photo walkers in full-view mode, HUD timer/bar/weapon/reticle placement, four-region row-tail canaries and a padded-framebuffer no-op pass. JPRE has generated/relocation and mask/projection instruction proofs; complete JPRE 2D runtime execution remains unverified by the Retail-specific compositor harness.

## Coverage and limits

- Polygon edges: existing V02 real Retail clip-code fragment tests include 3840 extents. This does not cover every polygon/near-plane/object path.
- Rasterizer/mask: ten packed consumers, row/clear/origin paths and canaries pass. Exhaustive content-dependent span behavior remains unknown.
- Canvas/copies: existing regions D_OFF/D_STAGE/D_COPY fit; no new game buffer or expanded canvas. Only the emulator's host-side test surface allocation grows to fit the fixture.
- Object visibility: existing yaw-based meshing/hangar rules remain unchanged; no speculative culling correction. Wider scene behavior needs later validation.
- Split assumptions: generated legacy split data still exists, but projection/indicator ownership has not been redesigned or accepted for 32:9 VS. Tests of stored A/B offsets are not local VS implementation or acceptance.
- Framebuffer: minimum and padded pitches pass selected arithmetic/compositor tests. Actual DirectDraw allocation, two-backbuffer operation and presentation remain NEEDS VALIDATION; no startup semantics or wrapper settings changed.

The offline proof passes within those limits. No live clipping instrumentation, controller changes, presentation queue or timing change was introduced. Old admitted modes remain byte-identical both in normal and explicitly gated module instances.

Recommended D03-P02 scope: review the documented photo-edge rounding before making any visual-policy change; then, only if authorized, address per-viewport projection/marker ownership for local VS as a separate proof. Do not treat these 1P outputs as an accepted VS or physical Windows candidate.
