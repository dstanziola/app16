"""
Generador de PDFs para el sistema de reportes

Este módulo implementa la generación profesional de PDFs para todos los tipos
de reportes del sistema usando reportlab.

TIPOS DE PDF SOPORTADOS:
1. Reporte de Inventario Actual
2. Reporte de Movimientos por período
3. Reporte de Ventas con filtros
4. Reporte de Rentabilidad

CARACTERÍSTICAS:
- Formato corporativo con logo y datos de empresa
- Tablas profesionales con datos
- Gráficos y estadísticas
- Paginación automática
- Totales y resúmenes

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025 - FASE 2
"""

import os
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from decimal import Decimal

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import Color, HexColor


class PDFReportGenerator:
    """Generador principal de PDFs para reportes"""
    
    def __init__(self):
        """Inicializa el generador de PDFs"""
        self.styles = getSampleStyleSheet()
        self.company_color = HexColor('#1E3A8A')  # Azul corporativo
        self.secondary_color = HexColor('#3B82F6')  # Azul claro
        self.success_color = HexColor('#10B981')  # Verde
        self.warning_color = HexColor('#F59E0B')  # Amarillo
        self.error_color = HexColor('#EF4444')  # Rojo
        
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        # Estilo para título principal
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=self.company_color,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulos
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.company_color,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para información de empresa
        self.company_style = ParagraphStyle(
            'CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=6
        )
        
        # Estilo para datos numéricos
        self.number_style = ParagraphStyle(
            'NumberStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        )
        
        # Estilo para totales
        self.total_style = ParagraphStyle(
            'TotalStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=self.company_color,
            alignment=TA_RIGHT
        )
    
    def generate_report_pdf(
        self,
        report_data: Dict[str, Any],
        pdf_path: str,
        report_type: str,
        company_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Genera un PDF del reporte especificado
        
        Args:
            report_data: Datos del reporte
            pdf_path: Ruta donde guardar el PDF
            report_type: Tipo de reporte ('inventory', 'movements', 'sales', 'profitability')
            company_info: Información de la empresa
            
        Returns:
            True si la generación fue exitosa
        """
        try:
            # Crear documento
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=1 * inch,
                bottomMargin=0.75 * inch
            )
            
            # Crear contenido según el tipo de reporte
            story = []
            
            # Encabezado corporativo
            story.extend(self._create_header(company_info, report_type, report_data))
            
            # Contenido específico del reporte
            if report_type == "inventory":
                story.extend(self._create_inventory_content(report_data))
            elif report_type == "movements":
                story.extend(self._create_movements_content(report_data))
            elif report_type == "sales":
                story.extend(self._create_sales_content(report_data))
            elif report_type == "profitability":
                story.extend(self._create_profitability_content(report_data))
            else:
                raise ValueError(f"Tipo de reporte no soportado: {report_type}")
            
            # Pie de página
            story.extend(self._create_footer(report_data))
            
            # Generar PDF
            doc.build(story)
            return True
            
        except Exception as e:
            raise Exception(f"Error generando PDF: {e}")
    
    def _create_header(self, company_info: Dict[str, str], report_type: str, report_data: Dict) -> List:
        """Crea el encabezado corporativo del PDF"""
        elements = []
        
        # Información de la empresa
        if company_info:
            company_text = f"""
            <b>{company_info.get('nombre', 'Copy Point S.A.')}</b><br/>
            RUC: {company_info.get('ruc', '888-888-8888')}<br/>
            {company_info.get('direccion', 'Las Lajas, Las Cumbres, Panamá')}<br/>
            Tel: {company_info.get('telefono', '6666-6666')} | Email: {company_info.get('email', 'copy.point@gmail.com')}
            """
            elements.append(Paragraph(company_text, self.company_style))
            elements.append(Spacer(1, 20))
        
        # Título del reporte
        report_titles = {
            'inventory': '📦 REPORTE DE INVENTARIO ACTUAL',
            'movements': '📋 REPORTE DE MOVIMIENTOS',
            'sales': '💰 REPORTE DE VENTAS',
            'profitability': '📊 REPORTE DE RENTABILIDAD'
        }
        
        title = report_titles.get(report_type, 'REPORTE DEL SISTEMA')
        elements.append(Paragraph(title, self.title_style))
        
        # Información de generación
        generated_at = report_data.get('generated_at', datetime.now())
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        
        info_text = f"Generado el: {generated_at.strftime('%d/%m/%Y a las %H:%M')}"
        
        # Agregar información de filtros si existe
        filters = report_data.get('filters_applied', {})
        if filters:
            filter_parts = []
            if 'fecha_inicio' in filters and 'fecha_fin' in filters:
                filter_parts.append(f"Período: {filters['fecha_inicio']} - {filters['fecha_fin']}")
            if 'categoria_id' in filters and filters['categoria_id']:
                filter_parts.append(f"Categoría ID: {filters['categoria_id']}")
            if 'solo_con_stock' in filters and filters['solo_con_stock']:
                filter_parts.append("Solo productos con stock")
            
            if filter_parts:
                info_text += f"<br/>Filtros aplicados: {', '.join(filter_parts)}"
        
        elements.append(Paragraph(info_text, self.company_style))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_inventory_content(self, report_data: Dict) -> List:
        """Crea contenido específico para reporte de inventario"""
        elements = []
        
        # Resumen del inventario
        summary = report_data.get('summary', {})
        elements.append(Paragraph("RESUMEN EJECUTIVO", self.subtitle_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de productos', f"{summary.get('total_productos', 0):,}"],
            ['Productos con stock', f"{summary.get('productos_con_stock', 0):,}"],
            ['Productos sin stock', f"{summary.get('productos_sin_stock', 0):,}"],
            ['Valor total inventario', f"${summary.get('valor_total_inventario', 0):,.2f}"],
            ['Fecha de corte', summary.get('fecha_corte', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.company_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Detalle de productos
        data = report_data.get('data', [])
        if data:
            elements.append(Paragraph("DETALLE DE PRODUCTOS", self.subtitle_style))
            
            # Encabezados de la tabla
            table_data = [['ID', 'Producto', 'Categoría', 'Stock', 'Costo Unit.', 'Valor Total']]
            
            # Agregar datos
            for item in data[:50]:  # Limitar a 50 productos por página
                table_data.append([
                    str(item.get('id_producto', '')),
                    item.get('nombre', '')[:30],  # Truncar nombres largos
                    item.get('categoria', '')[:20],
                    f"{item.get('stock_actual', 0):,}",
                    f"${item.get('costo_unitario', 0):.2f}",
                    f"${item.get('valor_total', 0):,.2f}"
                ])
            
            # Crear tabla
            detail_table = Table(
                table_data,
                colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1.2*inch]
            )
            
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.company_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Alinear números a la derecha
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('ALTERNATEROWCOLORS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(detail_table)
            
            # Nota si hay más productos
            if len(data) > 50:
                elements.append(Spacer(1, 10))
                note = f"Nota: Se muestran los primeros 50 productos de {len(data)} total."
                elements.append(Paragraph(note, self.styles['Normal']))
        
        return elements
    
    def _create_movements_content(self, report_data: Dict) -> List:
        """Crea contenido específico para reporte de movimientos"""
        elements = []
        
        # Resumen de movimientos
        summary = report_data.get('summary', {})
        elements.append(Paragraph("RESUMEN DE MOVIMIENTOS", self.subtitle_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total movimientos', f"{summary.get('total_movimientos', 0):,}"],
            ['Total entradas', f"{summary.get('total_entradas', 0):,}"],
            ['Total salidas', f"{summary.get('total_salidas', 0):,}"],
            ['Valor total movimientos', f"${summary.get('valor_total_movimientos', 0):,.2f}"],
            ['Período', summary.get('periodo', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(self._get_summary_table_style())
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Detalle de movimientos
        data = report_data.get('data', [])
        if data:
            elements.append(Paragraph("DETALLE DE MOVIMIENTOS", self.subtitle_style))
            
            # Encabezados
            table_data = [['Fecha', 'Tipo', 'Producto', 'Cantidad', 'Responsable', 'Valor']]
            
            # Agregar datos (últimos 30 movimientos)
            for item in data[:30]:
                fecha_mov = item.get('fecha_movimiento', '')
                if 'T' in fecha_mov:
                    fecha_mov = fecha_mov.split('T')[0]
                
                cantidad = item.get('cantidad', 0)
                cantidad_str = f"+{cantidad}" if cantidad > 0 else str(cantidad)
                
                table_data.append([
                    fecha_mov,
                    item.get('tipo_movimiento', ''),
                    item.get('producto_nombre', '')[:25],
                    cantidad_str,
                    item.get('responsable', '')[:15],
                    f"${item.get('valor_movimiento', 0):,.2f}"
                ])
            
            detail_table = Table(
                table_data,
                colWidths=[1*inch, 1*inch, 2*inch, 0.8*inch, 1.2*inch, 1*inch]
            )
            
            detail_table.setStyle(self._get_detail_table_style())
            elements.append(detail_table)
            
            if len(data) > 30:
                elements.append(Spacer(1, 10))
                note = f"Nota: Se muestran los últimos 30 movimientos de {len(data)} total."
                elements.append(Paragraph(note, self.styles['Normal']))
        
        return elements
    
    def _create_sales_content(self, report_data: Dict) -> List:
        """Crea contenido específico para reporte de ventas"""
        elements = []
        
        # Resumen de ventas
        summary = report_data.get('summary', {})
        totals = report_data.get('totals', {})
        
        elements.append(Paragraph("RESUMEN DE VENTAS", self.subtitle_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total ventas', f"{summary.get('total_ventas', 0):,}"],
            ['Promedio por venta', f"${summary.get('promedio_venta', 0):,.2f}"],
            ['Subtotal', f"${totals.get('subtotal_total', 0):,.2f}"],
            ['Impuestos', f"${totals.get('impuestos_total', 0):,.2f}"],
            ['Total', f"${totals.get('gran_total', 0):,.2f}"],
            ['Período', summary.get('periodo', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(self._get_summary_table_style())
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Detalle de ventas
        data = report_data.get('data', [])
        if data:
            elements.append(Paragraph("DETALLE DE VENTAS", self.subtitle_style))
            
            table_data = [['ID', 'Fecha', 'Cliente', 'Subtotal', 'Impuestos', 'Total', 'Responsable']]
            
            for item in data[:40]:
                fecha_venta = item.get('fecha_venta', '')
                if 'T' in fecha_venta:
                    fecha_venta = fecha_venta.split('T')[0]
                
                table_data.append([
                    str(item.get('id_venta', '')),
                    fecha_venta,
                    item.get('cliente_nombre', '')[:20],
                    f"${item.get('subtotal', 0):,.2f}",
                    f"${item.get('impuestos', 0):,.2f}",
                    f"${item.get('total', 0):,.2f}",
                    item.get('responsable', '')[:12]
                ])
            
            detail_table = Table(
                table_data,
                colWidths=[0.5*inch, 0.8*inch, 1.8*inch, 1*inch, 1*inch, 1*inch, 0.9*inch]
            )
            
            detail_table.setStyle(self._get_detail_table_style())
            elements.append(detail_table)
            
            if len(data) > 40:
                elements.append(Spacer(1, 10))
                note = f"Nota: Se muestran las últimas 40 ventas de {len(data)} total."
                elements.append(Paragraph(note, self.styles['Normal']))
        
        return elements
    
    def _create_profitability_content(self, report_data: Dict) -> List:
        """Crea contenido específico para reporte de rentabilidad"""
        elements = []
        
        # Resumen de rentabilidad
        summary = report_data.get('summary', {})
        totals = report_data.get('totals', {})
        
        elements.append(Paragraph("ANÁLISIS DE RENTABILIDAD", self.subtitle_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Productos analizados', f"{summary.get('productos_analizados', 0):,}"],
            ['Ingresos totales', f"${totals.get('total_ingresos', 0):,.2f}"],
            ['Costos totales', f"${totals.get('total_costos', 0):,.2f}"],
            ['Ganancia bruta', f"${totals.get('total_ganancia', 0):,.2f}"],
            ['Margen total', f"{totals.get('margen_total_porcentaje', 0):.2f}%"],
            ['Período', summary.get('periodo', 'N/A')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(self._get_summary_table_style())
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Detalle por producto
        data = report_data.get('data', [])
        if data:
            elements.append(Paragraph("RENTABILIDAD POR PRODUCTO", self.subtitle_style))
            
            table_data = [['Producto', 'Cantidad', 'Ingresos', 'Costos', 'Ganancia', 'Margen %']]
            
            for item in data[:25]:  # Top 25 productos más rentables
                table_data.append([
                    item.get('producto_nombre', '')[:25],
                    f"{item.get('cantidad_vendida', 0):,}",
                    f"${item.get('ingresos_brutos', 0):,.2f}",
                    f"${item.get('costo_total', 0):,.2f}",
                    f"${item.get('ganancia_bruta', 0):,.2f}",
                    f"{item.get('margen_porcentaje', 0):.1f}%"
                ])
            
            detail_table = Table(
                table_data,
                colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch]
            )
            
            detail_table.setStyle(self._get_detail_table_style())
            elements.append(detail_table)
            
            if len(data) > 25:
                elements.append(Spacer(1, 10))
                note = f"Nota: Se muestran los 25 productos más rentables de {len(data)} total."
                elements.append(Paragraph(note, self.styles['Normal']))
        
        return elements
    
    def _create_footer(self, report_data: Dict) -> List:
        """Crea el pie de página del reporte"""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        # Línea separadora
        footer_line = Table([[''] * 7], colWidths=[1*inch] * 7)
        footer_line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, self.company_color),
        ]))
        elements.append(footer_line)
        
        # Información del sistema
        footer_text = f"""
        <b>Copy Point S.A. - Sistema de Gestión de Inventario v1.1</b><br/>
        Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}<br/>
        Para consultas técnicas: tus_amigos@copypoint.online
        """
        
        elements.append(Paragraph(footer_text, self.company_style))
        
        return elements
    
    def _get_summary_table_style(self) -> TableStyle:
        """Retorna estilo estándar para tablas de resumen"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.company_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ])
    
    def _get_detail_table_style(self) -> TableStyle:
        """Retorna estilo estándar para tablas de detalle"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.company_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALTERNATEROWCOLORS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])


# Función auxiliar para generar PDFs
def generate_pdf_report(
    report_data: Dict[str, Any],
    pdf_path: str,
    report_type: str,
    company_info: Optional[Dict[str, str]] = None
) -> bool:
    """
    Función auxiliar para generar PDFs de reportes
    
    Args:
        report_data: Datos del reporte
        pdf_path: Ruta donde guardar el PDF
        report_type: Tipo de reporte
        company_info: Información de la empresa
        
    Returns:
        True si la generación fue exitosa
    """
    generator = PDFReportGenerator()
    return generator.generate_report_pdf(report_data, pdf_path, report_type, company_info)
