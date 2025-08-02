"""
Widget BarcodeEntry - Modo Teclado

Widget especializado para captura de códigos de barras usando lectores
configurados en modo HID teclado.

Características:
- Extiende ttk.Entry para compatibilidad total
- Manejo automático del evento <Return>
- Callback para procesamiento automático
- Validación en tiempo real opcional
- Configuración flexible de comportamiento
- Compatible con cualquier lector HID configurado como teclado

Modo de operación:
1. El lector de códigos de barras envía caracteres como si fuera un teclado
2. Al final envía un Return (<CR>) automáticamente
3. El widget detecta el Return y ejecuta el callback
4. Opcionalmente valida el código y limpia el campo

Autor: Sistema de Inventario Copy Point S.A.
Versión: 1.0.0
Fecha: Julio 2025
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Callable, Dict, Any, Union
import traceback

# Importaciones del sistema
try:
    from utils.barcode_utils import validate_barcode, BarcodeUtils
except ImportError:
    # Fallback si no están disponibles las utilidades
    def validate_barcode(code: str) -> bool:
        """Fallback validation function"""
        return bool(code and len(code.strip()) > 0)
    
    class BarcodeUtils:
        @staticmethod
        def normalize_code(code: str) -> str:
            return str(code).strip().upper()


# Configurar logging
logger = logging.getLogger(__name__)


class BarcodeEntryError(Exception):
    """Excepción base para errores del widget BarcodeEntry"""
    pass


class BarcodeEntry(ttk.Entry):
    """
    Widget Entry especializado para códigos de barras en modo teclado.
    
    Este widget está diseñado para funcionar con lectores de códigos de barras
    configurados en modo HID teclado, donde el lector simula escribir caracteres
    en el teclado y termina con un Return.
    
    Características principales:
    - Detección automática del evento Return
    - Callback personalizable para procesamiento
    - Validación opcional en tiempo real
    - Limpieza automática configurable
    - Manejo robusto de errores
    - Compatible con entrada manual y scanner
    
    Uso típico:
    ```python
    def on_code_scanned(code, is_valid=True):
        print(f"Código escaneado: {code}, Válido: {is_valid}")
    
    entry = BarcodeEntry(
        parent,
        on_scan_complete=on_code_scanned,
        validation_enabled=True,
        clear_after_scan=True
    )
    ```
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_scan_complete: Optional[Callable[[str, bool], None]] = None,
        validation_enabled: bool = True,
        clear_after_scan: bool = True,
        **kwargs
    ):
        """
        Inicializar BarcodeEntry.
        
        Args:
            parent: Widget padre
            on_scan_complete: Callback a ejecutar cuando se escanea un código.
                             Recibe (codigo: str, es_valido: bool)
            validation_enabled: Si habilitar validación en tiempo real
            clear_after_scan: Si limpiar el campo después del escaneo
            **kwargs: Argumentos adicionales para ttk.Entry
        
        Raises:
            TypeError: Si on_scan_complete no es callable
        """
        # Validar callback
        if on_scan_complete is not None and not callable(on_scan_complete):
            raise TypeError("on_scan_complete debe ser una función callable")
        
        # Inicializar Entry base
        super().__init__(parent, **kwargs)
        
        # Configuración del widget
        self._on_scan_complete: Optional[Callable] = on_scan_complete
        self._validation_enabled: bool = validation_enabled
        self._clear_after_scan: bool = clear_after_scan
        
        # Estado interno
        self._last_validation_result: bool = True
        self._original_style: str = str(self.cget('style'))
        
        # Configurar estilos para validación
        self._setup_validation_styles()
        
        # Configurar eventos
        self._setup_events()
        
        logger.debug(f"BarcodeEntry inicializado - validación: {validation_enabled}, "
                    f"limpiar: {clear_after_scan}")
    
    def _setup_validation_styles(self) -> None:
        """Configurar estilos para mostrar estado de validación."""
        try:
            style = ttk.Style()
            
            # Estilo para código inválido (fondo rojo claro)
            style.configure(
                'Invalid.TEntry',
                fieldbackground='#ffcccc',
                bordercolor='#ff6666',
                focuscolor='#ff6666'
            )
            
            # Estilo para código válido (fondo verde claro)
            style.configure(
                'Valid.TEntry',
                fieldbackground='#ccffcc',
                bordercolor='#66cc66',
                focuscolor='#66cc66'
            )
            
        except Exception as e:
            logger.warning(f"No se pudieron configurar estilos de validación: {e}")
    
    def _setup_events(self) -> None:
        """Configurar eventos del widget."""
        # Evento Return (principal para lectores de código de barras)
        self.bind('<Return>', self._on_return_pressed)
        
        # Evento de cambio de contenido para validación en tiempo real
        if self._validation_enabled:
            self.bind('<KeyRelease>', self._on_content_changed)
            self.bind('<FocusOut>', self._on_focus_lost)
        
        logger.debug("Eventos configurados para BarcodeEntry")
    
    def _on_return_pressed(self, event: tk.Event) -> str:
        """
        Manejar evento Return (enviado por lectores o usuario).
        
        Este es el evento principal que detecta cuando se ha escaneado
        un código o el usuario presiona Enter manualmente.
        
        Args:
            event: Evento de Tkinter
            
        Returns:
            str: 'break' para evitar propagación del evento
        """
        try:
            # Obtener código actual
            raw_code = self.get()
            
            # Limpiar y validar código
            code = raw_code.strip()
            
            # Verificar que no esté vacío
            if not code:
                logger.debug("Return presionado con campo vacío, ignorando")
                return 'break'
            
            # Normalizar código
            normalized_code = self._normalize_code(code)
            
            # Validar si está habilitado
            is_valid = True
            if self._validation_enabled:
                is_valid = self._validate_code(normalized_code)
                logger.debug(f"Código validado: {normalized_code} -> {is_valid}")
            
            # Ejecutar callback si está configurado
            if self._on_scan_complete:
                try:
                    self._on_scan_complete(normalized_code, is_valid)
                    logger.debug(f"Callback ejecutado para código: {normalized_code}")
                except Exception as e:
                    logger.error(f"Error en callback de BarcodeEntry: {e}")
                    logger.error(traceback.format_exc())
                    # No re-lanzar la excepción para no romper la UI
            
            # Limpiar campo si está configurado
            if self._clear_after_scan:
                # self.delete(0, tk.END)
                if self.winfo_exists():
                    self.delete(0, tk.END)

                logger.debug("Campo limpiado después del escaneo")
            
            # Actualizar estilo según validación
            self._update_validation_style(is_valid)
            
        except Exception as e:
            logger.error(f"Error procesando Return en BarcodeEntry: {e}")
            logger.error(traceback.format_exc())
        
        # Evitar que el evento se propague
        return 'break'
    
    def _on_content_changed(self, event: tk.Event) -> None:
        """
        Manejar cambio de contenido para validación en tiempo real.
        
        Args:
            event: Evento de Tkinter
        """
        if not self._validation_enabled:
            return
        
        try:
            current_code = self.get().strip()
            
            # Solo validar si hay contenido
            if current_code:
                is_valid = self._validate_code(current_code)
                self._update_validation_style(is_valid)
            else:
                # Restaurar estilo original si está vacío
                self._restore_original_style()
                
        except Exception as e:
            logger.warning(f"Error en validación en tiempo real: {e}")
    
    def _on_focus_lost(self, event: tk.Event) -> None:
        """
        Manejar pérdida de foco.
        
        Args:
            event: Evento de Tkinter
        """
        # Restaurar estilo original cuando pierde el foco si no hay contenido
        if not self.get().strip():
            self._restore_original_style()
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalizar código de barras.
        
        Args:
            code: Código a normalizar
            
        Returns:
            str: Código normalizado
        """
        try:
            return BarcodeUtils.normalize_code(code)
        except Exception:
            # Fallback simple
            return str(code).strip().upper()
    
    def _validate_code(self, code: str) -> bool:
        """
        Validar código de barras.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            return validate_barcode(code)
        except Exception as e:
            logger.warning(f"Error validando código {code}: {e}")
            # En caso de error, considerar válido para no bloquear
            return True
    
    def _update_validation_style(self, is_valid: bool) -> None:
        """
        Actualizar estilo según estado de validación.
        
        Args:
            is_valid: Si el código es válido
        """
        if not self._validation_enabled:
            return
        
        try:
            if is_valid:
                self.configure(style='Valid.TEntry')
            else:
                self.configure(style='Invalid.TEntry')
            
            self._last_validation_result = is_valid
            
        except Exception as e:
            logger.warning(f"Error actualizando estilo de validación: {e}")
    
    def _restore_original_style(self) -> None:
        """Restaurar estilo original del widget."""
        try:
            self.configure(style=self._original_style)
        except Exception as e:
            logger.warning(f"Error restaurando estilo original: {e}")
    
    def _validate_content(self) -> bool:
        """
        Validar contenido actual (método público para tests).
        
        Returns:
            bool: True si el contenido es válido
        """
        if not self._validation_enabled:
            return True
        
        code = self.get().strip()
        if not code:
            self._restore_original_style()
            return True
        
        is_valid = self._validate_code(code)
        self._update_validation_style(is_valid)
        return is_valid
    
    # Métodos públicos para configuración dinámica
    
    def set_scan_callback(self, callback: Optional[Callable[[str, bool], None]]) -> None:
        """
        Establecer callback para escaneo.
        
        Args:
            callback: Función callback o None para desactivar
            
        Raises:
            TypeError: Si callback no es callable
        """
        if callback is not None and not callable(callback):
            raise TypeError("callback debe ser una función callable")
        
        self._on_scan_complete = callback
        logger.debug(f"Callback de escaneo {'configurado' if callback else 'removido'}")
    
    def enable_validation(self) -> None:
        """Habilitar validación en tiempo real."""
        if not self._validation_enabled:
            self._validation_enabled = True
            self.bind('<KeyRelease>', self._on_content_changed)
            self.bind('<FocusOut>', self._on_focus_lost)
            logger.debug("Validación habilitada")
    
    def disable_validation(self) -> None:
        """Deshabilitar validación en tiempo real."""
        if self._validation_enabled:
            self._validation_enabled = False
            self.unbind('<KeyRelease>')
            self.unbind('<FocusOut>')
            self._restore_original_style()
            logger.debug("Validación deshabilitada")
    
    def configure_clear_after_scan(self, clear: bool) -> None:
        """
        Configurar si limpiar después del escaneo.
        
        Args:
            clear: True para limpiar automáticamente
        """
        self._clear_after_scan = clear
        logger.debug(f"Limpiar después del escaneo: {clear}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Obtener estado actual del widget.
        
        Returns:
            Dict: Estado del widget
        """
        return {
            'validation_enabled': self._validation_enabled,
            'clear_after_scan': self._clear_after_scan,
            'callback_configured': self._on_scan_complete is not None,
            'last_validation_result': self._last_validation_result,
            'current_content': self.get(),
            'has_focus': self.focus_get() == self
        }
    
    def reset(self) -> None:
        """Reiniciar widget a estado inicial."""
        try:
            # Limpiar contenido
            self.delete(0, tk.END)
            
            # Restaurar estilo
            self._restore_original_style()
            
            # Resetear validación
            self._last_validation_result = True
            
            # Remover callback (opcional, comentado para preservar configuración)
            # self._on_scan_complete = None
            
            logger.debug("BarcodeEntry reiniciado")
            
        except Exception as e:
            logger.error(f"Error reiniciando BarcodeEntry: {e}")
    
    def simulate_scan(self, code: str) -> None:
        """
        Simular escaneo de código (útil para testing).
        
        Args:
            code: Código a simular
        """
        try:
            # Limpiar contenido actual
            self.delete(0, tk.END)
            
            # Insertar código
            self.insert(0, code)
            
            # Simular Return
            fake_event = type('Event', (), {'widget': self})()
            self._on_return_pressed(fake_event)
            
            logger.debug(f"Escaneo simulado: {code}")
            
        except Exception as e:
            logger.error(f"Error simulando escaneo: {e}")
    
    # Propiedades de solo lectura
    
    @property
    def validation_enabled(self) -> bool:
        """Si la validación está habilitada."""
        return self._validation_enabled
    
    @property
    def clear_after_scan(self) -> bool:
        """Si se limpia después del escaneo."""
        return self._clear_after_scan
    
    @property
    def has_callback(self) -> bool:
        """Si tiene callback configurado."""
        return self._on_scan_complete is not None
    
    @property
    def last_validation_result(self) -> bool:
        """Resultado de la última validación."""
        return self._last_validation_result


def create_barcode_entry(
    parent: tk.Widget,
    on_scan: Optional[Callable[[str], None]] = None,
    **kwargs
) -> BarcodeEntry:
    """
    Función de conveniencia para crear BarcodeEntry.
    
    Args:
        parent: Widget padre
        on_scan: Callback simple que solo recibe el código
        **kwargs: Argumentos adicionales
        
    Returns:
        BarcodeEntry: Widget configurado
    """
    # Adaptar callback simple a formato completo
    full_callback = None
    if on_scan:
        def adapted_callback(code: str, is_valid: bool = True):
            on_scan(code)
        full_callback = adapted_callback
    
    return BarcodeEntry(
        parent,
        on_scan_complete=full_callback,
        **kwargs
    )


# Ejemplo de uso
if __name__ == '__main__':
    def test_callback(code: str, is_valid: bool = True):
        print(f"Código escaneado: '{code}', Válido: {is_valid}")
    
    # Crear ventana de prueba
    root = tk.Tk()
    root.title("Test BarcodeEntry")
    root.geometry("400x300")
    
    # Crear frame principal
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Etiqueta
    ttk.Label(main_frame, text="Escanear código de barras:").pack(pady=(0, 10))
    
    # Widget BarcodeEntry
    barcode_entry = BarcodeEntry(
        main_frame,
        on_scan_complete=test_callback,
        validation_enabled=True,
        clear_after_scan=True,
        width=30,
        font=('Consolas', 12)
    )
    barcode_entry.pack(pady=(0, 10))
    
    # Botones de prueba
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10)
    
    def simulate_valid_scan():
        barcode_entry.simulate_scan("123456789")
    
    def simulate_invalid_scan():
        barcode_entry.simulate_scan("invalid@code#")
    
    def toggle_validation():
        if barcode_entry.validation_enabled:
            barcode_entry.disable_validation()
        else:
            barcode_entry.enable_validation()
    
    ttk.Button(button_frame, text="Simular Válido", command=simulate_valid_scan).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Simular Inválido", command=simulate_invalid_scan).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Toggle Validación", command=toggle_validation).pack(side=tk.LEFT, padx=5)
    
    # Información
    info_label = ttk.Label(
        main_frame,
        text="Escriba un código y presione Enter, o use los botones de simulación.\n"
             "El widget está diseñado para lectores HID en modo teclado.",
        justify=tk.CENTER,
        foreground="gray"
    )
    info_label.pack(pady=20)
    
    # Foco inicial
    barcode_entry.focus()
    
    # Ejecutar aplicación
    root.mainloop()
