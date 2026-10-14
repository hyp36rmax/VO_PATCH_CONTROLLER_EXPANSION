# D04-P04 shared presentation gate

Status: **BLOCKED — shared composition; D04-P03 runtime preserved.**

Baseline: `7c676682175489adfa57c23e6b1335539878547c`, clean `Display-Expansion` checkout. Its complete-history recovery bundle verified successfully. The user reports D04-P03 independent P1/P2 physical UAT passed; this is physical evidence, distinct from the host API-double tests. The intro has audio and can be skipped, but its picture is not visible according to the same brief.

## Verified dependency

`asm/ui.asm:frame_setup` already selects the original shared/split geometry for each frame (`D_SHOW`): the round substate set selects split, otherwise one player's full viewport is selected. No replacement state machine is needed. Existing Retail/JPRE emulation exercises shared/round transitions and confirms shared width 3840 versus independent width 1920.

The D02 `hud_rect=(960,0,1920,1080)` is a HUD composition boundary, not the bounds of all shared content. `pre` computes a 1706-column shared pre-phase canvas; `fit` scales it by 2.25 to 3838 pixels at x=1. `margins_photo` fills that canvas from the original 496-column photo. The proposed center extraction samples approximately photo columns 123.92–372.01, versus 0.01–495.99 in the existing canvas. It therefore discards real artwork, not just empty margins. World/targeting coordinates also retain the full 3840-wide viewport.

`tools/dual_display/test_shared_bounds.py` reproduces this numerical counterexample using current production geometry. It is a structural bounds audit, not a screenshot or proof that every shared screen uses the photo path.

A wrapper-only crop cannot recover the discarded composition. Fitting the full 32:9 frame into each monitor would preserve its pixels but would not implement the requested centered 16:9 shared composition. Changing producer-side shared canvas geometry could resolve this, but changes generated game images; changing the shared 3D view also needs explicit review against the no-projection-change constraint. No such change was made under this task's byte-identical image requirement.

A future implementation must latch the producer's presentation selection with the completed surface generation. Reading current game modes when presenting a texture is insufficient: a texture may predate the current game state. The existing surface lock/upload boundary is the integration point to investigate, not permission to invent a speculative state hook.

## Preserved implementation and validation

- Runtime wrapper, game generator, controller implementation, launcher and collector are unchanged.
- Independent source rectangles remain `(0,0,1920,1080)` and `(1920,0,1920,1080)`.
- Mixed-aspect coverage expands from 36 to 64 monitor-size pairs, adding 5120×1440 and 1600×1200. Existing cases remain. The later identity-test fixture is reset explicitly to avoid accidental overlap after the expanded matrix.
- Production presentation API-double tests pass, including 28 graphics failure points, shared texture generation ownership, focus, reset and resource teardown. These do not validate shared mirroring.
- Retail/JPRE checks: all 33 reported passing; GUI execution skips without Tk and CI tree checks are not executed locally.
- Existing VS transition and renderer isolation tests pass. Six Retail/JPRE single-player images at 1920, 2560 and 3840 match the P03 hashes byte-for-byte.

Outputs still draw from the same uploaded texture generation, then present sequentially using the existing windowed swapchains. Different refresh rates are not forced equal. This does not guarantee simultaneous scanout or zero added latency.

## Movie and delivery status

Movie visibility root cause: **UNKNOWN**. The pinned wrapper contains separate AVI/MCI/GDI handling, but that alone does not establish which path this game's movie takes. No decoder, video hook, or input behavior changed. Audio/skip evidence is preserved; no movie fix is claimed.

Shared mirroring, shared routing transitions, and shared-content physical acceptance: **BLOCKED / NOT IMPLEMENTED**. No D04-P04 UAT ZIP is produced and no new physical test is requested. The validated P03 package remains the usable checkpoint. Packaging and relocation were not rerun for a nonexistent P04 binary.

Next scope: resolve the shared producer-composition dependency while retaining the original P03 images as immutable controls; explicitly settle whether a new private game variant may change shared composition. Then implement frame-coherent routing and deliver one consolidated UAT package. No public branch, controller code, main, Unified Overlay, release or remote was modified.
