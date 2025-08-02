"""
Servicio de gestión de usuarios - OPTIMIZADO FASE 4A.

PATRÓN FASE 3 IMPLEMENTADO:
- DatabaseHelper para operaciones de BD seguras y optimizadas
- ValidationHelper para validaciones robustas
- LoggingHelper para logging estructurado y auditoría

MEJORAS DE SEGURIDAD:
- Validación avanzada de contraseñas
- Logging de intentos de autenticación
- Protección contra enumeración de usuarios
- Validaciones robustas con helpers

COMPATIBILIDAD:
- 100% compatible con LoginWindow existente
- Todos los métodos originales mantenidos
- Comportamiento idéntico en interfaces públicas

Fecha optimización: 02/07/2025
Versión: FASE 4A
"""

import hashlib
import re
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from db.database import DatabaseConnection
from helpers.database_helper import DatabaseHelper
from helpers.validation_helper import ValidationHelper  
from helpers.logging_helper import LoggingHelper
from models.usuario import Usuario


class UserService:
    """Servicio para gestión de usuarios - OPTIMIZADO FASE 4A."""
    
    def __init__(self, db_connection: DatabaseConnection, password_hasher):
        """
        Inicializa el servicio de usuarios con patrón FASE 3.
        
        Args:
            db_connection: Conexión a la base de datos
        """
        # Patrón FASE 3: Inyección de helpers optimizados
        self.password_hasher = password_hasher
        self.db_connection = db_connection
        self.db_helper = DatabaseHelper(db_connection)
        self.validator = ValidationHelper()
        self.logger = LoggingHelper.get_service_logger('user_service')
        
        # Configuración de seguridad
        self._salt = "inventory_system_salt_2024"
        self._timing_delay = 0.001  # Delay mínimo para prevenir timing attacks
        
        self.logger.info("UserService inicializado con patrón FASE 3")
        
    def authenticate(self, username: str, password: str) -> Optional[Usuario]:
        """
        Autentica un usuario con sus credenciales.
        
        OPTIMIZACIÓN FASE 4A:
        - Usa DatabaseHelper para consultas seguras
        - Logging automático de intentos de autenticación
        - Protección contra timing attacks
        - Validaciones robustas
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario autenticado si las credenciales son válidas, None en caso contrario
        """
        start_time = time.time()
        
        try:
            # Validar entrada con ValidationHelper
            if not username or not password:
                self.logger.warning(f"Intento de autenticación con datos vacíos")
                LoggingHelper.log_authentication_attempt(username or "EMPTY", False)
                return None
                
            # Sanitizar entrada
            username = self.validator.sanitize_string(username, 30)
            
            if not self.validator.validate_username(username):
                self.logger.warning(f"Intento de autenticación con username inválido: {username}")
                LoggingHelper.log_authentication_attempt(username, False)
                return None
                
            # Hash de la contraseña para comparación
            password_hash = self.password_hasher.hash_password(password)
            
            # Buscar usuario usando DatabaseHelper - CONSULTA OPTIMIZADA
            query = """
                SELECT id_usuario, nombre_usuario, password_hash, rol, activo
                FROM usuarios 
                WHERE nombre_usuario = ? AND activo = 1
            """
            
            user_data = self.db_helper.safe_execute(query, (username,), 'one')
            
            # Protección contra timing attacks
            authentication_success = False
            user_object = None
            
            if user_data and self.password_hasher.verify_password(password, user_data['password_hash']):

                # Crear objeto Usuario con los datos encontrados
                user_object = Usuario(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    password_hash=user_data['password_hash'],
                    rol=user_data['rol'],
                    activo=bool(user_data['activo'])
                )
                authentication_success = True
                
                self.logger.info(f"Autenticación exitosa para usuario: {username}")
                LoggingHelper.log_user_action(
                    user_data['id_usuario'], 
                    'LOGIN_SUCCESS',
                    {'username': username, 'role': user_data['rol']}
                )
            else:
                self.logger.warning(f"Autenticación fallida para usuario: {username}")
                
            # Logging de intento de autenticación
            LoggingHelper.log_authentication_attempt(username, authentication_success)
            
            # Asegurar tiempo mínimo para prevenir timing attacks
            elapsed_time = time.time() - start_time
            if elapsed_time < self._timing_delay:
                time.sleep(self._timing_delay - elapsed_time)
                
            return user_object if authentication_success else None
            
        except Exception as e:
            self.logger.error(f"Error durante autenticación de {username}: {e}")
            LoggingHelper.log_authentication_attempt(username, False)
            return None
        
    def create_user(self, nombre_usuario: str, password: str, rol: str) -> Usuario:
        """
        Crea un nuevo usuario en el sistema.
        
        OPTIMIZACIÓN FASE 4A:
        - Validaciones robustas con ValidationHelper
        - Logging automático de operaciones
        - Manejo seguro de contraseñas
        - Transacciones optimizadas
        
        Args:
            nombre_usuario: Nombre único del usuario
            password: Contraseña en texto plano
            rol: Rol del usuario ('ADMIN' o 'VENDEDOR')
            
        Returns:
            Usuario creado exitosamente
            
        Raises:
            ValueError: Si los datos son inválidos o el usuario ya existe
        """
        try:
            # Validaciones robustas con ValidationHelper
            if not self.validator.validate_username(nombre_usuario):
                raise ValueError("Nombre de usuario inválido. Debe tener 3-30 caracteres alfanuméricos")
                
            if not self.validator.validate_role(rol):
                raise ValueError("Rol debe ser 'ADMIN' o 'VENDEDOR'")
                
            # Validación avanzada de contraseña
            password_validation = self.validator.validate_password_strength(password)
            if not password_validation['is_valid']:
                errors = '; '.join(password_validation['errors'])
                raise ValueError(f"Contraseña no cumple criterios de seguridad: {errors}")
                
            # Verificar que el usuario no exista usando DatabaseHelper
            if self._user_exists_by_username(nombre_usuario):
                raise ValueError(f"Usuario '{nombre_usuario}' ya existe")
                
            # Hash seguro de la contraseña
            password_hash = self.password_hasher.hash_password(password)

            
            # Insertar nuevo usuario con DatabaseHelper
            query = """
                INSERT INTO usuarios (nombre_usuario, password_hash, rol, activo)
                VALUES (?, ?, ?, 1)
            """
            
            user_id = self.db_helper.safe_execute_with_commit(
                query, 
                (nombre_usuario, password_hash, rol)
            )
            
            if not user_id:
                raise ValueError("Error al crear usuario en base de datos")
                
            # Crear objeto Usuario para retorno
            new_user = Usuario(
                id_usuario=user_id,
                nombre_usuario=nombre_usuario,
                password_hash=password_hash,
                rol=rol,
                activo=True
            )
            
            # Logging de operación exitosa
            self.logger.info(f"Usuario creado exitosamente: {nombre_usuario} (ID: {user_id})")
            LoggingHelper.log_database_operation(
                'usuarios', 
                'INSERT', 
                user_id,
                {'username': nombre_usuario, 'role': rol}
            )
            
            return new_user
            
        except Exception as e:
            self.logger.error(f"Error creando usuario {nombre_usuario}: {e}")
            raise
        
    def get_user_by_id(self, user_id: int) -> Optional[Usuario]:
        """
        Busca un usuario por su ID.
        
        OPTIMIZACIÓN FASE 4A:
        - Usa DatabaseHelper para consulta optimizada
        - Logging de acceso a datos
        - Manejo robusto de errores
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            Usuario encontrado o None si no existe
        """
        try:
            query = """
                SELECT id_usuario, nombre_usuario, password_hash, rol, activo
                FROM usuarios 
                WHERE id_usuario = ?
            """
            
            user_data = self.db_helper.safe_execute(query, (user_id,), 'one')
            
            if user_data:
                self.logger.debug(f"Usuario encontrado por ID: {user_id}")
                return Usuario(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    password_hash=user_data['password_hash'],
                    rol=user_data['rol'],
                    activo=bool(user_data['activo'])
                )
            else:
                self.logger.debug(f"Usuario no encontrado por ID: {user_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error buscando usuario por ID {user_id}: {e}")
            return None
        
    def update_user(self, id_usuario: int, nombre_usuario: str = None, 
                   rol: str = None) -> Optional[Usuario]:
        """
        Actualiza información de un usuario existente.
        
        OPTIMIZACIÓN FASE 4A:
        - Validaciones con ValidationHelper
        - Transacciones seguras con DatabaseHelper
        - Logging detallado de cambios
        
        Args:
            id_usuario: ID del usuario a actualizar
            nombre_usuario: Nuevo nombre de usuario (opcional)
            rol: Nuevo rol (opcional)
            
        Returns:
            Usuario actualizado o None si no existe
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        try:
            # Verificar que el usuario existe
            existing_user = self.get_user_by_id(id_usuario)
            if not existing_user:
                return None
                
            # Preparar campos a actualizar con validaciones
            updates = []
            params = []
            changes = {}
            
            if nombre_usuario is not None:
                if not self.validator.validate_username(nombre_usuario):
                    raise ValueError("Nombre de usuario inválido")
                    
                # Verificar duplicados
                if self._user_exists_by_username(nombre_usuario, exclude_id=id_usuario):
                    raise ValueError(f"Ya existe otro usuario con el nombre '{nombre_usuario}'")
                    
                updates.append("nombre_usuario = ?")
                params.append(nombre_usuario)
                changes['username'] = {'old': existing_user.nombre_usuario, 'new': nombre_usuario}
                
            if rol is not None:
                if not self.validator.validate_role(rol):
                    raise ValueError("Rol debe ser 'ADMIN' o 'VENDEDOR'")
                updates.append("rol = ?")
                params.append(rol)
                changes['role'] = {'old': existing_user.rol, 'new': rol}
                
            if not updates:
                return existing_user  # No hay cambios
                
            # Ejecutar actualización con DatabaseHelper
            params.append(id_usuario)
            query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id_usuario = ?"
            
            rows_affected = self.db_helper.safe_execute_with_commit(query, tuple(params))
            
            if rows_affected:
                # Logging de cambios
                self.logger.info(f"Usuario {id_usuario} actualizado: {changes}")
                LoggingHelper.log_database_operation(
                    'usuarios',
                    'UPDATE', 
                    id_usuario,
                    {'changes': changes}
                )
                
                # Retornar usuario actualizado
                return self.get_user_by_id(id_usuario)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error actualizando usuario {id_usuario}: {e}")
            raise
        
    def change_password(self, user_id: int, old_password: str, 
                       new_password: str) -> bool:
        """
        Cambia la contraseña de un usuario.
        
        OPTIMIZACIÓN FASE 4A:
        - Validación robusta de contraseña actual
        - Validación de fortaleza de nueva contraseña
        - Logging de cambios de contraseña
        - Protección contra timing attacks
        
        Args:
            user_id: ID del usuario
            old_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            True si el cambio fue exitoso, False en caso contrario
        """
        start_time = time.time()
        
        try:
            # Verificar usuario existente
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            # Verificar contraseña actual
            password_correct = self.password_hasher.verify_password(old_password, user.password_hash)

            # Validar nueva contraseña independientemente del resultado anterior
            password_validation = self.validator.validate_password_strength(new_password)
            new_password_valid = password_validation['is_valid']

            # Continuar procesamiento para evitar timing attacks
            new_password_hash = self.password_hasher.hash_password(new_password) if new_password_valid else None

            success = False

            if password_correct and new_password_valid:
                # Actualizar contraseña
                query = "UPDATE usuarios SET password_hash = ? WHERE id_usuario = ?"
                rows_affected = self.db_helper.safe_execute_with_commit(
                    query, 
                    (new_password_hash, user_id)
                )
                
                success = bool(rows_affected)
                
                if success:
                    self.logger.info(f"Contraseña cambiada exitosamente para usuario ID: {user_id}")
                    LoggingHelper.log_user_action(
                        user_id,
                        'PASSWORD_CHANGE_SUCCESS',
                        {'username': user.nombre_usuario}
                    )
                    
            if not success:
                self.logger.warning(f"Intento fallido de cambio de contraseña para usuario ID: {user_id}")
                LoggingHelper.log_user_action(
                    user_id,
                    'PASSWORD_CHANGE_FAILED',
                    {'username': user.nombre_usuario, 'reason': 'invalid_credentials_or_weak_password'}
                )
                
            # Asegurar tiempo mínimo para prevenir timing attacks
            elapsed_time = time.time() - start_time
            if elapsed_time < self._timing_delay:
                time.sleep(self._timing_delay - elapsed_time)
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error cambiando contraseña para usuario {user_id}: {e}")
            return False
        
    def deactivate_user(self, user_id: int) -> bool:
        """
        Desactiva un usuario del sistema.
        
        OPTIMIZACIÓN FASE 4A:
        - Logging de desactivación
        - Validación de existencia
        
        Args:
            user_id: ID del usuario a desactivar
            
        Returns:
            True si la desactivación fue exitosa, False en caso contrario
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
                
            query = "UPDATE usuarios SET activo = 0 WHERE id_usuario = ?"
            rows_affected = self.db_helper.safe_execute_with_commit(query, (user_id,))
            
            success = bool(rows_affected)
            
            if success:
                self.logger.info(f"Usuario desactivado: {user.nombre_usuario} (ID: {user_id})")
                LoggingHelper.log_database_operation(
                    'usuarios',
                    'UPDATE',
                    user_id,
                    {'action': 'deactivate', 'username': user.nombre_usuario}
                )
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error desactivando usuario {user_id}: {e}")
            return False
        
    def get_all_users(self) -> List[Usuario]:
        """
        Obtiene todos los usuarios del sistema.
        
        OPTIMIZACIÓN FASE 4A:
        - Usa DatabaseHelper para consulta optimizada
        - Manejo robusto de múltiples resultados
        
        Returns:
            Lista de usuarios
        """
        try:
            query = """
                SELECT id_usuario, nombre_usuario, password_hash, rol, activo
                FROM usuarios 
                ORDER BY nombre_usuario
            """
            
            users_data = self.db_helper.safe_execute(query, fetch_mode='all')
            
            if not users_data:
                return []
                
            users = []
            for user_data in users_data:
                users.append(Usuario(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    password_hash=user_data['password_hash'],
                    rol=user_data['rol'],
                    activo=bool(user_data['activo'])
                ))
            
            self.logger.debug(f"Obtenidos {len(users)} usuarios del sistema")
            return users
            
        except Exception as e:
            self.logger.error(f"Error obteniendo lista de usuarios: {e}")
            return []
            
    # NUEVOS MÉTODOS OPTIMIZADOS - FASE 4A
    
    def get_users_by_role(self, role: str) -> List[Usuario]:
        """
        Obtiene usuarios filtrados por rol.
        
        NUEVO MÉTODO FASE 4A:
        - Consulta optimizada por rol
        - Validación de rol
        
        Args:
            role: Rol a filtrar ('ADMIN' o 'VENDEDOR')
            
        Returns:
            Lista de usuarios del rol especificado
        """
        try:
            if not self.validator.validate_role(role):
                raise ValueError(f"Rol inválido: {role}")
                
            query = """
                SELECT id_usuario, nombre_usuario, password_hash, rol, activo
                FROM usuarios 
                WHERE rol = ? AND activo = 1
                ORDER BY nombre_usuario
            """
            
            users_data = self.db_helper.safe_execute(query, (role,), 'all')
            
            if not users_data:
                return []
                
            users = []
            for user_data in users_data:
                users.append(Usuario(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    password_hash=user_data['password_hash'],
                    rol=user_data['rol'],
                    activo=bool(user_data['activo'])
                ))
            
            self.logger.debug(f"Obtenidos {len(users)} usuarios con rol {role}")
            return users
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios por rol {role}: {e}")
            return []
            
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de usuarios del sistema.
        
        NUEVO MÉTODO FASE 4A:
        - Estadísticas agregadas optimizadas
        - Información útil para administración
        
        Returns:
            Diccionario con estadísticas de usuarios
        """
        try:
            stats = {}
            
            # Total de usuarios
            total_query = "SELECT COUNT(*) as count FROM usuarios"
            total_result = self.db_helper.safe_execute(total_query, fetch_mode='all')
            stats['total_users'] = total_result[0]['count'] if total_result else 0
            
            # Usuarios activos
            active_query = "SELECT COUNT(*) as count FROM usuarios WHERE activo = 1"
            active_result = self.db_helper.safe_execute(active_query, fetch_mode='all')
            stats['active_users'] = active_result[0]['count'] if active_result else 0
            
            # Usuarios por rol
            admin_query = "SELECT COUNT(*) as count FROM usuarios WHERE rol = 'ADMIN' AND activo = 1"
            admin_result = self.db_helper.safe_execute(admin_query, fetch_mode='all')
            stats['admin_count'] = admin_result[0]['count'] if admin_result else 0
            
            vendor_query = "SELECT COUNT(*) as count FROM usuarios WHERE rol = 'VENDEDOR' AND activo = 1"
            vendor_result = self.db_helper.safe_execute(vendor_query, fetch_mode='all')
            stats['vendor_count'] = vendor_result[0]['count'] if vendor_result else 0
            
            # Usuarios inactivos
            stats['inactive_users'] = stats['total_users'] - stats['active_users']
            
            # Fecha de generación
            stats['generated_at'] = datetime.now().isoformat()
            
            self.logger.debug(f"Estadísticas de usuarios generadas: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generando estadísticas de usuarios: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'admin_count': 0,
                'vendor_count': 0,
                'inactive_users': 0,
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    # MÉTODOS PRIVADOS OPTIMIZADOS
    
    def _user_exists_by_username(self, username: str, exclude_id: int = None) -> bool:
        """
        Verificar si existe un usuario por nombre de usuario.
        
        OPTIMIZACIÓN FASE 4A:
        - Usa DatabaseHelper para consulta optimizada
        - Soporte para exclusión de ID (útil en updates)
        
        Args:
            username: Nombre de usuario a verificar
            exclude_id: ID a excluir de la búsqueda (opcional)
            
        Returns:
            True si el usuario existe
        """
        try:
            query = "SELECT COUNT(*) as count FROM usuarios WHERE LOWER(nombre_usuario) = LOWER(?)"
            params = [username]
            
            if exclude_id:
                query += " AND id_usuario != ?"
                params.append(exclude_id)
                
            result = self.db_helper.safe_execute(query, tuple(params), 'one')
            
            if result:
                return result['count'] > 0
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error verificando existencia de usuario {username}: {e}")
            return False
        
    # def _hash_password(self, password: str) -> str:
        """
        Genera hash seguro de contraseña.
        
        OPTIMIZACIÓN FASE 4A:
        - Consistente con implementación original
        - Logging de uso para auditoría
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
    #    try:
    #        return hashlib.sha256((password + self._salt).encode()).hexdigest()
    #    except Exception as e:
    #        self.logger.error(f"Error generando hash de contraseña: {e}")
    #        raise ValueError("Error procesando contraseña")
    
    def get_by_username(self, username: str) -> Optional[Usuario]:
        """
        Buscar usuario por nombre de usuario (aunque esté inactivo).
        
        Returns:
            Usuario si existe, None si no
        """
        try:
            query = """
                SELECT id_usuario, nombre_usuario, password_hash, rol, activo
                FROM usuarios 
                WHERE LOWER(nombre_usuario) = LOWER(?)
                LIMIT 1
            """
            user_data = self.db_helper.safe_execute(query, (username,), 'one')
            
            if user_data:
                return Usuario(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    password_hash=user_data['password_hash'],
                    rol=user_data['rol'],
                    activo=bool(user_data['activo'])
                )
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error en get_by_username({username}): {e}")
            return None


    def _validate_username(self, username: str) -> bool:
        """
        Valida formato de nombre de usuario.
        
        DEPRECATED: Usar self.validator.validate_username() en su lugar.
        Mantenido solo para compatibilidad.
        """
        return self.validator.validate_username(username)
        
    def _validate_password(self, password: str) -> bool:
        """
        Valida fortaleza de contraseña.
        
        DEPRECATED: Usar self.validator.validate_password_strength() en su lugar.
        Mantenido solo para compatibilidad.
        """
        return len(password) >= 6 if password else False
        
    def _validate_role(self, role: str) -> bool:
        """
        Valida que el rol sea válido.
        
        DEPRECATED: Usar self.validator.validate_role() en su lugar.
        Mantenido solo para compatibilidad.
        """
        return self.validator.validate_role(role)
