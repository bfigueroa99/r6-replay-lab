# Instala todo de una: entorno virtual, dependencias, base de datos y frontend.
# Uso:  .\scripts\setup.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

Write-Host '=> Entorno virtual' -ForegroundColor Cyan
if (-not (Test-Path '.venv')) { python -m venv .venv }
& '.\.venv\Scripts\python.exe' -m pip install --upgrade pip --quiet
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt

Write-Host '=> Configuracion' -ForegroundColor Cyan
if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host '   Cree .env desde .env.example. Revisa REPLAY_DIR antes de importar.' -ForegroundColor Yellow
} else {
    Write-Host '   .env ya existe, no lo toco.'
}

Write-Host '=> Base de datos' -ForegroundColor Cyan
Set-Location "$repo\backend"
& "$repo\.venv\Scripts\python.exe" manage.py migrate
Set-Location $repo

Write-Host '=> Frontend' -ForegroundColor Cyan
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Set-Location "$repo\frontend"
    npm install
    npm run build
    # El navegador del e2e: ~130 MB, una sola vez. Va aislado porque este script
    # corre con ErrorActionPreference 'Stop' y npx escribe su avance en stderr:
    # sin el 'Continue' local, una descarga ruidosa abortaria todo el setup.
    # Y si de verdad falla tampoco corta: la app anda igual sin poder correr el e2e.
    & {
        $ErrorActionPreference = 'Continue'
        npx playwright install chromium
        if ($LASTEXITCODE -ne 0) {
            Write-Host '   No pude bajar Chromium para el e2e. Despues: cd frontend; npm run e2e:browser' -ForegroundColor Yellow
        }
    }
    Set-Location $repo
} else {
    Write-Host '   npm no esta en el PATH. Instala Node 18+ y corre: cd frontend; npm install; npm run build' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Listo. Ahora:' -ForegroundColor Green
Write-Host '  .\scripts\import.ps1    para importar tus replays'
Write-Host '  .\scripts\start.ps1     para levantar la app en http://127.0.0.1:8000'
Write-Host '  .\scripts\watch.ps1     para que importe sola al terminar cada partida'
