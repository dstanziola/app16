"""
Schemas de Pydantic para la API REST - Categorías
Sistema de Inventario v2.0

Estos schemas definen la estructura y validación de datos
para los endpoints de categorías siguiendo OpenAPI 3.0.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from enum import Enum


class CategoryType(str, Enum):
    """Tipos válidos de categoría."""
    MATERIAL = "MATERIAL"
    SERVICIO = "SERVICIO"


class CategoryBase(BaseModel):
    """Schema base para categorías."""
    nombre: str = Field(
        ..., 
        min_length=1,
        max_length=60,
        description="Nombre de la categoría"
    )
    tipo: CategoryType = Field(
        ...,
        description="Tipo de categoría: MATERIAL o SERVICIO"
    )
    
    @field_validator('nombre')
    def validate_nombre(cls, v):
        """Validar que el nombre no sea solo espacios."""
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío o ser solo espacios")
        return v.strip()


class CategoryCreate(CategoryBase):
    """Schema para crear una nueva categoría."""
    pass
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Herramientas Eléctricas",
                "tipo": "MATERIAL"
            }
        }


class CategoryUpdate(CategoryBase):
    """Schema para actualizar una categoría existente."""
    nombre: Optional[str] = Field(
        None,
        min_length=1,
        max_length=60,
        description="Nombre de la categoría (opcional)"
    )
    tipo: Optional[CategoryType] = Field(
        None,
        description="Tipo de categoría (opcional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Herramientas Manuales",
                "tipo": "MATERIAL"
            }
        }


class CategoryResponse(CategoryBase):
    """Schema para respuestas de categoría."""
    id_categoria: int = Field(
        ...,
        description="ID único de la categoría"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_categoria": 1,
                "nombre": "Herramientas",
                "tipo": "MATERIAL"
            }
        }


class CategoryListResponse(BaseModel):
    """Schema para lista de categorías."""
    status: Literal["success"] = "success"
    data: list[CategoryResponse] = Field(
        ...,
        description="Lista de categorías"
    )
    count: int = Field(
        ...,
        description="Número total de categorías"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {
                        "id_categoria": 1,
                        "nombre": "Herramientas",
                        "tipo": "MATERIAL"
                    },
                    {
                        "id_categoria": 2,
                        "nombre": "Servicios Técnicos",
                        "tipo": "SERVICIO"
                    }
                ],
                "count": 2
            }
        }


class CategorySingleResponse(BaseModel):
    """Schema para respuesta de categoría individual."""
    status: Literal["success"] = "success"
    data: CategoryResponse = Field(
        ...,
        description="Datos de la categoría"
    )
    message: Optional[str] = Field(
        None,
        description="Mensaje adicional"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "id_categoria": 1,
                    "nombre": "Herramientas",
                    "tipo": "MATERIAL"
                },
                "message": "Categoría obtenida exitosamente"
            }
        }


class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    status: Literal["error"] = "error"
    message: str = Field(
        ...,
        description="Mensaje de error"
    )
    detail: Optional[str] = Field(
        None,
        description="Detalle adicional del error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Categoría no encontrada",
                "detail": "No existe una categoría con ID 999"
            }
        }


class SuccessResponse(BaseModel):
    """Schema para respuestas de éxito sin datos."""
    status: Literal["success"] = "success"
    message: str = Field(
        ...,
        description="Mensaje de éxito"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Categoría eliminada exitosamente"
            }
        }


# Schemas para validación de parámetros de ruta
class CategoryId(BaseModel):
    """Schema para validar ID de categoría."""
    id_categoria: int = Field(
        ...,
        gt=0,
        description="ID de la categoría debe ser mayor a 0"
    )
