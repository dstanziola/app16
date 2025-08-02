"""
Gestor de ventanas mejorado para prevenir errores de Tkinter.

Este módulo proporciona funciones utilitarias para gestionar ventanas
de forma segura, evitando referencias a widgets destruidos.
"""

import tkinter as tk
from typing import Dict, Any, Optional
import logging

class WindowManager:
    """Gestor centralizado de ventanas secundarias."""
    
    def __init__(self):
        self._windows: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def register_window(self, name: str, window: Any) -> None:
        """
        Registra una ventana en el gestor.
        
        Args:
            name: Nombre único de la ventana
            window: Instancia de la ventana
        """
        # Cerrar ventana anterior si existe
        if name in self._windows:
            self.close_window(name)
            
        self._windows[name] = window
        
        # Configurar callback de cierre
        if hasattr(window, 'root'):
            window.root.protocol("WM_DELETE_WINDOW", lambda: self._on_window_close(name))
            
    def get_window(self, name: str) -> Optional[Any]:
        """
        Obtiene una ventana por nombre.
        
        Args:
            name: Nombre de la ventana
            
        Returns:
            Instancia de la ventana o None si no existe
        """
        return self._windows.get(name)
        
    def is_window_open(self, name: str) -> bool:
        """
        Verifica si una ventana está abierta y válida.
        
        Args:
            name: Nombre de la ventana
            
        Returns:
            True si la ventana existe y es válida
        """
        if name not in self._windows:
            return False
            
        window = self._windows[name]
        
        # Verificar si la ventana y su root existen
        if not hasattr(window, 'root'):
            self._remove_window(name)
            return False
            
        try:
            # Intentar acceder al estado de la ventana
            window.root.winfo_exists()
            return True
        except (tk.TclError, AttributeError):
            self._remove_window(name)
            return False
            
    def bring_to_front(self, name: str) -> bool:
        """
        Trae una ventana al frente.
        
        Args:
            name: Nombre de la ventana
            
        Returns:
            True si la operación fue exitosa
        """
        if not self.is_window_open(name):
            return False
            
        try:
            window = self._windows[name]
            window.root.lift()
            window.root.focus_force()
            return True
        except (tk.TclError, AttributeError):
            self._remove_window(name)
            return False
            
    def close_window(self, name: str) -> None:
        """
        Cierra una ventana específica.
        
        Args:
            name: Nombre de la ventana
        """
        if name in self._windows:
            window = self._windows[name]
            try:
                if hasattr(window, 'root') and window.root.winfo_exists():
                    window.root.destroy()
            except (tk.TclError, AttributeError):
                pass
            finally:
                self._remove_window(name)
                
    def close_all_windows(self) -> None:
        """Cierra todas las ventanas registradas."""
        for name in list(self._windows.keys()):
            self.close_window(name)
            
    def _on_window_close(self, name: str) -> None:
        """Callback interno para manejar cierre de ventana."""
        self._remove_window(name)
        
    def _remove_window(self, name: str) -> None:
        """Remueve una ventana del registro."""
        if name in self._windows:
            del self._windows[name]
            self.logger.debug(f"Ventana '{name}' removida del gestor")
    
    @staticmethod
    def center_window(window, width: int, height: int) -> None:
        """
        Centra una ventana en la pantalla.
        
        Args:
            window: Ventana de Tkinter a centrar
            width: Ancho deseado de la ventana
            height: Alto deseado de la ventana
        """
        try:
            # Obtener dimensiones de la pantalla
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calcular posición centrada
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            # Asegurar que la ventana no quede fuera de la pantalla
            x = max(0, x)
            y = max(0, y)
            
            # Aplicar geometría
            window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            # Si hay error, usar geometría simple sin centrar
            window.geometry(f"{width}x{height}")

# Instancia global del gestor
window_manager = WindowManager()


def safe_widget_config(widget, **kwargs):
    """
    Configura un widget de forma segura.
    
    Args:
        widget: Widget de Tkinter
        **kwargs: Opciones de configuración
        
    Returns:
        True si la configuración fue exitosa
    """
    try:
        if widget and widget.winfo_exists():
            widget.config(**kwargs)
            return True
    except (tk.TclError, AttributeError):
        pass
    return False


def safe_widget_state(widget, state: str) -> bool:
    """
    Cambia el estado de un widget de forma segura.
    
    Args:
        widget: Widget de Tkinter
        state: Nuevo estado ('normal', 'disabled', etc.)
        
    Returns:
        True si el cambio fue exitoso
    """
    return safe_widget_config(widget, state=state)


def validate_widget_exists(widget) -> bool:
    """
    Valida que un widget existe y es accesible.
    
    Args:
        widget: Widget de Tkinter
        
    Returns:
        True si el widget es válido
    """
    try:
        return widget and widget.winfo_exists()
    except (tk.TclError, AttributeError):
        return False
