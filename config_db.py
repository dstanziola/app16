"""
Configuración global de la aplicación para la base de datos.

Este módulo centraliza la configuración de la ruta de la base de datos
para evitar inconsistencias en toda la aplicación.
"""

import os

# CONFIGURACIÓN GLOBAL DE BASE DE DATOS
# Ruta absoluta al archivo de base de datos
DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "inventario.db"))

# Configuración de logging
LOG_PATH = os.path.join(os.path.dirname(__file__), "eventos.log")

# Configuración de directorios
BASE_DIR = os.path.dirname(__file__)
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
BACKUPS_DIR = os.path.join(BASE_DIR, "ui", "forms", "backups")

def get_database_path():
    """
    Obtiene la ruta absoluta de la base de datos.
    
    Returns:
        str: Ruta absoluta al archivo de base de datos
    """
    return DATABASE_PATH

def ensure_database_exists():
    """
    Verifica que el archivo de base de datos existe.
    
    Returns:
        bool: True si existe, False si no
    """
    return os.path.exists(DATABASE_PATH)

def get_database_info():
    """
    Obtiene información sobre el archivo de base de datos.
    
    Returns:
        dict: Información del archivo de BD
    """
    if os.path.exists(DATABASE_PATH):
        stat = os.stat(DATABASE_PATH)
        return {
            "exists": True,
            "path": DATABASE_PATH,
            "size": stat.st_size,
            "modified": stat.st_mtime
        }
    else:
        return {
            "exists": False,
            "path": DATABASE_PATH,
            "size": 0,
            "modified": None
        }

def print_database_status():
    """
    Imprime el estado actual de la base de datos.
    """
    info = get_database_info()
    print(f"Base de datos: {info['path']}")
    if info['exists']:
        print(f"✅ Archivo existe ({info['size']} bytes)")
    else:
        print("❌ Archivo no encontrado")
