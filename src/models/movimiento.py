"""
Modelo de datos para Movimiento.
Representa movimientos de inventario (entrada, venta, ajuste) en el sistema.

Este archivo fue implementado siguiendo TDD:
- Tests escritos primero en tests/unit/test_models.py
- Implementación mínima para pasar tests (GREEN)
- Refactorización manteniendo tests pasando

Autor: Sistema TDD
Fecha: 2025-05-26
"""

from typing import Optional
from datetime import datetime


class Movimiento:
    """
    Modelo para representar un movimiento de inventario.
    
    Los movimientos pueden ser de tipo ENTRADA, VENTA o AJUSTE.
    Registran cambios en el stock de productos con información de auditoría.
    """
    
    # Tipos válidos de movimiento
    TIPOS_VALIDOS = {'ENTRADA', 'VENTA', 'AJUSTE'}
    
    def __init__(
        self,
        id_producto: int,
        tipo_movimiento: str,
        cantidad: int,
        responsable: str,
        fecha_movimiento: Optional[datetime] = None,
        id_venta: Optional[int] = None,
        observaciones: Optional[str] = None,
        id_movimiento: Optional[int] = None
    ):
        """
        Inicializar un nuevo movimiento.
        
        Args:
            id_producto: ID del producto afectado
            tipo_movimiento: Tipo de movimiento ('ENTRADA', 'VENTA', 'AJUSTE')
            cantidad: Cantidad del movimiento (positiva o negativa)
            responsable: Usuario responsable del movimiento
            fecha_movimiento: Fecha del movimiento (default: ahora)
            id_venta: ID de venta relacionada (opcional)
            observaciones: Observaciones adicionales (opcional)
            id_movimiento: ID único (asignado por la base de datos)
            
        Raises:
            ValueError: Si el tipo de movimiento no es válido
        """
        if tipo_movimiento not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo movimiento '{tipo_movimiento}' no válido. "
                           f"Debe ser uno de: {', '.join(self.TIPOS_VALIDOS)}")
        
        self.id_movimiento = id_movimiento
        self.id_producto = id_producto
        self.tipo_movimiento = tipo_movimiento
        self.cantidad = cantidad
        self.fecha_movimiento = fecha_movimiento if fecha_movimiento else datetime.now()
        self.responsable = responsable.strip() if responsable else ""
        self.id_venta = id_venta
        self.observaciones = observaciones.strip() if observaciones else None
    
    def es_entrada(self) -> bool:
        """
        Verificar si es un movimiento de entrada.
        
        Returns:
            True si es tipo ENTRADA
        """
        return self.tipo_movimiento == 'ENTRADA'
    
    def es_venta(self) -> bool:
        """
        Verificar si es un movimiento de venta.
        
        Returns:
            True si es tipo VENTA
        """
        return self.tipo_movimiento == 'VENTA'
    
    def es_ajuste(self) -> bool:
        """
        Verificar si es un movimiento de ajuste.
        
        Returns:
            True si es tipo AJUSTE
        """
        return self.tipo_movimiento == 'AJUSTE'
    
    def afecta_stock_positivamente(self) -> bool:
        """
        Determinar si el movimiento incrementa el stock.
        
        Returns:
            True si incrementa el stock
        """
        if self.es_entrada():
            return self.cantidad > 0
        elif self.es_venta():
            return self.cantidad < 0  # Venta con cantidad negativa incrementa stock (devolución)
        else:  # AJUSTE
            return self.cantidad > 0
    
    def afecta_stock_negativamente(self) -> bool:
        """
        Determinar si el movimiento decrementa el stock.
        
        Returns:
            True si decrementa el stock
        """
        return not self.afecta_stock_positivamente()
    
    def obtener_impacto_stock(self) -> int:
        """
        Obtener el impacto neto en el stock.
        
        Returns:
            Cantidad que se suma/resta del stock
        """
        if self.es_entrada():
            return abs(self.cantidad)  # Entrada siempre suma
        elif self.es_venta():
            return -abs(self.cantidad)  # Venta siempre resta
        else:  # AJUSTE
            return self.cantidad  # Ajuste puede ser positivo o negativo
    
    def tiene_venta_asociada(self) -> bool:
        """
        Verificar si el movimiento tiene una venta asociada.
        
        Returns:
            True si tiene venta asociada
        """
        return self.id_venta is not None
    
    def tiene_observaciones(self) -> bool:
        """
        Verificar si el movimiento tiene observaciones.
        
        Returns:
            True si tiene observaciones
        """
        return self.observaciones is not None and len(self.observaciones) > 0
    
    def obtener_descripcion_corta(self) -> str:
        """
        Obtener descripción corta del movimiento.
        
        Returns:
            String descriptivo del movimiento
        """
        signo = "+" if self.afecta_stock_positivamente() else "-"
        cantidad_abs = abs(self.cantidad)
        return f"{self.tipo_movimiento}: {signo}{cantidad_abs}"
    
    def es_movimiento_reciente(self, horas: int = 24) -> bool:
        """
        Verificar si el movimiento es reciente.
        
        Args:
            horas: Número de horas para considerar reciente
            
        Returns:
            True si el movimiento fue en las últimas N horas
        """
        if not self.fecha_movimiento:
            return False
        
        ahora = datetime.now()
        diferencia = ahora - self.fecha_movimiento
        return diferencia.total_seconds() < (horas * 3600)
    
    def validar_datos(self) -> list:
        """
        Validar los datos del movimiento.
        
        Returns:
            Lista de errores encontrados
        """
        errores = []
        
        if not self.responsable or len(self.responsable.strip()) == 0:
            errores.append("El responsable del movimiento es requerido")
        
        if self.tipo_movimiento not in self.TIPOS_VALIDOS:
            errores.append(f"Tipo de movimiento inválido: {self.tipo_movimiento}")
        
        if self.cantidad == 0:
            errores.append("La cantidad no puede ser cero")
        
        if self.id_producto is None or self.id_producto <= 0:
            errores.append("ID del producto debe ser un número positivo")
        
        # Validaciones específicas por tipo
        if self.es_entrada() and self.cantidad < 0:
            errores.append("Las entradas deben tener cantidad positiva")
        
        if self.es_venta() and self.cantidad > 0:
            errores.append("Las ventas deben tener cantidad negativa")
        
        return errores
    
    def es_valido(self) -> bool:
        """
        Verificar si el movimiento tiene datos válidos.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_datos()) == 0
    
    def __str__(self) -> str:
        """
        Representación string del movimiento.
        
        Returns:
            String descriptivo con información básica
        """
        return (f"Movimiento({self.tipo_movimiento}, producto={self.id_producto}, "
                f"cantidad={self.cantidad}, responsable='{self.responsable}')")
    
    def __repr__(self) -> str:
        """
        Representación técnica del movimiento.
        
        Returns:
            String con todos los atributos principales
        """
        return (f"Movimiento(id_movimiento={self.id_movimiento}, "
                f"id_producto={self.id_producto}, tipo_movimiento='{self.tipo_movimiento}', "
                f"cantidad={self.cantidad}, fecha_movimiento='{self.fecha_movimiento}', "
                f"responsable='{self.responsable}')")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos movimientos por igualdad.
        
        Args:
            other: Otra instancia de Movimiento
            
        Returns:
            True si son el mismo movimiento
        """
        if not isinstance(other, Movimiento):
            return False
        
        # Si ambos tienen ID, comparar por ID
        if self.id_movimiento is not None and other.id_movimiento is not None:
            return self.id_movimiento == other.id_movimiento
        
        # Si no tienen ID, comparar por producto, tipo, cantidad y fecha
        return (self.id_producto == other.id_producto and 
                self.tipo_movimiento == other.tipo_movimiento and
                self.cantidad == other.cantidad and
                self.fecha_movimiento == other.fecha_movimiento)
    
    def __hash__(self) -> int:
        """
        Hash del movimiento para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID o atributos clave
        """
        if self.id_movimiento is not None:
            return hash(('Movimiento', self.id_movimiento))
        
        return hash(('Movimiento', self.id_producto, self.tipo_movimiento, 
                    self.cantidad, self.fecha_movimiento))
    
    def to_dict(self) -> dict:
        """
        Convertir el movimiento a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_movimiento': self.id_movimiento,
            'id_producto': self.id_producto,
            'tipo_movimiento': self.tipo_movimiento,
            'cantidad': self.cantidad,
            'fecha_movimiento': self.fecha_movimiento.isoformat() if self.fecha_movimiento else None,
            'responsable': self.responsable,
            'id_venta': self.id_venta,
            'observaciones': self.observaciones
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Movimiento':
        """
        Crear un movimiento desde un diccionario.
        
        Args:
            data: Diccionario con los datos del movimiento
            
        Returns:
            Nueva instancia de Movimiento
        """
        fecha_movimiento = None
        if data.get('fecha_movimiento'):
            fecha_movimiento = datetime.fromisoformat(data['fecha_movimiento'])
        
        return cls(
            id_producto=data['id_producto'],
            tipo_movimiento=data['tipo_movimiento'],
            cantidad=data['cantidad'],
            responsable=data['responsable'],
            fecha_movimiento=fecha_movimiento,
            id_venta=data.get('id_venta'),
            observaciones=data.get('observaciones'),
            id_movimiento=data.get('id_movimiento')
        )
    
    @classmethod
    def crear_entrada(
        cls,
        id_producto: int,
        cantidad: int,
        responsable: str,
        observaciones: Optional[str] = None
    ) -> 'Movimiento':
        """
        Crear un movimiento de entrada al inventario.
        
        Args:
            id_producto: ID del producto
            cantidad: Cantidad a ingresar (debe ser positiva)
            responsable: Usuario responsable
            observaciones: Observaciones opcionales
            
        Returns:
            Nueva instancia de Movimiento tipo ENTRADA
        """
        return cls(
            id_producto=id_producto,
            tipo_movimiento='ENTRADA',
            cantidad=abs(cantidad),  # Asegurar que sea positiva
            responsable=responsable,
            observaciones=observaciones
        )
    
    @classmethod
    def crear_venta(
        cls,
        id_producto: int,
        cantidad: int,
        responsable: str,
        id_venta: int,
        observaciones: Optional[str] = None
    ) -> 'Movimiento':
        """
        Crear un movimiento de venta (salida del inventario).
        
        Args:
            id_producto: ID del producto
            cantidad: Cantidad vendida (se convertirá a negativa)
            responsable: Usuario responsable
            id_venta: ID de la venta asociada
            observaciones: Observaciones opcionales
            
        Returns:
            Nueva instancia de Movimiento tipo VENTA
        """
        return cls(
            id_producto=id_producto,
            tipo_movimiento='VENTA',
            cantidad=-abs(cantidad),  # Asegurar que sea negativa
            responsable=responsable,
            id_venta=id_venta,
            observaciones=observaciones
        )
    
    @classmethod
    def crear_ajuste(
        cls,
        id_producto: int,
        cantidad: int,
        responsable: str,
        observaciones: Optional[str] = None
    ) -> 'Movimiento':
        """
        Crear un movimiento de ajuste de inventario.
        
        Args:
            id_producto: ID del producto
            cantidad: Cantidad del ajuste (positiva o negativa)
            responsable: Usuario responsable
            observaciones: Observaciones del ajuste
            
        Returns:
            Nueva instancia de Movimiento tipo AJUSTE
        """
        return cls(
            id_producto=id_producto,
            tipo_movimiento='AJUSTE',
            cantidad=cantidad,
            responsable=responsable,
            observaciones=observaciones or "Ajuste de inventario"
        )
    
    def obtener_info_resumida(self) -> dict:
        """
        Obtener información resumida del movimiento.
        
        Returns:
            Diccionario con información básica
        """
        return {
            'id_movimiento': self.id_movimiento,
            'id_producto': self.id_producto,
            'tipo_movimiento': self.tipo_movimiento,
            'cantidad': self.cantidad,
            'impacto_stock': self.obtener_impacto_stock(),
            'fecha_movimiento': self.fecha_movimiento.strftime('%Y-%m-%d %H:%M') if self.fecha_movimiento else None,
            'responsable': self.responsable,
            'descripcion': self.obtener_descripcion_corta()
        }
    
    def obtener_fecha_formateada(self, formato: str = '%d/%m/%Y %H:%M') -> str:
        """
        Obtener fecha formateada para mostrar.
        
        Args:
            formato: Formato de fecha (default: DD/MM/YYYY HH:MM)
            
        Returns:
            Fecha formateada como string
        """
        if self.fecha_movimiento:
            return self.fecha_movimiento.strftime(formato)
        return "Sin fecha"
    
    @classmethod
    def filtrar_por_tipo(cls, movimientos: list, tipo_movimiento: str) -> list:
        """
        Filtrar movimientos por tipo.
        
        Args:
            movimientos: Lista de movimientos
            tipo_movimiento: Tipo a filtrar
            
        Returns:
            Lista de movimientos del tipo especificado
        """
        return [mov for mov in movimientos 
                if isinstance(mov, cls) and mov.tipo_movimiento == tipo_movimiento]
    
    @classmethod
    def filtrar_por_producto(cls, movimientos: list, id_producto: int) -> list:
        """
        Filtrar movimientos por producto.
        
        Args:
            movimientos: Lista de movimientos
            id_producto: ID del producto a filtrar
            
        Returns:
            Lista de movimientos del producto especificado
        """
        return [mov for mov in movimientos 
                if isinstance(mov, cls) and mov.id_producto == id_producto]
