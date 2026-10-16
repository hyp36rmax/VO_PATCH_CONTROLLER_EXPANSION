# Private 3840 × 1080 local VS candidate

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

The dedicated `tools/engineering_vs.py` generator extends the private 3840
image with two 1920 × 1080 viewports using the original split renderer.
Normal generators and existing single-player images remain unchanged.
This is a Windows acceptance candidate, not physically validated local VS.

## Implementation

- Existing viewport setup supplies adjacent A/B destinations and the surface's
  actual row pitch. Existing mask regions use 240 bytes each in 512-byte rows.
- The dedicated image uses side-by-side projection factor 1.0, yielding scale
  2.25 at 1080 height. The original F4 alternate-resolution table is retained.
- A small private frame adapter selects the original Ver layout in split mode
  at 3840 width. It chains into the existing `frame_setup` wrapper.
- Each original indicator entry selects its own bounds before producing
  geometry. The predicate matches `frame_setup` and reads the same live game
  states and round-state mask. It does not use last frame's cached view choice.
- Split gameplay installs horizontal bounds derived from a 1920-wide viewport
  and the corresponding signed bearing limits. Shared presentation restores the
  existing 3840 constants. Alternate resolution leaves its installed values alone.
- Entry adapters preserve registers/flags and replay the verified nine-byte
  prologues. They do not intercept camera updates, input or DirectDraw calls.
  Original marker vertices are not translated by an extra viewport offset.

Only the explicit private generator installs `.vovs`. Retail and JPRE have
independently checked entry bytes and operand locations; unsupported builds
are rejected. Existing writable F4 code/data sections also contain the
indicator operands. No new full-frame allocation or queue is introduced.

## Reproduction

From the repository, using the existing dependencies and pristine games:

```sh
python3 tools/engineering_vs.py /path/to/v_on.exe --private-local-vs --output /new/path/v_on.exe
python3 tools/vstest.py /path/to/retail/v_on.exe /path/to/jpre/v_on.exe
python3 tools/vsisolationtest.py /path/to/retail/v_on.exe /path/to/jpre/v_on.exe /path/to/results
python3 tools/check.py /path/to/retail /path/to/jpre
```

The private CLI creates an executable only. Use the prepared UAT package for
runtime assets, input helper, pinned wrapper, launchers and automatic logs.

## Evidence and limits

| Check | Offline result |
|---|---|
| Producer-time state combinations | 7,128 per edition; live-state selection and register/flag preservation |
| Shared → split → shared frame setup | Original wrapper executed in both editions; dimensions/destinations/scales checked |
| HUD composition | Existing compositor writes distinct pixels only inside the owning view |
| Solid/textured quad/triangle flushes | 192 guarded cases: two editions, both renderers, three pitches, four corners |
| Mask ownership | Own-region writes; opposite mask region retained across draws; shared scratch recorded |
| Existing generated images | Six 1920/2560/3840 Retail/JPRE images retain their baseline hashes |

Rasterizer fixtures use valid pre-clipped records and bounded synthetic
materials; they do not exhaust every texture/material, execute the complete
world-target-to-indicator submission chain, or prove runtime isolation.
Physical UAT must cover independent cameras/input, HUD and targeting ownership,
edge behavior, transitions, corruption, pacing and stable presentation.

The JPRE package retains the P02 wrapper revision and configuration. It also
includes the byte-identical original 3840 single-player comparison.
The observer records startup mode/surface results and process exit; the return
archive contains diagnostics, not game assets. PowerShell/Explorer delivery
still requires Windows acceptance. No live clipping detection is claimed.

Intro centering, previously reported clipping and one-pixel photo margins
remain recorded and unchanged. This work does not enable a public display
mode, monitor routing, spectator rendering or Unified Overlay.
