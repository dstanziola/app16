"""
ProductSearchWidget - Widget reutilizable para búsqueda de productos
Implementa funcionalidad común de búsqueda con código de barras

REFACTORIZACIÓN: Integración con Event Bus para eliminar dependencias circulares
Patrón: Publisher/Subscriber via Event Bus
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Callable, Optional
import logging

from utils.logger import get_logger
from ui.shared.event_bus_tkinter import get_event_bus_tkinter, EventBusTkinter, EventData
from ui.shared.events import (
    EventTypes, EventSources,
    create_product_selected_event_data, create_search_request_event_data
)


class ProductSearchWidget(ttk.Frame):
    """
    Widget reutilizable para búsqueda de productos
    
    Características:
    - Búsqueda por ID o nombre
    - Soporte código de barras
    - Validación en tiempo real
    - Comunicación via Event Bus (elimina dependencias circulares)
    
    REFACTORIZACIÓN:
    - Eliminados callbacks directos
    - Integración con Event Bus
    - Publisher de eventos estándar
    """

    def __init__(self, parent: tk.Widget, product_service, event_bus: Optional[EventBusTkinter] = None, **kwargs):
        """
        Inicializar widget de búsqueda de productos
        
        Args:
            parent: Widget padre
            product_service: Servicio de productos
            event_bus: Event Bus instance (opcional, usa singleton por defecto)
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, **kwargs)
        
        self.product_service = product_service
        self.logger = get_logger(__name__)
        
        # Event Bus integration - CORRECCIÓN CRÍTICA: tkinter compatible
        self._event_bus = event_bus or get_event_bus_tkinter()
        
        # Estado del widget
        self.current_results: List[Dict] = []
        self.selected_product: Optional[Dict] = None
        
        # DEPRECATED: Callbacks (mantenidos para compatibilidad, usar Event Bus)
        self.on_product_selected: Optional[Callable] = None
        self.on_search_completed: Optional[Callable] = None
        self.on_focus_quantity: Optional[Callable] = None
        
        # Crear interfaz
        self._create_interface()
        self._setup_bindings()
        
        self.logger.info("ProductSearchWidget inicializado con Event Bus")

    def _create_interface(self):
        """Crear interfaz del widget"""
        # Configurar grid
        self.grid_columnconfigure(1, weight=1)
        
        # Campo de búsqueda
        ttk.Label(self, text="Buscar:").grid(
            row=0, column=0, sticky="w", padx=5
        )
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self,
            textvariable=self.search_var,
            width=40
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Botón búsqueda
        self.search_button = ttk.Button(
            self,
            text="Buscar",
            command=self._perform_search
        )
        self.search_button.grid(row=0, column=2, padx=2)
        
        # Botón borrar código
        self.clear_code_button = ttk.Button(
            self,
            text="Borrar Código",
            command=self._clear_code_and_selection,
            style="Toolbutton"
        )
        self.clear_code_button.grid(row=0, column=3, padx=2)
        
        # Lista de resultados
        self.results_listbox = tk.Listbox(
            self,
            height=3
        )
        self.results_listbox.grid(
            row=1, column=0, columnspan=4, 
            sticky="ew", pady=5
        )
        
        # Label para producto seleccionado
        self.selected_label = ttk.Label(
            self,
            text="Ningún producto seleccionado",
            foreground="gray"
        )
        self.selected_label.grid(
            row=2, column=0, columnspan=4,
            sticky="w", pady=5
        )

    def _setup_bindings(self):
        """Configurar eventos"""
        # Enter en búsqueda
        self.search_entry.bind("<Return>", lambda e: self._perform_search())
        
        # Selección en listbox
        self.results_listbox.bind("<<ListboxSelect>>", self._on_selection_change)
        
        # Doble click
        self.results_listbox.bind("<Double-Button-1>", self._on_double_click)
        
        # Validación en tiempo real
        self.search_var.trace("w", self._on_search_change)

    def _perform_search(self):
        """Ejecutar búsqueda de productos"""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            return
            
        try:
            # Publicar evento de solicitud de búsqueda
            self._publish_search_request_event(search_term, "partial")
            
            results = self.product_service.search_products(search_term)
            self._update_results_optimized(results)
            
            # Publicar evento de resultados de búsqueda
            self._publish_search_result_event(search_term, results)
            
            # BACKWARD COMPATIBILITY: Ejecutar callback si existe
            if self.on_search_completed:
                self.on_search_completed(results)
                
            self.logger.info(f"Búsqueda completada: {len(results)} productos")
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}")
            self._update_results_optimized([])

    def on_enter_code(self, code: str):
        """Procesar código introducido (manual o por lector)"""
        try:
            # Publicar evento de solicitud de búsqueda por código
            self._publish_search_request_event(code, "exact")
            
            # Buscar productos por código
            results = self.product_service.buscar_por_codigo(code)
            
            # Usar flujo optimizado para auto-selección
            self._update_results_optimized(results)
            
            # Publicar evento de resultados
            self._publish_search_result_event(code, results)
            
            # BACKWARD COMPATIBILITY: Ejecutar callback si existe
            if self.on_search_completed:
                self.on_search_completed(results)
                
            self.logger.info(f"Código procesado: {code}, resultados: {len(results)}")
                
        except Exception as e:
            self.logger.error(f"Error procesando código {code}: {e}")
            self._update_results_optimized([])

    def _normalize_product(self, product) -> Dict:
        """
        Normalizar producto a formato diccionario compatible
        
        CORRECCIÓN CRÍTICA: 'Producto' object is not subscriptable
        Convierte objetos Producto a diccionarios para compatibilidad
        
        Args:
            product: Objeto Producto o diccionario
            
        Returns:
            Dict: Producto normalizado como diccionario
        """
        try:
            # Si ya es diccionario, usar directamente
            if isinstance(product, dict):
                # Normalizar claves para compatibilidad
                normalized = {
                    'id': product.get('id') or product.get('id_producto'),
                    'nombre': product.get('nombre'),
                    'stock': product.get('stock', 0),
                    'categoria_tipo': product.get('categoria_tipo'),
                    'precio': product.get('precio', 0),
                    'activo': product.get('activo', True)
                }
                # Preservar campos originales también
                normalized.update(product)
                return normalized
            
            # Si es objeto Producto, convertir a diccionario
            elif hasattr(product, 'id_producto'):
                return {
                    'id': product.id_producto,
                    'id_producto': product.id_producto,
                    'nombre': product.nombre,
                    'stock': getattr(product, 'stock', 0),
                    'categoria_tipo': getattr(product, 'categoria_tipo', None),
                    'precio': float(getattr(product, 'precio', 0)),
                    'activo': getattr(product, 'activo', True),
                    'costo': float(getattr(product, 'costo', 0)),
                    'tasa_impuesto': float(getattr(product, 'tasa_impuesto', 0)),
                    'id_categoria': getattr(product, 'id_categoria', None)
                }
            
            else:
                # Fallback: intentar conversión genérica
                self.logger.warning(f"Producto tipo desconocido: {type(product)}")
                return {
                    'id': getattr(product, 'id', None) or getattr(product, 'id_producto', None),
                    'nombre': getattr(product, 'nombre', str(product)),
                    'stock': getattr(product, 'stock', 0),
                    'categoria_tipo': getattr(product, 'categoria_tipo', None),
                    'precio': getattr(product, 'precio', 0),
                    'activo': getattr(product, 'activo', True)
                }
                
        except Exception as e:
            self.logger.error(f"Error normalizando producto {product}: {e}")
            # Fallback seguro
            return {
                'id': None,
                'nombre': f"Error: {str(product)}",
                'stock': 0,
                'categoria_tipo': None,
                'precio': 0,
                'activo': False
            }

    def _update_results_optimized(self, results: List):
        """
        Actualizar lista de resultados con selección automática optimizada
        
        OPTIMIZACIÓN: Si hay un solo resultado, lo selecciona automáticamente
        y publica evento via Event Bus.
        
        CORRECCIÓN CRÍTICA: Normaliza productos para compatibilidad Dict/Object
        
        Args:
            results: Lista de productos encontrados (Dict o objetos Producto)
        """
        self.logger.info(f"DEBUGGING _update_results_optimized:")
        self.logger.info(f"  - results count: {len(results)}")
        
        # CORRECCIÓN CRÍTICA: Normalizar productos para compatibilidad
        normalized_results = []
        for product in results:
            try:
                normalized = self._normalize_product(product)
                normalized_results.append(normalized)
                self.logger.debug(f"Producto normalizado: {normalized['nombre']} (ID: {normalized['id']})")
            except Exception as e:
                self.logger.error(f"Error normalizando producto: {e}")
                continue
        
        self.current_results = normalized_results
        
        # Limpiar listbox
        self.results_listbox.delete(0, tk.END)
        
        if not normalized_results:
            # Sin resultados
            self.selected_product = None
            self.selected_label.config(
                text="No se encontraron productos",
                foreground="red"
            )
            self.logger.info(f"  - Sin resultados, selected_product = None")
            return
        
        # Agregar resultados al listbox
        for product in normalized_results:
            display_text = f"{product['id']} - {product['nombre']}"
            if 'stock' in product:
                display_text += f" (Stock: {product['stock']})"
            self.results_listbox.insert(tk.END, display_text)
        
        # OPTIMIZACIÓN: Selección automática para resultado único
        if len(normalized_results) == 1:
            self.logger.info(f"  - Un solo resultado: iniciando auto-selección")
            
            # Un solo resultado: selección automática INMEDIATA
            self.results_listbox.selection_set(0)
            self.selected_product = normalized_results[0]
            
            self.logger.info(f"  - selected_product asignado: {self.selected_product}")
            
            # Actualizar label
            self.selected_label.config(
                text=f"✓ Auto-seleccionado: {self.selected_product['nombre']}",
                foreground="blue"
            )
            
            # NUEVA FUNCIONALIDAD: Publicar evento de selección via Event Bus
            self._publish_product_selected_event(self.selected_product, "auto_selection")
            
            self.logger.info(f"Producto auto-seleccionado y evento publicado: {self.selected_product['nombre']}")
        
        else:
            # Múltiples resultados: mostrar para selección manual
            self.selected_product = None
            self.selected_label.config(
                text=f"Encontrados {len(normalized_results)} productos - seleccione uno",
                foreground="orange"
            )
            self.logger.info(f"  - Múltiples resultados, selected_product = None")

    def _on_selection_change(self, event):
        """Manejar cambio de selección"""
        selection = self.results_listbox.curselection()
        
        if selection:
            index = selection[0]
            self.selected_product = self.current_results[index]
            
            # Actualizar label
            self.selected_label.config(
                text=f"Seleccionado: {self.selected_product['nombre']}",
                foreground="black"
            )
            
            # NUEVA FUNCIONALIDAD: Publicar evento via Event Bus
            self._publish_product_selected_event(self.selected_product, "manual_selection")
            
            # BACKWARD COMPATIBILITY: Ejecutar callback si existe
            if self.on_product_selected:
                self.on_product_selected(self.selected_product)
            
            # BACKWARD COMPATIBILITY: Foco en cantidad
            if self.on_focus_quantity:
                self.on_focus_quantity()
        else:
            self.selected_product = None
            self.selected_label.config(
                text="Ningún producto seleccionado",
                foreground="gray"
            )

    def _on_double_click(self, event):
        """Manejar doble click en resultado"""
        if self.selected_product:
            # Publicar evento de selección con doble click
            self._publish_product_selected_event(self.selected_product, "double_click")
            
            # BACKWARD COMPATIBILITY
            if self.on_product_selected:
                self.on_product_selected(self.selected_product, double_click=True)

    def _on_search_change(self, *args):
        """Manejar cambios en campo de búsqueda"""
        search_term = self.search_var.get()
        
        # Auto-búsqueda si es código numérico (código de barras/ID)
        if search_term.isdigit() and len(search_term) >= 3:
            self.on_enter_code(search_term)

    # ==================== EVENT BUS INTEGRATION ====================

    def _publish_product_selected_event(self, product: Dict, user_action: str):
        """
        Publicar evento de selección de producto via Event Bus
        
        Args:
            product: Producto seleccionado
            user_action: Tipo de acción del usuario
        """
        try:
            event_data = create_product_selected_event_data(
                product=product,
                source=EventSources.PRODUCT_SEARCH_WIDGET,
                user_action=user_action
            )
            
            self._event_bus.publish(
                EventTypes.PRODUCT_SELECTED,
                event_data.__dict__,
                EventSources.PRODUCT_SEARCH_WIDGET
            )
            
            self.logger.debug(f"Evento product_selected publicado: {product.get('code', product.get('id'))}")
            
        except Exception as e:
            self.logger.error(f"Error publicando evento product_selected: {e}")

    def _publish_search_request_event(self, search_term: str, search_type: str):
        """
        Publicar evento de solicitud de búsqueda
        
        Args:
            search_term: Término de búsqueda
            search_type: Tipo de búsqueda (exact, partial, etc.)
        """
        try:
            event_data = create_search_request_event_data(
                search_term=search_term,
                search_type=search_type,
                requester=EventSources.PRODUCT_SEARCH_WIDGET
            )
            
            self._event_bus.publish(
                EventTypes.PRODUCT_SEARCH_REQUEST,
                event_data.__dict__,
                EventSources.PRODUCT_SEARCH_WIDGET
            )
            
            self.logger.debug(f"Evento search_request publicado: '{search_term}' ({search_type})")
            
        except Exception as e:
            self.logger.error(f"Error publicando evento search_request: {e}")

    def _publish_search_result_event(self, search_term: str, results: List[Dict]):
        """
        Publicar evento de resultados de búsqueda
        
        Args:
            search_term: Término que se buscó
            results: Resultados encontrados
        """
        try:
            import time
            
            self._event_bus.publish(
                EventTypes.PRODUCT_SEARCH_RESULT,
                {
                    "search_term": search_term,
                    "results": results,
                    "total_results": len(results),
                    "search_duration_ms": 0,  # Placeholder
                    "search_source": EventSources.PRODUCT_SEARCH_WIDGET
                },
                EventSources.PRODUCT_SEARCH_WIDGET
            )
            
            self.logger.debug(f"Evento search_result publicado: {len(results)} resultados")
            
        except Exception as e:
            self.logger.error(f"Error publicando evento search_result: {e}")

    # ==================== MÉTODOS ORIGINALES (Compatibilidad) ====================

    def get_selected_product(self) -> Optional[Dict]:
        """
        Obtener producto seleccionado
        
        Returns:
            Dict: Producto seleccionado o None
        """
        return self.selected_product

    def clear_selection(self):
        """Limpiar selección actual"""
        self.search_var.set("")
        self.results_listbox.delete(0, tk.END)
        self.selected_product = None
        self.current_results.clear()
        
        self.selected_label.config(
            text="Ningún producto seleccionado",
            foreground="gray"
        )

    def set_focus(self):
        """Establecer foco en campo de búsqueda"""
        self.search_entry.focus()

    def set_search_term(self, term: str):
        """
        Establecer término de búsqueda y ejecutar
        
        Args:
            term: Término a buscar
        """
        self.search_var.set(term)
        self._perform_search()

    def _clear_code_and_selection(self):
        """
        Limpiar código y selección para nueva búsqueda
        """
        # Limpiar completamente el estado
        self.search_var.set("")
        self.results_listbox.delete(0, tk.END)
        self.selected_product = None
        self.current_results.clear()
        
        # Resetear label
        self.selected_label.config(
            text="Ningún producto seleccionado",
            foreground="gray"
        )
        
        # Regresar foco al campo de búsqueda para nueva entrada
        self.search_entry.focus()
        
        self.logger.info("Código y selección limpiados - listo para nueva búsqueda")

    # ==================== EVENT BUS LISTENERS (Para futura extensión) ====================

    def register_event_listeners(self):
        """
        Registrar listeners para eventos del Event Bus
        
        FUNCIONALIDAD EXTENDIDA: Permite que ProductSearchWidget
        también escuche eventos de otros widgets si es necesario.
        """
        try:
            # Ejemplo: Escuchar solicitudes de búsqueda desde otros widgets
            self._event_bus.register(
                EventTypes.PRODUCT_SEARCH_REQUEST,
                self._handle_external_search_request
            )
            
            self.logger.debug("Event listeners registrados para ProductSearchWidget")
            
        except Exception as e:
            self.logger.error(f"Error registrando event listeners: {e}")

    def _handle_external_search_request(self, event_data: EventData):
        """
        Manejar solicitudes de búsqueda de otros widgets
        
        Args:
            event_data: Datos del evento de solicitud
        """
        try:
            # Solo procesar si no viene de este widget
            if event_data.source != EventSources.PRODUCT_SEARCH_WIDGET:
                search_term = event_data.data.get("search_term", "")
                search_type = event_data.data.get("search_type", "partial")
                
                if search_term:
                    self.set_search_term(search_term)
                    self.logger.debug(f"Búsqueda externa procesada: '{search_term}'")
            
        except Exception as e:
            self.logger.error(f"Error manejando búsqueda externa: {e}")

    def cleanup(self):
        """Limpiar recursos del widget"""
        try:
            # Desregistrar listeners si se registraron
            if hasattr(self, '_event_listeners_registered'):
                self._event_bus.unregister(
                    EventTypes.PRODUCT_SEARCH_REQUEST,
                    self._handle_external_search_request
                )
            
            self.logger.info("ProductSearchWidget cleanup completado")
            
        except Exception as e:
            self.logger.error(f"Error durante cleanup: {e}")


# ==================== FACTORY FUNCTIONS ====================

def create_product_search_widget(
    parent: tk.Widget,
    product_service,
    event_bus: Optional[EventBusTkinter] = None,
    **kwargs
) -> ProductSearchWidget:
    """
    Factory para crear ProductSearchWidget con Event Bus
    
    Args:
        parent: Widget padre
        product_service: Servicio de productos
        event_bus: Event Bus instance (opcional)
        **kwargs: Argumentos adicionales
        
    Returns:
        ProductSearchWidget: Widget configurado con Event Bus
    """
    return ProductSearchWidget(parent, product_service, event_bus, **kwargs)


if __name__ == "__main__":
    # Test básico del widget con Event Bus
    import sys
    import tkinter as tk
    from unittest.mock import Mock
    
    # Mock del product service
    mock_service = Mock()
    mock_service.search_products.return_value = [
        {"id": 1, "nombre": "Laptop HP", "stock": 5},
        {"id": 2, "nombre": "Mouse Logitech", "stock": 10}
    ]
    
    # Crear ventana de prueba
    root = tk.Tk()
    root.title("Test ProductSearchWidget con Event Bus")
    
    # Crear widget
    widget = create_product_search_widget(root, mock_service)
    widget.pack(padx=10, pady=10, fill="both", expand=True)
    
    # Test event listener
    def test_listener(event_data):
        print(f"Evento recibido: {event_data.event_type}")
        print(f"Datos: {event_data.data}")
    
    event_bus = get_event_bus_tkinter()
    event_bus.register(EventTypes.PRODUCT_SELECTED, test_listener)
    
    root.mainloop()
