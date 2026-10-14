# D04-P05-F04 — mode selection and movie geometry

Status: **VERIFIED internally; NEEDS VALIDATION on Windows**.
Protected physical baseline: F03C, `18c87a0ac0463badcbaa0fdbdd1d6c4a2a587ff4`.
The user confirms visible movie, audio/skip, single and dual gameplay at that baseline.

## Selection and preservation

The launcher resolves [DUX-V1.0](DUX-V1.0.md) before starting one game process.
One game directory retains controller and game configuration across all profiles.
Immutable executable profiles are verified and copied into that directory before
launch. No runtime renderer switch, second game, new camera or input backend is added.

| Profile | Initial internal size | Generator / scope |
|---|---|---|
| Original 4:3 | 640×480 | Existing non-hires patch selection; original rendering and Local VS |
| Widescreen 16:9 | 1920×1080 | Existing upstream/D01 implementation and original Local VS options |
| Ultrawide 21:9 | 2560×1080 | Existing D01/D02 single-player implementation |
| Super-ultrawide 32:9 | 3840×1080 | Existing D03 single-player implementation |
| Dual Versus / Mirror | 3840×1080 | Existing F02 shared composition and independent 1920×1080 halves |

Widescreen/ultrawide F4 and F5 behavior is unchanged, including saved alternate
resolution selection. The Original profile deliberately does not install native
widescreen: the current generator cannot pair hires 4:3 with its default widescreen
F4 alternate. It uses the original renderer rather than claiming that unsupported
pair works. Expanded 21:9 Local VS is not implemented; use Original or Widescreen
for ordinary single-display VS. Existing camera ownership is unchanged.

Missing monitors/profiles fall back before launch without erasing requested
settings. If dual initialization fails after startup, F03C's composed game-window
fallback remains; it does not automatically relaunch a 1920-wide game. Selecting
Single Display on the next launch is required for that profile change.

## Movie evidence and correction

Retail and JPRE contain the identical AVI (SHA-256
`cf5094ec93879089b2544aa5bc1ff83764a6ab120fb8eac0c77c4b5492fe0c38`). Its RIFF
header reports 320×240, 1,056 frames, 41,667 microseconds per frame and two streams.
The upstream movie stub documents a 320×180 central picture within that 4:3 frame.
F04 preserves the entire frame and embedded black bars, as required by the no-crop
contract. It does not assume that the full file is 16:9.

The private generator changes only two constants in the linked movie stub:
source top 30→0 and source height 180→240. Blob size, relocations, labels, all
other game bytes and MCI call ordering remain identical to each existing profile.
The existing real-client-area calculation then contains and centers the full frame.
On a 2560×1440 client the result is 1920×1440 at (320,0).

The pinned wrapper's child-GDI hooks otherwise apply framebuffer scaling to these
already physical movie coordinates. F04 forwards the four GDI blit forms unchanged
to their original functions only for this process's direct `AVIWnd32` child in the
private launch mode. Other child windows and game framebuffer paths retain their
original code. Original MCI decoding, audio, timing and skip mechanisms are retained.

The original game window uses the selected monitor's current desktop rectangle,
including negative origins. The wrapper's borderless origin reset is corrected
for that explicit selection. This is window geometry, not a Windows display-mode
request. F03C visibility/lifecycle handling, black P2, phase classification and
independent scaling remain unchanged. No timer determines movie completion.

## Evidence limits and acceptance

Host tests execute the linked movie code under Unicorn for both editions and six
sizes, checking source/destination rectangles, MCI arguments, registers and stack.
API doubles exercise movie identity, lifecycle, skip-equivalent disappearance,
focus restoration, output failures, mode selection, fallback, mixed geometry and
preference immutability. Source/image comparisons establish audio/skip code and
controller preservation; they cannot establish audible or physical behavior.

Run the single and dual launchers from the consolidated ZIP. Both open the same
saved settings; choose the intended mode explicitly. Check movie framing, audio,
skip, menu, Solo, original Local VS, mirrored selection, independent gameplay,
focus/minimize/restore, return to menu and exit. Optional checks cover 21:9/32:9
single-player and Mirror mode. Return `RETURN-THIS-D04-P05-F04.zip` with observations.
All runs are retained; raw copies survive ZIP compression failure.

No public changes, F-key integration, Unified Overlay or release are included.
