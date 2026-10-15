# F01-P04-F01: Display preference persistence

The F01-P04 transaction interpreted `WritePrivateProfileStringW(NULL, NULL,
NULL, temp)` as an ordinary Boolean write result. Microsoft documents zero for a
cache flush as well as failure. With zero returned after successful field writes,
the old code skipped replacement, deleted the temporary file and reported failure.
The original API double returned one for flushing, concealing this defect.

Reference: [Microsoft WritePrivateProfileStringW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-writeprivateprofilestringw).

The corrected transaction invalidates the INI cache without interpreting that
return as a write verdict, then opens the temporary file and checks
`FlushFileBuffers` before same-directory replacement. Every actual field write,
conversion, open, flush, close and replacement is checked. Errors leave the
previous preferences intact. No renderer, controller, installation or configuration
authority changes are involved.

## Configuration and permissions

The authoritative location remains `player-displays.ini` beside the launched game
executable, resolved from `GetModuleFileNameW(NULL, ...)`, never the working directory.
The transaction copies an existing INI to preserve unknown keys. New files use the
same location. Missing directories fail explicitly; no alternate settings directory
or automatic migration is introduced.

All file operations use the current user's ordinary process token. No elevation,
ACL changes or permission bypass is requested. Creating the same-directory temporary
file tests directory writability; actual writes and replacement test file access.
Read-only files and denied directories remain protected. Actual ACLs on the user's
Windows installation have not been inspected; the reported message alone cannot
establish them. The corrected build records the failing operation/error if needed.

## Evidence

`diagnostics/display-save.log` is a bounded, local-only transaction trace containing
requested mode, validation result, resolved configuration location, file/directory
attributes, operation result and captured Windows error. An attributes value of
4294967295 means unavailable. It is excluded from exported archives because paths
may contain personal information. The normal numeric event export includes
`save_stage` and `winerror`. The failure dialog also displays these values.

| Stage | Operation |
|---|---|
| 0 | Validation / transaction entry |
| 1 | Parent path resolution |
| 2 | Create same-directory temporary file |
| 3 | Inspect/copy existing configuration |
| 4 | Write requested mode |
| 5 | Write aspect ratio |
| 6 | Convert/write primary monitor ID |
| 7 | Convert/write secondary monitor ID |
| 8 | INI cache flush: raw zero is permitted, not an error verdict |
| 9 | Open temporary file for durable flush |
| 10 | FlushFileBuffers |
| 11 | Close temporary file handle |
| 12 | Atomic replacement: successful commit |

OK validates and commits pending preferences; Cancel does not call the transaction.
Saved preferences take effect through the existing next-launch reader/selector,
not by reinitializing the running game.

## Regression evidence

The production transaction is extracted into a native sanitized API-double test.
Using the documented zero-return flush reproduces the original failure, then passes
with the correction. Coverage includes all three modes, four aspects, new/existing
files, spaces/Unicode paths, every transaction operation failing, missing/denied
directories, read-only files and preservation of unrelated settings. The production
reader and launch selector recover every committed mode/aspect. Existing pending/
Cancel, fallback, F5 bridge and startup tests remain unchanged and pass.

These tests establish the control-flow defect and correction. Real Win32 INI/file
behavior and the corrected dialog still require consolidated physical Windows UAT.
