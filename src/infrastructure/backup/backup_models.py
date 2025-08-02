# src/infrastructure/backup/backup_models.py
"""
Modelos de datos para el sistema de respaldos
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import os


@dataclass
class BackupResult:
    """
    Resultado de una operación de respaldo.
    
    Attributes:
        success: Si la operación fue exitosa
        backup_path: Ruta del archivo de respaldo creado
        size_bytes: Tamaño del respaldo en bytes
        created_at: Timestamp de creación
        backup_type: Tipo de respaldo ('manual', 'automatic')
        description: Descripción del respaldo
        created_by: Usuario que creó el respaldo
        error_message: Mensaje de error si falló
        duration_seconds: Tiempo que tomó crear el respaldo
    """
    
    success: bool
    backup_path: Optional[Path] = None
    size_bytes: int = 0
    created_at: Optional[datetime] = None
    backup_type: str = "manual"
    description: str = ""
    created_by: str = "system"
    error_message: str = ""
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        """Inicializar valores por defecto después de creación."""
        if self.created_at is None:
            self.created_at = datetime.now()
        
        if self.success and self.backup_path and self.backup_path.exists():
            # Calcular tamaño si el archivo existe y el tamaño no se especificó
            if self.size_bytes == 0:
                self.size_bytes = self.backup_path.stat().st_size
    
    @property
    def size_mb(self) -> float:
        """Tamaño del respaldo en megabytes."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def is_valid(self) -> bool:
        """Verificar si el resultado representa un respaldo válido."""
        return (
            self.success and 
            self.backup_path is not None and 
            self.backup_path.exists() and
            self.size_bytes > 0
        )
    
    def to_dict(self) -> dict:
        """Convertir resultado a diccionario."""
        return {
            'success': self.success,
            'backup_path': str(self.backup_path) if self.backup_path else None,
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_mb, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'backup_type': self.backup_type,
            'description': self.description,
            'created_by': self.created_by,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
            'is_valid': self.is_valid
        }


@dataclass
class BackupInfo:
    """
    Información detallada de un respaldo existente.
    
    Attributes:
        backup_path: Ruta del archivo de respaldo
        size_bytes: Tamaño del archivo en bytes
        created_at: Fecha de creación
        backup_type: Tipo de respaldo
        description: Descripción del respaldo
        created_by: Usuario que creó el respaldo
        is_valid: Si el respaldo es válido/íntegro
        checksum: Checksum del archivo para verificación
    """
    
    backup_path: Path
    size_bytes: int = 0
    created_at: Optional[datetime] = None
    backup_type: str = "unknown"
    description: str = ""
    created_by: str = "system"
    is_valid: bool = False
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Inicializar información del archivo después de creación."""
        if self.backup_path.exists():
            stat = self.backup_path.stat()
            
            if self.size_bytes == 0:
                self.size_bytes = stat.st_size
            
            if self.created_at is None:
                self.created_at = datetime.fromtimestamp(stat.st_mtime)
            
            # Inferir tipo de respaldo del nombre del archivo
            if self.backup_type == "unknown":
                self.backup_type = self._infer_backup_type()
    
    def _infer_backup_type(self) -> str:
        """Inferir tipo de respaldo del nombre del archivo."""
        filename = self.backup_path.name.lower()
        
        if "auto" in filename:
            return "automatic"
        elif "manual" in filename:
            return "manual"
        else:
            return "unknown"
    
    @property
    def size_mb(self) -> float:
        """Tamaño del respaldo en megabytes."""
        return self.size_bytes / (1024 * 1024)
    
    @property
    def filename(self) -> str:
        """Nombre del archivo de respaldo."""
        return self.backup_path.name
    
    @property
    def age_days(self) -> int:
        """Edad del respaldo en días."""
        if self.created_at:
            return (datetime.now() - self.created_at).days
        return 0
    
    def to_dict(self) -> dict:
        """Convertir información a diccionario."""
        return {
            'backup_path': str(self.backup_path),
            'filename': self.filename,
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_mb, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'backup_type': self.backup_type,
            'description': self.description,
            'created_by': self.created_by,
            'is_valid': self.is_valid,
            'age_days': self.age_days,
            'checksum': self.checksum
        }


@dataclass
class BackupScheduleInfo:
    """
    Información sobre la programación de respaldos automáticos.
    
    Attributes:
        is_enabled: Si los respaldos automáticos están habilitados
        interval_days: Intervalo en días entre respaldos
        last_backup_date: Fecha del último respaldo automático
        next_backup_date: Fecha estimada del próximo respaldo
        backups_created_count: Número total de respaldos creados
        last_backup_success: Si el último respaldo fue exitoso
    """
    
    is_enabled: bool = True
    interval_days: int = 15
    last_backup_date: Optional[datetime] = None
    next_backup_date: Optional[datetime] = None
    backups_created_count: int = 0
    last_backup_success: bool = True
    
    @property
    def days_since_last_backup(self) -> Optional[int]:
        """Días desde el último respaldo."""
        if self.last_backup_date:
            return (datetime.now() - self.last_backup_date).days
        return None
    
    @property
    def is_backup_due(self) -> bool:
        """Si es momento de crear un respaldo automático."""
        if not self.is_enabled:
            return False
        
        if self.last_backup_date is None:
            return True
        
        return self.days_since_last_backup >= self.interval_days
    
    def to_dict(self) -> dict:
        """Convertir información a diccionario."""
        return {
            'is_enabled': self.is_enabled,
            'interval_days': self.interval_days,
            'last_backup_date': self.last_backup_date.isoformat() if self.last_backup_date else None,
            'next_backup_date': self.next_backup_date.isoformat() if self.next_backup_date else None,
            'backups_created_count': self.backups_created_count,
            'last_backup_success': self.last_backup_success,
            'days_since_last_backup': self.days_since_last_backup,
            'is_backup_due': self.is_backup_due
        }


class BackupStatistics:
    """
    Estadísticas del sistema de respaldos.
    """
    
    def __init__(self, backup_infos: List[BackupInfo]):
        """
        Inicializar estadísticas con lista de respaldos.
        
        Args:
            backup_infos: Lista de información de respaldos
        """
        self.backup_infos = backup_infos
    
    @property
    def total_backups(self) -> int:
        """Número total de respaldos."""
        return len(self.backup_infos)
    
    @property
    def total_size_bytes(self) -> int:
        """Tamaño total de todos los respaldos en bytes."""
        return sum(backup.size_bytes for backup in self.backup_infos)
    
    @property
    def total_size_mb(self) -> float:
        """Tamaño total de todos los respaldos en megabytes."""
        return self.total_size_bytes / (1024 * 1024)
    
    @property
    def automatic_backups_count(self) -> int:
        """Número de respaldos automáticos."""
        return len([b for b in self.backup_infos if b.backup_type == "automatic"])
    
    @property
    def manual_backups_count(self) -> int:
        """Número de respaldos manuales."""
        return len([b for b in self.backup_infos if b.backup_type == "manual"])
    
    @property
    def valid_backups_count(self) -> int:
        """Número de respaldos válidos."""
        return len([b for b in self.backup_infos if b.is_valid])
    
    @property
    def oldest_backup(self) -> Optional[BackupInfo]:
        """Respaldo más antiguo."""
        if not self.backup_infos:
            return None
        
        return min(
            self.backup_infos, 
            key=lambda b: b.created_at or datetime.min
        )
    
    @property
    def newest_backup(self) -> Optional[BackupInfo]:
        """Respaldo más reciente."""
        if not self.backup_infos:
            return None
        
        return max(
            self.backup_infos, 
            key=lambda b: b.created_at or datetime.min
        )
    
    @property
    def average_backup_size_mb(self) -> float:
        """Tamaño promedio de respaldos en megabytes."""
        if not self.backup_infos:
            return 0.0
        
        return self.total_size_mb / len(self.backup_infos)
    
    def to_dict(self) -> dict:
        """Convertir estadísticas a diccionario."""
        return {
            'total_backups': self.total_backups,
            'total_size_bytes': self.total_size_bytes,
            'total_size_mb': round(self.total_size_mb, 2),
            'automatic_backups_count': self.automatic_backups_count,
            'manual_backups_count': self.manual_backups_count,
            'valid_backups_count': self.valid_backups_count,
            'average_backup_size_mb': round(self.average_backup_size_mb, 2),
            'oldest_backup': self.oldest_backup.to_dict() if self.oldest_backup else None,
            'newest_backup': self.newest_backup.to_dict() if self.newest_backup else None
        }
