# src/services/backup_integration.py
"""
Integración del sistema de respaldos con ServiceContainer
"""
import logging
from pathlib import Path
from typing import Optional

from src.infrastructure.backup import (
    BackupConfig, BackupService, BackupScheduler
)
from src.services.service_container import ServiceContainer


class BackupIntegrationService:
    """
    Servicio de integración para el sistema de respaldos.
    
    Integra el sistema de respaldos con la arquitectura existente
    del sistema de inventario.
    """
    
    def __init__(self, container: ServiceContainer):
        """
        Inicializar servicio de integración.
        
        Args:
            container: Contenedor de servicios del sistema
        """
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Configuración por defecto
        self._backup_config: Optional[BackupConfig] = None
        self._backup_service: Optional[BackupService] = None
        self._backup_scheduler: Optional[BackupScheduler] = None
    
    def initialize_backup_system(
        self,
        database_path: Optional[str] = None,
        backup_directory: Optional[str] = None,
        auto_start_scheduler: bool = True
    ) -> BackupService:
        """
        Inicializar sistema de respaldos con configuración.
        
        Args:
            database_path: Ruta de la base de datos (None para usar default)
            backup_directory: Directorio de respaldos (None para usar default)
            auto_start_scheduler: Si iniciar automáticamente el scheduler
            
        Returns:
            BackupService: Servicio de respaldos configurado
        """
        try:
            # Crear configuración
            config_params = {}
            
            if database_path:
                config_params['source_db_path'] = Path(database_path)
            else:
                # Usar ruta por defecto del sistema
                config_params['source_db_path'] = Path("inventario.db")
            
            if backup_directory:
                config_params['backup_directory'] = Path(backup_directory)
            else:
                config_params['backup_directory'] = Path("backups")
            
            # Configuración específica para Copy Point S.A.
            config_params.update({
                'retention_days': 90,  # 3 meses
                'auto_backup_enabled': True,
                'auto_backup_interval_days': 15,  # Cada 15 días
                'compression_enabled': True,
                'encryption_enabled': False,  # Por ahora sin encriptación
                'max_backup_size_mb': 500,
                'notification_enabled': True
            })
            
            self._backup_config = BackupConfig(**config_params)
            
            # Crear servicio de respaldos
            self._backup_service = BackupService(self._backup_config)
            
            # Registrar en el container
            self.container.register_singleton(
                'backup_service',
                lambda: self._backup_service
            )
            
            # Crear y configurar scheduler
            self._backup_scheduler = BackupScheduler(
                backup_service=self._backup_service,
                schedule_interval_days=15,
                check_interval_hours=6  # Verificar cada 6 horas
            )
            
            self.container.register_singleton(
                'backup_scheduler',
                lambda: self._backup_scheduler
            )
            
            # Iniciar scheduler si se solicita
            if auto_start_scheduler:
                self._backup_scheduler.start()
                self.logger.info("Backup scheduler iniciado automáticamente")
            
            self.logger.info(
                f"Sistema de respaldos inicializado: "
                f"DB={self._backup_config.source_db_path}, "
                f"Backup_Dir={self._backup_config.backup_directory}"
            )
            
            return self._backup_service
            
        except Exception as e:
            self.logger.error(f"Error inicializando sistema de respaldos: {e}")
            raise
    
    def create_manual_backup(self, description: str = "Manual backup") -> dict:
        """
        Crear respaldo manual con descripción.
        
        Args:
            description: Descripción del respaldo
            
        Returns:
            dict: Resultado del respaldo
        """
        if not self._backup_service:
            raise RuntimeError("Sistema de respaldos no inicializado")
        
        # Obtener usuario actual del sistema de autenticación
        try:
            auth_service = self.container.get('auth_service')
            current_user = auth_service.get_current_user()
            created_by = current_user.username if current_user else "system"
        except:
            created_by = "system"
        
        result = self._backup_service.create_manual_backup(
            description=description,
            created_by=created_by
        )
        
        return result.to_dict()
    
    def get_backup_status(self) -> dict:
        """
        Obtener estado completo del sistema de respaldos.
        
        Returns:
            dict: Estado del sistema de respaldos
        """
        if not self._backup_service:
            return {"initialized": False, "error": "Sistema no inicializado"}
        
        try:
            # Información del servicio
            service_info = {
                "initialized": True,
                "config": self._backup_config.to_dict() if self._backup_config else {},
                "statistics": self._backup_service.get_backup_statistics().to_dict(),
                "schedule_info": self._backup_service.get_schedule_info().to_dict()
            }
            
            # Información del scheduler
            if self._backup_scheduler:
                service_info["scheduler"] = self._backup_scheduler.get_scheduler_status()
            
            # Lista de respaldos recientes (últimos 10)
            recent_backups = self._backup_service.list_available_backups()[:10]
            service_info["recent_backups"] = [backup.to_dict() for backup in recent_backups]
            
            return service_info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de respaldos: {e}")
            return {
                "initialized": True, 
                "error": f"Error obteniendo estado: {str(e)}"
            }
    
    def cleanup_old_backups(self) -> dict:
        """
        Ejecutar limpieza de respaldos antiguos.
        
        Returns:
            dict: Resultado de la limpieza
        """
        if not self._backup_service:
            raise RuntimeError("Sistema de respaldos no inicializado")
        
        try:
            deleted_count = self._backup_service.cleanup_old_backups()
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Se eliminaron {deleted_count} respaldos antiguos"
            }
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de respaldos: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error ejecutando limpieza de respaldos"
            }
    
    def force_backup_now(self, description: str = "Forced backup") -> dict:
        """
        Forzar creación inmediata de respaldo.
        
        Args:
            description: Descripción del respaldo forzado
            
        Returns:
            dict: Resultado del respaldo forzado
        """
        if not self._backup_scheduler:
            # Si no hay scheduler, crear respaldo manual
            return self.create_manual_backup(f"Forced: {description}")
        
        result = self._backup_scheduler.force_backup_now(description)
        return result.to_dict()
    
    def stop_backup_system(self) -> None:
        """Detener sistema de respaldos (especialmente el scheduler)."""
        if self._backup_scheduler and self._backup_scheduler.is_running:
            self._backup_scheduler.stop()
            self.logger.info("Backup scheduler detenido")
    
    def restart_backup_scheduler(self) -> None:
        """Reiniciar el scheduler de respaldos."""
        if self._backup_scheduler:
            if self._backup_scheduler.is_running:
                self._backup_scheduler.stop()
            
            self._backup_scheduler.start()
            self.logger.info("Backup scheduler reiniciado")


def setup_backup_system(container: ServiceContainer) -> BackupIntegrationService:
    """
    Configurar sistema de respaldos en el ServiceContainer.
    
    Args:
        container: Contenedor de servicios
        
    Returns:
        BackupIntegrationService: Servicio de integración configurado
    """
    # Crear servicio de integración
    backup_integration = BackupIntegrationService(container)
    
    # Registrar en container
    container.register_singleton(
        'backup_integration',
        lambda: backup_integration
    )
    
    # Inicializar sistema de respaldos
    backup_integration.initialize_backup_system()
    
    return backup_integration
