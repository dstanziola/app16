"""
Módulo de exportación de datos - Infrastructure Layer.

Este módulo contiene los exportadores especializados para diferentes formatos
de archivos, siguiendo el patrón de Clean Architecture.

COMPONENTES:
- ExcelExporter: Exportación especializada a formato Excel (.xlsx)
- PDFExporter: Exportación especializada a formato PDF
- ReportTemplates: Plantillas profesionales y formatos corporativos

ARQUITECTURA:
- Infrastructure Layer: Implementaciones concretas de exportación
- Factory Pattern: Creación de exportadores especializados
- Template Pattern: Plantillas base y personalización
- Separation of Concerns: Cada exportador maneja un formato específico

SPRINT 2: Implementación TDD con Clean Architecture
Cumple con patrones SOLID y principios establecidos

Autor: Sistema de Inventario Copy Point S.A.
Versión: 1.0.0 - Sprint 2
Fecha: 2025-07-12
"""

from .excel_exporter import ExcelExporter
from .pdf_exporter import PDFExporter
from .report_templates import ReportTemplates

__all__ = [
    'ExcelExporter',
    'PDFExporter', 
    'ReportTemplates'
]

__version__ = '1.0.0'
__author__ = 'Sistema de Inventario Copy Point S.A.'
