# Arma el instalador de Windows, de cero.
# Uso:  .\scripts\package.ps1
#
# Son tres pasos y el orden importa:
#   1. build del frontend           -> frontend\dist
#   2. PyInstaller sobre el backend -> packaging\dist\r6-backend (lleva dist adentro)
#   3. electron-builder             -> packaging\installer\R6ReplayLab-*-setup.exe
#
# Tarda varios minutos y el resultado pesa unos 135 MB: adentro va un Python
# completo, Chromium y el frontend. Necesita las herramientas de desarrollo
# (pip install -r requirements-dev.txt) y npm install en frontend\.
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

$pyinstaller = "$repo\.venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstaller)) {
    throw "Falta PyInstaller: pip install -r requirements-dev.txt"
}

# electron-builder descomprime sus herramientas en %LOCALAPPDATA%, que en este
# equipo esta marcado como cifrado (EFS) y hace fallar el rename con EXDEV. Con
# la cache dentro del repo no pasa por ese borde.
$env:ELECTRON_BUILDER_CACHE = "$repo\packaging\.cache"
New-Item -ItemType Directory -Force $env:ELECTRON_BUILDER_CACHE | Out-Null

Write-Host "`n[1/3] build del frontend" -ForegroundColor Cyan
Push-Location "$repo\frontend"
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "fallo el build del frontend" }
Pop-Location

Write-Host "`n[2/3] backend con PyInstaller" -ForegroundColor Cyan
& $pyinstaller "$repo\packaging\backend.spec" --noconfirm `
    --distpath "$repo\packaging\dist" --workpath "$repo\packaging\build"
if ($LASTEXITCODE -ne 0) { throw "fallo PyInstaller" }

Write-Host "`n[3/3] instalador con electron-builder" -ForegroundColor Cyan
Push-Location "$repo\frontend"
npm run desktop:pack
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "fallo electron-builder" }
Pop-Location

$setup = Get-ChildItem "$repo\packaging\installer\*-setup.exe" -ErrorAction SilentlyContinue |
    Select-Object -First 1
Write-Host ""
if ($setup) {
    Write-Host ("Instalador listo: {0} ({1:N0} MB)" -f $setup.FullName, ($setup.Length / 1MB)) `
        -ForegroundColor Green
    Write-Host "Sin firmar: Windows va a mostrar SmartScreen la primera vez." -ForegroundColor Yellow
} else {
    Write-Host "No se encontro el instalador." -ForegroundColor Red
    exit 1
}
