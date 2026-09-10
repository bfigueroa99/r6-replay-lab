# Modo desarrollo: Django en 8000 y Vite con hot reload en 5173.
# Abre el de Vite (http://localhost:5173), que proxea /api a Django.
# Uso:  .\scripts\dev.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

Start-Process -FilePath $python -ArgumentList 'manage.py', 'runserver', '127.0.0.1:8000' -WorkingDirectory "$repo\backend"
Start-Sleep -Seconds 2
Start-Process 'http://localhost:5173'
Set-Location "$repo\frontend"
npm run dev
