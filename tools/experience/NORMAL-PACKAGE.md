# Private normal-launch Experience distribution

The package reuses the upstream Windows launcher and UI. `normal_install.py` binds
only the packaged Apply/Restore backend; the repository's original patcher remains
unchanged. Players select their original game files/ISO, Apply, then launch the
installed game normally. Existing patched installations require Restore Original.

## Rebuild

Use the existing project Python environment and NASM. Build the controller helper
with its established build process. Generate the option catalog:

```
python tools/experience/build_catalog.py CATALOG RETAIL_GAME_FOLDER JPRE_GAME_FOLDER
```

Compile `tools/dual_display/f5_dialog.c` as a 32-bit Windows shared library with
LLVM-MinGW, `-O2 -Wall -Wextra -Werror -Wno-unused-function`, exports without stdcall
suffixes (`-Wl,--kill-at`), and user32/gdi32. Use `--no-insert-timestamp` for
reproducibility. This produces `vodisplay.dll`.

Build the existing pinned wrapper using `tools/dual_display/build_wrapper.py`,
`--mode-aware`, `--profiles CATALOG/game_profiles.h`, and the 32-bit compiler and
resource compiler. The wrapper source pin is checked by the builder.

```
python tools/experience/package_normal.py OUTPUT UPSTREAM_WINDOWS_BUNDLE CATALOG WRAPPER_BUILD VODISPLAY_DLL
python tools/experience/test_normal_package.py OUTPUT
python tools/experience/test_normal_install.py OUTPUT RETAIL_GAME_FOLDER JPRE_GAME_FOLDER
python tools/experience/test_catalog_identity.py CATALOG RETAIL_GAME_FOLDER JPRE_GAME_FOLDER
```

The established local G03 presentation INI supplies the private windowed wrapper
configuration. The upstream Windows bundle supplies the launcher, Python/Tk runtime
and licenses. These are required local build inputs, not game assets. The assembler
requires a new output directory and records all package file hashes.

Catalog recipes are sparse patch data; no original/patched game executable or disc
image is shipped. The player does not need Python, NASM, compiler, administrator
privileges, manual configuration editing or a separate game launcher.

## Ownership

The adapter tracks runtime files and their prior contents in `.vo-ex-backup`.
Apply verifies all payload hashes before changing the installation. Restore first
uses upstream restoration, then restores owned runtime files. It never recursively
deletes arbitrary game directories. Unrelated files and changed runtime files are
preserved; changed owned files retain their recovery record for review. Ordinary
write failures are transactionally tested; power-loss recovery is not claimed.

Runtime Python uses `-B` to avoid generating bytecode in the installation. Saved
Display preferences, logs and exported archives remain user data after Restore.

## Acceptance

Run the full existing suite plus the F5/startup/installation/presentation/diagnostic
regressions. Physical Windows UAT must separately establish normal launch,
configuration/relaunch, real monitors, F4/F7/controller behavior, movies, clean exit
and Apply/Restore. Automated results must not be presented as physical validation.
