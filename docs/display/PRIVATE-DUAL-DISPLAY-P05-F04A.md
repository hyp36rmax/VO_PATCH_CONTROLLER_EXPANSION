# F04A: explicit private display-mode sessions

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

Status: **VERIFIED** internally; **NEEDS VALIDATION** on Windows. Movie enlargement is **BLOCKED** under the full-frame, no-crop/no-stretch requirements. F04 playback is preserved.

Baseline: `b168d5d29db4868cf0afeacb04e37c8cb7bf1e2d`. Frozen requirements remain in [DUX-V1.0](DUX-V1.0.md).

## Session selection

| Launcher | Required mode | Gameplay source |
| --- | --- | --- |
| START-SINGLE-DISPLAY.cmd | Single | Selected original/wide/ultrawide/superwide profile |
| START-DUAL-VERSUS.cmd | Versus | Independent 1920×1080 halves of 3840×1080 |
| START-DUAL-MIRROR.cmd | Mirror | Player 1 on both displays |

Each private launcher locks and labels its mode. The existing selector validates monitor assignments and profile availability. Dual requests with fewer than two active monitors are rejected before launching. An emitted mode different from the request is also rejected.

`game/player-displays.ini` remains the saved authority. Session selections use a temporary `game/session-display.ini`, passed explicitly to the wrapper through `VO_SESSION_CONFIG`. This is a disposable projection of the same schema. The launcher records saved-file hashes before and after, collects the session file as evidence, deletes the active temporary file and clears environment overrides. Normal `LaunchModes.ps1 -Entry saved` retains the saved-settings flow.

Explicit dual tests set `VO_STRICT_MODE`. Wrapper initialization/presentation failure requests normal game closure once through WM_CLOSE; it does not force-kill the game or globally intercept Windows behavior. The collector retains the existing raw HRESULT/fallback record. Missing presentation evidence, a fallback, no presented pairs, or a Mirror mismatch makes the launcher report failure. Normal launches retain existing recovery behavior.

## Movie evidence and limitation

Both original AVI assets have SHA-256 `cf5094ec93879089b2544aa5bc1ff83764a6ab120fb8eac0c77c4b5492fe0c38`. Their frame is 320×240 (4:3), with a central 320×180 image and embedded top/bottom bars. The header records 1056 frames, 41667 microseconds per frame and two streams.

On a 2560×1440 display, the largest uncropped 4:3 destination is already 1920×1440 at (320, 0), inside the centered 2560×1440 16:9 region. Its central picture occupies 1920×1080. Filling more of that display with the central picture requires cropping original frame content or stretching. Neither is authorized. Actual decoded physical pixel coverage remains **UNKNOWN** until Windows observation; destination calculations alone do not establish it.

No movie geometry, asset, decoder, audio, timing or skip implementation changes are included. F03C visibility and F04 placement remain intact. This candidate does not claim to solve the reported movie-size concern.

## Preservation and validation

Default Single uses the existing 1920×1080 profile. Original 640×480, 21:9 and 32:9 selections remain available. Original Local VS remains; no expanded 21:9 VS is added. Dual framebuffer, camera ownership, three-phase routing, monitor geometry and controller implementation are unchanged.

The 33 baseline regressions pass. Targeted host/API-double tests cover session selection, immutable preferences, missing monitors, mixed geometry, Versus/Mirror routing, strict failure closure, movie identity/lifecycle and centering. Package verification regenerates profiles, compares assets/helpers, inspects i386 dependencies/manifests, checks hashes/ZIP CRC and extracts under a relocated Unicode path. These checks do not replace physical Windows acceptance.

The private package contains all three launchers and automatically selects `RETURN-THIS-D04-P05-F04A.zip`; raw diagnostics survive compression failure. Windows mode selection, presentation, focus/restore, playback/audio/skip, controllers and shutdown require acceptance. Keep this checkpoint local; no publication or F-key/overlay integration is included.
