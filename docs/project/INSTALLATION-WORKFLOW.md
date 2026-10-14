# Installation workflow — G03A

VO PATCH EX uses Pairomaniac's patcher for installation. Keep the original
ISO/file selection, patch options, Apply patches, Restore original, backups,
validation and error handling. No separate installer or mandatory Experience
launcher is part of this workflow. Controller Expansion is the integration
reference; G03A leaves these patcher methods unchanged.

For a new installation, use the patcher's INSTALL section with the original
supported disc image. For an existing installation, select the original
`v_on.exe`. An already patched installation must use **Restore original** before
applying VO PATCH EX. Modified executables are not accepted as pristine inputs.
Launch the patched game normally through `v_on.exe`.

## Default and configuration boundary

A fresh installation defaults to single-display 16:9, using the existing
1920×1080 patch. Display mode and rendering-profile selection belong in the game,
not in new installation controls. The F-key functions will be reviewed separately.

The existing Display implementation generates different executable layouts and
uses a temporary external selector for presentation configuration. It does not
yet connect the expanded display settings to the in-game F-key menus. Completing
that configuration path is a prerequisite for integrated three-mode acceptance.
The validated Display implementations remain preserved in this branch; their
presence does not mean the normal patcher currently installs all three modes.

## Private installation control

The G03A Windows control uses the upstream launcher and bundled Python/Tk runtime,
the current patcher, and its Controller Expansion and network helpers. It contains
no game files, external Experience coordinator, profile preparer or mode selector.
It verifies the normal installation path and default patch generation, not full
Display runtime integration or Windows physical acceptance.

The earlier G03 package and its diagnostic coordinator are retained as prototype
and recovery evidence. They are superseded as an installation workflow and must
not be presented as a required installer or launcher.

Acceptance still requires Windows execution. Automated Retail/JPRE patch and
restore checks cannot establish GUI interaction or physical display behavior.
No F-key assignments, runtime mode switching, renderer changes or Unified Overlay
work are included in G03A.
