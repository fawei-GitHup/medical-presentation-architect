$ErrorActionPreference = 'Stop'
$Version = if ($env:MPA_VERSION) { $env:MPA_VERSION } else { '1.1.0' }
$Agent = if ($env:MPA_AGENT) { $env:MPA_AGENT } else { 'kimi' }
$Base = if ($env:MPA_BASE_URL) { $env:MPA_BASE_URL.TrimEnd('/') } else { "https://github.com/fawei-GitHup/medical-presentation-architect/releases/download/v$Version" }
$ArchiveName = "medical-presentation-architect-v$Version.zip"
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("mpa-install-" + [guid]::NewGuid().ToString('N'))

try {
    New-Item -ItemType Directory -Path $TempRoot | Out-Null
    $Archive = Join-Path $TempRoot $ArchiveName
    $Checksum = "$Archive.sha256"
    Invoke-WebRequest "$Base/$ArchiveName" -OutFile $Archive
    Invoke-WebRequest "$Base/$ArchiveName.sha256" -OutFile $Checksum

    $Expected = ((Get-Content -LiteralPath $Checksum -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
    $Actual = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Actual -ne $Expected) { throw "SHA-256 mismatch; installation stopped." }

    $Expanded = Join-Path $TempRoot 'expanded'
    Expand-Archive -LiteralPath $Archive -DestinationPath $Expanded
    $Source = Join-Path $Expanded "medical-presentation-architect-$Version"
    $InstallerArgs = @((Join-Path $Source 'scripts/install.py'), 'install', '--agent', $Agent)
    if ($env:MPA_TARGET) { $InstallerArgs += @('--target', $env:MPA_TARGET) }
    python @InstallerArgs
    if ($LASTEXITCODE -ne 0) { throw "Installer exited with code $LASTEXITCODE." }

    Write-Host "Installed Medical Presentation Architect $Version for $Agent."
    if ($Agent -eq 'kimi') { Write-Host 'Start Kimi and enter: /skill:medical-presentation-architect' }
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}
