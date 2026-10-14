# F04B complete presentation Mirror

Baseline: `1bdab554816c2154ab0d071e420a62010b6278dc`.

Mirror previously selected the dedicated 3840×1080 VS image and cropped P1's
1920×1080 half twice. That implemented the former specification; F04B explicitly
replaces it with complete original presentation mirroring.

The selector now chooses the same original/wide/ultrawide/superwide executable
for Single and Mirror. Versus alone requires the dedicated dual image. Existing
monitor planning validates two separate outputs; missing output recovers before
startup without erasing saved preferences.

The launcher's `VO_COMPLETE_MIRROR` and `VO_SOURCE_SIZE` are transient projections
of its verified selection, not new saved settings. The wrapper requires Mirror's
configuration Mode to agree. It waits for the selected source dimensions and uses
the entire active framebuffer, excluding texture allocation padding. Both draws
sample the same uploaded texture over [0,width] × [0,height], so neither player
view nor HUD can be removed by a crop. Each destination uses independent aspect
containment. The classifier is retained for Versus; Mirror does not infer gameplay
or camera ownership from display mode.

The existing movie identity/ownership/bounds checks gate native AVI visibility.
Mirror permits that exact movie window independently of the dual-image classifier,
which intentionally does not recognize Single-profile executables. While it is
active, the primary output is hidden and secondary cleared black; normal complete
mirroring resumes when the child disappears. No timing delay or decoder change.

Internal tests cover all four source sizes, all classifier phases, full UV bounds,
shared texture identity, mixed monitor geometry, movie lifecycle, and existing
Versus failure/state-restoration checks. Baseline executable profiles remain
byte-identical, including original split layouts and controller code. Source
coverage establishes preservation of every rendered HUD/view pixel; physical
correctness of the original composition still requires Windows acceptance.

Resolution changes after output initialization retain the existing strict normal
closure policy; live profile switching is not claimed. All twenty F04B physical
acceptance items remain NEEDS VALIDATION. No publication is authorized.
