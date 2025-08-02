@echo off
chcp 65001
echo Iniciando limpieza del entorno de desarrollo Python...
echo ¿Estas seguro que quieres borrar todo? (S/N)
set /p confirm=Confirmar (S/N):
echo Eliminando archivos y carpetas generados por el entorno de desarrollo Python...

REM Eliminar carpeta venv
if exist venv (
    echo Eliminando carpeta venv...
    rmdir /s /q venv
)

REM Eliminar carpetas __pycache__ de forma recursiva
echo Buscando y eliminando carpetas __pycache__...
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        echo Eliminando %%d
        rmdir /s /q "%%d"
    )
)

REM Eliminar archivos .pyc de forma recursiva
echo Buscando y eliminando archivos .pyc...
for /r %%f in (*.pyc) do (
    del /q "%%f"
)

REM Eliminar archivos .pyo de forma recursiva
echo Buscando y eliminando archivos .pyo...
for /r %%f in (*.pyo) do (
    del /q "%%f"
)

REM Eliminar carpeta .pytest_cache si existe
if exist .pytest_cache (
    echo Eliminando carpeta .pytest_cache...
    rmdir /s /q .pytest_cache
)

REM Eliminar carpeta .mypy_cache si existe
if exist .mypy_cache (
    echo Eliminando carpeta .mypy_cache...
    rmdir /s /q .mypy_cache
)

echo Limpieza completada.
pause
