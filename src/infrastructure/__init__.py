# src/infrastructure/__init__.py
"""
Capa de Infraestructura - Clean Architecture
Fecha: 2025-07-16
"""

# Importaciones de infraestructura
try:
    from .security import PasswordHasher, create_password_hasher
    __all__ = ['PasswordHasher', 'create_password_hasher']
except ImportError:
    __all__ = []
