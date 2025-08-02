"""
Módulo UI - Capa de Presentación

Este módulo contiene toda la interfaz de usuario del sistema
implementada con Tkinter siguiendo el patrón MVP.

Submódulos disponibles:
- auth: Autenticación y gestión de sesiones
- main: Ventana principal y navegación
- forms: Formularios específicos por funcionalidad
- widgets: Componentes reutilizables
- components: Componentes complejos

Patrones aplicados:
- MVP (Model-View-Presenter)
- Factory Pattern para creación de ventanas
- Observer Pattern para eventos UI

Fecha: 2025-07-17
Estado: P03 - Corrección crítica importaciones
"""

__version__ = '2.0.0'
__description__ = 'Capa de Presentación - Clean Architecture'

# Constantes de UI
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768
DEFAULT_FONT_FAMILY = 'Arial'
DEFAULT_FONT_SIZE = 10

# Configuración de colores
UI_COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'success': '#F18F01',
    'danger': '#C73E1D',
    'background': '#F5F5F5',
    'text': '#333333'
}

# Configuración de ventanas
WINDOW_CONFIG = {
    'resizable': True,
    'center_on_screen': True,
    'min_width': 800,
    'min_height': 600
}
