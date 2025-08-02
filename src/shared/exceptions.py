# src/shared/exceptions.py
"""
Excepciones del Sistema de Inventario Copy Point S.A.
Incluye excepciones base del sistema y específicas para respaldos
"""
from typing import List, Optional


# Excepciones base del sistema
class InventorySystemException(Exception):
    """Excepción base del sistema de inventario."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ValidationException(InventorySystemException):
    """Excepción para errores de validación."""
    
    def __init__(self, message: str, invalid_fields: Optional[List[str]] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.invalid_fields = invalid_fields or []


class BusinessRuleException(InventorySystemException):
    """Excepción para violaciones de reglas de negocio."""
    
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_ERROR")


class InfrastructureException(InventorySystemException):
    """Excepción para errores de infraestructura."""
    
    def __init__(self, message: str):
        super().__init__(message, "INFRASTRUCTURE_ERROR")


class DatabaseException(InfrastructureException):
    """Excepción para errores de base de datos."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.error_code = "DATABASE_ERROR"


class SecurityException(InventorySystemException):
    """Excepción para violaciones de seguridad."""
    
    def __init__(self, message: str):
        super().__init__(message, "SECURITY_ERROR")


# Excepciones específicas del sistema de respaldos
class BackupException(InventorySystemException):
    """Excepción base para errores de respaldo."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message, error_code or "BACKUP_ERROR")


class ConfigurationException(BackupException):
    """Excepción para errores de configuración de respaldos."""
    
    def __init__(self, message: str, invalid_fields: Optional[List[str]] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.invalid_fields = invalid_fields or []


class BackupCreationException(BackupException):
    """Excepción para errores durante creación de respaldos."""
    
    def __init__(self, message: str, source_path: Optional[str] = None):
        super().__init__(message, "BACKUP_CREATION_ERROR")
        self.source_path = source_path


class BackupValidationException(BackupException):
    """Excepción para errores de validación de respaldos."""
    
    def __init__(self, message: str, backup_path: Optional[str] = None):
        super().__init__(message, "BACKUP_VALIDATION_ERROR")
        self.backup_path = backup_path


class SchedulerException(BackupException):
    """Excepción para errores del programador de respaldos."""
    
    def __init__(self, message: str):
        super().__init__(message, "SCHEDULER_ERROR")


class InsufficientSpaceException(BackupException):
    """Excepción para errores de espacio insuficiente en disco."""
    
    def __init__(self, required_space: int, available_space: int):
        message = f"Espacio insuficiente: requerido {required_space} bytes, disponible {available_space} bytes"
        super().__init__(message, "INSUFFICIENT_SPACE")
        self.required_space = required_space
        self.available_space = available_space


# Excepciones de productos y movimientos
class ProductNotFoundException(BusinessRuleException):
    """Producto no encontrado."""
    
    def __init__(self, product_id: int):
        super().__init__(f"Producto con ID {product_id} no encontrado")
        self.product_id = product_id


class InsufficientStockException(BusinessRuleException):
    """Stock insuficiente para operación."""
    
    def __init__(self, product_code: str, requested: int, available: int):
        super().__init__(
            f"Stock insuficiente para {product_code}. "
            f"Solicitado: {requested}, Disponible: {available}"
        )
        self.product_code = product_code
        self.requested_quantity = requested
        self.available_quantity = available


class DuplicateProductException(BusinessRuleException):
    """Producto duplicado en el sistema."""
    
    def __init__(self, product_code: str):
        super().__init__(f"Ya existe un producto con código '{product_code}'")
        self.product_code = product_code


# Excepciones de autenticación y autorización
class AuthenticationException(SecurityException):
    """Error de autenticación."""
    
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message)


class AuthorizationException(SecurityException):
    """Error de autorización."""
    
    def __init__(self, message: str = "No tiene permisos para esta operación"):
        super().__init__(message)


class SessionExpiredException(SecurityException):
    """Sesión expirada."""
    
    def __init__(self, message: str = "La sesión ha expirado"):
        super().__init__(message)


# Excepciones de exportación y reportes
class ExportException(InfrastructureException):
    """Error en exportación de datos."""
    
    def __init__(self, message: str, export_format: Optional[str] = None):
        super().__init__(message)
        self.export_format = export_format


class ReportGenerationException(InfrastructureException):
    """Error en generación de reportes."""
    
    def __init__(self, message: str, report_type: Optional[str] = None):
        super().__init__(message)
        self.report_type = report_type


# Excepciones de UI y formularios
class UIException(InventorySystemException):
    """Excepción para errores de interfaz de usuario."""
    
    def __init__(self, message: str):
        super().__init__(message, "UI_ERROR")


class FormValidationException(UIException):
    """Error de validación en formularios."""
    
    def __init__(self, message: str, form_name: Optional[str] = None):
        super().__init__(message)
        self.form_name = form_name


class WidgetException(UIException):
    """Error en widgets de UI."""
    
    def __init__(self, message: str, widget_name: Optional[str] = None):
        super().__init__(message)
        self.widget_name = widget_name


# Utilidades para manejo de excepciones
def format_exception_message(exception: Exception) -> str:
    """
    Formatear mensaje de excepción para mostrar al usuario.
    
    Args:
        exception: Excepción a formatear
        
    Returns:
        str: Mensaje formateado
    """
    if isinstance(exception, InventorySystemException):
        if exception.error_code:
            return f"[{exception.error_code}] {exception.message}"
        return exception.message
    
    return str(exception)


def is_user_recoverable_error(exception: Exception) -> bool:
    """
    Determinar si un error es recuperable por el usuario.
    
    Args:
        exception: Excepción a evaluar
        
    Returns:
        bool: True si el usuario puede recuperarse del error
    """
    recoverable_types = (
        ValidationException,
        BusinessRuleException,
        FormValidationException,
        DuplicateProductException,
        InsufficientStockException
    )
    
    return isinstance(exception, recoverable_types)


def get_exception_category(exception: Exception) -> str:
    """
    Obtener categoría de la excepción para logging y análisis.
    
    Args:
        exception: Excepción a categorizar
        
    Returns:
        str: Categoría de la excepción
    """
    if isinstance(exception, SecurityException):
        return "SECURITY"
    elif isinstance(exception, BusinessRuleException):
        return "BUSINESS"
    elif isinstance(exception, ValidationException):
        return "VALIDATION"
    elif isinstance(exception, BackupException):
        return "BACKUP"
    elif isinstance(exception, DatabaseException):
        return "DATABASE"
    elif isinstance(exception, InfrastructureException):
        return "INFRASTRUCTURE"
    elif isinstance(exception, UIException):
        return "UI"
    else:
        return "UNKNOWN"
