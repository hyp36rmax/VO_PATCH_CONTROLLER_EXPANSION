# Display Expansion implementation

This document describes the current Controllers + Display implementation on
Experience. Source inspection and automated checks establish implementation
behavior; maintainer hardware records and acceptance of a particular Windows
package are separate evidence. Historical display reports retain their original
checkpoint scope. The [design record](DUX-V1.0.md) includes superseded requirements;
its complete-presentation Mirror amendment takes precedence over earlier P1-only rows.

## Upstream foundation and rendering

Pairomaniac's native widescreen patch replaces the original rendering dimensions
and related game/UI calculations rather than stretching a finished 4:3 image.
Display Expansion reuses the existing patch/linking machinery and extends its
profile generation and output routing. See [upstream rendering notes](../HIRES.md).
Original game logic, player input ownership and simulation remain authoritative.

| Profile | Generated rendering dimensions | Purpose |
|---|---|---|
| Original 4:3 | 640×480 | Original non-hires path |
| 16:9 | 1920×1080 | Wide single-source presentation |
| 21:9 option | 2560×1080 | Ultrawide profile; label denotes the common display class |
| 32:9 | 3840×1080 | Superwide single-source presentation |
| Dual Versus | 3840×1080 | Dedicated P1/P2 view composition |

These are internal profile dimensions, not a demand that Windows switch the
physical monitor to the same resolution. F4's existing resolution behavior and
its profile restrictions remain; the original non-hires 4:3 path does not install
the native-widescreen toggle. Monitor output fitting is a separate presentation
operation. The game aspect preference is not inferred from monitor width.

## Discovery, assignments and configuration

Active Windows paths are queried through QueryDisplayConfig. Discovery resolves
monitor identity, current desktop geometry and availability; assignment uses saved
identifiers rather than assuming enumeration order is stable. Independent dual
outputs require distinct active desktop targets; cloned outputs sharing an origin
are rejected as an independent pair.

F5 **Graphic Settings → Display...** exposes **Display Mode**, **Primary Display**,
**Secondary Display** and **Game Aspect Ratio**. Secondary selection is relevant
only to dual modes. Pending edits are validated before saving; OK persists and
Cancel discards. The existing `player-displays.ini` stores presentation choices
and player display IDs. Startup resolves the saved request into an effective mode
before the game's retained entry point. Settings requiring reinitialization apply
on the next launch; saving does not rebuild the running renderer.

The resolver preserves requested preferences when a monitor is unavailable. It
can choose an available primary and fall back to Single at launch without deleting
saved IDs or aspect. This is not a promise of seamless renderer replacement after
mid-game display loss. Recovery of a changed physical layout requires another
launch. A save failure retains the prior settings and reports its stage/error.

## Presentation routing

| Mode | Ordinary/menu presentation | Local VS gameplay |
|---|---|---|
| Single | One selected output | Original split-screen layout |
| Dual Versus | Primary-only startup/menu; shared selection on both outputs | Independent P1/P2 views |
| Dual Mirror | Complete source on both outputs | Complete split-screen image duplicated |

Dual Versus uses the dedicated internal composition with independent 1920×1080
player viewports. Mirror uses the same selected source profile as Single, not a
P1 crop. Each output fits its source into its own desktop bounds, preserving aspect
without requiring equal monitor dimensions. The original AVI is an exception:
visible movie playback remains on the primary display and the secondary is black.
Upstream movie-picture framing is retained. Camera and controller ownership do
not change when presentation mode changes.

## Source boundaries

| Source | Responsibility |
|---|---|
| [mode_profiles.py](../../tools/dual_display/mode_profiles.py) | Profile dimensions and reuse of existing generators/movie blob |
| [startup_image.py](../../tools/dual_display/startup_image.py), [startup_runtime.h](../../tools/dual_display/startup_runtime.h) | Generated startup plans and checked activation before original game entry |
| [inventory.h](../../tools/dual_display/inventory.h) | Active-path discovery and monitor identities |
| [mode_config.h](../../tools/dual_display/mode_config.h), [layout.h](../../tools/dual_display/layout.h) | Effective selection, fallback and output fitting |
| [f5_dialog.c](../../tools/dual_display/f5_dialog.c), [f5_settings.h](../../tools/dual_display/f5_settings.h) | Player dialog, validation and persistence |
| [presentation.h](../../tools/dual_display/presentation.h), [policy.h](../../tools/dual_display/policy.h) | Output routing and phase policy |
| [split_preference.py](../../tools/dual_display/split_preference.py) | Retained Local VS split preference |
| [build_catalog.py](../../tools/experience/build_catalog.py), [catalog_input.py](../../tools/experience/catalog_input.py) | Offline Retail/JPRE recipes and strict source locks |
| [package_normal.py](../../tools/experience/package_normal.py) | Complete upstream patcher plus required display runtime |

Generated recipes are derived from recognized original executables and verified
source, not a replacement authority. They contain sparse changes, not original
game images. No additional offsets or hooks are specified here beyond the actual
source. Diagnostics use the existing [local privacy controls](../project/EXPERIENCE-DIAGNOSTICS.md).

Automated coverage includes profile generation, source-lock rejection, 512 recipe
reconstructions, startup activation, display selection/fallback, F5 transactions,
presentation API doubles and Retail/JPRE Apply/Restore. These tests do not prove
physical monitor timings, every display pairing or Windows GUI acceptance. The
[validated hardware inventory](../../README.md#validated-hardware) records the
maintainer's supplied scope; final integrated-package acceptance remains pending.
