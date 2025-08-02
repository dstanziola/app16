@echo off
chcp 65001
echo Iniciando Gestor de Inventario...
echo.

:: Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv 
    call venv\Scripts\activate
    echo Instalando dependencias...
    python -m pip install --upgrade pip
    pip install sqlalchemy
    py -m pip install pandas
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

:: Configurar PYTHONPATH
:: set PYTHONPATH=%CD%;%PYTHONPATH%
set PYTHONPATH=%CD%\src;%PYTHONPATH%

:: Cambiar al directorio del proyecto
cd /d "D:\inventario_app"

:: Verificar si existe el entorno virtual
if not exist "venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv venv >nul
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Existe venv pero No se pudo activar el entorno virtual
    pause
    exit /b 1
)

:: Actualizar pip e instalar dependencias
echo [INFO] Actualizando pip e instalando dependencias...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERROR] Error actualizando pip
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Error instalando dependencias
    pause
    exit /b 1
)
call cmd
pause