# VO PATCH EX branding assets

Original logo and icon: SirRockEmSockEm. `VONPatcherLogo1.png` is preserved
byte-for-byte. `EX-approved.png` is the transparent PNG supplied by the project
maintainer for B01; the supplied file is retained unchanged. Its transparent RGB
pixels may contain checkerboard colors, but alpha controls their visibility.

`VOPatchEXLogo.png` composites the original at native size and the approved EX,
proportionally scaled to 650 pixels wide, at (2020, 480), beneath PATCHER.
The 2715×716 transparent canvas avoids clipping. No lettering was regenerated.

Embed with `python3 tools/assets.py --logo-only` (Pillow required). This uses the
existing 192-pixel PNG pipeline and preserves both the embedded icon and icon.ico.
The patcher displays the header at its existing DPI-scaled height. About uses text
attribution without repeating the logo. Physical Windows scaling acceptance is pending.
