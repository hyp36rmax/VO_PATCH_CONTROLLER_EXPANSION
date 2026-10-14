# D04-P05-F03C — movie-window visibility

Status: **VERIFIED internally; NEEDS VALIDATION on Windows**.
Starting private HEAD: `938b7928c08129aa7a2840f113cd1ed7f72c07bd`.
Physically validated display baseline: `81f1eae4dfcfbb5698ac98b971e9071c96af8a15`.
Pinned wrapper: `279a057ee7e1e4d584b56141c014ab01f3c6ee6d`.

## Evidence and scope

F03B recorded visible `AVIWnd32` / `von.avi`, parent/root `VirtualONClass`, beneath
the P1 presentation window. Both occupied (0,0,2560,1440); P2 occupied a different
1920×1080 display. That supports occlusion, not proof of decoded pixel visibility.
The returned enumeration marked top-level storage truncation; the relevant movie,
game and P1 windows were individually recorded. Movie absence after its last
sample is not independently proof of destruction.

This candidate removes the observed covering window only. It does not change
movie decoding, MCI commands, assets, source/destination movie rectangles, audio,
input, game executable, shared layout, gameplay rendering or phase classification.

## Identification and visibility

Management runs only after successful dual-output initialization and a completed
PRIMARY_ONLY pair, with the current completed policy also PRIMARY_ONLY. That
establishes a black P2 before intervention. Single-display mode never activates
this path.

A bounded child enumeration requires exactly one visible, existing `AVIWnd32`
window with the current process ID, direct parent/root equal to the original game
window, WS_CHILD and either no owner or the game as owner. Its positive rectangle
must fit wholly inside the assigned P1 monitor. Class names are read without
sending WM_GETTEXT or other synchronous messages to the movie thread. No movie
window or unrelated application window is repositioned, reparented or restyled.

While that window is visible, P1's presentation window is hidden. The normal
P1 stacking repair is suppressed and its swapchain is not presented. The existing
P2 target remains black. No extra game, frame queue, texture or playback system
is created. Game input focus and movie ownership remain original.

When the identified window disappears, becomes hidden, fails identity validation,
or the primary-only eligibility ends, P1 is restored with the existing topmost,
no-activate placement. Restoration is deferred while focus is elsewhere or the
game is minimized. Visibility failure disables dual output through the existing
fallback; teardown remains on the output-owning render thread. There are no
elapsed-time decisions about movie completion or skipping.

A movie outside the assigned P1 monitor, ambiguous identity or enumeration cap
preserves F02 behavior and logs rejection. This candidate deliberately does not
relocate the original game/movie to another monitor. It therefore does not promise
movie placement on a P1 monitor different from the movie's current monitor.

## Diagnostics and tests

Up to 64 movie transition records are buffered in memory. Shutdown writes detection,
identity rejection, previous P1 visibility, intervention, observed lifecycle end,
restoration result, shutdown and failure records to the existing presentation log.
No movie-path disk writes occur during playback/rendering. Suppressed P1 presents
are counted separately from successfully paired output presents.

Host tests execute production integration with API doubles: identity/ownership,
visibility/bounds, ambiguity/cap rejection, disappearance/hidden end conditions,
focus-deferred restoration, graphics/lifecycle failures, mixed output sizes,
black P2, gameplay resumption and the disabled single-display gate. They do not
execute a native decoder or prove physical video/audio/skip behavior.

## Private acceptance

Run START-DUAL-DISPLAY.cmd: check movie visibility/proportions/audio, black P2,
skip and menu restoration, mirrored selection, independent gameplay, original
controls, menu return and exit. Run START-SINGLE-DISPLAY.cmd: check original movie,
skip, menu, split-screen gameplay, F-keys and controllers. Return
RETURN-THIS-D04-P05-F03C.zip and observations for both runs.

The single-display package retains the exact original F02 control files. The dual
game, observer, helper and movie remain byte-identical to F02; only its private
wrapper changes. If the movie remains invisible, retain decoder/framebuffer-path
uncertainty and review the new evidence before any further correction.
