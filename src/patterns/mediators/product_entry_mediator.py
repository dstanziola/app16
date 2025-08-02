"""
Product Entry Mediator Pattern Implementation
Sistema de Inventario - Clean Architecture

Implementa el Mediator pattern para coordinar las interacciones entre 
ProductSearchWidget y MovementEntryForm, eliminando dependencias circulares.

Patrón: Mediator + Facade
Responsabilidad: Coordinación centralizada del flujo de entrada de productos
Integración: Event Bus para comunicación asíncrona
"""

from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from utils.logger import get_logger
from patterns.event_bus import get_event_bus, InventoryEvents


@dataclass
class ProductEntryState:
    """Estado centralizado del proceso de entrada de productos"""
    selected_products: List[Dict] = None
    current_search_results: List[Dict] = None
    selected_product: Optional[Dict] = None
    is_product_locked: bool = False
    last_search_term: str = ""
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.selected_products is None:
            self.selected_products = []
        if self.current_search_results is None:
            self.current_search_results = []
        if self.validation_errors is None:
            self.validation_errors = []


class ProductEntryMediator:
    """
    Mediator para coordinar flujo de entrada de productos al inventario
    
    Responsabilidades:
    - Coordinar comunicación entre ProductSearchWidget y MovementEntryForm
    - Gestionar estado centralizado del proceso de entrada
    - Validar productos y cantidades según reglas de negocio
    - Orquestar flujo optimizado de entrada de productos
    - Emitir eventos vía EventBus para desacoplar componentes
    """
    
    def __init__(
        self, 
        product_service: Any,
        movement_service: Any,
        session_manager: Any,
        category_service: Any = None
    ):
        """
        Inicializar mediator con servicios requeridos
        
        Args:
            product_service: Servicio de productos
            movement_service: Servicio de movimientos
            session_manager: Gestor de sesión
            category_service: Servicio de categorías (opcional)
        """
        self.product_service = product_service
        self.movement_service = movement_service
        self.session_manager = session_manager
        self.category_service = category_service
        
        self.state = ProductEntryState()
        self.event_bus = get_event_bus()
        self.logger = get_logger(__name__)
        
        # Callbacks registrados por componentes
        self.callbacks: Dict[str, List[Callable]] = {
            'on_search_completed': [],
            'on_product_selected': [],
            'on_quantity_focus_requested': [],
            'on_products_list_updated': [],
            'on_entry_registered': [],
            'on_error_occurred': []
        }
        
        self.logger.info("ProductEntryMediator inicializado correctamente")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """
        Registrar callback para eventos específicos
        
        Args:
            event_type: Tipo de evento
            callback: Función callback
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            self.logger.debug(f"Callback registrado: {event_type}")
        else:
            self.logger.warning(f"Tipo de evento no reconocido: {event_type}")
    
    def handle_product_search(self, search_term: str) -> List[Dict]:
        """
        Manejar búsqueda de productos
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            List[Dict]: Lista de productos encontrados
        """
        try:
            self.logger.info(f"Iniciando búsqueda de productos: '{search_term}'")
            
            # Emitir evento de inicio de búsqueda
            self.event_bus.publish(InventoryEvents.PRODUCT_SEARCH_STARTED, {
                'search_term': search_term,
                'timestamp': datetime.now()
            })
            
            # Ejecutar búsqueda
            results = self.product_service.search_products(search_term)
            
            # Actualizar estado
            self.state.current_search_results = results
            self.state.last_search_term = search_term
            
            # Emitir evento de búsqueda completada
            self.event_bus.publish(InventoryEvents.PRODUCT_SEARCH_COMPLETED, {
                'search_term': search_term,
                'results': results,
                'count': len(results)
            })
            
            # Ejecutar callbacks registrados
            for callback in self.callbacks['on_search_completed']:
                try:
                    callback(results)
                except Exception as e:
                    self.logger.error(f"Error en callback search_completed: {e}")
            
            self.logger.info(f"Búsqueda completada: {len(results)} productos encontrados")
            
            # Auto-selección para resultado único
            if len(results) == 1:
                self._handle_auto_selection(results[0])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error en búsqueda de productos: {e}")
            self._emit_error_event("Error en búsqueda", str(e))
            return []
    
    def handle_product_selection(self, product: Dict, auto_selected: bool = False) -> bool:
        """
        Manejar selección de producto
        
        Args:
            product: Producto seleccionado
            auto_selected: Si fue auto-seleccionado
            
        Returns:
            bool: True si selección exitosa
        """
        try:
            # Validar que el producto no esté bloqueado para nueva selección
            if self.state.is_product_locked:
                self.logger.warning("Producto ya bloqueado, ignorando nueva selección")
                return False
            
            self.logger.info(f"Producto seleccionado: {product.get('nombre', 'UNKNOWN')}")
            
            # Actualizar estado
            self.state.selected_product = product
            self.state.is_product_locked = True
            
            # Emitir evento apropiado
            event_type = (InventoryEvents.PRODUCT_AUTO_SELECTED if auto_selected 
                         else InventoryEvents.PRODUCT_SELECTED)
            
            self.event_bus.publish(event_type, {
                'product': product,
                'auto_selected': auto_selected,
                'timestamp': datetime.now()
            })
            
            # Ejecutar callbacks registrados
            for callback in self.callbacks['on_product_selected']:
                try:
                    callback(product)
                except Exception as e:
                    self.logger.error(f"Error en callback product_selected: {e}")
            
            # Solicitar foco en cantidad
            self._request_quantity_focus()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al seleccionar producto: {e}")
            self._emit_error_event("Error en selección", str(e))
            return False
    
    def validate_product_for_inventory(self, product: Dict) -> Tuple[bool, str]:
        """
        Validar que un producto sea válido para inventario
        
        Args:
            product: Producto a validar
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        try:
            # Validar ID de categoría
            id_categoria = product.get('id_categoria')
            if not id_categoria:
                return False, f"El producto '{product.get('nombre', 'UNKNOWN')}' no tiene categoría asignada"
            
            # Obtener información de categoría si el servicio está disponible
            if self.category_service:
                categoria = self.category_service.get_category_by_id(id_categoria)
                
                if not categoria:
                    return False, f"No se pudo obtener información de la categoría para '{product.get('nombre', 'UNKNOWN')}'"
                
                # Validar que sea MATERIAL (no SERVICIO)
                if categoria.tipo == 'SERVICIO':
                    self.event_bus.publish(InventoryEvents.SERVICE_PRODUCT_REJECTED, {
                        'product': product,
                        'reason': 'SERVICIO no permitido en inventario'
                    })
                    
                    return False, (
                        f"'{product.get('nombre', 'UNKNOWN')}' es un SERVICIO.\n\n"
                        f"❌ Los SERVICIOS no pueden agregarse al inventario.\n"
                        f"✅ Solo productos de tipo MATERIAL pueden tener stock."
                    )
                
                # Agregar tipo de categoría al producto para referencia
                product['categoria_tipo'] = categoria.tipo
            
            # Emitir evento de validación exitosa
            self.event_bus.publish(InventoryEvents.PRODUCT_VALIDATION_PASSED, {
                'product': product
            })
            
            return True, ""
            
        except Exception as e:
            error_msg = f"No se pudo validar el producto '{product.get('nombre', 'UNKNOWN')}': {e}"
            self.logger.error(error_msg)
            
            self.event_bus.publish(InventoryEvents.PRODUCT_VALIDATION_FAILED, {
                'product': product,
                'error': str(e)
            })
            
            return False, error_msg
    
    def handle_product_addition(self, quantity: int) -> bool:
        """
        Manejar adición de producto a la lista
        
        Args:
            quantity: Cantidad a agregar
            
        Returns:
            bool: True si adición exitosa
        """
        try:
            if not self.state.selected_product:
                self._emit_error_event("Sin producto", "No hay producto seleccionado")
                return False
            
            # Validar producto para inventario
            is_valid, error_msg = self.validate_product_for_inventory(self.state.selected_product)
            if not is_valid:
                self._emit_error_event("Producto inválido", error_msg)
                return False
            
            # Validar cantidad
            if quantity <= 0:
                self._emit_error_event("Cantidad inválida", "La cantidad debe ser un número positivo")
                return False
            
            # Buscar si el producto ya está en la lista
            existing_index = None
            for i, selected_product in enumerate(self.state.selected_products):
                if selected_product['id'] == self.state.selected_product['id']:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Sumar cantidades
                self.state.selected_products[existing_index]['cantidad'] += quantity
                self.logger.info(f"Cantidad sumada para producto {self.state.selected_product['id']}: {quantity}")
            else:
                # Agregar nuevo producto
                product_data = {
                    'id': self.state.selected_product['id'],
                    'nombre': self.state.selected_product['nombre'],
                    'cantidad': quantity,
                    'stock_original': self.state.selected_product.get('stock', 0),
                    'categoria_tipo': self.state.selected_product.get('categoria_tipo', 'MATERIAL')
                }
                self.state.selected_products.append(product_data)
                self.logger.info(f"Producto MATERIAL agregado: {self.state.selected_product['id']} - {quantity} unidades")
            
            # Emitir evento de producto agregado
            self.event_bus.publish(InventoryEvents.PRODUCT_ADDED_TO_LIST, {
                'product': self.state.selected_product,
                'quantity': quantity,
                'total_products': len(self.state.selected_products)
            })
            
            # Ejecutar callbacks registrados
            for callback in self.callbacks['on_products_list_updated']:
                try:
                    callback(self.state.selected_products)
                except Exception as e:
                    self.logger.error(f"Error en callback products_list_updated: {e}")
            
            # Preparar para siguiente producto
            self._prepare_for_next_product()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al agregar producto: {e}")
            self._emit_error_event("Error al agregar", str(e))
            return False
    
    def handle_product_removal(self, product_id: int) -> bool:
        """
        Manejar remoción de producto de la lista
        
        Args:
            product_id: ID del producto a remover
            
        Returns:
            bool: True si remoción exitosa
        """
        try:
            original_count = len(self.state.selected_products)
            
            # Remover producto de la lista
            self.state.selected_products = [
                p for p in self.state.selected_products if p['id'] != product_id
            ]
            
            if len(self.state.selected_products) < original_count:
                self.logger.info(f"Producto {product_id} removido de la lista")
                
                # Emitir evento
                self.event_bus.publish(InventoryEvents.PRODUCT_REMOVED_FROM_LIST, {
                    'product_id': product_id,
                    'total_products': len(self.state.selected_products)
                })
                
                # Ejecutar callbacks
                for callback in self.callbacks['on_products_list_updated']:
                    try:
                        callback(self.state.selected_products)
                    except Exception as e:
                        self.logger.error(f"Error en callback products_list_updated: {e}")
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error al remover producto: {e}")
            self._emit_error_event("Error al remover", str(e))
            return False
    
    def handle_entry_registration(self) -> bool:
        """
        Manejar registro de entrada al inventario
        
        Returns:
            bool: True si registro exitoso
        """
        try:
            if not self.state.selected_products:
                self._emit_error_event("Sin productos", "Agregue productos antes de registrar")
                return False
            
            self.logger.info(f"Iniciando registro de entrada: {len(self.state.selected_products)} productos")
            
            # Emitir evento de inicio
            self.event_bus.publish(InventoryEvents.ENTRY_REGISTRATION_STARTED, {
                'products_count': len(self.state.selected_products)
            })
            
            # Pre-validar productos
            is_valid, errors = self._pre_validate_products_for_entry()
            if not is_valid:
                error_msg = "Errores de validación:\n" + "\n".join([f"• {error}" for error in errors])
                self._emit_error_event("Error de validación", error_msg)
                return False
            
            # Obtener usuario actual
            current_user = self.session_manager.get_current_user()
            if not current_user or not current_user.get('id'):
                self._emit_error_event("Error de sesión", "No se pudo obtener información del usuario actual")
                return False
            
            # Preparar datos del movimiento
            movement_data = {
                'tipo': 'ENTRADA',
                'fecha': datetime.now(),
                'responsable_id': current_user['id'],
                'productos': self.state.selected_products
            }
            
            # Ejecutar registro
            result = self.movement_service.create_entry_movement(movement_data)
            
            # Validar respuesta
            if not result or not isinstance(result, dict):
                raise ValueError("Respuesta inválida del servicio")
            
            required_fields = ['id', 'ticket_number']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"Respuesta incompleta: {missing_fields}")
            
            # Emitir evento de éxito
            self.event_bus.publish(InventoryEvents.ENTRY_REGISTRATION_COMPLETED, {
                'entry_id': result['id'],
                'ticket_number': result['ticket_number'],
                'products_count': len(self.state.selected_products)
            })
            
            # Ejecutar callbacks
            for callback in self.callbacks['on_entry_registered']:
                try:
                    callback(result)
                except Exception as e:
                    self.logger.error(f"Error en callback entry_registered: {e}")
            
            self.logger.info(f"Entrada registrada exitosamente: ID={result['id']}")
            
            # Limpiar estado
            self.clear_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al registrar entrada: {e}")
            
            self.event_bus.publish(InventoryEvents.ENTRY_REGISTRATION_FAILED, {
                'error': str(e)
            })
            
            self._emit_error_event("Error de registro", str(e))
            return False
    
    def clear_state(self) -> None:
        """Limpiar estado del mediator"""
        self.state = ProductEntryState()
        
        # Emitir evento de limpieza
        self.event_bus.publish(InventoryEvents.FORM_CLEARED, {
            'timestamp': datetime.now()
        })
        
        self.logger.info("Estado del mediator limpiado")
    
    def get_current_state(self) -> ProductEntryState:
        """
        Obtener estado actual del mediator
        
        Returns:
            ProductEntryState: Estado actual
        """
        return self.state
    
    def _handle_auto_selection(self, product: Dict) -> None:
        """Manejar auto-selección de producto único"""
        self.handle_product_selection(product, auto_selected=True)
    
    def _request_quantity_focus(self) -> None:
        """Solicitar foco en campo de cantidad"""
        self.event_bus.publish(InventoryEvents.QUANTITY_FOCUS_REQUESTED, {
            'product': self.state.selected_product
        })
        
        # Ejecutar callbacks registrados
        for callback in self.callbacks['on_quantity_focus_requested']:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error en callback quantity_focus: {e}")
    
    def _prepare_for_next_product(self) -> None:
        """Preparar para siguiente producto"""
        # Resetear estado de selección
        self.state.selected_product = None
        self.state.is_product_locked = False
        self.state.current_search_results = []
        
        # Emitir evento
        self.event_bus.publish(InventoryEvents.NEXT_PRODUCT_PREPARED, {
            'timestamp': datetime.now()
        })
        
        self.logger.debug("Preparado para siguiente producto")
    
    def _pre_validate_products_for_entry(self) -> Tuple[bool, List[str]]:
        """Pre-validar productos antes de registro"""
        errors = []
        
        if not self.state.selected_products:
            errors.append("No hay productos seleccionados")
            return False, errors
        
        for i, producto in enumerate(self.state.selected_products):
            producto_nombre = producto.get('nombre', f'Producto #{i+1}')
            producto_id = producto.get('id')
            cantidad = producto.get('cantidad', 0)
            
            if not producto_id or not isinstance(producto_id, int):
                errors.append(f"{producto_nombre}: ID inválido ({producto_id})")
                continue
            
            if cantidad <= 0:
                errors.append(f"{producto_nombre}: Cantidad inválida ({cantidad})")
            
            categoria_tipo = producto.get('categoria_tipo')
            if categoria_tipo == 'SERVICIO':
                errors.append(f"{producto_nombre}: SERVICIO no permitido en inventario")
        
        return len(errors) == 0, errors
    
    def _emit_error_event(self, error_type: str, error_message: str) -> None:
        """Emitir evento de error"""
        error_data = {
            'error_type': error_type,
            'message': error_message,
            'timestamp': datetime.now()
        }
        
        # Emitir vía event bus
        self.event_bus.publish("error_occurred", error_data)
        
        # Ejecutar callbacks registrados
        for callback in self.callbacks['on_error_occurred']:
            try:
                callback(error_data)
            except Exception as e:
                self.logger.error(f"Error en callback error_occurred: {e}")
