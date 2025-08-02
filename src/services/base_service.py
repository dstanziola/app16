"""
Servicio base para todos los servicios del sistema.
Proporciona funcionalidad común y patrones estándar.
"""

from typing import Any, Dict, Optional, List
from abc import ABC, abstractmethod


class BaseService(ABC):
    """Clase base para todos los servicios del sistema."""
    
    def __init__(self, database_connection):
        """
        Inicializar servicio base.
        
        Args:
            database_connection: Conexión a base de datos
        """
        self.database_connection = database_connection
    
    @abstractmethod
    def get_name(self) -> str:
        """Obtener nombre del servicio."""
        pass
    
    def get_database_connection(self):
        """Obtener conexión a base de datos."""
        return self.database_connection
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validar que los campos requeridos estén presentes.
        
        Args:
            data: Datos a validar
            required_fields: Lista de campos requeridos
            
        Returns:
            True si todos los campos están presentes, False en caso contrario
        """
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        return True
    
    def log_operation(self, operation: str, details: str = ""):
        """
        Registrar operación en log.
        
        Args:
            operation: Nombre de la operación
            details: Detalles adicionales
        """
        print(f"[{self.get_name()}] {operation}: {details}")
