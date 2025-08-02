"""
Punto de entrada principal para el sistema de gestión de inventario.

Fecha: 30/06/2025
Ruta: D:/inventario_app2/main.py
Estado: CORREGIDO - Inconsistencia MainWindow solucionada
"""
import os
import sys
import logging
import configparser
from tkinter import messagebox

# Agregar src/ al path para imports correctos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
# print("PATHS actuales:")
# Configurar logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'inventario_sistema.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos necesarios con paths corregidos

try:
    from db.database import get_database_connection, initialize_database
    from ui.auth.login_window import LoginWindow
    from ui.main.main_window import start_main_window
    from services.service_container import setup_default_container, cleanup_container
    
    logger.info("Módulos importados correctamente")
except ImportError as e:
    logger.critical(f"Error al importar módulos: {e}")
    messagebox.showerror("Error de Sistema", f"Error al importar módulos: {e}")
    exit(1)

def setup_configuration():
    """
    Carga la configuración del programa desde un archivo config.ini.
    """
    config = configparser.ConfigParser()
    
    # Verificar que existe el directorio config
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    if not os.path.exists(config_dir):
        logger.info("Creando directorio 'config'...")
        os.makedirs(config_dir)
        
    # Verificar que existe config.ini
    config_path = os.path.join(config_dir, 'config.ini')
    if not os.path.exists(config_path):
        logger.warning("Archivo config.ini no encontrado. Creando valores por defecto.")
        # Crear config.ini con valores por defecto
        config['database'] = {
            'db_type': 'sqlite',
            'db_name': 'inventario.db',
            'db_host': 'localhost',
            'db_user': 'root',
            'db_password': ''
        }
        config['paths'] = {
            'reports': './data/reports/'
        }
        config['monetary'] = {
            'currency_symbol': 'B/.',
            'decimal_places': '2',
            'use_locale': 'True'
        }
        
        with open(config_path, 'w') as configfile:
            config.write(configfile)
            logger.info(f"Creado archivo de configuración: {config_path}")
    else:
        config.read(config_path)

    # Configuración de la base de datos
    db_config = {
        'db_type': config.get('database', 'db_type', fallback='sqlite'),
        'db_name': config.get('database', 'db_name', fallback='inventario.db'),
        'db_host': config.get('database', 'db_host', fallback='localhost'),
        'db_user': config.get('database', 'db_user', fallback='root'),
        'db_password': config.get('database', 'db_password', fallback='')
    }
    
    # Configuración monetaria
    monetary_config = {
        'currency_symbol': config.get('monetary', 'currency_symbol', fallback='B/.'),
        'decimal_places': config.getint('monetary', 'decimal_places', fallback=2),
        'use_locale': config.getboolean('monetary', 'use_locale', fallback=True)
    }

    return db_config, monetary_config

def initialize_system():
    """
    Inicializar sistema completo incluyendo base de datos.
    """
    try:
        # Cargar configuración
        db_config, monetary_config = setup_configuration()
        logger.info("Configuración cargada exitosamente")
        
        # Obtener ruta completa de la base de datos
        db_path = os.path.join(os.path.dirname(__file__), db_config['db_name'])
        
        # Verificar si la base de datos existe, si no, crearla
        if not os.path.exists(db_path):
            logger.info(f"Base de datos no existe. Creando: {db_path}")
            db_connection = initialize_database(db_path)
            logger.info("Base de datos inicializada con schema y datos por defecto")
        else:
            logger.info(f"Conectando a base de datos existente: {db_path}")
            db_connection = get_database_connection(db_path)
        
        # Verificar integridad de la base de datos
        if not db_connection.verify_schema_integrity():
            logger.warning("Problemas de integridad en la base de datos")
            messagebox.showwarning("Advertencia", 
                                 "Se detectaron problemas en la base de datos. "
                                 "Algunas funciones pueden no trabajar correctamente.")
        
        return db_connection, monetary_config
        
    except Exception as e:
        logger.critical(f"Error al inicializar sistema: {e}", exc_info=True)
        messagebox.showerror("Error del Sistema", 
                           f"No se pudo inicializar el sistema: {e}")
        raise

def main():
    """
    Función principal que inicia la aplicación.
    """
    try:
        logger.info("=== INICIANDO SISTEMA DE INVENTARIO ===")
        
        # Inicializar sistema
        db_connection, monetary_config = initialize_system()
        logger.info("Sistema inicializado correctamente")
        
        # Configurar Service Container con servicios del sistema
        logger.info("Configurando Service Container...")
        try:
            container = setup_default_container()
            logger.info(f"Service Container configurado con {len(container.get_registered_services())} servicios")
        except Exception as e:
            logger.error(f"Error configurando Service Container: {e}")
            messagebox.showerror("Error", f"Error configurando servicios del sistema: {e}")
            return
        
        # Mostrar ventana de login
        login_window = LoginWindow()
        login_success = login_window.show()
        
        if login_success:
            logger.info("Login exitoso, iniciando ventana principal")
            
            # Iniciar ventana principal (MainWindow maneja su propia instancia de Tk)
            try:
                main_window = start_main_window()
                logger.info("Aplicación iniciada correctamente")
            finally:
                # Cleanup del Service Container al cerrar aplicación
                logger.info("Limpiando Service Container...")
                cleanup_container()
        else:
            logger.info("Login cancelado o fallido")
            cleanup_container()
            return
        
    except Exception as e:
        logger.critical(f"Error crítico en la aplicación: {e}", exc_info=True)
        messagebox.showerror("Error Crítico", 
                           f"Error crítico en la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
