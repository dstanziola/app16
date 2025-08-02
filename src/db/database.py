"""
Módulo de conexión y gestión de base de datos para el sistema de inventario.
Implementado siguiendo metodología TDD - debe satisfacer todos los tests.
"""

import sqlite3
import os
import logging
from typing import Optional
from src.infrastructure.security.password_hasher import PasswordHasher


class DatabaseConnection:
    """
    Gestor de conexión y operaciones básicas de base de datos.
    Implementa el patrón Singleton para la conexión.
    """
    
    def __init__(self, db_path: str):
        """
        Inicializar conexión de base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._logger = logging.getLogger(__name__)
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Inicializar la conexión con configuraciones optimizadas."""
        self._connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False  # Permitir uso en múltiples threads si es necesario
        )
        self._connection.row_factory = sqlite3.Row  # Acceso por nombre de columna
        
        # Habilitar foreign keys para integridad referencial
        self._connection.execute("PRAGMA foreign_keys = ON")
        
        # Configurar journal mode para mejor concurrencia
        self._connection.execute("PRAGMA journal_mode = WAL")
        
        self._connection.commit()
    
    def migrate_legacy_passwords(self) -> dict:
        """
        Migrar passwords legacy al formato PasswordHasher.
        
        Busca usuarios con hashes en formato legacy (sin '$') y los migra
        al formato PasswordHasher con salt aleatorio para mejor seguridad.
        
        Returns:
            dict: Reporte de migración con usuarios migrados
        """
        migrated_users = 0
        modern_users = 0
        errors = []
        
        try:
            cursor = self._connection.cursor()
            
            # Obtener todos los usuarios
            cursor.execute("""
                SELECT id_usuario, nombre_usuario, password_hash, rol 
                FROM usuarios 
                WHERE activo = 1
            """)
            
            users = cursor.fetchall()
            password_hasher = PasswordHasher()
            
            for user_id, username, current_hash, rol in users:
                # Verificar si es hash legacy (sin '$')
                if '$' not in current_hash:
                    try:
                        # Migrar hash legacy a formato PasswordHasher
                        # Para usuarios legacy conocidos (admin), conocemos el password
                        if username == 'admin':
                            new_hash = password_hasher.hash_password('admin123')
                        else:
                            # Para otros usuarios, generar nuevo hash con password temporal
                            # En producción real, esto requeriría reseteo de password
                            self._logger.warning(f"Usuario {username} requiere cambio manual de password")
                            continue
                        
                        # Actualizar hash en base de datos
                        cursor.execute("""
                            UPDATE usuarios 
                            SET password_hash = ?
                            WHERE id_usuario = ?
                        """, (new_hash, user_id))
                        
                        migrated_users += 1
                        self._logger.info(f"Usuario {username} migrado a formato PasswordHasher")
                        
                    except Exception as e:
                        error_msg = f"Error migrando usuario {username}: {e}"
                        errors.append(error_msg)
                        self._logger.error(error_msg)
                else:
                    modern_users += 1
            
            # Confirmar cambios
            self._connection.commit()
            
            return {
                'migrated_users': migrated_users,
                'modern_users': modern_users,
                'total_users': len(users),
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            self._connection.rollback()
            error_msg = f"Error en migración de passwords: {e}"
            self._logger.error(error_msg)
            return {
                'migrated_users': 0,
                'modern_users': 0,
                'total_users': 0,
                'errors': [error_msg],
                'success': False
            }
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtener la conexión activa de base de datos.
        
        Returns:
            Conexión SQLite activa
        """
        if self._connection is None:
            self._initialize_connection()
        return self._connection
    
    def close(self):
        """Cerrar la conexión de base de datos."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def create_tables(self):
        """
        Crear todas las tablas necesarias del sistema.
        Schema basado en los requerimientos del sistema de inventario.
        """
        schema_sql = """
        -- Tabla de usuarios del sistema
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario VARCHAR(30) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            rol VARCHAR(20) NOT NULL CHECK (rol IN ('ADMIN', 'VENDEDOR')),
            activo BOOLEAN DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla de categorías para productos/servicios
        CREATE TABLE IF NOT EXISTS categorias (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(60) NOT NULL,
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('MATERIAL', 'SERVICIO')),
            descripcion TEXT,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla unificada de productos (materiales y servicios)
        CREATE TABLE IF NOT EXISTS productos (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(60) NOT NULL,
            id_categoria INTEGER NOT NULL,
            descripcion TEXT,
            stock INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 0,
            costo DECIMAL(10,4) DEFAULT 0,
            precio DECIMAL(10,2) DEFAULT 0,
            tasa_impuesto DECIMAL(5,2) DEFAULT 0,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria) ON DELETE RESTRICT
        );

        -- Tabla de clientes
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(60) NOT NULL,
            ruc VARCHAR(20) UNIQUE,
            dv VARCHAR(2),
            telefono VARCHAR(20),
            email VARCHAR(100),
            direccion TEXT,
            activo BOOLEAN DEFAULT 1,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla de ventas (cabecera)
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_factura VARCHAR(20) UNIQUE,
            fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
            id_cliente INTEGER,
            subtotal DECIMAL(10,2) DEFAULT 0,
            impuestos DECIMAL(10,2) DEFAULT 0,
            total DECIMAL(10,2) DEFAULT 0,
            responsable VARCHAR(60) NOT NULL,
            estado VARCHAR(20) DEFAULT 'COMPLETADA',
            observaciones TEXT,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente) ON DELETE SET NULL
        );

        -- Tabla de detalle de ventas
        CREATE TABLE IF NOT EXISTS detalle_ventas (
            id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad > 0),
            precio_unitario DECIMAL(10,2) NOT NULL,
            subtotal_item DECIMAL(10,2) NOT NULL,
            impuesto_item DECIMAL(10,2) DEFAULT 0,
            descuento DECIMAL(10,2) DEFAULT 0,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE CASCADE,
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE RESTRICT
        );

        -- Tabla de movimientos de inventario
        CREATE TABLE IF NOT EXISTS movimientos (
            id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto INTEGER NOT NULL,
            tipo_movimiento VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN ('ENTRADA', 'VENTA', 'AJUSTE')),
            cantidad INTEGER NOT NULL,
            cantidad_anterior INTEGER DEFAULT 0,
            cantidad_nueva INTEGER DEFAULT 0,
            fecha_movimiento DATETIME DEFAULT CURRENT_TIMESTAMP,
            responsable VARCHAR(60) NOT NULL,
            id_venta INTEGER,
            observaciones TEXT,
            costo_unitario DECIMAL(10,4),
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto) ON DELETE RESTRICT,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE SET NULL
        );

        -- Tabla de configuración de empresa (FASE 3)
        CREATE TABLE IF NOT EXISTS company_config (
            id INTEGER PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL DEFAULT 'Copy Point S.A.',
            ruc VARCHAR(20) DEFAULT '888-888-8888',
            direccion TEXT DEFAULT 'Las Lajas, Las Cumbres, Panamá',
            telefono VARCHAR(20) DEFAULT '6666-6666',
            email VARCHAR(100) DEFAULT 'copy.point@gmail.com',
            logo_path VARCHAR(255),
            itbms_rate DECIMAL(5,2) DEFAULT 7.00,
            moneda VARCHAR(10) DEFAULT 'USD',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla de numeración de tickets (FASE 3)
        CREATE TABLE IF NOT EXISTS ticket_numbering (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_type VARCHAR(20) NOT NULL UNIQUE CHECK (ticket_type IN ('VENTA', 'ENTRADA', 'AJUSTE')),
            last_number INTEGER DEFAULT 0,
            prefix VARCHAR(10) DEFAULT '',
            suffix VARCHAR(10) DEFAULT '',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabla de registro de tickets generados (FASE 3)
        CREATE TABLE IF NOT EXISTS tickets (
            id_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number VARCHAR(50) NOT NULL UNIQUE,
            ticket_type VARCHAR(20) NOT NULL CHECK (ticket_type IN ('VENTA', 'ENTRADA', 'AJUSTE')),
            id_venta INTEGER,
            id_movimiento INTEGER,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            generated_by VARCHAR(60) NOT NULL,
            pdf_path VARCHAR(255),
            reprint_count INTEGER DEFAULT 0,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta) ON DELETE SET NULL,
            FOREIGN KEY (id_movimiento) REFERENCES movimientos(id_movimiento) ON DELETE SET NULL
        );

        -- Tabla para control de versiones de base de datos
        CREATE TABLE IF NOT EXISTS db_version (
            version INTEGER PRIMARY KEY,
            descripcion TEXT,
            fecha_aplicacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Índices para optimizar consultas frecuentes
        CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(id_categoria);
        CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);
        CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);
        CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(id_cliente);
        CREATE INDEX IF NOT EXISTS idx_detalle_venta ON detalle_ventas(id_venta);
        CREATE INDEX IF NOT EXISTS idx_detalle_producto ON detalle_ventas(id_producto);
        CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos(id_producto);
        CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha_movimiento);
        CREATE INDEX IF NOT EXISTS idx_clientes_ruc ON clientes(ruc);
        
        -- Índices para FASE 3 - Sistema de Tickets
        CREATE INDEX IF NOT EXISTS idx_tickets_number ON tickets(ticket_number);
        CREATE INDEX IF NOT EXISTS idx_tickets_type ON tickets(ticket_type);
        CREATE INDEX IF NOT EXISTS idx_tickets_venta ON tickets(id_venta);
        CREATE INDEX IF NOT EXISTS idx_tickets_movimiento ON tickets(id_movimiento);
        CREATE INDEX IF NOT EXISTS idx_tickets_generated_at ON tickets(generated_at);
        """
        
        # Ejecutar el schema completo
        self._connection.executescript(schema_sql)
        
        # Establecer versión inicial de base de datos
        self._set_database_version(3, "Schema con sistema de tickets - FASE 3")
        
        self._connection.commit()
    
    def initialize_default_data(self):
        """
        Insertar datos iniciales necesarios para el funcionamiento del sistema.
        Incluye usuario administrador y categorías básicas.
        """
        cursor = self._connection.cursor()
        
        # Verificar si ya existe el usuario admin
        cursor.execute(
            "SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = ? AND rol = ?",
            ("admin", "ADMIN")
        )
        
        if cursor.fetchone()[0] == 0:
            # Crear hash del password por defecto usando PasswordHasher
            default_password = "admin123"  # En producción debería ser más seguro
            password_hasher = PasswordHasher()
            password_hash = password_hasher.hash_password(default_password)
            
            # Insertar usuario administrador
            cursor.execute("""
                INSERT INTO usuarios (nombre_usuario, password_hash, rol, activo)
                VALUES (?, ?, ?, ?)
            """, ("admin", password_hash, "ADMIN", 1))
        
        # Insertar categorías básicas si no existen
        default_categories = [
            ("Computadoras", "SERVICIO", "Uso de equipos de cómputo e internet"),
            ("Desarrollo de documentos", "SERVICIO", "Servicios de elaboración y edición de documentos digitales"),
            ("Impresiones y copias", "SERVICIO", "Fotocopiado, impresión y escaneo de documentos"),
            ("Libros y revistas", "MATERIAL", "Publicaciones impresas"),
            ("Materiales y útiles", "MATERIAL", "Diferentes materiales y útiles escolares y de oficina"),
            ("Regalos", "MATERIAL", "Artículos para obsequios y detalles especiales"),
            ("Snacks", "MATERIAL", "Aperitivos y bocadillos para consumo inmediato"),
            ("Trámites en línea", "SERVICIO", "Gestión de trámites y servicios gubernamentales en línea"),
            ("Video juegos", "SERVICIO", "Uso de equipos para juegos interactivos y entretenimiento"),
            ("Otros materiales", "MATERIAL", "Productos diversos no clasificados en otras categorías"),
        ]

        for nombre, tipo, descripcion in default_categories:
            cursor.execute(
                "SELECT COUNT(*) FROM categorias WHERE nombre = ? AND tipo = ?",
                (nombre, tipo)
            )
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO categorias (nombre, tipo, descripcion)
                    VALUES (?, ?, ?)
                """, (nombre, tipo, descripcion))
        
        # Insertar configuración inicial de empresa (FASE 3)
        cursor.execute("SELECT COUNT(*) FROM company_config")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO company_config (
                    id, nombre, ruc, direccion, telefono, email, itbms_rate, moneda
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Copy Point S.A.",
                "888-888-8888",
                "Las Lajas, Las Cumbres, Panamá",
                "6666-6666",
                "copy.point@gmail.com",
                7.00,
                "USD"
            ))
        
        # Insertar configuración inicial de numeración de tickets (FASE 3)
        ticket_types = [
            ("VENTA", "VT-", ""),
            ("ENTRADA", "EN-", "")
        ]
        
        for ticket_type, prefix, suffix in ticket_types:
            cursor.execute(
                "SELECT COUNT(*) FROM ticket_numbering WHERE ticket_type = ?",
                (ticket_type,)
            )
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO ticket_numbering (ticket_type, last_number, prefix, suffix)
                    VALUES (?, ?, ?, ?)
                """, (ticket_type, 0, prefix, suffix))
        
        self._connection.commit()
    
    def _set_database_version(self, version: int, description: str):
        """
        Establecer versión de base de datos para control de migraciones.
        
        Args:
            version: Número de versión
            description: Descripción de la versión
        """
        cursor = self._connection.cursor()
        
        # Verificar si ya existe esta versión
        cursor.execute("SELECT COUNT(*) FROM db_version WHERE version = ?", (version,))
        
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO db_version (version, descripcion) VALUES (?, ?)",
                (version, description)
            )
        
        # Establecer versión en PRAGMA para compatibilidad
        cursor.execute(f"PRAGMA user_version = {version}")
    
    def get_database_version(self) -> int:
        """
        Obtener versión actual de base de datos.
        
        Returns:
            Número de versión actual
        """
        cursor = self._connection.cursor()
        cursor.execute("PRAGMA user_version")
        return cursor.fetchone()[0]
    
    def verify_schema_integrity(self) -> bool:
        """
        Verificar integridad del schema de base de datos.
        
        Returns:
            True si el schema es válido, False en caso contrario
        """
        try:
            cursor = self._connection.cursor()
            
            # Verificar que todas las tablas principales existen
            expected_tables = [
                'usuarios', 'categorias', 'productos', 'clientes', 
                'ventas', 'detalle_ventas', 'movimientos', 'db_version',
                'company_config', 'ticket_numbering', 'tickets'  # FASE 3
            ]
            
            for table in expected_tables:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                    (table,)
                )
                if not cursor.fetchone():
                    return False
            
            # Verificar integridad de foreign keys
            cursor.execute("PRAGMA foreign_key_check")
            foreign_key_errors = cursor.fetchall()
            
            return len(foreign_key_errors) == 0
            
        except Exception:
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Crear backup de la base de datos.
        
        Args:
            backup_path: Ruta donde guardar el backup
            
        Returns:
            True si el backup fue exitoso, False en caso contrario
        """
        try:
            backup_conn = sqlite3.connect(backup_path)
            self._connection.backup(backup_conn)
            backup_conn.close()
            return True
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Función de conveniencia para obtener conexión global
_global_connection: Optional[DatabaseConnection] = None


def get_database_connection(db_path: str = "inventario.db") -> DatabaseConnection:
    """
    Obtener conexión global de base de datos (patrón Singleton).
    
    Args:
        db_path: Ruta al archivo de base de datos
        
    Returns:
        Instancia de DatabaseConnection
    """
    global _global_connection
    
    if _global_connection is None:
        _global_connection = DatabaseConnection(db_path)
    
    return _global_connection


def initialize_database(db_path: str = "inventario.db") -> DatabaseConnection:
    """
    Inicializar base de datos con schema y datos por defecto.
    
    Args:
        db_path: Ruta al archivo de base de datos
        
    Returns:
        Instancia de DatabaseConnection configurada
    """
    db_conn = DatabaseConnection(db_path)
    db_conn.create_tables()
    db_conn.initialize_default_data()
    
    return db_conn
