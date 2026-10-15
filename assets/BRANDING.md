# VO PATCH EX branding assets

Original logo and icon: SirRockEmSockEm. `VONPatcherLogo1.png` is preserved
byte-for-byte. `EX-approved.png` is the transparent PNG supplied by the project
maintainer for B01; the supplied file is retained unchanged. Its transparent RGB
pixels may contain checkerboard colors, but alpha controls their visibility.

`VOPatchEXLogo.png` composites the original at native size and the approved EX,
proportionally scaled to 760 pixels wide, at (1944, 447), beneath PATCHER.
The 2715×723 transparent canvas avoids clipping. No lettering was regenerated.

Embed with `python3 tools/assets.py --logo-only` (Pillow required). This uses the
existing 212-pixel PNG pipeline and preserves both the embedded icon and icon.ico.
The header is 106 logical pixels tall to preserve the original V-ON scale.
EX is 97% of the 783-pixel PATCHER capsule width, centered with slight overlap. About uses text
attribution without repeating the logo. Physical Windows scaling acceptance is pending.
