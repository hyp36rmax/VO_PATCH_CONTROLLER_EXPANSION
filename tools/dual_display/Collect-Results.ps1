# Stage byte-preserving diagnostic copies before loading any compression library.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$returnFolder = Join-Path $root 'RETURN-THIS-D04-P02B-LF01'
$zip = "$returnFolder.zip"
$selected = $returnFolder
try {
    $run = Join-Path $returnFolder ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path $run -Force | Out-Null
    $files = @('build-record.json', 'launch-error.txt')
    $records = @('Missing logs are not successful results. Unrun modes are expected.')
    foreach ($mode in @('dual','control')) {
        foreach ($name in @('launch-status.txt','displays.txt','display-errors.txt','assignment.txt','RETURN-THIS-D01-3840.log','game\D04-P02B-presentation.log','game\player-displays.ini','game\ddraw.ini')) {
            $files += "$mode\$name"
        }
        foreach ($name in @('v_on.exe','ddraw.dll','vontanita.dll')) {
            try { $records += "$mode/$name SHA256: $((Get-FileHash -LiteralPath (Join-Path $root "$mode\game\$name") -Algorithm SHA256).Hash)" }
            catch { $records += "Hash unavailable: $mode/$name : $_" }
        }
    }
    foreach ($file in $files) {
        $source = Join-Path $root $file
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            try {
                $destination = Join-Path $run $file
                New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
                Copy-Item -LiteralPath $source -Destination $destination
                $records += "Copied: $file; source UTC: $((Get-Item -LiteralPath $source).LastWriteTimeUtc.ToString('o'))"
            } catch { $records += "Copy failed (original retained): $file : $_" }
        } else { $records += "Not present: $file" }
    }
    $records | Set-Content -LiteralPath (Join-Path $run 'collection-status.txt') -Encoding UTF8
    $temporary = Join-Path $root ('RETURN-THIS-D04-P02B-LF01-' + [Guid]::NewGuid().ToString('N') + '.new.zip')
    try {
        # ZipArchive/ZipArchiveMode live in Compression, not FileSystem.
        Add-Type -AssemblyName System.IO.Compression
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory($returnFolder, $temporary)
        $archive = [System.IO.Compression.ZipFile]::OpenRead($temporary)
        try {
            $expected = @(Get-ChildItem -LiteralPath $returnFolder -Recurse -File).Count
            if ($archive.Entries.Count -ne $expected) { throw 'Incomplete archive' }
        } finally { $archive.Dispose() }
        Move-Item -LiteralPath $temporary -Destination $zip -Force
        $selected = $zip
    } catch {
        "ZIP unavailable: $_`r`nReturn this folder. Original logs and staged copies are retained." |
            Set-Content -LiteralPath (Join-Path $run 'compression-status.txt') -Encoding UTF8
        Write-Host "ZIP unavailable. Logs retained in: $returnFolder"
    }
    # A shell-selection failure must not invalidate the successfully saved evidence.
    try { Start-Process -FilePath explorer.exe -ArgumentList ('/select,"' + $selected + '"') } catch { Write-Host "Saved results: $selected" }
    Write-Host "Return: $selected"
} catch {
    Write-Host "Collection could not finish: $_"
    Write-Host "Original logs remain in the dual and control folders under: $root"
    try { $_ | Out-String | Set-Content -LiteralPath (Join-Path $root 'collection-error.txt') } catch {}
}
