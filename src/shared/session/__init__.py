# src/shared/session/__init__.py
"""
Gestión de sesiones - Shared Layer
Fecha: 2025-07-16
"""

from .session_manager import SessionManager, create_session_manager

__all__ = [
    'SessionManager',
    'create_session_manager'
]
