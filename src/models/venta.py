"""
Modelo de datos para Venta.
Representa una venta/factura en el sistema de inventario.

Este archivo fue implementado siguiendo TDD:
- Tests escritos primero en tests/unit/test_models.py
- Implementación mínima para pasar tests (GREEN)
- Refactorización manteniendo tests pasando

Autor: Sistema TDD
Fecha: 2025-05-26
"""

from typing import Optional, List
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


class Venta:
    """
    Modelo para representar una venta en el sistema.
    
    Una venta puede tener o no cliente asociado y contiene
    información sobre subtotal, impuestos y total.
    """
    
    def __init__(
        self,
        responsable: str,
        id_cliente: Optional[int] = None,
        subtotal: Decimal = Decimal('0'),
        impuestos: Decimal = Decimal('0'),
        total: Decimal = Decimal('0'),
        fecha_venta: Optional[datetime] = None,
        id_venta: Optional[int] = None
    ):
        """
        Inicializar una nueva venta.
        
        Args:
            responsable: Nombre del usuario responsable de la venta
            id_cliente: ID del cliente (opcional)
            subtotal: Subtotal de la venta (default: 0)
            impuestos: Impuestos de la venta (default: 0)
            total: Total de la venta (default: 0)
            fecha_venta: Fecha de la venta (default: ahora)
            id_venta: ID único (asignado por la base de datos)
        """
        self.id_venta = id_venta
        self.fecha_venta = fecha_venta if fecha_venta else datetime.now()
        self.id_cliente = id_cliente
        self.subtotal = Decimal(str(subtotal))
        self.impuestos = Decimal(str(impuestos))
        self.total = Decimal(str(total))
        self.responsable = responsable.strip() if responsable else ""
        
        # Lista de items de la venta (se llenará con detalle_ventas)
        self._items = []
    
    def calcular_total(self) -> None:
        """
        Calcular el total sumando subtotal + impuestos.
        Actualiza el atributo total de la venta.
        """
        self.total = (self.subtotal + self.impuestos).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def agregar_item(self, id_producto: int, cantidad: int, precio_unitario: Decimal, 
                     tasa_impuesto: Decimal = Decimal('0')) -> dict:
        """
        Agregar un item a la venta y recalcular totales.
        
        Args:
            id_producto: ID del producto
            cantidad: Cantidad vendida
            precio_unitario: Precio unitario del producto
            tasa_impuesto: Tasa de impuesto del producto
            
        Returns:
            Diccionario con información del item agregado
        """
        subtotal_item = precio_unitario * Decimal(str(cantidad))
        impuesto_item = (subtotal_item * tasa_impuesto) / Decimal('100')
        
        item = {
            'id_producto': id_producto,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal_item': subtotal_item.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'impuesto_item': impuesto_item.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'tasa_impuesto': tasa_impuesto
        }
        
        self._items.append(item)
        self._recalcular_totales()
        
        return item
    
    def quitar_item(self, index: int) -> bool:
        """
        Quitar un item de la venta por índice.
        
        Args:
            index: Índice del item a quitar
            
        Returns:
            True si se quitó exitosamente
        """
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self._recalcular_totales()
            return True
        return False
    
    def _recalcular_totales(self) -> None:
        """Recalcular subtotal, impuestos y total basado en los items."""
        self.subtotal = sum(item['subtotal_item'] for item in self._items)
        self.impuestos = sum(item['impuesto_item'] for item in self._items)
        self.calcular_total()
    
    def obtener_items(self) -> List[dict]:
        """
        Obtener lista de items de la venta.
        
        Returns:
            Lista de diccionarios con información de cada item
        """
        return self._items.copy()
    
    def cantidad_items(self) -> int:
        """
        Obtener cantidad total de items en la venta.
        
        Returns:
            Número de items diferentes
        """
        return len(self._items)
    
    def cantidad_productos(self) -> int:
        """
        Obtener cantidad total de productos vendidos.
        
        Returns:
            Suma de cantidades de todos los items
        """
        return sum(item['cantidad'] for item in self._items)
    
    def tiene_cliente(self) -> bool:
        """
        Verificar si la venta tiene cliente asociado.
        
        Returns:
            True si tiene cliente
        """
        return self.id_cliente is not None
    
    def es_venta_contado(self) -> bool:
        """
        Determinar si es venta al contado (sin cliente específico).
        
        Returns:
            True si no tiene cliente asociado
        """
        return not self.tiene_cliente()
    
    def obtener_resumen_financiero(self) -> dict:
        """
        Obtener resumen financiero de la venta.
        
        Returns:
            Diccionario con información financiera
        """
        return {
            'subtotal': float(self.subtotal),
            'impuestos': float(self.impuestos),
            'total': float(self.total),
            'cantidad_items': self.cantidad_items(),
            'cantidad_productos': self.cantidad_productos()
        }
    
    def validar_venta(self) -> List[str]:
        """
        Validar los datos de la venta.
        
        Returns:
            Lista de errores encontrados
        """
        errores = []
        
        if not self.responsable or len(self.responsable.strip()) == 0:
            errores.append("El responsable de la venta es requerido")
        
        if self.subtotal < 0:
            errores.append("El subtotal no puede ser negativo")
        
        if self.impuestos < 0:
            errores.append("Los impuestos no pueden ser negativos")
        
        if self.total < 0:
            errores.append("El total no puede ser negativo")
        
        if len(self._items) == 0:
            errores.append("La venta debe tener al menos un item")
        
        # Verificar que total sea consistente con subtotal + impuestos
        total_calculado = self.subtotal + self.impuestos
        if abs(self.total - total_calculado) > Decimal('0.01'):
            errores.append("El total no coincide con subtotal + impuestos")
        
        return errores
    
    def es_valida(self) -> bool:
        """
        Verificar si la venta es válida.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_venta()) == 0
    
    def __str__(self) -> str:
        """
        Representación string de la venta.
        
        Returns:
            String descriptivo con información básica
        """
        cliente_info = f"Cliente {self.id_cliente}" if self.tiene_cliente() else "Venta al contado"
        return f"Venta(total={self.total}, {cliente_info}, responsable='{self.responsable}')"
    
    def __repr__(self) -> str:
        """
        Representación técnica de la venta.
        
        Returns:
            String con todos los atributos principales
        """
        return (f"Venta(id_venta={self.id_venta}, "
                f"fecha_venta='{self.fecha_venta}', id_cliente={self.id_cliente}, "
                f"total={self.total}, responsable='{self.responsable}')")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos ventas por igualdad.
        
        Args:
            other: Otra instancia de Venta
            
        Returns:
            True si son la misma venta
        """
        if not isinstance(other, Venta):
            return False
        
        # Si ambas tienen ID, comparar por ID
        if self.id_venta is not None and other.id_venta is not None:
            return self.id_venta == other.id_venta
        
        # Si no tienen ID, comparar por fecha y responsable
        return (self.fecha_venta == other.fecha_venta and 
                self.responsable == other.responsable)
    
    def __hash__(self) -> int:
        """
        Hash de la venta para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID o fecha+responsable
        """
        if self.id_venta is not None:
            return hash(('Venta', self.id_venta))
        
        return hash(('Venta', self.fecha_venta, self.responsable))
    
    def to_dict(self) -> dict:
        """
        Convertir la venta a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_venta': self.id_venta,
            'fecha_venta': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'id_cliente': self.id_cliente,
            'subtotal': float(self.subtotal),
            'impuestos': float(self.impuestos),
            'total': float(self.total),
            'responsable': self.responsable,
            'items': self._items.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Venta':
        """
        Crear una venta desde un diccionario.
        
        Args:
            data: Diccionario con los datos de la venta
            
        Returns:
            Nueva instancia de Venta
        """
        fecha_venta = None
        if data.get('fecha_venta'):
            fecha_venta = datetime.fromisoformat(data['fecha_venta'])
        
        venta = cls(
            responsable=data['responsable'],
            id_cliente=data.get('id_cliente'),
            subtotal=Decimal(str(data.get('subtotal', 0))),
            impuestos=Decimal(str(data.get('impuestos', 0))),
            total=Decimal(str(data.get('total', 0))),
            fecha_venta=fecha_venta,
            id_venta=data.get('id_venta')
        )
        
        # Restaurar items si existen
        if 'items' in data:
            venta._items = data['items'].copy()
        
        return venta
    
    @classmethod
    def crear_venta_contado(cls, responsable: str) -> 'Venta':
        """
        Crear una venta al contado (sin cliente).
        
        Args:
            responsable: Usuario responsable de la venta
            
        Returns:
            Nueva instancia de Venta sin cliente
        """
        return cls(responsable=responsable, id_cliente=None)
    
    @classmethod
    def crear_venta_credito(cls, responsable: str, id_cliente: int) -> 'Venta':
        """
        Crear una venta a crédito (con cliente).
        
        Args:
            responsable: Usuario responsable de la venta
            id_cliente: ID del cliente
            
        Returns:
            Nueva instancia de Venta con cliente
        """
        return cls(responsable=responsable, id_cliente=id_cliente)
    
    def obtener_info_resumida(self) -> dict:
        """
        Obtener información resumida de la venta.
        
        Returns:
            Diccionario con información básica
        """
        return {
            'id_venta': self.id_venta,
            'fecha_venta': self.fecha_venta.strftime('%Y-%m-%d %H:%M') if self.fecha_venta else None,
            'id_cliente': self.id_cliente,
            'total': float(self.total),
            'responsable': self.responsable,
            'cantidad_items': self.cantidad_items(),
            'tipo_venta': 'Crédito' if self.tiene_cliente() else 'Contado'
        }
    
    def calcular_cambio(self, monto_recibido: Decimal) -> Decimal:
        """
        Calcular cambio a devolver al cliente.
        
        Args:
            monto_recibido: Monto recibido del cliente
            
        Returns:
            Cambio a devolver (puede ser negativo si falta dinero)
        """
        cambio = monto_recibido - self.total
        return cambio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def obtener_fecha_formateada(self, formato: str = '%d/%m/%Y %H:%M') -> str:
        """
        Obtener fecha formateada para mostrar.
        
        Args:
            formato: Formato de fecha (default: DD/MM/YYYY HH:MM)
            
        Returns:
            Fecha formateada como string
        """
        if self.fecha_venta:
            return self.fecha_venta.strftime(formato)
        return "Sin fecha"
    
    def get(self, key: str, default=None):
        """
        Obtener valor de atributo usando interface dict-like.
        
        Proporciona compatibilidad con TicketGenerator y otros componentes
        que esperan poder usar .get() como con diccionarios.
        
        Args:
            key: Nombre del atributo a obtener
            default: Valor por defecto si el atributo no existe
            
        Returns:
            Valor del atributo o default si no existe
            
        Raises:
            None: Método seguro que no lanza excepciones
        """
        try:
            # Usar getattr para acceso seguro a atributos
            return getattr(self, key, default)
        except Exception:
            # En caso de cualquier error, retornar default
            return default
