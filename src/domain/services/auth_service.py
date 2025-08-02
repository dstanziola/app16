# src/domain/services/auth_service.py
"""
Interface IAuthService - Domain Layer
Clean Architecture - Capa de Dominio
Fecha: 2025-07-16
Propósito: Interface abstracta para servicios de autenticación
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from models.usuario import Usuario


class IAuthService(ABC):
    """
    Interface para servicio de autenticación empresarial.
    
    Responsabilidades:
    - Definir contrato autenticación
    - Gestión sesiones usuario
    - Validación permisos
    - Eventos autenticación/logout
    
    Principios aplicados:
    - Interface Segregation (solo métodos necesarios)
    - Dependency Inversion (abstracción)
    - Single Responsibility (solo autenticación)
    """
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[Usuario]:
        """
        Autenticar usuario con credenciales.
        
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña en texto plano
            
        Returns:
            Optional[Usuario]: Usuario autenticado o None si falla
            
        Raises:
            ValidationError: Si credenciales inválidas
            AuthenticationError: Si error interno autenticación
        """
        pass
    
    @abstractmethod
    def get_current_user(self) -> Optional[Usuario]:
        """
        Obtener usuario actual autenticado.
        
        Returns:
            Optional[Usuario]: Usuario actual o None si no autenticado
        """
        pass
    
    @abstractmethod
    def has_permission(self, permission: str) -> bool:
        """
        Verificar si usuario actual tiene permiso específico.
        
        Args:
            permission (str): Permiso a verificar ('admin', 'vendedor', etc.)
            
        Returns:
            bool: True si tiene permiso, False caso contrario
        """
        pass
    
    @abstractmethod
    def logout(self) -> None:
        """
        Cerrar sesión usuario actual.
        
        Efectos:
        - Limpia sesión activa
        - Genera evento logout
        - Libera recursos
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Verificar si hay sesión activa.
        
        Returns:
            bool: True si hay usuario autenticado, False caso contrario
        """
        pass
    
    @abstractmethod
    def refresh_session(self) -> bool:
        """
        Refrescar sesión activa.
        
        Returns:
            bool: True si sesión refrescada, False si expiró
        """
        pass
    
    @abstractmethod
    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtener información sesión actual.
        
        Returns:
            Dict[str, Any]: Información sesión (tiempo, permisos, etc.)
        """
        pass


# Excepciones específicas del dominio
class AuthenticationError(Exception):
    """Error de autenticación del dominio."""
    pass


class ValidationError(Exception):
    """Error de validación de credenciales."""
    pass


class SessionExpiredError(Exception):
    """Error de sesión expirada."""
    pass
