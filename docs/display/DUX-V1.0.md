# DUX-V1.0 — Display Configuration and Presentation

This is the canonical frozen design specification, confirmed by the project
owner. Requirements below define the intended behavior; they do not establish
implementation completion or physical validation.

## Frozen requirements

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

### F04 scope

Implement mode-aware rendering selection and correct movie centering while
preserving the physically validated F03C dual-display implementation. F04 does
not begin F-key integration or Unified Overlay. Development remains private and
local; no push or publication is authorized.

## Implementation and validation status

This section describes the current checkpoint separately from the frozen contract.

| Area | Status at F04 checkpoint `0a65238d19b346dffba646422f44e4b675e05ed1` |
|---|---|
| F03C baseline | Physical movie visibility, audio/skip, single and dual gameplay confirmed by the project owner |
| F04 selection and movie geometry | Implemented; internal tests passed; Windows acceptance pending |
| Existing F-key menus | Retained; expanded display-setting integration remains deferred |
| F04 private setup interface | Temporary launch-time selector for UAT, not completion of the frozen F-key interface requirement |
| Original 4:3 | Uses original non-hires rendering; native-widescreen F4 toggle is not installed in this profile |
| Hires 4:3 with widescreen F4 alternate | Existing generator dependency remains unsupported |
| Dual failure after startup | Retains F03C composed-window fallback; changing the rendering profile requires another launch |
| Unified Overlay | Deferred; no implementation in F04 |

The private test package is internally verified, not physically accepted.
Implementation details and test boundaries are recorded in the
[F04 engineering record](PRIVATE-DUAL-DISPLAY-P05-F04.md). The current settings
schema is documented separately in [F04 configuration storage](DISPLAY-UX-V1.md).
