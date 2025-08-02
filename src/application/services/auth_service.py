# src/application/services/auth_service.py
"""
AuthService - Application Layer
Clean Architecture - Capa de Aplicación
Fecha: 2025-07-16
Propósito: Implementación concreta servicio autenticación
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from domain.services.auth_service import (
    IAuthService, 
    AuthenticationError, 
    ValidationError, 
    SessionExpiredError
)
from models.usuario import Usuario


class AuthService(IAuthService):
    """
    Servicio de autenticación empresarial.
    
    Implementa interface IAuthService siguiendo Clean Architecture.
    
    Responsabilidades:
    - Autenticación segura usuarios
    - Gestión sesiones con timeout
    - Validación permisos por rol
    - Logging eventos seguridad
    
    Principios aplicados:
    - Single Responsibility (solo autenticación)
    - Dependency Inversion (depende de abstracciones)
    - Open/Closed (extensible sin modificar)
    """
    
    def __init__(self, user_repository, session_manager, password_hasher):
        """
        Inicializar AuthService con dependencias inyectadas.
        
        Args:
            user_repository: Repositorio usuarios (interface)
            session_manager: Gestor sesiones (interface)
            password_hasher: Hasher passwords (interface)
        """
        self._user_repository = user_repository
        self._session_manager = session_manager
        self._password_hasher = password_hasher
        self._logger = logging.getLogger(__name__)
        
        # Configuración seguridad
        self._max_login_attempts = 3
        self._session_timeout = 3600  # 1 hora en segundos
        
        self._logger.info("AuthService inicializado correctamente")
    
    def authenticate(self, username: str, password: str) -> Optional[Usuario]:
        """
        Autenticar usuario con credenciales.
        
        Implementación TDD para pasar tests definidos.
        """
        try:
            # Validación entrada (test_authenticate_empty_credentials_fails)
            if not username or not password:
                self._logger.warning(f"Intento autenticación con credenciales vacías")
                return None
            
            # Buscar usuario en repositorio
            user = self._user_repository.get_by_username(username)
            
            # Validar usuario existe (test_authenticate_invalid_username_fails)
            if not user:
                self._logger.warning(f"Usuario no encontrado: {username}")
                return None
            
            # Validar usuario activo (test_authenticate_inactive_user_fails)
            if not user.es_activo():
                self._logger.warning(f"Usuario inactivo: {username}")
                return None
            
            # Verificar password (test_authenticate_invalid_password_fails)
            if not self._password_hasher.verify_password(password, user.password_hash):
                self._logger.warning(f"Password incorrecto para usuario: {username}")
                return None
            
            # Autenticación exitosa - establecer sesión
            self._session_manager.login(user)
            
            # Logging exitoso (test_authenticate_valid_user_success)
            self._logger.info(f"Autenticación exitosa: {username} ({user.rol})")
            
            return user
            
        except Exception as e:
            self._logger.error(f"Error interno autenticación {username}: {e}")
            raise AuthenticationError(f"Error interno autenticación: {str(e)}")
    
    def get_current_user(self) -> Optional[Usuario]:
        """
        Obtener usuario actual autenticado.
        
        Implementación TDD para test_get_current_user_success.
        """
        try:
            return self._session_manager.get_current_user()
        except Exception as e:
            self._logger.error(f"Error obteniendo usuario actual: {e}")
            return None
    
    def has_permission(self, permission: str) -> bool:
        """
        Verificar permiso específico usuario actual.
        
        Implementación TDD para:
        - test_has_permission_admin_success
        - test_has_permission_no_user_fails
        """
        try:
            # Obtener usuario actual
            current_user = self.get_current_user()
            
            # Sin usuario no hay permisos (test_has_permission_no_user_fails)
            if not current_user:
                return False
            
            # Validar permisos según rol
            if permission == 'admin':
                # Administrador tiene todos los permisos (test_has_permission_admin_success)
                return current_user.rol.lower() == 'administrador'
            elif permission == 'vendedor':
                # Vendedor y admin tienen permisos vendedor
                return current_user.rol.lower() in ['vendedor', 'administrador']
            else:
                # Permiso no reconocido
                self._logger.warning(f"Permiso no reconocido: {permission}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error verificando permiso {permission}: {e}")
            return False
    
    def logout(self) -> None:
        """
        Cerrar sesión usuario actual.
        
        Implementación TDD para test_logout_success.
        """
        try:
            current_user = self.get_current_user()
            
            # Cerrar sesión en session_manager
            self._session_manager.logout()
            
            # Logging
            if current_user:
                self._logger.info(f"Logout exitoso: {current_user.username}")
            else:
                self._logger.info("Logout realizado (sin usuario activo)")
                
        except Exception as e:
            self._logger.error(f"Error durante logout: {e}")
            # No re-lanzar excepción para no bloquear logout
    
    def is_authenticated(self) -> bool:
        """
        Verificar si hay sesión activa.
        
        Implementación TDD para:
        - test_is_authenticated_true
        - test_is_authenticated_false
        
        CORRECCIÓN: SessionManager.is_authenticated es @property, no método.
        """
        try:
            return self._session_manager.is_authenticated
        except Exception as e:
            self._logger.error(f"Error verificando autenticación: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """
        Refrescar sesión activa.
        
        Implementación básica para compliance interface.
        """
        try:
            if not self.is_authenticated():
                return False
                
            # Refrescar timestamp sesión
            current_user = self.get_current_user()
            if current_user:
                self._session_manager.refresh_session()
                self._logger.debug(f"Sesión refrescada: {current_user.username}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error refrescando sesión: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtener información sesión actual.
        
        Implementación básica para compliance interface.
        """
        try:
            current_user = self.get_current_user()
            
            if not current_user:
                return {
                    'authenticated': False,
                    'user': None,
                    'session_time': None,
                    'permissions': []
                }
            
            return {
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'rol': current_user.rol
                },
                'session_time': datetime.now().isoformat(),
                'permissions': self._get_user_permissions(current_user)
            }
            
        except Exception as e:
            self._logger.error(f"Error obteniendo info sesión: {e}")
            return {'authenticated': False, 'error': str(e)}
    
    def _get_user_permissions(self, user: Usuario) -> list:
        """
        Obtener lista permisos usuario.
        
        Método privado para gestión permisos.
        """
        permissions = []
        
        if user.rol.lower() == 'administrador':
            permissions = ['admin', 'vendedor', 'reportes', 'configuracion']
        elif user.rol.lower() == 'vendedor':
            permissions = ['vendedor', 'reportes']
        
        return permissions


# Factory function para ServiceContainer
def create_auth_service(user_repository, session_manager, password_hasher):
    """
    Factory function para crear AuthService con dependencias.
    
    Usado por ServiceContainer para inyección de dependencias.
    """
    return AuthService(user_repository, session_manager, password_hasher)
