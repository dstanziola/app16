"""
Mediators Package - Mediator Pattern Implementations
Sistema de Inventario

Incluye mediators específicos para coordinar componentes del sistema:
- ProductEntryMediator: Coordinación flujo entrada productos
"""

from .product_entry_mediator import ProductEntryMediator, ProductEntryState

__all__ = [
    'ProductEntryMediator',
    'ProductEntryState'
]
