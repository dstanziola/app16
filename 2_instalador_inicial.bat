@echo off
chcp 65001 >nul
title Instalador Inicial - CopyPoint V1.0
SETLOCAL

:: ================================
:: Paso 1: Crear carpeta en Program Files
:: ================================
SET "INSTALL_DIR=%ProgramFiles%\CopyPointV1_0"
if not exist "%INSTALL_DIR%" (
    echo Creando directorio %INSTALL_DIR%...
    mkdir "%INSTALL_DIR%"
)

:: ================================
:: Paso 2: Cambiar al directorio creado
:: ================================
cd /d "%INSTALL_DIR%"

:: ================================
:: Paso 3: Añadir esta carpeta al PATH (solo para esta sesión)
:: ================================
set "PATH=%INSTALL_DIR%;%PATH%"

:: ================================
:: Paso 4: Instalar programas previos si faltan
:: ================================

:: Verificar Winget e instalar si falta
where winget >nul 2>&1 || (
    echo Winget no está instalado. Descargando e instalando Winget...
    powershell -Command ^
      "Invoke-WebRequest -Uri https://aka.ms/getwinget -OutFile winget.msixbundle -UseBasicParsing; ^
       Add-AppxPackage .\winget.msixbundle; ^
       Remove-Item .\winget.msixbundle"
)

:: Verifica Python
where python >nul 2>&1 || (
    echo Python no está instalado. Instalando con winget...
    winget install --id Python.Python.3 -e --silent
)

:: ================================
:: Paso 5: Crear y activar entorno virtual
:: ================================
echo Creando entorno virtual...
python -m venv venv

echo Activando entorno virtual...
call venv\Scripts\activate

:: ================================
:: Paso 6: Instalar dependencias desde requirements.txt
:: ================================
echo Actualizando pip e instalando dependencias...
pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo ¡Aviso! requirements.txt no encontrado en %INSTALL_DIR%
)

:: ================================
:: Paso 7: Crear acceso directo en el Escritorio
:: ================================
:: Ruta al Escritorio del usuario
set "DESKTOP=%USERPROFILE%\Desktop"
:: Nombre y ruta del .lnk que vamos a crear
set "SHORTCUT=%DESKTOP%\CopyPointV1_0.lnk"

:: Usa PowerShell para generar el acceso directo
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$shell = New-Object -ComObject WScript.Shell; ^
   $sc = $shell.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%INSTALL_DIR%\venv\Scripts\python.exe'; ^
   $sc.Arguments = '%INSTALL_DIR%\main.py'; ^
   $sc.WorkingDirectory = '%INSTALL_DIR%'; ^
   :: Opcional: si tienes un icono .ico, indícalo aquí:
   $sc.IconLocation = '%INSTALL_DIR%\icon.ico'; ^
   $sc.Save()"

:: ================================
:: Paso 8: Ejecutar la aplicación
:: ================================
echo Iniciando main.py...
python main.py

ENDLOCAL
pause
