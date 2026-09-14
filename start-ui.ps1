param(
    [string]$Workspace,
    [int]$Port = 8765
)
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ArgsList = @((Join-Path $ScriptDir 'scripts/ui_server.py'), '--port', $Port)
if ($Workspace) { $ArgsList += @('--workspace', $Workspace) }
python @ArgsList
if ($LASTEXITCODE -ne 0) { throw "Local UI failed ($LASTEXITCODE)" }
