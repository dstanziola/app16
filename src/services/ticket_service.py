"""
Servicio de gestión de tickets.
Implementa la lógica de negocio para generación, registro y consulta de tickets.

Este servicio maneja:
- Generación de tickets de venta y entrada
- Numeración automática consecutiva
- Registro en base de datos
- Búsqueda y reimpresión
- Integración con SalesService/MovementService

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from db.database import get_database_connection

from models.ticket import Ticket, TicketNumberGenerator
from services.sales_service import SalesService
from services.movement_service import MovementService

class TicketService:
    """
    Servicio para gestión de tickets del sistema.
    
    Proporciona funcionalidades para crear, consultar y reimprimir
    tickets de venta y entrada de inventario.
    """
    
    def __init__(self, db_connection=None):
        """
        Inicializar el servicio de tickets.
        
        Args:
            db_connection: Conexión a la base de datos (opcional)
        """
        self.db = db_connection or get_database_connection()
        self.sales_service = SalesService(self.db)
        self.movement_service = MovementService(self.db)
    
    def _obtener_siguiente_numero_ticket(self, ticket_type: str) -> str:
        """
        Obtener el siguiente número de ticket para el tipo especificado.
        
        Args:
            ticket_type: Tipo de ticket ('VENTA' o 'ENTRADA')
            
        Returns:
            Número de ticket formateado
            
        Raises:
            ValueError: Si el tipo de ticket es inválido
        """
        if ticket_type not in Ticket.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de ticket inválido: {ticket_type}. Tipos válidos: {Ticket.TIPOS_VALIDOS}")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar el último número de ticket del tipo especificado
            query = """
                SELECT ticket_number 
                FROM tickets 
                WHERE ticket_type = ? 
                ORDER BY id_ticket DESC 
                LIMIT 1
            """
            
            cursor.execute(query, (ticket_type,))
            resultado = cursor.fetchone()
            
            if resultado is None:
                # Es el primer ticket de este tipo
                ultimo_numero = 0
            else:
                ultimo_ticket_number = resultado[0]
                # Extraer el número secuencial del ticket
                if ticket_type == Ticket.TIPO_VENTA:
                    ultimo_numero = TicketNumberGenerator.extraer_numero_secuencial(
                        ultimo_ticket_number, prefix="V"
                    )
                else:  # ENTRADA
                    ultimo_numero = TicketNumberGenerator.extraer_numero_secuencial(
                        ultimo_ticket_number, prefix="E"
                    )
            
            # Generar el siguiente número
            if ticket_type == Ticket.TIPO_VENTA:
                return TicketNumberGenerator.generar_numero(
                    ticket_type, ultimo_numero, prefix="V"
                )
            else:  # ENTRADA
                return TicketNumberGenerator.generar_numero(
                    ticket_type, ultimo_numero, prefix="E"
                )
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _verificar_ticket_existente_para_venta(self, id_venta: int) -> bool:
        """
        Verificar si ya existe un ticket para la venta especificada.
        
        Args:
            id_venta: ID de la venta
            
        Returns:
            True si ya existe un ticket para esta venta
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket 
                FROM tickets 
                WHERE id_venta = ? 
                LIMIT 1
            """
            
            cursor.execute(query, (id_venta,))
            resultado = cursor.fetchone()
            
            return resultado is not None
            
        finally:
            cursor.close()
    
    def _verificar_ticket_existente_para_movimiento(self, id_movimiento: int) -> bool:
        """
        Verificar si ya existe un ticket para el movimiento especificado.
        
        Args:
            id_movimiento: ID del movimiento
            
        Returns:
            True si ya existe un ticket para este movimiento
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket 
                FROM tickets 
                WHERE id_movimiento = ? 
                LIMIT 1
            """
            
            cursor.execute(query, (id_movimiento,))
            resultado = cursor.fetchone()
            
            return resultado is not None
            
        finally:
            cursor.close()
    
    def _insertar_ticket_en_bd(self, ticket: Ticket) -> int:
        """
        Insertar ticket en la base de datos.
        
        Args:
            ticket: Instancia de ticket a insertar
            
        Returns:
            ID del ticket insertado
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            insert_query = """
                INSERT INTO tickets (
                    ticket_type, ticket_number, id_venta, id_movimiento,
                    generated_at, generated_by, pdf_path, reprint_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                ticket.ticket_type,
                ticket.ticket_number,
                ticket.id_venta,
                ticket.id_movimiento,
                ticket.generated_at,
                ticket.generated_by,
                ticket.pdf_path,
                ticket.reprint_count
            )
            
            cursor.execute(insert_query, values)
            conn.commit()
            
            return cursor.lastrowid
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _row_to_ticket(self, row: tuple) -> Ticket:
        """
        Convertir fila de base de datos a objeto Ticket.
        
        Args:
            row: Tupla con datos de la base de datos
            
        Returns:
            Instancia de Ticket
        """
        generated_at = None
        if row[5]:  # generated_at
            if isinstance(row[5], str):
                generated_at = datetime.fromisoformat(row[5].replace(' ', 'T'))
            else:
                generated_at = row[5]
        
        return Ticket(
            id_ticket=row[0],
            ticket_type=row[1],
            ticket_number=row[2],
            id_venta=row[3],
            id_movimiento=row[4],
            generated_at=generated_at,
            generated_by=row[6],
            pdf_path=row[7],
            reprint_count=row[8] or 0
        )
    
    def generar_ticket_venta(
        self, 
        id_venta: int, 
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> Ticket:
        """
        Generar un ticket para una venta.
        
        Args:
            id_venta: ID de la venta
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF generado (opcional)
            
        Returns:
            Ticket generado
            
        Raises:
            ValueError: Si la venta no existe o ya tiene ticket
        """
        # Verificar que la venta existe
        venta = self.sales_service.obtener_venta_por_id(id_venta)
        if venta is None:
            raise ValueError(f"La venta con ID {id_venta} no existe")
        
        # Verificar que no existe ya un ticket para esta venta
        if self._verificar_ticket_existente_para_venta(id_venta):
            raise ValueError(f"La venta {id_venta} ya tiene un ticket generado")
        
        # Generar número de ticket
        ticket_number = self._obtener_siguiente_numero_ticket(Ticket.TIPO_VENTA)
        
        # Crear instancia de ticket
        ticket = Ticket.crear_ticket_venta(
            ticket_number=ticket_number,
            id_venta=id_venta,
            generated_by=generated_by,
            pdf_path=pdf_path
        )
        
        # Insertar en base de datos
        ticket_id = self._insertar_ticket_en_bd(ticket)
        ticket.id_ticket = ticket_id
        
        return ticket
    
    def generar_ticket_entrada(
        self, 
        id_movimiento: int, 
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> Ticket:
        """
        Generar un ticket para un movimiento de entrada.
        
        Args:
            id_movimiento: ID del movimiento
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF generado (opcional)
            
        Returns:
            Ticket generado
            
        Raises:
            ValueError: Si el movimiento no existe, no es de entrada o ya tiene ticket
        """
        # Verificar que el movimiento existe
        movimiento = self.movement_service.get_movement_by_id(id_movimiento)
        if movimiento is None:
            raise ValueError(f"El movimiento con ID {id_movimiento} no existe")
        
        # Verificar que es un movimiento de entrada
        if movimiento.get('tipo_movimiento') == 'VENTA':
            raise ValueError(f"El movimiento {id_movimiento} no es de entrada de inventario")
        
        # Verificar que no existe ya un ticket para este movimiento
        if self._verificar_ticket_existente_para_movimiento(id_movimiento):
            raise ValueError(f"El movimiento {id_movimiento} ya tiene un ticket generado")
        
        # Generar número de ticket
        ticket_number = self._obtener_siguiente_numero_ticket(Ticket.TIPO_ENTRADA)
        
        # Crear instancia de ticket
        ticket = Ticket.crear_ticket_entrada(
            ticket_number=ticket_number,
            id_movimiento=id_movimiento,
            generated_by=generated_by,
            pdf_path=pdf_path
        )
        
        # Insertar en base de datos
        ticket_id = self._insertar_ticket_en_bd(ticket)
        ticket.id_ticket = ticket_id
        
        return ticket
    
    def generar_ticket_ajuste(
        self, 
        id_movimiento: int, 
        generated_by: str,
        pdf_path: Optional[str] = None
    ) -> Ticket:
        """
        Generar un ticket para un movimiento de ajuste.
        
        Args:
            id_movimiento: ID del movimiento
            generated_by: Usuario que genera el ticket
            pdf_path: Ruta del PDF generado (opcional)
            
        Returns:
            Ticket generado
            
        Raises:
            ValueError: Si el movimiento no existe, no es de ajuste o ya tiene ticket
        """
        # Verificar que el movimiento existe
        movimiento = self.movement_service.get_movement_by_id(id_movimiento)
        if movimiento is None:
            raise ValueError(f"El movimiento con ID {id_movimiento} no existe")
        
        # Verificar que es un movimiento de ajuste
        if movimiento.get('tipo_movimiento') != 'AJUSTE':
            raise ValueError(f"El movimiento {id_movimiento} no es un ajuste de inventario")
        
        # Verificar que no existe ya un ticket para este movimiento
        if self._verificar_ticket_existente_para_movimiento(id_movimiento):
            raise ValueError(f"El movimiento {id_movimiento} ya tiene un ticket generado")
        
        # Generar número de ticket
        ticket_number = f"ADJ-{id_movimiento:06d}"
        
        # Crear instancia de ticket
        ticket = Ticket.crear_ticket_ajuste(
            ticket_number=ticket_number,
            id_movimiento=id_movimiento,
            generated_by=generated_by,
            pdf_path=pdf_path
        )
        
        # Insertar en base de datos
        ticket_id = self._insertar_ticket_en_bd(ticket)
        ticket.id_ticket = ticket_id
        
        return ticket
    
    def obtener_ticket_por_id(self, id_ticket: int) -> Optional[Ticket]:
        """
        Obtener un ticket por su ID.
        
        Args:
            id_ticket: ID del ticket
            
        Returns:
            Ticket encontrado o None si no existe
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE id_ticket = ?
            """
            
            cursor.execute(query, (id_ticket,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_ticket(row)
            
        finally:
            cursor.close()
    
    def obtener_tickets_por_venta(self, id_venta: int) -> List[Ticket]:
        """
        Obtener todos los tickets asociados a una venta.
        
        Args:
            id_venta: ID de la venta
            
        Returns:
            Lista de tickets (incluyendo reimpresiones)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE id_venta = ?
                ORDER BY generated_at ASC
            """
            
            cursor.execute(query, (id_venta,))
            rows = cursor.fetchall()
            
            return [self._row_to_ticket(row) for row in rows]
            
        finally:
            cursor.close()
    
    def obtener_tickets_por_movimiento(self, id_movimiento: int) -> List[Ticket]:
        """
        Obtener todos los tickets asociados a un movimiento.
        
        Args:
            id_movimiento: ID del movimiento
            
        Returns:
            Lista de tickets (incluyendo reimpresiones)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE id_movimiento = ?
                ORDER BY generated_at ASC
            """
            
            cursor.execute(query, (id_movimiento,))
            rows = cursor.fetchall()
            
            return [self._row_to_ticket(row) for row in rows]
            
        finally:
            cursor.close()
    
    def reimprimir_ticket(self, id_ticket: int, generated_by: str) -> Ticket:
        """
        Reimprimir un ticket existente.
        
        Crea una nueva entrada en la base de datos con el mismo número
        pero incrementando el contador de reimpresiones.
        
        Args:
            id_ticket: ID del ticket original
            generated_by: Usuario que solicita la reimpresión
            
        Returns:
            Nuevo ticket con contador incrementado
            
        Raises:
            ValueError: Si el ticket original no existe
        """
        # Obtener el ticket original
        ticket_original = self.obtener_ticket_por_id(id_ticket)
        if ticket_original is None:
            raise ValueError(f"El ticket con ID {id_ticket} no existe")
        
        # Crear nuevo ticket con mismo número pero reprint_count incrementado
        ticket_reimpreso = Ticket(
            ticket_type=ticket_original.ticket_type,
            ticket_number=ticket_original.ticket_number,
            generated_by=generated_by,
            id_venta=ticket_original.id_venta,
            id_movimiento=ticket_original.id_movimiento,
            reprint_count=ticket_original.reprint_count + 1,
            generated_at=datetime.now()
        )
        
        # Insertar en base de datos
        ticket_id = self._insertar_ticket_en_bd(ticket_reimpreso)
        ticket_reimpreso.id_ticket = ticket_id
        
        return ticket_reimpreso
    
    def actualizar_pdf_path(self, id_ticket: int, pdf_path: str) -> bool:
        """
        Actualizar la ruta del PDF de un ticket.
        
        Args:
            id_ticket: ID del ticket
            pdf_path: Nueva ruta del PDF
            
        Returns:
            True si se actualizó correctamente
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            update_query = """
                UPDATE tickets 
                SET pdf_path = ? 
                WHERE id_ticket = ?
            """
            
            cursor.execute(update_query, (pdf_path, id_ticket))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def obtener_tickets_por_fecha(
        self, 
        fecha_inicio: datetime, 
        fecha_fin: datetime
    ) -> List[Ticket]:
        """
        Obtener tickets generados en un rango de fechas.
        
        Args:
            fecha_inicio: Fecha de inicio del rango
            fecha_fin: Fecha de fin del rango
            
        Returns:
            Lista de tickets en el rango especificado
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE generated_at BETWEEN ? AND ?
                ORDER BY generated_at ASC
            """
            
            cursor.execute(query, (fecha_inicio, fecha_fin))
            rows = cursor.fetchall()
            
            return [self._row_to_ticket(row) for row in rows]
            
        finally:
            cursor.close()
    
    def obtener_estadisticas_tickets(self) -> Dict[str, int]:
        """
        Obtener estadísticas de tickets generados.
        
        Returns:
            Diccionario con conteo por tipo y total
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT ticket_type, COUNT(*) as count
                FROM tickets 
                GROUP BY ticket_type
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            estadisticas = {}
            total = 0
            
            for row in rows:
                ticket_type, count = row
                estadisticas[ticket_type] = count
                total += count
            
            estadisticas["total"] = total
            
            return estadisticas
            
        finally:
            cursor.close()
    
    def obtener_ultimo_ticket_por_tipo(self, ticket_type: str) -> Optional[Ticket]:
        """
        Obtener el último ticket generado del tipo especificado.
        
        Args:
            ticket_type: Tipo de ticket ('VENTA' o 'ENTRADA')
            
        Returns:
            Último ticket del tipo o None si no hay ninguno
        """
        if ticket_type not in Ticket.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de ticket inválido: {ticket_type}")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE ticket_type = ?
                ORDER BY id_ticket DESC
                LIMIT 1
            """
            
            cursor.execute(query, (ticket_type,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_ticket(row)
            
        finally:
            cursor.close()
    
    def obtener_tickets_sin_pdf(self) -> List[Ticket]:
        """
        Obtener tickets que no tienen PDF generado.
        
        Returns:
            Lista de tickets sin PDF
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id_ticket, ticket_type, ticket_number, id_venta, id_movimiento,
                       generated_at, generated_by, pdf_path, reprint_count
                FROM tickets 
                WHERE pdf_path IS NULL OR pdf_path = ''
                ORDER BY generated_at ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_ticket(row) for row in rows]
            
        finally:
            cursor.close()
    
    def eliminar_ticket(self, id_ticket: int) -> bool:
        """
        Eliminar un ticket de la base de datos.
        
        NOTA: Esta operación debe usarse con cuidado ya que puede
        afectar la integridad de la numeración.
        
        Args:
            id_ticket: ID del ticket a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            delete_query = "DELETE FROM tickets WHERE id_ticket = ?"
            
            cursor.execute(delete_query, (id_ticket,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
