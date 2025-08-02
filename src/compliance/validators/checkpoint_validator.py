"""
Validador de checkpoints del sistema de compliance.

Este módulo implementa el sistema de validación de checkpoints que verifica
el cumplimiento de criterios obligatorios en cada fase del proceso de
desarrollo siguiendo metodología TDD y criterios arquitectónicos.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.compliance.models.compliance_models import (
    CompliancePhase,
    ComplianceStatus,
    ValidationResult
)


@dataclass
class CheckpointValidationResult:
    """Resultado de validación de checkpoint."""
    phase: CompliancePhase
    is_valid: bool
    validation_details: Dict[str, bool]
    failed_criteria: List[str]
    messages: List[str]
    completion_percentage: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PhaseValidationConfig:
    """Configuración de validación para una fase específica."""
    phase: CompliancePhase
    required_criteria: List[str]
    optional_criteria: List[str]
    validation_weights: Dict[str, float]
    minimum_completion_threshold: float = 0.8


class CheckpointValidator:
    """
    Validador de checkpoints del sistema de compliance.
    
    Gestiona la validación automática de criterios obligatorios en cada
    fase del desarrollo, asegurando el cumplimiento de la metodología TDD
    y los estándares arquitectónicos establecidos.
    """
    
    def __init__(self):
        """Inicializar validador de checkpoints."""
        self.validation_configs = {}
        self.validation_history = []
        self.load_phase_validation_configs()
        
    def load_phase_validation_configs(self):
        """Cargar configuraciones de validación para todas las fases."""
        
        # Configuración para fase ANALYSIS
        self.validation_configs[CompliancePhase.ANALYSIS] = PhaseValidationConfig(
            phase=CompliancePhase.ANALYSIS,
            required_criteria=[
                'contexto_cargado',
                'estructura_comprendida',
                'funcionalidades_analizadas',
                'redundancias_verificadas'
            ],
            optional_criteria=[
                'documentacion_revisada',
                'dependencias_identificadas'
            ],
            validation_weights={
                'contexto_cargado': 0.3,
                'estructura_comprendida': 0.3,
                'funcionalidades_analizadas': 0.25,
                'redundancias_verificadas': 0.15
            }
        )
        
        # Configuración para fase PLANNING
        self.validation_configs[CompliancePhase.PLANNING] = PhaseValidationConfig(
            phase=CompliancePhase.PLANNING,
            required_criteria=[
                'lista_archivos_presentada',
                'autorizacion_solicitada',
                'impacto_estimado'
            ],
            optional_criteria=[
                'redundancias_detectadas',
                'arquitectura_validada'
            ],
            validation_weights={
                'lista_archivos_presentada': 0.4,
                'autorizacion_solicitada': 0.4,
                'impacto_estimado': 0.2
            }
        )
        
        # Configuración para fase IMPLEMENTATION
        self.validation_configs[CompliancePhase.IMPLEMENTATION] = PhaseValidationConfig(
            phase=CompliancePhase.IMPLEMENTATION,
            required_criteria=[
                'tests_escritos_primero',
                'cobertura_tdd_cumplida',
                'sintaxis_validada',
                'convenciones_cumplidas'
            ],
            optional_criteria=[
                'documentacion_actualizada',
                'refactoring_aplicado'
            ],
            validation_weights={
                'tests_escritos_primero': 0.35,
                'cobertura_tdd_cumplida': 0.35,
                'sintaxis_validada': 0.15,
                'convenciones_cumplidas': 0.15
            }
        )
        
        # Configuración para fase VALIDATION
        self.validation_configs[CompliancePhase.VALIDATION] = PhaseValidationConfig(
            phase=CompliancePhase.VALIDATION,
            required_criteria=[
                'tests_ejecutados',
                'sintaxis_verificada',
                'documentacion_actualizada',
                'reportes_generados'
            ],
            optional_criteria=[
                'performance_validado',
                'seguridad_verificada'
            ],
            validation_weights={
                'tests_ejecutados': 0.3,
                'sintaxis_verificada': 0.25,
                'documentacion_actualizada': 0.25,
                'reportes_generados': 0.2
            }
        )
        
        # Configuración para fase CONFIRMATION
        self.validation_configs[CompliancePhase.CONFIRMATION] = PhaseValidationConfig(
            phase=CompliancePhase.CONFIRMATION,
            required_criteria=[
                'confirmacion_recibida',
                'estado_reportado',
                'proximos_pasos_definidos'
            ],
            optional_criteria=[
                'metricas_calculadas',
                'feedback_registrado'
            ],
            validation_weights={
                'confirmacion_recibida': 0.5,
                'estado_reportado': 0.3,
                'proximos_pasos_definidos': 0.2
            }
        )
        
    def validate_phase(self, phase: CompliancePhase, validation_data: Dict[str, Any]) -> CheckpointValidationResult:
        """
        Validar una fase específica con sus criterios obligatorios.
        
        Args:
            phase: Fase a validar
            validation_data: Datos de validación proporcionados
            
        Returns:
            CheckpointValidationResult: Resultado de la validación
        """
        if phase not in self.validation_configs:
            return CheckpointValidationResult(
                phase=phase,
                is_valid=False,
                validation_details={},
                failed_criteria=[],
                messages=[f"No se encontró configuración para fase {phase.value}"]
            )
            
        config = self.validation_configs[phase]
        validation_details = {}
        failed_criteria = []
        messages = []
        
        # Validar criterios obligatorios
        for criteria in config.required_criteria:
            is_met = validation_data.get(criteria, False)
            validation_details[criteria] = is_met
            
            if not is_met:
                failed_criteria.append(criteria)
                messages.append(f"Criterio obligatorio no cumplido: {criteria}")
                
        # Validar criterios opcionales
        for criteria in config.optional_criteria:
            is_met = validation_data.get(criteria, False)
            validation_details[criteria] = is_met
            
        # Calcular porcentaje de completitud
        completion_percentage = self.calculate_phase_completion_percentage(phase, validation_data)
        
        # Determinar si la validación es exitosa
        is_valid = len(failed_criteria) == 0 and completion_percentage >= (config.minimum_completion_threshold * 100)
        
        if is_valid:
            messages.append(f"Validación de fase {phase.value} completada exitosamente")
        else:
            messages.append(f"Validación de fase {phase.value} falló - {len(failed_criteria)} criterios no cumplidos")
            
        result = CheckpointValidationResult(
            phase=phase,
            is_valid=is_valid,
            validation_details=validation_details,
            failed_criteria=failed_criteria,
            messages=messages,
            completion_percentage=completion_percentage
        )
        
        # Agregar al historial
        self.validation_history.append(result)
        
        return result
        
    def get_phase_requirements(self, phase: CompliancePhase) -> List[str]:
        """
        Obtener requerimientos específicos de una fase.
        
        Args:
            phase: Fase para obtener requerimientos
            
        Returns:
            List[str]: Lista de requerimientos obligatorios
        """
        if phase not in self.validation_configs:
            return []
            
        config = self.validation_configs[phase]
        return config.required_criteria.copy()
        
    def validate_tdd_compliance(self, tdd_data: Dict[str, Any]) -> ValidationResult:
        """
        Validar cumplimiento específico de metodología TDD.
        
        Args:
            tdd_data: Datos de validación TDD
            
        Returns:
            ValidationResult: Resultado de validación TDD
        """
        validation_details = {}
        is_valid = True
        messages = []
        
        # Verificar que existan archivos de test
        test_files_exist = tdd_data.get('test_files_exist', False)
        validation_details['test_files_exist'] = test_files_exist
        if not test_files_exist:
            is_valid = False
            messages.append("No se encontraron archivos de test")
            
        # Verificar que los tests se escribieron primero
        tests_written_first = tdd_data.get('tests_written_first', False)
        validation_details['tests_written_first'] = tests_written_first
        if not tests_written_first:
            is_valid = False
            messages.append("Los tests no fueron escritos antes del código")
            
        # Verificar cobertura mínima
        coverage_percentage = tdd_data.get('coverage_percentage', 0.0)
        validation_details['coverage_percentage'] = coverage_percentage
        if coverage_percentage < 95.0:
            is_valid = False
            messages.append(f"Cobertura de tests insuficiente: {coverage_percentage}% (mínimo 95%)")
            
        # Verificar ejecución exitosa de tests
        test_execution_success = tdd_data.get('test_execution_success', False)
        validation_details['test_execution_success'] = test_execution_success
        if not test_execution_success:
            is_valid = False
            messages.append("La ejecución de tests falló")
            
        if is_valid:
            messages.append("Cumplimiento TDD validado exitosamente")
            
        return ValidationResult(
            instruction_id="TDD_COMPLIANCE",
            is_valid=is_valid,
            validation_details=validation_details,
            message="; ".join(messages)
        )
        
    def validate_syntax_compliance(self, syntax_data: Dict[str, Any]) -> ValidationResult:
        """
        Validar cumplimiento de sintaxis y convenciones.
        
        Args:
            syntax_data: Datos de validación de sintaxis
            
        Returns:
            ValidationResult: Resultado de validación de sintaxis
        """
        validation_details = {}
        is_valid = True
        messages = []
        
        # Verificar sintaxis Python válida
        python_syntax_valid = syntax_data.get('python_syntax_valid', False)
        validation_details['python_syntax_valid'] = python_syntax_valid
        if not python_syntax_valid:
            is_valid = False
            messages.append("Errores de sintaxis Python detectados")
            
        # Verificar convenciones de nomenclatura
        naming_conventions = syntax_data.get('naming_conventions', False)
        validation_details['naming_conventions'] = naming_conventions
        if not naming_conventions:
            is_valid = False
            messages.append("Convenciones de nomenclatura no cumplidas")
            
        # Verificar documentación presente
        documentation_present = syntax_data.get('documentation_present', False)
        validation_details['documentation_present'] = documentation_present
        if not documentation_present:
            is_valid = False
            messages.append("Documentación faltante")
            
        # Verificar imports válidos
        imports_valid = syntax_data.get('imports_valid', False)
        validation_details['imports_valid'] = imports_valid
        if not imports_valid:
            is_valid = False
            messages.append("Errores en imports detectados")
            
        if is_valid:
            messages.append("Cumplimiento de sintaxis validado exitosamente")
            
        return ValidationResult(
            instruction_id="SYNTAX_COMPLIANCE",
            is_valid=is_valid,
            validation_details=validation_details,
            message="; ".join(messages)
        )
        
    def validate_redundancy_check(self, redundancy_data: Dict[str, Any]) -> ValidationResult:
        """
        Validar verificación de redundancias.
        
        Args:
            redundancy_data: Datos de verificación de redundancias
            
        Returns:
            ValidationResult: Resultado de validación de redundancias
        """
        validation_details = {}
        is_valid = True
        messages = []
        
        # Verificar que no hay funciones duplicadas
        duplicate_functions_found = redundancy_data.get('duplicate_functions_found', True)
        validation_details['duplicate_functions_found'] = duplicate_functions_found
        if duplicate_functions_found:
            is_valid = False
            messages.append("Funciones duplicadas detectadas")
            
        # Verificar que no hay lógica similar
        similar_logic_detected = redundancy_data.get('similar_logic_detected', True)
        validation_details['similar_logic_detected'] = similar_logic_detected
        if similar_logic_detected:
            is_valid = False
            messages.append("Lógica similar detectada")
            
        # Verificar conflictos de nomenclatura
        naming_conflicts = redundancy_data.get('naming_conflicts', True)
        validation_details['naming_conflicts'] = naming_conflicts
        if naming_conflicts:
            is_valid = False
            messages.append("Conflictos de nomenclatura detectados")
            
        # Verificar consistencia arquitectónica
        architecture_consistency = redundancy_data.get('architecture_consistency', False)
        validation_details['architecture_consistency'] = architecture_consistency
        if not architecture_consistency:
            is_valid = False
            messages.append("Inconsistencias arquitectónicas detectadas")
            
        if is_valid:
            messages.append("Verificación de redundancias completada exitosamente")
            
        return ValidationResult(
            instruction_id="REDUNDANCY_CHECK",
            is_valid=is_valid,
            validation_details=validation_details,
            message="; ".join(messages)
        )
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generar reporte completo de validaciones.
        
        Returns:
            Dict: Reporte de validaciones
        """
        total_validations = len(self.validation_history)
        successful_validations = sum(1 for result in self.validation_history if result.is_valid)
        failed_validations = total_validations - successful_validations
        
        report = {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'failed_validations': failed_validations,
            'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0.0,
            'validation_history': [
                {
                    'phase': result.phase.value,
                    'is_valid': result.is_valid,
                    'completion_percentage': result.completion_percentage,
                    'failed_criteria': result.failed_criteria,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in self.validation_history
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        return report
        
    def get_validation_history(self) -> List[CheckpointValidationResult]:
        """
        Obtener historial completo de validaciones.
        
        Returns:
            List[CheckpointValidationResult]: Historial de validaciones
        """
        return self.validation_history.copy()
        
    def reset_validation_history(self):
        """Reiniciar historial de validaciones."""
        self.validation_history.clear()
        
    def calculate_phase_completion_percentage(self, phase: CompliancePhase, validation_data: Dict[str, Any]) -> float:
        """
        Calcular porcentaje de completitud de una fase.
        
        Args:
            phase: Fase a evaluar
            validation_data: Datos de validación
            
        Returns:
            float: Porcentaje de completitud (0.0 - 100.0)
        """
        if phase not in self.validation_configs:
            return 0.0
            
        config = self.validation_configs[phase]
        total_weight = 0.0
        achieved_weight = 0.0
        
        # Calcular peso total y peso logrado
        for criteria, weight in config.validation_weights.items():
            total_weight += weight
            if validation_data.get(criteria, False):
                achieved_weight += weight
                
        if total_weight == 0.0:
            return 0.0
            
        return (achieved_weight / total_weight) * 100.0
