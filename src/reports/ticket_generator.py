"""
Generador de PDFs para tickets.
Implementa la generación de documentos PDF para tickets de venta y entrada.

Este módulo maneja:
- Templates especializados para tickets
- Formato compacto (80mm térmicas)
- Formato A4 (impresoras normales)
- Integración con reportlab
- Códigos QR opcionales

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
import io

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import mm, inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

from models.ticket import Ticket
from models.company_config import CompanyConfig
from services.company_service import CompanyService
from services.sales_service import SalesService
from services.movement_service import MovementService


class TicketGenerator:
    """
    Generador de PDFs para tickets del sistema.
    
    Soporta múltiples formatos de salida y tipos de ticket.
    """
    
    # Formatos de ticket disponibles
    FORMATO_TERMICO_80MM = "termico_80mm"
    FORMATO_A4 = "a4"
    FORMATO_CARTA = "carta"
    
    # Tamaños de página
    TAMAÑOS_PAGINA = {
        FORMATO_TERMICO_80MM: (80*mm, 200*mm),  # 80mm ancho, altura variable
        FORMATO_A4: A4,
        FORMATO_CARTA: letter
    }
    
    def __init__(self, db_connection=None):
        """
        Inicializar el generador de tickets.
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab es requerido para generar PDFs. "
                "Instalar con: pip install reportlab"
            )

        self.company_service = CompanyService()
        self.sales_service = SalesService(db_connection) if db_connection else None
        self.movement_service = MovementService(db_connection) if db_connection else None

        # if self.sales_service is None:
        #    raise RuntimeError("El servicio de ventas no está inicializado.")

        if not self.sales_service:
            raise RuntimeError("Servicio de ventas no disponible para obtener datos de venta.")

        self._setup_styles()

    def _setup_styles(self):
        """
        Configurar estilos de texto para los PDFs.
        """
        self.styles = getSampleStyleSheet()
        
        # Estilo para encabezado de empresa
        self.styles.add(ParagraphStyle(
            name='EmpresaHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Estilo para datos de empresa
        self.styles.add(ParagraphStyle(
            name='EmpresaInfo',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Estilo para título de ticket
        self.styles.add(ParagraphStyle(
            name='TituloTicket',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Estilo para datos del ticket
        self.styles.add(ParagraphStyle(
            name='DatosTicket',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=2,
            alignment=TA_LEFT,
            textColor=colors.black
        ))
        
        # Estilo para totales
        self.styles.add(ParagraphStyle(
            name='Totales',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            alignment=TA_RIGHT,
            textColor=colors.black
        ))
    
    def _obtener_datos_empresa(self) -> Dict[str, Any]:
        """
        Obtener datos de empresa para el encabezado.
        
        Returns:
            Diccionario con datos de empresa
        """
        return self.company_service.obtener_encabezado_documentos()
    
    def _generar_codigo_qr(self, datos: str) -> Optional[bytes]:
        """
        Generar código QR con los datos especificados.
        
        Args:
            datos: String con datos para el QR
            
        Returns:
            Bytes del código QR como PNG o None si no disponible
        """
        if not QRCODE_AVAILABLE:
            return None
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=2,
            )
            qr.add_data(datos)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception:
            return None
    
    def _obtener_datos_venta(self, id_venta: int) -> Dict[str, Any]:
        """
        Obtener datos completos de una venta para el ticket.
        
        Args:
            id_venta: ID de la venta
            
        Returns:
            Diccionario con datos de la venta
        """
        venta = self.sales_service.obtener_venta_por_id(id_venta)
        if not venta:
            raise ValueError(f"Venta {id_venta} no encontrada")
        
        # Obtener detalles de la venta
        detalles = self.sales_service.obtener_detalles_venta(id_venta)
        
        return {
            'venta': venta,
            'detalles': detalles
        }
    
    def _obtener_datos_movimiento(self, id_movimiento: int) -> Dict[str, Any]:
        """
        Obtener datos completos de un movimiento para el ticket.
        
        Args:
            id_movimiento: ID del movimiento
            
        Returns:
            Diccionario con datos del movimiento
        """
        movimiento = self.movement_service.get_movement_by_id(id_movimiento)
        if not movimiento:
            raise ValueError(f"Movimiento {id_movimiento} no encontrado")
        
        return {
            'movimiento': movimiento
        }
    
    def generar_ticket_venta_pdf(
        self, 
        ticket: Ticket, 
        output_path: str,
        formato: str = FORMATO_A4,
        incluir_qr: bool = True
    ) -> bool:
        """
        Generar PDF para ticket de venta.
        
        Args:
            ticket: Instancia del ticket
            output_path: Ruta donde guardar el PDF
            formato: Formato del ticket (FORMATO_A4, FORMATO_TERMICO_80MM, etc.)
            incluir_qr: Si incluir código QR
            
        Returns:
            True si se generó correctamente
            
        Raises:
            ValueError: Si el ticket no es de venta o faltan datos
        """
        if not ticket.es_ticket_venta():
            raise ValueError("El ticket debe ser de tipo VENTA")
        
        if not ticket.id_venta:
            raise ValueError("El ticket debe tener id_venta asociado")
        
        # Obtener datos necesarios
        datos_empresa = self._obtener_datos_empresa()
        datos_venta = self._obtener_datos_venta(ticket.id_venta)
        
        # Configurar documento
        tamaño_pagina = self.TAMAÑOS_PAGINA.get(formato, A4)
        
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=tamaño_pagina,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            # Construir contenido
            story = []
            
            # Encabezado de empresa
            story.append(Paragraph(datos_empresa['nombre'], self.styles['EmpresaHeader']))
            story.append(Paragraph(datos_empresa['ruc'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['direccion'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['telefono'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['email'], self.styles['EmpresaInfo']))
            
            story.append(Spacer(1, 10*mm))
            
            # Título del ticket
            story.append(Paragraph("TICKET DE VENTA", self.styles['TituloTicket']))
            
            # Datos del ticket
            story.append(Paragraph(f"Ticket No: {ticket.ticket_number}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Fecha: {ticket.obtener_fecha_formateada()}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Atendido por: {ticket.generated_by}", self.styles['DatosTicket']))
            
            if ticket.reprint_count > 0:
                story.append(Paragraph(f"REIMPRESIÓN #{ticket.reprint_count}", self.styles['DatosTicket']))
            
            story.append(Spacer(1, 5*mm))
            
            # Tabla de productos
            if datos_venta['detalles']:
                # Encabezados de tabla
                tabla_datos = [
                    ['Producto', 'Cant.', 'Precio', 'Total']
                ]
                
                # Agregar productos
                for detalle in datos_venta['detalles']:
                    fila = [
                        str(detalle.get('nombre_producto', 'N/A')),
                        str(detalle.get('cantidad', 0)),
                        f"${detalle.get('precio_unitario', 0):.2f}",
                        f"${detalle.get('subtotal_item', 0):.2f}"
                    ]
                    tabla_datos.append(fila)
                
                # Crear tabla
                tabla = Table(tabla_datos, colWidths=[40*mm, 15*mm, 20*mm, 20*mm])
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(tabla)
                story.append(Spacer(1, 5*mm))
            
            # Totales
            venta = datos_venta['venta']
            story.append(Paragraph(f"Subtotal: ${venta.get('subtotal', 0):.2f}", self.styles['Totales']))
            story.append(Paragraph(f"ITBMS: ${venta.get('impuestos', 0):.2f}", self.styles['Totales']))
            story.append(Paragraph(f"<b>TOTAL: ${venta.get('total', 0):.2f}</b>", self.styles['Totales']))
            
            # Código QR (si está habilitado)
            if incluir_qr:
                qr_data = f"TICKET:{ticket.ticket_number}|VENTA:{ticket.id_venta}|TOTAL:{venta.get('total', 0)}"
                qr_bytes = self._generar_codigo_qr(qr_data)
                if qr_bytes:
                    story.append(Spacer(1, 5*mm))
                    story.append(Paragraph("Código QR para verificación", self.styles['EmpresaInfo']))
            
            # Pie de página
            story.append(Spacer(1, 10*mm))
            story.append(Paragraph("¡Gracias por su compra!", self.styles['EmpresaInfo']))
            story.append(Paragraph(f"Ticket generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['EmpresaInfo']))
            
            # Generar PDF
            doc.build(story)
            
            return True
            
        except Exception as e:
            # Si hay error, intentar eliminar archivo parcial
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise e
    
    def generar_ticket_entrada_pdf(
        self, 
        ticket: Ticket, 
        output_path: str,
        formato: str = FORMATO_A4,
        incluir_qr: bool = True
    ) -> bool:
        """
        Generar PDF para ticket de entrada.
        
        Args:
            ticket: Instancia del ticket
            output_path: Ruta donde guardar el PDF
            formato: Formato del ticket
            incluir_qr: Si incluir código QR
            
        Returns:
            True si se generó correctamente
            
        Raises:
            ValueError: Si el ticket no es de entrada o faltan datos
        """
        if not ticket.es_ticket_entrada():
            raise ValueError("El ticket debe ser de tipo ENTRADA")
        
        if not ticket.id_movimiento:
            raise ValueError("El ticket debe tener id_movimiento asociado")
        
        # Obtener datos necesarios
        datos_empresa = self._obtener_datos_empresa()
        datos_movimiento = self._obtener_datos_movimiento(ticket.id_movimiento)
        
        # Configurar documento
        tamaño_pagina = self.TAMAÑOS_PAGINA.get(formato, A4)
        
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=tamaño_pagina,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            # Construir contenido
            story = []
            
            # Encabezado de empresa
            story.append(Paragraph(datos_empresa['nombre'], self.styles['EmpresaHeader']))
            story.append(Paragraph(datos_empresa['ruc'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['direccion'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['telefono'], self.styles['EmpresaInfo']))
            story.append(Paragraph(datos_empresa['email'], self.styles['EmpresaInfo']))
            
            story.append(Spacer(1, 10*mm))
            
            # Título del ticket
            story.append(Paragraph("TICKET DE ENTRADA DE INVENTARIO", self.styles['TituloTicket']))
            
            # Datos del ticket
            story.append(Paragraph(f"Ticket No: {ticket.ticket_number}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Fecha: {ticket.obtener_fecha_formateada()}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Responsable: {ticket.generated_by}", self.styles['DatosTicket']))
            
            if ticket.reprint_count > 0:
                story.append(Paragraph(f"REIMPRESIÓN #{ticket.reprint_count}", self.styles['DatosTicket']))
            
            story.append(Spacer(1, 5*mm))
            
            # Datos del movimiento
            movimiento = datos_movimiento['movimiento']
            story.append(Paragraph(f"Tipo de movimiento: {movimiento.get('tipo_movimiento', 'N/A')}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Cantidad: {movimiento.get('cantidad', 0)}", self.styles['DatosTicket']))
            story.append(Paragraph(f"Fecha movimiento: {movimiento.get('fecha_movimiento', 'N/A')}", self.styles['DatosTicket']))
            
            if movimiento.get('observaciones'):
                story.append(Paragraph(f"Observaciones: {movimiento.get('observaciones')}", self.styles['DatosTicket']))
            
            # Código QR (si está habilitado)
            if incluir_qr:
                qr_data = f"TICKET:{ticket.ticket_number}|MOVIMIENTO:{ticket.id_movimiento}|TIPO:ENTRADA"
                qr_bytes = self._generar_codigo_qr(qr_data)
                if qr_bytes:
                    story.append(Spacer(1, 5*mm))
                    story.append(Paragraph("Código QR para verificación", self.styles['EmpresaInfo']))
            
            # Pie de página
            story.append(Spacer(1, 10*mm))
            story.append(Paragraph("Ticket de entrada de inventario", self.styles['EmpresaInfo']))
            story.append(Paragraph(f"Ticket generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['EmpresaInfo']))
            
            # Generar PDF
            doc.build(story)
            
            return True
            
        except Exception as e:
            # Si hay error, intentar eliminar archivo parcial
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise e
    
    def generar_ticket_pdf(
        self, 
        ticket: Ticket, 
        output_path: str,
        formato: str = FORMATO_A4,
        incluir_qr: bool = True
    ) -> bool:
        """
        Generar PDF para cualquier tipo de ticket.
        
        Args:
            ticket: Instancia del ticket
            output_path: Ruta donde guardar el PDF
            formato: Formato del ticket
            incluir_qr: Si incluir código QR
            
        Returns:
            True si se generó correctamente
        """
        if ticket.es_ticket_venta():
            return self.generar_ticket_venta_pdf(ticket, output_path, formato, incluir_qr)
        elif ticket.es_ticket_entrada():
            return self.generar_ticket_entrada_pdf(ticket, output_path, formato, incluir_qr)
        else:
            raise ValueError(f"Tipo de ticket no soportado: {ticket.ticket_type}")
    
    def generar_ruta_archivo(
        self, 
        ticket: Ticket, 
        directorio_base: str = "data/reports",
        extension: str = "pdf"
    ) -> str:
        """
        Generar ruta de archivo para el ticket.
        
        Args:
            ticket: Instancia del ticket
            directorio_base: Directorio base para archivos
            extension: Extensión del archivo
            
        Returns:
            Ruta completa del archivo
        """
        # Crear nombre de archivo único
        fecha_str = ticket.generated_at.strftime("%Y%m%d")
        
        if ticket.reprint_count > 0:
            nombre_archivo = f"{ticket.ticket_number}_reprint_{ticket.reprint_count}_{fecha_str}.{extension}"
        else:
            nombre_archivo = f"{ticket.ticket_number}_{fecha_str}.{extension}"
        
        # Crear subdirectorio por tipo
        subdirectorio = "ventas" if ticket.es_ticket_venta() else "entradas"
        
        ruta_completa = os.path.join(directorio_base, subdirectorio, nombre_archivo)
        
        return ruta_completa
    
    def verificar_dependencias(self) -> Dict[str, bool]:
        """
        Verificar disponibilidad de dependencias.
        
        Returns:
            Diccionario con estado de dependencias
        """
        return {
            'reportlab': REPORTLAB_AVAILABLE,
            'qrcode': QRCODE_AVAILABLE
        }
    
    def obtener_formatos_disponibles(self) -> Dict[str, str]:
        """
        Obtener lista de formatos de ticket disponibles.
        
        Returns:
            Diccionario con formatos y sus descripciones
        """
        return {
            self.FORMATO_A4: "Formato A4 (210 x 297 mm)",
            self.FORMATO_CARTA: "Formato Carta (8.5 x 11 in)",
            self.FORMATO_TERMICO_80MM: "Formato Térmico 80mm (80 x 200 mm)"
        }
