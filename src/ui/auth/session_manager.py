# ui/auth/session_manager.py

"""
Sistema de gestión de sesiones de usuario.

Este módulo maneja el estado de la sesión del usuario autenticado,
incluyendo información de usuario, permisos y configuraciones.

RESPONSABILIDADES:
- Mantener información de usuario activo
- Gestionar permisos y roles
- Proporcionar interfaz para validación de acceso
- Limpiar sesión al logout
"""

from typing import Optional
from models.usuario import Usuario  # Asegúrate de tener esta clase definida

class SessionManager:
    """
    Gestor de sesión para mantener al usuario autenticado actual.
    """

    def __init__(self):
        self._current_user: Optional[Usuario] = None
        self._is_authenticated: bool = False

    def login(self, user: Usuario) -> None:
        """Establece sesión para usuario autenticado."""
        self._current_user = user
        self._is_authenticated = True

    def logout(self) -> None:
        """Cierra la sesión actual y limpia datos de usuario."""
        self._current_user = None
        self._is_authenticated = False

    def has_permission(self, action: str) -> bool:
        """Verifica si el usuario actual tiene permiso para una acción."""
        if not self.is_authenticated or not self._current_user:
            return False

        user_role = self._current_user.rol

        if user_role == 'ADMIN':
            return True

        if user_role == 'VENDEDOR':
            allowed_actions = ['sales', 'view_products', 'view_clients', 'view_categories']
            return action in allowed_actions

        return False

    def get_user_info(self) -> dict:
        """Retorna información del usuario actual para mostrar en UI."""
        if not self.is_authenticated or not self._current_user:
            return {
                'nombre_usuario': 'No autenticado',
                'rol': '',
                'activo': False
            }

        return {
            'nombre_usuario': self._current_user.nombre_usuario,
            'rol': self._current_user.rol,
            'activo': self._current_user.activo
        }

    def get_current_user(self) -> Optional[dict]:
        """Retorna un diccionario con los datos del usuario actual, compatible con el sistema."""
        if self._current_user:
            return self.get_user_info()
        return None

    @property
    def current_user(self) -> Optional[Usuario]:
        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

# Instancia global
session_manager = SessionManager()
