# Arma el instalador de Windows, de cero.
# Uso:  .\scripts\package.ps1
#
# Son tres pasos y el orden importa:
#   1. build del frontend           -> frontend\dist
#   2. PyInstaller sobre el backend -> packaging\dist\r6-backend (lleva dist adentro)
#   3. electron-builder             -> packaging\installer\R6ReplayLab-*-setup.exe
#
# Sale un solo .exe, el instalador de un clic: no pregunta nada, instala para
# el usuario (sin pedir admin), deja los accesos directos y abre la app. Correr
# uno nuevo encima actualiza sin tocar los datos de %APPDATA%.
#
# Tarda varios minutos y el .exe pesa unos 135 MB: adentro va un Python
# completo, Chromium y el frontend.
#
# Se prepara solo: si falta el venv, PyInstaller o node_modules, los instala.
# En un clon recien bajado basta con Python 3.11+ y Node 18+ en el PATH; no
# hace falta haber corrido setup.ps1 antes.
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
$pyinstaller = "$repo\.venv\Scripts\pyinstaller.exe"

Write-Host "`n[0/3] herramientas" -ForegroundColor Cyan
if (-not (Test-Path $python)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "No hay Python en el PATH. Instala Python 3.11+ (winget install Python.Python.3.12) y vuelve a correr esto."
    }
    python -m venv "$repo\.venv"
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual en .venv" }
}
if (-not (Test-Path $pyinstaller)) {
    & $python -m pip install --quiet -r "$repo\requirements.txt" -r "$repo\requirements-dev.txt"
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias de Python" }
}
if (-not (Test-Path "$repo\frontend\node_modules\electron-builder")) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "No hay npm en el PATH. Instala Node 18+ (winget install OpenJS.NodeJS.LTS) y vuelve a correr esto."
    }
    Push-Location "$repo\frontend"
    npm ci
    $npmOk = $LASTEXITCODE -eq 0
    Pop-Location
    if (-not $npmOk) { throw "fallo npm ci en frontend\" }
}

# electron-builder descomprime sus herramientas en %LOCALAPPDATA%, que en este
# equipo esta marcado como cifrado (EFS) y hace fallar el rename con EXDEV. Con
# la cache dentro del repo no pasa por ese borde.
$env:ELECTRON_BUILDER_CACHE = "$repo\packaging\.cache"
New-Item -ItemType Directory -Force $env:ELECTRON_BUILDER_CACHE | Out-Null

# De cero de verdad: release.ps1 sube lo que haya aca, y un .exe de una version
# vieja (o el -portable.exe que se armaba antes) terminaria colgado de la Release.
if (Test-Path "$repo\packaging\installer") {
    Remove-Item "$repo\packaging\installer" -Recurse -Force
}

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

$exes = Get-ChildItem "$repo\packaging\installer\R6ReplayLab-*-setup.exe" -ErrorAction SilentlyContinue
Write-Host ""
if ($exes) {
    foreach ($exe in $exes) {
        Write-Host ("Listo: {0} ({1:N0} MB)" -f $exe.FullName, ($exe.Length / 1MB)) -ForegroundColor Green
    }
    Write-Host "Sin firmar: Windows va a mostrar SmartScreen la primera vez." -ForegroundColor Yellow
} else {
    Write-Host "No se encontro ningun .exe en packaging\installer." -ForegroundColor Red
    exit 1
}
