param([ValidateSet('single','dual')][string]$Entry = 'single')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, 'Local\VirtualOnPrivateDisplayUAT')
$owned = $false
$stage = 'Acquire session'
try {
    try { $owned = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { throw 'Another private test session is running.' }
    if (Get-Process -Name v_on -ErrorAction SilentlyContinue) { throw 'Virtual-On is already running.' }
    $status = Join-Path $root 'launch-status.txt'
    "Entry: $Entry; settings remain authoritative`r`nStarted: $(Get-Date -Format o)" | Set-Content -LiteralPath $status
    $stage = 'Verify package'
    $manifest = Get-Content -LiteralPath (Join-Path $root 'package-manifest.json') -Raw | ConvertFrom-Json
    foreach ($item in $manifest.files.PSObject.Properties) {
        if ($item.Name -like 'profiles/*' -and -not (Test-Path -LiteralPath (Join-Path $root $item.Name))) { continue }
        if ((Get-FileHash -LiteralPath (Join-Path $root $item.Name) -Algorithm SHA256).Hash -ne $item.Value) { throw "Package integrity failed: $($item.Name)" }
    }
    $game = Join-Path $root 'game'
    $stage = 'Select display mode and aspect'
    $setup = Start-Process -FilePath (Join-Path $game 'DISPLAY-MODES.exe') -WorkingDirectory $game -Wait -PassThru -RedirectStandardOutput (Join-Path $root 'selection.txt') -RedirectStandardError (Join-Path $root 'selection-errors.txt')
    if ($setup.ExitCode -eq 2) { 'Setup cancelled; game not launched.' | Add-Content -LiteralPath $status; return }
    if ($setup.ExitCode -ne 0) { throw 'Display setup failed.' }
    $selection = Get-Content -LiteralPath (Join-Path $root 'selection.txt') | Where-Object { $_ -match '^SELECT ' } | Select-Object -Last 1
    if ($selection -notmatch '^SELECT mode=([0-2]) profile=([0-4]) desktop=(-?\d+,-?\d+,\d+,\d+) fallback=(\d+) ') { throw 'Invalid display selection result.' }
    $mode = [int]$Matches[1]; $profile = [int]$Matches[2]; $desktop = $Matches[3]
    $selection | Add-Content -LiteralPath $status
    $names = @('original','wide','ultrawide','superwide','dual')
    $source = Join-Path $root ('profiles\' + $names[$profile] + '.exe')
    $record = Get-Content -LiteralPath (Join-Path $root 'build-record.json') -Raw | ConvertFrom-Json
    $chosen = $record.profiles | Where-Object { $_.profile -eq $names[$profile] }
    "Selected internal rendering: $($chosen.internal -join 'x'); expected from verified executable" | Add-Content -LiteralPath $status
    Copy-Item -LiteralPath $source -Destination (Join-Path $game 'v_on.exe') -Force
    if ((Get-FileHash -LiteralPath (Join-Path $game 'v_on.exe') -Algorithm SHA256).Hash -ne $chosen.sha256) { throw 'Selected executable integrity failed.' }
    $env:VO_DUAL_DISPLAY = $(if ($mode -eq 0) {'0'} else {'1'})
    $env:VO_PRIVATE_DISPLAY = '1'
    $env:VO_DESKTOP = $desktop
    $stage = 'Run game with external window observer'
    $process = Start-Process -FilePath (Join-Path $root 'MOVIE-OBSERVER.exe') -WorkingDirectory $root -Wait -PassThru
    "Observer exit: $($process.ExitCode); Finished: $(Get-Date -Format o)" | Add-Content -LiteralPath $status
    if ($process.ExitCode -ne 0) { throw "Observer returned $($process.ExitCode)" }
} catch {
    "Stage: $stage`r`n$($_ | Out-String)" | Set-Content -LiteralPath (Join-Path $root 'launch-error.txt')
    Write-Host "Launch could not complete: $_"
} finally {
    $env:VO_DUAL_DISPLAY = '0'; $env:VO_PRIVATE_DISPLAY = '0'; $env:VO_DESKTOP = ''
    if ($owned) {
        try { & (Join-Path $root 'Collect-Modes.ps1') } finally { $mutex.ReleaseMutex() }
    }
    $mutex.Dispose()
}
