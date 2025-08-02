@echo off
chcp 65001 >nul
title Sistema de Inventario - Launcher Simple

echo Iniciando Sistema de Inventario v2.0
echo(

:: Configurar PYTHONPATH
:: set PYTHONPATH=%CD%;%PYTHONPATH%
set PYTHONPATH=%CD%\src;%PYTHONPATH%

:: Verificar si Python está disponible
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en PATH.
    pause
    exit
)

:: Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate
    echo Instalando dependencias...
    python -m pip install --upgrade pip
    pip install black flake8 pylint isort
    pip install sqlalchemy
    py -m pip install pandas
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo(
if exist "main.py" (
    echo main.py encontrado
) else (
    echo ERROR: main.py no encontrado
    pause
    exit
)

echo Ejecutando aplicación: usuario: admin, contraseña: admin123
python main.py

if errorlevel 1 (
    echo ERROR: La aplicación terminó con errores.
) else (
    echo Aplicación finalizada correctamente.
)

pause
