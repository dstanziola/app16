"""
Schemas Pydantic para API de Productos - ACTUALIZADO
Sistema de Inventario v2.0 - TDD FASE GREEN

NUEVA FUNCIONALIDAD: Validación de restricción stock=0 para servicios
Modelos de validación para endpoints CRUD de productos usando Pydantic.
"""

from pydantic import BaseModel, field_validator, model_validator, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from src.api.schemas.category_schemas import CategoryType


class ProductCreate(BaseModel):
    """Schema para crear un nuevo producto."""
    
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del producto")
    precio_venta: Decimal = Field(..., gt=0, description="Precio de venta (debe ser mayor a 0)")
    precio_compra: Optional[Decimal] = Field(None, ge=0, description="Precio de compra")
    stock_inicial: int = Field(..., ge=0, description="Stock inicial (debe ser mayor o igual a 0)")
    stock_minimo: int = Field(default=1, ge=0, description="Stock mínimo para alertas")
    id_categoria: int = Field(..., gt=0, description="ID de la categoría")
    
    # NUEVO: Campo opcional para validación de tipo de categoría
    categoria_tipo: Optional[CategoryType] = Field(None, description="Tipo de categoría para validación")
    
    @field_validator('nombre')
    def validate_nombre(cls, v):
        """Validar que el nombre no esté vacío después de limpiar espacios."""
        if v:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede estar vacío")
        return v
    
    @field_validator('descripcion')
    def validate_descripcion(cls, v):
        """Limpiar espacios en la descripción."""
        if v:
            return v.strip()
        return v
    
    @model_validator(mode='after')
    def validate_business_rules(self):
        """Validar reglas de negocio del sistema."""
        # Validar precio de compra vs venta
        if self.precio_compra is not None and self.precio_compra > self.precio_venta:
            raise ValueError("El precio de compra no puede ser mayor al precio de venta")
        
        # NUEVA VALIDACIÓN: Stock = 0 para servicios
        if self.categoria_tipo == CategoryType.SERVICIO:
            if self.stock_inicial != 0:
                # Auto-corrección: forzar stock a 0 para servicios
                self.stock_inicial = 0
            
            if self.stock_minimo != 0:
                # Auto-corrección: forzar stock mínimo a 0 para servicios
                self.stock_minimo = 0
        
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Laptop HP EliteBook",
                "descripcion": "Laptop profesional para oficina",
                "precio_venta": 1500.00,
                "precio_compra": 1200.00,
                "stock_inicial": 10,
                "stock_minimo": 2,
                "id_categoria": 1,
                "categoria_tipo": "MATERIAL"
            }
        }


class ProductCreateWithValidation(ProductCreate):
    """Schema para crear producto con validación estricta de servicios."""
    
    categoria_tipo: CategoryType = Field(..., description="Tipo de categoría (requerido para validación)")
    
    @model_validator(mode='after')
    def validate_service_stock_strict(self):
        """Validación estricta: servicios NO pueden tener stock > 0."""
        # Validar precio de compra vs venta
        if self.precio_compra is not None and self.precio_compra > self.precio_venta:
            raise ValueError("El precio de compra no puede ser mayor al precio de venta")
        
        # VALIDACIÓN ESTRICTA: Stock = 0 para servicios (sin auto-corrección)
        if self.categoria_tipo == CategoryType.SERVICIO:
            if self.stock_inicial != 0:
                raise ValueError("Los servicios no pueden tener stock inicial diferente de 0")
            
            if self.stock_minimo != 0:
                raise ValueError("Los servicios no pueden tener stock mínimo diferente de 0")
        
        return self


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto existente."""
    
    nombre: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del producto")
    precio_venta: Optional[Decimal] = Field(None, gt=0, description="Precio de venta")
    precio_compra: Optional[Decimal] = Field(None, ge=0, description="Precio de compra")
    stock_minimo: Optional[int] = Field(None, ge=0, description="Stock mínimo")
    id_categoria: Optional[int] = Field(None, gt=0, description="ID de la categoría")
    activo: Optional[bool] = Field(None, description="Estado activo/inactivo del producto")
    
    # NUEVO: Campo opcional para validación de tipo de categoría
    categoria_tipo: Optional[CategoryType] = Field(None, description="Tipo de categoría para validación")
    
    @field_validator('nombre')
    def validate_nombre(cls, v):
        """Validar que el nombre no esté vacío después de limpiar espacios."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede estar vacío")
        return v
    
    @field_validator('descripcion')
    def validate_descripcion(cls, v):
        """Limpiar espacios en la descripción."""
        if v is not None:
            return v.strip()
        return v
    
    @model_validator(mode='after')
    def validate_service_stock_update(self):
        """Validar que servicios no puedan actualizar stock."""
        # NUEVA VALIDACIÓN: Stock = 0 para servicios en actualizaciones
        if self.categoria_tipo == CategoryType.SERVICIO:
            if self.stock_minimo is not None and self.stock_minimo != 0:
                raise ValueError("Los servicios no pueden tener stock mínimo diferente de 0")
        
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "precio_venta": 1450.00,
                "stock_minimo": 3,
                "activo": True,
                "categoria_tipo": "MATERIAL"
            }
        }


class ProductResponse(BaseModel):
    """Schema para respuesta de un producto."""
    
    id_producto: int
    nombre: str
    descripcion: Optional[str]
    precio_venta: Decimal
    precio_compra: Optional[Decimal]
    stock_actual: int
    stock_minimo: int
    id_categoria: int
    categoria_nombre: Optional[str]
    categoria_tipo: Optional[CategoryType] = Field(None, description="Tipo de categoría")  # NUEVO
    activo: bool
    fecha_creacion: str
    
    @model_validator(mode='after')
    def validate_response_consistency(self):
        """Validar consistencia en respuesta de servicios."""
        # VALIDACIÓN: Servicios deben aparecer con stock = 0
        if self.categoria_tipo == CategoryType.SERVICIO:
            if self.stock_actual != 0:
                # Log de inconsistencia (no corregir en respuesta)
                print(f"WARNING: Servicio {self.id_producto} tiene stock inconsistente: {self.stock_actual}")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_producto": 1,
                "nombre": "Laptop HP EliteBook",
                "descripcion": "Laptop profesional para oficina",
                "precio_venta": 1500.00,
                "precio_compra": 1200.00,
                "stock_actual": 8,
                "stock_minimo": 2,
                "id_categoria": 1,
                "categoria_nombre": "Electrónicos",
                "categoria_tipo": "MATERIAL",
                "activo": True,
                "fecha_creacion": "2025-05-27T10:00:00"
            }
        }


class ProductListResponse(BaseModel):
    """Schema para respuesta de lista de productos."""
    
    status: str = "success"
    data: List[ProductResponse]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {
                        "id_producto": 1,
                        "nombre": "Laptop HP",
                        "descripcion": "Laptop para oficina",
                        "precio_venta": 1500.00,
                        "stock_actual": 8,
                        "categoria_nombre": "Electrónicos",
                        "categoria_tipo": "MATERIAL",
                        "activo": True
                    }
                ],
                "count": 1
            }
        }


class ProductSingleResponse(BaseModel):
    """Schema para respuesta de un solo producto."""
    
    status: str = "success"
    data: ProductResponse
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "id_producto": 1,
                    "nombre": "Laptop HP",
                    "precio_venta": 1500.00,
                    "stock_actual": 8,
                    "categoria_nombre": "Electrónicos",
                    "categoria_tipo": "MATERIAL",
                    "activo": True
                },
                "message": "Producto obtenido exitosamente"
            }
        }


class ProductSearchRequest(BaseModel):
    """Schema para petición de búsqueda."""
    q: str = Field(..., min_length=1, description="Término de búsqueda")


class ProductSearchResponse(BaseModel):
    """Schema para respuesta de búsqueda de productos."""
    
    status: str = "success"
    data: List[ProductResponse]
    count: int
    query: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {
                        "id_producto": 1,
                        "nombre": "Laptop HP",
                        "precio_venta": 1500.00,
                        "stock_actual": 8,
                        "categoria_tipo": "MATERIAL",
                        "activo": True
                    }
                ],
                "count": 1,
                "query": "laptop"
            }
        }


class LowStockProductResponse(BaseModel):
    """Schema para productos con stock bajo."""
    
    id_producto: int
    nombre: str
    stock_actual: int
    stock_minimo: int
    categoria_nombre: Optional[str]
    categoria_tipo: Optional[CategoryType] = Field(None, description="Tipo de categoría")  # NUEVO
    precio_venta: Decimal
    activo: bool
    
    @model_validator(mode='after')
    def validate_low_stock_services(self):
        """Validar que servicios no aparezcan en stock bajo."""
        # VALIDACIÓN: Servicios no deberían estar en reportes de stock bajo
        if self.categoria_tipo == CategoryType.SERVICIO:
            if self.stock_actual != 0 or self.stock_minimo != 0:
                print(f"WARNING: Servicio {self.id_producto} aparece incorrectamente en stock bajo")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "id_producto": 4,
                "nombre": "Cable USB",
                "stock_actual": 2,
                "stock_minimo": 5,
                "categoria_nombre": "Accesorios",
                "categoria_tipo": "MATERIAL",
                "precio_venta": 15.99,
                "activo": True
            }
        }


class LowStockListResponse(BaseModel):
    """Schema para respuesta de productos con stock bajo."""
    
    status: str = "success"
    data: List[LowStockProductResponse]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {
                        "id_producto": 4,
                        "nombre": "Cable USB",
                        "stock_actual": 2,
                        "stock_minimo": 5,
                        "categoria_nombre": "Accesorios",
                        "categoria_tipo": "MATERIAL",
                        "activo": True
                    }
                ],
                "count": 1
            }
        }


class ProductStatsResponse(BaseModel):
    """Schema para estadísticas de productos."""
    
    status: str = "success"
    data: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "total_products": 25,
                    "active_products": 23,
                    "inactive_products": 2,
                    "low_stock_products": 3,
                    "total_stock_value": 45750.50,
                    "categories_distribution": {
                        "Electrónicos": 12,
                        "Accesorios": 8,
                        "Software": 5
                    },
                    "materials_vs_services": {
                        "MATERIAL": 20,
                        "SERVICIO": 5
                    }
                }
            }
        }


# Schemas de error reutilizados de categorías
class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    
    status: str = "error"
    message: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Violación de regla de negocio",
                "detail": "Los servicios no pueden tener stock diferente de 0"
            }
        }


class SuccessResponse(BaseModel):
    """Schema para respuestas de éxito simples."""
    
    status: str = "success"
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Producto creado exitosamente"
            }
        }


# NUEVO: Schema específico para validación de reglas de negocio
class ServiceStockValidationError(ErrorResponse):
    """Schema específico para errores de validación de stock en servicios."""
    
    message: str = "Violación de regla de negocio: Stock de servicios"
    detail: str = "Los servicios no pueden tener stock diferente de 0"
    error_code: str = "SERVICE_STOCK_VIOLATION"
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Violación de regla de negocio: Stock de servicios",
                "detail": "Los servicios no pueden tener stock diferente de 0",
                "error_code": "SERVICE_STOCK_VIOLATION"
            }
        }
