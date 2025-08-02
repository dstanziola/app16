"""
Módulo UI Main - Ventana Principal del Sistema

Este módulo contiene la ventana principal y el sistema de navegación
principal del sistema de inventario.

Componentes principales:
- MainWindow: Ventana principal con menús y navegación
- WindowManager: Gestor de ventanas secundarias  
- MenuFactory: Factory para creación de menús
- NavigationController: Controlador de navegación

Responsabilidades:
- Gestión ventana principal del sistema
- Sistema de navegación entre módulos
- Gestión de menús y toolbars
- Coordinación con sistema de autenticación

Fecha: 2025-07-17
Estado: P03 - Corrección crítica importaciones
"""

from .main_window import start_main_window, MainWindow

__version__ = '2.0.0'
__description__ = 'Ventana Principal - Sistema de Navegación'

# Exportar componentes principales
__all__ = [
    'start_main_window',
    'MainWindow'
]

# Configuración de la ventana principal
MAIN_WINDOW_CONFIG = {
    'title': 'Sistema de Gestión de Inventario v5.0 - Copy Point S.A.',
    'width': 1200,
    'height': 800,
    'min_width': 1024,
    'min_height': 768,
    'center_on_screen': True,
    'resizable': True
}

# Configuración de menús
MENU_CONFIG = {
    'show_tooltips': True,
    'show_icons': True,
    'show_shortcuts': True,
    'enable_context_menus': True
}
