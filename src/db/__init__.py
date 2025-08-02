"""
Módulo DB - Capa de Infraestructura de Datos

Este módulo contiene toda la lógica de acceso a datos y persistencia
siguiendo el patrón Repository y principios de Clean Architecture.

Componentes principales:
- database: Gestión de conexiones y configuración
- repositories: Implementaciones concretas de repositorios
- migrations: Sistema de migración de esquemas
- connection: Pool de conexiones y gestión

Tecnología:
- SQLite para desarrollo y pruebas
- PostgreSQL preparado para producción
- ORM propio ligero
- Sistema de migraciones automático

Fecha: 2025-07-17
Estado: P03 - Corrección crítica importaciones
"""

from .database import get_database_connection, initialize_database, DatabaseConnection

__version__ = '2.0.0'
__description__ = 'Capa de Infraestructura de Datos'

# Exportar componentes principales
__all__ = [
    'get_database_connection',
    'initialize_database', 
    'DatabaseConnection'
]

# Configuración de base de datos por defecto
DEFAULT_DB_CONFIG = {
    'type': 'sqlite',
    'name': 'inventario.db',
    'host': 'localhost',
    'port': 5432,
    'timeout': 30,
    'pool_size': 5
}

# Configuración de migraciones
MIGRATION_CONFIG = {
    'auto_migrate': True,
    'backup_before_migrate': True,
    'migration_table': 'schema_migrations',
    'migration_dir': 'migrations'
}
