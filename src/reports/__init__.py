"""
Paquete de reportes del sistema de inventario - FASE 2

Este paquete contiene todos los módulos relacionados con la generación
de reportes y exportación de datos del sistema de inventario.

MÓDULOS PRINCIPALES:
- pdf_generator: Generación profesional de PDFs con reportlab
- [Futuros módulos de reportes específicos]

CARACTERÍSTICAS:
- Generación de 4 tipos de reportes principales
- Exportación profesional a PDF
- Formato corporativo con branding
- Tablas y gráficos profesionales
- Paginación automática

TIPOS DE REPORTES SOPORTADOS:
1. Inventario Actual - Estado del stock por categorías
2. Movimientos - Historial de entradas, salidas y ajustes
3. Ventas - Análisis de ventas por período con filtros
4. Rentabilidad - Análisis de ganancias por producto

INTEGRACIÓN:
Se integra con el ReportService para proveer capacidades
de exportación a PDF de todos los reportes del sistema.

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025 - FASE 2
"""

from .pdf_generator import PDFReportGenerator, generate_pdf_report

__all__ = [
    'PDFReportGenerator',
    'generate_pdf_report'
]

# Versión del paquete de reportes
__version__ = '1.0.0'

# Metadatos del paquete
__author__ = 'Copy Point S.A.'
__email__ = 'copy.point@gmail.com'
__description__ = 'Sistema de generación de reportes y PDFs para inventario'
