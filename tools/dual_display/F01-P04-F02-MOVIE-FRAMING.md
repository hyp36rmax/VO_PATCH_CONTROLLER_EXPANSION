# F01-P04-F02 — Upstream movie framing

## Evidence and cause

The authoritative `asm/movie.asm` is unchanged from upstream commit
`87b99dc6a59c4149bebcefd52a21ee4f82b67ddf` (Native widescreen). Its comments record a
measured Retail picture band at rows 30–209 inside a 320×240 AVI, with dim boundary
rows outside it. The visible band is 320×180, or 16:9. The local Retail and JPRE
files have identical 16,488,200-byte content and SHA-256
`cf5094ec93879089b2544aa5bc1ff83764a6ab120fb8eac0c77c4b5492fe0c38`.
AVI headers independently confirm 320×240. Pixel boundaries were not independently
remeasured during this correction; their measurement provenance is upstream's source record.

The legacy caller passes a 640×400 or 320×200 movie window. Upstream instead asks
MCI_WHERE for the maximum source size, scales the measured band proportionally,
fits that picture without distortion, centers the AVI child, then applies MCI_PUT
source and destination rectangles. Maximum-source querying avoids cropping an
already cropped rectangle on repeated placement. If querying fails, the existing
caller-size fallback remains. The decoder, audio, file and playback loop are not
replaced.

Experience's `movie_blob` previously reassembled this source after replacing
`BAND_TOP=30` with zero and `BAND_ROWS=180` with 240. This explicitly disabled the
framing correction. At a 1920×1080 physical client it fitted a 1440×1080 full frame,
leaving a 1440×810 visible picture. Reusing the original blob produces a centered
1920×1080 visible picture. No new crop coordinates were invented.

## Correction and preservation

`movie_blob` now returns the upstream MOVIE blob unchanged. The existing physical
GetClientRect lookup, F04A AVI-only wrapper scaling bypass, F03C window ownership
and visibility handling, and F04B complete mirroring remain untouched. The optional
upstream movie checkbox remains authoritative; disabled movie patching is not
silently reenabled. The normal installation backend only adds that checkbox's
Boolean value to diagnostic version metadata.

| Physical display | Centered visible picture (x, y, width, height) |
|---|---|
| 640×480 | 0, 60, 640, 360 |
| 1600×1200 | 0, 150, 1600, 900 |
| 1920×1080 | 0, 0, 1920, 1080 |
| 2560×1440 | 0, 0, 2560, 1440 |
| 3440×1440 | 440, 0, 2560, 1440 |
| 5120×1440 | 1280, 0, 2560, 1440 |

Coordinates are relative to the selected physical client; desktop offsets are
added for diagnostic screen coordinates. No desktop mode or internal framebuffer
size is requested or changed by this correction. Dual Versus and Dual Mirror
retain Display 1 movie presentation and a black Display 2, then their established
presentation restoration.

## Diagnostics

The passive collector reads the AVI header and checks the known original identity;
it never decodes, captures or exports frames. It records numeric source dimensions,
known picture bounds, selected physical rectangle and expected picture rectangle.
Unknown assets, absent files, disabled patching and invalid geometry are explicitly
marked as geometry evidence fallback, not declared measured crops.

The existing window sampler additionally records observed movie bounds and
visibility transitions. `expected_*` values are calculated policy; `window_*` values
are observed Win32 rectangles. `geometry_match` compares them without claiming
pixel visibility or MCI success. Sampled movie appearance/disappearance approximates
playback start/end; it is not a decoder timing trace. Existing dual presentation
logs retain hide/end/restore events. Single-display restoration still needs visual
acceptance; an ended window alone does not prove restored pixels.

Exports remain bounded, numeric and local. The automatic return archive is
`RETURN-THIS-VO-PATCH-EX-F01-P04-F02.zip`.

## Acceptance boundary

VERIFIED internally: linked upstream code for both editions across physical sizes,
scaled source frames, failed/empty source queries, ABI preservation, existing movie
and dual-presentation lifecycle policies, mixed resolutions and offsets, all 33
baseline regressions, F4/F5/save correction, diagnostics and package tests.

NEEDS VALIDATION: actual Windows MCI source clipping, visible picture size/shape,
Display 2 black during movies in both dual modes, skip/completion and presentation
restoration. Use the normal patcher, Restore Original before Apply, then normal
game launch. No administrator privileges, manual configuration or special launcher.
