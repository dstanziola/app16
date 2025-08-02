"""
LoggingHelper - Patrón FASE 3
Helper para logging estructurado y configuración centralizada.

RESPONSABILIDADES:
- Configuración centralizada de logging
- Loggers específicos por servicio
- Formateo estandarizado de mensajes
- Rotación automática de archivos de log
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json


class LoggingHelper:
    """Helper para configuración y manejo de logging."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls, log_level: str = 'INFO', 
                     log_dir: str = 'logs',
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5):
        """
        Configurar el sistema de logging globalmente.
        
        Args:
            log_level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR')
            log_dir: Directorio para archivos de log
            max_file_size: Tamaño máximo de archivo antes de rotación
            backup_count: Número de archivos de backup a mantener
        """
        if cls._configured:
            return
            
        # Crear directorio de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Formato para logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'inventory_system.log'),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)  # Solo warnings y errores en consola
        
        # Agregar handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        cls._configured = True
        
        # Log inicial
        cls.get_system_logger().info("Sistema de logging configurado exitosamente")
        
    @classmethod
    def get_service_logger(cls, service_name: str) -> logging.Logger:
        """
        Obtener logger específico para un servicio.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Logger configurado para el servicio
        """
        if not cls._configured:
            cls.setup_logging()
            
        logger_name = f"inventory.services.{service_name}"
        
        if logger_name not in cls._loggers:
            logger = logging.getLogger(logger_name)
            cls._loggers[logger_name] = logger
            
        return cls._loggers[logger_name]
        
    @classmethod
    def get_ui_logger(cls, form_name: str) -> logging.Logger:
        """
        Obtener logger específico para formularios UI.
        
        Args:
            form_name: Nombre del formulario
            
        Returns:
            Logger configurado para UI
        """
        if not cls._configured:
            cls.setup_logging()
            
        logger_name = f"inventory.ui.{form_name}"
        
        if logger_name not in cls._loggers:
            logger = logging.getLogger(logger_name)
            cls._loggers[logger_name] = logger
            
        return cls._loggers[logger_name]
        
    @classmethod
    def get_system_logger(cls) -> logging.Logger:
        """
        Obtener logger para eventos del sistema.
        
        Returns:
            Logger del sistema
        """
        if not cls._configured:
            cls.setup_logging()
            
        logger_name = "inventory.system"
        
        if logger_name not in cls._loggers:
            logger = logging.getLogger(logger_name)
            cls._loggers[logger_name] = logger
            
        return cls._loggers[logger_name]
        
    @classmethod
    def log_user_action(cls, user_id: int, action: str, details: Dict[str, Any] = None):
        """
        Registrar acción de usuario para auditoría.
        
        Args:
            user_id: ID del usuario
            action: Acción realizada
            details: Detalles adicionales de la acción
        """
        logger = cls.get_system_logger()
        
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"USER_ACTION: {json.dumps(log_data, ensure_ascii=False)}")
        
    @classmethod
    def log_authentication_attempt(cls, username: str, success: bool, 
                                  ip_address: str = None):
        """
        Registrar intento de autenticación.
        
        Args:
            username: Nombre de usuario
            success: Si el intento fue exitoso
            ip_address: Dirección IP del intento
        """
        logger = cls.get_system_logger()
        
        log_data = {
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        }
        
        level = 'INFO' if success else 'WARNING'
        message = f"AUTH_ATTEMPT: {json.dumps(log_data, ensure_ascii=False)}"
        
        if success:
            logger.info(message)
        else:
            logger.warning(message)
            
    @classmethod
    def log_database_operation(cls, table: str, operation: str, 
                              record_id: Optional[int] = None,
                              details: Dict[str, Any] = None):
        """
        Registrar operación de base de datos.
        
        Args:
            table: Tabla afectada
            operation: Tipo de operación (INSERT, UPDATE, DELETE)
            record_id: ID del registro afectado
            details: Detalles adicionales
        """
        logger = cls.get_system_logger()
        
        log_data = {
            'table': table,
            'operation': operation,
            'record_id': record_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"DB_OPERATION: {json.dumps(log_data, ensure_ascii=False)}")
        
    @classmethod
    def log_error_with_context(cls, logger: logging.Logger, error: Exception,
                              context: Dict[str, Any] = None):
        """
        Registrar error con contexto adicional.
        
        Args:
            logger: Logger a usar
            error: Excepción capturada
            context: Contexto adicional del error
        """
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        logger.error(f"ERROR_WITH_CONTEXT: {json.dumps(error_data, ensure_ascii=False)}")
        
    @classmethod
    def log_performance_metrics(cls, operation: str, duration: float,
                               details: Dict[str, Any] = None):
        """
        Registrar métricas de performance.
        
        Args:
            operation: Operación medida
            duration: Duración en segundos
            details: Detalles adicionales
        """
        logger = cls.get_system_logger()
        
        metrics_data = {
            'operation': operation,
            'duration_seconds': round(duration, 4),
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        # Log como WARNING si la operación toma más de 1 segundo
        if duration > 1.0:
            logger.warning(f"SLOW_OPERATION: {json.dumps(metrics_data, ensure_ascii=False)}")
        else:
            logger.debug(f"PERFORMANCE: {json.dumps(metrics_data, ensure_ascii=False)}")
            
    @classmethod
    def log_business_rule_violation(cls, rule: str, details: Dict[str, Any] = None):
        """
        Registrar violación de regla de negocio.
        
        Args:
            rule: Regla violada
            details: Detalles de la violación
        """
        logger = cls.get_system_logger()
        
        violation_data = {
            'rule': rule,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        logger.warning(f"BUSINESS_RULE_VIOLATION: {json.dumps(violation_data, ensure_ascii=False)}")
        
    @classmethod
    def configure_for_production(cls):
        """Configurar logging optimizado para producción."""
        cls.setup_logging(
            log_level='INFO',
            log_dir='logs',
            max_file_size=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )
        
    @classmethod
    def configure_for_development(cls):
        """Configurar logging detallado para desarrollo."""
        cls.setup_logging(
            log_level='DEBUG',
            log_dir='logs',
            max_file_size=10 * 1024 * 1024,  # 10MB
            backup_count=3
        )
        
    @classmethod
    def get_log_statistics(cls) -> Dict[str, Any]:
        """
        Obtener estadísticas de logging.
        
        Returns:
            Dict con estadísticas
        """
        stats = {
            'configured': cls._configured,
            'active_loggers': len(cls._loggers),
            'logger_names': list(cls._loggers.keys()),
            'timestamp': datetime.now().isoformat()
        }
        
        return stats


class LoggingContext:
    """Context manager para logging con contexto adicional."""
    
    def __init__(self, logger: logging.Logger, operation: str, 
                 context: Dict[str, Any] = None):
        """
        Inicializar contexto de logging.
        
        Args:
            logger: Logger a usar
            operation: Nombre de la operación
            context: Contexto adicional
        """
        self.logger = logger
        self.operation = operation
        self.context = context or {}
        self.start_time = None
        
    def __enter__(self):
        """Entrar al contexto."""
        self.start_time = datetime.now()
        self.logger.debug(f"OPERATION_START: {self.operation} - Context: {self.context}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Salir del contexto."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Operación exitosa
            self.logger.debug(f"OPERATION_SUCCESS: {self.operation} - Duration: {duration:.4f}s")
            LoggingHelper.log_performance_metrics(self.operation, duration, self.context)
        else:
            # Operación con error
            LoggingHelper.log_error_with_context(
                self.logger, 
                exc_val, 
                {**self.context, 'operation': self.operation, 'duration': duration}
            )
