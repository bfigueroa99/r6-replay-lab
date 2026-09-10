# Levanta la app (API + frontend compilado) y abre el navegador.
# Uso:  .\scripts\start.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

Set-Location "$repo\backend"
Start-Process 'http://127.0.0.1:8000'
& $python manage.py runserver 127.0.0.1:8000
