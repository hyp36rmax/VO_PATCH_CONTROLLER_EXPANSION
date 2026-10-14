# Experience diagnostics and private G03 acceptance

The G03 coordinator is retained as prototype evidence, not the installation
workflow. See [G03A installation workflow](INSTALLATION-WORKFLOW.md) for the
normal patcher control and pending F-key integration.

G03 adds an external coordinator around the existing F04B display launcher.
Controller polling, camera ownership, renderer code, display selection, F-key
menus and G02 attribution remain unchanged. Windows acceptance is pending.

## Local collection

`tools/experience/session.py` prepares a private working copy, starts the existing
mode selector/observer, waits for shutdown and exports diagnostics. The legacy observer's unconditional `VO_DUAL_DISPLAY=1` override is removed in
the G03 build: Single must inherit `0` and dual modes `1` from the launcher.
This prevents the 3840×1080 Single profile from entering the dual-output path.
No service,
driver, administrator rights, network upload or game-process injection is used.

| Evidence | Source and interpretation |
|---|---|
| Experience/module versions | Pinned package revision, helper and wrapper hashes; game revision from verified preparation |
| Startup/shutdown | Flushed coordinator events and observer exit status; a stale session marker identifies an incomplete prior run |
| Module initialization | Preparation success and presence of selector/presentation/movie logs; log presence alone does not prove successful initialization |
| Controller discovery | Raw Input gamepad/joystick metadata and XInput capabilities every ten seconds, recorded only on change; interfaces may overlap |
| Player assignments | Numeric saved `1P/2P Device No.` settings; live physical ownership is not inferred |
| Display discovery | Active monitor dimensions from Windows metadata; saved monitor identity remains in the existing configuration authority |
| Mode/profile/fallback | Existing selector output and strict launch-result checks |
| Presentation transitions | Existing bounded wrapper trace, normally written at render-thread teardown; unavailable after some crashes |
| Movie lifecycle | External window-class appearance/visibility/disappearance observations and existing wrapper movie trace; not decoded-pixel or audio validation |
| Errors/recovery | Launch/observer status, nonzero game exit, failing HRESULT, strict-stop/fallback and missing-discovery events |

All diagnostic file I/O runs outside rendering and controller polling. No raw
controller state is sampled. The external observer uses the same ordinary process
launch and window enumeration mechanism, with free-form text output disabled.

| Level | Behavior |
|---|---|
| NORMAL | Default; changed discovery, startup/shutdown, bounded module projections and movie lifecycle events; periodic window dumps suppressed |
| DETAILED | Explicit `--level DETAILED`; bounded periodic window metadata and up to 256 projected rows per module at collection |
| DEVELOPMENT | Explicit `--level DEVELOPMENT`; the same privacy rules with up to 1,024 projected rows; no raw input capture |

Shared events rotate at 256 KiB with three backups. Input reads are bounded to
256 KiB per file (head and tail for larger logs); partial crash records are ignored.
Existing module logs have their own observer/trace bounds and three session
backups. Four timestamped exports plus the stable return ZIP are retained. A
failed export preserves raw logs and the previous successful ZIP. Flushed events
survive a process crash; power-loss durability is not guaranteed.

## Privacy and export interface

The stable Python interface for a future caller is
`diagnostics.event(root, name, numeric_fields)` and `diagnostics.export(root)`.
Only fixed event names and allowlisted integer/boolean fields are accepted.
No graphical overlay is implemented.

Export produces `VO-PATCH-EX-Diagnostics-YYYYMMDD-HHMMSS.zip` and an identical
`RETURN-THIS-VO-PATCH-EX-G03.zip`, containing exactly:

| File | Contents |
|---|---|
| `summary.json` | Verified-format revision/hashes, game edition, missing logs, errors and recovery events |
| `events.json` | Allowlisted event names and numeric fields across retained sessions |
| `module-logs.json` | Numeric projections of selector, presentation and observer logs |
| `configuration.json` | Allowlisted numeric mode, profile and controller settings |

No recursive directory export occurs. Free-form strings, usernames, absolute
paths, monitor/HID paths, device serials, credentials, raw inputs, executables and
game assets are excluded. Existing module logs/configurations remain local and
may retain identifiers required by those modules; they are not copied verbatim
into shared diagnostics. The G03 observer suppresses executable paths and window
text at its source. Missing logs are explicitly reported, never treated as PASS.

## Private package and preparation

The package requires 64-bit Windows and contains bundled Python, ordinary-user display/observer tools, the
unchanged validated helper/wrapper, notices and hash-checked sparse patch recipes.
It contains no original or generated game executable, original game DLL, movie,
texture, sound or other game resource. Recipes contain patch data, not playable
images. The original `dpctrl.dll` and `cpuid32.dll` come from the user's installation.

On first launch, a folder picker requests a pristine Retail or JPRE installation.
Preparation verifies the executable and required resources, copies them into the
private working directory, uses upstream's existing banner/credit writers and
builds five exact-hash profiles. Original resources and executable are never
modified. Retail and JPRE use separate extracted package copies. Generated files
are private test data and must not be committed or redistributed.

The three launchers select Single, Dual Versus or complete-presentation Mirror.
The existing session-only mode policy, strict dual failure handling, immutable
saved preferences and temporary fallback remain authoritative. Export is automatic
on return; `EXPORT-DIAGNOSTICS.cmd` retries it independently. The full twelve-item
Windows checklist is packaged as `READ-ME.txt` from `tools/experience/UAT.txt`.

## Validation boundary and ending credits

Host tests exercise all ten exact Retail/JPRE profile outputs, original executable/resource
backups and full Restore Original, read-only source installations, corrupted-profile rejection, export
privacy, rotation, failed-export recovery, crash records and lifecycle failures.
The existing 33-check runner and additional presentation, movie, preferences,
attribution and restore checks pass. Its native GUI entry is skipped on this host.
Windows PowerShell, discovery calls, runtime execution, controller ownership and
visual/audio behavior still require physical acceptance.

G03 rechecks the existing credit resource read-size tables: Retail offsets
`0x1fcec8/0x1fcecc`, JPRE `0x1f76d0/0x1f76d4`, growing from 144,512/9,288 bytes to
160,000/9,708 bytes. These are data-table sizes, not allocator bounds. They do not
resolve G02's inconsistent capacity comments or prove room for additional tiles.
The optional VO PATCH EX/hyp36rmax ending lines remain BLOCKED; original SEGA and
upstream credits remain exact. See [attribution and lineage](ATTRIBUTION-AND-LINEAGE.md).
