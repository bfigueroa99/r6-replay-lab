# Publica una version desde este PC: verifica, empaqueta, taggea y sube la Release.
# Uso:  .\scripts\release.ps1             version = la de frontend\package.json
#       .\scripts\release.ps1 -SinE2E     sin el end to end (no recomendado)
#       .\scripts\release.ps1 -SoloArmar  verifica y empaqueta; ni tag ni Release
#
# Existe porque GitHub Actions no asigna runners en esta cuenta: el workflow de
# .github\workflows\release.yml esta bien, pero no corre. La verificacion que
# cuenta es la de la maquina (check.ps1, con el e2e incluido) y el .exe se arma
# aca, con el mismo package.ps1 que correria el runner.
#
# Para publicar usa el CLI de GitHub (`gh`, winget install GitHub.cli) si esta
# instalado. Si no, abre la pagina de la Release con el tag ya puesto y deja
# los .exe a mano para arrastrarlos.
param(
    [switch]$SinE2E,
    [switch]$SoloArmar
)
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$version = (Get-Content "$repo\frontend\package.json" -Raw | ConvertFrom-Json).version
$tag = "v$version"
Write-Host "`nRelease $tag" -ForegroundColor Cyan

# --- precondiciones: no se publica desde una rama a medias ------------------
$rama = (git rev-parse --abbrev-ref HEAD).Trim()
if ($rama -ne 'main') {
    throw "Estas en '$rama'. Las releases salen de main: git checkout main; git pull origin main"
}
if (git status --porcelain) {
    throw "Hay cambios sin commitear. Commitea o descarta antes de publicar."
}
git fetch origin main --quiet
if ((git rev-parse HEAD) -ne (git rev-parse origin/main)) {
    throw "main local y origin/main no coinciden. git pull origin main (o push) primero."
}
if (-not $SoloArmar) {
    if ((git tag --list $tag) -or (git ls-remote --tags origin $tag)) {
        throw "El tag $tag ya existe. Sube 'version' en frontend\package.json y commitea."
    }
}

# --- verificacion: lint, tests, build y e2e ---------------------------------
Write-Host "`n== Verificacion" -ForegroundColor Cyan
if ($SinE2E) { & "$repo\scripts\check.ps1" -SinE2E } else { & "$repo\scripts\check.ps1" }
if ($LASTEXITCODE -ne 0) { throw "La verificacion fallo. No se publica nada en rojo." }

# --- empaquetado --------------------------------------------------------------
Write-Host "`n== Empaquetado" -ForegroundColor Cyan
& "$repo\scripts\package.ps1"
if ($LASTEXITCODE -ne 0) { throw "Fallo el empaquetado." }
$exes = Get-ChildItem "$repo\packaging\installer\*.exe"
if (-not $exes) { throw "No hay .exe en packaging\installer." }

if ($SoloArmar) {
    Write-Host "`nListo (-SoloArmar): sin tag ni Release." -ForegroundColor Green
    exit 0
}

# --- tag ----------------------------------------------------------------------
Write-Host "`n== Tag $tag" -ForegroundColor Cyan
git tag -a $tag -m "R6 Replay Lab $version"
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el tag." }
git push origin $tag
if ($LASTEXITCODE -ne 0) { throw "No se pudo pushear el tag. Revisa el acceso al remoto." }

# --- release ------------------------------------------------------------------
$remoto = (git remote get-url origin).Trim() -replace '\.git$', '' -replace '^git@github\.com:', 'https://github.com/'
$notas = @"
**Para usarla:** descarga ``R6ReplayLab-$version-portable.exe`` y hazle doble clic.
No instala nada. Si prefieres acceso directo en el escritorio, usa el ``-setup.exe``.

Al abrir busca sola la carpeta ``MatchReplay`` de Siege (Steam y Ubisoft Connect).
Los datos quedan en ``%APPDATA%\r6-replay-lab``.

El ejecutable no esta firmado: la primera vez Windows muestra SmartScreen
(*Mas informacion* -> *Ejecutar de todas formas*).
"@
$notasPath = "$repo\packaging\release-notes.md"
Set-Content -Path $notasPath -Value $notas -Encoding UTF8

Write-Host "`n== Release" -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh release create $tag @($exes.FullName) --title "R6 Replay Lab $version" --notes-file $notasPath
    if ($LASTEXITCODE -ne 0) { throw "gh release create fallo. La Release se puede crear a mano en $remoto/releases/new?tag=$tag" }
    Write-Host "`nPublicada: $remoto/releases/tag/$tag" -ForegroundColor Green
} else {
    Write-Host "No esta el CLI de GitHub (gh). La Release se crea a mano:" -ForegroundColor Yellow
    Write-Host "  1. Se abre $remoto/releases/new?tag=$tag"
    Write-Host "  2. Pega el texto de $notasPath"
    Write-Host "  3. Arrastra estos archivos:"
    foreach ($exe in $exes) { Write-Host "     $($exe.FullName)" }
    Start-Process "$remoto/releases/new?tag=$tag&title=R6+Replay+Lab+$version"
}
