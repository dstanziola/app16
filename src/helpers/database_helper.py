"""
DatabaseHelper - Patrón FASE 3
Helper para operaciones de base de datos optimizadas y seguras.

RESPONSABILIDADES:
- Ejecución segura de queries con manejo de errores
- Transacciones robustas
- Optimización de performance
- Logging de operaciones críticas
"""

import sqlite3
from typing import Optional, List, Dict, Any, Union
import logging
from contextlib import contextmanager


class DatabaseHelper:
    """Helper para operaciones de base de datos optimizadas."""
    
    def __init__(self, db_connection):
        """
        Inicializar helper con conexión de base de datos.
        
        Args:
            db_connection: Conexión a base de datos
        """
        self.db_connection = db_connection
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def safe_execute(self, query: str, params: tuple = None, 
                    fetch_mode: str = 'one') -> Optional[Union[Dict, List[Dict]]]:
        """
        Ejecutar query de forma segura con manejo de errores.
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query
            fetch_mode: 'one', 'all', 'none' para tipo de retorno
            
        Returns:
            Resultado de la query o None si error
        """
        try:
            cursor = self.db_connection.get_connection().cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_mode == 'one':
                result = cursor.fetchone()
                return self._row_to_dict(result, cursor) if result else None
                
            elif fetch_mode == 'all':
                results = cursor.fetchall()
                return [self._row_to_dict(row, cursor) for row in results]
                
            elif fetch_mode == 'none':
                return None
                
        except Exception as e:
            self.logger.error(f"Error ejecutando query: {query[:100]}... - Error: {e}")
            return None
            
    def safe_execute_with_commit(self, query: str, params: tuple = None) -> Optional[int]:
        """
        Ejecutar query con commit automático.
        
        Args:
            query: Query SQL a ejecutar  
            params: Parámetros para la query
            
        Returns:
            ID del último registro insertado o número de filas afectadas
        """
        try:
            cursor = self.db_connection.get_connection().cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            self.db_connection.get_connection().commit()
            
            # Retornar lastrowid para INSERT o rowcount para UPDATE/DELETE
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            else:
                return cursor.rowcount
                
        except Exception as e:
            self.logger.error(f"Error ejecutando query con commit: {e}")
            self.db_connection.get_connection().rollback()
            return None
            
    @contextmanager
    def transaction(self):
        """
        Context manager para transacciones seguras.
        
        Usage:
            with db_helper.transaction():
                db_helper.safe_execute_with_commit(query1, params1)
                db_helper.safe_execute_with_commit(query2, params2)
        """
        connection = self.db_connection.get_connection()
        try:
            yield connection
            connection.commit()
            self.logger.debug("Transacción completada exitosamente")
        except Exception as e:
            connection.rollback()
            self.logger.error(f"Error en transacción, rollback ejecutado: {e}")
            raise
            
    def execute_batch(self, queries_with_params: List[tuple]) -> bool:
        """
        Ejecutar múltiples queries en una transacción.
        
        Args:
            queries_with_params: Lista de tuplas (query, params)
            
        Returns:
            True si todas las queries fueron exitosas
        """
        try:
            with self.transaction():
                cursor = self.db_connection.get_connection().cursor()
                
                for query, params in queries_with_params:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Error en batch execution: {e}")
            return False
            
    def get_table_info(self, table_name: str) -> Optional[List[Dict]]:
        """
        Obtener información de estructura de tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Lista con información de columnas
        """
        query = f"PRAGMA table_info({table_name})"
        return self.safe_execute(query, fetch_mode='all')
        
    def table_exists(self, table_name: str) -> bool:
        """
        Verificar si una tabla existe.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            True si la tabla existe
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.safe_execute(query, (table_name,))
        return result is not None
        
    def count_records(self, table_name: str, where_clause: str = None, 
                     params: tuple = None) -> int:
        """
        Contar registros en una tabla.
        
        Args:
            table_name: Nombre de la tabla
            where_clause: Cláusula WHERE opcional
            params: Parámetros para WHERE
            
        Returns:
            Número de registros
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        result = self.safe_execute(query, params)
        return result['count'] if result else 0
        
    def record_exists(self, table_name: str, where_clause: str, 
                     params: tuple) -> bool:
        """
        Verificar si existe un registro que cumpla condiciones.
        
        Args:
            table_name: Nombre de la tabla
            where_clause: Condición WHERE
            params: Parámetros para la condición
            
        Returns:
            True si existe el registro
        """
        count = self.count_records(table_name, where_clause, params)
        return count > 0
        
    def get_last_insert_id(self) -> Optional[int]:
        """
        Obtener el ID del último registro insertado.
        
        Returns:
            ID del último registro o None
        """
        try:
            cursor = self.db_connection.get_connection().cursor()
            return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error obteniendo last insert ID: {e}")
            return None
            
    def optimize_database(self) -> bool:
        """
        Optimizar la base de datos (VACUUM, ANALYZE).
        
        Returns:
            True si la optimización fue exitosa
        """
        try:
            cursor = self.db_connection.get_connection().cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            self.logger.info("Base de datos optimizada exitosamente")
            return True
        except Exception as e:
            self.logger.error(f"Error optimizando base de datos: {e}")
            return False
            
    def _row_to_dict(self, row, cursor) -> Optional[Dict]:
        """
        Convertir fila de SQLite a diccionario.
        
        Args:
            row: Fila de resultado
            cursor: Cursor de base de datos
            
        Returns:
            Diccionario con datos de la fila
        """
        if not row:
            return None
            
        try:
            # Si row ya es un Row de SQLite con keys()
            if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                return dict(row)
            
            # Si es una tupla, usar description del cursor
            if hasattr(cursor, 'description') and cursor.description:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            
            # Fallback para casos edge
            return {'data': row}
            
        except Exception as e:
            self.logger.warning(f"Error convirtiendo row a dict: {e}")
            return None
