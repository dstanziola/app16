"""
Módulo src - Sistema de Gestión de Inventario v5.0

Este es el módulo raíz del sistema que contiene todas las capas
de la Clean Architecture implementada.

Capas disponibles:
- ui: Capa de Presentación (Interfaz usuario)
- application: Capa de Aplicación (Casos de uso)
- domain: Capa de Dominio (Lógica de negocio)
- infrastructure: Capa de Infraestructura (Persistencia)
- shared: Capa Compartida (Utilidades comunes)

Fecha: 2025-07-17
Estado: P03 - Corrección crítica importaciones
"""

__version__ = '5.0.0'
__author__ = 'TDD Development Team'
__description__ = 'Sistema de Gestión de Inventario - Clean Architecture'

# Metadatos del sistema
SYSTEM_NAME = 'Sistema de Gestión de Inventario'
SYSTEM_VERSION = '5.0.0'
ARCHITECTURE = 'Clean Architecture'
METHODOLOGY = 'TDD (Test Driven Development)'
