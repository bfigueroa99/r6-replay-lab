# Deja el importador vigilando la carpeta de replays. Ctrl+C para salir.
# Uso:  .\scripts\watch.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

Set-Location "$repo\backend"
& $python manage.py watch_replays
