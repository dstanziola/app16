"""
Inicialización del módulo de compliance
Desarrollado siguiendo TDD
Validado contra duplicación
Autorizado el: 2025-07-10
Actualizado Fase 2: 2025-07-10
"""

from .models import (
    CompliancePhase,
    ComplianceStatus,
    InstructionType,
    ComplianceRecord,
    ComplianceInstruction,
    ComplianceSession,
    ValidationResult
)

from .utils import (
    SessionManager,
    ComplianceSetup,
    ComplianceRunner
)

__all__ = [
    # Modelos base (Fase 1)
    'CompliancePhase',
    'ComplianceStatus', 
    'InstructionType',
    'ComplianceRecord',
    'ComplianceInstruction',
    'ComplianceSession',
    'ValidationResult',
    
    # Componentes utilidades (Fase 2)
    'SessionManager',
    'ComplianceSetup',
    'ComplianceRunner'
]
