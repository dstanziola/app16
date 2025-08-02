"""
Helpers para patrón FASE 3 - Sistema de Inventario Copy Point S.A.

Este módulo contiene helpers especializados que implementan el patrón FASE 3:
- DatabaseHelper: Operaciones de base de datos optimizadas y seguras
- ValidationHelper: Validaciones de datos robustas y reutilizables  
- LoggingHelper: Sistema de logging estructurado y centralizado

ARQUITECTURA FASE 3:
Los servicios optimizados utilizan estos helpers para:
1. Separar responsabilidades claramente
2. Reutilizar código común
3. Estandarizar operaciones críticas
4. Facilitar testing y mantenimiento

USO EN SERVICIOS:
```python
class OptimizedService:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.db_helper = DatabaseHelper(db_connection)
        self.validator = ValidationHelper()
        self.logger = LoggingHelper.get_service_logger('service_name')
```
"""

from .database_helper import DatabaseHelper
from .validation_helper import ValidationHelper
from .logging_helper import LoggingHelper, LoggingContext

__all__ = [
    'DatabaseHelper',
    'ValidationHelper', 
    'LoggingHelper',
    'LoggingContext'
]

# Configurar logging automáticamente al importar helpers
LoggingHelper.configure_for_development()
