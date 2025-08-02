"""
Event Definitions - Eventos específicos del dominio de inventario
Capa: Presentation Layer - UI Event Communication
Objetivo: Definir eventos estándar para comunicación entre widgets

Eventos implementados:
- ProductSelectedEvent: Cuando se selecciona un producto
- ProductSearchRequestEvent: Solicitud de búsqueda de productos
- MovementEntryEvent: Eventos del formulario de movimientos
- ValidationEvent: Eventos de validación de datos
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from decimal import Decimal
import time


# ==================== EVENTOS DE PRODUCTOS ====================

@dataclass
class ProductSelectedEventData:
    """Datos para evento de selección de producto."""
    
    product: Dict[str, Any]  # Datos completos del producto
    selection_source: str    # Widget que originó la selección
    user_action: str        # Acción específica del usuario (click, enter, etc.)
    
    def __post_init__(self):
        """Validar datos del producto seleccionado - COMPATIBILIDAD MEJORADA."""
        # CORRECCIÓN CRÍTICA: Validación compatible con estructura real de BD
        
        # Campo ID es obligatorio (puede ser 'id' o 'id_producto')
        if 'id' not in self.product and 'id_producto' not in self.product:
            raise ValueError("Campo obligatorio 'id' o 'id_producto' faltante en producto")
        
        # Normalizar 'id' si viene como 'id_producto'
        if 'id_producto' in self.product and 'id' not in self.product:
            self.product['id'] = self.product['id_producto']
        
        # Campo 'nombre' es obligatorio 
        if 'nombre' not in self.product and 'name' not in self.product:
            raise ValueError("Campo obligatorio 'nombre' o 'name' faltante en producto")
        
        # Normalizar 'name' si viene como 'nombre'
        if 'nombre' in self.product and 'name' not in self.product:
            self.product['name'] = self.product['nombre']
        
        # Campo 'code' es opcional - generar desde ID si no existe
        if 'code' not in self.product:
            product_id = self.product.get('id') or self.product.get('id_producto')
            if product_id:
                self.product['code'] = str(product_id)
            else:
                self.product['code'] = 'UNKNOWN'
        
        # Campo 'category' es opcional - derivar de categoria_tipo o id_categoria
        if 'category' not in self.product:
            if 'categoria_tipo' in self.product:
                self.product['category'] = self.product['categoria_tipo']
            elif 'id_categoria' in self.product:
                self.product['category'] = f"CAT_{self.product['id_categoria']}"
            else:
                self.product['category'] = 'UNKNOWN'


@dataclass 
class ProductSearchRequestEventData:
    """Datos para evento de solicitud de búsqueda de productos."""
    
    search_term: str        # Término de búsqueda
    search_type: str        # Tipo de búsqueda (code, name, barcode, etc.)
    filters: Dict[str, Any] # Filtros adicionales (categoría, precio, etc.)
    requester: str          # Widget que solicita la búsqueda
    
    def __post_init__(self):
        """Validar datos de la solicitud de búsqueda."""
        if not self.search_term.strip():
            raise ValueError("search_term no puede estar vacío")
        
        valid_search_types = ["code", "name", "barcode", "partial", "exact"]
        if self.search_type not in valid_search_types:
            raise ValueError(f"search_type debe ser uno de: {valid_search_types}")


@dataclass
class ProductSearchResultEventData:
    """Datos para evento de resultado de búsqueda de productos."""
    
    search_term: str           # Término que se buscó
    results: List[Dict[str, Any]]  # Lista de productos encontrados
    total_results: int         # Total de resultados encontrados
    search_duration_ms: float  # Tiempo de búsqueda en milisegundos
    search_source: str         # Widget que ejecutó la búsqueda
    
    def __post_init__(self):
        """Validar datos de resultados de búsqueda."""
        if self.total_results < 0:
            raise ValueError("total_results no puede ser negativo")
        
        if len(self.results) > self.total_results:
            raise ValueError("Cantidad de results no puede exceder total_results")


# ==================== EVENTOS DE MOVIMIENTOS ====================

@dataclass
class MovementEntryEventData:
    """Datos para eventos del formulario de entrada de movimientos."""
    
    action: str              # Acción específica (add, remove, update, clear)
    product_data: Optional[Dict[str, Any]]  # Datos del producto afectado
    quantity: Optional[int]  # Cantidad en el movimiento
    movement_type: str       # Tipo de movimiento (ENTRADA, SALIDA, AJUSTE)
    form_state: Dict[str, Any]  # Estado actual del formulario
    
    def __post_init__(self):
        """Validar datos del evento de movimiento."""
        valid_actions = ["add", "remove", "update", "clear", "validate", "product_selected"]
        if self.action not in valid_actions:
            raise ValueError(f"action debe ser uno de: {valid_actions}")
        
        valid_movement_types = ["ENTRADA", "SALIDA", "AJUSTE"]
        if self.movement_type not in valid_movement_types:
            raise ValueError(f"movement_type debe ser uno de: {valid_movement_types}")


@dataclass
class MovementValidationEventData:
    """Datos para eventos de validación de movimientos."""
    
    validation_type: str     # Tipo de validación (product, quantity, business_rule)
    is_valid: bool          # Si la validación pasó
    error_messages: List[str]  # Lista de mensajes de error
    field_name: str         # Campo que se está validando
    field_value: Any        # Valor del campo
    validator_source: str   # Widget/servicio que ejecutó la validación
    
    def __post_init__(self):
        """Validar datos del evento de validación."""
        if not self.is_valid and not self.error_messages:
            raise ValueError("error_messages es obligatorio cuando is_valid=False")


# ==================== EVENTOS DE UI STATE ====================

@dataclass
class UIStateChangeEventData:
    """Datos para eventos de cambio de estado de UI."""
    
    widget_name: str        # Nombre del widget que cambió
    state_change: str       # Tipo de cambio (enabled, disabled, focused, etc.)
    previous_state: Any     # Estado anterior
    new_state: Any         # Nuevo estado
    reason: str            # Razón del cambio de estado
    
    def __post_init__(self):
        """Validar datos del cambio de estado."""
        if not self.widget_name.strip():
            raise ValueError("widget_name no puede estar vacío")


@dataclass
class FormSubmissionEventData:
    """Datos para eventos de envío de formularios."""
    
    form_name: str          # Nombre del formulario
    form_data: Dict[str, Any]  # Datos del formulario
    validation_status: bool  # Si los datos son válidos
    submission_result: Optional[str]  # Resultado del envío
    errors: List[str]       # Lista de errores si los hay
    
    def __post_init__(self):
        """Validar datos del envío de formulario."""
        if not self.validation_status and not self.errors:
            raise ValueError("errors es obligatorio cuando validation_status=False")


# ==================== CONSTANTES DE EVENTOS ====================

class EventTypes:
    """Constantes para tipos de eventos del sistema."""
    
    # Eventos de productos
    PRODUCT_SELECTED = "product_selected"
    PRODUCT_SEARCH_REQUEST = "product_search_request" 
    PRODUCT_SEARCH_RESULT = "product_search_result"
    PRODUCT_VALIDATION = "product_validation"
    
    # Eventos de movimientos
    MOVEMENT_ENTRY_ACTION = "movement_entry_action"
    MOVEMENT_VALIDATION = "movement_validation"
    MOVEMENT_ITEM_ADDED = "movement_item_added"
    MOVEMENT_ITEM_REMOVED = "movement_item_removed"
    MOVEMENT_FORM_CLEARED = "movement_form_cleared"
    
    # Eventos de UI
    UI_STATE_CHANGE = "ui_state_change"
    FORM_SUBMISSION = "form_submission"
    WIDGET_FOCUS_CHANGE = "widget_focus_change"
    
    # Eventos de validación
    VALIDATION_SUCCESS = "validation_success"
    VALIDATION_ERROR = "validation_error"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"


class EventSources:
    """Constantes para fuentes de eventos del sistema."""
    
    # Widgets de productos
    PRODUCT_SEARCH_WIDGET = "ProductSearchWidget"
    PRODUCT_LIST_WIDGET = "ProductListWidget"
    
    # Formularios de movimientos
    MOVEMENT_ENTRY_FORM = "MovementEntryForm"
    MOVEMENT_ADJUST_FORM = "MovementAdjustForm"
    MOVEMENT_HISTORY_FORM = "MovementHistoryForm"
    
    # Servicios
    PRODUCT_SERVICE = "ProductService"
    INVENTORY_SERVICE = "InventoryService"
    VALIDATION_SERVICE = "ValidationService"
    
    # Mediadores
    PRODUCT_MOVEMENT_MEDIATOR = "ProductMovementMediator"


# ==================== FACTORY FUNCTIONS ====================

def create_product_selected_event_data(
    product: Dict[str, Any],
    source: str,
    user_action: str = "click"
) -> ProductSelectedEventData:
    """
    Factory para crear datos de evento de selección de producto.
    
    CORRECCIÓN: Normalización automática de campos del producto
    
    Args:
        product: Datos del producto seleccionado
        source: Widget que originó la selección
        user_action: Acción específica del usuario
        
    Returns:
        ProductSelectedEventData: Datos del evento validados y normalizados
    """
    # Crear copia para no modificar el original
    normalized_product = product.copy()
    
    # Normalización automática de campos comunes
    if 'id_producto' in normalized_product and 'id' not in normalized_product:
        normalized_product['id'] = normalized_product['id_producto']
    
    if 'nombre' in normalized_product and 'name' not in normalized_product:
        normalized_product['name'] = normalized_product['nombre']
    
    return ProductSelectedEventData(
        product=normalized_product,
        selection_source=source,
        user_action=user_action
    )


def create_search_request_event_data(
    search_term: str,
    search_type: str,
    requester: str,
    filters: Optional[Dict[str, Any]] = None
) -> ProductSearchRequestEventData:
    """
    Factory para crear datos de evento de solicitud de búsqueda.
    
    Args:
        search_term: Término a buscar
        search_type: Tipo de búsqueda
        requester: Widget que solicita la búsqueda
        filters: Filtros adicionales opcionales
        
    Returns:
        ProductSearchRequestEventData: Datos del evento validados
    """
    return ProductSearchRequestEventData(
        search_term=search_term,
        search_type=search_type,
        filters=filters or {},
        requester=requester
    )


def create_movement_entry_event_data(
    action: str,
    movement_type: str,
    form_state: Dict[str, Any],
    product_data: Optional[Dict[str, Any]] = None,
    quantity: Optional[int] = None
) -> MovementEntryEventData:
    """
    Factory para crear datos de evento de entrada de movimiento.
    
    Args:
        action: Acción específica
        movement_type: Tipo de movimiento
        form_state: Estado actual del formulario
        product_data: Datos del producto (opcional)
        quantity: Cantidad (opcional)
        
    Returns:
        MovementEntryEventData: Datos del evento validados
    """
    return MovementEntryEventData(
        action=action,
        product_data=product_data,
        quantity=quantity,
        movement_type=movement_type,
        form_state=form_state
    )


# ==================== UTILIDADES DE DEBUG ====================

def validate_product_for_events(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validar y normalizar producto para compatibilidad con eventos.
    
    Args:
        product: Datos del producto original
        
    Returns:
        Dict: Producto normalizado para eventos
        
    Raises:
        ValueError: Si el producto no puede normalizarse
    """
    if not product:
        raise ValueError("Producto no puede estar vacío")
    
    normalized = product.copy()
    
    # Validar y normalizar ID
    if 'id' not in normalized and 'id_producto' not in normalized:
        raise ValueError("Producto debe tener 'id' o 'id_producto'")
    
    if 'id_producto' in normalized and 'id' not in normalized:
        normalized['id'] = normalized['id_producto']
    
    # Validar y normalizar nombre
    if 'nombre' not in normalized and 'name' not in normalized:
        raise ValueError("Producto debe tener 'nombre' o 'name'")
    
    if 'nombre' in normalized and 'name' not in normalized:
        normalized['name'] = normalized['nombre']
    
    # Generar code si no existe
    if 'code' not in normalized:
        product_id = normalized.get('id') or normalized.get('id_producto')
        normalized['code'] = str(product_id) if product_id else 'UNKNOWN'
    
    # Generar category si no existe
    if 'category' not in normalized:
        if 'categoria_tipo' in normalized:
            normalized['category'] = normalized['categoria_tipo']
        elif 'id_categoria' in normalized:
            normalized['category'] = f"CAT_{normalized['id_categoria']}"
        else:
            normalized['category'] = 'UNKNOWN'
    
    return normalized


if __name__ == "__main__":
    # Test de la corrección con producto real del sistema
    
    # Producto como viene del ProductService
    product_from_db = {
        "id": 1,
        "nombre": "Laptop HP",
        "stock": 5,
        "precio": 1500.00,
        "id_categoria": 2,
        "categoria_tipo": "MATERIAL"
    }
    
    # Test normalización automática
    try:
        normalized = validate_product_for_events(product_from_db)
        print(f"Producto normalizado: {normalized}")
        
        # Test creación de evento
        event_data = create_product_selected_event_data(
            product=product_from_db,
            source=EventSources.PRODUCT_SEARCH_WIDGET,
            user_action="click"
        )
        
        print(f"Evento creado exitosamente: {event_data}")
        print(f"Producto: {event_data.product['name']} (ID: {event_data.product['id']})")
        print(f"Code: {event_data.product['code']}, Category: {event_data.product['category']}")
        
    except ValueError as e:
        print(f"Error en validación: {e}")
