"""
Event Bus Pattern Implementation
Sistema de Inventario - Clean Architecture

Implementa un Event Bus thread-safe para desacoplar componentes UI y eliminar
dependencias circulares entre ProductSearchWidget y MovementEntryForm.

Patrón: Observer + Publisher-Subscriber
Responsabilidad: Gestión centralizada de eventos entre componentes
Thread-Safety: Sí (usando threading.Lock)
"""

import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
from utils.logger import get_logger


@dataclass
class EventSubscription:
    """Representa una suscripción a un evento específico"""
    event_name: str
    callback: Callable[[Any], None]
    subscriber_id: str
    created_at: datetime = field(default_factory=datetime.now)


class EventBus:
    """
    Event Bus implementation para desacoplar componentes UI
    
    Características:
    - Thread-safe para suscripciones y publicaciones concurrentes
    - Soporte para múltiples suscriptores por evento
    - Logging automático de eventos para debugging
    - Manejo robusto de errores en callbacks
    - Identificación única de suscriptores
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Inicializar Event Bus
        
        Args:
            enable_logging: Si activar logging de eventos
        """
        self._subscribers: Dict[str, List[EventSubscription]] = {}
        self._lock = threading.RLock()  # Re-entrant lock para thread safety
        self._enable_logging = enable_logging
        self._logger = get_logger(__name__) if enable_logging else None
        
        if self._enable_logging:
            self._logger.info("EventBus inicializado correctamente")
    
    def subscribe(
        self, 
        event_name: str, 
        callback: Callable[[Any], None],
        subscriber_id: Optional[str] = None
    ) -> str:
        """
        Suscribirse a un evento específico
        
        Args:
            event_name: Nombre del evento
            callback: Función callback a ejecutar
            subscriber_id: ID opcional del suscriptor
            
        Returns:
            str: ID único de la suscripción
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            
            # Generar ID único si no se proporciona
            if subscriber_id is None:
                subscriber_id = f"{event_name}_{len(self._subscribers[event_name])}"
            
            subscription = EventSubscription(
                event_name=event_name,
                callback=callback,
                subscriber_id=subscriber_id
            )
            
            self._subscribers[event_name].append(subscription)
            
            if self._enable_logging:
                self._logger.info(
                    f"Suscripción agregada: {event_name} -> {subscriber_id}"
                )
            
            return subscriber_id
    
    def unsubscribe(
        self, 
        event_name: str, 
        callback: Optional[Callable] = None,
        subscriber_id: Optional[str] = None
    ) -> bool:
        """
        Desuscribirse de un evento
        
        Args:
            event_name: Nombre del evento
            callback: Callback específico a remover (opcional)
            subscriber_id: ID específico a remover (opcional)
            
        Returns:
            bool: True si se removió alguna suscripción
        """
        with self._lock:
            if event_name not in self._subscribers:
                return False
            
            original_count = len(self._subscribers[event_name])
            
            # Filtrar suscripciones a remover
            if callback is not None:
                self._subscribers[event_name] = [
                    sub for sub in self._subscribers[event_name]
                    if sub.callback != callback
                ]
            elif subscriber_id is not None:
                self._subscribers[event_name] = [
                    sub for sub in self._subscribers[event_name]
                    if sub.subscriber_id != subscriber_id
                ]
            else:
                # Remover todas las suscripciones del evento
                self._subscribers[event_name] = []
            
            removed_count = original_count - len(self._subscribers[event_name])
            
            if self._enable_logging and removed_count > 0:
                self._logger.info(
                    f"Suscripciones removidas: {event_name} ({removed_count})"
                )
            
            return removed_count > 0
    
    def publish(self, event_name: str, event_data: Any = None) -> int:
        """
        Publicar un evento a todos los suscriptores
        
        Args:
            event_name: Nombre del evento a publicar
            event_data: Datos del evento
            
        Returns:
            int: Número de callbacks ejecutados exitosamente
        """
        with self._lock:
            if event_name not in self._subscribers:
                if self._enable_logging:
                    self._logger.debug(f"Evento publicado sin suscriptores: {event_name}")
                return 0
            
            subscriptions = self._subscribers[event_name].copy()
        
        successful_callbacks = 0
        
        if self._enable_logging:
            self._logger.info(
                f"Publicando evento: {event_name} -> {len(subscriptions)} suscriptores"
            )
        
        # Ejecutar callbacks fuera del lock para evitar deadlocks
        for subscription in subscriptions:
            try:
                subscription.callback(event_data)
                successful_callbacks += 1
                
                if self._enable_logging:
                    self._logger.debug(
                        f"Callback ejecutado: {subscription.subscriber_id}"
                    )
                    
            except Exception as e:
                if self._enable_logging:
                    self._logger.error(
                        f"Error en callback {subscription.subscriber_id}: {e}"
                    )
        
        return successful_callbacks
    
    def has_subscriber(
        self, 
        event_name: str, 
        callback: Optional[Callable] = None,
        subscriber_id: Optional[str] = None
    ) -> bool:
        """
        Verificar si existe un suscriptor específico
        
        Args:
            event_name: Nombre del evento
            callback: Callback específico a verificar
            subscriber_id: ID específico a verificar
            
        Returns:
            bool: True si existe el suscriptor
        """
        with self._lock:
            if event_name not in self._subscribers:
                return False
            
            for subscription in self._subscribers[event_name]:
                if callback is not None and subscription.callback == callback:
                    return True
                if subscriber_id is not None and subscription.subscriber_id == subscriber_id:
                    return True
            
            return False
    
    def get_subscribers_count(self, event_name: str) -> int:
        """
        Obtener número de suscriptores para un evento
        
        Args:
            event_name: Nombre del evento
            
        Returns:
            int: Número de suscriptores
        """
        with self._lock:
            return len(self._subscribers.get(event_name, []))
    
    def get_all_events(self) -> List[str]:
        """
        Obtener lista de todos los eventos con suscriptores
        
        Returns:
            List[str]: Lista de nombres de eventos
        """
        with self._lock:
            return list(self._subscribers.keys())
    
    def clear_all_subscriptions(self) -> None:
        """Limpiar todas las suscripciones (útil para testing)"""
        with self._lock:
            cleared_events = len(self._subscribers)
            self._subscribers.clear()
            
            if self._enable_logging:
                self._logger.info(f"Todas las suscripciones limpiadas ({cleared_events} eventos)")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Obtener información de debugging del EventBus
        
        Returns:
            Dict con información de estado
        """
        with self._lock:
            return {
                'total_events': len(self._subscribers),
                'events': {
                    event_name: len(subscriptions) 
                    for event_name, subscriptions in self._subscribers.items()
                },
                'total_subscriptions': sum(
                    len(subs) for subs in self._subscribers.values()
                ),
                'logging_enabled': self._enable_logging
            }


# Instancia global singleton del EventBus
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Obtener instancia global del EventBus (Singleton)
    
    Returns:
        EventBus: Instancia global
    """
    global _global_event_bus
    
    if _global_event_bus is None:
        _global_event_bus = EventBus(enable_logging=True)
    
    return _global_event_bus


def create_event_bus(enable_logging: bool = True) -> EventBus:
    """
    Crear nueva instancia del EventBus (para testing o casos específicos)
    
    Args:
        enable_logging: Si activar logging
        
    Returns:
        EventBus: Nueva instancia
    """
    return EventBus(enable_logging=enable_logging)


# Eventos estándar del sistema de inventario
class InventoryEvents:
    """Constantes para eventos estándar del sistema"""
    
    # Eventos de búsqueda de productos
    PRODUCT_SEARCH_STARTED = "product_search_started"
    PRODUCT_SEARCH_COMPLETED = "product_search_completed"
    PRODUCT_SEARCH_FAILED = "product_search_failed"
    
    # Eventos de selección de productos
    PRODUCT_SELECTED = "product_selected"
    PRODUCT_DESELECTED = "product_deselected"
    PRODUCT_AUTO_SELECTED = "product_auto_selected"
    
    # Eventos de gestión de cantidad
    QUANTITY_FOCUS_REQUESTED = "quantity_focus_requested"
    QUANTITY_VALIDATED = "quantity_validated"
    QUANTITY_INVALID = "quantity_invalid"
    
    # Eventos de entrada de inventario
    PRODUCT_ADDED_TO_LIST = "product_added_to_list"
    PRODUCT_REMOVED_FROM_LIST = "product_removed_from_list"
    ENTRY_VALIDATION_STARTED = "entry_validation_started"
    ENTRY_VALIDATION_COMPLETED = "entry_validation_completed"
    ENTRY_REGISTRATION_STARTED = "entry_registration_started"
    ENTRY_REGISTRATION_COMPLETED = "entry_registration_completed"
    ENTRY_REGISTRATION_FAILED = "entry_registration_failed"
    
    # Eventos de interfaz de usuario
    FORM_CLEARED = "form_cleared"
    NEXT_PRODUCT_PREPARED = "next_product_prepared"
    SEARCH_FIELD_FOCUSED = "search_field_focused"
    
    # Eventos de validación
    PRODUCT_VALIDATION_PASSED = "product_validation_passed"
    PRODUCT_VALIDATION_FAILED = "product_validation_failed"
    SERVICE_PRODUCT_REJECTED = "service_product_rejected"
