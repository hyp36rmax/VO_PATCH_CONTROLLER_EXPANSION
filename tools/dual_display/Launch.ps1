param([ValidateSet('dual','control')][string]$Mode = 'dual')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, 'Local\VirtualOnPrivateDisplayUAT')
$owned = $false
try {
    try { $owned = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { throw 'Another private test session is running. Close it first.' }
    if (Get-Process -Name v_on -ErrorAction SilentlyContinue) { throw 'Virtual-On is already running. Close it before launching this test.' }
    $folder = Join-Path $root $Mode
    $game = Join-Path $folder 'game'
    $status = Join-Path $folder 'launch-status.txt'
    "Mode: $Mode`r`nStarted: $(Get-Date -Format o)" | Set-Content -LiteralPath $status
    $manifest = Get-Content -LiteralPath (Join-Path $root 'package-manifest.json') -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        if ($manifest.mutable_files -contains $entry.Name) { continue }
        $path = Join-Path $root $entry.Name
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.Value) { throw "Package integrity failed: $($entry.Name)" }
    }
    foreach ($name in @('D04-P02B-presentation.log')) {
        $old = Join-Path $game $name
        if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old }
    }
    $env:VO_DUAL_DISPLAY = '0'
    if ($Mode -eq 'dual') {
        $setup = Join-Path $game 'DISPLAY-SETUP.exe'
        $list = Start-Process -FilePath $setup -ArgumentList '--list' -WorkingDirectory $game -Wait -PassThru -RedirectStandardOutput (Join-Path $folder 'displays.txt') -RedirectStandardError (Join-Path $folder 'display-errors.txt')
        if ($list.ExitCode -ne 0) { throw 'Display discovery failed. Diagnostics will be collected automatically.' }
        $select = Start-Process -FilePath $setup -WorkingDirectory $game -Wait -PassThru -RedirectStandardOutput (Join-Path $folder 'assignment.txt')
        if ($select.ExitCode -ne 0) { 'Display selection cancelled or failed; game was not launched.' | Add-Content -LiteralPath $status; return }
        $env:VO_DUAL_DISPLAY = '1'
    }
    $observer = Start-Process -FilePath (Join-Path $folder 'OBSERVER.exe') -WorkingDirectory $folder -Wait -PassThru
    "Observer exit: $($observer.ExitCode)`r`nFinished: $(Get-Date -Format o)" | Add-Content -LiteralPath $status
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $root 'launch-error.txt')
    Write-Host "Test could not complete: $_"
} finally {
    $env:VO_DUAL_DISPLAY = '0'
    if ($owned) {
        & (Join-Path $root 'Collect-Results.ps1')
        $mutex.ReleaseMutex()
    }
    $mutex.Dispose()
}
