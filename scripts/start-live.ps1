param(
    [string]$Phone = '',
    [int]$Port = 5173,
    [string]$Calibration = ''
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskArgs = @((Join-Path $PSScriptRoot 'live.mjs'), '--port', "$Port")
if ($Phone) { $taskArgs += @('--phone', $Phone) }
if ($Calibration) { $taskArgs += @('--calibration', $Calibration) }
Push-Location -LiteralPath $taskRoot
try {
    & node @taskArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
