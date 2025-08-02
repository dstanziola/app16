"""
Patterns Package - Clean Architecture Design Patterns
Sistema de Inventario

Incluye implementaciones de:
- Event Bus Pattern (desacoplamiento de comunicación)
- Mediator Pattern (coordinación centralizada)
"""

from .event_bus import EventBus, get_event_bus, create_event_bus, InventoryEvents

__all__ = [
    'EventBus',
    'get_event_bus', 
    'create_event_bus',
    'InventoryEvents'
]
