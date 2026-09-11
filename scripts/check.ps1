# Todo lo que hay que pasar antes de commitear: lint, tests y build.
# Uso:  .\scripts\check.ps1
#
# Solo corre `ruff check`, no `ruff format`: el formateador reescribiria medio
# repo para pelear con un estilo que ya es consistente. El linter busca errores;
# el formateador impone gustos.
# 'Continue' y no 'Stop': Django y npm escriben su salida normal en stderr, y
# con 'Stop' PowerShell la toma como error y corta en la primera linea. Cada
# paso mira $LASTEXITCODE, que es lo que de verdad dice si fallo.
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
$python = "$repo\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Falta el entorno virtual. Corre .\scripts\setup.ps1 primero." }

$fallos = @()

Write-Host "`n[1/4] ruff" -ForegroundColor Cyan
$ruff = "$repo\.venv\Scripts\ruff.exe"
if (Test-Path $ruff) {
    & $ruff check "$repo\backend"
    if ($LASTEXITCODE -ne 0) { $fallos += 'ruff' }
} else {
    Write-Host "  ruff no esta instalado: pip install -r requirements-dev.txt" -ForegroundColor Yellow
}

Write-Host "`n[2/4] tests del backend" -ForegroundColor Cyan
Push-Location "$repo\backend"
& $python manage.py test tests
if ($LASTEXITCODE -ne 0) { $fallos += 'tests' }
Pop-Location

Write-Host "`n[3/4] tests del frontend" -ForegroundColor Cyan
if (Test-Path "$repo\frontend\node_modules") {
    Push-Location "$repo\frontend"
    npm test
    if ($LASTEXITCODE -ne 0) { $fallos += 'tests del frontend' }
    Pop-Location
} else {
    Write-Host "  falta node_modules: corre 'npm install' en frontend\" -ForegroundColor Yellow
}

Write-Host "`n[4/4] build del frontend" -ForegroundColor Cyan
if (Test-Path "$repo\frontend\node_modules") {
    Push-Location "$repo\frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) { $fallos += 'build' }
    Pop-Location
}

Write-Host ""
if ($fallos.Count -gt 0) {
    Write-Host "Fallo: $($fallos -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host "Todo en verde." -ForegroundColor Green
