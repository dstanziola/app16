"""
Event Bus Implementation - 100% tkinter compatible
Carga: Presentation Layer - UI Shared Components
Objetivo: Desacoplar comunicación entre widgets UI SIN PyQt6

CORRECCIÓN CRÍTICA: Eliminada dependencia PyQt6 para compatibilidad tkinter
- Sin QObject, sin pyqtSignal
- Event loop 100% tkinter compatible
- Threading safe con tkinter after()
- Logging integrado para debugging
"""

import logging
import time
import threading
import tkinter as tk
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass


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


class EventBusTkinter:
    """
    Event Bus implementation 100% compatible con tkinter.
    
    Implementa patrón Publisher/Subscriber con:
    - Registro dinámico de listeners
    - Publicación asíncrona de eventos via tkinter.after()
    - Thread safety para aplicaciones tkinter
    - Logging para debugging
    - Manejo robusto de errores
    - SIN dependencias PyQt6
    """
    
    _instance: Optional['EventBusTkinter'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventBusTkinter':
        """Implementar Singleton pattern thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializar Event Bus si no está ya inicializado."""
        # Solo inicializar instancia una vez (patrón Singleton)
        if hasattr(self, '_initialized'):
            return
        
        self._listeners: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._initialized = True
        
        # Tkinter root para scheduling asíncrono
        self._root: Optional[tk.Tk] = None
        
        self._logger.info("EventBusTkinter inicializado correctamente (sin PyQt6)")
    
    def set_tkinter_root(self, root: tk.Tk) -> None:
        """
        Establecer root de tkinter para scheduling asíncrono.
        
        Args:
            root: Instancia principal de tkinter
        """
        self._root = root
        self._logger.debug("Tkinter root configurado para Event Bus")
    
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
            
            # Procesar de forma asíncrona via tkinter.after() si root disponible
            if self._root:
                self._root.after(0, lambda: self._handle_event_async(event_data))
            else:
                # Fallback: procesamiento síncrono
                self._handle_event_async(event_data)
            
            self._logger.debug(f"Evento '{event_type}' publicado desde '{source}' (tkinter)")
            
        except Exception as e:
            self._logger.error(f"Error publicando evento '{event_type}': {e}")
    
    def _handle_event_async(self, event_data: EventData) -> None:
        """
        Manejar evento de forma asíncrona (compatible con tkinter).
        
        Args:
            event_data: Datos del evento
        """
        try:
            with self._lock:
                listeners = self._listeners.get(event_data.event_type, []).copy()
            
            if not listeners:
                self._logger.debug(f"No hay listeners para evento '{event_data.event_type}'")
                return
            
            # Notificar a todos los listeners
            for listener in listeners:
                try:
                    listener(event_data)
                except Exception as e:
                    self._logger.error(
                        f"Error en listener para evento '{event_data.event_type}': {e}",
                        exc_info=True
                    )
            
            self._logger.debug(f"Evento '{event_data.event_type}' procesado por {len(listeners)} listeners")
            
        except Exception as e:
            self._logger.error(f"Error manejando evento '{event_data.event_type}': {e}", exc_info=True)
    
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


# Instancia global del Event Bus tkinter-compatible (Singleton) - Inicialización lazy
_global_event_bus_tkinter: Optional[EventBusTkinter] = None


def get_event_bus_tkinter() -> EventBusTkinter:
    """
    Obtener instancia global del Event Bus tkinter-compatible con inicialización lazy.
    
    Returns:
        EventBusTkinter: Instancia singleton del Event Bus
    """
    global _global_event_bus_tkinter
    if _global_event_bus_tkinter is None:
        _global_event_bus_tkinter = EventBusTkinter()
    return _global_event_bus_tkinter


def clear_global_event_bus_tkinter() -> None:
    """
    Limpiar la instancia global del Event Bus tkinter.
    Útil para testing y cleanup.
    """
    global _global_event_bus_tkinter
    if _global_event_bus_tkinter is not None:
        _global_event_bus_tkinter.clear_all_listeners()
        _global_event_bus_tkinter = None


# ==================== COMPATIBILITY LAYER ====================

# Aliasas para compatibilidad con código existente
EventBus = EventBusTkinter
get_event_bus = get_event_bus_tkinter
clear_global_event_bus = clear_global_event_bus_tkinter


if __name__ == "__main__":
    # Test básico de funcionalidad con tkinter
    import tkinter as tk
    
    # Crear ventana de prueba
    root = tk.Tk()
    root.title("Test EventBusTkinter")
    
    # Test básico usando get_event_bus() para consistencia
    eb = get_event_bus()
    eb.set_tkinter_root(root)
    
    def test_listener(event_data: EventData):
        print(f"Recibido evento: {event_data.event_type} desde {event_data.source}")
        print(f"Datos: {event_data.data}")
    
    eb.register("test_event", test_listener)
    eb.publish("test_event", {"message": "Hello World"}, "test_source")
    
    print(f"Eventos registrados: {eb.get_registered_events()}")
    print(f"Listeners para 'test_event': {eb.get_listener_count('test_event')}")
    
    # Test de procesamiento asíncrono
    def delayed_test():
        eb.publish("delayed_test", {"message": "Delayed message"}, "timer")
    
    root.after(1000, delayed_test)
    
    # Botón para test manual
    def manual_test():
        eb.publish("manual_test", {"message": "Manual test"}, "button")
    
    eb.register("delayed_test", test_listener)
    eb.register("manual_test", test_listener)
    
    test_button = tk.Button(root, text="Test Manual", command=manual_test)
    test_button.pack(pady=20)
    
    label = tk.Label(root, text="EventBusTkinter Test - Check console for events")
    label.pack(pady=10)
    
    # Cleanup para testing después de 5 segundos
    def cleanup_test():
        print("Ejecutando cleanup...")
        clear_global_event_bus()
        print("Cleanup completado")
        root.destroy()
    
    root.after(5000, cleanup_test)
    
    print("Iniciando tkinter mainloop...")
    root.mainloop()
