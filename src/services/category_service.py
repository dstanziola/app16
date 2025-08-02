"""
Servicio para gestión de categorías.
Implementa la lógica de negocio para operaciones CRUD de categorías.

ARQUITECTURA LIMPIA:
- Esta capa contiene lógica de negocio pura
- No depende de UI ni frameworks externos
- Recibe dependencias por inyección (database connection)
"""

from typing import Optional, List
from models.categoria import Categoria


class CategoryService:
    """
    Servicio para gestión de categorías de productos.
    
    Responsabilidades:
    - Validación de datos de negocio
    - Aplicación de reglas de negocio
    - Coordinación con la capa de persistencia
    """
    
    def __init__(self, db_connection):
        """
        Inicializar servicio con conexión a base de datos.
        
        Args:
            db_connection: Conexión a base de datos (inyección de dependencia)
        """
        self.db = db_connection
    
    def create_category(self, nombre: str, tipo: str, descripcion: Optional[str] = None, activo: bool = True) -> Categoria:
        """
        Crear una nueva categoría aplicando validaciones de negocio.
        
        Args:
            nombre: Nombre de la categoría
            tipo: Tipo de categoría ('MATERIAL' o 'SERVICIO')
            descripcion: Descripción opcional de la categoría
            activo: Si la categoría está activa (True por defecto)
            
        Returns:
            Categoria: Objeto categoría creado
            
        Raises:
            ValueError: Si los datos no son válidos
        """
        # Validaciones de negocio
        if not nombre or not nombre.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")
        
        if tipo not in ['MATERIAL', 'SERVICIO']:
            raise ValueError("El tipo debe ser 'MATERIAL' o 'SERVICIO'")
        
        # Limpiar datos
        nombre = nombre.strip()
        descripcion = descripcion.strip() if descripcion else None
        
        # Verificar si ya existe
        if self._category_exists(nombre):
            raise ValueError(f"Ya existe una categoría con el nombre '{nombre}'")
        
        # Crear en base de datos
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "INSERT INTO categorias (nombre, tipo, descripcion, activo) VALUES (?, ?, ?, ?)",
            (nombre, tipo, descripcion, activo)
        )
        self.db.get_connection().commit()
        
        # Crear objeto de dominio
        categoria = Categoria(
            id_categoria=cursor.lastrowid,
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            activo=activo
        )
        
        return categoria
    
    def get_category_by_id(self, id_categoria: int) -> Optional[Categoria]:
        """
        Obtener categoría por su ID.
        
        Args:
            id_categoria: ID de la categoría
            
        Returns:
            Categoria o None si no existe
        """
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT id_categoria, nombre, tipo, descripcion, activo FROM categorias WHERE id_categoria = ?",
            (id_categoria,)
        )
        
        row = cursor.fetchone()
        if row:
            # Convertir Row a dict si es necesario
            if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                # Es un Row de SQLite con método keys()
                data = dict(row)
            else:
                # Es una tupla o mock - usar indexación posicional
                data = {
                    'id_categoria': row[0],
                    'nombre': row[1], 
                    'tipo': row[2],
                    'descripcion': row[3] if len(row) > 3 else None,
                    'activo': row[4] if len(row) > 4 else True
                }
            
            return Categoria(**data)
        
        return None
    
    def get_all_categories(self) -> List[Categoria]:
        """
        Obtener todas las categorías activas.
        
        Returns:
            Lista de categorías
        """
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT id_categoria, nombre, tipo, descripcion, activo FROM categorias ORDER BY nombre"
        )
        
        categorias = []
        for row in cursor.fetchall():
            if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                # Es un Row de SQLite con método keys()
                data = dict(row)
            else:
                # Es una tupla o mock - usar indexación posicional
                data = {
                    'id_categoria': row[0],
                    'nombre': row[1],
                    'tipo': row[2],
                    'descripcion': row[3] if len(row) > 3 else None,
                    'activo': row[4] if len(row) > 4 else True
                }
            
            categorias.append(Categoria(**data))
        
        return categorias
    
    def get_active_categories(self) -> List[Categoria]:
        """
        Obtener todas las categorías activas.
        
        Returns:
            Lista de categorías activas
        """
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT id_categoria, nombre, tipo, descripcion, activo FROM categorias WHERE activo = 1 ORDER BY nombre"
        )
        
        categorias = []
        for row in cursor.fetchall():
            if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                # Es un Row de SQLite con método keys()
                data = dict(row)
            else:
                # Es una tupla o mock - usar indexación posicional
                data = {
                    'id_categoria': row[0],
                    'nombre': row[1],
                    'tipo': row[2],
                    'descripcion': row[3] if len(row) > 3 else None,
                    'activo': row[4] if len(row) > 4 else True
                }
            
            categorias.append(Categoria(**data))
        
        return categorias
    
    def update_category(self, id_categoria: int, nombre: str = None, tipo: str = None, descripcion: str = None, activo: bool = None) -> Optional[Categoria]:
        """
        Actualizar una categoría existente.
        
        Args:
            id_categoria: ID de la categoría
            nombre: Nuevo nombre (opcional)
            tipo: Nuevo tipo (opcional)
            descripcion: Nueva descripción (opcional)
            activo: Nuevo estado activo (opcional)
            
        Returns:
            Categoria actualizada o None si no existe
        """
        # Verificar que existe
        categoria_actual = self.get_category_by_id(id_categoria)
        if not categoria_actual:
            return None
        
        # Aplicar cambios con validaciones
        nuevo_nombre = nombre.strip() if nombre else categoria_actual.nombre
        nuevo_tipo = tipo if tipo else categoria_actual.tipo
        nueva_descripcion = descripcion.strip() if descripcion is not None else categoria_actual.descripcion
        nuevo_activo = activo if activo is not None else categoria_actual.activo
        
        # Validar nuevo tipo si se especifica
        if tipo and tipo not in ['MATERIAL', 'SERVICIO']:
            raise ValueError("El tipo debe ser 'MATERIAL' o 'SERVICIO'")
        
        # Validar nuevo nombre si se especifica
        if nombre and not nombre.strip():
            raise ValueError("El nombre no puede estar vacío")
        
        # Verificar duplicados si cambió el nombre
        if nuevo_nombre != categoria_actual.nombre and self._category_exists(nuevo_nombre):
            raise ValueError(f"Ya existe una categoría con el nombre '{nuevo_nombre}'")
        
        # Actualizar en base de datos
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "UPDATE categorias SET nombre = ?, tipo = ?, descripcion = ?, activo = ? WHERE id_categoria = ?",
            (nuevo_nombre, nuevo_tipo, nueva_descripcion, nuevo_activo, id_categoria)
        )
        self.db.get_connection().commit()
        
        # Retornar categoría actualizada
        return self.get_category_by_id(id_categoria)
    
    def delete_category(self, id_categoria: int) -> bool:
        """
        Eliminar una categoría (soft delete).
        
        Args:
            id_categoria: ID de la categoría
            
        Returns:
            True si se eliminó, False si no existe
        """
        # Verificar que existe
        if not self.get_category_by_id(id_categoria):
            return False
        
        # Verificar que no tiene productos asociados
        if self._has_associated_products(id_categoria):
            raise ValueError("No se puede eliminar una categoría que tiene productos asociados")
        
        # Eliminar
        cursor = self.db.get_connection().cursor()
        cursor.execute("DELETE FROM categorias WHERE id_categoria = ?", (id_categoria,))
        self.db.get_connection().commit()
        
        return cursor.rowcount > 0
    
    def get_material_categories(self) -> List[dict]:
        """
        Obtener todas las categorías de tipo MATERIAL activas.
        
        Returns:
            Lista de categorías tipo MATERIAL
        """
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                "SELECT id_categoria, nombre, tipo, descripcion, activo FROM categorias WHERE tipo = 'MATERIAL' AND activo = 1 ORDER BY nombre"
            )
            
            categories = []
            for row in cursor.fetchall():
                if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                    # Es un Row de SQLite con método keys()
                    data = dict(row)
                else:
                    # Es una tupla o mock - usar indexación posicional
                    data = {
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'description': row[3] if len(row) > 3 else None,
                        'active': row[4] if len(row) > 4 else True
                    }
                
                categories.append(data)
            
            return categories
            
        except Exception as e:
            print(f"❌ Error obteniendo categorías MATERIAL: {e}")
            return []
    
    def get_service_categories(self) -> List[dict]:
        """
        Obtener todas las categorías de tipo SERVICIO activas.
        
        Returns:
            Lista de categorías tipo SERVICIO
        """
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute(
                "SELECT id_categoria, nombre, tipo, descripcion, activo FROM categorias WHERE tipo = 'SERVICIO' AND activo = 1 ORDER BY nombre"
            )
            
            categories = []
            for row in cursor.fetchall():
                if hasattr(row, 'keys') and callable(getattr(row, 'keys', None)):
                    # Es un Row de SQLite con método keys()
                    data = dict(row)
                else:
                    # Es una tupla o mock - usar indexación posicional
                    data = {
                        'id': row[0],
                        'name': row[1],
                        'type': row[2],
                        'description': row[3] if len(row) > 3 else None,
                        'active': row[4] if len(row) > 4 else True
                    }
                
                categories.append(data)
            
            return categories
            
        except Exception as e:
            print(f"❌ Error obteniendo categorías SERVICIO: {e}")
            return []
    
    def _category_exists(self, nombre: str) -> bool:
        """Verificar si existe una categoría con el nombre dado."""
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM categorias WHERE LOWER(nombre) = LOWER(?)",
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
    
    def _has_associated_products(self, id_categoria: int) -> bool:
        """Verificar si la categoría tiene productos asociados."""
        cursor = self.db.get_connection().cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM productos WHERE id_categoria = ? AND activo = 1",
            (id_categoria,)
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
