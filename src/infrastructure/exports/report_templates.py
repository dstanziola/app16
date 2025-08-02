"""
ReportTemplates - Plantillas profesionales para reportes.

Este módulo maneja la creación y personalización de plantillas para diferentes
tipos de reportes, aplicando branding corporativo y formatos profesionales.

FUNCIONALIDADES:
- Plantillas base para Excel y PDF
- Aplicación de branding corporativo
- Formateo personalizado por tipo de reporte
- Configuración de estilos y layouts
- Gestión de logos e imágenes corporativas

PATRONES:
- Template Method: Plantillas base con puntos de extensión
- Factory Pattern: Creación de plantillas específicas
- Builder Pattern: Construcción progresiva de templates
- Strategy Pattern: Diferentes estilos según tipo de reporte

ARQUITECTURA:
- Infrastructure Layer: Implementación concreta de plantillas
- Single Responsibility: Solo maneja plantillas y formatos
- Open/Closed: Extensible para nuevos tipos de plantillas

SPRINT 2: Implementación TDD con tests previos
Autor: Sistema de Inventario Copy Point S.A.
Versión: 1.0.0 - Sprint 2
Fecha: 2025-07-12
"""

import os
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)


class ReportTemplates:
    """
    Gestor de plantillas profesionales para reportes.
    
    RESPONSABILIDADES:
    - Crear plantillas base para diferentes tipos de reportes
    - Aplicar branding corporativo consistente
    - Formatear datos según tipo de reporte
    - Gestionar estilos y configuraciones de diseño
    - Proporcionar layouts optimizados para cada formato
    
    PATRONES:
    - Template Method: Proceso estándar de creación de plantillas
    - Factory Pattern: Creación de plantillas específicas por tipo
    - Builder Pattern: Construcción progresiva de configuración
    """
    
    def __init__(self):
        """
        Inicializar gestor de plantillas con configuración corporativa.
        """
        # Información corporativa base
        self.company_branding = {
            'nombre': 'Copy Point S.A.',
            'ruc': '888-888-8888',
            'direccion': 'Las Lajas, Las Cumbres, Panamá',
            'telefono': '6666-6666',
            'email': 'copy.point@gmail.com',
            'web': 'www.copypoint.com.pa',
            'slogan': 'Su centro de copiado e impresión de confianza'
        }
        
        # Colores corporativos (valores hex)
        self.corporate_colors = {
            'primary': '#1F4E79',      # Azul corporativo principal
            'secondary': '#70AD47',    # Verde corporativo secundario
            'accent': '#C55A11',       # Naranja corporativo para acentos
            'light_gray': '#F2F2F2',   # Gris claro para fondos
            'dark_gray': '#595959',    # Gris oscuro para texto
            'white': '#FFFFFF',        # Blanco puro
            'black': '#000000'         # Negro puro
        }
        
        # Configuración de fuentes
        self.font_config = {
            'title_size': 18,
            'subtitle_size': 14,
            'header_size': 12,
            'normal_size': 10,
            'small_size': 9,
            'primary_font': 'Calibri',
            'secondary_font': 'Arial',
            'monospace_font': 'Courier New'
        }
        
        # Templates disponibles
        self.available_templates = {
            'movements': 'Plantilla para movimientos de inventario',
            'stock_report': 'Plantilla para reportes de stock',
            'sales_summary': 'Plantilla para resúmenes de ventas',
            'executive_report': 'Plantilla para reportes ejecutivos',
            'inventory_audit': 'Plantilla para auditorías de inventario'
        }
        
        logger.info("ReportTemplates inicializado con branding corporativo")
    
    def create_excel_template(self, title: str, filters: Dict[str, Any], 
                            data: List[Dict[str, Any]], template_type: str = 'movements') -> Dict[str, Any]:
        """
        Crear plantilla Excel con formato profesional corporativo.
        
        Args:
            title: Título del reporte
            filters: Filtros aplicados al reporte
            data: Datos a incluir en el reporte
            template_type: Tipo de plantilla a aplicar
        
        Returns:
            Dict[str, Any]: Configuración completa de plantilla Excel
        
        Raises:
            ValueError: Si el tipo de plantilla no es válido
        """
        try:
            # Validar tipo de plantilla
            if template_type not in self.available_templates:
                raise ValueError(f"Tipo de plantilla '{template_type}' no válido. "
                               f"Disponibles: {list(self.available_templates.keys())}")
            
            # Crear configuración base de plantilla
            template_config = {
                'title': title,
                'data': data,
                'filters': filters,
                'template_type': template_type,
                'company_info': self.company_branding.copy(),
                'colors': self.corporate_colors.copy(),
                'fonts': self.font_config.copy(),
                'generation_time': datetime.now(),
                'summary': self._generate_data_summary(data, template_type)
            }
            
            # Aplicar configuración específica según tipo
            if template_type == 'movements':
                template_config.update(self._get_movements_excel_config())
            elif template_type == 'stock_report':
                template_config.update(self._get_stock_excel_config())
            elif template_type == 'executive_report':
                template_config.update(self._get_executive_excel_config())
            else:
                template_config.update(self._get_default_excel_config())
            
            # Agregar metadatos del archivo
            template_config['metadata'] = self._create_excel_metadata(title, template_type)
            
            logger.debug(f"Plantilla Excel creada: {template_type} con {len(data)} registros")
            return template_config
            
        except ValueError as e:
            logger.error(f"Error validando plantilla Excel: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creando plantilla Excel: {e}")
            raise Exception(f"Error en plantilla Excel: {e}")
    
    def create_pdf_template(self, title: str, filters: Dict[str, Any], 
                          data: List[Dict[str, Any]], summary: Optional[Dict[str, Any]] = None,
                          template_type: str = 'movements') -> Dict[str, Any]:
        """
        Crear plantilla PDF con diseño profesional corporativo.
        
        Args:
            title: Título del reporte
            filters: Filtros aplicados al reporte
            data: Datos a incluir en el reporte
            summary: Resumen ejecutivo (opcional)
            template_type: Tipo de plantilla a aplicar
        
        Returns:
            Dict[str, Any]: Configuración completa de plantilla PDF
        
        Raises:
            ValueError: Si el tipo de plantilla no es válido
        """
        try:
            # Validar tipo de plantilla
            if template_type not in self.available_templates:
                raise ValueError(f"Tipo de plantilla '{template_type}' no válido")
            
            # Crear configuración base de plantilla PDF
            template_config = {
                'title': title,
                'data': data,
                'filters': filters,
                'summary': summary or self._generate_data_summary(data, template_type),
                'template_type': template_type,
                'company_info': self.company_branding.copy(),
                'colors': self._get_pdf_colors(),
                'fonts': self._get_pdf_fonts(),
                'layout': self._get_pdf_layout(template_type),
                'generation_time': datetime.now()
            }
            
            # Aplicar configuración específica según tipo
            if template_type == 'movements':
                template_config.update(self._get_movements_pdf_config())
            elif template_type == 'stock_report':
                template_config.update(self._get_stock_pdf_config())
            elif template_type == 'executive_report':
                template_config.update(self._get_executive_pdf_config())
            else:
                template_config.update(self._get_default_pdf_config())
            
            # Optimizar datos para presentación PDF
            template_config['data'] = self._optimize_data_for_pdf(data)
            
            logger.debug(f"Plantilla PDF creada: {template_type}")
            return template_config
            
        except ValueError as e:
            logger.error(f"Error validando plantilla PDF: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creando plantilla PDF: {e}")
            raise Exception(f"Error en plantilla PDF: {e}")
    
    def _generate_data_summary(self, data: List[Dict[str, Any]], template_type: str) -> Dict[str, Any]:
        """
        Generar resumen automático de los datos.
        
        Args:
            data: Datos a resumir
            template_type: Tipo de plantilla para personalizar resumen
        
        Returns:
            Dict[str, Any]: Resumen de datos generado
        """
        if not data:
            return {
                'total_records': 0,
                'summary_message': 'No hay datos para mostrar',
                'generation_time': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        
        summary = {
            'total_records': len(data),
            'generation_time': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'template_type': template_type
        }
        
        # Resumen específico para movimientos
        if template_type == 'movements':
            summary.update(self._summarize_movements_data(data))
        
        # Resumen específico para stock
        elif template_type == 'stock_report':
            summary.update(self._summarize_stock_data(data))
        
        # Resumen genérico
        else:
            summary.update(self._summarize_generic_data(data))
        
        return summary
    
    def _summarize_movements_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear resumen específico para datos de movimientos."""
        summary = {
            'total_movimientos': len(data),
            'total_entradas': 0,
            'total_ajustes': 0,
            'productos_afectados': set(),
            'responsables': set()
        }
        
        for record in data:
            # Contar por tipo
            tipo = record.get('Tipo', record.get('tipo_movimiento', ''))
            if tipo == 'ENTRADA':
                summary['total_entradas'] += 1
            elif tipo == 'AJUSTE':
                summary['total_ajustes'] += 1
            
            # Productos únicos
            producto = record.get('Producto', record.get('producto_nombre', ''))
            if producto:
                summary['productos_afectados'].add(producto)
            
            # Responsables únicos
            responsable = record.get('Responsable', record.get('responsable', ''))
            if responsable:
                summary['responsables'].add(responsable)
        
        # Convertir sets a conteos
        summary['total_productos_afectados'] = len(summary['productos_afectados'])
        summary['total_responsables'] = len(summary['responsables'])
        
        # Limpiar sets (no serializables)
        del summary['productos_afectados']
        del summary['responsables']
        
        return summary
    
    def _summarize_stock_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear resumen específico para datos de stock."""
        summary = {
            'total_productos': len(data),
            'criticos': 0,
            'bajo_stock': 0,
            'valor_total_faltante': 0
        }
        
        for record in data:
            faltante = record.get('Faltante', record.get('faltante', 0))
            
            if isinstance(faltante, (int, float)) and faltante > 0:
                summary['bajo_stock'] += 1
                
                if faltante > 5:  # Criterio crítico
                    summary['criticos'] += 1
                
                summary['valor_total_faltante'] += faltante
        
        return summary
    
    def _summarize_generic_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear resumen genérico para cualquier tipo de datos."""
        summary = {
            'total_records': len(data),
            'columns_count': len(data[0].keys()) if data else 0,
            'non_empty_records': 0
        }
        
        # Contar registros con datos no vacíos
        for record in data:
            if any(str(value).strip() for value in record.values() if value is not None):
                summary['non_empty_records'] += 1
        
        return summary
    
    def _get_movements_excel_config(self) -> Dict[str, Any]:
        """Configuración específica Excel para movimientos."""
        return {
            'column_widths': {
                'ID': 10,
                'Fecha': 18,
                'Producto': 25,
                'Tipo': 12,
                'Cantidad': 12,
                'Stock Anterior': 15,
                'Stock Nuevo': 15,
                'Responsable': 15,
                'Observaciones': 30
            },
            'frozen_rows': 1,
            'auto_filter': True,
            'show_gridlines': True,
            'print_settings': {
                'orientation': 'landscape',
                'fit_to_page': True,
                'repeat_rows': 1
            }
        }
    
    def _get_stock_excel_config(self) -> Dict[str, Any]:
        """Configuración específica Excel para stock."""
        return {
            'column_widths': {
                'Producto': 30,
                'Stock Actual': 15,
                'Stock Mínimo': 15,
                'Faltante': 12,
                'Estado': 12
            },
            'conditional_formatting': {
                'critical_stock': {'color': '#FF0000', 'condition': 'faltante > 5'},
                'low_stock': {'color': '#FFA500', 'condition': 'faltante > 0'}
            }
        }
    
    def _get_executive_excel_config(self) -> Dict[str, Any]:
        """Configuración específica Excel para reportes ejecutivos."""
        return {
            'include_charts': True,
            'summary_position': 'top',
            'professional_formatting': True,
            'print_settings': {
                'orientation': 'portrait',
                'margins': 'narrow',
                'header_footer': True
            }
        }
    
    def _get_default_excel_config(self) -> Dict[str, Any]:
        """Configuración por defecto para Excel."""
        return {
            'auto_adjust_columns': True,
            'freeze_first_row': True,
            'apply_table_style': True,
            'include_summary': True
        }
    
    def _get_movements_pdf_config(self) -> Dict[str, Any]:
        """VERSIÓN MEJORADA: Configuración específica PDF para movimientos con landscape."""
        return {
            'table_style': 'detailed_landscape',        # Nuevo estilo
            'include_summary': True,
            'page_orientation': 'landscape',             # LANDSCAPE por defecto
            'font_size': 8,                             # Font size optimizado
            'header_font_size': 9,                      # Headers ligeramente más grandes
            'row_height': 'auto',                       # Altura automática para word wrap
            'word_wrap': True,                          # Word wrapping habilitado
            'show_page_numbers': True,
            'optimized_columns': {                      # Anchos específicos
                'fecha': 3.2,
                'producto': 4.5,
                'observaciones': 4.0,
                'id': 0.8,
                'tipo': 1.8,
                'ticket': 1.5,
                'cantidad': 1.5,
                'responsable': 2.2
            },
            'margins': {                                # Márgenes reducidos para landscape
                'top': 1.5,
                'bottom': 1.5,
                'left': 1.5,
                'right': 1.5
            }
        }
    
    def _get_stock_pdf_config(self) -> Dict[str, Any]:
        """Configuración específica PDF para stock."""
        return {
            'table_style': 'compact',
            'highlight_critical': True,
            'include_charts': False,
            'page_orientation': 'portrait',
            'font_size': 9
        }
    
    def _get_executive_pdf_config(self) -> Dict[str, Any]:
        """Configuración específica PDF para ejecutivos."""
        return {
            'table_style': 'executive',
            'include_summary': True,
            'include_charts': True,
            'page_orientation': 'portrait',
            'font_size': 10,
            'professional_header': True
        }
    
    def _get_default_pdf_config(self) -> Dict[str, Any]:
        """Configuración por defecto para PDF."""
        return {
            'table_style': 'standard',
            'include_summary': False,
            'page_orientation': 'portrait',
            'font_size': 9
        }
    
    def _get_pdf_colors(self) -> Dict[str, Tuple[float, float, float]]:
        """Convertir colores hex a tuplas RGB para PDF."""
        def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        
        return {
            'primary': hex_to_rgb(self.corporate_colors['primary']),
            'secondary': hex_to_rgb(self.corporate_colors['secondary']),
            'accent': hex_to_rgb(self.corporate_colors['accent']),
            'light_gray': hex_to_rgb(self.corporate_colors['light_gray']),
            'dark_gray': hex_to_rgb(self.corporate_colors['dark_gray']),
            'white': (1.0, 1.0, 1.0),
            'black': (0.0, 0.0, 0.0)
        }
    
    def _get_pdf_fonts(self) -> Dict[str, Any]:
        """Configuración de fuentes para PDF."""
        return {
            'title': {'name': 'Helvetica-Bold', 'size': self.font_config['title_size']},
            'subtitle': {'name': 'Helvetica-Bold', 'size': self.font_config['subtitle_size']},
            'header': {'name': 'Helvetica-Bold', 'size': self.font_config['header_size']},
            'normal': {'name': 'Helvetica', 'size': self.font_config['normal_size']},
            'small': {'name': 'Helvetica', 'size': self.font_config['small_size']}
        }
    
    def _get_pdf_layout(self, template_type: str) -> Dict[str, Any]:
        """Configuración de layout para PDF según tipo."""
        base_layout = {
            'margins': {'top': 2, 'bottom': 2, 'left': 2, 'right': 2},  # en cm
            'header_height': 3,  # en cm
            'footer_height': 1.5,  # en cm
            'spacing': {'paragraph': 6, 'section': 12}  # en puntos
        }
        
        if template_type == 'executive_report':
            base_layout['margins'] = {'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5}
            base_layout['header_height'] = 4
        
        return base_layout
    
    def _optimize_data_for_pdf(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimizar datos para presentación en PDF.
        
        Args:
            data: Datos originales
        
        Returns:
            List[Dict[str, Any]]: Datos optimizados para PDF
        """
        if not data:
            return data
        
        optimized_data = []
        
        for record in data:
            optimized_record = {}
            
            for key, value in record.items():
                # Truncar valores muy largos
                if isinstance(value, str) and len(value) > 50:
                    optimized_record[key] = value[:47] + "..."
                
                # Formatear números
                elif isinstance(value, (int, float)):
                    if key.lower() in ['precio', 'costo', 'valor', 'total']:
                        optimized_record[key] = f"B/. {value:,.2f}"
                    else:
                        optimized_record[key] = f"{value:,}"
                
                # Mantener otros valores
                else:
                    optimized_record[key] = str(value) if value is not None else ""
            
            optimized_data.append(optimized_record)
        
        return optimized_data
    
    def _create_excel_metadata(self, title: str, template_type: str) -> Dict[str, Any]:
        """Crear metadatos para archivo Excel."""
        return {
            'title': title,
            'subject': f'Reporte de Inventario - {template_type}',
            'creator': self.company_branding['nombre'],
            'description': f'Reporte generado por Sistema de Inventario',
            'keywords': 'inventario, reporte, gestión, copy point',
            'category': 'Reportes de Inventario',
            'created': datetime.now(),
            'version': '1.0'
        }
    
    def get_available_templates(self) -> Dict[str, str]:
        """
        Obtener lista de plantillas disponibles.
        
        Returns:
            Dict[str, str]: Plantillas disponibles con descripciones
        """
        return self.available_templates.copy()
    
    def validate_template_type(self, template_type: str) -> bool:
        """
        Validar que un tipo de plantilla es válido.
        
        Args:
            template_type: Tipo a validar
        
        Returns:
            bool: True si es válido
        """
        return template_type in self.available_templates
    
    def get_corporate_branding(self) -> Dict[str, Any]:
        """
        Obtener información de branding corporativo.
        
        Returns:
            Dict[str, Any]: Información corporativa completa
        """
        return {
            'company_info': self.company_branding.copy(),
            'colors': self.corporate_colors.copy(),
            'fonts': self.font_config.copy()
        }
    
    def update_company_branding(self, new_branding: Dict[str, Any]) -> None:
        """
        Actualizar información de branding corporativo.
        
        Args:
            new_branding: Nueva información corporativa
        
        Raises:
            ValueError: Si la información no es válida
        """
        required_fields = ['nombre', 'ruc', 'telefono', 'email']
        
        for field in required_fields:
            if field not in new_branding:
                raise ValueError(f"Campo requerido '{field}' faltante en branding")
        
        # Actualizar información válida
        for key, value in new_branding.items():
            if key in self.company_branding:
                self.company_branding[key] = value
        
        logger.info("Branding corporativo actualizado")
    
    def create_custom_template(self, template_name: str, config: Dict[str, Any]) -> bool:
        """
        Crear plantilla personalizada.
        
        Args:
            template_name: Nombre de la nueva plantilla
            config: Configuración de la plantilla
        
        Returns:
            bool: True si se creó exitosamente
        
        Raises:
            ValueError: Si la configuración no es válida
        """
        try:
            # Validar configuración básica
            required_config = ['description', 'type', 'settings']
            for key in required_config:
                if key not in config:
                    raise ValueError(f"Configuración '{key}' requerida para plantilla personalizada")
            
            # Registrar nueva plantilla
            self.available_templates[template_name] = config['description']
            
            logger.info(f"Plantilla personalizada creada: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando plantilla personalizada: {e}")
            raise
