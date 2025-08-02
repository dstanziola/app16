"""
Product Movement Mediator - 100% tkinter compatible
Capa: Presentation Layer - UI Coordination
Objetivo: Eliminar dependencias circulares ProductSearchWidget ↔ MovementEntryForm

CORRECCIÓN CRÍTICA: Eliminada dependencia PyQt6 para compatibilidad tkinter
- Sin QObject, sin pyqtSlot  
- 100% Python puro con tkinter
- Threading safe con locks estándar
- Event Bus tkinter-compatible
"""

import logging
from typing import Optional, Dict, Any, List

from .event_bus_tkinter import EventBusTkinter, get_event_bus_tkinter, EventData
from .events import (
    EventTypes, EventSources,
    ProductSelectedEventData, ProductSearchRequestEventData,
    MovementEntryEventData, MovementValidationEventData,
    create_product_selected_event_data, create_search_request_event_data,
    create_movement_entry_event_data
)


class ProductMovementMediatorTkinter:
    """
    Mediator para coordinar comunicación entre ProductSearchWidget y MovementEntryForm.
    100% compatible con tkinter (sin PyQt6).
    
    Responsabilidades:
    - Facilitar comunicación desacoplada via Event Bus tkinter
    - Validar reglas de negocio en la comunicación
    - Mantener estado coherente entre widgets
    - Loggear actividad para debugging
    - Manejar errores de comunicación robustamente
    """
    
    def __init__(self, event_bus: Optional[EventBusTkinter] = None):
        """
        Inicializar Mediator tkinter-compatible.
        
        Args:
            event_bus: Instancia del Event Bus tkinter (opcional, usa singleton por defecto)
        """
        self._event_bus = event_bus or get_event_bus_tkinter()
        self._logger = logging.getLogger(__name__)
        
        # Estado interno del mediator
        self._current_selected_product: Optional[Dict[str, Any]] = None
        self._current_search_term: Optional[str] = None
        self._movement_form_state: Dict[str, Any] = {}
        
        # Registrar listeners para eventos relevantes
        self._register_event_listeners()
        
        self._logger.info("ProductMovementMediatorTkinter inicializado (sin PyQt6)")
    
    def _register_event_listeners(self) -> None:
        """Registrar listeners para eventos del Event Bus."""
        try:
            # Eventos de selección de productos
            self._event_bus.register(
                EventTypes.PRODUCT_SELECTED,
                self._handle_product_selected
            )
            
            # Eventos de solicitud de búsqueda
            self._event_bus.register(
                EventTypes.PRODUCT_SEARCH_REQUEST,
                self._handle_search_request
            )
            
            # Eventos de acciones en formulario de movimientos
            self._event_bus.register(
                EventTypes.MOVEMENT_ENTRY_ACTION,
                self._handle_movement_entry_action
            )
            
            # Eventos de validación
            self._event_bus.register(
                EventTypes.MOVEMENT_VALIDATION,
                self._handle_movement_validation
            )
            
            self._logger.debug("Event listeners registrados correctamente (tkinter)")
            
        except Exception as e:
            self._logger.error(f"Error registrando event listeners: {e}", exc_info=True)
    
    def _handle_product_selected(self, event_data: EventData) -> None:
        """
        Manejar evento de selección de producto.
        
        Flujo:
        1. Validar datos del producto seleccionado
        2. Verificar reglas de negocio
        3. Notificar a MovementEntryForm si corresponde
        4. Actualizar estado interno
        
        Args:
            event_data: Datos del evento de selección
        """
        try:
            self._logger.debug(f"Manejando selección de producto desde {event_data.source}")
            
            # Extraer datos del producto
            product_data = event_data.data.get("product")
            if not product_data:
                self._logger.warning("Evento product_selected sin datos de producto")
                return
            
            # Validar datos básicos del producto
            validation_result = self._validate_product_data(product_data)
            if not validation_result["is_valid"]:
                self._logger.warning(f"Producto inválido: {validation_result['errors']}")
                self._publish_validation_error(
                    "product_data",
                    validation_result["errors"],
                    EventSources.PRODUCT_MOVEMENT_MEDIATOR
                )
                return
            
            # Validar reglas de negocio específicas
            business_validation = self._validate_product_business_rules(product_data)
            if not business_validation["is_valid"]:
                self._logger.info(f"Producto válido pero con restricciones: {business_validation['warnings']}")
                # No bloquear, pero advertir al usuario
                self._publish_business_rule_warning(
                    business_validation["warnings"],
                    product_data
                )
            
            # Actualizar estado interno
            self._current_selected_product = product_data.copy()
            
            # Notificar a MovementEntryForm sobre selección
            self._notify_movement_form_of_selection(product_data, event_data.source)
            
            self._logger.info(f"Producto seleccionado procesado: {product_data.get('code', 'N/A')}")
            
        except Exception as e:
            self._logger.error(f"Error manejando selección de producto: {e}", exc_info=True)
    
    def _handle_search_request(self, event_data: EventData) -> None:
        """
        Manejar solicitud de búsqueda de productos.
        
        Args:
            event_data: Datos del evento de solicitud de búsqueda
        """
        try:
            self._logger.debug(f"Manejando solicitud de búsqueda desde {event_data.source}")
            
            search_term = event_data.data.get("search_term", "")
            search_type = event_data.data.get("search_type", "partial")
            filters = event_data.data.get("filters", {})
            
            # Validar parámetros de búsqueda
            if not search_term.strip():
                self._logger.warning("Solicitud de búsqueda con término vacío")
                return
            
            self._current_search_term = search_term
            
            # Reenviar solicitud a ProductSearchWidget si vino de otro widget
            if event_data.source != EventSources.PRODUCT_SEARCH_WIDGET:
                self._forward_search_request_to_product_widget(
                    search_term, search_type, filters, event_data.source
                )
            
            self._logger.debug(f"Solicitud de búsqueda procesada: '{search_term}'")
            
        except Exception as e:
            self._logger.error(f"Error manejando solicitud de búsqueda: {e}", exc_info=True)
    
    def _handle_movement_entry_action(self, event_data: EventData) -> None:
        """
        Manejar acciones del formulario de entrada de movimientos.
        
        Args:
            event_data: Datos del evento de acción del formulario
        """
        try:
            action = event_data.data.get("action")
            self._logger.debug(f"Manejando acción de movimiento: {action}")
            
            # Actualizar estado del formulario
            form_state = event_data.data.get("form_state", {})
            self._movement_form_state.update(form_state)
            
            # Procesar acción específica
            if action == "clear":
                self._handle_form_clear()
            elif action == "add":
                self._handle_item_add(event_data.data)
            elif action == "validate":
                self._handle_form_validation(event_data.data)
            
        except Exception as e:
            self._logger.error(f"Error manejando acción de movimiento: {e}", exc_info=True)
    
    def _handle_movement_validation(self, event_data: EventData) -> None:
        """
        Manejar eventos de validación de movimientos.
        
        Args:
            event_data: Datos del evento de validación
        """
        try:
            validation_type = event_data.data.get("validation_type")
            is_valid = event_data.data.get("is_valid", False)
            
            # CORRECCIÓN: Debugging mejorado para detectar eventos mal formados
            if validation_type is None:
                self._logger.warning(f"Evento de validación recibido sin validation_type desde {event_data.source}")
                self._logger.debug(f"Datos del evento: {event_data.data}")
            
            self._logger.debug(f"Validación {validation_type}: {'PASÓ' if is_valid else 'FALLÓ'}")
            
            if not is_valid:
                errors = event_data.data.get("error_messages", [])
                self._handle_validation_failure(validation_type, errors)
            
        except Exception as e:
            self._logger.error(f"Error manejando validación: {e}", exc_info=True)
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar datos básicos del producto.
        
        Args:
            product_data: Datos del producto a validar
            
        Returns:
            Dict con is_valid y errors
        """
        errors = []
        
        # Campos obligatorios
        required_fields = ["id", "nombre"]  # Ajustado a nombres reales del sistema
        for field in required_fields:
            if field not in product_data or not product_data[field]:
                errors.append(f"Campo obligatorio '{field}' faltante o vacío")
        
        # Validar tipos de datos
        if "id" in product_data:
            try:
                int(product_data["id"])
            except (ValueError, TypeError):
                errors.append("ID del producto debe ser numérico")
        
        # Validar categoría si está disponible
        if "categoria_tipo" in product_data:
            valid_categories = ["MATERIAL", "SERVICIO"]
            if product_data["categoria_tipo"] not in valid_categories:
                errors.append(f"Categoría debe ser una de: {valid_categories}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_product_business_rules(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar reglas de negocio del producto.
        
        Args:
            product_data: Datos del producto
            
        Returns:
            Dict con is_valid y warnings
        """
        warnings = []
        
        # Regla: SERVICIOS no pueden tener stock
        if product_data.get("categoria_tipo") == "SERVICIO":
            warnings.append(
                "Los productos SERVICIO no pueden agregarse al inventario "
                "(no manejan stock físico)"
            )
        
        # Regla: Verificar stock si está disponible
        if "stock" in product_data:
            try:
                stock = int(product_data["stock"])
                if stock < 0:
                    warnings.append("Producto tiene stock negativo")
            except (ValueError, TypeError):
                warnings.append("Stock del producto no es válido")
        
        return {
            "is_valid": True,  # Warnings no bloquean
            "warnings": warnings
        }
    
    def _notify_movement_form_of_selection(
        self, 
        product_data: Dict[str, Any], 
        selection_source: str
    ) -> None:
        """
        Notificar al formulario de movimientos sobre selección de producto.
        
        Args:
            product_data: Datos del producto seleccionado
            selection_source: Widget que originó la selección
        """
        try:
            # Crear evento específico para el formulario de movimientos
            movement_event_data = create_movement_entry_event_data(
                action="product_selected",
                movement_type="ENTRADA",  # Default, el formulario puede cambiar
                form_state=self._movement_form_state,
                product_data=product_data
            )
            
            self._event_bus.publish(
                EventTypes.MOVEMENT_ENTRY_ACTION,
                movement_event_data.__dict__,
                EventSources.PRODUCT_MOVEMENT_MEDIATOR
            )
            
            self._logger.debug("Selección de producto notificada al formulario de movimientos")
            
        except Exception as e:
            self._logger.error(f"Error notificando selección al formulario: {e}", exc_info=True)
    
    def _forward_search_request_to_product_widget(
        self,
        search_term: str,
        search_type: str,
        filters: Dict[str, Any],
        original_requester: str
    ) -> None:
        """
        Reenviar solicitud de búsqueda al widget de productos.
        
        Args:
            search_term: Término de búsqueda
            search_type: Tipo de búsqueda
            filters: Filtros adicionales
            original_requester: Widget que originó la solicitud
        """
        try:
            search_event_data = create_search_request_event_data(
                search_term=search_term,
                search_type=search_type,
                requester=f"{EventSources.PRODUCT_MOVEMENT_MEDIATOR} (from {original_requester})",
                filters=filters
            )
            
            self._event_bus.publish(
                EventTypes.PRODUCT_SEARCH_REQUEST,
                search_event_data.__dict__,
                EventSources.PRODUCT_MOVEMENT_MEDIATOR
            )
            
            self._logger.debug(f"Solicitud de búsqueda reenviada: '{search_term}'")
            
        except Exception as e:
            self._logger.error(f"Error reenviando solicitud de búsqueda: {e}", exc_info=True)
    
    def _publish_validation_error(
        self,
        field_name: str,
        errors: List[str],
        validator_source: str
    ) -> None:
        """Publicar evento de error de validación."""
        try:
            validation_event_data = MovementValidationEventData(
                validation_type="product_data",
                is_valid=False,
                error_messages=errors,
                field_name=field_name,
                field_value=self._current_selected_product,
                validator_source=validator_source
            )
            
            self._event_bus.publish(
                EventTypes.VALIDATION_ERROR,
                validation_event_data.__dict__,
                validator_source
            )
            
        except Exception as e:
            self._logger.error(f"Error publicando error de validación: {e}", exc_info=True)
    
    def _publish_business_rule_warning(
        self,
        warnings: List[str],
        product_data: Dict[str, Any]
    ) -> None:
        """Publicar advertencia de regla de negocio."""
        try:
            self._event_bus.publish(
                EventTypes.BUSINESS_RULE_VIOLATION,
                {
                    "rule_type": "product_category_restriction",
                    "is_blocking": False,
                    "warnings": warnings,
                    "product_data": product_data
                },
                EventSources.PRODUCT_MOVEMENT_MEDIATOR
            )
            
        except Exception as e:
            self._logger.error(f"Error publicando advertencia de regla de negocio: {e}", exc_info=True)
    
    def _handle_form_clear(self) -> None:
        """Manejar limpieza del formulario."""
        self._current_selected_product = None
        self._current_search_term = None
        self._movement_form_state.clear()
        self._logger.debug("Estado del mediator limpiado")
    
    def _handle_item_add(self, event_data: Dict[str, Any]) -> None:
        """Manejar adición de item al formulario."""
        self._logger.debug("Item agregado al formulario de movimientos")
    
    def _handle_form_validation(self, event_data: Dict[str, Any]) -> None:
        """Manejar validación del formulario."""
        self._logger.debug("Validación de formulario solicitada")
    
    def _handle_validation_failure(self, validation_type: str, errors: List[str]) -> None:
        """Manejar fallo de validación."""
        # CORRECCIÓN: Manejar validation_type None para prevenir errores
        if validation_type is None:
            self._logger.warning(f"Validación sin tipo especificado falló: {errors}")
            self._logger.debug("DEBUGGING: Evento de validación recibido sin validation_type")
            return
        
        self._logger.warning(f"Validación {validation_type} falló: {errors}")
    
    def get_current_selected_product(self) -> Optional[Dict[str, Any]]:
        """Obtener producto actualmente seleccionado."""
        return self._current_selected_product.copy() if self._current_selected_product else None
    
    def get_movement_form_state(self) -> Dict[str, Any]:
        """Obtener estado actual del formulario de movimientos."""
        return self._movement_form_state.copy()
    
    def cleanup(self) -> None:
        """Limpiar recursos del mediator."""
        try:
            # Desregistrar listeners
            self._event_bus.unregister(EventTypes.PRODUCT_SELECTED, self._handle_product_selected)
            self._event_bus.unregister(EventTypes.PRODUCT_SEARCH_REQUEST, self._handle_search_request)
            self._event_bus.unregister(EventTypes.MOVEMENT_ENTRY_ACTION, self._handle_movement_entry_action)
            self._event_bus.unregister(EventTypes.MOVEMENT_VALIDATION, self._handle_movement_validation)
            
            # Limpiar estado
            self._current_selected_product = None
            self._current_search_term = None
            self._movement_form_state.clear()
            
            self._logger.info("ProductMovementMediatorTkinter limpiado correctamente")
            
        except Exception as e:
            self._logger.error(f"Error durante cleanup del mediator: {e}", exc_info=True)


def create_product_movement_mediator_tkinter(event_bus: Optional[EventBusTkinter] = None) -> ProductMovementMediatorTkinter:
    """
    Factory para crear instancia del ProductMovementMediatorTkinter.
    
    Args:
        event_bus: Instancia del Event Bus tkinter (opcional)
        
    Returns:
        ProductMovementMediatorTkinter: Instancia configurada del mediator
    """
    return ProductMovementMediatorTkinter(event_bus)


# ==================== COMPATIBILITY LAYER ====================

# Aliasas para compatibilidad con código existente
ProductMovementMediator = ProductMovementMediatorTkinter
create_product_movement_mediator = create_product_movement_mediator_tkinter


if __name__ == "__main__":
    # Test básico del mediator tkinter
    import tkinter as tk
    
    # Crear ventana de prueba
    root = tk.Tk()
    root.title("Test ProductMovementMediatorTkinter")
    
    # Crear mediator
    mediator = create_product_movement_mediator_tkinter()
    
    # Configurar Event Bus con tkinter root
    eb = get_event_bus_tkinter()
    eb.set_tkinter_root(root)
    
    # Test de selección de producto
    product_data = {
        "id": 1,
        "nombre": "Laptop HP",
        "categoria_tipo": "MATERIAL",
        "stock": 15
    }
    
    def test_product_selection():
        eb.publish(
            EventTypes.PRODUCT_SELECTED,
            {"product": product_data},
            EventSources.PRODUCT_SEARCH_WIDGET
        )
        print(f"Producto seleccionado: {mediator.get_current_selected_product()}")
    
    # Botón para test
    test_button = tk.Button(root, text="Test Product Selection", command=test_product_selection)
    test_button.pack(pady=20)
    
    label = tk.Label(root, text="ProductMovementMediatorTkinter Test - Check console")
    label.pack(pady=10)
    
    # Cleanup después de 3 segundos
    def cleanup_test():
        print("Ejecutando cleanup del mediator...")
        mediator.cleanup()
        print("Cleanup completado")
        root.destroy()
    
    root.after(3000, cleanup_test)
    
    print("Iniciando test del mediator tkinter...")
    root.mainloop()
