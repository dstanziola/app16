"""
Sistema de configuración inicial para el compliance de desarrollo.

Este módulo implementa la configuración completa del sistema de compliance,
incluyendo validación de requisitos del sistema, inicialización de componentes
y creación de la estructura de directorios necesaria.
"""

import os
import sys
import json
import shutil
import importlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RequirementStatus(Enum):
    """Estados de validación de requisitos."""
    VALID = "VALID"
    INVALID = "INVALID"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


@dataclass
class SystemRequirements:
    """Requisitos del sistema de compliance."""
    python_version: RequirementStatus
    directory_structure: RequirementStatus
    dependencies: RequirementStatus
    file_permissions: RequirementStatus = RequirementStatus.UNKNOWN
    disk_space: RequirementStatus = RequirementStatus.UNKNOWN


@dataclass
class SetupResult:
    """Resultado de la configuración del sistema."""
    success: bool
    requirements: SystemRequirements
    created_directories: List[str]
    initialized_components: List[str]
    error_message: Optional[str] = None
    warnings: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.warnings is None:
            self.warnings = []


class ComplianceSetup:
    """
    Sistema de configuración inicial para compliance.
    
    Proporciona funcionalidad completa para validar requisitos del sistema,
    crear estructura de directorios e inicializar componentes necesarios
    para el funcionamiento del sistema de compliance.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Inicializar configuración de compliance.
        
        Args:
            base_dir: Directorio base del proyecto
        """
        self.base_dir = base_dir or os.getcwd()
        self.requirements = SystemRequirements(
            python_version=RequirementStatus.UNKNOWN,
            directory_structure=RequirementStatus.UNKNOWN,
            dependencies=RequirementStatus.UNKNOWN
        )
        self.validated_components: List[str] = []
        self.setup_log: List[Dict[str, Any]] = []
        self.required_directories = [
            'src/compliance',
            'src/compliance/models',
            'src/compliance/controllers',
            'src/compliance/validators',
            'src/compliance/utils',
            'tests/compliance',
            'tests/reports',
            'temp',
            'temp/sessions',
            'logs',
            'docs',
            'backups'
        ]
        self.required_dependencies = [
            'json',
            'os',
            'sys',
            'datetime',
            'typing',
            'dataclasses',
            'enum',
            'uuid',
            'unittest'
        ]
        
    def validate_python_version(self) -> bool:
        """
        Validar versión de Python.
        
        Returns:
            bool: True si la versión es compatible
        """
        self._log_operation("validate_python_version", "start")
        
        try:
            current_version = sys.version_info
            required_version = (3, 8)
            
            is_valid = current_version >= required_version
            
            self.requirements.python_version = (
                RequirementStatus.VALID if is_valid else RequirementStatus.INVALID
            )
            
            self._log_operation(
                "validate_python_version", 
                "completed",
                {
                    'current_version': f"{current_version.major}.{current_version.minor}",
                    'required_version': f"{required_version[0]}.{required_version[1]}",
                    'is_valid': is_valid
                }
            )
            
            return is_valid
            
        except Exception as e:
            self._log_operation("validate_python_version", "error", {'error': str(e)})
            return False
            
    def validate_directory_structure(self) -> bool:
        """
        Validar estructura de directorios requerida.
        
        Returns:
            bool: True si la estructura es válida
        """
        self._log_operation("validate_directory_structure", "start")
        
        try:
            missing_directories = []
            
            for dir_path in self.required_directories:
                full_path = os.path.join(self.base_dir, dir_path)
                if not os.path.exists(full_path):
                    missing_directories.append(dir_path)
                    
            is_valid = len(missing_directories) == 0
            
            self.requirements.directory_structure = (
                RequirementStatus.VALID if is_valid else RequirementStatus.INVALID
            )
            
            self._log_operation(
                "validate_directory_structure",
                "completed",
                {
                    'missing_directories': missing_directories,
                    'is_valid': is_valid
                }
            )
            
            return is_valid
            
        except Exception as e:
            self._log_operation("validate_directory_structure", "error", {'error': str(e)})
            return False
            
    def validate_dependencies(self) -> bool:
        """
        Validar dependencias requeridas.
        
        Returns:
            bool: True si todas las dependencias están disponibles
        """
        self._log_operation("validate_dependencies", "start")
        
        try:
            missing_dependencies = []
            
            for dependency in self.required_dependencies:
                try:
                    importlib.import_module(dependency)
                except ImportError:
                    missing_dependencies.append(dependency)
                    
            is_valid = len(missing_dependencies) == 0
            
            self.requirements.dependencies = (
                RequirementStatus.VALID if is_valid else RequirementStatus.INVALID
            )
            
            self._log_operation(
                "validate_dependencies",
                "completed",
                {
                    'missing_dependencies': missing_dependencies,
                    'is_valid': is_valid
                }
            )
            
            return is_valid
            
        except Exception as e:
            self._log_operation("validate_dependencies", "error", {'error': str(e)})
            return False
            
    def create_required_directories(self) -> bool:
        """
        Crear directorios requeridos.
        
        Returns:
            bool: True si todos los directorios fueron creados
        """
        self._log_operation("create_required_directories", "start")
        
        try:
            created_directories = []
            
            for dir_path in self.required_directories:
                full_path = os.path.join(self.base_dir, dir_path)
                
                if not os.path.exists(full_path):
                    os.makedirs(full_path, exist_ok=True)
                    created_directories.append(dir_path)
                    
            self._log_operation(
                "create_required_directories",
                "completed",
                {'created_directories': created_directories}
            )
            
            return True
            
        except Exception as e:
            self._log_operation("create_required_directories", "error", {'error': str(e)})
            return False
            
    def initialize_components(self) -> bool:
        """
        Inicializar componentes de compliance.
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        self._log_operation("initialize_components", "start")
        
        try:
            initialized_components = []
            
            # Crear archivos __init__.py en directorios de código
            init_dirs = [
                'src/compliance',
                'src/compliance/models',
                'src/compliance/controllers',
                'src/compliance/validators',
                'src/compliance/utils',
                'tests/compliance'
            ]
            
            for dir_path in init_dirs:
                init_file = os.path.join(self.base_dir, dir_path, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w', encoding='utf-8') as f:
                        f.write('"""Módulo de compliance del sistema de inventario."""\n')
                    initialized_components.append(f"{dir_path}/__init__.py")
                    
            # Crear archivos de control si no existen
            control_files = [
                ('compliance_log.md', self._get_default_compliance_log()),
                ('session_control.md', self._get_default_session_control())
            ]
            
            for file_name, content in control_files:
                file_path = os.path.join(self.base_dir, file_name)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    initialized_components.append(file_name)
                    
            self.validated_components = initialized_components
            
            self._log_operation(
                "initialize_components",
                "completed",
                {'initialized_components': initialized_components}
            )
            
            return True
            
        except Exception as e:
            self._log_operation("initialize_components", "error", {'error': str(e)})
            return False
            
    def validate_system_requirements(self) -> SystemRequirements:
        """
        Validar todos los requisitos del sistema.
        
        Returns:
            SystemRequirements: Estado de validación de requisitos
        """
        self._log_operation("validate_system_requirements", "start")
        
        try:
            # Ejecutar todas las validaciones
            python_valid = self.validate_python_version()
            structure_valid = self.validate_directory_structure()
            dependencies_valid = self.validate_dependencies()
            permissions_valid = self.validate_file_permissions()
            
            # Actualizar estado de requisitos
            self.requirements.python_version = (
                RequirementStatus.VALID if python_valid else RequirementStatus.INVALID
            )
            self.requirements.directory_structure = (
                RequirementStatus.VALID if structure_valid else RequirementStatus.INVALID
            )
            self.requirements.dependencies = (
                RequirementStatus.VALID if dependencies_valid else RequirementStatus.INVALID
            )
            self.requirements.file_permissions = (
                RequirementStatus.VALID if permissions_valid else RequirementStatus.INVALID
            )
            
            self._log_operation(
                "validate_system_requirements",
                "completed",
                {
                    'python_version': self.requirements.python_version.value,
                    'directory_structure': self.requirements.directory_structure.value,
                    'dependencies': self.requirements.dependencies.value,
                    'file_permissions': self.requirements.file_permissions.value
                }
            )
            
            return self.requirements
            
        except Exception as e:
            self._log_operation("validate_system_requirements", "error", {'error': str(e)})
            return self.requirements
            
    def run_setup(self) -> SetupResult:
        """
        Ejecutar configuración completa del sistema.
        
        Returns:
            SetupResult: Resultado de la configuración
        """
        self._log_operation("run_setup", "start")
        
        try:
            # Validar requisitos del sistema
            requirements = self.validate_system_requirements()
            
            # Verificar si hay errores críticos
            critical_errors = []
            if requirements.python_version == RequirementStatus.INVALID:
                critical_errors.append("Python version")
            if requirements.dependencies == RequirementStatus.INVALID:
                critical_errors.append("Dependencies")
                
            if critical_errors:
                error_message = f"Critical validation errors: {', '.join(critical_errors)}"
                return SetupResult(
                    success=False,
                    requirements=requirements,
                    created_directories=[],
                    initialized_components=[],
                    error_message=error_message
                )
                
            # Crear directorios requeridos
            directories_created = self.create_required_directories()
            if not directories_created:
                return SetupResult(
                    success=False,
                    requirements=requirements,
                    created_directories=[],
                    initialized_components=[],
                    error_message="Failed to create required directories"
                )
                
            # Inicializar componentes
            components_initialized = self.initialize_components()
            if not components_initialized:
                return SetupResult(
                    success=False,
                    requirements=requirements,
                    created_directories=self.required_directories,
                    initialized_components=[],
                    error_message="Failed to initialize components"
                )
                
            result = SetupResult(
                success=True,
                requirements=requirements,
                created_directories=self.required_directories,
                initialized_components=self.validated_components
            )
            
            self._log_operation("run_setup", "completed", {'success': True})
            
            return result
            
        except Exception as e:
            self._log_operation("run_setup", "error", {'error': str(e)})
            return SetupResult(
                success=False,
                requirements=self.requirements,
                created_directories=[],
                initialized_components=[],
                error_message=str(e)
            )
            
    def generate_setup_report(self) -> Dict[str, Any]:
        """
        Generar reporte completo de configuración.
        
        Returns:
            Dict: Reporte de configuración
        """
        status = self.get_setup_status()
        
        report = {
            'setup_status': status,
            'requirements_validation': {
                'python_version': self.requirements.python_version.value,
                'directory_structure': self.requirements.directory_structure.value,
                'dependencies': self.requirements.dependencies.value,
                'file_permissions': self.requirements.file_permissions.value,
                'disk_space': self.requirements.disk_space.value
            },
            'created_directories': self.required_directories,
            'initialized_components': self.validated_components,
            'setup_logs': self.setup_log,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    def get_setup_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la configuración.
        
        Returns:
            Dict: Estado de configuración
        """
        missing_components = []
        validation_errors = []
        
        # Verificar directorios
        for dir_path in self.required_directories:
            full_path = os.path.join(self.base_dir, dir_path)
            if not os.path.exists(full_path):
                missing_components.append(f"Directory: {dir_path}")
                
        # Verificar requisitos
        if self.requirements.python_version == RequirementStatus.INVALID:
            validation_errors.append("Python version incompatible")
        if self.requirements.dependencies == RequirementStatus.INVALID:
            validation_errors.append("Missing dependencies")
            
        is_configured = len(missing_components) == 0 and len(validation_errors) == 0
        
        return {
            'is_configured': is_configured,
            'missing_components': missing_components,
            'validation_errors': validation_errors,
            'last_validation': datetime.now().isoformat()
        }
        
    def reset_configuration(self) -> bool:
        """
        Reiniciar configuración del sistema.
        
        Returns:
            bool: True si se reinició correctamente
        """
        self._log_operation("reset_configuration", "start")
        
        try:
            # Limpiar logs y estado
            self.setup_log.clear()
            self.validated_components.clear()
            
            # Reiniciar requisitos
            self.requirements = SystemRequirements(
                python_version=RequirementStatus.UNKNOWN,
                directory_structure=RequirementStatus.UNKNOWN,
                dependencies=RequirementStatus.UNKNOWN
            )
            
            self._log_operation("reset_configuration", "completed")
            
            return True
            
        except Exception as e:
            self._log_operation("reset_configuration", "error", {'error': str(e)})
            return False
            
    def validate_file_permissions(self) -> bool:
        """
        Validar permisos de archivos del sistema.
        
        Returns:
            bool: True si los permisos son válidos
        """
        try:
            # Verificar permisos de escritura en directorio base
            test_file = os.path.join(self.base_dir, 'test_permissions.tmp')
            
            with open(test_file, 'w') as f:
                f.write('test')
                
            os.remove(test_file)
            
            return True
            
        except (OSError, PermissionError):
            return False
            
    def check_disk_space(self) -> Dict[str, Any]:
        """
        Verificar espacio disponible en disco.
        
        Returns:
            Dict: Información de espacio en disco
        """
        try:
            stat_result = os.statvfs(self.base_dir)
            available_bytes = stat_result.f_bavail * stat_result.f_frsize
            available_mb = available_bytes / (1024 * 1024)
            
            required_mb = 100  # 100 MB requeridos
            sufficient = available_mb >= required_mb
            
            return {
                'available_mb': round(available_mb, 2),
                'required_mb': required_mb,
                'sufficient': sufficient
            }
            
        except (OSError, AttributeError):
            # En Windows usar shutil.disk_usage
            try:
                total, used, free = shutil.disk_usage(self.base_dir)
                available_mb = free / (1024 * 1024)
                required_mb = 100
                
                return {
                    'available_mb': round(available_mb, 2),
                    'required_mb': required_mb,
                    'sufficient': available_mb >= required_mb
                }
                
            except OSError:
                return {
                    'available_mb': 0,
                    'required_mb': 100,
                    'sufficient': False
                }
                
    def backup_existing_configuration(self) -> Optional[str]:
        """
        Respaldar configuración existente.
        
        Returns:
            str: Ruta del respaldo o None si no se creó
        """
        try:
            backup_dir = os.path.join(self.base_dir, 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'config_backup_{timestamp}')
            
            # Crear directorio de respaldo
            os.makedirs(backup_path, exist_ok=True)
            
            return backup_path
            
        except OSError:
            return None
            
    def get_setup_logs(self) -> List[Dict[str, Any]]:
        """
        Obtener logs del proceso de configuración.
        
        Returns:
            List[Dict]: Lista de entradas de log
        """
        return self.setup_log.copy()
        
    def _log_operation(self, operation: str, status: str, details: Dict[str, Any] = None):
        """
        Registrar operación en el log.
        
        Args:
            operation: Nombre de la operación
            status: Estado de la operación
            details: Detalles adicionales
        """
        log_entry = {
            'operation': operation,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.setup_log.append(log_entry)
        
    def _get_default_compliance_log(self) -> str:
        """Obtener contenido por defecto para compliance_log.md."""
        return """# Registro de Cumplimiento

## Configuración Inicial
- **Fecha**: {}
- **Sistema configurado**: Automáticamente por ComplianceSetup
- **Estado**: Inicializado

---
**Próxima actualización**: Al completar primera fase de desarrollo
""".format(datetime.now().strftime('%Y-%m-%d %H:%M'))

    def _get_default_session_control(self) -> str:
        """Obtener contenido por defecto para session_control.md."""
        return """# Control de Sesión de Compliance

## Estado Actual
- **Sesión activa**: No
- **Fase actual**: Configuración inicial
- **Última actividad**: {}

## Configuración
- **Timeout de sesión**: 2 horas
- **Directorio de sesiones**: temp/sessions/
- **Logging habilitado**: Sí

---
**Configurado automáticamente por**: ComplianceSetup
""".format(datetime.now().strftime('%Y-%m-%d %H:%M'))
