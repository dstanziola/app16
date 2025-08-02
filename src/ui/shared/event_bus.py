"""
Event Bus Implementation - Patrón Publisher/Subscriber
Capa: Presentation Layer - UI Shared Components
Objetivo: Desacoplar comunicación entre widgets UI

Clean Architecture compliance:
- Sin dependencias a capas externas
- Interfaz simple y enfocada
- Thread-safe para aplicaciones PyQt6
- Logging integrado para debugging
"""

import logging
import time
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class EventData:
    """Estructura de datos estándar para eventos del Event Bus."""
    
    event_type: str
    timestamp: float
    data: Dict[str, Any]
    source: str
    
    def __post_init__(self):
        """Validar datos del evento después de inicialización."""
        if not self.event_type:
            raise ValueError("event_type es obligatorio")
        
        if not self.source:
            raise ValueError("source es obligatorio")
        
        if self.timestamp <= 0:
            self.timestamp = time.time()


class EventBus(QObject):
    """
    Event Bus implementation para comunicación desacoplada entre widgets.
    
    Implementa patrón Publisher/Subscriber con:
    - Registro dinámico de listeners
    - Publicación asíncrona de eventos
    - Thread safety para PyQt6
    - Logging para debugging
    - Manejo robusto de errores
    """
    
    # Señal PyQt6 para eventos asíncronos
    event_published = pyqtSignal(str, dict)
    
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventBus':
        """Implementar Singleton pattern thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializar Event Bus si no está ya inicializado."""
        # CORRECCIÓN CRÍTICA: super().__init__() SIEMPRE debe ejecutarse para PyQt6
        super().__init__()
        
        # Solo inicializar instancia una vez (patrón Singleton)
        if hasattr(self, '_initialized'):
            return
        
        self._listeners: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._initialized = True
        
        # Conectar señal PyQt6 para manejo asíncrono
        self.event_published.connect(self._handle_event_async)
        
        self._logger.info("EventBus inicializado correctamente")
    
    def register(self, event_type: str, callback: Callable[[EventData], None]) -> None:
        """
        Registrar listener para tipo de evento específico.
        
        Args:
            event_type: Tipo de evento a escuchar
            callback: Función a llamar cuando se publique el evento
            
        Raises:
            ValueError: Si event_type está vacío o callback es None
        """
        if not event_type or not event_type.strip():
            raise ValueError("event_type no puede estar vacío")
        
        if callback is None:
            raise ValueError("callback no puede ser None")
        
        if not callable(callback):
            raise ValueError("callback debe ser callable")
        
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            
            if callback not in self._listeners[event_type]:
                self._listeners[event_type].append(callback)
                self._logger.debug(f"Listener registrado para evento '{event_type}'")
            else:
                self._logger.warning(f"Listener ya estaba registrado para evento '{event_type}'")
    
    def unregister(self, event_type: str, callback: Callable) -> bool:
        """
        Desregistrar listener específico.
        
        Args:
            event_type: Tipo de evento
            callback: Callback a desregistrar
            
        Returns:
            bool: True si se desregistró exitosamente, False si no existía
        """
        if not event_type or callback is None:
            return False
        
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(callback)
                    self._logger.debug(f"Listener desregistrado para evento '{event_type}'")
                    
                    # Limpiar lista vacía
                    if not self._listeners[event_type]:
                        del self._listeners[event_type]
                    
                    return True
                except ValueError:
                    self._logger.warning(f"Listener no encontrado para evento '{event_type}'")
                    return False
            
            return False
    
    def publish(self, event_type: str, data: Dict[str, Any], source: str = "unknown") -> None:
        """
        Publicar evento a todos los listeners registrados.
        
        Args:
            event_type: Tipo de evento a publicar
            data: Datos del evento
            source: Fuente que origina el evento
        """
        try:
            event_data = EventData(
                event_type=event_type,
                timestamp=time.time(),
                data=data,
                source=source
            )
            
            # Publicar via señal PyQt6 para thread safety
            self.event_published.emit(event_type, event_data.__dict__)
            
            self._logger.debug(f"Evento '{event_type}' publicado desde '{source}'")
            
        except Exception as e:
            self._logger.error(f"Error publicando evento '{event_type}': {e}")
    
    def _handle_event_async(self, event_type: str, event_data_dict: Dict[str, Any]) -> None:
        """
        Manejar evento de forma asíncrona (llamado por señal PyQt6).
        
        Args:
            event_type: Tipo de evento
            event_data_dict: Datos del evento como diccionario
        """
        try:
            # Reconstruir EventData desde diccionario
            event_data = EventData(**event_data_dict)
            
            with self._lock:
                listeners = self._listeners.get(event_type, []).copy()
            
            if not listeners:
                self._logger.debug(f"No hay listeners para evento '{event_type}'")
                return
            
            # Notificar a todos los listeners
            for listener in listeners:
                try:
                    listener(event_data)
                except Exception as e:
                    self._logger.error(
                        f"Error en listener para evento '{event_type}': {e}",
                        exc_info=True
                    )
            
            self._logger.debug(f"Evento '{event_type}' procesado por {len(listeners)} listeners")
            
        except Exception as e:
            self._logger.error(f"Error manejando evento '{event_type}': {e}", exc_info=True)
    
    def get_registered_events(self) -> List[str]:
        """
        Obtener lista de tipos de eventos registrados.
        
        Returns:
            List[str]: Lista de tipos de eventos con listeners
        """
        with self._lock:
            return list(self._listeners.keys())
    
    def get_listener_count(self, event_type: str) -> int:
        """
        Obtener cantidad de listeners para evento específico.
        
        Args:
            event_type: Tipo de evento
            
        Returns:
            int: Cantidad de listeners registrados
        """
        with self._lock:
            return len(self._listeners.get(event_type, []))
    
    def clear_all_listeners(self) -> None:
        """Limpiar todos los listeners registrados."""
        with self._lock:
            self._listeners.clear()
            self._logger.info("Todos los listeners han sido limpiados")
    
    def clear_listeners_for_event(self, event_type: str) -> int:
        """
        Limpiar listeners para evento específico.
        
        Args:
            event_type: Tipo de evento
            
        Returns:
            int: Cantidad de listeners que fueron removidos
        """
        with self._lock:
            if event_type in self._listeners:
                count = len(self._listeners[event_type])
                del self._listeners[event_type]
                self._logger.debug(f"Removidos {count} listeners para evento '{event_type}'")
                return count
            return 0


# Instancia global del Event Bus (Singleton) - Inicialización lazy
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Obtener instancia global del Event Bus con inicialización lazy.
    
    Returns:
        EventBus: Instancia singleton del Event Bus
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def clear_global_event_bus() -> None:
    """
    Limpiar la instancia global del Event Bus.
    Útil para testing y cleanup.
    """
    global _global_event_bus
    if _global_event_bus is not None:
        _global_event_bus.clear_all_listeners()
        _global_event_bus = None


if __name__ == "__main__":
    # Test básico de funcionalidad
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test básico usando get_event_bus() para consistencia
    eb = get_event_bus()
    
    def test_listener(event_data: EventData):
        print(f"Recibido evento: {event_data.event_type} desde {event_data.source}")
        print(f"Datos: {event_data.data}")
    
    eb.register("test_event", test_listener)
    eb.publish("test_event", {"message": "Hello World"}, "test_source")
    
    print(f"Eventos registrados: {eb.get_registered_events()}")
    print(f"Listeners para 'test_event': {eb.get_listener_count('test_event')}")
    
    # Cleanup para testing
    clear_global_event_bus()
