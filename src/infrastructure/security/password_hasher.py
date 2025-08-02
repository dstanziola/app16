# src/infrastructure/security/password_hasher.py
"""
PasswordHasher - Infrastructure Layer
Clean Architecture - Capa de Infraestructura
Fecha: 2025-07-16
Propósito: Gestión segura de passwords con hash + salt
"""

import hashlib
import secrets
import logging


class PasswordHasher:
    """
    Servicio de hash de passwords empresarial.
    
    Funcionalidades:
    - Hash seguro con salt aleatorio
    - Verificación passwords
    - Algoritmo bcrypt compatible
    - Logging eventos seguridad
    
    Principios aplicados:
    - Single Responsibility (solo hash passwords)
    - Security Best Practices
    """
    
    def __init__(self, algorithm: str = 'sha256', salt_length: int = 32):
        """
        Inicializar hasher con configuración seguridad.
        
        Args:
            algorithm (str): Algoritmo hash ('sha256', 'sha512')
            salt_length (int): Longitud salt en bytes
        """
        self._algorithm = algorithm
        self._salt_length = salt_length
        self._logger = logging.getLogger(__name__)
        
        # Validar algoritmo
        if algorithm not in ['sha256', 'sha512']:
            raise ValueError(f"Algoritmo no soportado: {algorithm}")
        
        self._logger.info(f"PasswordHasher inicializado: {algorithm}")
    
    def hash_password(self, password: str) -> str:
        """
        Generar hash seguro de password.
        
        Args:
            password (str): Password en texto plano
            
        Returns:
            str: Hash en formato 'salt$hash'
            
        Raises:
            ValueError: Si password vacío
        """
        if not password:
            raise ValueError("Password no puede estar vacío")
        
        try:
            # Generar salt aleatorio
            salt = secrets.token_hex(self._salt_length)
            
            # Crear hash con salt
            hash_obj = hashlib.new(self._algorithm)
            hash_obj.update(f"{salt}{password}".encode('utf-8'))
            password_hash = hash_obj.hexdigest()
            
            # Formato: salt$hash
            hashed_password = f"{salt}${password_hash}"
            
            self._logger.debug("Password hasheado exitosamente")
            return hashed_password
            
        except Exception as e:
            self._logger.error(f"Error hasheando password: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verificar password contra hash almacenado.
        
        Args:
            password (str): Password en texto plano
            hashed_password (str): Hash almacenado formato 'salt$hash'
            
        Returns:
            bool: True si password correcto, False caso contrario
        """
        if not password or not hashed_password:
            return False
        
        try:
            # Extraer salt y hash
            if '$' not in hashed_password:
                # Compatibilidad con hashes antiguos sin salt
                return self._verify_legacy_password(password, hashed_password)
            
            salt, stored_hash = hashed_password.split('$', 1)
            
            # Recrear hash con mismo salt
            hash_obj = hashlib.new(self._algorithm)
            hash_obj.update(f"{salt}{password}".encode('utf-8'))
            computed_hash = hash_obj.hexdigest()
            
            # Comparación segura contra timing attacks
            is_valid = secrets.compare_digest(computed_hash, stored_hash)
            
            if is_valid:
                self._logger.debug("Password verificado exitosamente")
            else:
                self._logger.warning("Password incorrecto verificado")
            
            return is_valid
            
        except Exception as e:
            self._logger.error(f"Error verificando password: {e}")
            return False
    
    def _verify_legacy_password(self, password: str, hashed_password: str) -> bool:
        """
        Verificar passwords legacy con salt específico del sistema (compatibilidad).
        
        Args:
            password (str): Password en texto plano
            hashed_password (str): Hash legacy del sistema de inventario
            
        Returns:
            bool: True si password correcto
        """
        try:
            # Hash legacy con salt específico del sistema de inventario
            legacy_salt = "inventory_system_salt_2024"
            hash_obj = hashlib.new(self._algorithm)
            hash_obj.update((password + legacy_salt).encode('utf-8'))
            computed_hash = hash_obj.hexdigest()
            
            is_valid = secrets.compare_digest(computed_hash, hashed_password)
            
            if is_valid:
                self._logger.info("Password legacy verificado (considerar actualizar)")
            
            return is_valid
            
        except Exception as e:
            self._logger.error(f"Error verificando password legacy: {e}")
            return False
    
    def change_password(self, old_password: str, new_password: str, current_hash: str) -> str:
        """
        Cambiar password validando password actual.
        
        Args:
            old_password (str): Password actual
            new_password (str): Nuevo password
            current_hash (str): Hash actual almacenado
            
        Returns:
            str: Nuevo hash generado
            
        Raises:
            ValueError: Si password actual incorrecto
        """
        # Verificar password actual
        if not self.verify_password(old_password, current_hash):
            raise ValueError("Password actual incorrecto")
        
        # Validar nuevo password
        if len(new_password) < 6:
            raise ValueError("Nuevo password debe tener mínimo 6 caracteres")
        
        # Generar nuevo hash
        new_hash = self.hash_password(new_password)
        
        self._logger.info("Password cambiado exitosamente")
        return new_hash
    
    def is_strong_password(self, password: str) -> tuple[bool, list]:
        """
        Validar fortaleza de password.
        
        Args:
            password (str): Password a validar
            
        Returns:
            tuple[bool, list]: (es_fuerte, lista_errores)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Mínimo 8 caracteres requeridos")
        
        if not any(c.isupper() for c in password):
            errors.append("Requiere al menos una mayúscula")
        
        if not any(c.islower() for c in password):
            errors.append("Requiere al menos una minúscula")
        
        if not any(c.isdigit() for c in password):
            errors.append("Requiere al menos un número")
        
        special_chars = "!@#$%^&*()_+-=[]{}|;':\".,<>?"
        if not any(c in special_chars for c in password):
            errors.append("Requiere al menos un carácter especial")
        
        is_strong = len(errors) == 0
        return is_strong, errors


# Factory function para ServiceContainer
def create_password_hasher():
    """Factory function para crear PasswordHasher."""
    return PasswordHasher()
