param([ValidateSet('dual','control')][string]$Mode = 'dual')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, 'Local\VirtualOnPrivateDisplayUAT')
$owned = $false
$stage = 'Acquire session'
function Start-RecordedProcess {
    param([string]$Executable, [string]$Directory, [string[]]$Arguments = @(), [string]$Output = '', [string]$ErrorOutput = '')
    $script:stage = "Launch: $Executable; arguments: $($Arguments -join ' '); cwd: $Directory"
    $script:stage | Add-Content -LiteralPath $status
    $parameters = @{ FilePath=$Executable; WorkingDirectory=$Directory; Wait=$true; PassThru=$true; ErrorAction='Stop' }
    if ($Arguments.Count) { $parameters.ArgumentList = $Arguments }
    if ($Output) { $parameters.RedirectStandardOutput = $Output }
    if ($ErrorOutput) { $parameters.RedirectStandardError = $ErrorOutput }
    # No RunAs verb, elevation request, or compatibility override.
    $process = Start-Process @parameters
    "Exit code: $($process.ExitCode)" | Add-Content -LiteralPath $status
    return $process
}
try {
    try { $owned = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { throw 'Another private test session is running. Close it first.' }
    if (Get-Process -Name v_on -ErrorAction SilentlyContinue) { throw 'Virtual-On is already running. Close it before launching this test.' }
    $folder = Join-Path $root $Mode
    $game = Join-Path $folder 'game'
    $status = Join-Path $folder 'launch-status.txt'
    "Mode: $Mode`r`nStarted: $(Get-Date -Format o)" | Set-Content -LiteralPath $status
    $stage = 'Verify package integrity'
    $manifest = Get-Content -LiteralPath (Join-Path $root 'package-manifest.json') -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        if ($manifest.mutable_files -contains $entry.Name) { continue }
        $path = Join-Path $root $entry.Name
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.Value) { throw "Package integrity failed: $($entry.Name)" }
    }
    $env:VO_DUAL_DISPLAY = '0'
    if ($Mode -eq 'dual') {
        $setup = Join-Path $game 'DISPLAY-ASSIGN.exe'
        $list = Start-RecordedProcess -Executable $setup -Arguments @('--list') -Directory $game -Output (Join-Path $folder 'displays.txt') -ErrorOutput (Join-Path $folder 'display-errors.txt')
        if ($list.ExitCode -ne 0) { throw 'Display discovery failed. Diagnostics will be collected automatically.' }
        $select = Start-RecordedProcess -Executable $setup -Directory $game -Output (Join-Path $folder 'assignment.txt')
        if ($select.ExitCode -ne 0) { 'Display selection cancelled or failed; game was not launched.' | Add-Content -LiteralPath $status; return }
        $env:VO_DUAL_DISPLAY = '1'
    }
    $observer = Start-RecordedProcess -Executable (Join-Path $folder 'OBSERVER.exe') -Directory $folder
    "Observer exit: $($observer.ExitCode)`r`nFinished: $(Get-Date -Format o)" | Add-Content -LiteralPath $status
} catch {
    $failure = @("Stage: $stage", ($_ | Out-String), "Exception: $($_.Exception.GetType().FullName)")
    $exception = $_.Exception
    while ($exception) {
        $failure += "Exception detail: $($exception.Message); HResult: $($exception.HResult)"
        if ($exception -is [System.ComponentModel.Win32Exception]) { $failure += "NativeErrorCode: $($exception.NativeErrorCode)" }
        $exception = $exception.InnerException
    }
    $failure | Set-Content -LiteralPath (Join-Path $root 'launch-error.txt')
    Write-Host "Test could not complete: $_"
} finally {
    $env:VO_DUAL_DISPLAY = '0'
    if ($owned) {
        try { & (Join-Path $root 'Collect-Results.ps1') } finally { $mutex.ReleaseMutex() }
    }
    $mutex.Dispose()
}
