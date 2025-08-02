"""
Schemas de Pydantic para la API REST
Sistema de Inventario v2.0

Exportación centralizada de todos los schemas.
"""

# Schemas de Categorías
from .category_schemas import (
    CategoryType,
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategorySingleResponse,
    CategoryId
)

# Schemas de Productos
from .product_schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductSingleResponse,
    ProductSearchResponse,
    LowStockProductResponse,
    LowStockListResponse,
    ProductStatsResponse
)

# Schemas compartidos
from .category_schemas import ErrorResponse, SuccessResponse

__all__ = [
    # Categorías
    'CategoryType',
    'CategoryBase', 
    'CategoryCreate',
    'CategoryUpdate',
    'CategoryResponse',
    'CategoryListResponse',
    'CategorySingleResponse',
    'CategoryId',
    
    # Productos
    'ProductCreate',
    'ProductUpdate',
    'ProductResponse',
    'ProductListResponse',
    'ProductSingleResponse',
    'ProductSearchResponse',
    'LowStockProductResponse',
    'LowStockListResponse',
    'ProductStatsResponse',
    
    # Compartidos
    'ErrorResponse',
    'SuccessResponse'
]
