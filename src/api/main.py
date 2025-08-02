"""
Aplicación principal FastAPI para Sistema de Inventario
Sistema de Inventario v2.0 - TDD FASE GREEN

Punto de entrada principal para la API REST del sistema de inventario.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Importar routers
from api.routes.categories import router as categories_router
from api.routes.products import router as products_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Inventario API",
    description="API REST para gestión de inventario con TDD",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers con prefijo v1
app.include_router(
    categories_router,
    prefix="/api/v1",
    tags=["categorias"]
)

app.include_router(
    products_router,
    prefix="/api/v1", 
    tags=["productos"]
)

# Endpoint de salud
@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio."""
    return {
        "status": "healthy",
        "service": "inventario-api",
        "version": "2.0.0"
    }

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "Sistema de Inventario API v2.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
