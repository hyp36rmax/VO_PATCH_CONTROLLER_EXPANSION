$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, 'Local\VirtualOnPrivateDisplayUAT')
$owned = $false
try {
    try { $owned = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $owned = $true }
    if (-not $owned) { throw 'Another private test session is running.' }
    if (Get-Process -Name v_on -ErrorAction SilentlyContinue) { throw 'Virtual-On is already running.' }
    "Started: $(Get-Date -Format o)" | Set-Content -LiteralPath (Join-Path $root 'launch-status.txt')
    $manifest = Get-Content -LiteralPath (Join-Path $root 'package-manifest.json') -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        if ($manifest.mutable_files -contains $entry.Name) { continue }
        if ((Get-FileHash -LiteralPath (Join-Path $root $entry.Name) -Algorithm SHA256).Hash -ne $entry.Value) { throw "Integrity failure: $($entry.Name)" }
    }
    # External observer opens its log first, then launches the unchanged game normally.
    $process = Start-Process -FilePath (Join-Path $root 'MOVIE-OBSERVER.exe') -WorkingDirectory $root -Wait -PassThru
    "Observer exit: $($process.ExitCode); finished: $(Get-Date -Format o)" | Add-Content -LiteralPath (Join-Path $root 'launch-status.txt')
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $root 'launch-error.txt')
    Write-Host "Observation could not finish: $_"
} finally {
    if ($owned) {
        try { & (Join-Path $root 'Collect-Results.ps1') } finally { $mutex.ReleaseMutex() }
    }
    $mutex.Dispose()
}
