# Corre la suite de tests. Con -Replay <archivo.rec> o -ReplayDir <carpeta>
# tambien corren los tests de integracion contra replays reales.
# Uso:  .\scripts\test.ps1
#       .\scripts\test.ps1 -ReplayDir "D:\...\MatchReplay"
param(
    [string]$Replay,
    [string]$ReplayDir
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

if ($Replay) { $env:R6_TEST_REPLAY = $Replay }
if ($ReplayDir) { $env:R6_TEST_REPLAY_DIR = $ReplayDir }

Set-Location "$repo\backend"
& $python manage.py test tests -v 1
