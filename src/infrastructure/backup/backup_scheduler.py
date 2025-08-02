# src/infrastructure/backup/backup_scheduler.py
"""
Planificador para respaldos automáticos cada 15 días
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from src.infrastructure.backup.backup_service import BackupService
from src.infrastructure.backup.backup_models import BackupResult
from src.shared.exceptions import SchedulerException


class BackupScheduler:
    """
    Planificador para respaldos automáticos del sistema.
    
    Ejecuta en background y crea respaldos automáticos según la programación
    configurada (por defecto cada 15 días).
    """
    
    def __init__(
        self, 
        backup_service: BackupService, 
        schedule_interval_days: int = 15,
        check_interval_hours: int = 1
    ):
        """
        Inicializar planificador de respaldos.
        
        Args:
            backup_service: Servicio de respaldos a utilizar
            schedule_interval_days: Intervalo en días entre respaldos automáticos
            check_interval_hours: Intervalo en horas para verificar si es necesario respaldo
        """
        self.backup_service = backup_service
        self.schedule_interval_days = schedule_interval_days
        self.check_interval_hours = check_interval_hours
        self.check_interval_seconds = check_interval_hours * 3600
        
        self.logger = logging.getLogger(__name__)
        
        # Estado del scheduler
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Estadísticas
        self.last_check_time: Optional[datetime] = None
        self.last_backup_time: Optional[datetime] = None
        self.checks_performed = 0
        self.backups_created = 0
        
        self.logger.info(
            f"BackupScheduler inicializado: intervalo {schedule_interval_days} días, "
            f"verificación cada {check_interval_hours} horas"
        )
    
    def start(self) -> None:
        """
        Iniciar el planificador en background.
        
        Raises:
            SchedulerException: Si el scheduler ya está ejecutándose
        """
        if self.is_running:
            raise SchedulerException("Scheduler ya está ejecutándose")
        
        self.logger.info("Iniciando BackupScheduler...")
        
        self.is_running = True
        self._stop_event.clear()
        
        # Crear y iniciar hilo del scheduler
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="BackupScheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("BackupScheduler iniciado exitosamente")
    
    def stop(self) -> None:
        """
        Detener el planificador graciosamente.
        """
        if not self.is_running:
            return
        
        self.logger.info("Deteniendo BackupScheduler...")
        
        self.is_running = False
        self._stop_event.set()
        
        # Esperar a que termine el hilo del scheduler
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
            
            if self.scheduler_thread.is_alive():
                self.logger.warning("Scheduler thread no terminó en tiempo esperado")
        
        self.logger.info("BackupScheduler detenido")
    
    def check_and_create_backup(self) -> Optional[BackupResult]:
        """
        Verificar si es necesario crear un respaldo automático y crearlo.
        
        Returns:
            Optional[BackupResult]: Resultado del respaldo si se creó uno
        """
        self.last_check_time = datetime.now()
        self.checks_performed += 1
        
        try:
            # Verificar si es necesario crear respaldo
            if self.backup_service.should_create_automatic_backup():
                self.logger.info("Es necesario crear respaldo automático")
                
                # Crear respaldo automático
                result = self.backup_service.create_automatic_backup()
                
                if result.success:
                    self.last_backup_time = datetime.now()
                    self.backups_created += 1
                    
                    self.logger.info(
                        f"Respaldo automático creado exitosamente: "
                        f"{result.backup_path} ({result.size_mb:.2f} MB)"
                    )
                else:
                    self.logger.error(
                        f"Error creando respaldo automático: {result.error_message}"
                    )
                
                return result
            else:
                self.logger.debug("No es necesario crear respaldo automático en este momento")
                return None
                
        except Exception as e:
            self.logger.error(f"Error en verificación de respaldo automático: {e}")
            return None
    
    def force_backup_now(self, description: str = "Forced backup") -> BackupResult:
        """
        Forzar creación inmediata de respaldo manual.
        
        Args:
            description: Descripción del respaldo forzado
            
        Returns:
            BackupResult: Resultado del respaldo
        """
        self.logger.info(f"Forzando respaldo inmediato: {description}")
        
        result = self.backup_service.create_manual_backup(
            description=description,
            created_by="scheduler_force"
        )
        
        if result.success:
            self.logger.info(f"Respaldo forzado creado exitosamente: {result.backup_path}")
        else:
            self.logger.error(f"Error en respaldo forzado: {result.error_message}")
        
        return result
    
    def get_scheduler_status(self) -> dict:
        """
        Obtener estado actual del planificador.
        
        Returns:
            dict: Estado del scheduler
        """
        return {
            'is_running': self.is_running,
            'schedule_interval_days': self.schedule_interval_days,
            'check_interval_hours': self.check_interval_hours,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'last_backup_time': self.last_backup_time.isoformat() if self.last_backup_time else None,
            'checks_performed': self.checks_performed,
            'backups_created': self.backups_created,
            'next_check_time': self._get_next_check_time().isoformat() if self.is_running else None
        }
    
    def _scheduler_loop(self) -> None:
        """
        Bucle principal del planificador ejecutándose en background.
        """
        self.logger.info("Bucle del scheduler iniciado")
        
        try:
            while self.is_running and not self._stop_event.is_set():
                try:
                    # Verificar y crear respaldo si es necesario
                    self.check_and_create_backup()
                    
                    # Esperar hasta la próxima verificación o hasta que se detenga
                    self._stop_event.wait(timeout=self.check_interval_seconds)
                    
                except Exception as e:
                    self.logger.error(f"Error en bucle del scheduler: {e}")
                    # Esperar un poco antes de continuar para evitar bucle de errores
                    self._stop_event.wait(timeout=60)
                    
        except KeyboardInterrupt:
            self.logger.info("Scheduler interrumpido por usuario")
        except Exception as e:
            self.logger.error(f"Error crítico en scheduler: {e}")
        finally:
            self.is_running = False
            self.logger.info("Bucle del scheduler terminado")
    
    def _get_next_check_time(self) -> datetime:
        """
        Calcular hora de la próxima verificación.
        
        Returns:
            datetime: Tiempo de la próxima verificación
        """
        if self.last_check_time:
            return self.last_check_time + timedelta(hours=self.check_interval_hours)
        else:
            return datetime.now() + timedelta(hours=self.check_interval_hours)
    
    def __enter__(self):
        """Context manager para uso con 'with' statement."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.stop()


class BackupSchedulerManager:
    """
    Manager para múltiples schedulers o configuraciones avanzadas.
    """
    
    def __init__(self):
        """Inicializar manager de schedulers."""
        self.schedulers: dict = {}
        self.logger = logging.getLogger(__name__)
    
    def add_scheduler(
        self, 
        name: str, 
        backup_service: BackupService, 
        **scheduler_kwargs
    ) -> BackupScheduler:
        """
        Agregar un nuevo scheduler.
        
        Args:
            name: Nombre único del scheduler
            backup_service: Servicio de respaldos
            **scheduler_kwargs: Argumentos para BackupScheduler
            
        Returns:
            BackupScheduler: Scheduler creado
        """
        if name in self.schedulers:
            raise SchedulerException(f"Scheduler '{name}' ya existe")
        
        scheduler = BackupScheduler(backup_service, **scheduler_kwargs)
        self.schedulers[name] = scheduler
        
        self.logger.info(f"Scheduler '{name}' agregado")
        return scheduler
    
    def start_scheduler(self, name: str) -> None:
        """
        Iniciar un scheduler específico.
        
        Args:
            name: Nombre del scheduler
        """
        if name not in self.schedulers:
            raise SchedulerException(f"Scheduler '{name}' no encontrado")
        
        self.schedulers[name].start()
    
    def stop_scheduler(self, name: str) -> None:
        """
        Detener un scheduler específico.
        
        Args:
            name: Nombre del scheduler
        """
        if name not in self.schedulers:
            raise SchedulerException(f"Scheduler '{name}' no encontrado")
        
        self.schedulers[name].stop()
    
    def start_all(self) -> None:
        """Iniciar todos los schedulers."""
        for name, scheduler in self.schedulers.items():
            try:
                scheduler.start()
                self.logger.info(f"Scheduler '{name}' iniciado")
            except Exception as e:
                self.logger.error(f"Error iniciando scheduler '{name}': {e}")
    
    def stop_all(self) -> None:
        """Detener todos los schedulers."""
        for name, scheduler in self.schedulers.items():
            try:
                scheduler.stop()
                self.logger.info(f"Scheduler '{name}' detenido")
            except Exception as e:
                self.logger.error(f"Error deteniendo scheduler '{name}': {e}")
    
    def get_all_status(self) -> dict:
        """
        Obtener estado de todos los schedulers.
        
        Returns:
            dict: Estado de todos los schedulers
        """
        return {
            name: scheduler.get_scheduler_status()
            for name, scheduler in self.schedulers.items()
        }
    
    def remove_scheduler(self, name: str) -> None:
        """
        Remover un scheduler.
        
        Args:
            name: Nombre del scheduler a remover
        """
        if name not in self.schedulers:
            raise SchedulerException(f"Scheduler '{name}' no encontrado")
        
        # Detener antes de remover
        self.schedulers[name].stop()
        del self.schedulers[name]
        
        self.logger.info(f"Scheduler '{name}' removido")
