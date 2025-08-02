"""
ui/widgets/decimal_entry.py
Widget personalizado para entrada de números decimales con validación en tiempo real.

Implementación TDD siguiendo Clean Architecture.
Autor: Sistema TDD
Fecha: 15 Junio 2025
"""

import tkinter as tk
from tkinter import ttk
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Callable
import logging


class DecimalEntry(ttk.Entry):
    """
    Widget de entrada para números decimales con validación en tiempo real.
    
    Características implementadas según requerimientos:
    - Solo permite números reales positivos/negativos
    - Un único punto decimal
    - Máximo N decimales (configurable, default: 2)
    - Formato automático con separadores de miles al salir del campo
    - Alineación a la derecha
    - Validación de caracteres en tiempo real
    - Rechaza entrada de caracteres inválidos
    
    Casos de uso cubiertos:
    - Entrada 1234 → Mostrar 1,234.00
    - Entrada 5.2 → Mostrar 5.20  
    - Entrada 0 → Mostrar 0.00
    - Entrada 1234.567 → Rechaza el 7
    - Entrada abc → No permite el ingreso
    - Campo vacío → No genera error, permanece vacío
    """
    
    def __init__(self, parent, decimal_places: int = 2, 
                 allow_negative: bool = True, 
                 on_value_change: Optional[Callable] = None,
                 max_value: Optional[Decimal] = None,
                 min_value: Optional[Decimal] = None,
                 **kwargs):
        """
        Inicializa el widget DecimalEntry.
        
        Args:
            parent: Widget padre
            decimal_places: Número de decimales permitidos (default: 2)
            allow_negative: Si permite números negativos (default: True)
            on_value_change: Callback cuando cambia el valor
            max_value: Valor máximo permitido (opcional)
            min_value: Valor mínimo permitido (opcional)
            **kwargs: Argumentos adicionales para ttk.Entry
        """
        # Configurar estilo por defecto según requerimientos
        default_kwargs = {
            'justify': 'right',  # Alineación a la derecha
            'font': ('Segoe UI', 10),
            'width': 15
        }
        default_kwargs.update(kwargs)
        
        # CORRECCIÓN: Inicializar Entry ANTES de configurar validación
        super().__init__(parent, **default_kwargs)
        
        # Configuración del widget
        self.decimal_places = decimal_places
        self.allow_negative = allow_negative
        self.on_value_change = on_value_change
        self.max_value = max_value
        self.min_value = min_value
        
        # Control de estado interno
        self._is_formatting = False  # Flag para evitar recursión
        self._last_valid_value = ""
        
        # Logger para debugging
        self.logger = logging.getLogger(f"DecimalEntry.{id(self)}")
        
        # CORRECCIÓN: Configurar validación DESPUÉS de inicialización completa
        self._setup_widget()
        
    def _setup_widget(self):
        """Configurar validación y eventos del widget."""
        # Registrar validadores y eventos
        self._register_validators()
        self._bind_events()
        
    def _register_validators(self):
        """Registra los validadores de entrada en tiempo real."""
        # CORRECCIÓN: Usar validación simplificada que no bloquee inserciones
        # Solo validar en eventos específicos, no en cada tecla
        pass  # Deshabilitado temporalmente para debugging
        
    def _bind_events(self):
        """Configura los eventos del widget."""
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<Return>', self._on_focus_out)
        self.bind('<KeyRelease>', self._on_key_release)  # Usar KeyRelease en lugar de KeyPress
        
    def _on_key_release(self, event):
        """Validar después de que se suelte la tecla."""
        current_value = self.get()
        
        # Solo validar si hay contenido
        if current_value:
            # Validar formato básico
            if not self._is_valid_decimal_format(current_value):
                # Restaurar último valor válido
                if self._last_valid_value:
                    self.delete(0, tk.END)
                    self.insert(0, self._last_valid_value)
                else:
                    # Limpiar caracteres inválidos
                    clean_value = self._clean_invalid_chars(current_value)
                    if clean_value != current_value:
                        self.delete(0, tk.END)
                        self.insert(0, clean_value)
            else:
                # Validar decimales
                if '.' in current_value:
                    parts = current_value.split('.')
                    if len(parts) == 2 and len(parts[1]) > self.decimal_places:
                        # Truncar decimales extras
                        truncated = f"{parts[0]}.{parts[1][:self.decimal_places]}"
                        self.delete(0, tk.END)
                        self.insert(0, truncated)
                        
    def _clean_invalid_chars(self, value: str) -> str:
        """Limpiar caracteres inválidos de una cadena."""
        # Permitir solo dígitos, punto y signo negativo al inicio
        allowed_chars = '0123456789.'
        if self.allow_negative:
            allowed_chars += '-'
            
        # Filtrar caracteres válidos
        clean = ''
        decimal_found = False
        
        for i, char in enumerate(value):
            if char in '0123456789':
                clean += char
            elif char == '.' and not decimal_found:
                clean += char
                decimal_found = True
            elif char == '-' and i == 0 and self.allow_negative:
                clean += char
                
        return clean
        
    def _validate_char(self, new_value: str, char: str, action: str) -> bool:
        """
        Valida cada carácter ingresado en tiempo real.
        
        Args:
            new_value: Valor completo después del carácter
            char: Carácter que se está ingresando
            action: Tipo de acción (1=insert, 0=delete)
            
        Returns:
            bool: True si el carácter es válido, False si se rechaza
        """
        # Permitir delete/backspace
        if action == '0':
            return True
            
        # Permitir campo vacío
        if not new_value.strip():
            return True
            
        try:
            # Validar formato básico
            if not self._is_valid_decimal_format(new_value):
                self.logger.debug(f"Formato inválido: '{new_value}'")
                return False
                
            # Validar signo negativo
            if char == '-':
                if not self.allow_negative:
                    self.logger.debug("Números negativos no permitidos")
                    return False
                if len(new_value) != 1:  # Solo al inicio
                    self.logger.debug("Signo negativo solo al inicio")
                    return False
                return True
                
            # Validar que solo sean dígitos o punto decimal
            if not (char.isdigit() or char == '.'):
                self.logger.debug(f"Carácter inválido: '{char}'")
                return False
                
            # Validar número de decimales
            if '.' in new_value:
                parts = new_value.split('.')
                if len(parts) > 2:  # Múltiples puntos
                    self.logger.debug("Múltiples puntos decimales")
                    return False
                if len(parts[1]) > self.decimal_places:
                    self.logger.debug(f"Demasiados decimales: {len(parts[1])} > {self.decimal_places}")
                    return False
                    
            # Validar rango si está configurado
            if self._is_complete_number(new_value):
                try:
                    decimal_val = Decimal(new_value)
                    if self.max_value is not None and decimal_val > self.max_value:
                        self.logger.debug(f"Valor excede máximo: {decimal_val} > {self.max_value}")
                        return False
                    if self.min_value is not None and decimal_val < self.min_value:
                        self.logger.debug(f"Valor menor que mínimo: {decimal_val} < {self.min_value}")
                        return False
                except InvalidOperation:
                    pass  # Formato incompleto, continuar validación
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error en validación: {e}")
            return False
            
    def _on_invalid(self, attempted_value: str, char: str):
        """
        Maneja caracteres rechazados por la validación.
        
        Args:
            attempted_value: Valor que se intentó ingresar
            char: Carácter rechazado
        """
        self.logger.debug(f"Carácter rechazado: '{char}' en '{attempted_value}'")
        # Opcional: mostrar feedback visual o sonido
        self.bell()  # Sonido de error del sistema
        
    def _is_valid_decimal_format(self, value: str) -> bool:
        """
        Valida que el formato sea un número decimal válido.
        
        Args:
            value: Valor a validar
            
        Returns:
            bool: True si es formato válido
        """
        # Patrones válidos para números decimales
        patterns = [
            r'^-?\d*$',           # Solo dígitos (con signo opcional)
            r'^-?\d*\.$',         # Dígitos con punto al final
            r'^-?\d*\.\d*$',      # Número decimal completo
        ]
        
        return any(re.match(pattern, value) for pattern in patterns)
        
    def _is_complete_number(self, value: str) -> bool:
        """
        Verifica si el valor es un número completo (no formato intermedio).
        
        Args:
            value: Valor a verificar
            
        Returns:
            bool: True si es número completo
        """
        try:
            Decimal(value)
            return True
        except (ValueError, InvalidOperation):
            return False
            
    def _on_key_press(self, event):
        """Maneja eventos de teclas especiales."""
        # Permitir teclas de control (backspace, delete, arrows, etc.)
        control_keys = {
            'BackSpace', 'Delete', 'Left', 'Right', 
            'Home', 'End', 'Tab', 'Return', 'Escape'
        }
        
        if event.keysym in control_keys:
            return
            
        # Para Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X, etc.
        if event.state & 0x4:  # Ctrl presionado
            return
            
    def _on_click(self, event):
        """Maneja clicks del mouse para selección."""
        # Permitir selección normal
        pass
        
    def _on_focus_out(self, event=None):
        """
        Formatea el valor cuando se pierde el foco.
        Aplica formato con separadores de miles y decimales fijos.
        
        Implementa los casos de uso requeridos:
        - 1234 → 1,234.00
        - 5.2 → 5.20
        - 0 → 0.00
        """
        if self._is_formatting:
            return
            
        current_value = self.get().strip()
        
        # Si está vacío, no hacer nada (caso de uso: campo vacío permitido)
        if not current_value:
            return
            
        try:
            # Limpiar formato existente para conversión
            clean_value = current_value.replace(',', '')
            
            # Convertir a Decimal para precisión
            decimal_value = Decimal(clean_value)
            
            # Validar rango final
            if self.max_value is not None and decimal_value > self.max_value:
                decimal_value = self.max_value
            if self.min_value is not None and decimal_value < self.min_value:
                decimal_value = self.min_value
                
            # Formatear con separadores de miles y decimales fijos
            formatted_value = self._format_decimal(decimal_value)
            
            # Actualizar el campo
            self._is_formatting = True
            self.delete(0, tk.END)
            self.insert(0, formatted_value)
            self._is_formatting = False
            
            # Guardar como último valor válido
            self._last_valid_value = formatted_value
            
            # Callback de cambio de valor
            if self.on_value_change:
                try:
                    # Usar after_idle para evitar problemas de recursión
                    self.after_idle(lambda: self._safe_callback(decimal_value))
                except Exception as e:
                    self.logger.error(f"Error en callback: {e}")
                    
        except (ValueError, InvalidOperation) as e:
            self.logger.warning(f"Error formateando valor '{current_value}': {e}")
            # Si hay error, restaurar último valor válido
            self._is_formatting = True
            self.delete(0, tk.END)
            self.insert(0, self._last_valid_value)
            self._is_formatting = False
            
    def _format_decimal(self, value: Decimal) -> str:
        """
        Formatea un valor Decimal con separadores de miles y decimales fijos.
        
        Args:
            value: Valor Decimal a formatear
            
        Returns:
            str: Valor formateado (ej: "1,234.50")
        """
        try:
            # Crear formato con decimales fijos
            format_str = f"{{:,.{self.decimal_places}f}}"
            return format_str.format(float(value))
        except Exception as e:
            self.logger.error(f"Error formateando decimal {value}: {e}")
            # Fallback: formatear sin separadores
            return f"{float(value):.{self.decimal_places}f}"
        
    def get_decimal(self) -> Optional[Decimal]:
        """
        Obtiene el valor actual como Decimal.
        
        Returns:
            Decimal: Valor actual o None si es inválido/vacío
        """
        current_value = self.get().strip()
        
        if not current_value:
            return None
            
        try:
            # Remover separadores de miles para conversión
            clean_value = current_value.replace(',', '')
            return Decimal(clean_value)
        except (ValueError, InvalidOperation):
            self.logger.warning(f"No se pudo convertir '{current_value}' a Decimal")
            return None
            
    def set_value(self, value: Optional[Decimal]):
        """
        Establece un valor Decimal en el campo.
        
        Args:
            value: Valor Decimal a establecer o None para vacío
        """
        # CORRECCIÓN: Simplificar set_value para evitar problemas
        self.delete(0, tk.END)
        
        if value is not None:
            try:
                # Convertir a string sin formato inicialmente
                str_value = str(value)
                self.insert(0, str_value)
                self._last_valid_value = str_value
                
                self.logger.debug(f"set_value: {value} -> '{str_value}'")
                
                # Aplicar formato después
                self.after_idle(self._apply_format)
                
            except Exception as e:
                self.logger.error(f"Error en set_value {value}: {e}")
                
    def _apply_format(self):
        """Aplicar formato al valor actual."""
        try:
            current = self.get()
            if current:
                decimal_val = Decimal(current)
                formatted = self._format_decimal(decimal_val)
                
                self.delete(0, tk.END)
                self.insert(0, formatted)
                self._last_valid_value = formatted
        except Exception as e:
            self.logger.debug(f"Error aplicando formato: {e}")
        
    def clear(self):
        """Limpia el campo."""
        self.delete(0, tk.END)
        self._last_valid_value = ""
        
    def get_raw_value(self) -> str:
        """
        Obtiene el valor sin formato para depuración.
        
        Returns:
            str: Valor crudo del campo
        """
        return self.get()
        
    def is_valid(self) -> bool:
        """
        Verifica si el valor actual es válido.
        
        Returns:
            bool: True si el valor es válido
        """
        return self.get_decimal() is not None or self.get().strip() == ""


    
    def _safe_callback(self, value):
        """Ejecutar callback de forma segura."""
        try:
            if self.on_value_change and callable(self.on_value_change):
                self.on_value_change(value)
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.debug(f"Error en callback seguro: {e}")

# Factory functions para casos de uso comunes del sistema
def create_currency_entry(parent, **kwargs) -> DecimalEntry:
    """
    Crea un campo para moneda (2 decimales, sin negativos).
    Uso: precios, costos, totales.
    """
    defaults = {
        'decimal_places': 2,
        'allow_negative': False,
        'min_value': Decimal('0.00')
    }
    defaults.update(kwargs)
    return DecimalEntry(parent, **defaults)


def create_quantity_entry(parent, **kwargs) -> DecimalEntry:
    """
    Crea un campo para cantidades (3 decimales, sin negativos).
    Uso: stock, cantidades de venta.
    """
    defaults = {
        'decimal_places': 3,
        'allow_negative': False,
        'min_value': Decimal('0.000')
    }
    defaults.update(kwargs)
    return DecimalEntry(parent, **defaults)


def create_percentage_entry(parent, **kwargs) -> DecimalEntry:
    """
    Crea un campo para porcentajes (2 decimales, 0-100%).
    Uso: impuestos, descuentos.
    """
    defaults = {
        'decimal_places': 2,
        'allow_negative': False,
        'min_value': Decimal('0.00'),
        'max_value': Decimal('100.00')
    }
    defaults.update(kwargs)
    return DecimalEntry(parent, **defaults)


def create_discount_entry(parent, **kwargs) -> DecimalEntry:
    """
    Crea un campo para descuentos (2 decimales, 0-100%).
    Uso: descuentos en ventas.
    """
    return create_percentage_entry(parent, **kwargs)


def create_price_entry(parent, **kwargs) -> DecimalEntry:
    """
    Crea un campo para precios (2 decimales, sin negativos).
    Uso: precios de compra, venta.
    """
    return create_currency_entry(parent, **kwargs)


# Test de ejemplo y demostración
if __name__ == "__main__":
    # Configurar logging para debugging
    logging.basicConfig(level=logging.DEBUG)
    
    root = tk.Tk()
    root.title("Test DecimalEntry - Sistema de Inventario")
    root.geometry("500x400")
    
    # Frame principal con padding
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    title_label = ttk.Label(main_frame, text="Test Widget DecimalEntry", 
                           font=('Segoe UI', 14, 'bold'))
    title_label.pack(pady=(0, 20))
    
    # Ejemplos de uso según casos del sistema
    examples = [
        ("Precio de venta (moneda):", create_currency_entry),
        ("Cantidad en stock (3 decimales):", create_quantity_entry),
        ("Porcentaje de impuesto:", create_percentage_entry),
        ("Descuento aplicado:", create_discount_entry),
        ("Precio de compra:", create_price_entry)
    ]
    
    entries = {}
    
    for label_text, factory_func in examples:
        # Label
        label = ttk.Label(main_frame, text=label_text)
        label.pack(anchor='w', pady=(10, 2))
        
        # Entry usando factory apropiada
        entry = factory_func(main_frame, width=20)
        entry.pack(anchor='w', pady=(0, 5))
        
        # Guardar referencia
        entries[label_text] = entry
    
    # Frame para botones
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20, fill='x')
    
    def show_values():
        """Muestra los valores actuales de todos los campos."""
        print("\n" + "="*50)
        print("VALORES ACTUALES:")
        print("="*50)
        for label, entry in entries.items():
            raw_value = entry.get()
            decimal_value = entry.get_decimal()
            print(f"{label:<30} Raw: '{raw_value}' | Decimal: {decimal_value}")
        print("="*50)
        
    def load_test_values():
        """Carga valores de prueba para demostrar el formato."""
        test_values = [
            ("Precio de venta (moneda):", Decimal("1234.50")),
            ("Cantidad en stock (3 decimales):", Decimal("25.125")),
            ("Porcentaje de impuesto:", Decimal("18.00")),
            ("Descuento aplicado:", Decimal("5.75")),
            ("Precio de compra:", Decimal("999.99"))
        ]
        
        for label, value in test_values:
            if label in entries:
                entries[label].set_value(value)
                
    def clear_all():
        """Limpia todos los campos."""
        for entry in entries.values():
            entry.clear()
    
    # Botones de prueba
    ttk.Button(button_frame, text="Mostrar Valores", 
              command=show_values).pack(side='left', padx=(0, 5))
    ttk.Button(button_frame, text="Cargar Datos de Prueba", 
              command=load_test_values).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Limpiar Todo", 
              command=clear_all).pack(side='left', padx=5)
    
    # Instrucciones
    instructions = ttk.Label(main_frame, 
                           text="Instrucciones:\n" +
                                "• Ingrese números en cualquier campo\n" +
                                "• Presione Tab o click fuera para formatear\n" +
                                "• Intente ingresar letras o caracteres inválidos\n" +
                                "• Pruebe números con más decimales de los permitidos",
                           font=('Segoe UI', 9),
                           foreground='gray')
    instructions.pack(pady=10)
    
    root.mainloop()
