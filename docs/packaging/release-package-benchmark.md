# Release package benchmark

Status: VERIFIED local archive measurements and regression results; Windows hardware acceptance NEEDS VALIDATION.

## Published inputs

| Package | Release date (UTC) | Source commit | Archive |
|---|---|---|---|
| Upstream v0.17.2 | 2026-09-28 21:45 | af0dc5efc782b363ad08f9facee7ac92a1ff356d | v-on-patcher-v0.17.2-win.zip |
| VO PATCH EX v0.18.0-experience.1 | 2026-10-16 05:34 | 8afce868f70f8d82ecb21f7ea083d8f5b2f07f07 | VO-PATCH-EX-Experience.zip |

These are downloaded release assets, not estimates from source size. The maintenance branch starts at Experience d2f65f2e96386520a381e4a8aa10e6cf17bf34ae; the published application's source remains the commit above. No release asset is replaced.

SHA-256:

- Upstream: `d44f201148c6bf924b596fe4549306047ac8e262c5f9dbfb419fd7d14a6d1e5c`
- Current: `d9afa87394bc3b69e596c942064dd2be6b489d67f3cfdc61e265600d6c05f4d7`
- Locally assembled candidate: `d031a1dddb3a2e55404a12bf0ddb57ce6e7fc549b9f66efbd23c0c2b2bdd20ee`

## Measurements

All sizes are bytes. MB means decimal MB; upstream is 15.65 MB or 14.93 MiB.

| Metric | Upstream | Current | Optimized local candidate |
|---|---:|---:|---:|
| ZIP | 15,650,198 | 50,084,530 | 43,627,108 |
| Extracted | 33,300,871 | 81,412,217 | 74,864,153 |
| Files | 1,156 | 1,208 | 1,208 |
| DLLs | 15 | 29 | 29 |
| Python extension modules (.pyd) | 23 | 46 | 46 |
| Launcher executable | 215,008 | 215,008 | 215,008 |
| Standalone debug symbol files | 0 | 0 | 0 |
| Identical-content additional copies, raw | 86,971 | 26,294,389 | 26,294,389 |
| Identical-content additional copies, compressed | 18,714 | 13,344,536 | 13,344,536 |
| Essential documentation/licenses, raw | 36,874 | 153,761 | 153,761 |
| ZIP headers/directory overhead | 178,058 | 195,436 | 195,436 |

Compressed reduction: **6,457,422 bytes (12.89%)**. Extracted reduction: **6,548,064 bytes (8.04%)**. No files are deleted. Remaining compressed difference from upstream: **27,976,910 bytes**. Outer ZIP timestamps, writer and manifest newline convention can change the final archive hash/size across hosts; these figures identify the local candidate above.

## Causes and dependency decisions

| Component | Current compressed | Optimized compressed | Decision |
|---|---:|---:|---|
| Catalog and sparse recipes | 20,677,971 | 14,220,582 | SAFE lossless compression; all 512 decoded recipe hashes unchanged |
| Installed Python runtime | 13,324,627 | 13,324,627 | REQUIRED independent installed runtime |
| Other display payload | 343,039 | 343,039 | REQUIRED display startup, settings and presentation |
| Controller helper | 9,830 | 9,830 | REQUIRED controller functionality |
| Additional top-level notices/readme | 21,207 | 21,207 | REQUIRED attribution and usage information |

The main growth is sparse patch recipes and a second Python runtime. The patcher runtime belongs to the portable patcher. The installed runtime is copied beside the game and supports normal launch, display selection, monitor discovery, movie geometry and diagnostics after the patcher folder is removed. Identical hashes do not make these copies removable. The launcher itself has not grown.

The [file-by-file matrix](release-package-file-comparison.csv) records raw and compressed sizes, purpose and opportunity for every filename. Categories A–H and J classify file roles; category I (duplicate/obsolete) is an overlapping content-hash analysis, quantified above. No obsolete file was established. Runtime groups marked REQUIRED are preserved dependency sets, not proof that each individual Python module is directly imported by this application. Unknown individual dependency edges remain UNKNOWN.

| Candidate | Classification | Finding |
|---|---|---|
| DEFLATE to LZMA inside recipes.zip | SAFE | Existing bundled Python includes the codec; no extra download or runtime file; verify on Windows before merge |
| Delete second runtime | REQUIRED | Breaks independently installed game startup |
| Prune Python/Tk/OpenSSL/SQLite modules | CONDITIONAL | Requires transitive import and Windows runtime coverage; not removed |
| Remove inherited _ctypes_test.pyd | CONDITIONAL | Test module, but broad upstream runtime trimming is outside the proven dependency boundary |
| Separate symbols ZIP | UNSUITABLE | No shipped standalone symbols materially contribute |
| Store recipes uncompressed inside outer ZIP | UNSUITABLE | Similar download size but increases extracted storage substantially |
| Drop licensing, diagnostics or profiles | REQUIRED | Preserved without changes |

## Build audit

The launcher uses MSVC `/O1 /MT /W4 /WX`, Windows subsystem, embedded manifest and user32; no `/Zi` or `/DEBUG`. Controller/helper builds use optimized native code; the Display helper uses `-O2 -Wall -Wextra -Werror`, user32/gdi32 and timestamp suppression. The pinned cnc-ddraw wrapper uses `-O2`, `-s -static -shared` and the existing Windows libraries. No security or runtime-check options change.

Python 3.12.10 is bundled, with isolated module search paths and certifi 2026.07.22. Upstream bundle assembly excludes tests, idlelib, turtledemo, ensurepip, venv, lib2to3 and site-packages from its standard-library ZIP, and filters `_test*` extensions. The installed runtime copies the supported DLL/extension set. Tcl runtime resources and certificates are functional dependencies, not build objects. No PDB/OBJ/ILK release clutter was identified. Original game assets remain excluded.

The existing build workflow assembles the normal upstream Windows launcher plus Experience payload. `package_normal.py` now compresses recipes before writing package hashes. No folders, player actions, configuration system or dependency installers are introduced. Optional locally generated diagnostic logs remain user data, not release content.

## Reproduction and validation

```sh
python tools/experience/test_package_compression.py
python tools/experience/optimize_package.py ORIGINAL_DIRECTORY NEW_CANDIDATE_DIRECTORY
python tools/experience/test_normal_package.py NEW_CANDIDATE_DIRECTORY
python tools/experience/test_normal_install.py NEW_CANDIDATE_DIRECTORY RETAIL_GAME_DIRECTORY JPRE_GAME_DIRECTORY
```

Use an untouched extracted published package. The optimizer verifies complete manifest coverage and all source hashes before copying; it preserves the original. Each recipe is checked before and after compression, using stable entry ordering/timestamps. A failed catalog check leaves the original recipe archive untouched. No recipe, executable, DLL or installed runtime payload changes; only recipes.zip and the package checksum manifest differ.

VERIFIED: all 33 baseline checks; Retail/JPRE Apply, Restore, reapply, selected options, patch-over refusal, failure rollback and unrelated/modified-file preservation; package manifest/license/runtime completeness; no original game assets; compression repeatability and corrupt-index refusal.

The dedicated read-only Windows workflow downloads the hash-pinned original, prepares the candidate, exercises all 512 recipes through the shipped interpreter, runs the upstream launcher selfcheck and uploads the candidate for review. It cannot publish releases. Its result is reported on the pull request.

NEEDS VALIDATION on physical Windows hardware: interactive patcher launch, XInput/HID discovery, all controller profiles and P1/P2 assignments, bindings, single/dual/mixed-display behavior, settings persistence, networking and portable operation after installation. Byte-identical runtime preservation and automated tests do not substitute for those checks. No new hardware pass is claimed.

Rollback is to discard the unmerged branch/candidate; published artifacts and Experience remain unchanged. Future dependency pruning must have its own measured runtime evidence.
