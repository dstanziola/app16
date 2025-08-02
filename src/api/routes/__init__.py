"""
Rutas de la API REST
Sistema de Inventario v2.0

Exportación centralizada de todas las rutas de la API.
"""

from .categories import router as categories_router
from .products import router as products_router

__all__ = [
    'categories_router',
    'products_router'
]
