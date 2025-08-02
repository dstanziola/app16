# src/infrastructure/backup/__init__.py
"""
Sistema de Respaldos Automáticos para Copy Point S.A.

Funcionalidades:
- Respaldos automáticos cada 15 días
- Respaldos manuales a petición
- Compresión y validación de respaldos
- Limpieza automática de respaldos antiguos
- Programación automática con BackupScheduler
"""

from .backup_config import BackupConfig
from .backup_models import BackupResult, BackupInfo, BackupScheduleInfo, BackupStatistics
from .backup_service import BackupService
from .backup_scheduler import BackupScheduler, BackupSchedulerManager

__all__ = [
    'BackupConfig',
    'BackupResult', 
    'BackupInfo', 
    'BackupScheduleInfo', 
    'BackupStatistics',
    'BackupService',
    'BackupScheduler',
    'BackupSchedulerManager'
]

__version__ = '1.0.0'
