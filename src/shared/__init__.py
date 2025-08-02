# src/shared/__init__.py
"""
Módulo compartido del Sistema de Inventario
Contiene excepciones y utilidades comunes
"""

from .exceptions import (
    # Excepciones base
    InventorySystemException,
    ValidationException,
    BusinessRuleException,
    InfrastructureException,
    DatabaseException,
    SecurityException,
    
    # Excepciones de respaldos
    BackupException,
    ConfigurationException,
    BackupCreationException,
    BackupValidationException,
    SchedulerException,
    InsufficientSpaceException,
    
    # Excepciones de productos
    ProductNotFoundException,
    InsufficientStockException,
    DuplicateProductException,
    
    # Excepciones de seguridad
    AuthenticationException,
    AuthorizationException,
    SessionExpiredException,
    
    # Excepciones de exportación
    ExportException,
    ReportGenerationException,
    
    # Excepciones de UI
    UIException,
    FormValidationException,
    WidgetException,
    
    # Utilidades
    format_exception_message,
    is_user_recoverable_error,
    get_exception_category
)

__all__ = [
    # Excepciones base
    'InventorySystemException',
    'ValidationException',
    'BusinessRuleException',
    'InfrastructureException',
    'DatabaseException',
    'SecurityException',
    
    # Excepciones de respaldos
    'BackupException',
    'ConfigurationException',
    'BackupCreationException',
    'BackupValidationException',
    'SchedulerException',
    'InsufficientSpaceException',
    
    # Excepciones de productos
    'ProductNotFoundException',
    'InsufficientStockException',
    'DuplicateProductException',
    
    # Excepciones de seguridad
    'AuthenticationException',
    'AuthorizationException',
    'SessionExpiredException',
    
    # Excepciones de exportación
    'ExportException',
    'ReportGenerationException',
    
    # Excepciones de UI
    'UIException',
    'FormValidationException',
    'WidgetException',
    
    # Utilidades
    'format_exception_message',
    'is_user_recoverable_error',
    'get_exception_category'
]

__version__ = '1.0.0'
