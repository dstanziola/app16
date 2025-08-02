"""
Módulo Services - Capa de Aplicación

Este módulo contiene todos los servicios de aplicación que implementan
los casos de uso del sistema siguiendo principios de Clean Architecture.

Servicios disponibles:
- ProductService: Gestión de productos
- CategoryService: Gestión de categorías
- ClientService: Gestión de clientes
- SalesService: Gestión de ventas
- MovementService: Gestión de movimientos
- ReportService: Generación de reportes
- ExportService: Exportación de datos
- AuthService: Autenticación y autorización

ServiceContainer:
- Inyección de dependencias
- Gestión del ciclo de vida de servicios
- Lazy loading de dependencias
- Configuración automática

Fecha: 2025-07-17
Estado: P03 - Corrección crítica importaciones
"""

from .service_container import (
    get_container, 
    setup_default_container, 
    cleanup_container,
    ServiceContainer
)

__version__ = '2.0.0'
__description__ = 'Capa de Aplicación - Servicios y Casos de Uso'

# Exportar componentes principales
__all__ = [
    'get_container',
    'setup_default_container',
    'cleanup_container', 
    'ServiceContainer'
]

# Configuración de servicios por defecto
DEFAULT_SERVICES = [
    'product_service',
    'category_service', 
    'client_service',
    'sales_service',
    'movement_service',
    'report_service',
    'export_service',
    'auth_service',
    'user_service',
    'ticket_service'
]

# Configuración del ServiceContainer
CONTAINER_CONFIG = {
    'lazy_loading': True,
    'auto_register': True,
    'singleton_by_default': True,
    'thread_safe': True
}
