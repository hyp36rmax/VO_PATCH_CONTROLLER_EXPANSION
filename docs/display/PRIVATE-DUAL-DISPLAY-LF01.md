# D04-P02B-LF01 launcher and collection correction

> Historical engineering record. Findings and pending tests below belong to the
> named checkpoint; they are not a current release checklist. The
> [DUX specification](DUX-V1.0.md) defines the display contract, including the
> F04B complete-presentation Mirror amendment.

Previous HEAD: `701836ff28f3596e135e4297756509b4b4f46b30`.
Physical P02B result: launch/elevation and compression errors; no dual-display
acceptance result can be inferred from this attempt.

## Elevation investigation

**VERIFIED packaging defect:** the original `DISPLAY-SETUP.exe` is i386 with no
manifest resource. It is the first executable started by the dual launcher, with
`--list`, output/error redirection, and its game directory as working directory.
The subsequent stages are assignment UI, then the already-manifested asInvoker
observer, which uses ordinary CreateProcess to start the unchanged game.

Windows installer detection applies to unmanifested 32-bit programs and considers
names containing "setup". Its elevation request is compatible with the reported
failure on redirected process creation. See [Microsoft's UAC architecture](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/architecture).

**NEEDS VALIDATION:** the original report lacks process-stage/native-error logs,
so the exact failing operation on that PC and any per-machine compatibility flags
cannot be proven retrospectively. Installer detection at `DISPLAY-SETUP.exe --list`
is the strongest supported explanation, not a claimed Windows reproduction.
No registry/compatibility settings were changed. Discovery reads display data and
writes only a local INI; it does not install software or change desktop modes.

The corrected utility is `DISPLAY-ASSIGN.exe`, with resource type 24 / ID 1
specifying `requestedExecutionLevel="asInvoker"`, `uiAccess="false"`. New process
logging records stage, executable, arguments, working directory, exit code,
exception chain, HRESULT and native Win32 error code. No RunAs verb, administrator
request or compatibility override is introduced.

## Compression root cause and correction

**VERIFIED dependency defect:** the collector loaded only
`System.IO.Compression.FileSystem`, then referenced `ZipArchiveMode` from
`System.IO.Compression`. That assembly was not explicitly loaded, matching the
reported missing-type error. [Microsoft's enum documentation](https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.ziparchivemode)
identifies its owning assembly.

The collector now copies logs before any compression call and loads both
assemblies explicitly. `CreateFromDirectory` avoids the early enum expression;
archive entry counts are checked before replacing the completed ZIP. If loading
or compression fails, the obvious `RETURN-THIS-D04-P02B-LF01` folder retains
byte-preserving copies, a compression-status file and previous collected runs.
Original logs are not deleted. Shell selection failures do not invalidate saved
evidence. The collector runs after the launch attempt/session, so compression
cannot prevent startup.

## Validation boundaries

| Check | Status |
|---|---|
| Manifest embedded as type 24 / ID 1; asInvoker | VERIFIED by PE inspection |
| Assignment utility i386 build | VERIFIED |
| Renderer/wrapper/game/controller/observer bytes preserved | VERIFIED by comparison with P02B |
| Package integrity and relocated extraction | VERIFIED on host; spaces/non-ASCII path |
| Missing compression dependencies / ZIP failure | Host contract and four fallback-model cases passed; not PowerShell execution |
| Existing Retail/JPRE/controller suite | Passed; GUI internally skipped for missing Tk; CI-only tree check skipped |
| Ordinary-user Windows execution | NEEDS VALIDATION |
| CMD/Terminal/Windows PowerShell execution | NEEDS VALIDATION; unchanged quoted executable-relative CMD entry points |
| Actual dual-monitor gameplay and lifecycle | NEEDS VALIDATION |

No Windows runtime is available on this build host. The next action is one normal,
non-administrator Windows session with the corrected ZIP. Return the automatically
selected `RETURN-THIS-D04-P02B-LF01.zip`, or the same-named folder if compression
is unavailable. No renderer/controller change, public push or D04-P03 work is included.
