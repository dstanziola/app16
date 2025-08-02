"""
Configuración del Sistema de Inventario - Copy Point S.A.

Este módulo contiene todas las configuraciones centralizadas del sistema,
incluyendo configuraciones de base de datos, interfaz, reportes y empresa.

Fecha: 30/06/2025
Estado: IMPLEMENTADO
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class SystemConfig:
    """
    Configuración centralizada del sistema de inventario.
    Implementa patrón Singleton para asegurar configuración única.
    """
    
    _instance: Optional['SystemConfig'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'SystemConfig':
        """Implementar patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializar configuración si no se ha hecho antes."""
        if not self._initialized:
            self._setup_configuration()
            SystemConfig._initialized = True
    
    def _setup_configuration(self):
        """Configurar todos los parámetros del sistema."""
        
        # Directorios base
        self.PROJECT_ROOT = Path(__file__).parent
        self.SRC_DIR = self.PROJECT_ROOT / "src"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        self.REPORTS_DIR = self.DATA_DIR / "reports"
        self.BACKUPS_DIR = self.PROJECT_ROOT / "backups"
        self.TEMP_DIR = self.PROJECT_ROOT / "temp"
        
        # Crear directorios si no existen
        for directory in [self.DATA_DIR, self.LOGS_DIR, self.REPORTS_DIR, 
                         self.BACKUPS_DIR, self.TEMP_DIR]:
            directory.mkdir(exist_ok=True)
    
    # === CONFIGURACIÓN DE BASE DE DATOS ===
    
    @property
    def DATABASE_CONFIG(self) -> Dict[str, Any]:
        """Configuración de base de datos."""
        return {
            'type': 'sqlite',
            'name': 'inventario.db',
            'path': str(self.PROJECT_ROOT / 'inventario.db'),
            'backup_interval_hours': 24,
            'max_connections': 10,
            'timeout_seconds': 30,
            'foreign_keys': True,
            'journal_mode': 'WAL',
            'synchronous': 'NORMAL'
        }
    
    # === CONFIGURACIÓN DE EMPRESA ===
    
    @property
    def COMPANY_CONFIG(self) -> Dict[str, Any]:
        """Configuración por defecto de la empresa."""
        return {
            'name': 'Copy Point S.A.',
            'ruc': '888-888-8888',
            'address': 'Las Lajas, Las Cumbres, Panamá',
            'phone': '6666-6666',
            'email': 'copy.point@gmail.com',
            'website': 'www.copypoint.pa',
            'logo_path': str(self.DATA_DIR / 'logo.png'),
            'itbms_rate': 7.00,
            'currency': 'USD',
            'currency_symbol': 'B/.',
            'decimal_places': 2
        }
    
    # === CONFIGURACIÓN DE INTERFAZ ===
    
    @property
    def UI_CONFIG(self) -> Dict[str, Any]:
        """Configuración de interfaz de usuario."""
        return {
            'theme': 'clam',
            'window_width': 1200,
            'window_height': 800,
            'min_width': 1024,
            'min_height': 768,
            'window_state': 'normal',  # normal, maximized
            'font_family': 'Segoe UI',
            'font_size': 10,
            'title_font_size': 14,
            'auto_save_interval_minutes': 5,
            'confirmation_dialogs': True,
            'show_tooltips': True,
            'language': 'es',
            'date_format': '%d/%m/%Y',
            'datetime_format': '%d/%m/%Y %H:%M:%S'
        }
    
    # === CONFIGURACIÓN DE REPORTES ===
    
    @property
    def REPORTS_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de reportes."""
        return {
            'default_format': 'PDF',
            'page_size': 'LETTER',  # LETTER, A4
            'margins': {
                'top': 2.5,
                'bottom': 2.5,
                'left': 2.0,
                'right': 2.0
            },
            'font_name': 'Helvetica',
            'font_size': 10,
            'title_font_size': 16,
            'header_font_size': 12,
            'auto_open_reports': True,
            'save_path': str(self.REPORTS_DIR),
            'include_logo': True,
            'include_qr_codes': True,
            'watermark': False,
            'max_rows_per_page': 40
        }
    
    # === CONFIGURACIÓN DE TICKETS ===
    
    @property
    def TICKETS_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de tickets."""
        return {
            'formats': {
                'A4': {
                    'width': 210,
                    'height': 297,
                    'margins': (20, 20, 20, 20)
                },
                'CARTA': {
                    'width': 215.9,
                    'height': 279.4,
                    'margins': (20, 20, 20, 20)
                },
                'TERMICO_80MM': {
                    'width': 80,
                    'height': 'variable',
                    'margins': (5, 5, 5, 5)
                }
            },
            'default_format': 'A4',
            'numbering': {
                'sale_prefix': 'VT-',
                'entry_prefix': 'EN-',
                'padding_zeros': 6
            },
            'auto_print': False,
            'include_qr': True,
            'include_logo': True,
            'font_size': 9,
            'line_spacing': 1.2
        }
    
    # === CONFIGURACIÓN DE CÓDIGOS DE BARRAS ===
    
    @property
    def BARCODE_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de códigos de barras."""
        return {
            'default_format': 'CODE128',
            'supported_formats': ['CODE128', 'CODE39', 'EAN13', 'EAN8'],
            'label_size': {
                'width': 50,
                'height': 25
            },
            'include_text': True,
            'text_size': 8,
            'margin': 2,
            'auto_generate': True,
            'validation_pattern': r'^[A-Z0-9]{4,20}$',
            'reader_timeout': 5000,  # ms
            'auto_connect': True,
            'scan_sound': True
        }
    
    # === CONFIGURACIÓN DE INVENTARIO ===
    
    @property
    def INVENTORY_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de inventario."""
        return {
            'auto_update_stock': True,
            'stock_alerts': True,
            'low_stock_threshold': 10,
            'negative_stock_allowed': False,
            'auto_calculate_costs': True,
            'cost_method': 'PROMEDIO',  # FIFO, LIFO, PROMEDIO
            'track_movements': True,
            'require_movement_notes': False,
            'auto_backup_on_movements': True,
            'movement_categories': [
                'ENTRADA', 'VENTA', 'AJUSTE', 'DEVOLUCION', 'TRANSFERENCIA'
            ]
        }
    
    # === CONFIGURACIÓN DE VENTAS ===
    
    @property
    def SALES_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de ventas."""
        return {
            'auto_generate_invoice_number': True,
            'invoice_prefix': 'FAC-',
            'require_customer_for_invoice': False,
            'auto_calculate_taxes': True,
            'tax_rate': 7.00,  # ITBMS
            'allow_discounts': True,
            'max_discount_percent': 20.0,
            'round_to_cents': True,
            'auto_print_receipt': False,
            'auto_update_inventory': True,
            'payment_methods': [
                'EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'CHEQUE'
            ],
            'currencies': ['USD', 'PAB']
        }
    
    # === CONFIGURACIÓN DE SEGURIDAD ===
    
    @property
    def SECURITY_CONFIG(self) -> Dict[str, Any]:
        """Configuración de seguridad del sistema."""
        return {
            'password_min_length': 6,
            'password_require_special': False,
            'password_require_numbers': True,
            'session_timeout_minutes': 60,
            'max_login_attempts': 3,
            'lockout_duration_minutes': 15,
            'audit_trail': True,
            'log_user_actions': True,
            'backup_encryption': False,
            'require_logout_confirmation': True
        }
    
    # === CONFIGURACIÓN DE LOGGING ===
    
    @property
    def LOGGING_CONFIG(self) -> Dict[str, Any]:
        """Configuración del sistema de logging."""
        return {
            'level': 'INFO',
            'file_path': str(self.LOGS_DIR / 'inventario_sistema.log'),
            'error_file_path': str(self.LOGS_DIR / 'inventario_errores.log'),
            'max_file_size_mb': 10,
            'backup_count': 5,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'log_to_console': False,
            'log_database_queries': False,
            'log_user_actions': True
        }
    
    # === MÉTODOS DE UTILIDAD ===
    
    def get_config_section(self, section: str) -> Dict[str, Any]:
        """
        Obtener una sección específica de configuración.
        
        Args:
            section: Nombre de la sección (DATABASE, COMPANY, UI, etc.)
            
        Returns:
            Diccionario con la configuración de la sección
        """
        section = section.upper()
        config_map = {
            'DATABASE': self.DATABASE_CONFIG,
            'COMPANY': self.COMPANY_CONFIG,
            'UI': self.UI_CONFIG,
            'REPORTS': self.REPORTS_CONFIG,
            'TICKETS': self.TICKETS_CONFIG,
            'BARCODE': self.BARCODE_CONFIG,
            'INVENTORY': self.INVENTORY_CONFIG,
            'SALES': self.SALES_CONFIG,
            'SECURITY': self.SECURITY_CONFIG,
            'LOGGING': self.LOGGING_CONFIG
        }
        
        return config_map.get(section, {})
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        Actualizar un valor específico de configuración.
        
        Args:
            section: Nombre de la sección
            key: Clave a actualizar
            value: Nuevo valor
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            config_section = self.get_config_section(section)
            if key in config_section:
                config_section[key] = value
                return True
            return False
        except Exception:
            return False
    
    def get_database_path(self) -> str:
        """Obtener ruta completa de la base de datos."""
        return self.DATABASE_CONFIG['path']
    
    def get_reports_path(self) -> str:
        """Obtener ruta de reportes."""
        return self.REPORTS_CONFIG['save_path']
    
    def get_logs_path(self) -> str:
        """Obtener ruta de logs."""
        return str(self.LOGS_DIR)


# Instancia global de configuración
config = SystemConfig()

# Funciones de conveniencia para acceso rápido
def get_database_config() -> Dict[str, Any]:
    """Obtener configuración de base de datos."""
    return config.DATABASE_CONFIG

def get_company_config() -> Dict[str, Any]:
    """Obtener configuración de empresa."""
    return config.COMPANY_CONFIG

def get_ui_config() -> Dict[str, Any]:
    """Obtener configuración de interfaz."""
    return config.UI_CONFIG

def get_reports_config() -> Dict[str, Any]:
    """Obtener configuración de reportes."""
    return config.REPORTS_CONFIG

def get_tickets_config() -> Dict[str, Any]:
    """Obtener configuración de tickets."""
    return config.TICKETS_CONFIG

def get_barcode_config() -> Dict[str, Any]:
    """Obtener configuración de códigos de barras."""
    return config.BARCODE_CONFIG

def get_security_config() -> Dict[str, Any]:
    """Obtener configuración de seguridad."""
    return config.SECURITY_CONFIG

def get_logging_config() -> Dict[str, Any]:
    """Obtener configuración de logging."""
    return config.LOGGING_CONFIG

# Variables de entorno y configuración dinámica
def setup_environment():
    """Configurar variables de entorno del sistema."""
    os.environ['INVENTORY_ROOT'] = str(config.PROJECT_ROOT)
    os.environ['INVENTORY_DATA'] = str(config.DATA_DIR)
    os.environ['INVENTORY_LOGS'] = str(config.LOGS_DIR)

# Configurar entorno al importar
setup_environment()

# Metadatos
__version__ = '1.0.0'
__author__ = 'Sistema de Inventario'
__description__ = 'Configuración centralizada del sistema'
