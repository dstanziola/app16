"""
Autenticación de usuarios - Módulo de login.

Este módulo contiene la lógica de autenticación y componentes
relacionados con el sistema de login.

ACTUALIZACIÓN: SessionManager migrado a src/shared/session/
Para mantener compatibilidad, se reexporta desde la nueva ubicación.
"""

# Importar SessionManager desde la nueva ubicación (shared layer)
from shared.session.session_manager import SessionManager
from .login_window import LoginWindow

# Crear instancia global para compatibilidad
session_manager = SessionManager()

__all__ = ['SessionManager', 'session_manager', 'LoginWindow']
