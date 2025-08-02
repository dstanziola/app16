"""
Modelo de datos para Ticket.
Representa tickets de venta y entrada en el sistema de inventario.

Este archivo implementa el modelo siguiendo TDD:
- Estructurado para pasar tests unitarios
- Validaciones robustas
- Cálculos automáticos de numeración

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP


class Ticket:
    """
    Modelo para representar un ticket de venta o entrada.
    
    Los tickets documentan transacciones del sistema y permiten
    generar documentos PDF para impresión.
    """
    
    # Tipos válidos de ticket
    TIPO_VENTA = "VENTA"
    TIPO_ENTRADA = "ENTRADA"
    TIPO_AJUSTE = "AJUSTE"
    TIPOS_VALIDOS = [TIPO_VENTA, TIPO_ENTRADA, TIPO_AJUSTE]
    
    def __init__(
        self,
        ticket_type: str,
        ticket_number: str,
        generated_by: str,
        id_venta: Optional[int] = None,
        id_movimiento: Optional[int] = None,
        pdf_path: Optional[str] = None,
        generated_at: Optional[datetime] = None,
        id_ticket: Optional[int] = None,
        reprint_count: int = 0
    ):
        """
        Inicializar un nuevo ticket.
        
        Args:
            ticket_type: Tipo de ticket ('VENTA' o 'ENTRADA')
            ticket_number: Número único del ticket
            generated_by: Usuario que generó el ticket
            id_venta: ID de venta asociada (para tickets de venta)
            id_movimiento: ID de movimiento asociado (para tickets de entrada)
            pdf_path: Ruta del archivo PDF generado
            generated_at: Fecha/hora de generación
            id_ticket: ID único del ticket
            reprint_count: Número de reimpresiones
        """
        self.id_ticket = id_ticket
        self.ticket_type = ticket_type
        self.ticket_number = ticket_number
        self.id_venta = id_venta
        self.id_movimiento = id_movimiento
        self.generated_at = generated_at or datetime.now()
        self.generated_by = generated_by
        self.pdf_path = pdf_path
        self.reprint_count = reprint_count
        
        # Validar datos en la inicialización
        self._validar_datos_iniciales()
    
    def _validar_datos_iniciales(self) -> None:
        """
        Validar datos básicos durante la inicialización.
        
        Raises:
            ValueError: Si los datos no son válidos
        """
        errores = self.validar_datos()
        if errores:
            raise ValueError(f"Datos del ticket no válidos: {', '.join(errores)}")
    
    def validar_datos(self) -> list:
        """
        Validar todos los datos del ticket.
        
        Returns:
            Lista de errores encontrados (vacía si todo está bien)
        """
        errores = []
        
        # Validar tipo de ticket
        if not self.ticket_type or self.ticket_type not in self.TIPOS_VALIDOS:
            errores.append(f"Tipo de ticket debe ser uno de: {', '.join(self.TIPOS_VALIDOS)}")
        
        # Validar número de ticket
        if not self.ticket_number or len(self.ticket_number.strip()) == 0:
            errores.append("El número de ticket es requerido")
        
        # Validar usuario generador
        if not self.generated_by or len(self.generated_by.strip()) == 0:
            errores.append("El usuario generador es requerido")
        
        # Validar asociaciones según tipo
        if self.ticket_type == self.TIPO_VENTA:
            if not self.id_venta:
                errores.append("Ticket de venta debe tener id_venta asociado")
            if self.id_movimiento:
                errores.append("Ticket de venta no debe tener id_movimiento")
                
        elif self.ticket_type == self.TIPO_ENTRADA:
            if not self.id_movimiento:
                errores.append("Ticket de entrada debe tener id_movimiento asociado")
            if self.id_venta:
                errores.append("Ticket de entrada no debe tener id_venta")
                
        elif self.ticket_type == self.TIPO_AJUSTE:
            if not self.id_movimiento:
                errores.append("Ticket de ajuste debe tener id_movimiento asociado")
            if self.id_venta:
                errores.append("Ticket de ajuste no debe tener id_venta")
        
        # Validar contador de reimpresiones
        if self.reprint_count < 0:
            errores.append("El contador de reimpresiones no puede ser negativo")
        
        return errores
    
    def es_valido(self) -> bool:
        """
        Verificar si el ticket tiene datos válidos.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_datos()) == 0
    
    def es_ticket_venta(self) -> bool:
        """
        Verificar si es un ticket de venta.
        
        Returns:
            True si es ticket de venta
        """
        return self.ticket_type == self.TIPO_VENTA
    
    def es_ticket_entrada(self) -> bool:
        """
        Verificar si es un ticket de entrada.
        
        Returns:
            True si es ticket de entrada
        """
        return self.ticket_type == self.TIPO_ENTRADA
    
    def es_ticket_ajuste(self) -> bool:
        """
        Verificar si es un ticket de ajuste.
        
        Returns:
            True si es ticket de ajuste
        """
        return self.ticket_type == self.TIPO_AJUSTE
    
    def incrementar_reimpresiones(self) -> None:
        """
        Incrementar el contador de reimpresiones.
        """
        self.reprint_count += 1
    
    def tiene_pdf_generado(self) -> bool:
        """
        Verificar si el ticket tiene un PDF generado.
        
        Returns:
            True si hay ruta de PDF configurada
        """
        return bool(self.pdf_path and len(self.pdf_path.strip()) > 0)
    
    def establecer_pdf_path(self, pdf_path: str) -> None:
        """
        Establecer la ruta del archivo PDF generado.
        
        Args:
            pdf_path: Ruta completa al archivo PDF
        """
        if not pdf_path or len(pdf_path.strip()) == 0:
            raise ValueError("La ruta del PDF no puede estar vacía")
        
        self.pdf_path = pdf_path.strip()
    
    def obtener_descripcion_tipo(self) -> str:
        """
        Obtener descripción legible del tipo de ticket.
        
        Returns:
            Descripción del tipo de ticket
        """
        if self.ticket_type == self.TIPO_VENTA:
            return "Ticket de Venta"
        elif self.ticket_type == self.TIPO_ENTRADA:
            return "Ticket de Entrada de Inventario"
        elif self.ticket_type == self.TIPO_AJUSTE:
            return "Ticket de Ajuste de Inventario"
        else:
            return f"Ticket {self.ticket_type}"
    
    def obtener_fecha_formateada(self) -> str:
        """
        Obtener fecha de generación formateada.
        
        Returns:
            Fecha formateada como string
        """
        return self.generated_at.strftime("%d/%m/%Y %H:%M:%S")
    
    def obtener_fecha_solo_dia(self) -> str:
        """
        Obtener solo la fecha (sin hora) formateada.
        
        Returns:
            Fecha sin hora como string
        """
        return self.generated_at.strftime("%d/%m/%Y")
    
    def obtener_hora_formateada(self) -> str:
        """
        Obtener solo la hora formateada.
        
        Returns:
            Hora formateada como string
        """
        return self.generated_at.strftime("%H:%M:%S")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir el ticket a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'id_ticket': self.id_ticket,
            'ticket_type': self.ticket_type,
            'ticket_number': self.ticket_number,
            'id_venta': self.id_venta,
            'id_movimiento': self.id_movimiento,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'generated_by': self.generated_by,
            'pdf_path': self.pdf_path,
            'reprint_count': self.reprint_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticket':
        """
        Crear un ticket desde un diccionario.
        
        Args:
            data: Diccionario con los datos del ticket
            
        Returns:
            Nueva instancia de Ticket
        """
        generated_at = None
        if data.get('generated_at'):
            if isinstance(data['generated_at'], str):
                generated_at = datetime.fromisoformat(data['generated_at'])
            elif isinstance(data['generated_at'], datetime):
                generated_at = data['generated_at']
        
        return cls(
            ticket_type=data['ticket_type'],
            ticket_number=data['ticket_number'],
            generated_by=data['generated_by'],
            id_venta=data.get('id_venta'),
            id_movimiento=data.get('id_movimiento'),
            pdf_path=data.get('pdf_path'),
            generated_at=generated_at,
            id_ticket=data.get('id_ticket'),
            reprint_count=data.get('reprint_count', 0)
        )
    
    @classmethod
    def crear_ticket_venta(
        cls,
        ticket_number: str,
        id_venta: int,
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> 'Ticket':
        """
        Crear un ticket de venta.
        
        Args:
            ticket_number: Número único del ticket
            id_venta: ID de la venta asociada
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF (opcional)
            
        Returns:
            Nueva instancia de Ticket para venta
        """
        return cls(
            ticket_type=cls.TIPO_VENTA,
            ticket_number=ticket_number,
            generated_by=generated_by,
            id_venta=id_venta,
            pdf_path=pdf_path
        )
    
    @classmethod
    def crear_ticket_entrada(
        cls,
        ticket_number: str,
        id_movimiento: int,
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> 'Ticket':
        """
        Crear un ticket de entrada de inventario.
        
        Args:
            ticket_number: Número único del ticket
            id_movimiento: ID del movimiento asociado
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF (opcional)
            
        Returns:
            Nueva instancia de Ticket para entrada
        """
        return cls(
            ticket_type=cls.TIPO_ENTRADA,
            ticket_number=ticket_number,
            generated_by=generated_by,
            id_movimiento=id_movimiento,
            pdf_path=pdf_path
        )
    
    @classmethod
    def crear_ticket_ajuste(
        cls,
        ticket_number: str,
        id_movimiento: int,
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> 'Ticket':
        """
        Crear un ticket de ajuste de inventario.
        
        Args:
            ticket_number: Número único del ticket
            id_movimiento: ID del movimiento asociado
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF (opcional)
            
        Returns:
            Nueva instancia de Ticket para ajuste
        """
        return cls(
            ticket_type=cls.TIPO_AJUSTE,
            ticket_number=ticket_number,
            generated_by=generated_by,
            id_movimiento=id_movimiento,
            pdf_path=pdf_path
        )
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Obtener resumen del ticket para mostrar en listas.
        
        Returns:
            Diccionario con información resumida
        """
        return {
            'id_ticket': self.id_ticket,
            'numero': self.ticket_number,
            'tipo': self.obtener_descripcion_tipo(),
            'fecha': self.obtener_fecha_formateada(),
            'generado_por': self.generated_by,
            'reimpresiones': self.reprint_count,
            'tiene_pdf': self.tiene_pdf_generado()
        }
    
    def __str__(self) -> str:
        """
        Representación string del ticket.
        
        Returns:
            String descriptivo con número y tipo
        """
        return f"Ticket(numero='{self.ticket_number}', tipo='{self.ticket_type}')"
    
    def __repr__(self) -> str:
        """
        Representación técnica del ticket.
        
        Returns:
            String con todos los atributos principales
        """
        return (f"Ticket(id_ticket={self.id_ticket}, "
                f"ticket_number='{self.ticket_number}', "
                f"ticket_type='{self.ticket_type}', "
                f"generated_by='{self.generated_by}')")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos tickets por igualdad.
        
        Args:
            other: Otra instancia de Ticket
            
        Returns:
            True si son el mismo ticket
        """
        if not isinstance(other, Ticket):
            return False
        
        # Si ambos tienen ID, comparar por ID
        if self.id_ticket is not None and other.id_ticket is not None:
            return self.id_ticket == other.id_ticket
        
        # Si no tienen ID, comparar por número de ticket
        return self.ticket_number == other.ticket_number
    
    def __hash__(self) -> int:
        """
        Hash del ticket para usar en conjuntos y diccionarios.
        
        Returns:
            Hash basado en ID o número de ticket
        """
        if self.id_ticket is not None:
            return hash(('Ticket', self.id_ticket))
        
        return hash(('Ticket', self.ticket_number))


class TicketNumberGenerator:
    """
    Generador de números de tickets únicos.
    
    Maneja la numeración secuencial con prefijos y sufijos
    según la configuración de la base de datos.
    """
    
    @staticmethod
    def generar_numero(
        ticket_type: str,
        ultimo_numero: int,
        prefix: str = "",
        suffix: str = ""
    ) -> str:
        """
        Generar el siguiente número de ticket.
        
        Args:
            ticket_type: Tipo de ticket ('VENTA' o 'ENTRADA')
            ultimo_numero: Último número usado
            prefix: Prefijo del ticket
            suffix: Sufijo del ticket
            
        Returns:
            Número de ticket formateado
        """
        if ticket_type not in Ticket.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de ticket inválido: {ticket_type}")
        
        nuevo_numero = ultimo_numero + 1
        numero_formateado = f"{prefix}{nuevo_numero:06d}{suffix}"
        
        return numero_formateado
    
    @staticmethod
    def extraer_numero_secuencial(ticket_number: str, prefix: str = "", suffix: str = "") -> int:
        """
        Extraer el número secuencial de un número de ticket.
        
        Args:
            ticket_number: Número completo del ticket
            prefix: Prefijo a remover
            suffix: Sufijo a remover
            
        Returns:
            Número secuencial extraído
        """
        # Remover prefijo y sufijo
        numero_limpio = ticket_number
        
        if prefix and numero_limpio.startswith(prefix):
            numero_limpio = numero_limpio[len(prefix):]
        
        if suffix and numero_limpio.endswith(suffix):
            numero_limpio = numero_limpio[:-len(suffix)]
        
        try:
            return int(numero_limpio)
        except ValueError:
            return 0
    
    @staticmethod
    def validar_formato_numero(ticket_number: str) -> bool:
        """
        Validar que el número de ticket tenga un formato válido.
        
        Args:
            ticket_number: Número de ticket a validar
            
        Returns:
            True si el formato es válido
        """
        if not ticket_number or len(ticket_number.strip()) == 0:
            return False
        
        # Debe tener al menos 1 carácter
        if len(ticket_number) < 1:
            return False
        
        # No debe contener caracteres especiales problemáticos
        caracteres_invalidos = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in caracteres_invalidos:
            if char in ticket_number:
                return False
        
        return True
