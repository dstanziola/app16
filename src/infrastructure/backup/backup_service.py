# src/infrastructure/backup/backup_service.py
"""
Servicio principal para el sistema de respaldos automáticos
Respaldos cada 15 días + a petición
"""
import logging
import shutil
import zipfile
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import sqlite3

from src.infrastructure.backup.backup_config import BackupConfig
from src.infrastructure.backup.backup_models import (
    BackupResult, BackupInfo, BackupScheduleInfo, BackupStatistics
)
from src.shared.exceptions import (
    BackupCreationException, BackupValidationException, 
    InsufficientSpaceException, ConfigurationException
)


class BackupService:
    """
    Servicio principal para gestión de respaldos del sistema.
    
    Funcionalidades:
    - Respaldos automáticos cada 15 días
    - Respaldos manuales a petición
    - Compresión y validación de respaldos
    - Limpieza automática de respaldos antiguos
    - Estadísticas y monitoreo
    """
    
    def __init__(self, config: BackupConfig):
        """
        Inicializar servicio de respaldos.
        
        Args:
            config: Configuración del sistema de respaldos
            
        Raises:
            ConfigurationException: Si la configuración es inválida
        """
        if config is None:
            raise ConfigurationException("BackupConfig no puede ser None")
        
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._metadata_file = self.config.backup_directory / "backup_metadata.json"
        self._metadata = self._load_metadata()
        
        # Verificar que el directorio de respaldos exista
        self.config.backup_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"BackupService inicializado: {self.config}")
    
    @property
    def is_initialized(self) -> bool:
        """Verificar si el servicio está inicializado correctamente."""
        return (
            self.config is not None and
            self.config.backup_directory.exists() and
            hasattr(self, 'logger')
        )
    
    def create_manual_backup(
        self, 
        description: str = "Manual backup", 
        created_by: str = "system"
    ) -> BackupResult:
        """
        Crear respaldo manual a petición.
        
        Args:
            description: Descripción del respaldo
            created_by: Usuario que solicita el respaldo
            
        Returns:
            BackupResult: Resultado de la operación
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Iniciando respaldo manual: {description}")
            
            # Verificar que la base de datos existe
            if not self.config.source_db_path.exists():
                return BackupResult(
                    success=False,
                    error_message="Database file not found",
                    duration_seconds=time.time() - start_time
                )
            
            # Verificar espacio en disco
            self._check_disk_space()
            
            # Generar nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"inventory_manual_{timestamp}.zip"
            backup_path = self.config.backup_directory / backup_filename
            
            # Crear respaldo
            self._create_backup_file(backup_path)
            
            # Crear resultado
            result = BackupResult(
                success=True,
                backup_path=backup_path,
                backup_type="manual",
                description=description,
                created_by=created_by,
                duration_seconds=time.time() - start_time
            )
            
            # Guardar metadata
            self._save_backup_metadata(result)
            
            self.logger.info(f"Respaldo manual completado: {backup_path} ({result.size_mb:.2f} MB)")
            return result
            
        except Exception as e:
            self.logger.error(f"Error creando respaldo manual: {e}")
            return BackupResult(
                success=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
    
    def create_automatic_backup(self) -> BackupResult:
        """
        Crear respaldo automático (programado cada 15 días).
        
        Returns:
            BackupResult: Resultado de la operación
        """
        result = self.create_manual_backup(
            description="Automatic backup (15-day schedule)",
            created_by="scheduler"
        )
        
        # Cambiar tipo a automático
        if result.success:
            return BackupResult(
                success=result.success,
                backup_path=result.backup_path,
                size_bytes=result.size_bytes,
                created_at=result.created_at,
                backup_type="automatic",  # Cambiar tipo
                description=result.description,
                created_by=result.created_by,
                error_message=result.error_message,
                duration_seconds=result.duration_seconds
            )
        
        return result
    
    def should_create_automatic_backup(self) -> bool:
        """
        Verificar si es necesario crear un respaldo automático.
        
        Returns:
            bool: True si es necesario crear respaldo
        """
        if not self.config.auto_backup_enabled:
            return False
        
        # Obtener fecha del último respaldo automático
        last_auto_backup = self._get_last_automatic_backup_date()
        
        if last_auto_backup is None:
            # No hay respaldos automáticos previos
            return True
        
        # Verificar si ha pasado suficiente tiempo
        time_since_last = datetime.now() - last_auto_backup
        return time_since_last.days >= self.config.auto_backup_interval_days
    
    def list_available_backups(self) -> List[BackupInfo]:
        """
        Listar todos los respaldos disponibles.
        
        Returns:
            List[BackupInfo]: Lista de respaldos ordenada por fecha (más reciente primero)
        """
        backups = []
        
        # Buscar archivos de respaldo en el directorio
        backup_files = list(self.config.backup_directory.glob("inventory_*.zip"))
        
        for backup_file in backup_files:
            try:
                backup_info = self.get_backup_info(backup_file)
                backups.append(backup_info)
            except Exception as e:
                self.logger.warning(f"Error leyendo información de respaldo {backup_file}: {e}")
        
        # Ordenar por fecha de creación (más reciente primero)
        backups.sort(key=lambda b: b.created_at or datetime.min, reverse=True)
        
        return backups
    
    def get_backup_info(self, backup_path: Path) -> BackupInfo:
        """
        Obtener información detallada de un respaldo.
        
        Args:
            backup_path: Ruta del archivo de respaldo
            
        Returns:
            BackupInfo: Información del respaldo
        """
        if not backup_path.exists():
            raise BackupValidationException(f"Backup file not found: {backup_path}")
        
        # Obtener metadata guardada si existe
        backup_metadata = self._get_backup_metadata(backup_path)
        
        backup_info = BackupInfo(
            backup_path=backup_path,
            description=backup_metadata.get("description", ""),
            created_by=backup_metadata.get("created_by", "system"),
            is_valid=self.validate_backup_integrity(backup_path)
        )
        
        return backup_info
    
    def validate_backup_integrity(self, backup_path: Path) -> bool:
        """
        Validar la integridad de un archivo de respaldo.
        
        Args:
            backup_path: Ruta del archivo de respaldo
            
        Returns:
            bool: True si el respaldo es válido
        """
        try:
            if not backup_path.exists():
                return False
            
            # Verificar que es un archivo ZIP válido
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                # Verificar integridad del ZIP
                bad_file = zip_file.testzip()
                if bad_file:
                    self.logger.error(f"Archivo corrupto en respaldo: {bad_file}")
                    return False
                
                # Verificar que contiene la base de datos
                expected_db_name = self.config.source_db_path.name
                if expected_db_name not in zip_file.namelist():
                    self.logger.error(f"Base de datos {expected_db_name} no encontrada en respaldo")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando integridad de respaldo {backup_path}: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Limpiar respaldos antiguos según política de retención.
        
        Returns:
            int: Número de respaldos eliminados
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        self.logger.info(f"Iniciando limpieza de respaldos anteriores a {cutoff_date}")
        
        backups = self.list_available_backups()
        
        for backup in backups:
            if backup.created_at and backup.created_at < cutoff_date:
                try:
                    backup.backup_path.unlink()
                    self._remove_backup_metadata(backup.backup_path)
                    deleted_count += 1
                    self.logger.info(f"Respaldo eliminado: {backup.backup_path}")
                except Exception as e:
                    self.logger.error(f"Error eliminando respaldo {backup.backup_path}: {e}")
        
        self.logger.info(f"Limpieza completada: {deleted_count} respaldos eliminados")
        return deleted_count
    
    def get_backup_statistics(self) -> BackupStatistics:
        """
        Obtener estadísticas del sistema de respaldos.
        
        Returns:
            BackupStatistics: Estadísticas de respaldos
        """
        backups = self.list_available_backups()
        return BackupStatistics(backups)
    
    def get_schedule_info(self) -> BackupScheduleInfo:
        """
        Obtener información sobre la programación de respaldos.
        
        Returns:
            BackupScheduleInfo: Información de programación
        """
        last_backup_date = self._get_last_automatic_backup_date()
        next_backup_date = None
        
        if last_backup_date:
            next_backup_date = last_backup_date + timedelta(days=self.config.auto_backup_interval_days)
        
        # Contar respaldos automáticos
        backups = self.list_available_backups()
        auto_backups_count = len([b for b in backups if b.backup_type == "automatic"])
        
        return BackupScheduleInfo(
            is_enabled=self.config.auto_backup_enabled,
            interval_days=self.config.auto_backup_interval_days,
            last_backup_date=last_backup_date,
            next_backup_date=next_backup_date,
            backups_created_count=auto_backups_count,
            last_backup_success=True  # TODO: Implementar tracking de fallos
        )
    
    def _create_backup_file(self, backup_path: Path) -> None:
        """
        Crear archivo de respaldo comprimido.
        
        Args:
            backup_path: Ruta donde crear el respaldo
            
        Raises:
            BackupCreationException: Si falla la creación
        """
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Agregar base de datos principal
                zip_file.write(
                    self.config.source_db_path, 
                    self.config.source_db_path.name
                )
                
                # Agregar metadatos de respaldo
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "source_db_path": str(self.config.source_db_path),
                    "backup_version": "1.0",
                    "system_info": {
                        "python_version": __import__("sys").version,
                        "platform": __import__("platform").platform()
                    }
                }
                
                zip_file.writestr(
                    "backup_metadata.json", 
                    json.dumps(metadata, indent=2)
                )
                
        except Exception as e:
            if backup_path.exists():
                backup_path.unlink()  # Limpiar archivo parcial
            raise BackupCreationException(f"Error creating backup: {e}", str(self.config.source_db_path))
    
    def _check_disk_space(self) -> None:
        """
        Verificar que hay suficiente espacio en disco.
        
        Raises:
            InsufficientSpaceException: Si no hay suficiente espacio
        """
        # Estimar tamaño necesario (tamaño DB + 20% buffer)
        source_size = self.config.source_db_path.stat().st_size
        required_space = int(source_size * 1.2)
        
        # Verificar espacio disponible
        statvfs = shutil.disk_usage(self.config.backup_directory)
        available_space = statvfs.free
        
        if available_space < required_space:
            raise InsufficientSpaceException(required_space, available_space)
    
    def _get_last_automatic_backup_date(self) -> Optional[datetime]:
        """
        Obtener fecha del último respaldo automático.
        
        Returns:
            Optional[datetime]: Fecha del último respaldo automático
        """
        backups = self.list_available_backups()
        auto_backups = [b for b in backups if b.backup_type == "automatic"]
        
        if auto_backups:
            # Los respaldos están ordenados por fecha (más reciente primero)
            return auto_backups[0].created_at
        
        return None
    
    def _load_metadata(self) -> Dict[str, Any]:
        """
        Cargar metadata de respaldos desde archivo.
        
        Returns:
            Dict[str, Any]: Metadata de respaldos
        """
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error cargando metadata de respaldos: {e}")
        
        return {"backups": {}}
    
    def _save_metadata(self) -> None:
        """Guardar metadata de respaldos a archivo."""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando metadata de respaldos: {e}")
    
    def _save_backup_metadata(self, backup_result: BackupResult) -> None:
        """
        Guardar metadata de un respaldo específico.
        
        Args:
            backup_result: Resultado del respaldo
        """
        if not backup_result.success or not backup_result.backup_path:
            return
        
        backup_key = backup_result.backup_path.name
        self._metadata["backups"][backup_key] = {
            "description": backup_result.description,
            "created_by": backup_result.created_by,
            "backup_type": backup_result.backup_type,
            "created_at": backup_result.created_at.isoformat(),
            "size_bytes": backup_result.size_bytes
        }
        
        self._save_metadata()
    
    def _get_backup_metadata(self, backup_path: Path) -> Dict[str, Any]:
        """
        Obtener metadata de un respaldo específico.
        
        Args:
            backup_path: Ruta del respaldo
            
        Returns:
            Dict[str, Any]: Metadata del respaldo
        """
        backup_key = backup_path.name
        return self._metadata.get("backups", {}).get(backup_key, {})
    
    def _remove_backup_metadata(self, backup_path: Path) -> None:
        """
        Remover metadata de un respaldo eliminado.
        
        Args:
            backup_path: Ruta del respaldo eliminado
        """
        backup_key = backup_path.name
        if backup_key in self._metadata.get("backups", {}):
            del self._metadata["backups"][backup_key]
            self._save_metadata()
