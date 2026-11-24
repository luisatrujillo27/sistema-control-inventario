@echo off
REM Lanzador del Sistema de Control de Inventario.
REM Prepara el entorno, arranca Flask y abre el navegador.
setlocal
cd /d "%~dp0"
title Sistema de Control de Inventario

set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py"
if not defined PY_CMD (
    where python >nul 2>&1 && set "PY_CMD=python"
)
if not defined PY_CMD (
    echo [ERROR] No se encontro Python en el sistema.
    echo         Instalalo desde https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando el entorno virtual .venv ...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Entorno virtual ya existente.
)

echo [2/3] Instalando dependencias ...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo [3/3] Arrancando el servidor en http://127.0.0.1:5000
echo       Para detenerlo, pulsa Ctrl+C en esta ventana.
echo.
start "" "http://127.0.0.1:5000"
".venv\Scripts\python.exe" app.py

echo.
echo El servidor se detuvo.
pause
