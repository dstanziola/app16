"""
Service Container Implementation - Inyección de Dependencias Centralizada

CARACTERÍSTICAS IMPLEMENTADAS:
✓ Inyección de dependencias centralizada y explícita
✓ Servicios como singleton (una instancia por tipo)
✓ Inicialización lazy (solo cuando se necesiten)
✓ Dependencias claramente definidas y manejadas por el container
✓ Eliminación de duplicación de instancias y dependencias circulares
✓ Factory methods para configuración compleja
✓ Cleanup automático de recursos
✓ Detección de dependencias circulares
✓ Inspección del estado del container
✓ Manejo robusto de errores

PATRÓN ARQUITECTÓNICO:
- Service Container gestiona todas las instancias de servicios
- Registro explícito de servicios con sus dependencias
- Resolución automática del grafo de dependencias
- Lazy loading para optimización de performance
- Singleton pattern garantizado
- Factory pattern para creación compleja
- Observer pattern para cleanup

INTEGRACIÓN CON EL SISTEMA:
- Compatible con la arquitectura existente
- Elimina problemas de dependencias circulares identificados
- Optimiza uso de memoria con singleton
- Simplifica testing con inyección clara
- Mejora mantenibilidad del código

Autor: Sistema de Inventario - Arquitectura Clean
Fecha: Julio 2025
Versión: 1.0 - Implementación completa
"""

import logging
import threading
from typing import Dict, Any, Callable, List, Optional, Set
from functools import wraps
import weakref
import gc


class ServiceContainerError(Exception):
    """Excepción base para errores del Service Container."""
    pass


class ServiceNotFoundError(ServiceContainerError):
    """Excepción cuando un servicio no está registrado."""
    pass


class CircularDependencyError(ServiceContainerError):
    """Excepción cuando se detecta una dependencia circular."""
    pass


class ServiceRegistrationError(ServiceContainerError):
    """Excepción cuando hay error en el registro de servicios."""
    pass


class ServiceContainer:
    """
    Service Container para inyección de dependencias centralizada.
    
    Proporciona:
    - Registro de servicios con dependencias explícitas
    - Lazy loading con singleton pattern
    - Resolución automática de dependencias
    - Detección de dependencias circulares
    - Cleanup automático de recursos
    - Thread safety
    - Inspección de estado
    
    Ejemplo de uso:
        container = ServiceContainer()
        
        # Registrar servicios
        container.register('database', lambda: DatabaseConnection())
        container.register('category_service', 
                         lambda c: CategoryService(c.get('database')),
                         dependencies=['database'])
        
        # Usar servicios
        category_service = container.get('category_service')
    """
    
    def __init__(self, name: str = "main"):
        """
        Inicializar Service Container.
        
        Args:
            name: Nombre del container para debugging
        """
        self.name = name
        self._services: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: Set[str] = set()
        self._logger = logging.getLogger(f"ServiceContainer.{name}")
        
        self._logger.info(f"Service Container '{name}' inicializado")
    
    def register(self, 
                 service_name: str,
                 factory: Callable,
                 dependencies: Optional[List[str]] = None,
                 singleton: bool = True,
                 metadata: Optional[Dict[str, Any]] = None) -> 'ServiceContainer':
        """
        Registrar un servicio en el container.
        
        Args:
            service_name: Nombre único del servicio
            factory: Factory function que crea el servicio
            dependencies: Lista de dependencias requeridas
            singleton: Si debe usar patrón singleton (True por defecto)
            metadata: Metadatos adicionales del servicio
            
        Returns:
            Self para chaining
            
        Raises:
            ServiceRegistrationError: Si hay error en el registro
        """
        with self._lock:
            try:
                if not service_name or not service_name.strip():
                    raise ServiceRegistrationError("El nombre del servicio no puede estar vacío")
                
                if not callable(factory):
                    raise ServiceRegistrationError("Factory debe ser callable")
                
                # Validar dependencias
                dependencies = dependencies or []
                if not isinstance(dependencies, list):
                    raise ServiceRegistrationError("Dependencies debe ser una lista")
                
                # Verificar dependencias circulares en tiempo de registro
                self._validate_no_circular_dependencies(service_name, dependencies)
                
                # Registrar servicio
                self._services[service_name] = {
                    'factory': factory,
                    'dependencies': dependencies.copy(),
                    'singleton': singleton,
                    'metadata': metadata or {},
                    'registered_at': self._get_timestamp()
                }
                
                self._logger.debug(f"Servicio '{service_name}' registrado con dependencias: {dependencies}")
                return self
                
            except Exception as e:
                self._logger.error(f"Error registrando servicio '{service_name}': {e}")
                raise ServiceRegistrationError(f"Error registrando '{service_name}': {e}")
    
    def get(self, service_name: str) -> Any:
        """
        Obtener una instancia del servicio solicitado.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Instancia del servicio
            
        Raises:
            ServiceNotFoundError: Si el servicio no está registrado
            CircularDependencyError: Si se detecta dependencia circular
        """
        with self._lock:
            try:
                # Verificar que el servicio está registrado
                if not self.is_registered(service_name):
                    raise ServiceNotFoundError(f"Servicio '{service_name}' no está registrado")
                
                # Verificar si ya está instanciado (singleton)
                if service_name in self._instances:
                    self._logger.debug(f"Retornando instancia singleton de '{service_name}'")
                    return self._instances[service_name]
                
                # Verificar dependencias circulares durante resolución
                if service_name in self._resolution_stack:
                    cycle = list(self._resolution_stack) + [service_name]
                    raise CircularDependencyError(f"Dependencia circular detectada: {' -> '.join(cycle)}")
                
                # Agregar a stack de resolución
                self._resolution_stack.add(service_name)
                
                try:
                    # Resolver dependencias primero
                    service_config = self._services[service_name]
                    resolved_dependencies = {}
                    
                    for dep_name in service_config['dependencies']:
                        resolved_dependencies[dep_name] = self.get(dep_name)
                    
                    # Crear instancia usando factory
                    factory = service_config['factory']
                    
                    # Llamar factory con container como parámetro
                    if self._factory_takes_container(factory):
                        instance = factory(self)
                    else:
                        instance = factory()
                    
                    # Almacenar instancia si es singleton
                    if service_config['singleton']:
                        self._instances[service_name] = instance
                    
                    self._logger.debug(f"Servicio '{service_name}' instanciado exitosamente")
                    return instance
                    
                finally:
                    # Remover del stack de resolución
                    self._resolution_stack.discard(service_name)
                    
            except (ServiceNotFoundError, CircularDependencyError):
                raise
            except Exception as e:
                self._logger.error(f"Error obteniendo servicio '{service_name}': {e}")
                raise ServiceContainerError(f"Error obteniendo '{service_name}': {e}")
    
    def is_registered(self, service_name: str) -> bool:
        """
        Verificar si un servicio está registrado.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            True si está registrado
        """
        with self._lock:
            return service_name in self._services
    
    def is_instantiated(self, service_name: str) -> bool:
        """
        Verificar si un servicio ya está instanciado.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            True si está instanciado
        """
        with self._lock:
            return service_name in self._instances
    
    def get_dependencies(self, service_name: str) -> List[str]:
        """
        Obtener lista de dependencias de un servicio.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Lista de dependencias
            
        Raises:
            ServiceNotFoundError: Si el servicio no existe
        """
        with self._lock:
            if not self.is_registered(service_name):
                raise ServiceNotFoundError(f"Servicio '{service_name}' no está registrado")
            
            return self._services[service_name]['dependencies'].copy()
    
    def get_registered_services(self) -> List[str]:
        """
        Obtener lista de todos los servicios registrados.
        
        Returns:
            Lista de nombres de servicios registrados
        """
        with self._lock:
            return list(self._services.keys())
    
    def get_instantiated_services(self) -> List[str]:
        """
        Obtener lista de servicios ya instanciados.
        
        Returns:
            Lista de nombres de servicios instanciados
        """
        with self._lock:
            return list(self._instances.keys())
    
    def unregister(self, service_name: str) -> bool:
        """
        Desregistrar un servicio del container.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            True si se desregistró exitosamente
        """
        with self._lock:
            try:
                # Cleanup de instancia si existe
                if service_name in self._instances:
                    instance = self._instances[service_name]
                    self._cleanup_service_instance(instance)
                    del self._instances[service_name]
                
                # Remover registro
                if service_name in self._services:
                    del self._services[service_name]
                    self._logger.debug(f"Servicio '{service_name}' desregistrado")
                    return True
                
                return False
                
            except Exception as e:
                self._logger.error(f"Error desregistrando servicio '{service_name}': {e}")
                return False
    
    def cleanup(self) -> None:
        """
        Limpiar todos los recursos del container.
        
        Llama cleanup en todos los servicios instanciados y limpia el container.
        """
        with self._lock:
            try:
                self._logger.info(f"Iniciando cleanup del container '{self.name}'")
                
                # Cleanup de todas las instancias
                for service_name, instance in list(self._instances.items()):
                    try:
                        self._cleanup_service_instance(instance)
                    except Exception as e:
                        self._logger.warning(f"Error en cleanup de '{service_name}': {e}")
                
                # Limpiar registros
                self._instances.clear()
                self._services.clear()
                self._resolution_stack.clear()
                
                # Forzar garbage collection
                gc.collect()
                
                self._logger.info(f"Cleanup del container '{self.name}' completado")
                
            except Exception as e:
                self._logger.error(f"Error durante cleanup: {e}")
    
    def get_container_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del container.
        
        Returns:
            Diccionario con estadísticas del container
        """
        with self._lock:
            return {
                'name': self.name,
                'total_registered': len(self._services),
                'total_instantiated': len(self._instances),
                'services_registered': list(self._services.keys()),
                'services_instantiated': list(self._instances.keys()),
                'memory_usage': self._estimate_memory_usage(),
                'resolution_stack': list(self._resolution_stack)
            }
    
    def validate_all_dependencies(self) -> Dict[str, List[str]]:
        """
        Validar todas las dependencias registradas.
        
        Returns:
            Diccionario con errores encontrados por servicio
        """
        errors = {}
        
        with self._lock:
            for service_name, config in self._services.items():
                service_errors = []
                
                # Verificar que todas las dependencias estén registradas
                for dep in config['dependencies']:
                    if not self.is_registered(dep):
                        service_errors.append(f"Dependencia '{dep}' no está registrada")
                
                # Verificar dependencias circulares
                try:
                    self._validate_no_circular_dependencies(service_name, config['dependencies'])
                except CircularDependencyError as e:
                    service_errors.append(str(e))
                
                if service_errors:
                    errors[service_name] = service_errors
        
        return errors
    
    # Métodos privados
    
    def _validate_no_circular_dependencies(self, service_name: str, dependencies: List[str]) -> None:
        """
        Validar que no haya dependencias circulares.
        
        Args:
            service_name: Nombre del servicio
            dependencies: Lista de dependencias
            
        Raises:
            CircularDependencyError: Si se detecta dependencia circular
        """
        visited = set()
        path = []
        
        def check_circular(current_service: str) -> None:
            if current_service in path:
                cycle_start = path.index(current_service)
                cycle = path[cycle_start:] + [current_service]
                raise CircularDependencyError(f"Dependencia circular: {' -> '.join(cycle)}")
            
            if current_service in visited:
                return
            
            visited.add(current_service)
            path.append(current_service)
            
            # Verificar dependencias del servicio actual
            if current_service in self._services:
                for dep in self._services[current_service]['dependencies']:
                    check_circular(dep)
            
            path.pop()
        
        # Simular agregar el nuevo servicio temporalmente
        temp_services = self._services.copy()
        temp_services[service_name] = {'dependencies': dependencies}
        
        # Verificar desde el nuevo servicio
        original_services = self._services
        self._services = temp_services
        
        try:
            check_circular(service_name)
        finally:
            self._services = original_services
    
    def _factory_takes_container(self, factory: Callable) -> bool:
        """
        Determinar si el factory necesita el container como parámetro.
        
        Args:
            factory: Factory function
            
        Returns:
            True si el factory espera el container
        """
        import inspect
        
        try:
            sig = inspect.signature(factory)
            params = list(sig.parameters.keys())
            
            # Si tiene un parámetro, asumimos que es el container
            return len(params) == 1
            
        except Exception:
            # En caso de error, asumir que no necesita container
            return False
    
    def _cleanup_service_instance(self, instance: Any) -> None:
        """
        Cleanup de una instancia de servicio.
        
        Args:
            instance: Instancia del servicio
        """
        try:
            # Intentar llamar método cleanup si existe
            if hasattr(instance, 'cleanup') and callable(getattr(instance, 'cleanup')):
                instance.cleanup()
            
            # Intentar llamar método close si existe
            elif hasattr(instance, 'close') and callable(getattr(instance, 'close')):
                instance.close()
            
            # Intentar llamar método dispose si existe
            elif hasattr(instance, 'dispose') and callable(getattr(instance, 'dispose')):
                instance.dispose()
                
        except Exception as e:
            self._logger.warning(f"Error en cleanup de instancia: {e}")
    
    def _estimate_memory_usage(self) -> int:
        """
        Estimar uso de memoria del container.
        
        Returns:
            Estimación de bytes utilizados
        """
        try:
            import sys
            
            total_size = 0
            total_size += sys.getsizeof(self._services)
            total_size += sys.getsizeof(self._instances)
            
            for instance in self._instances.values():
                total_size += sys.getsizeof(instance)
            
            return total_size
            
        except Exception:
            return 0
    
    def _get_timestamp(self) -> str:
        """
        Obtener timestamp actual.
        
        Returns:
            Timestamp en formato ISO
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def __repr__(self) -> str:
        """Representación string del container."""
        with self._lock:
            return (f"ServiceContainer(name='{self.name}', "
                   f"registered={len(self._services)}, "
                   f"instantiated={len(self._instances)})")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit con cleanup automático."""
        self.cleanup()


# Instancia global del container principal
_global_container: Optional[ServiceContainer] = None
_container_lock = threading.Lock()


def get_container(name: str = "main") -> ServiceContainer:
    """
    Obtener instancia del Service Container.
    
    Args:
        name: Nombre del container
        
    Returns:
        Instancia del Service Container
    """
    global _global_container
    
    with _container_lock:
        if _global_container is None:
            _global_container = ServiceContainer(name)
        
        return _global_container


def setup_default_container() -> ServiceContainer:
    """
    Configurar el container por defecto con los servicios del sistema.
    
    Returns:
        Container configurado
    """
    container = get_container()
    
    # Registrar servicios básicos del sistema
    try:
        from db.database import get_database_connection
        from services.category_service import CategoryService
        from services.product_service import ProductService
        from services.client_service import ClientService
        from services.sales_service import SalesService
        from services.movement_service import MovementService
        from services.report_service import ReportService
        from services.user_service import UserService
        
        # Registrar base de datos
        container.register(
            'database',
            lambda: get_database_connection(),
            dependencies=[]
        )
        
        # Registrar servicios de dominio
        container.register(
            'category_service',
            lambda c: CategoryService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'product_service',
            lambda c: ProductService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'client_service',
            lambda c: ClientService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'sales_service',
            lambda c: SalesService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'movement_service',
            lambda c: MovementService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'report_service',
            lambda c: ReportService(c.get('database')),
            dependencies=['database']
        )
        
        container.register(
            'user_service',
            lambda c: UserService(
                db_connection=c.get('database'),
                password_hasher=c.get('password_hasher')
            ),
            dependencies=['database', 'password_hasher']
        )

        
        # Registrar CompanyService con corrección aplicada
        try:
            from services.company_service import CompanyService
            container.register(
                'company_service',
                lambda c: CompanyService(db_connection=c.get('database')),
                dependencies=['database']
            )
        except ImportError:
            pass
        
        # Registrar servicios opcionales si están disponibles
        try:
            from services.label_service import LabelService
            container.register(
                'label_service',
                lambda c: LabelService(category_service=c.get('category_service')),  # Con dependency injection
                dependencies=['category_service']
            )
        except ImportError:
            pass
        
        try:
            from services.barcode_service import BarcodeService
            container.register(
                'barcode_service',
                lambda c: BarcodeService(),
                dependencies=[]
            )
        except ImportError:
            pass
        
        # Registrar TicketService - CORREGIDO
        try:
            from services.ticket_service import TicketService
            container.register(
                'ticket_service',
                lambda c: TicketService(c.get('database')),
                dependencies=['database']
            )
        except ImportError:
            pass
        
        # SPRINT 2: Registrar ExportService - Sistema de exportación
        # CORRECCIÓN CRÍTICA: Manejo robusto de errores con validación específica
        try:
            # Validar que el módulo se puede importar
            from services.export_service import ExportService
            
            # Validar que las dependencias están disponibles
            required_deps = ['movement_service', 'report_service']
            missing_deps = [dep for dep in required_deps if not container.is_registered(dep)]
            
            if missing_deps:
                raise ServiceRegistrationError(
                    f"ExportService requiere dependencias no registradas: {missing_deps}"
                )
            
            # Registrar ExportService con factory que valida dependencias
            def create_export_service(c):
                try:
                    movement_service = c.get('movement_service')
                    report_service = c.get('report_service')
                    
                    if not movement_service:
                        raise ValueError("MovementService no disponible para ExportService")
                    if not report_service:
                        raise ValueError("ReportService no disponible para ExportService")
                    
                    return ExportService(
                        movement_service=movement_service,
                        report_service=report_service
                    )
                except Exception as create_error:
                    logging.getLogger("ServiceContainer").error(
                        f"❌ Error creando instancia ExportService: {create_error}"
                    )
                    raise ServiceRegistrationError(
                        f"No se pudo crear ExportService: {create_error}"
                    )
            
            container.register(
                'export_service',
                create_export_service,
                dependencies=required_deps
            )
            
            # Verificar que el registro fue exitoso
            test_service = container.get('export_service')
            if not test_service:
                raise ServiceRegistrationError("ExportService se registró pero get() retorna None")
            
            # Verificar que tiene método crítico para tickets
            if not hasattr(test_service, 'generate_entry_ticket'):
                raise ServiceRegistrationError(
                    "ExportService no tiene método generate_entry_ticket requerido"
                )
            
            logging.getLogger("ServiceContainer").info(
                "✅ ExportService registrado y validado exitosamente en container"
            )
            
        except ImportError as e:
            error_msg = f"ExportService no se puede importar - Módulo no encontrado: {e}"
            logging.getLogger("ServiceContainer").error(f"❌ {error_msg}")
            
            # CRÍTICO: ExportService es requerido para tickets de entrada
            raise ServiceRegistrationError(
                f"CRÍTICO: {error_msg}. "
                f"ExportService es requerido para generar tickets de entrada. "
                f"Verifique que existe src/services/export_service.py"
            )
            
        except ServiceRegistrationError:
            # Re-lanzar errores de registro sin modificar
            raise
            
        except Exception as e:
            error_msg = f"Error inesperado registrando ExportService: {e}"
            logging.getLogger("ServiceContainer").error(f"❌ {error_msg}")
            
            raise ServiceRegistrationError(
                f"CRÍTICO: {error_msg}. "
                f"ExportService es requerido para el sistema de tickets."
            )
        
        # Registrar InventoryService si está disponible
        try:
            from services.inventory_service import InventoryService
            container.register(
                'inventory_service',
                lambda c: InventoryService(c.get('database')),
                dependencies=['database']
            )
        except ImportError:
            pass
        
        # CRITICAL: Registrar AuthService y dependencias de seguridad
        try:
            from infrastructure.security.password_hasher import create_password_hasher
            from shared.session.session_manager import create_session_manager  # CORRECCIÓN: Usar SessionManager correcto
            from application.services.auth_service import create_auth_service
            
            # Registrar PasswordHasher (sin dependencias)
            container.register(
                'password_hasher',
                lambda: create_password_hasher(),
                dependencies=[]
            )
            
            # Registrar SessionManager mejorado
            container.register(
                'session_manager',
                lambda: create_session_manager(),
                dependencies=[]
            )
            
            # Registrar AuthService (con todas sus dependencias)
            container.register(
                'auth_service',
                lambda c: create_auth_service(
                    user_repository=c.get('user_service'),
                    session_manager=c.get('session_manager'),
                    password_hasher=c.get('password_hasher')
                ),
                dependencies=['user_service', 'session_manager', 'password_hasher']
            )
            
            logging.getLogger("ServiceContainer").info("✅ AuthService registrado exitosamente en container")
            
        except ImportError as e:
            logging.getLogger("ServiceContainer").error(f"❌ AuthService no disponible - Error crítico: {e}")
            # Re-lanzar excepción porque AuthService es crítico
            raise ServiceRegistrationError(f"AuthService es requerido para el sistema: {e}")
        
        logging.getLogger("ServiceContainer").info("Container por defecto configurado exitosamente")
        
    except Exception as e:
        logging.getLogger("ServiceContainer").error(f"Error configurando container por defecto: {e}")
        raise
    
    return container


def cleanup_container() -> None:
    """
    Cleanup del container global.
    """
    global _global_container
    
    with _container_lock:
        if _global_container is not None:
            _global_container.cleanup()
            _global_container = None


# Decorador para inyección automática de dependencias
def inject(*service_names):
    """
    Decorador para inyección automática de dependencias.
    
    Args:
        *service_names: Nombres de servicios a inyectar
        
    Example:
        @inject('database', 'category_service')
        def my_function(database, category_service):
            # usar servicios
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            
            # Inyectar servicios como argumentos
            injected_services = []
            for service_name in service_names:
                injected_services.append(container.get(service_name))
            
            return func(*injected_services, *args, **kwargs)
        
        return wrapper
    return decorator
