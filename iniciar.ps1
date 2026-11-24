# Lanzador del Sistema de Control de Inventario (PowerShell).
# Uso:  .\iniciar.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$pythonCmd = $null
foreach ($candidato in @("py", "python")) {
    if (Get-Command $candidato -ErrorAction SilentlyContinue) { $pythonCmd = $candidato; break }
}
if (-not $pythonCmd) {
    Write-Host "[ERROR] No se encontro Python. Instalalo desde https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creando el entorno virtual .venv ..." -ForegroundColor Cyan
    & $pythonCmd -m venv .venv
} else {
    Write-Host "[1/3] Entorno virtual ya existente." -ForegroundColor Cyan
}

Write-Host "[2/3] Instalando dependencias ..." -ForegroundColor Cyan
& $venvPython -m pip install --quiet --disable-pip-version-check -r requirements.txt

Write-Host "[3/3] Arrancando el servidor en http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "      Para detenerlo, pulsa Ctrl+C." -ForegroundColor DarkGray
Start-Process "http://127.0.0.1:5000"
& $venvPython app.py
