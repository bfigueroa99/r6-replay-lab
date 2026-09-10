# Abre la app de escritorio (Electron). Levanta Django solo si no esta corriendo.
# Uso:  .\scripts\desktop.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }
if (-not (Test-Path "$repo\frontend\node_modules\electron")) {
    throw "Falta Electron. Corre 'npm install' en frontend\."
}
if (-not (Test-Path "$repo\frontend\dist\index.html")) {
    throw "Falta el build del frontend. Corre 'npm run build' en frontend\."
}

Set-Location "$repo\frontend"
npm run desktop
