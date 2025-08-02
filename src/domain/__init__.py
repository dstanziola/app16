# src/domain/__init__.py
"""
Capa de Dominio - Clean Architecture
Fecha: 2025-07-16
"""

# Importaciones de servicios del dominio
try:
    from .services import IAuthService, AuthenticationError, ValidationError, SessionExpiredError
    __all__ = ['IAuthService', 'AuthenticationError', 'ValidationError', 'SessionExpiredError']
except ImportError:
    __all__ = []
