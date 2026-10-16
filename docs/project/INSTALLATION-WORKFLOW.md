# Installation workflow

VO PATCH EX preserves Pairomaniac's ISO/file selection, patch options, Apply
patches, Restore original, backups, validation and error handling. Use the
original supported disc image/files. No separate installer or mandatory game
launcher is required.

For a new installation, use INSTALL with the original disc image. For an existing
installation, select its original `v_on.exe`. If already patched, use **Restore
original** first; applying over a patched executable is rejected. Keep the entire
Windows package together, including `_internal`. Launch the installed `v_on.exe`
normally after Apply.

## Install and upgrade

The complete patcher retains **INSTALL**, **GAME FILE**, **ESSENTIAL PATCHES**,
**EXTRA PATCHES** and **ADD-ONS**. For disc-image installation, select the `.cue`
sheet with its referenced data files available, choose the destination and use
**Install game**; **Rip soundtrack** is available through the upstream workflow.
For an existing original installation, select `v_on.exe` in GAME FILE. See the
[upstream installation guide](../PATCHER.md#installing-from-a-disc-image).

Essential patches are automatic; choose Extra patches, then **Apply patches**.
Retain XInput gamepad support for expanded controllers and **Disable menu bar
(Extras menu on F11)** for diagnostic controls. Optional add-ons retain their
existing Install actions and requirements; consult the [patcher guide](../PATCHER.md)
before adding or replacing a presentation component.

To upgrade, close the game and back up the installation and saved settings.
Use the previous patcher's **Restore original**, then Apply patches with the new
complete package. Do not copy individual patched game files over an existing
installation. Restore preserves unrelated files and reports modified owned files
it will not overwrite. Keep original backups until the new installation is accepted.
If restoration cannot complete, recover your backup rather than patching over a
partial installation. Integrated patch recipes are verified for Retail/JPRE;
upstream recognition of another edition is not equivalent expansion validation.

## Game configuration

Fresh defaults use **16:9 Single Display**. The existing Native widescreen checkbox
is retained; explicitly disabling it starts from original 4:3 unless a saved
Display preference overrides that choice. There is no additional expansion checkbox.

**F5 → Graphic Settings → Display...** selects Single Display, Dual Display —
Versus or Dual Display — Mirror, monitor assignments and game aspect ratio.
OK saves for next launch; Cancel discards pending edits. Dual Versus presents
independent player views; Dual Mirror duplicates the complete primary presentation,
including both Local VS views. Movie presentation retains its established policy.
Controller selection and Custom remapping remain in F7.

Restore original restores owned installation files and retains saved preferences,
diagnostics and unrelated files. Modified runtime files are preserved and reported.
No administrator privileges or manual configuration edits are required.

## Validation boundary

Automated Retail/JPRE Apply/Restore and configuration tests cover transaction
behavior. Normal Windows GUI use, display presentation, movie framing, scaling
and physical hardware acceptance remain separate checks. Private packages include
patch data and redistributables, never original game executables or assets.

## Experience build preparation

The canonical [VO PATCH EX Build workflow](https://github.com/hyp36rmax/VO_PATCH_EX/actions/workflows/build.yml)
is prepared to produce a complete Experience Windows ZIP with the existing
`v-on-patcher.exe` and `_internal` structure. Complete hosted Windows packaging
and final integrated UAT remain acceptance gates. This is separate from the published
Controller Expansion pre-release; no Experience release is announced.
