"""
Inicialización del módulo de modelos de compliance
Desarrollado siguiendo TDD
Validado contra duplicación
Autorizado el: 2025-07-10
"""

from .compliance_models import (
    CompliancePhase,
    ComplianceStatus,
    InstructionType,
    ComplianceRecord,
    ComplianceInstruction,
    ComplianceSession,
    ValidationResult,
    validate_syntax_compliance
)

__all__ = [
    'CompliancePhase',
    'ComplianceStatus',
    'InstructionType',
    'ComplianceRecord',
    'ComplianceInstruction',
    'ComplianceSession',
    'ValidationResult',
    'validate_syntax_compliance'
]
