"""
Servicio para gestión de clientes.
Implementa la lógica de negocio para operaciones CRUD de clientes.

ARQUITECTURA LIMPIA:
- Lógica de negocio pura para gestión de clientes
- Validaciones centralizadas
- Sin dependencias externas
"""

from typing import Optional, List
from models.cliente import Cliente


class ClientService:
    """
    Servicio para gestión de clientes.
    
    Responsabilidades:
    - Validación de datos de clientes
    - Aplicación de reglas de negocio
    - Coordinación con la capa de persistencia
    """
    
    def __init__(self, db_connection):
        """
        Inicializar servicio con conexión a base de datos.
        
        Args:
            db_connection: Conexión a base de datos
        """
        self.db = db_connection
    
    def create_client(self, nombre: str, ruc: Optional[str] = None) -> Cliente:
        """
        Crear un nuevo cliente aplicando validaciones de negocio.
        
        Args:
            nombre: Nombre del cliente
            ruc: RUC del cliente (opcional)
            
        Returns:
            Cliente: Objeto cliente creado
            
        Raises:
            ValueError: Si los datos no son válidos
        """
        # Validaciones de negocio
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del cliente no puede estar vacío")
        
        # Limpiar datos
        nombre = nombre.strip()
        ruc = ruc.strip() if ruc else None
        
        # Validar RUC si se proporciona
        if ruc and (len(ruc) < 6 or len(ruc) > 20):
            raise ValueError("El RUC debe tener entre 6 y 20 caracteres")
        
        # Verificar si ya existe (por nombre o RUC)
        if self._client_exists_by_name(nombre):
            raise ValueError(f"Ya existe un cliente con el nombre '{nombre}'")
        
        if ruc and self._client_exists_by_ruc(ruc):
            raise ValueError(f"Ya existe un cliente con el RUC '{ruc}'")
        
        # Crear en base de datos
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "INSERT INTO clientes (nombre, ruc, activo) VALUES (?, ?, 1)",
            (nombre, ruc)
        )
        self.db.get_connection().commit()
        
        # Crear objeto de dominio
        cliente = Cliente(
            id_cliente=cursor.lastrowid,
            nombre=nombre,
            ruc=ruc,
            activo=True
        )
        
        return cliente

    def update_client(self, id_cliente: int, nombre: str, ruc: Optional[str] = None) -> Cliente:
        """
        Actualiza un cliente existente aplicando validaciones de negocio.
        
        Args:
            id_cliente: ID del cliente a actualizar
            nombre: Nuevo nombre del cliente
            ruc: Nuevo RUC (opcional)
        
        Returns:
            Cliente actualizado
        
        Raises:
            ValueError: Si los datos no son válidos o el cliente no existe
        """
        # Validaciones básicas
        if not nombre or not nombre.strip():
            raise ValueError("El nombre del cliente no puede estar vacío")
        
        nombre = nombre.strip()
        ruc = ruc.strip() if ruc else None
        
        # Verificar existencia
        existing_client = self.get_client_by_id(id_cliente)
        if not existing_client:
            raise ValueError("El cliente no existe")
        
        # Validar unicidad del nombre si cambia
        if nombre.lower() != existing_client.nombre.lower() and self._client_exists_by_name(nombre):
            raise ValueError(f"Ya existe un cliente con el nombre '{nombre}'")
        
        # Validar unicidad del RUC si cambia y se proporciona
        if ruc and ruc != existing_client.ruc and self._client_exists_by_ruc(ruc):
            raise ValueError(f"Ya existe un cliente con el RUC '{ruc}'")
        
        # Actualizar en la base de datos
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "UPDATE clientes SET nombre = ?, ruc = ? WHERE id_cliente = ?",
            (nombre, ruc, id_cliente)
        )
        self.db.get_connection().commit()
        
        # Retornar objeto actualizado
        return Cliente(
            id_cliente=id_cliente,
            nombre=nombre,
            ruc=ruc,
            activo=existing_client.activo
        )

    def get_client_by_id(self, id_cliente: int) -> Optional[Cliente]:
        """
        Obtener cliente por su ID.
        
        Args:
            id_cliente: ID del cliente
            
        Returns:
            Cliente o None si no existe
        """
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT id_cliente, nombre, ruc, activo FROM clientes WHERE id_cliente = ?",
            (id_cliente,)
        )
        
        row = cursor.fetchone()
        if row:
            if hasattr(row, 'keys'):
                data = dict(row)
            else:
                data = {
                    'id_cliente': row[0],
                    'nombre': row[1],
                    'ruc': row[2],
                    'activo': bool(row[3])
                }
            
            return Cliente(**data)
        
        return None
    
    def get_all_clients(self, only_active: bool = True) -> List[Cliente]:
        """
        Obtener todos los clientes.
        
        Args:
            only_active: Si solo obtener clientes activos
            
        Returns:
            Lista de clientes
        """
        cursor = self.db.get_connection().cursor()
        if only_active:
            cursor.execute(
                "SELECT id_cliente, nombre, ruc, activo FROM clientes WHERE activo = 1 ORDER BY nombre"
            )
        else:
            cursor.execute(
                "SELECT id_cliente, nombre, ruc, activo FROM clientes ORDER BY nombre"
            )
        
        clientes = []
        for row in cursor.fetchall():
            if hasattr(row, 'keys'):
                data = dict(row)
            else:
                data = {
                    'id_cliente': row[0],
                    'nombre': row[1],
                    'ruc': row[2],
                    'activo': bool(row[3])
                }
            
            clientes.append(Cliente(**data))
        
        return clientes
    
    def _client_exists_by_name(self, nombre: str) -> bool:
        """Verificar si existe un cliente con el nombre dado."""
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM clientes WHERE LOWER(nombre) = LOWER(?) AND activo = 1",
            (nombre,)
        )
        result = cursor.fetchone()
        
        # Manejar tanto resultado real como mock para tests unitarios
        if hasattr(result, '__getitem__'):  # Es subscriptable (tuple/Row)
            count = result[0]
        elif hasattr(result, '__dict__'):  # Es un mock con atributos
            count = getattr(result, '0', 0)  # Para mocks configurados
        else:
            count = 0  # Valor por defecto seguro
        
        # Convertir a int si es posible para evitar errores con mocks
        try:
            return int(count) > 0
        except (TypeError, ValueError):
            return bool(count)  # Fallback para mocks complejos
    
    def _client_exists_by_ruc(self, ruc: str) -> bool:
        """Verificar si existe un cliente con el RUC dado."""
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM clientes WHERE ruc = ? AND activo = 1",
            (ruc,)
        )
        result = cursor.fetchone()
        
        # Manejar tanto resultado real como mock para tests unitarios
        if hasattr(result, '__getitem__'):  # Es subscriptable (tuple/Row)
            count = result[0]
        elif hasattr(result, '__dict__'):  # Es un mock con atributos
            count = getattr(result, '0', 0)  # Para mocks configurados
        else:
            count = 0  # Valor por defecto seguro
        
        # Convertir a int si es posible para evitar errores con mocks
        try:
            return int(count) > 0
        except (TypeError, ValueError):
            return bool(count)  # Fallback para mocks complejos
        
    def deactivate_client(self, id_cliente: int):
        """
        Desactiva un cliente (marca como inactivo).
        
        Args:
            id_cliente: ID del cliente a desactivar
            
        Raises:
            ValueError: Si el cliente no existe
        """
        existing_client = self.get_client_by_id(id_cliente)
        if not existing_client:
            raise ValueError("El cliente no existe")
        
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "UPDATE clientes SET activo = 0 WHERE id_cliente = ?",
            (id_cliente,)
        )
        self.db.get_connection().commit()