# DUX-V1.0 — Display Configuration and Presentation

This is the approved canonical frozen design specification. Requirements below
define the intended behavior; they do not establish
implementation completion or physical validation.

For current implementation and source boundaries, see
[Display Expansion implementation](IMPLEMENTATION.md). The checkpoint tables below
are historical requirements and evidence, not a current installation guide.

## Original frozen requirements (Mirror revised by F04B)

The approved F04B amendment below supersedes P1-only Mirror and the requirement
that every dual mode use the dual-view framebuffer. Other decisions remain in force.

### Display modes and discovery

| Condition or setting | Required behavior |
|---|---|
| Fresh installation | Single Display by default |
| One active monitor | Single Display |
| Two or more active monitors | Expose Single Display, Dual Display — Versus, and Dual Display — Mirror |
| Monitor assignments | Independent primary and secondary assignments |
| Physical outputs | Support independent resolutions and aspect ratios |
| Temporary hardware fallback | Preserve saved preferences |

### Rendering

Single Display uses the selected validated 4:3, 16:9, 21:9 or 32:9 rendering
profile. Ordinary 16:9 single-display operation must not be forced to 3840×1080.

Dual Display retains the validated 3840×1080 internal framebuffer with independent
1920×1080 P1/P2 viewports. Internal rendering resolution remains independent of
physical monitor output resolution.

### Dual-display presentation

| Game phase | Display 1 | Display 2 |
|---|---|---|
| Startup, attract mode and main menu | Active presentation | Black |
| Local VS player selection and pre-fight | Shared presentation | Mirrored shared presentation |
| Local VS gameplay — Versus | P1 | P2 |
| Local VS gameplay — Mirror | P1 | P1 |
| Return to menu | Active presentation | Black |

### Configuration and upstream compatibility

Existing F-key menus remain the initial configuration interface. Future Unified
Overlay must use the same configuration authority. Changes requiring display
reinitialization apply on the next launch unless live switching is validated.
Original upstream functionality must be preserved.

### Historical F04 scope

F04 introduced mode-aware rendering selection and movie centering while
preserving the physically validated F03C dual-display implementation. F-key
integration and Unified Overlay were outside that private checkpoint.

## Historical F04 implementation and validation status

This section records F04 evidence, not the current integration acceptance status.

| Area | Status at F04 checkpoint `0a65238d19b346dffba646422f44e4b675e05ed1` |
|---|---|
| F03C baseline | Physical validation confirmed movie visibility, audio/skip, single and dual gameplay |
| F04 selection and movie geometry | Implemented; internal tests passed; Windows acceptance pending |
| Existing F-key menus | Retained; expanded display-setting integration remains deferred |
| F04 private setup interface | Temporary launch-time selector for UAT, not completion of the frozen F-key interface requirement |
| Original 4:3 | Uses original non-hires rendering; native-widescreen F4 toggle is not installed in this profile |
| Hires 4:3 with widescreen F4 alternate | Existing generator dependency remains unsupported |
| Dual failure after startup | Retains F03C composed-window fallback; changing the rendering profile requires another launch |
| Unified Overlay | Deferred; no implementation in F04 |

At F04, the private test package was internally verified, not physically accepted.
Implementation details and test boundaries are recorded in the
[F04 engineering record](PRIVATE-DUAL-DISPLAY-P05-F04.md). The current settings
schema is documented separately in [F04 configuration storage](DISPLAY-UX-V1.md).

## Clarified Local VS routing contract — F04A

Display discovery, selected presentation mode, gameplay state and player viewport
ownership are independent. Entering Local VS must not change the selected mode.
Monitor count does not determine gameplay or override saved mode preferences.

| Effective mode | Local VS selection | Local VS gameplay |
|---|---|---|
| Single | Original game presentation | Original P1/P2 split-screen; upstream horizontal/vertical layouts |
| Dual Versus | Shared selection on both displays | P1 on Display 1; P2 on Display 2 |
| Dual Mirror | Shared selection on both displays | P1 on both displays; P2 remains independently controllable |

Unavailable dual output falls back before game initialization to a Single Display
profile, with the reason reported and saved mode, monitor IDs and aspect retained.
A running dual profile must not be relabeled as recovered Single Display. Until
runtime profile switching is validated, a later display loss ends that private
test through normal closure and requires another launch to resolve recovery.
Controller participation and camera ownership do not change with presentation.
Startup/menu remain primary-only; dual secondary is black. Existing movie
presentation is preserved; F04A did not implement movie enlargement.

At F04A, internal routing tests had not reproduced the reported physical P1
duplication; that checkpoint did not establish a fix.

## Approved F04B amendment — complete presentation Mirror

This revision changes Mirror's source, not camera or controller ownership.
It supersedes the P1-only Mirror rows above; they remain as revision history.

| Mode | Rendering profile | Ordinary presentation / Local VS |
|---|---|---|
| Single | Selected original 4:3, 16:9, 21:9 or 32:9 | Original image; original P1/P2 split-screen |
| Dual Versus | Dedicated 3840×1080 dual-view image | Existing three-phase policy; independent P1/P2 during gameplay |
| Dual Mirror | The same selected profile as Single | Complete final image on both outputs, including both VS views and HUDs |

Mirror scales the full source independently into each monitor's current desktop
bounds, preserving aspect without cropping. Ordinary menu/shared/gameplay frames
mirror regardless of gameplay classification. During the original AVI only,
Display 1 retains native visible playback and Display 2 remains black.
No Windows display-mode, camera, simulation or input ownership change is allowed.
Saved preferences, session overrides and prelaunch recovery remain authoritative.

**F04B checkpoint evidence:** the private implementation provides complete-source sampling using the
existing output swapchains. **Validation:** internal API-double and generation
checks; Windows physical acceptance pending. Native movie geometry is unchanged.
