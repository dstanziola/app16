"""
ExportService - Servicio centralizado para exportación de reportes.

Este servicio maneja la exportación de datos del sistema a múltiples formatos,
incluyendo Excel (.xlsx) y PDF con plantillas profesionales corporativas.

ARQUITECTURA:
- Service Layer Pattern para encapsular lógica de exportación
- Factory Pattern para crear exportadores especializados
- Dependency Injection para servicios dependientes
- Clean Architecture con separación de responsabilidades

FUNCIONALIDADES:
- Exportación de movimientos a Excel con formato profesional
- Exportación de movimientos a PDF con plantilla corporativa
- Aplicación automática de filtros y parámetros
- Generación de reportes ejecutivos
- Manejo robusto de errores y validaciones

SPRINT 2: Implementación TDD con tests previos
Cumple con Clean Architecture y patrones establecidos

Autor: Sistema de Inventario Copy Point S.A.
Versión: 1.0.0 - Sprint 2
Fecha: 2025-07-12
Compliance: TDD, SOLID, Clean Architecture
"""

import os
import tempfile
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Imports de infraestructura
from infrastructure.exports.excel_exporter import ExcelExporter
from infrastructure.exports.pdf_exporter import PDFExporter
from infrastructure.exports.report_templates import ReportTemplates

# Configurar logging
logger = logging.getLogger(__name__)


class ExportService:
    """
    Servicio centralizado para exportación de reportes y datos.
    
    RESPONSABILIDADES:
    - Coordinar exportación de datos a múltiples formatos
    - Aplicar filtros y parámetros de exportación
    - Generar archivos con plantillas profesionales
    - Manejar errores y validaciones de exportación
    - Integrar con servicios de datos (MovementService, ReportService)
    
    ARQUITECTURA:
    - Service Layer: Encapsula lógica de exportación
    - Dependency Injection: Recibe servicios por constructor
    - Factory Pattern: Crea exportadores especializados
    """
    
    def __init__(self, movement_service, report_service):
        """
        Inicializar servicio de exportación con dependencias inyectadas.
        
        Args:
            movement_service: Servicio para obtener datos de movimientos
            report_service: Servicio para obtener datos de reportes
        
        Raises:
            ValueError: Si las dependencias son inválidas
        """
        if not movement_service:
            raise ValueError("MovementService es requerido para ExportService")
        if not report_service:
            raise ValueError("ReportService es requerido para ExportService")
        
        self.movement_service = movement_service
        self.report_service = report_service
        
        # Inicializar exportadores especializados
        self.excel_exporter = ExcelExporter()
        self.pdf_exporter = PDFExporter()
        self.report_templates = ReportTemplates()
        
        # Configuración del servicio - Rutas específicas para Copy Point S.A.
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # D:\inventario_app2
        self.data_dir = os.path.join(self.project_root, "data")
        
        # Rutas específicas por tipo de documento
        self.tickets_entrada_path = os.path.join(self.data_dir, "tickets_entrada")
        self.tickets_venta_path = os.path.join(self.data_dir, "tickets_venta")
        self.tickets_ajuste_path = os.path.join(self.data_dir, "tickets_ajuste")
        self.reportes_path = os.path.join(self.data_dir, "reportes")
        
        # Mantener compatibilidad con export_base_path para reportes generales
        self.export_base_path = self.reportes_path
        
        # Crear todos los directorios necesarios
        self._create_required_directories()
        
        logger.info("ExportService inicializado con dependencias y exportadores")
    
    def _create_required_directories(self) -> None:
        r"""
        Crear todos los directorios necesarios para almacenar tickets y reportes.
        
        Crea la estructura:
        - D:\inventario_app2\data\tickets_entrada\
        - D:\inventario_app2\data\tickets_venta\
        - D:\inventario_app2\data\tickets_ajuste\
        - D:\inventario_app2\data\reportes\
        """
        directories_to_create = [
            self.data_dir,
            self.tickets_entrada_path,
            self.tickets_venta_path, 
            self.tickets_ajuste_path,
            self.reportes_path
        ]
        
        for directory in directories_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"Directorio creado/verificado: {directory}")
            except OSError as e:
                logger.error(f"Error creando directorio {directory}: {e}")
                raise Exception(f"No se pudo crear directorio requerido: {directory}")
                
        logger.info(f"Estructura de directorios configurada en: {self.data_dir}")
    
    def _get_ticket_directory(self, ticket_type: str) -> str:
        """
        Obtener directorio específico según tipo de ticket.
        
        Args:
            ticket_type: Tipo de ticket ('ENTRADA', 'VENTA', 'AJUSTE')
            
        Returns:
            str: Ruta al directorio específico
            
        Raises:
            ValueError: Si el tipo de ticket no es válido
        """
        ticket_type = ticket_type.upper()
        
        ticket_directories = {
            'ENTRADA': self.tickets_entrada_path,
            'VENTA': self.tickets_venta_path,
            'AJUSTE': self.tickets_ajuste_path
        }
        
        if ticket_type not in ticket_directories:
            raise ValueError(f"Tipo de ticket no válido: {ticket_type}. Debe ser: {list(ticket_directories.keys())}")
            
        return ticket_directories[ticket_type]
    
    def export_movements_to_excel(self, movements: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
        """
        Exportar movimientos de inventario a archivo Excel con formato profesional.
        
        Args:
            movements: Lista de movimientos a exportar
            filters: Filtros aplicados (fechas, tipo, categoría, etc.)
        
        Returns:
            str: Ruta al archivo Excel generado
        
        Raises:
            ValueError: Si los parámetros son inválidos
            IOError: Si hay error escribiendo el archivo
            Exception: Para otros errores de exportación
        """
        try:
            # Validar parámetros de entrada
            self._validate_export_parameters(movements, filters)
            
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"movimientos_inventario_{timestamp}.xlsx"
            file_path = os.path.join(self.export_base_path, filename)
            
            # Preparar datos con formato apropiado para Excel
            formatted_data = self._format_movements_for_excel(movements)
            
            # Crear plantilla Excel con información corporativa
            template_data = self.report_templates.create_excel_template(
                title="Reporte de Movimientos de Inventario",
                filters=filters,
                data=formatted_data
            )
            
            # Exportar usando ExcelExporter especializado
            self.excel_exporter.create_movements_workbook(
                data=template_data,
                file_path=file_path
            )
            
            logger.info(f"Movimientos exportados a Excel exitosamente: {file_path}")
            return file_path
            
        except ValueError as e:
            logger.error(f"Error validando parámetros para exportación Excel: {e}")
            raise
        except IOError as e:
            logger.error(f"Error de E/O escribiendo archivo Excel: {e}")
            raise IOError(f"No se pudo escribir archivo Excel: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en exportación Excel: {e}")
            raise Exception(f"Error exportando a Excel: {e}")
    
    def export_movements_to_pdf(self, movements: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
        """
        Exportar movimientos de inventario a archivo PDF con plantilla profesional.
        
        Args:
            movements: Lista de movimientos a exportar  
            filters: Filtros aplicados para incluir en el reporte
        
        Returns:
            Ticket: Objeto Ticket generado con pdf_path configurado
        
        Raises:
            ValueError: Si los parámetros son inválidos
            IOError: Si hay error escribiendo el archivo
            Exception: Para otros errores de exportación
        """
        try:
            # Validar parámetros
            self._validate_export_parameters(movements, filters)
            
            # Generar nombre único para PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_movimientos_{timestamp}.pdf"
            file_path = os.path.join(self.export_base_path, filename)
            
            # Preparar datos con formato apropiado para PDF
            formatted_data = self._format_movements_for_pdf(movements)
            
            # Generar resumen ejecutivo para PDF
            summary_data = self._generate_movements_summary(movements)
            
            # Crear plantilla PDF con diseño profesional
            template_data = self.report_templates.create_pdf_template(
                title="Reporte Ejecutivo de Movimientos",
                filters=filters,
                data=formatted_data,
                summary=summary_data
            )
            
            # Exportar usando PDFExporter especializado
            self.pdf_exporter.create_movements_pdf(
                template_data=template_data,
                file_path=file_path
            )
            
            logger.info(f"Movimientos exportados a PDF exitosamente: {file_path}")
            return file_path
            
        except ValueError as e:
            logger.error(f"Error validando parámetros para exportación PDF: {e}")
            raise
        except IOError as e:
            logger.error(f"Error de E/O escribiendo archivo PDF: {e}")
            raise IOError(f"No se pudo escribir archivo PDF: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en exportación PDF: {e}")
            raise Exception(f"Error exportando a PDF: {e}")
    
    def export_low_stock_report(self, format_type: str) -> str:
        """
        Exportar reporte de productos con stock bajo.
        
        Args:
            format_type: Formato de exportación ('excel' o 'pdf')
        
        Returns:
            str: Ruta al archivo generado
        
        Raises:
            ValueError: Si el formato no es soportado
            Exception: Para errores de exportación
        """
        try:
            if format_type not in ['excel', 'pdf']:
                raise ValueError(f"Formato '{format_type}' no soportado. Use 'excel' o 'pdf'")
            
            # Obtener datos de stock bajo usando movement_service
            low_stock_products = self.movement_service.get_productos_bajo_stock()
            
            if not low_stock_products:
                logger.warning("No hay productos con stock bajo para exportar")
                # Crear archivo vacío con mensaje
                return self._create_empty_report(format_type, "No hay productos con stock bajo")
            
            # Preparar filtros para reporte
            filters = {
                'tipo_reporte': 'Stock Bajo',
                'fecha_generacion': datetime.now(),
                'criterio': 'Productos por debajo del stock mínimo'
            }
            
            # Exportar según formato solicitado
            if format_type == 'excel':
                return self._export_low_stock_excel(low_stock_products, filters)
            else:
                return self._export_low_stock_pdf(low_stock_products, filters)
                
        except ValueError as e:
            logger.error(f"Formato inválido para reporte stock bajo: {e}")
            raise
        except Exception as e:
            logger.error(f"Error exportando reporte stock bajo: {e}")
            raise Exception(f"Error generando reporte de stock bajo: {e}")
    
    def _validate_export_parameters(self, movements: List[Dict[str, Any]], filters: Dict[str, Any]) -> None:
        """
        Validar parámetros de entrada para exportación.
        
        Args:
            movements: Lista de movimientos
            filters: Filtros aplicados
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        if not isinstance(movements, list):
            raise ValueError("Movimientos debe ser una lista")
        
        if not isinstance(filters, dict):
            raise ValueError("Filtros debe ser un diccionario")
        
        # Validar estructura de movimientos
        if movements:
            required_fields = ['id_movimiento', 'fecha_movimiento', 'tipo_movimiento']
            first_movement = movements[0]
            
            for field in required_fields:
                if field not in first_movement:
                    raise ValueError(f"Campo requerido '{field}' faltante en movimientos")
        
        logger.debug(f"Parámetros validados: {len(movements)} movimientos, filtros: {list(filters.keys())}")
    
    def _format_movements_for_excel(self, movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatear movimientos para exportación Excel.
        
        Args:
            movements: Movimientos originales
        
        Returns:
            List[Dict[str, Any]]: Movimientos formateados para Excel
        """
        formatted = []
        
        for mov in movements:
            # Formatear fecha para Excel
            fecha_str = mov.get('fecha_movimiento', '')
            try:
                if isinstance(fecha_str, str):
                    fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    fecha_formatted = fecha_dt.strftime('%d/%m/%Y %H:%M')
                else:
                    fecha_formatted = str(fecha_str)
            except:
                fecha_formatted = fecha_str
            
            # Formatear cantidad según tipo
            cantidad = mov.get('cantidad', 0)
            tipo = mov.get('tipo_movimiento', '')
            
            if tipo == 'ENTRADA':
                cantidad_formatted = f"+{cantidad}"
            elif tipo == 'AJUSTE':
                cantidad_formatted = f"{cantidad:+d}"
            else:
                cantidad_formatted = str(cantidad)
            
            formatted_movement = {
                'ID': mov.get('id_movimiento', ''),
                'Fecha': fecha_formatted,
                'Producto': mov.get('producto_nombre', ''),
                'Tipo': tipo,
                'Cantidad': cantidad_formatted,
                'Stock Anterior': mov.get('cantidad_anterior', ''),
                'Stock Nuevo': mov.get('cantidad_nueva', ''),
                'Responsable': mov.get('responsable', ''),
                'Observaciones': mov.get('observaciones', '')
            }
            
            formatted.append(formatted_movement)
        
        return formatted
    
    def _format_movements_for_pdf(self, movements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        VERSIÓN MEJORADA: Formatear movimientos para exportación PDF landscape.
        
        MEJORAS:
        - Preservar más contenido en campos críticos
        - Formateo optimizado para columnas anchas
        - Truncado inteligente para observaciones muy largas
        
        Args:
            movements: Movimientos originales
        
        Returns:
            List[Dict[str, Any]]: Movimientos formateados para landscape
        """
        formatted = []
        
        for mov in movements:
            # MEJORA 1: Formatear fecha completa (más espacio en landscape)
            fecha_str = mov.get('fecha_movimiento', '')
            try:
                if isinstance(fecha_str, str):
                    fecha_dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    fecha_formatted = fecha_dt.strftime('%d/%m/%Y\n%H:%M')  # Multilinea
                else:
                    fecha_formatted = str(fecha_str)
            except:
                fecha_formatted = fecha_str
            
            # MEJORA 2: Preservar nombres de producto completos (columna más ancha)
            producto_nombre = mov.get('producto_nombre', '')
            if len(producto_nombre) > 35:  # Límite aumentado para landscape
                producto_formatted = producto_nombre[:32] + "..."
            else:
                producto_formatted = producto_nombre
            
            # MEJORA 3: Observaciones con truncado inteligente
            observaciones = mov.get('observaciones', '')
            if len(observaciones) > 40:  # Límite aumentado
                observaciones_formatted = observaciones[:37] + "..."
            else:
                observaciones_formatted = observaciones
            
            # MEJORA 4: Formatear cantidad con signo para mejor visualización
            cantidad = mov.get('cantidad', 0)
            tipo = mov.get('tipo_movimiento', '')
            
            if tipo == 'ENTRADA':
                cantidad_formatted = f"+{cantidad}"
            elif tipo == 'AJUSTE':
                cantidad_formatted = f"{cantidad:+d}"
            else:
                cantidad_formatted = str(cantidad)
            
            formatted_movement = {
                'ID': mov.get('id_movimiento', ''),
                'Fecha/Hora': fecha_formatted,
                'Producto': producto_formatted,
                'Tipo': tipo,
                'Cantidad': cantidad_formatted,
                'Responsable': mov.get('responsable', ''),
                'Observaciones': observaciones_formatted
            }
            
            formatted.append(formatted_movement)
        
        return formatted
    
    def _generate_movements_summary(self, movements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generar resumen ejecutivo de movimientos.
        
        Args:
            movements: Lista de movimientos
        
        Returns:
            Dict[str, Any]: Resumen estadístico
        """
        if not movements:
            return {
                'total_movimientos': 0,
                'total_entradas': 0,
                'total_ajustes': 0,
                'valor_total': 'B/. 0.00'
            }
        
        total_entradas = sum(1 for mov in movements if mov.get('tipo_movimiento') == 'ENTRADA')
        total_ajustes = sum(1 for mov in movements if mov.get('tipo_movimiento') == 'AJUSTE')
        
        # Calcular valor total si está disponible
        valor_total = Decimal('0.00')
        for mov in movements:
            costo = mov.get('costo_total', 0)
            if costo:
                try:
                    valor_total += Decimal(str(costo))
                except (ValueError, TypeError):
                    pass
        
        return {
            'total_movimientos': len(movements),
            'total_entradas': total_entradas,
            'total_ajustes': total_ajustes,
            'valor_total': f"B/. {valor_total:,.2f}",
            'periodo_generacion': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
    
    def _export_low_stock_excel(self, products: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
        """Exportar productos con stock bajo a Excel."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_bajo_{timestamp}.xlsx"
        file_path = os.path.join(self.export_base_path, filename)
        
        # Formatear datos para Excel
        formatted_data = []
        for product in products:
            formatted_data.append({
                'Producto': product.get('nombre', ''),
                'Stock Actual': product.get('stock', 0),
                'Stock Mínimo': product.get('stock_minimo', 0),
                'Faltante': product.get('faltante', 0),
                'Estado': 'CRÍTICO' if product.get('faltante', 0) > 5 else 'BAJO'
            })
        
        # Crear plantilla especializada
        template_data = self.report_templates.create_excel_template(
            title="Reporte de Stock Bajo",
            filters=filters,
            data=formatted_data
        )
        
        self.excel_exporter.create_movements_workbook(template_data, file_path)
        return file_path
    
    def _export_low_stock_pdf(self, products: List[Dict[str, Any]], filters: Dict[str, Any]) -> str:
        """Exportar productos con stock bajo a PDF."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stock_bajo_{timestamp}.pdf"
        file_path = os.path.join(self.export_base_path, filename)
        
        # Formatear datos para PDF
        formatted_data = []
        for product in products:
            formatted_data.append({
                'Producto': product.get('nombre', ''),
                'Actual': product.get('stock', 0),
                'Mínimo': product.get('stock_minimo', 0),
                'Faltante': product.get('faltante', 0)
            })
        
        # Generar resumen para PDF
        summary = {
            'total_productos': len(products),
            'criticos': sum(1 for p in products if p.get('faltante', 0) > 5),
            'fecha_reporte': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        
        template_data = self.report_templates.create_pdf_template(
            title="Reporte de Stock Bajo",
            filters=filters,
            data=formatted_data,
            summary=summary
        )
        
        self.pdf_exporter.create_movements_pdf(template_data, file_path)
        return file_path
    
    def _create_empty_report(self, format_type: str, message: str) -> str:
        """Crear reporte vacío con mensaje informativo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'excel':
            filename = f"reporte_vacio_{timestamp}.xlsx"
            file_path = os.path.join(self.export_base_path, filename)
            
            # Crear Excel vacío con mensaje
            template_data = self.report_templates.create_excel_template(
                title="Reporte Vacío",
                filters={'mensaje': message},
                data=[]
            )
            self.excel_exporter.create_movements_workbook(template_data, file_path)
            
        else:  # PDF
            filename = f"reporte_vacio_{timestamp}.pdf"
            file_path = os.path.join(self.export_base_path, filename)
            
            template_data = self.report_templates.create_pdf_template(
                title="Reporte Vacío",
                filters={'mensaje': message},
                data=[],
                summary={'mensaje': message}
            )
            self.pdf_exporter.create_movements_pdf(template_data, file_path)
        
        return file_path
    
    def get_export_directory(self) -> str:
        """
        Obtener directorio base de exportación (reportes generales).
        
        Returns:
            str: Ruta al directorio de reportes
        """
        return self.export_base_path
    
    def get_tickets_directory(self, ticket_type: str = None) -> str:
        """
        Obtener directorio de tickets específico o base.
        
        Args:
            ticket_type: Tipo de ticket ('ENTRADA', 'VENTA', 'AJUSTE') o None para directorio base
            
        Returns:
            str: Ruta al directorio solicitado
        """
        if ticket_type is None:
            return self.data_dir
        
        return self._get_ticket_directory(ticket_type)
    
    def get_directory_info(self) -> Dict[str, str]:
        """
        Obtener información completa de directorios configurados.
        
        Returns:
            Dict[str, str]: Mapeo de tipo de directorio a ruta
        """
        return {
            'proyecto': self.project_root,
            'data': self.data_dir,
            'tickets_entrada': self.tickets_entrada_path,
            'tickets_venta': self.tickets_venta_path, 
            'tickets_ajuste': self.tickets_ajuste_path,
            'reportes': self.reportes_path
        }
    
    def generate_entry_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """
        Generar ticket de entrada de inventario con PDF.
        
        Args:
            ticket_data: Diccionario con datos del ticket
                - ticket_number: Número del ticket
                - tipo: Tipo de movimiento ('ENTRADA')
                - fecha: Fecha del movimiento
                - responsable: Usuario responsable
                - productos: Lista de productos del movimiento
                - id_movimiento: ID del movimiento (opcional)
        
        Returns:
            str: Ruta al archivo PDF generado
        
        Raises:
            ValueError: Si los datos del ticket son inválidos
            Exception: Para errores de generación o exportación
        """
        try:
            # Validar datos de entrada
            self._validate_ticket_data(ticket_data)
            
            # Preparar datos para generación de PDF - Usar directorio específico para entradas
            ticket_type = ticket_data.get('tipo', 'ENTRADA').upper()
            ticket_directory = self._get_ticket_directory(ticket_type)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ticket_number = ticket_data.get('ticket_number', timestamp)
            filename = f"ticket_{ticket_type.lower()}_{ticket_number}.pdf"
            file_path = os.path.join(ticket_directory, filename)
            
            # Formatear productos para el ticket
            formatted_products = self._format_products_for_ticket(ticket_data.get('productos', []))
            
            # Crear datos del template para PDF
            template_data = self._create_ticket_template_data(
                ticket_data,
                formatted_products,
                'ENTRADA'
            )
            
            # Generar PDF usando PDFExporter
            self.pdf_exporter.create_entry_ticket_pdf(
                template_data=template_data,
                file_path=file_path
            )
            
            # Si hay ID de movimiento, usar TicketService para persistir
            if ticket_data.get('id_movimiento'):
                self._persist_ticket_entry(
                    ticket_data.get('id_movimiento'),
                    ticket_data.get('ticket_number'),
                    ticket_data.get('responsable'),
                    file_path
                )
            
            logger.info(f"Ticket de entrada generado exitosamente: {file_path}")
            print(f"[DEBUG] Archivo generado en: {file_path}")
            return file_path
            
        except ValueError as e:
            logger.error(f"Error validando datos del ticket: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generando ticket de entrada: {e}")
            raise Exception(f"Error al generar ticket de entrada: {e}")
    
    def _validate_ticket_data(self, ticket_data: Dict[str, Any]) -> None:
        """
        Validar datos del ticket de entrada.
        
        Args:
            ticket_data: Datos del ticket a validar
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        if not isinstance(ticket_data, dict):
            raise ValueError("ticket_data debe ser un diccionario")
        
        required_fields = ['ticket_number', 'responsable', 'productos']
        missing_fields = [field for field in required_fields if field not in ticket_data]
        
        if missing_fields:
            raise ValueError(f"Campos requeridos faltantes: {missing_fields}")
        
        if not ticket_data.get('productos'):
            raise ValueError("La lista de productos no puede estar vacía")
        
        # Validar que el número de ticket tenga formato válido
        ticket_number = ticket_data.get('ticket_number', '')
        if not ticket_number or len(ticket_number.strip()) == 0:
            raise ValueError("El número de ticket es requerido")
        
        logger.debug(f"Datos del ticket validados: {ticket_number}")
    
    def _format_products_for_ticket(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatear productos para mostrar en el ticket.
        
        Args:
            products: Lista de productos originales
        
        Returns:
            List[Dict[str, Any]]: Productos formateados para ticket
        """
        formatted = []
        
        for product in products:
            formatted_product = {
                'nombre': product.get('nombre', 'Producto sin nombre'),
                'cantidad': product.get('cantidad', 0),
                'codigo': product.get('id', product.get('codigo', 'N/A')),
                'observaciones': product.get('observaciones', '')
            }
            formatted.append(formatted_product)
        
        return formatted
    
    def _create_ticket_template_data(self, ticket_data: Dict[str, Any], products: List[Dict[str, Any]], tipo: str) -> Dict[str, Any]:
        """
        Crear datos del template para el ticket PDF.
        
        Args:
            ticket_data: Datos básicos del ticket
            products: Productos formateados
            tipo: Tipo de ticket ('ENTRADA')
        
        Returns:
            Dict[str, Any]: Datos completos para el template
        """
        fecha_ticket = ticket_data.get('fecha', datetime.now())
        if isinstance(fecha_ticket, str):
            try:
                fecha_ticket = datetime.fromisoformat(fecha_ticket.replace('Z', '+00:00'))
            except:
                fecha_ticket = datetime.now()
        
        template_data = {
            'title': f'Ticket de {tipo.title()}',
            'ticket_info': {
                'numero': ticket_data.get('ticket_number', 'N/A'),
                'tipo': tipo,
                'fecha': fecha_ticket.strftime('%d/%m/%Y %H:%M:%S'),
                'responsable': ticket_data.get('responsable', 'No especificado')
            },
            'productos': products,
            'resumen': {
                'total_productos': len(products),
                'total_cantidad': sum(p.get('cantidad', 0) for p in products),
                'observaciones_generales': ticket_data.get('observaciones', '')
            },
            'empresa': {
                'nombre': 'Copy Point S.A.',
                'direccion': 'Las Lajas, Las Cumbres, Panamá',
                'telefono': '6342-9218',
                'email': 'tus_amigos@copypoint.online'
            }
        }
        
        return template_data
    
    def _persist_ticket_entry(self, id_movimiento: int, ticket_number: str, responsable: str, pdf_path: str) -> None:
        """
        Persistir información del ticket usando TicketService.
        
        Args:
            id_movimiento: ID del movimiento asociado
            ticket_number: Número del ticket
            responsable: Usuario responsable
            pdf_path: Ruta del archivo PDF
        """
        try:
            # Importar TicketService dinámicamente para evitar dependencias circulares
            from services.ticket_service import TicketService
            
            ticket_service = TicketService()
            
            # Generar ticket usando el servicio especializado
            ticket = ticket_service.generar_ticket_entrada(
                id_movimiento=id_movimiento,
                generated_by=responsable,
                pdf_path=pdf_path
            )
            
            logger.info(f"Ticket persistido: ID={ticket.id_ticket}, Número={ticket_number}")
            
        except Exception as e:
            # No fallar la generación del PDF si hay error en persistencia
            logger.warning(f"Error al persistir ticket (PDF generado exitosamente): {e}")
    
    def generate_adjustment_ticket(self, movement_id: int, adjustment_data: Dict[str, Any]):
        """
        Generar ticket de ajuste de inventario con PDF.
        
        Args:
            movement_id: ID del movimiento de ajuste
            adjustment_data: Diccionario con datos del ajuste
                - product_id: ID del producto
                - product_name: Nombre del producto
                - quantity: Cantidad de ajuste (puede ser negativa)
                - reason: Motivo del ajuste
                - observations: Observaciones
                - responsible: Usuario responsable
                - timestamp: Timestamp del ajuste
        
        Returns:
            Ticket: Objeto Ticket generado con pdf_path configurado
        
        Raises:
            ValueError: Si los datos del ajuste son inválidos
            Exception: Para errores de generación o exportación
        """
        try:
            # Validar datos de entrada
            self._validate_adjustment_data(adjustment_data)
            
            # Preparar datos para generación de PDF - Usar directorio específico para ajustes
            ticket_directory = self._get_ticket_directory('AJUSTE')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ticket_ajuste_{movement_id}_{timestamp}.pdf"
            file_path = os.path.join(ticket_directory, filename)
            
            # Crear datos del template para PDF
            template_data = self._create_adjustment_ticket_template_data(
                movement_id,
                adjustment_data
            )
            
            # Generar PDF usando PDFExporter
            self.pdf_exporter.create_adjustment_ticket_pdf(
                template_data=template_data,
                file_path=file_path
            )
            
            # Persistir información del ticket y retornar objeto Ticket
            ticket = self._persist_adjustment_ticket(
                movement_id,
                adjustment_data.get('responsible'),
                file_path
            )
            
            logger.info(f"Ticket de ajuste generado exitosamente: {file_path}")
            print(f"[DEBUG] Ticket de ajuste generado en: {file_path}")
            return ticket
            
        except ValueError as e:
            logger.error(f"Error validando datos del ajuste: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generando ticket de ajuste: {e}")
            raise Exception(f"Error al generar ticket de ajuste: {e}")
    
    def _validate_adjustment_data(self, adjustment_data: Dict[str, Any]) -> None:
        """
        Validar datos del ajuste.
        
        Args:
            adjustment_data: Datos del ajuste a validar
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        if not isinstance(adjustment_data, dict):
            raise ValueError("adjustment_data debe ser un diccionario")
        
        required_fields = ['product_id', 'product_name', 'quantity', 'reason', 'responsible']
        missing_fields = [field for field in required_fields if field not in adjustment_data]
        
        if missing_fields:
            raise ValueError(f"Campos requeridos faltantes: {missing_fields}")
        
        # Validar que la cantidad sea un entero diferente de cero
        quantity = adjustment_data.get('quantity')
        if not isinstance(quantity, int) or quantity == 0:
            raise ValueError("La cantidad debe ser un entero diferente de cero")
        
        logger.debug(f"Datos del ajuste validados: producto {adjustment_data.get('product_name')}")
    
    def _create_adjustment_ticket_template_data(self, movement_id: int, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear datos del template para el ticket de ajuste PDF.
        
        Args:
            movement_id: ID del movimiento de ajuste
            adjustment_data: Datos del ajuste
        
        Returns:
            Dict[str, Any]: Datos completos para el template
        """
        # Parsear timestamp si está presente
        fecha_ajuste = adjustment_data.get('timestamp')
        if isinstance(fecha_ajuste, str):
            try:
                fecha_ajuste = datetime.fromisoformat(fecha_ajuste.replace('Z', '+00:00'))
            except:
                fecha_ajuste = datetime.now()
        elif not isinstance(fecha_ajuste, datetime):
            fecha_ajuste = datetime.now()
        
        # Formatear cantidad con signo
        quantity = adjustment_data.get('quantity', 0)
        quantity_formatted = f"{quantity:+d}"  # +5 o -3
        
        # Determinar tipo de operación
        operation_type = "SUMA AL STOCK" if quantity > 0 else "RESTA DEL STOCK"
        
        template_data = {
            'title': 'Ticket de Ajuste de Inventario',
            'ticket_info': {
                'numero': f"ADJ-{movement_id:06d}",
                'tipo': 'AJUSTE',
                'fecha': fecha_ajuste.strftime('%d/%m/%Y %H:%M:%S'),
                'responsable': adjustment_data.get('responsible', 'No especificado'),
                'movimiento_id': movement_id
            },
            'producto_info': {
                'id': adjustment_data.get('product_id', 'N/A'),
                'nombre': adjustment_data.get('product_name', 'Producto sin nombre'),
                'cantidad_ajuste': quantity_formatted,
                'operacion': operation_type
            },
            'ajuste_details': {
                'motivo': adjustment_data.get('reason', 'No especificado'),
                'observaciones': adjustment_data.get('observations', 'Sin observaciones'),
                'cantidad_numerica': quantity
            },
            'empresa': {
                'nombre': 'Copy Point S.A.',
                'direccion': 'Las Lajas, Las Cumbres, Panamá',
                'telefono': '6342-9218',
                'email': 'tus_amigos@copypoint.online'
            }
        }
        
        return template_data
    
    def _persist_adjustment_ticket(self, movement_id: int, responsible: str, pdf_path: str):
        """
        Persistir información del ticket de ajuste usando TicketService.
        
        Args:
            movement_id: ID del movimiento asociado
            responsible: Usuario responsable
            pdf_path: Ruta del archivo PDF
            
        Returns:
            Ticket: Objeto Ticket generado y persistido
        """
        try:
            # Importar TicketService dinámicamente para evitar dependencias circulares
            from services.ticket_service import TicketService
            
            ticket_service = TicketService()
            
            # Generar ticket usando el servicio especializado
            ticket = ticket_service.generar_ticket_ajuste(
                id_movimiento=movement_id,
                generated_by=responsible,
                pdf_path=pdf_path
            )
            
            logger.info(f"Ticket de ajuste persistido: ID={ticket.id_ticket}, Movimiento={movement_id}")
            return ticket
            
        except Exception as e:
            # No fallar la generación del PDF si hay error en persistencia
            logger.warning(f"Error al persistir ticket de ajuste (PDF generado exitosamente): {e}")
            # Retornar un objeto ticket mínimo con la ruta del PDF
            from models.ticket import Ticket
            return Ticket(
                ticket_type='AJUSTE',
                ticket_number=f"ADJ-{movement_id:06d}",
                generated_by=responsible,
                pdf_path=pdf_path,
                id_movimiento=movement_id
            )

    def cleanup_old_exports(self, days_old: int = 7, include_tickets: bool = False) -> Dict[str, int]:
        """
        Limpiar archivos de exportación antiguos en todos los directorios.
        
        Args:
            days_old: Días de antigüedad para considerar archivo viejo
            include_tickets: Si incluir limpieza de tickets (default: False por seguridad)
        
        Returns:
            Dict[str, int]: Número de archivos eliminados por directorio
        """
        results = {}
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        # Directorios a limpiar
        directories_to_clean = {
            'reportes': self.reportes_path
        }
        
        # Agregar directorios de tickets si se solicita
        if include_tickets:
            directories_to_clean.update({
                'tickets_entrada': self.tickets_entrada_path,
                'tickets_venta': self.tickets_venta_path,
                'tickets_ajuste': self.tickets_ajuste_path
            })
            logger.warning(f"Limpieza de tickets habilitada para archivos más antiguos de {days_old} días")
        
        for dir_name, dir_path in directories_to_clean.items():
            try:
                if not os.path.exists(dir_path):
                    results[dir_name] = 0
                    continue
                
                files_deleted = 0
                
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        
                        if file_time < cutoff_time:
                            try:
                                os.remove(file_path)
                                files_deleted += 1
                                logger.debug(f"Archivo eliminado de {dir_name}: {filename}")
                            except OSError as e:
                                logger.warning(f"No se pudo eliminar {filename} de {dir_name}: {e}")
                
                results[dir_name] = files_deleted
                logger.info(f"Limpieza en {dir_name}: {files_deleted} archivos eliminados")
                
            except Exception as e:
                logger.error(f"Error en limpieza de directorio {dir_name}: {e}")
                results[dir_name] = 0
        
        total_deleted = sum(results.values())
        logger.info(f"Limpieza completada: {total_deleted} archivos eliminados en total")
        return results
