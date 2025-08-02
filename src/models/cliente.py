"""
Modelo de datos para Cliente.
Representa clientes en el sistema de inventario.

Este archivo fue implementado siguiendo TDD:
- Tests escritos primero en tests/unit/test_models.py
- Implementación mínima para pasar tests (GREEN)
- Refactorización manteniendo tests pasando

Autor: Sistema TDD
Fecha: 2025-05-26
"""

from typing import Optional
import re


class Cliente:
    """
    Modelo para representar un cliente en el sistema.
    
    Un cliente puede tener o no RUC (Registro Único de Contribuyente).
    Los clientes pueden estar activos o inactivos.
    """
    
    def __init__(
        self, 
        nombre: str,
        ruc: Optional[str] = None,
        activo: bool = True,
        id_cliente: Optional[int] = None
    ):
        """
        Inicializar un nuevo cliente.
        
        Args:
            nombre: Nombre del cliente (requerido)
            ruc: RUC del cliente (opcional, None si no tiene)
            activo: Si el cliente está activo (default: True)
            id_cliente: ID único (asignado por la base de datos)
        """
        self.id_cliente = id_cliente
        self.nombre = nombre.strip() if nombre else ""
        
        # Normalizar RUC: string vacío se convierte en None
        if ruc and ruc.strip():
            self.ruc = ruc.strip()
        else:
            self.ruc = None
            
        self.activo = activo
    
    def tiene_ruc(self) -> bool:
        """
        Verificar si el cliente tiene RUC.
        
        Returns:
            True si tiene RUC válido
        """
        return self.ruc is not None and len(self.ruc) > 0
    
    def es_activo(self) -> bool:
        """
        Verificar si el cliente está activo.
        
        Returns:
            True si está activo
        """
        return self.activo
    
    def activar(self) -> None:
        """Activar el cliente."""
        self.activo = True
    
    def desactivar(self) -> None:
        """Desactivar el cliente."""
        self.activo = False
    
    def actualizar_datos(self, nombre: Optional[str] = None, ruc: Optional[str] = None) -> None:
        """
        Actualizar los datos del cliente.
        
        Args:
            nombre: Nuevo nombre (opcional)
            ruc: Nuevo RUC (opcional)
        """
        if nombre is not None:
            self.nombre = nombre.strip()
        
        if ruc is not None:
            if ruc.strip():
                self.ruc = ruc.strip()
            else:
                self.ruc = None
    
    def validar_ruc_formato(self) -> bool:
        """
        Validar formato básico del RUC.
        
        Returns:
            True si el formato es válido o si no tiene RUC
        """
        if not self.tiene_ruc():
            return True  # No tener RUC es válido
        
        # Validación básica: solo números, guiones y longitud razonable
        if not self.ruc:
            return True
            
        # RUC debe tener entre 8 y 20 caracteres, permitir números y guiones
        patron = r'^[\d\-]{8,20}$'
        return bool(re.match(patron, self.ruc))
    
    def obtener_nombre_corto(self, max_length: int = 25) -> str:
        """
        Obtener versión corta del nombre para mostrar en interfaces.
        
        Args:
            max_length: Longitud máxima del nombre
            
        Returns:
            Nombre truncado si es necesario
        """
        if len(self.nombre) <= max_length:
            return self.nombre
        
        return self.nombre[:max_length - 3] + "..."
    
    def __str__(self) -> str:
        """
        Representación string del cliente.
        
        Returns:
            String descriptivo con nombre y RUC si tiene
        """
        if self.tiene_ruc():
            return f"Cliente(nombre='{self.nombre}', ruc='{self.ruc}')"
        else:
            return f"Cliente(nombre='{self.nombre}', sin_ruc=True)"
    
    def __repr__(self) -> str:
        """
        Representación técnica del cliente.
        
        Returns:
            String con todos los atributos
        """
        return (f"Cliente(id_cliente={self.id_cliente}, "
                f"nombre='{self.nombre}', ruc='{self.ruc}', "
                f"activo={self.activo})")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos clientes por igualdad.
        
        Args:
            other: Otra instancia de Cliente
            
        Returns:
            True si son el mismo cliente
        """
        if not isinstance(other, Cliente):
            return False
        
        # Si ambos tienen ID, comparar por ID
        if self.id_cliente is not None and other.id_cliente is not None:
            return self.id_cliente == other.id_cliente
        
        # Si no tienen ID, comparar por nombre y RUC
        return (self.nombre == other.nombre and 
                self.ruc == other.ruc)
    
    def __hash__(self) -> int:
        """
        Hash del cliente para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID o nombre+RUC
        """
        if self.id_cliente is not None:
            return hash(('Cliente', self.id_cliente))
        
        return hash(('Cliente', self.nombre, self.ruc))
    
    def to_dict(self) -> dict:
        """
        Convertir el cliente a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_cliente': self.id_cliente,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'activo': self.activo
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Cliente':
        """
        Crear un cliente desde un diccionario.
        
        Args:
            data: Diccionario con los datos del cliente
            
        Returns:
            Nueva instancia de Cliente
        """
        return cls(
            nombre=data['nombre'],
            ruc=data.get('ruc'),
            activo=data.get('activo', True),
            id_cliente=data.get('id_cliente')
        )
    
    @classmethod
    def crear_sin_ruc(cls, nombre: str, activo: bool = True) -> 'Cliente':
        """
        Crear un cliente sin RUC.
        
        Args:
            nombre: Nombre del cliente
            activo: Si está activo (default: True)
            
        Returns:
            Nueva instancia de Cliente sin RUC
        """
        return cls(nombre=nombre, ruc=None, activo=activo)
    
    @classmethod
    def crear_con_ruc(cls, nombre: str, ruc: str, activo: bool = True) -> 'Cliente':
        """
        Crear un cliente con RUC.
        
        Args:
            nombre: Nombre del cliente
            ruc: RUC del cliente
            activo: Si está activo (default: True)
            
        Returns:
            Nueva instancia de Cliente con RUC
        """
        return cls(nombre=nombre, ruc=ruc, activo=activo)
    
    def obtener_info_resumida(self) -> dict:
        """
        Obtener información resumida del cliente.
        
        Returns:
            Diccionario con información básica
        """
        return {
            'id_cliente': self.id_cliente,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'tiene_ruc': self.tiene_ruc(),
            'activo': self.activo
        }
    
    def validar_datos(self) -> list:
        """
        Validar los datos del cliente.
        
        Returns:
            Lista de errores encontrados (vacía si todo está bien)
        """
        errores = []
        
        if not self.nombre or len(self.nombre.strip()) == 0:
            errores.append("El nombre del cliente es requerido")
        
        if len(self.nombre) > 60:
            errores.append("El nombre no puede exceder 60 caracteres")
        
        if self.ruc and len(self.ruc) > 20:
            errores.append("El RUC no puede exceder 20 caracteres")
        
        if not self.validar_ruc_formato():
            errores.append("El formato del RUC no es válido")
        
        return errores
    
    def es_valido(self) -> bool:
        """
        Verificar si el cliente tiene datos válidos.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_datos()) == 0
    
    def obtener_etiqueta_display(self) -> str:
        """
        Obtener etiqueta para mostrar en interfaces de usuario.
        
        Returns:
            String formateado para mostrar al usuario
        """
        if self.tiene_ruc():
            return f"{self.nombre} (RUC: {self.ruc})"
        else:
            return f"{self.nombre} (Sin RUC)"
    
    def es_cliente_frecuente(self, min_compras: int = 5) -> bool:
        """
        Determinar si es un cliente frecuente.
        Nota: Esta funcionalidad requiere integración con el módulo de ventas.
        
        Args:
            min_compras: Número mínimo de compras para considerarse frecuente
            
        Returns:
            True si es cliente frecuente (placeholder)
        """
        # TODO: Implementar cuando se tenga acceso a datos de ventas
        return False
    
    @classmethod
    def buscar_por_nombre(cls, clientes: list, nombre_busqueda: str) -> list:
        """
        Buscar clientes por nombre (método de utilidad).
        
        Args:
            clientes: Lista de instancias de Cliente
            nombre_busqueda: Texto a buscar en los nombres
            
        Returns:
            Lista de clientes que coinciden con la búsqueda
        """
        nombre_lower = nombre_busqueda.lower().strip()
        if not nombre_lower:
            return clientes
        
        coincidencias = []
        for cliente in clientes:
            if isinstance(cliente, cls) and nombre_lower in cliente.nombre.lower():
                coincidencias.append(cliente)
        
        return coincidencias
    
    @classmethod
    def buscar_por_ruc(cls, clientes: list, ruc_busqueda: str) -> list:
        """
        Buscar clientes por RUC (método de utilidad).
        
        Args:
            clientes: Lista de instancias de Cliente
            ruc_busqueda: RUC a buscar
            
        Returns:
            Lista de clientes que coinciden con el RUC
        """
        ruc_clean = ruc_busqueda.strip()
        if not ruc_clean:
            return []
        
        coincidencias = []
        for cliente in clientes:
            if (isinstance(cliente, cls) and 
                cliente.tiene_ruc() and 
                ruc_clean in cliente.ruc):
                coincidencias.append(cliente)
        
        return coincidencias
