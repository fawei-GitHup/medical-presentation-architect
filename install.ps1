param(
    [ValidateSet('kimi','claude','codex','generic')][string]$Agent = 'kimi',
    [string]$Target
)
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArgsList = @((Join-Path $ScriptDir 'scripts/install.py'), 'install', '--agent', $Agent)
if ($Target) { $ArgsList += @('--target', $Target) }
python @ArgsList
if ($LASTEXITCODE -ne 0) { throw "Skill installation failed ($LASTEXITCODE)" }
