# src/infrastructure/backup/backup_config.py
"""
Configuración del Sistema de Respaldos Automáticos
Respaldos cada 15 días + a petición
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
from src.shared.exceptions import ConfigurationException


@dataclass
class BackupConfig:
    """
    Configuración para el sistema de respaldos automáticos.
    
    Attributes:
        source_db_path: Ruta de la base de datos a respaldar
        backup_directory: Directorio donde guardar respaldos
        retention_days: Días para mantener respaldos antes de eliminar
        auto_backup_enabled: Si los respaldos automáticos están habilitados
        auto_backup_interval_days: Intervalo en días para respaldos automáticos
        compression_enabled: Si comprimir los respaldos
        encryption_enabled: Si encriptar los respaldos
        max_backup_size_mb: Tamaño máximo permitido para un respaldo en MB
        notification_enabled: Si enviar notificaciones de respaldos
    """
    
    source_db_path: Path = field(default_factory=lambda: Path("data/inventario.db"))
    backup_directory: Path = field(default_factory=lambda: Path("backups"))
    retention_days: int = 90
    auto_backup_enabled: bool = True
    auto_backup_interval_days: int = 15
    compression_enabled: bool = True
    encryption_enabled: bool = False
    max_backup_size_mb: int = 500
    notification_enabled: bool = True
    
    def __post_init__(self):
        """Validar configuración después de inicialización."""
        self._validate_configuration()
        self._ensure_paths_are_pathlib()
        self._create_backup_directory_if_needed()
    
    def _validate_configuration(self) -> None:
        """Validar que la configuración sea válida."""
        errors = []
        
        # Validar valores positivos
        if self.retention_days <= 0:
            errors.append("retention_days debe ser positivo")
        
        if self.auto_backup_interval_days <= 0:
            errors.append("auto_backup_interval_days debe ser positivo")
        
        if self.max_backup_size_mb <= 0:
            errors.append("max_backup_size_mb debe ser positivo")
        
        # Validar rutas
        if not self.source_db_path or str(self.source_db_path).strip() == "":
            errors.append("source_db_path no puede estar vacío")
        
        if not self.backup_directory or str(self.backup_directory).strip() == "":
            errors.append("backup_directory no puede estar vacío")
        
        # Validar rangos razonables
        if self.retention_days > 3650:  # 10 años
            errors.append("retention_days no puede exceder 3650 días")
        
        if self.auto_backup_interval_days > 365:  # 1 año
            errors.append("auto_backup_interval_days no puede exceder 365 días")
        
        if errors:
            raise ConfigurationException(
                f"Configuración de respaldos inválida: {'; '.join(errors)}",
                invalid_fields=errors
            )
    
    def _ensure_paths_are_pathlib(self) -> None:
        """Asegurar que las rutas sean objetos Path."""
        if isinstance(self.source_db_path, str):
            self.source_db_path = Path(self.source_db_path)
        
        if isinstance(self.backup_directory, str):
            self.backup_directory = Path(self.backup_directory)
    
    def _create_backup_directory_if_needed(self) -> None:
        """Crear directorio de respaldos si no existe."""
        self.backup_directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BackupConfig':
        """
        Crear configuración desde diccionario.
        
        Args:
            config_dict: Diccionario con configuración
            
        Returns:
            BackupConfig: Instancia configurada
        """
        # Convertir rutas de string a Path si es necesario
        if 'source_db_path' in config_dict:
            config_dict['source_db_path'] = Path(config_dict['source_db_path'])
        
        if 'backup_directory' in config_dict:
            config_dict['backup_directory'] = Path(config_dict['backup_directory'])
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Exportar configuración a diccionario.
        
        Returns:
            Dict[str, Any]: Configuración como diccionario
        """
        return {
            'source_db_path': str(self.source_db_path),
            'backup_directory': str(self.backup_directory),
            'retention_days': self.retention_days,
            'auto_backup_enabled': self.auto_backup_enabled,
            'auto_backup_interval_days': self.auto_backup_interval_days,
            'compression_enabled': self.compression_enabled,
            'encryption_enabled': self.encryption_enabled,
            'max_backup_size_mb': self.max_backup_size_mb,
            'notification_enabled': self.notification_enabled
        }
    
    def get_backup_filename_pattern(self, backup_type: str) -> str:
        """
        Obtener patrón de nombre para archivos de respaldo.
        
        Args:
            backup_type: Tipo de respaldo ('auto', 'manual')
            
        Returns:
            str: Patrón de nombre
        """
        if backup_type == "automatic":
            return "inventory_auto_{timestamp}.zip"
        elif backup_type == "manual":
            return "inventory_manual_{timestamp}.zip"
        else:
            return "inventory_{backup_type}_{timestamp}.zip"
    
    def is_backup_due(self, last_backup_date: Optional[Any] = None) -> bool:
        """
        Verificar si es necesario crear un respaldo automático.
        
        Args:
            last_backup_date: Fecha del último respaldo automático
            
        Returns:
            bool: True si es necesario crear respaldo
        """
        if not self.auto_backup_enabled:
            return False
        
        if last_backup_date is None:
            return True
        
        from datetime import datetime, timedelta
        
        if isinstance(last_backup_date, str):
            # Convertir string a datetime si es necesario
            try:
                last_backup_date = datetime.fromisoformat(last_backup_date)
            except ValueError:
                return True  # Si no se puede parsear, crear respaldo
        
        time_since_last = datetime.now() - last_backup_date
        return time_since_last.days >= self.auto_backup_interval_days
    
    def get_max_backup_size_bytes(self) -> int:
        """
        Obtener tamaño máximo de respaldo en bytes.
        
        Returns:
            int: Tamaño máximo en bytes
        """
        return self.max_backup_size_mb * 1024 * 1024
    
    def validate_backup_size(self, backup_size_bytes: int) -> bool:
        """
        Validar que el tamaño del respaldo esté dentro del límite.
        
        Args:
            backup_size_bytes: Tamaño del respaldo en bytes
            
        Returns:
            bool: True si el tamaño es válido
        """
        max_size = self.get_max_backup_size_bytes()
        return backup_size_bytes <= max_size
    
    def __str__(self) -> str:
        """Representación string de la configuración."""
        return (
            f"BackupConfig("
            f"source_db='{self.source_db_path}', "
            f"backup_dir='{self.backup_directory}', "
            f"retention={self.retention_days}d, "
            f"interval={self.auto_backup_interval_days}d, "
            f"auto_enabled={self.auto_backup_enabled})"
        )
