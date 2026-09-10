# Importa los replays nuevos que haya en REPLAY_DIR.
# Uso:  .\scripts\import.ps1            importa lo nuevo
#       .\scripts\import.ps1 -Force     reimporta todo
#       .\scripts\import.ps1 -Path "D:\ruta\Match-2026-..."   importa una partida
param(
    [string]$Path,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

Set-Location "$repo\backend"
$args = @('manage.py', 'import_replays')
if ($Path) { $args += $Path; $args += '--quiet-seconds'; $args += '0' }
if ($Force) { $args += '--force' }
& $python @args
