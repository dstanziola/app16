"""
Definición de estilos para la interfaz gráfica de la aplicación.

Fecha: 10/04/2025 15:00:00
Ruta: D:/inventory_app/styles.py
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

# Colores
# COLOR_PRIMARY = "#126782"      # Azul principal #396ea3  3498db
# COLOR_SECONDARY = "#FFB703"    # Verde secundario #2ecc71
# COLOR_WARNING = "#FB8500"      # Naranja para advertencias "#f39c12"
# COLOR_DANGER = "#e74c3c"       # Rojo para errores o peligro "#e74c3c"
# COLOR_GRAY = "#00a5a6"         # Gris para elementos deshabilitados 95a5a6
# COLOR_DARK = "#023047"         # Oscuro para textos y bordes "#95a5a6"         # Gris para elementos deshabilitados
# COLOR_LIGHT = "#8ECAE6"        # Claro para fondos "#ecf0f1"
# COLOR_WHITE = "#ffffff"        # Blanco "#ffffff"
# COLOR_BLACK = "#000000"        # Negro "#000000"

# Colores Modernos para GUI de Inventario

COLOR_PRIMARY     = "#2563EB"  # Azul vivo pero elegante (similar a Tailwind blue-600)
COLOR_SECONDARY   = "#FACC15"  # Amarillo dorado suave para resaltar sin saturar
COLOR_WARNING     = "#F59E0B"  # Naranja más suave y elegante
COLOR_DANGER      = "#EF4444"  # Rojo coral moderno
COLOR_GRAY        = "#94A3B8"  # Gris neutro para textos, bordes y desactivados
COLOR_DARK        = "#1E293B"  # Azul oscuro profundo, elegante para fondo o encabezados
COLOR_LIGHT       = "#E2E8F0"  # Azul grisáceo claro, ideal para fondo de secciones
COLOR_WHITE       = "#FFFFFF"  # Blanco puro
COLOR_BLACK       = "#0F172A"  # Azul negruzco más suave que el negro absoluto

# Fuentes
FONT_FAMILY = "Segoe UI"  # Fuente principal
FONT_SIZE_SMALL = 9       # Tamaño pequeño
FONT_SIZE_NORMAL = 10     # Tamaño normal
FONT_SIZE_LARGE = 12      # Tamaño grande
FONT_SIZE_TITLE = 14      # Tamaño para títulos

# Padding y Márgenes
PADDING_SMALL = 5         # Padding pequeño
PADDING_NORMAL = 10       # Padding normal
PADDING_LARGE = 15        # Padding grande
MARGIN_SMALL = 5          # Margen pequeño
MARGIN_NORMAL = 10        # Margen normal
MARGIN_LARGE = 15         # Margen grande

# Bordes
BORDER_WIDTH = 1          # Ancho del borde
BORDER_RADIUS = 4         # Radio del borde

# Definiciones de estilos

class Styles:
    """
    Clase para manejar los estilos de la aplicación.
    Proporciona estilos para diferentes tipos de widgets.
    """
    
    @staticmethod
    def configure_ttk_styles(style: Any) -> None:
        """
        Configura los estilos ttk para la aplicación.
        
        Args:
            style: Objeto ttk.Style.
        """
        # Configuración de estilo para ttkbootstrap o ttk estándar
        style.configure(
            "TLabel",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            background=COLOR_LIGHT,
            foreground=COLOR_DARK
        )
        
        style.configure(
            "TButton",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            background=COLOR_PRIMARY,
            foreground=COLOR_WHITE,
            padding=(PADDING_NORMAL, PADDING_SMALL)
        )
        
        style.configure(
            "Danger.TButton",
            background=COLOR_DANGER,
            foreground=COLOR_WHITE
        )
        
        style.configure(
            "Warning.TButton",
            background=COLOR_WARNING,
            foreground=COLOR_WHITE
        )
        
        style.configure(
            "Success.TButton",
            background=COLOR_SECONDARY,
            foreground=COLOR_WHITE
        )
        
        style.configure(
            "TEntry",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fieldbackground=COLOR_WHITE
        )
        
        style.configure(
            "TCombobox",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fieldbackground=COLOR_WHITE
        )
        
        style.configure(
            "Treeview",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            background=COLOR_WHITE,
            fieldbackground=COLOR_WHITE
        )
        
        style.configure(
            "Treeview.Heading",
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            background=COLOR_LIGHT,
            foreground=COLOR_DARK
        )
        
        # Configurar el estilo para MoneyEntry si está disponible
        style.configure(
            'MoneyEntry.TEntry',
            foreground='#000066',
            fieldbackground='#FAFAFA',
            padding=5
        )
    
    @staticmethod
    def main_window_style() -> Dict[str, Any]:
        """
        Estilo para la ventana principal.
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "bg": COLOR_LIGHT,
            "padx": PADDING_LARGE,
            "pady": PADDING_LARGE
        }
    
    @staticmethod
    def frame_style() -> Dict[str, Any]:
        """
        Estilo para marcos (frames).
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "bg": COLOR_LIGHT,
            "padx": PADDING_NORMAL,
            "pady": PADDING_NORMAL,
            "bd": BORDER_WIDTH,
            "relief": tk.GROOVE
        }
    
    @staticmethod
    def title_style() -> Dict[str, Any]:
        """
        Estilo para títulos.
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "font": (FONT_FAMILY, FONT_SIZE_TITLE, "bold"),
            "bg": COLOR_LIGHT,
            "fg": COLOR_DARK,
            "pady": PADDING_NORMAL
        }
    
    @staticmethod
    def label_style() -> Dict[str, Any]:
        """
        Estilo para etiquetas (labels).
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "font": (FONT_FAMILY, FONT_SIZE_NORMAL),
            "bg": COLOR_LIGHT,
            "fg": COLOR_DARK,
            "anchor": tk.W
        }
    
    @staticmethod
    def entry_style() -> Dict[str, Any]:
        """
        Estilo para campos de entrada (entries).
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "font": (FONT_FAMILY, FONT_SIZE_NORMAL),
            "bg": COLOR_WHITE,
            "fg": COLOR_BLACK,
            "bd": BORDER_WIDTH,
            "relief": tk.SOLID
        }
    
    @staticmethod
    def button_style() -> Dict[str, Any]:
        """
        Estilo para botones.
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "font": (FONT_FAMILY, FONT_SIZE_NORMAL),
            "bg": COLOR_PRIMARY,
            "fg": COLOR_WHITE,
            "padx": PADDING_NORMAL,
            "pady": PADDING_SMALL,
            "bd": 0,
            "relief": tk.FLAT,
            "activebackground": COLOR_DARK,
            "activeforeground": COLOR_WHITE,
            "cursor": "hand2"
        }
    
    @staticmethod
    def listbox_style() -> Dict[str, Any]:
        """
        Estilo para listboxes.
        
        Returns:
            Dict[str, Any]: Diccionario con los estilos.
        """
        return {
            "font": (FONT_FAMILY, FONT_SIZE_NORMAL),
            "bg": COLOR_WHITE,
            "fg": COLOR_BLACK,
            "bd": BORDER_WIDTH,
            "relief": tk.SOLID,
            "selectbackground": COLOR_PRIMARY,
            "selectforeground": COLOR_WHITE
        }
    
    @staticmethod
    def apply_to_widget(widget: tk.Widget, style_dict: Dict[str, Any]) -> None:
        """
        Aplica un estilo a un widget.
        
        Args:
            widget: Widget al que aplicar el estilo.
            style_dict: Diccionario con los estilos a aplicar.
        """
        for key, value in style_dict.items():
            try:
                widget[key] = value
            except tk.TclError:
                pass  # Ignorar propiedades no soportadas por el widget