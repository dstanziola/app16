"""
Modelo de datos para Producto.
Representa productos y servicios en el sistema de inventario.

Este archivo fue implementado siguiendo TDD:
- Tests escritos primero en tests/unit/test_models.py
- Implementación mínima para pasar tests (GREEN)
- Refactorización manteniendo tests pasando

Autor: Sistema TDD
Fecha: 2025-05-26
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union


class Producto:
    """
    Modelo para representar un producto o servicio en el inventario.
    
    Un producto puede ser MATERIAL (con stock) o SERVICIO (sin stock).
    Incluye funcionalidades para cálculo de impuestos y totales.
    """
    
    def __init__(
        self, 
        nombre: str,
        id_categoria: int,
        stock: int = 0,
        costo: Union[int, float, Decimal] = 0,
        precio: Union[int, float, Decimal] = 0,
        tasa_impuesto: Union[int, float, Decimal] = 0,
        activo: bool = True,
        id_producto: Optional[int] = None,
        categoria_tipo: Optional[str] = None
    ):
        """
        Inicializar un nuevo producto.
        
        Args:
            nombre: Nombre descriptivo del producto
            id_categoria: ID de la categoría asociada
            stock: Cantidad en inventario (default: 0)
            costo: Costo unitario (default: 0)
            precio: Precio de venta unitario (default: 0)
            tasa_impuesto: Tasa de impuesto en porcentaje (default: 0)
            activo: Si el producto está activo (default: True)
            id_producto: ID único (asignado por la base de datos)
        """
        self.id_producto = id_producto
        self.nombre = nombre
        self.id_categoria = id_categoria
        self.stock = stock
        self.costo = Decimal(str(costo))
        self.precio = Decimal(str(precio))
        self.tasa_impuesto = Decimal(str(tasa_impuesto))
        self.activo = activo
        self.categoria_tipo = categoria_tipo
    
    def calcular_impuesto(self, cantidad: int) -> Decimal:
        """
        Calcular el impuesto para una cantidad específica.
        
        Args:
            cantidad: Cantidad de productos
            
        Returns:
            Monto del impuesto calculado
        """
        subtotal = self.precio * Decimal(str(cantidad))
        impuesto = (subtotal * self.tasa_impuesto) / Decimal('100')
        return impuesto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_subtotal(self, cantidad: int) -> Decimal:
        """
        Calcular el subtotal para una cantidad específica.
        
        Args:
            cantidad: Cantidad de productos
            
        Returns:
            Subtotal (precio * cantidad)
        """
        subtotal = self.precio * Decimal(str(cantidad))
        return subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_total(self, cantidad: int) -> Decimal:
        """
        Calcular el total incluyendo impuestos para una cantidad específica.
        
        Args:
            cantidad: Cantidad de productos
            
        Returns:
            Total (subtotal + impuesto)
        """
        subtotal = self.calcular_subtotal(cantidad)
        impuesto = self.calcular_impuesto(cantidad)
        total = subtotal + impuesto
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def tiene_stock_suficiente(self, cantidad: int) -> bool:
        """
        Verificar si hay stock suficiente para una cantidad.
        
        Args:
            cantidad: Cantidad requerida
            
        Returns:
            True si hay stock suficiente
        """
        return self.stock >= cantidad
    
    def actualizar_stock(self, cantidad: int) -> None:
        """
        Actualizar el stock del producto.
        
        Args:
            cantidad: Cantidad a agregar (positiva) o quitar (negativa)
        """
        self.stock += cantidad
        if self.stock < 0:
            self.stock = 0
    
    def calcular_margen_ganancia(self) -> Decimal:
        """
        Calcular el margen de ganancia como porcentaje.
        
        Returns:
            Margen de ganancia en porcentaje
        """
        if self.costo == 0:
            return Decimal('0')
        
        ganancia = self.precio - self.costo
        margen = (ganancia / self.costo) * Decimal('100')
        return margen.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def es_rentable(self) -> bool:
        """
        Verificar si el producto es rentable (precio > costo).
        
        Returns:
            True si el precio es mayor al costo
        """
        return self.precio > self.costo
    
    def __str__(self) -> str:
        """
        Representación string del producto.
        
        Returns:
            String descriptivo con nombre y precio
        """
        return f"Producto(nombre='{self.nombre}', precio={self.precio})"
    
    def __repr__(self) -> str:
        """
        Representación técnica del producto.
        
        Returns:
            String con todos los atributos principales
        """
        return (f"Producto(id_producto={self.id_producto}, "
                f"nombre='{self.nombre}', id_categoria={self.id_categoria}, "
                f"stock={self.stock}, precio={self.precio})")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos productos por igualdad.
        
        Args:
            other: Otra instancia de Producto
            
        Returns:
            True si son el mismo producto
        """
        if not isinstance(other, Producto):
            return False
        
        # Si ambos tienen ID, comparar por ID
        if self.id_producto is not None and other.id_producto is not None:
            return self.id_producto == other.id_producto
        
        # Si no tienen ID, comparar por nombre y categoría
        return (self.nombre == other.nombre and 
                self.id_categoria == other.id_categoria)
    
    def __hash__(self) -> int:
        """
        Hash del producto para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID o nombre+categoría
        """
        if self.id_producto is not None:
            return hash(('Producto', self.id_producto))
        
        return hash(('Producto', self.nombre, self.id_categoria))
    
    def to_dict(self) -> dict:
        """
        Convertir el producto a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_producto': self.id_producto,
            'nombre': self.nombre,
            'id_categoria': self.id_categoria,
            'stock': self.stock,
            'costo': float(self.costo),
            'precio': float(self.precio),
            'tasa_impuesto': float(self.tasa_impuesto),
            'activo': self.activo
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Producto':
        """
        Crear un producto desde un diccionario.
        
        Args:
            data: Diccionario con los datos del producto
            
        Returns:
            Nueva instancia de Producto
        """
        return cls(
            nombre=data['nombre'],
            id_categoria=data['id_categoria'],
            stock=data.get('stock', 0),
            costo=data.get('costo', 0),
            precio=data.get('precio', 0),
            tasa_impuesto=data.get('tasa_impuesto', 0),
            activo=data.get('activo', True),
            id_producto=data.get('id_producto')
        )
    
    @classmethod
    def crear_material(
        cls,
        nombre: str,
        id_categoria: int,
        stock: int = 0,
        costo: Union[int, float, Decimal] = 0,
        precio: Union[int, float, Decimal] = 0,
        tasa_impuesto: Union[int, float, Decimal] = 0
    ) -> 'Producto':
        """
        Crear un producto tipo MATERIAL con stock.
        
        Args:
            nombre: Nombre del producto
            id_categoria: ID de categoría tipo MATERIAL
            stock: Cantidad inicial en stock
            costo: Costo unitario
            precio: Precio de venta
            tasa_impuesto: Tasa de impuesto
            
        Returns:
            Nueva instancia de Producto para material
        """
        return cls(
            nombre=nombre,
            id_categoria=id_categoria,
            stock=stock,
            costo=costo,
            precio=precio,
            tasa_impuesto=tasa_impuesto
        )
    
    @classmethod
    def crear_servicio(
        cls,
        nombre: str,
        id_categoria: int,
        precio: Union[int, float, Decimal] = 0,
        tasa_impuesto: Union[int, float, Decimal] = 0
    ) -> 'Producto':
        """
        Crear un producto tipo SERVICIO sin stock.
        
        Args:
            nombre: Nombre del servicio
            id_categoria: ID de categoría tipo SERVICIO
            precio: Precio del servicio
            tasa_impuesto: Tasa de impuesto
            
        Returns:
            Nueva instancia de Producto para servicio
        """
        return cls(
            nombre=nombre,
            id_categoria=id_categoria,
            stock=0,  # Los servicios no tienen stock
            costo=0,  # Los servicios no tienen costo de inventario
            precio=precio,
            tasa_impuesto=tasa_impuesto
        )
    
    def obtener_info_resumida(self) -> dict:
        """
        Obtener información resumida del producto.
        
        Returns:
            Diccionario con información básica
        """
        return {
            'id_producto': self.id_producto,
            'nombre': self.nombre,
            'precio': float(self.precio),
            'stock': self.stock,
            'activo': self.activo
        }
    
    def validar_datos(self) -> list:
        """
        Validar los datos del producto.
        
        Returns:
            Lista de errores encontrados (vacía si todo está bien)
        """
        errores = []
        
        if not self.nombre or len(self.nombre.strip()) == 0:
            errores.append("El nombre del producto es requerido")
        
        if self.precio < 0:
            errores.append("El precio no puede ser negativo")
        
        if self.costo < 0:
            errores.append("El costo no puede ser negativo")
        
        if self.stock < 0:
            errores.append("El stock no puede ser negativo")
        
        if self.tasa_impuesto < 0 or self.tasa_impuesto > 100:
            errores.append("La tasa de impuesto debe estar entre 0 y 100")
        
        return errores
    
    def es_valido(self) -> bool:
        """
        Verificar si el producto tiene datos válidos.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_datos()) == 0
    
    def validate_service_stock_restriction(self, categoria) -> bool:
        """
        Validar que la restricción de stock para servicios se cumple.
        
        REQUERIMIENTO: Si en 'Categoria', tipo = 'SERVICIO' entonces 'Stock' = 0
        
        Args:
            categoria: Objeto Categoria asociado al producto
            
        Returns:
            True si la restricción se cumple, False en caso contrario
        """
        if categoria and hasattr(categoria, 'tipo') and categoria.tipo == 'SERVICIO':
            return self.stock == 0
        
        # Para materiales, cualquier stock es válido
        return True
    
    def enforce_service_stock_zero(self, categoria) -> None:
        """
        Forzar que el stock sea 0 si la categoría es SERVICIO.
        
        Args:
            categoria: Objeto Categoria asociado al producto
        """
        if categoria and hasattr(categoria, 'tipo') and categoria.tipo == 'SERVICIO':
            self.stock = 0

    @staticmethod
    def validar_stock(stock):
        """Validación ULTRA-ESTRICTA de stock - CERO tolerancia a negativos"""
        if stock is None:
            raise ValueError("Stock no puede ser None")
            
        try:
            stock_num = float(stock)
        except (ValueError, TypeError):
            raise ValueError(f"Stock debe ser numérico, recibido: {type(stock).__name__}")
        
        if stock_num < 0:
            raise ValueError(f"Stock negativo RECHAZADO: {stock_num}. Debe ser ≥ 0")
        
        return int(max(0, stock_num))
    
    @staticmethod
    def validar_precio(precio, nombre="precio"):
        """Validación de precios"""
        if precio is None or precio < 0:
            raise ValueError(f"{nombre} debe ser mayor o igual a 0")
        return float(precio)
