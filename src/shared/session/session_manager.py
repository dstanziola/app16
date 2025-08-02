# src/shared/session/session_manager.py
"""
SessionManager Mejorado - Shared Layer
Clean Architecture - Capa Compartida
Fecha: 2025-07-16
Propósito: Gestión avanzada de sesiones con seguridad empresarial
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models.usuario import Usuario


class SessionManager:
    """
    Gestor de sesión empresarial con características avanzadas.
    
    Funcionalidades:
    - Gestión segura de sesiones usuario
    - Timeout automático de sesiones
    - Validación permisos por rol
    - Logging eventos de seguridad
    - Thread safety
    - Refresh de sesiones
    
    Principios aplicados:
    - Single Responsibility (solo gestión sesiones)
    - Thread Safety (acceso concurrente seguro)
    - Security Best Practices
    """
    
    def __init__(self, session_timeout: int = 3600):
        """
        Inicializar SessionManager.
        
        Args:
            session_timeout (int): Timeout sesión en segundos (default: 1 hora)
        """
        self._current_user: Optional[Usuario] = None
        self._is_authenticated: bool = False
        self._session_start: Optional[datetime] = None
        self._last_activity: Optional[datetime] = None
        self._session_timeout = session_timeout
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        
        self._logger.info(f"SessionManager inicializado (timeout: {session_timeout}s)")
    
    def login(self, user: Usuario) -> None:
        """
        Establecer sesión para usuario autenticado.
        
        Args:
            user (Usuario): Usuario autenticado
            
        Efectos:
        - Establece sesión activa
        - Registra timestamps
        - Logging evento login
        """
        with self._lock:
            try:
                # Validar usuario
                if not user or not user.es_activo():
                    raise ValueError("Usuario inválido o inactivo")
                
                # Establecer sesión
                self._current_user = user
                self._is_authenticated = True
                now = datetime.now()
                self._session_start = now
                self._last_activity = now
                
                # Logging
                self._logger.info(f"Sesión iniciada: {user.username} ({user.rol})")
                
            except Exception as e:
                self._logger.error(f"Error iniciando sesión: {e}")
                raise
    
    def logout(self) -> None:
        """
        Cerrar sesión actual y limpiar datos.
        
        Efectos:
        - Limpia datos de sesión
        - Logging evento logout
        - Liberación recursos
        """
        with self._lock:
            try:
                if self._current_user:
                    username = self._current_user.username
                    session_duration = self._get_session_duration()
                    
                    # Limpiar sesión
                    self._current_user = None
                    self._is_authenticated = False
                    self._session_start = None
                    self._last_activity = None
                    
                    # Logging
                    self._logger.info(f"Sesión cerrada: {username} (duración: {session_duration}s)")
                else:
                    self._logger.info("Logout realizado (sin sesión activa)")
                    
            except Exception as e:
                self._logger.error(f"Error durante logout: {e}")
                # Forzar limpieza incluso con error
                self._clear_session()
    
    def get_current_user(self) -> Optional[Usuario]:
        """
        Obtener usuario actual autenticado.
        
        Returns:
            Optional[Usuario]: Usuario actual o None si no autenticado
            
        Nota: Verifica timeout automáticamente
        """
        with self._lock:
            # Verificar timeout automáticamente
            if self._is_session_expired():
                self._expire_session()
                return None
            
            # Actualizar actividad
            if self._is_authenticated and self._current_user:
                self._last_activity = datetime.now()
            
            return self._current_user
    
    def is_authenticated(self) -> bool:
        """
        Verificar si hay sesión activa válida.
        
        Returns:
            bool: True si hay sesión activa no expirada
        """
        with self._lock:
            # Verificar timeout
            if self._is_session_expired():
                self._expire_session()
                return False
            
            return self._is_authenticated and self._current_user is not None
    
    def has_permission(self, permission: str) -> bool:
        """
        Verificar permiso específico usuario actual.
        
        Args:
            permission (str): Permiso a verificar
            
        Returns:
            bool: True si tiene permiso
            
        Compatibilidad: Mantiene interfaz original + nuevas funcionalidades
        """
        with self._lock:
            try:
                # Verificar autenticación
                if not self.is_authenticated():
                    return False
                
                user = self.get_current_user()
                if not user:
                    return False
                
                # Mapeo de permisos según rol
                user_role = user.rol.upper()
                
                # Administrador tiene todos los permisos
                if user_role in ['ADMIN', 'ADMINISTRADOR']:
                    return True
                
                # Vendedor permisos específicos
                if user_role == 'VENDEDOR':
                    allowed_actions = [
                        'sales', 'view_products', 'view_clients', 
                        'view_categories', 'vendedor', 'reportes'
                    ]
                    return permission.lower() in [action.lower() for action in allowed_actions]
                
                # Permisos específicos por string
                if permission.lower() == 'admin':
                    return user_role in ['ADMIN', 'ADMINISTRADOR']
                elif permission.lower() == 'vendedor':
                    return user_role in ['VENDEDOR', 'ADMIN', 'ADMINISTRADOR']
                
                return False
                
            except Exception as e:
                self._logger.error(f"Error verificando permiso {permission}: {e}")
                return False
    
    def refresh_session(self) -> bool:
        """
        Refrescar sesión activa para evitar timeout.
        
        Returns:
            bool: True si sesión refrescada exitosamente
        """
        with self._lock:
            try:
                if not self._is_authenticated or not self._current_user:
                    return False
                
                # Verificar si no está expirada
                if self._is_session_expired():
                    self._expire_session()
                    return False
                
                # Refrescar actividad
                self._last_activity = datetime.now()
                
                self._logger.debug(f"Sesión refrescada: {self._current_user.username}")
                return True
                
            except Exception as e:
                self._logger.error(f"Error refrescando sesión: {e}")
                return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Obtener información completa de sesión.
        
        Returns:
            Dict[str, Any]: Información detallada de sesión
        """
        with self._lock:
            try:
                if not self.is_authenticated():
                    return {
                        'authenticated': False,
                        'user': None,
                        'session_start': None,
                        'last_activity': None,
                        'duration': 0,
                        'expires_in': 0
                    }
                
                user = self._current_user
                duration = self._get_session_duration()
                expires_in = self._get_time_until_expiry()
                
                return {
                    'authenticated': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'rol': user.rol,
                        'activo': user.activo
                    },
                    'session_start': self._session_start.isoformat() if self._session_start else None,
                    'last_activity': self._last_activity.isoformat() if self._last_activity else None,
                    'duration': duration,
                    'expires_in': expires_in,
                    'timeout': self._session_timeout
                }
                
            except Exception as e:
                self._logger.error(f"Error obteniendo info sesión: {e}")
                return {'authenticated': False, 'error': str(e)}
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Obtener información usuario actual (compatibilidad).
        
        Returns:
            Dict[str, Any]: Información usuario para UI
            
        Compatibilidad: Mantiene interfaz original
        """
        with self._lock:
            if not self.is_authenticated():
                return {
                    'nombre_usuario': 'No autenticado',
                    'rol': '',
                    'activo': False
                }
            
            user = self._current_user
            return {
                'nombre_usuario': user.username,
                'rol': user.rol,
                'activo': user.activo
            }
    
    def extend_session(self, additional_time: int = 3600) -> bool:
        """
        Extender tiempo de sesión.
        
        Args:
            additional_time (int): Tiempo adicional en segundos
            
        Returns:
            bool: True si sesión extendida
        """
        with self._lock:
            try:
                if not self.is_authenticated():
                    return False
                
                # Extender timeout
                self._session_timeout += additional_time
                self._last_activity = datetime.now()
                
                self._logger.info(f"Sesión extendida {additional_time}s: {self._current_user.username}")
                return True
                
            except Exception as e:
                self._logger.error(f"Error extendiendo sesión: {e}")
                return False
    
    # Propiedades para compatibilidad
    
    @property
    def current_user(self) -> Optional[Usuario]:
        """Propiedad current_user (compatibilidad)."""
        return self.get_current_user()
    
    # Métodos privados
    
    def _is_session_expired(self) -> bool:
        """
        Verificar si sesión ha expirado.
        
        Returns:
            bool: True si sesión expirada
        """
        if not self._is_authenticated or not self._last_activity:
            return True
        
        elapsed = (datetime.now() - self._last_activity).total_seconds()
        return elapsed > self._session_timeout
    
    def _expire_session(self) -> None:
        """
        Expirar sesión por timeout.
        """
        try:
            if self._current_user:
                username = self._current_user.username
                duration = self._get_session_duration()
                
                self._logger.warning(f"Sesión expirada por timeout: {username} (duración: {duration}s)")
            
            # Limpiar sesión
            self._clear_session()
            
        except Exception as e:
            self._logger.error(f"Error expirando sesión: {e}")
            self._clear_session()
    
    def _clear_session(self) -> None:
        """Limpiar datos de sesión forzadamente."""
        self._current_user = None
        self._is_authenticated = False
        self._session_start = None
        self._last_activity = None
    
    def _get_session_duration(self) -> int:
        """
        Obtener duración sesión en segundos.
        
        Returns:
            int: Duración en segundos
        """
        if not self._session_start:
            return 0
        
        return int((datetime.now() - self._session_start).total_seconds())
    
    def _get_time_until_expiry(self) -> int:
        """
        Obtener tiempo hasta expiración en segundos.
        
        Returns:
            int: Segundos hasta expiración
        """
        if not self._last_activity:
            return 0
        
        elapsed = (datetime.now() - self._last_activity).total_seconds()
        remaining = self._session_timeout - elapsed
        
        return max(0, int(remaining))


# Factory function para ServiceContainer
def create_session_manager(session_timeout: int = 3600):
    """
    Factory function para crear SessionManager.
    
    Args:
        session_timeout (int): Timeout en segundos
        
    Returns:
        SessionManager: Instancia configurada
    """
    return SessionManager(session_timeout)
