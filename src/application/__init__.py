# src/application/__init__.py
"""
Capa de Aplicación - Clean Architecture
Fecha: 2025-07-16
"""

# Importaciones de servicios de aplicación
try:
    from .services import AuthService, create_auth_service
    __all__ = ['AuthService', 'create_auth_service']
except ImportError:
    __all__ = []
