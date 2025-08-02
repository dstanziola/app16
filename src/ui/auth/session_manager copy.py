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
from models.usuario import Usuario


class SessionManager:
    """Gestor de sesiones de usuario para la aplicación.
       Implementación tipo Singleton simple.
    """
    
    def __init__(self):
        """Inicializa el gestor de sesiones."""
        self._current_user: Optional[Usuario] = None
        self._is_authenticated: bool = False
        
    @property
    def current_user(self) -> Optional[Usuario]:
        """Retorna el usuario actualmente autenticado."""
        return self._current_user
        
    @property
    def is_authenticated(self) -> bool:
        """Retorna True si hay un usuario autenticado."""
        return self._is_authenticated
        
    def login(self, user: Usuario) -> None:
        """
        Establece sesión para usuario autenticado.
        
        Args:
            user: Usuario autenticado exitosamente
        """
        self._current_user = user
        self._is_authenticated = True
        
    def logout(self) -> None:
        """Cierra la sesión actual y limpia datos de usuario."""
        self._current_user = None
        self._is_authenticated = False
        
    def has_permission(self, action: str) -> bool:
        """
        Verifica si el usuario actual tiene permiso para una acción.
        
        Args:
            action: Acción a verificar ('admin', 'sales', 'reports', etc.)
            
        Returns:
            True si el usuario tiene permiso, False en caso contrario
        """
        if not self.is_authenticated or not self._current_user:
            return False
            
        user_role = self._current_user.rol
        
        # Administradores tienen acceso completo
        if user_role == 'ADMIN':
            return True
            
        # Vendedores solo tienen acceso a ventas y consultas
        if user_role == 'VENDEDOR':
            allowed_actions = ['sales', 'view_products', 'view_clients', 'view_categories']
            return action in allowed_actions
            
        return False
        
    def get_user_info(self) -> dict:
        """
        Retorna información del usuario actual para mostrar en UI.
        
        Returns:
            Dict con información de usuario o datos vacíos si no hay sesión
        """
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


# Instancia global del gestor de sesiones
session_manager = SessionManager()
