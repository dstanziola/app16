"""
BaseForm - Clase base para formularios del sistema
Arquitectura: Clean Architecture - Capa Presentación  
Patrón: Template Method + MVP
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
import logging
from typing import Optional

from utils.logger import get_logger


class BaseForm(ABC):
    """
    Clase base abstracta para todos los formularios del sistema
    
    Implementa patrón Template Method para estandarizar:
    - Inicialización común
    - Manejo de ventanas
    - Logging estándar
    - Ciclo de vida de formularios
    """
    
    def __init__(self, parent: tk.Widget, db_connection):
        """
        Constructor base para formularios
        
        Args:
            parent: Widget padre (ventana principal)
            db_connection: Conexión base de datos
        """
        self.parent = parent
        self.db = db_connection
        self.window: Optional[tk.Toplevel] = None
        self.logger = get_logger(self.__class__.__name__)
        
        # Variables comunes
        self.is_initialized = False
        self.is_destroyed = False
        
        self.logger.debug(f"{self.__class__.__name__} inicializando...")
    
    @abstractmethod
    def show(self) -> None:
        """
        Mostrar formulario - debe ser implementado por cada subclase
        """
        pass
    
    def hide(self) -> None:
        """
        Ocultar formulario (común para todos los formularios)
        """
        try:
            if self.window and not self.is_destroyed:
                self.window.withdraw()
                self.logger.debug(f"{self.__class__.__name__} ocultado")
        except Exception as e:
            self.logger.error(f"Error ocultando formulario: {e}")
    
    def destroy(self) -> None:
        """
        Destruir formulario y limpiar recursos (común para todos)
        """
        try:
            if self.window and not self.is_destroyed:
                self.window.destroy()
                self.window = None
                self.is_destroyed = True
                self.logger.debug(f"{self.__class__.__name__} destruido")
        except Exception as e:
            self.logger.error(f"Error destruyendo formulario: {e}")
    
    def center_window(self, width: int = None, height: int = None) -> None:
        """
        Centrar ventana en pantalla (utilidad común)
        
        Args:
            width: Ancho personalizado (opcional)
            height: Alto personalizado (opcional)
        """
        try:
            if not self.window:
                return
                
            self.window.update_idletasks()
            
            # Usar dimensiones específicas o las actuales
            w = width or self.window.winfo_width()
            h = height or self.window.winfo_height()
            
            # Calcular posición centrada
            x = (self.window.winfo_screenwidth() // 2) - (w // 2)
            y = (self.window.winfo_screenheight() // 2) - (h // 2)
            
            self.window.geometry(f"{w}x{h}+{x}+{y}")
            
        except Exception as e:
            self.logger.error(f"Error centrando ventana: {e}")
    
    def set_window_properties(self, title: str, geometry: str = None, 
                             resizable: bool = True, modal: bool = True) -> None:
        """
        Configurar propiedades comunes de ventana
        
        Args:
            title: Título de la ventana
            geometry: Geometría (ej: "800x600")
            resizable: Si la ventana es redimensionable
            modal: Si la ventana es modal
        """
        try:
            if not self.window:
                return
                
            self.window.title(title)
            
            if geometry:
                self.window.geometry(geometry)
            
            self.window.resizable(resizable, resizable)
            
            if modal:
                self.window.transient(self.parent)
                self.window.grab_set()
                
        except Exception as e:
            self.logger.error(f"Error configurando propiedades ventana: {e}")
    
    def bind_events(self) -> None:
        """
        Vincular eventos comunes (puede ser sobrescrito)
        """
        try:
            if self.window:
                # Evento de cierre de ventana
                self.window.protocol("WM_DELETE_WINDOW", self.destroy)
                
                # Evento ESC para cerrar
                self.window.bind('<Escape>', lambda e: self.destroy())
                
        except Exception as e:
            self.logger.error(f"Error vinculando eventos: {e}")
    
    def validate_initialization(self) -> bool:
        """
        Validar que el formulario se inicializó correctamente
        
        Returns:
            bool: True si está correctamente inicializado
        """
        try:
            if not self.parent:
                self.logger.error("Parent widget no definido")
                return False
                
            if not self.db:
                self.logger.warning("Database connection no definida")
                # No es crítico para todos los formularios
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando inicialización: {e}")
            return False
    
    def handle_error(self, error: Exception, user_message: str = None) -> None:
        """
        Manejo centralizado de errores para formularios
        
        Args:
            error: Excepción ocurrida
            user_message: Mensaje personalizado para el usuario
        """
        try:
            # Log técnico
            self.logger.error(f"Error en {self.__class__.__name__}: {error}")
            
            # Mensaje al usuario
            if user_message:
                from tkinter import messagebox
                messagebox.showerror("Error", user_message)
            
        except Exception as e:
            # Error crítico en manejo de errores
            print(f"Error crítico en handle_error: {e}")
    
    def get_form_status(self) -> dict:
        """
        Obtener estado actual del formulario (útil para debugging)
        
        Returns:
            dict: Estado del formulario
        """
        return {
            'class_name': self.__class__.__name__,
            'is_initialized': self.is_initialized,
            'is_destroyed': self.is_destroyed,
            'has_window': self.window is not None,
            'has_parent': self.parent is not None,
            'has_db': self.db is not None
        }


class SimpleForm(BaseForm):
    """
    Implementación simple de BaseForm para casos básicos
    """
    
    def __init__(self, parent: tk.Widget, db_connection=None):
        super().__init__(parent, db_connection)
        
        # Crear ventana simple
        self.window = tk.Toplevel(parent)
        self.set_window_properties("Formulario Simple", "400x300", True, True)
        self.bind_events()
        self.center_window()
        
        self.is_initialized = True
    
    def show(self) -> None:
        """Implementación básica de show"""
        if self.window and not self.is_destroyed:
            self.window.deiconify()
            self.window.focus_set()


# Factory function para crear formularios básicos
def create_simple_form(parent: tk.Widget, title: str = "Formulario", 
                      geometry: str = "400x300") -> SimpleForm:
    """
    Factory function para crear formularios simples
    
    Args:
        parent: Widget padre
        title: Título del formulario
        geometry: Geometría de la ventana
        
    Returns:
        SimpleForm: Instancia del formulario
    """
    form = SimpleForm(parent)
    form.set_window_properties(title, geometry)
    return form


if __name__ == "__main__":
    # Test básico de BaseForm
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    try:
        # Crear formulario simple de prueba
        test_form = create_simple_form(root, "Test BaseForm", "500x400")
        test_form.show()
        
        # Agregar contenido de prueba
        test_label = ttk.Label(test_form.window, text="BaseForm Test")
        test_label.pack(pady=20)
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error en test BaseForm: {e}")
    finally:
        root.destroy()
