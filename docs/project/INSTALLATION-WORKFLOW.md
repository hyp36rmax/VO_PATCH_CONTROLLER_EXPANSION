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
`v-on-patcher.exe` and `_internal` structure. Its first GitHub Windows execution
and final integrated UAT remain pending. This is separate from the published
Controller Expansion pre-release; no Experience release is announced.
