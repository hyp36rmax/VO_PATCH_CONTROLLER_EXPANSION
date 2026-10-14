# Collect diagnostics only; never collect game assets or memory contents.
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $root = $PSScriptRoot
    $zip = Join-Path $root 'RETURN-THIS-D04-P02B.zip'
    $temporary = Join-Path $root 'RETURN-THIS-D04-P02B.new.zip'
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
    $files = @('build-record.json')
    $records = @('Missing logs are not successful results. Unrun modes are expected.')
    foreach ($mode in @('dual','control')) {
        foreach ($name in @('launch-status.txt','displays.txt','display-errors.txt','assignment.txt','RETURN-THIS-D01-3840.log','game\D04-P02B-presentation.log','game\player-displays.ini','game\ddraw.ini')) {
            $relative = "$mode\$name"
            $exists = Test-Path -LiteralPath (Join-Path $root $relative)
            $records += "$relative present: $exists"
            if ($exists) { $files += $relative }
        }
        foreach ($name in @('v_on.exe','ddraw.dll','vontanita.dll')) {
            $path = Join-Path $root "$mode\game\$name"
            $records += "$mode/$name SHA256: $((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash)"
        }
    }
    if (Test-Path -LiteralPath (Join-Path $root 'launch-error.txt')) { $files += 'launch-error.txt' }
    $records | Set-Content -LiteralPath (Join-Path $root 'collection-status.txt') -Encoding UTF8
    $files += 'collection-status.txt'
    $archive = [System.IO.Compression.ZipFile]::Open($temporary, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($file in $files) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, (Join-Path $root $file), $file.Replace('\','/'), [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        }
    } finally { $archive.Dispose() }
    $verify = [System.IO.Compression.ZipFile]::OpenRead($temporary)
    try { if ($verify.Entries.Count -ne $files.Count) { throw 'Incomplete results archive' } } finally { $verify.Dispose() }
    Move-Item -LiteralPath $temporary -Destination $zip -Force
    Start-Process -FilePath explorer.exe -ArgumentList ('/select,"' + $zip + '"')
    Write-Host "Results ready: $zip"
} catch {
    Write-Host "Automatic collection failed: $_"
    Read-Host 'Press Enter to close'
}
