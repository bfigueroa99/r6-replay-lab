# Inicializa el repositorio git con el commit inicial.
# Se ejecuta una sola vez, la primera vez que clonas o copias esta carpeta.
# Uso:  .\scripts\init-git.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git no esta en el PATH. Instalalo desde https://git-scm.com/download/win'
}
if (Test-Path '.git') {
    Write-Host 'Ya existe un repositorio git aca. No toco nada.' -ForegroundColor Yellow
    git -C $repo log --oneline -n 5
    return
}

git init -b main
git add -A
git commit -F 'docs\commit-inicial.txt'

Write-Host ''
Write-Host 'Repositorio creado.' -ForegroundColor Green
git log --stat --oneline -n 1
Write-Host ''
Write-Host 'Para subirlo a GitHub:' -ForegroundColor Cyan
Write-Host '  gh repo create r6-replay-lab --private --source . --push'
Write-Host 'o, sin gh:'
Write-Host '  git remote add origin https://github.com/bfigueroa99/r6-replay-lab.git'
Write-Host '  git push -u origin main'
