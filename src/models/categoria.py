"""
Modelo de datos para Categoría.
Representa las categorías de productos/servicios en el sistema de inventario.

Este archivo fue implementado siguiendo TDD:
- Tests escritos primero en tests/unit/test_models.py
- Implementación mínima para pasar tests (GREEN)
- Refactorización manteniendo tests pasando

Autor: Sistema TDD
Fecha: 2025-05-26
"""

from typing import Optional


class Categoria:
    """
    Modelo para representar una categoría de productos o servicios.
    
    Una categoría puede ser de tipo MATERIAL o SERVICIO, lo que determina
    el comportamiento de los productos asociados (ej: manejo de stock).
    """
    
    # Tipos válidos de categoría
    TIPOS_VALIDOS = {'MATERIAL', 'SERVICIO'}
    
    def __init__(self, nombre: str, tipo: str, id_categoria: Optional[int] = None, descripcion: Optional[str] = None, activo: bool = True):
        """
        Inicializar una nueva categoría.
        
        Args:
            nombre: Nombre descriptivo de la categoría
            tipo: Tipo de categoría ('MATERIAL' o 'SERVICIO')
            id_categoria: ID único (asignado por la base de datos)
            descripcion: Descripción opcional de la categoría
            activo: Si la categoría está activa (True por defecto)
            
        Raises:
            ValueError: Si el tipo no es válido
        """
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo '{tipo}' no válido. Debe ser uno de: {', '.join(self.TIPOS_VALIDOS)}")
        
        self.id_categoria = id_categoria
        self.nombre = nombre
        self.tipo = tipo
        self.descripcion = descripcion
        self.activo = activo
    
    def __str__(self) -> str:
        """
        Representación string de la categoría.
        
        Returns:
            String descriptivo con nombre y tipo
        """
        return f"Categoria(nombre='{self.nombre}', tipo='{self.tipo}')"
    
    def __repr__(self) -> str:
        """
        Representación técnica de la categoría.
        
        Returns:
            String con todos los atributos
        """
        return (f"Categoria(id_categoria={self.id_categoria}, "
                f"nombre='{self.nombre}', tipo='{self.tipo}', activo={self.activo})")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos categorías por igualdad.
        
        Args:
            other: Otra instancia de Categoria
            
        Returns:
            True si tienen el mismo ID (si existe) o mismo nombre y tipo
        """
        if not isinstance(other, Categoria):
            return False
        
        # Si ambas tienen ID, comparar por ID
        if self.id_categoria is not None and other.id_categoria is not None:
            return self.id_categoria == other.id_categoria
        
        # Si no tienen ID, comparar por nombre y tipo
        return self.nombre == other.nombre and self.tipo == other.tipo
    
    def __hash__(self) -> int:
        """
        Hash de la categoría para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID (si existe) o nombre y tipo
        """
        if self.id_categoria is not None:
            return hash(('Categoria', self.id_categoria))
        
        return hash(('Categoria', self.nombre, self.tipo))
    
    @classmethod
    def crear_material(cls, nombre: str, id_categoria: Optional[int] = None, descripcion: Optional[str] = None, activo: bool = True) -> 'Categoria':
        """
        Crear una categoría de tipo MATERIAL.
        
        Args:
            nombre: Nombre de la categoría
            id_categoria: ID opcional
            descripcion: Descripción opcional
            activo: Si la categoría está activa (True por defecto)
            
        Returns:
            Nueva instancia de Categoria tipo MATERIAL
        """
        return cls(nombre=nombre, tipo='MATERIAL', id_categoria=id_categoria, descripcion=descripcion, activo=activo)
    
    @classmethod
    def crear_servicio(cls, nombre: str, id_categoria: Optional[int] = None, descripcion: Optional[str] = None, activo: bool = True) -> 'Categoria':
        """
        Crear una categoría de tipo SERVICIO.
        
        Args:
            nombre: Nombre de la categoría
            id_categoria: ID opcional
            descripcion: Descripción opcional
            activo: Si la categoría está activa (True por defecto)
            
        Returns:
            Nueva instancia de Categoria tipo SERVICIO
        """
        return cls(nombre=nombre, tipo='SERVICIO', id_categoria=id_categoria, descripcion=descripcion, activo=activo)
    
    def es_material(self) -> bool:
        """
        Verificar si la categoría es de tipo MATERIAL.
        
        Returns:
            True si es tipo MATERIAL
        """
        return self.tipo == 'MATERIAL'
    
    def es_servicio(self) -> bool:
        """
        Verificar si la categoría es de tipo SERVICIO.
        
        Returns:
            True si es tipo SERVICIO
        """
        return self.tipo == 'SERVICIO'
    
    def to_dict(self) -> dict:
        """
        Convertir la categoría a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_categoria': self.id_categoria,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'descripcion': self.descripcion,
            'activo': self.activo
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Categoria':
        """
        Crear una categoría desde un diccionario.
        
        Args:
            data: Diccionario con los datos de la categoría
            
        Returns:
            Nueva instancia de Categoria
        """
        return cls(
            nombre=data['nombre'],
            tipo=data['tipo'],
            id_categoria=data.get('id_categoria'),
            descripcion=data.get('descripcion'),
            activo=data.get('activo', True)
        )

    @staticmethod
    def validar_tipo(tipo):
        """Validación ULTRA-ESTRICTA de tipo - Rechaza cualquier cosa inválida"""
        if not isinstance(tipo, str):
            raise ValueError(f"Tipo debe ser string, recibido: {type(tipo).__name__}")
        
        tipo_clean = tipo.upper().strip()
        tipos_validos = ['MATERIAL', 'SERVICIO']
        
        if not tipo_clean:
            raise ValueError("Tipo no puede estar vacío")
            
        if tipo_clean not in tipos_validos:
            raise ValueError(f"Tipo '{tipo}' RECHAZADO. Solo acepta: {', '.join(tipos_validos)}")
        
        return tipo_clean
    
    @staticmethod
    def validar_nombre(nombre):
        """Validación de nombre de categoría"""
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("Nombre de categoría inválido")
        return nombre.strip()
    
    def esta_activa(self) -> bool:
        """
        Verificar si la categoría está activa.
        
        Returns:
            True si la categoría está activa
        """
        return self.activo
    
    def activar(self) -> None:
        """
        Activar la categoría.
        """
        self.activo = True
    
    def desactivar(self) -> None:
        """
        Desactivar la categoría.
        """
        self.activo = False
