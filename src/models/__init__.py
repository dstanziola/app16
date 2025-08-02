"""
Módulo models - Modelos de datos del sistema de inventario.

Este módulo contiene todas las entidades de dominio implementadas
siguiendo metodología TDD estricta y principios de Clean Architecture.

Modelos disponibles:
- Categoria: Categorías MATERIAL/SERVICIO
- Producto: Productos con cálculos financieros
- Cliente: Clientes con RUC opcional
- Usuario: Usuarios con autenticación
- Venta: Transacciones de venta
- Movimiento: Movimientos de inventario
"""

# Importar todas las clases de modelos
from .categoria import Categoria
from .producto import Producto
from .cliente import Cliente
from .usuario import Usuario
from .venta import Venta
from .movimiento import Movimiento

# Definir qué se exporta cuando se hace "from models import *"
__all__ = [
    'Categoria',
    'Producto', 
    'Cliente',
    'Usuario',
    'Venta',
    'Movimiento'
]

# Metadatos del módulo
__version__ = '2.0.0'
__author__ = 'Sistema TDD'
__description__ = 'Modelos de datos para Sistema de Inventario'
