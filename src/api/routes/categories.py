"""
Rutas de la API REST para Categorías - VERSIÓN FINAL
Sistema de Inventario v2.0 - TDD FASE GREEN COMPLETADA

Implementación final de endpoints CRUD para categorías que pasa todos los tests.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List
import logging

# Importar schemas
from api.schemas import (
    CategoryCreate,
    CategoryUpdate, 
    CategoryResponse,
    CategoryListResponse,
    CategorySingleResponse,
    ErrorResponse,
    SuccessResponse
)

# Importar servicios de negocio
from services import CategoryService
from db.database import DatabaseConnection

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router de categorías
router = APIRouter(
    prefix="/categories",
    tags=["Categorías"]
)


# Dependency injection para el servicio
def get_category_service() -> CategoryService:
    """Obtener instancia del servicio de categorías."""
    db_connection = DatabaseConnection("inventario.db")
    return CategoryService(db_connection)


def convert_category_to_dict(category):
    """Convertir categoría a diccionario para respuesta JSON."""
    if hasattr(category, 'to_dict'):
        return category.to_dict()
    elif isinstance(category, dict):
        return category
    else:
        return {
            "id_categoria": getattr(category, 'id_categoria', category.get('id_categoria', None)),
            "nombre": getattr(category, 'nombre', category.get('nombre', '')),
            "tipo": getattr(category, 'tipo', category.get('tipo', ''))
        }


@router.get("/")
async def get_categories(
    category_service: CategoryService = Depends(get_category_service)
):
    """Obtener todas las categorías - Formato compatible con tests."""
    try:
        logger.info("Obteniendo todas las categorías")
        categories = category_service.get_all_categories()
        
        # Convertir a formato esperado por tests
        categories_data = [convert_category_to_dict(cat) for cat in categories]
        
        return {
            "status": "success",
            "data": categories_data,
            "count": len(categories_data)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo categorías: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor",
                "detail": str(e)
            }
        )


@router.get("/{category_id}")
async def get_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service)
):
    """Obtener categoría por ID - Formato compatible con tests."""
    try:
        # Validar ID positivo - permitir que FastAPI maneje esto automáticamente para 422
        if category_id <= 0:
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "ID de categoría debe ser mayor a 0"
                }
            )
        
        logger.info(f"Obteniendo categoría con ID: {category_id}")
        category = category_service.get_category_by_id(category_id)
        
        if category is None:
            # Formato directo esperado por test_get_category_by_id_not_found
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Categoría con ID {category_id} no encontrada"
                }
            )
        
        category_data = convert_category_to_dict(category)
        
        return {
            "status": "success",
            "data": category_data,
            "message": "Categoría obtenida exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo categoría {category_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor"
            }
        )


@router.post("/")
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service)
):
    """Crear nueva categoría - Formato compatible con tests."""
    try:
        logger.info(f"Creando nueva categoría: {category_data.nombre}")
        
        # Crear la categoría usando el servicio
        new_category = category_service.create_category(
            nombre=category_data.nombre,
            tipo=category_data.tipo.value
        )
        
        category_dict = convert_category_to_dict(new_category)
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "data": category_dict,
                "message": "Categoría creada exitosamente"
            }
        )
        
    except ValueError as e:
        # Error de lógica de negocio - formato directo esperado por test_create_category_duplicate_name
        logger.warning(f"Error de validación creando categoría: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error creando categoría: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor"
            }
        )


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service)
):
    """Actualizar categoría - Formato compatible con tests."""
    try:
        if category_id <= 0:
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "ID de categoría debe ser mayor a 0"
                }
            )
        
        logger.info(f"Actualizando categoría ID: {category_id}")
        
        # Preparar datos para actualización
        update_data = {}
        if category_data.nombre is not None:
            update_data['nombre'] = category_data.nombre
        if category_data.tipo is not None:
            update_data['tipo'] = category_data.tipo.value
        
        updated_category = category_service.update_category(category_id, **update_data)
        
        if updated_category is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Categoría con ID {category_id} no encontrada"
                }
            )
        
        category_dict = convert_category_to_dict(updated_category)
        
        return {
            "status": "success",
            "data": category_dict,
            "message": "Categoría actualizada exitosamente"
        }
        
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error actualizando categoría {category_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor"
            }
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    category_service: CategoryService = Depends(get_category_service)
):
    """Eliminar categoría - Formato compatible con tests."""
    try:
        if category_id <= 0:
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "ID de categoría debe ser mayor a 0"
                }
            )
        
        logger.info(f"Eliminando categoría ID: {category_id}")
        
        success = category_service.delete_category(category_id)
        
        if not success:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Categoría con ID {category_id} no encontrada"
                }
            )
        
        return {
            "status": "success",
            "message": "Categoría eliminada exitosamente"
        }
        
    except ValueError as e:
        # Error por productos asociados - formato directo esperado por test
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error eliminando categoría {category_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor"
            }
        )

# Endpoint adicional para estadísticas
@router.get("/stats/summary")
async def get_category_stats(
    category_service: CategoryService = Depends(get_category_service)
):
    """Obtener estadísticas de categorías."""
    try:
        categories = category_service.get_all_categories()
        total_categories = len(categories)
        material_count = sum(1 for cat in categories if cat.get('tipo') == 'MATERIAL')
        service_count = total_categories - material_count
        
        return {
            "status": "success",
            "data": {
                "total_categories": total_categories,
                "material_categories": material_count,
                "service_categories": service_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error interno del servidor"
            }
        )
