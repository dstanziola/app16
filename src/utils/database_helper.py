"""
Módulo de ayuda para operaciones de base de datos.
Proporciona utilidades comunes para testing y operaciones.
"""

from typing import Optional, Dict, Any
import sqlite3
from pathlib import Path


class DatabaseHelper:
    """Clase de ayuda para operaciones de base de datos."""
    
    @staticmethod
    def create_test_database(db_path: str) -> sqlite3.Connection:
        """
        Crear base de datos de prueba.
        
        Args:
            db_path: Ruta a la base de datos
            
        Returns:
            Conexión a la base de datos
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def cleanup_test_database(db_path: str):
        """
        Limpiar base de datos de prueba.
        
        Args:
            db_path: Ruta a la base de datos
        """
        db_file = Path(db_path)
        if db_file.exists():
            db_file.unlink()
    
    @staticmethod
    def execute_query(conn: sqlite3.Connection, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """
        Ejecutar consulta SQL.
        
        Args:
            conn: Conexión a la base de datos
            query: Consulta SQL
            params: Parámetros de la consulta
            
        Returns:
            Cursor con resultados
        """
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
        except Exception as e:
            print(f"Error ejecutando query: {e}")
            return None
    
    @staticmethod
    def insert_test_data(conn: sqlite3.Connection, table: str, data: Dict[str, Any]) -> bool:
        """
        Insertar datos de prueba.
        
        Args:
            conn: Conexión a la base de datos
            table: Nombre de la tabla
            data: Datos a insertar
            
        Returns:
            True si la inserción fue exitosa
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            cursor = conn.cursor()
            cursor.execute(query, list(data.values()))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error insertando datos: {e}")
            return False
    
    @staticmethod
    def safe_execute(conn: sqlite3.Connection, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """
        Ejecutar consulta SQL de forma segura con manejo de errores.
        
        Args:
            conn: Conexión a la base de datos
            query: Consulta SQL
            params: Parámetros de la consulta
            
        Returns:
            Cursor con resultados o None si hay error
        """
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            print(f"Error SQL: {e}")
            return None
        except Exception as e:
            print(f"Error ejecutando query: {e}")
            return None
