"""
Ejecutor principal del flujo de compliance del sistema.

Este módulo implementa el coordinador central que gestiona la ejecución completa
del flujo de compliance, coordinando entre componentes y manejando el ciclo
completo de desarrollo siguiendo la metodología TDD establecida.
"""

import os
import sys
import ast
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.compliance.models.compliance_models import CompliancePhase, ComplianceStatus
from src.compliance.controllers.compliance_controller import ComplianceController
from src.compliance.utils.session_manager import SessionManager


class ExecutionPhase(Enum):
    """Fases de ejecución del compliance."""
    ANALYSIS = "ANALYSIS"
    PLANNING = "PLANNING"
    IMPLEMENTATION = "IMPLEMENTATION"
    VALIDATION = "VALIDATION"
    CONFIRMATION = "CONFIRMATION"


class ValidationStage(Enum):
    """Etapas de validación durante la ejecución."""
    TDD_COMPLIANCE = "TDD_COMPLIANCE"
    SYNTAX_VALIDATION = "SYNTAX_VALIDATION"
    TEST_EXECUTION = "TEST_EXECUTION"
    CHECKPOINT_VALIDATION = "CHECKPOINT_VALIDATION"


@dataclass
class ExecutionResult:
    """Resultado de ejecución de una fase."""
    success: bool
    phase: ExecutionPhase
    validation_stages: List[ValidationStage]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0


@dataclass
class ComplianceExecution:
    """Datos de una ejecución de compliance."""
    execution_id: str
    started_at: datetime
    current_phase: ExecutionPhase
    completed_phases: List[ExecutionPhase]
    is_active: bool
    results: List[ExecutionResult]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceRunner:
    """
    Ejecutor principal del flujo de compliance.
    
    Coordina la ejecución completa del proceso de compliance, gestionando
    las transiciones entre fases, validación TDD y control de calidad
    según los criterios establecidos.
    """
    
    def __init__(self, project_dir: str = None):
        """
        Inicializar ejecutor de compliance.
        
        Args:
            project_dir: Directorio del proyecto
        """
        self.project_dir = project_dir or os.getcwd()
        self.current_execution: Optional[ComplianceExecution] = None
        self.execution_history: List[ComplianceExecution] = []
        
        # Inicializar componentes de compliance
        self.session_manager = SessionManager()
        self.compliance_controller = ComplianceController()
        
        # Configuración de validación TDD
        self.tdd_coverage_threshold = 95.0
        self.syntax_validation_enabled = True
        self.test_execution_required = True
        
    def start_execution(self) -> str:
        """
        Iniciar nueva ejecución de compliance.
        
        Returns:
            str: Identificador único de la ejecución
        """
        # Finalizar ejecución activa si existe
        if self.current_execution and self.current_execution.is_active:
            self.stop_execution()
            
        execution_id = str(uuid.uuid4())
        
        self.current_execution = ComplianceExecution(
            execution_id=execution_id,
            started_at=datetime.now(),
            current_phase=ExecutionPhase.ANALYSIS,
            completed_phases=[],
            is_active=True,
            results=[]
        )
        
        # Inicializar sesión de compliance
        session_id = self.session_manager.create_session()
        self.compliance_controller.start_compliance_session()
        
        self.current_execution.metadata['session_id'] = session_id
        
        return execution_id
        
    def execute_phase(self, phase: ExecutionPhase) -> ExecutionResult:
        """
        Ejecutar fase específica de compliance.
        
        Args:
            phase: Fase a ejecutar
            
        Returns:
            ExecutionResult: Resultado de la ejecución de la fase
        """
        if not self.current_execution:
            return ExecutionResult(
                success=False,
                phase=phase,
                validation_stages=[],
                message="No hay ejecución activa"
            )
            
        start_time = datetime.now()
        validation_stages = []
        
        try:
            if phase == ExecutionPhase.ANALYSIS:
                result = self._execute_analysis_phase()
                validation_stages.append(ValidationStage.CHECKPOINT_VALIDATION)
                
            elif phase == ExecutionPhase.PLANNING:
                result = self._execute_planning_phase()
                validation_stages.append(ValidationStage.CHECKPOINT_VALIDATION)
                
            elif phase == ExecutionPhase.IMPLEMENTATION:
                result = self._execute_implementation_phase()
                validation_stages.extend([
                    ValidationStage.TDD_COMPLIANCE,
                    ValidationStage.SYNTAX_VALIDATION
                ])
                
            elif phase == ExecutionPhase.VALIDATION:
                result = self._execute_validation_phase()
                validation_stages.extend([
                    ValidationStage.SYNTAX_VALIDATION,
                    ValidationStage.TEST_EXECUTION
                ])
                
            elif phase == ExecutionPhase.CONFIRMATION:
                result = self._execute_confirmation_phase()
                validation_stages.append(ValidationStage.CHECKPOINT_VALIDATION)
                
            else:
                result = ExecutionResult(
                    success=False,
                    phase=phase,
                    validation_stages=[],
                    message=f"Fase no reconocida: {phase}"
                )
                
            # Calcular duración
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
            result.validation_stages = validation_stages
            
            # Actualizar ejecución actual
            self.current_execution.results.append(result)
            if result.success and phase not in self.current_execution.completed_phases:
                self.current_execution.completed_phases.append(phase)
                
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_result = ExecutionResult(
                success=False,
                phase=phase,
                validation_stages=validation_stages,
                message=f"Error durante ejecución de fase {phase.value}: {str(e)}",
                duration_seconds=duration
            )
            
            self.current_execution.results.append(error_result)
            return error_result
            
    def run_complete_workflow(self) -> ExecutionResult:
        """
        Ejecutar flujo completo de trabajo de compliance.
        
        Returns:
            ExecutionResult: Resultado de la ejecución completa
        """
        if not self.current_execution:
            self.start_execution()
            
        workflow_start = datetime.now()
        phases_to_execute = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.PLANNING,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.VALIDATION,
            ExecutionPhase.CONFIRMATION
        ]
        
        successful_phases = 0
        failed_phase = None
        
        for phase in phases_to_execute:
            result = self.execute_phase(phase)
            
            if result.success:
                successful_phases += 1
                self.current_execution.current_phase = phase
            else:
                failed_phase = phase
                break
                
        workflow_end = datetime.now()
        total_duration = (workflow_end - workflow_start).total_seconds()
        
        if failed_phase:
            return ExecutionResult(
                success=False,
                phase=failed_phase,
                validation_stages=[],
                message=f"Flujo de trabajo falló en fase {failed_phase.value}",
                duration_seconds=total_duration
            )
        else:
            return ExecutionResult(
                success=True,
                phase=ExecutionPhase.CONFIRMATION,
                validation_stages=[],
                message="Flujo de trabajo completado exitosamente",
                duration_seconds=total_duration
            )
            
    def _execute_analysis_phase(self) -> ExecutionResult:
        """Ejecutar fase de análisis."""
        checkpoint_result = self.compliance_controller.execute_checkpoint()
        
        if checkpoint_result.is_valid:
            self.compliance_controller.advance_to_next_phase()
            return ExecutionResult(
                success=True,
                phase=ExecutionPhase.ANALYSIS,
                validation_stages=[],
                message="Fase de análisis completada exitosamente"
            )
        else:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.ANALYSIS,
                validation_stages=[],
                message="Validación de checkpoint de análisis falló"
            )
            
    def _execute_planning_phase(self) -> ExecutionResult:
        """Ejecutar fase de planificación."""
        advance_result = self.compliance_controller.advance_to_next_phase()
        
        if advance_result:
            return ExecutionResult(
                success=True,
                phase=ExecutionPhase.PLANNING,
                validation_stages=[],
                message="Fase de planificación completada exitosamente"
            )
        else:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.PLANNING,
                validation_stages=[],
                message="Error al avanzar a fase de planificación"
            )
            
    def _execute_implementation_phase(self) -> ExecutionResult:
        """Ejecutar fase de implementación."""
        # Validar cumplimiento TDD
        tdd_valid = self._validate_tdd_compliance()
        
        if not tdd_valid:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.IMPLEMENTATION,
                validation_stages=[ValidationStage.TDD_COMPLIANCE],
                message="Validación TDD falló: tests deben escribirse antes del código"
            )
            
        # Validar sintaxis
        syntax_valid = self._run_syntax_validation()
        
        if not syntax_valid:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.IMPLEMENTATION,
                validation_stages=[ValidationStage.SYNTAX_VALIDATION],
                message="Validación de sintaxis falló"
            )
            
        return ExecutionResult(
            success=True,
            phase=ExecutionPhase.IMPLEMENTATION,
            validation_stages=[
                ValidationStage.TDD_COMPLIANCE,
                ValidationStage.SYNTAX_VALIDATION
            ],
            message="Fase de implementación completada exitosamente"
        )
        
    def _execute_validation_phase(self) -> ExecutionResult:
        """Ejecutar fase de validación."""
        # Ejecutar validación de sintaxis
        syntax_valid = self._run_syntax_validation()
        
        if not syntax_valid:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.VALIDATION,
                validation_stages=[ValidationStage.SYNTAX_VALIDATION],
                message="Validación de sintaxis falló"
            )
            
        # Ejecutar suite de tests
        tests_valid = self._run_test_suite()
        
        if not tests_valid:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.VALIDATION,
                validation_stages=[ValidationStage.TEST_EXECUTION],
                message="Ejecución de tests falló"
            )
            
        return ExecutionResult(
            success=True,
            phase=ExecutionPhase.VALIDATION,
            validation_stages=[
                ValidationStage.SYNTAX_VALIDATION,
                ValidationStage.TEST_EXECUTION
            ],
            message="Fase de validación completada exitosamente"
        )
        
    def _execute_confirmation_phase(self) -> ExecutionResult:
        """Ejecutar fase de confirmación."""
        confirmation_received = self._wait_for_user_confirmation()
        
        if confirmation_received:
            return ExecutionResult(
                success=True,
                phase=ExecutionPhase.CONFIRMATION,
                validation_stages=[ValidationStage.CHECKPOINT_VALIDATION],
                message="Confirmación recibida exitosamente"
            )
        else:
            return ExecutionResult(
                success=False,
                phase=ExecutionPhase.CONFIRMATION,
                validation_stages=[ValidationStage.CHECKPOINT_VALIDATION],
                message="Confirmación del usuario denegada"
            )
            
    def _validate_tdd_compliance(self) -> bool:
        """
        Validar cumplimiento de metodología TDD.
        
        Returns:
            bool: True si cumple con TDD
        """
        try:
            # Buscar archivos de tests y código fuente
            test_files = []
            source_files = []
            
            for root, dirs, files in os.walk(self.project_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        if 'test' in root.lower() or file.startswith('test_'):
                            test_files.append(file_path)
                        elif 'src' in root or not ('test' in root.lower()):
                            source_files.append(file_path)
                            
            # Para cada archivo fuente debe existir al menos un test
            source_modules = set()
            test_modules = set()
            
            for src_file in source_files:
                module_name = os.path.basename(src_file).replace('.py', '')
                if not module_name.startswith('__'):
                    source_modules.add(module_name)
                    
            for test_file in test_files:
                module_name = os.path.basename(test_file).replace('test_', '').replace('.py', '')
                test_modules.add(module_name)
                
            # Verificar cobertura de tests
            untested_modules = source_modules - test_modules
            coverage_percentage = ((len(source_modules) - len(untested_modules)) / len(source_modules)) * 100 if source_modules else 100
            
            return coverage_percentage >= self.tdd_coverage_threshold
            
        except Exception:
            return False
            
    def _run_syntax_validation(self) -> bool:
        """
        Ejecutar validación de sintaxis en archivos Python.
        
        Returns:
            bool: True si no hay errores de sintaxis
        """
        try:
            syntax_errors = []
            
            for root, dirs, files in os.walk(self.project_dir):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                source_code = f.read()
                                
                            ast.parse(source_code)
                            
                        except SyntaxError as e:
                            syntax_errors.append(f"{file_path}: {str(e)}")
                        except Exception:
                            # Ignorar otros errores de archivo
                            continue
                            
            return len(syntax_errors) == 0
            
        except Exception:
            return False
            
    def _run_test_suite(self) -> bool:
        """
        Ejecutar suite completa de tests.
        
        Returns:
            bool: True si todos los tests pasan
        """
        try:
            # Ejecutar pytest o unittest
            test_commands = [
                ['python', '-m', 'pytest', '-v'],
                ['python', '-m', 'unittest', 'discover', '-s', 'tests']
            ]
            
            for command in test_commands:
                try:
                    result = subprocess.run(
                        command,
                        cwd=self.project_dir,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutos timeout
                    )
                    
                    return result.returncode == 0
                    
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                    
            return False
            
        except Exception:
            return False
            
    def _wait_for_user_confirmation(self) -> bool:
        """
        Esperar confirmación explícita del usuario.
        
        Returns:
            bool: True si el usuario confirma
        """
        try:
            response = input("¿Confirma proceder con la siguiente fase? (y/n): ").lower().strip()
            return response in ['y', 'yes', 'sí', 'si']
        except (EOFError, KeyboardInterrupt):
            return False
            
    def generate_execution_report(self) -> Dict[str, Any]:
        """
        Generar reporte de ejecución actual.
        
        Returns:
            Dict: Reporte de ejecución
        """
        if not self.current_execution:
            return {}
            
        total_phases = len(list(ExecutionPhase))
        completed_phases = len(self.current_execution.completed_phases)
        success_rate = (completed_phases / total_phases) * 100
        
        total_duration = sum(
            result.duration_seconds for result in self.current_execution.results
        )
        
        report = {
            'execution_id': self.current_execution.execution_id,
            'started_at': self.current_execution.started_at.isoformat(),
            'current_phase': self.current_execution.current_phase.value,
            'completed_phases': [phase.value for phase in self.current_execution.completed_phases],
            'success_rate': round(success_rate, 2),
            'total_duration': round(total_duration, 2),
            'phase_results': [
                {
                    'phase': result.phase.value,
                    'success': result.success,
                    'message': result.message,
                    'duration': result.duration_seconds,
                    'validation_stages': [stage.value for stage in result.validation_stages]
                }
                for result in self.current_execution.results
            ],
            'is_active': self.current_execution.is_active,
            'metadata': self.current_execution.metadata
        }
        
        return report
        
    def get_execution_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de ejecución.
        
        Returns:
            Dict: Estado de ejecución
        """
        if not self.current_execution:
            return {
                'is_running': False,
                'current_phase': None,
                'progress_percentage': 0.0,
                'last_activity': None
            }
            
        total_phases = len(list(ExecutionPhase))
        completed_phases = len(self.current_execution.completed_phases)
        progress_percentage = (completed_phases / total_phases) * 100
        
        last_activity = None
        if self.current_execution.results:
            last_activity = max(
                result.timestamp for result in self.current_execution.results
            ).isoformat()
            
        return {
            'is_running': self.current_execution.is_active,
            'current_phase': self.current_execution.current_phase.value,
            'progress_percentage': round(progress_percentage, 2),
            'last_activity': last_activity,
            'execution_id': self.current_execution.execution_id
        }
        
    def stop_execution(self) -> Optional[ComplianceExecution]:
        """
        Detener ejecución activa.
        
        Returns:
            ComplianceExecution: Ejecución detenida
        """
        if not self.current_execution:
            return None
            
        self.current_execution.is_active = False
        stopped_execution = self.current_execution
        
        # Agregar a historial
        self.execution_history.append(stopped_execution)
        
        # Cerrar sesión de compliance
        self.session_manager.close_session()
        
        self.current_execution = None
        
        return stopped_execution
        
    def resume_execution(self, execution_id: str) -> bool:
        """
        Reanudar ejecución detenida.
        
        Args:
            execution_id: ID de la ejecución a reanudar
            
        Returns:
            bool: True si se reanudó exitosamente
        """
        try:
            # Buscar ejecución en historial
            execution_to_resume = None
            for execution in self.execution_history:
                if execution.execution_id == execution_id:
                    execution_to_resume = execution
                    break
                    
            if not execution_to_resume:
                return False
                
            # Reactivar ejecución
            execution_to_resume.is_active = True
            self.current_execution = execution_to_resume
            
            # Restaurar sesión
            session_id = execution_to_resume.metadata.get('session_id')
            if session_id:
                self.session_manager.load_session(f"session_{session_id}.json")
                
            return True
            
        except Exception:
            return False
            
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Obtener historial de ejecuciones.
        
        Returns:
            List[Dict]: Lista de ejecuciones históricas
        """
        history = []
        
        for execution in self.execution_history:
            history.append({
                'execution_id': execution.execution_id,
                'started_at': execution.started_at.isoformat(),
                'completed_phases': [phase.value for phase in execution.completed_phases],
                'is_active': execution.is_active,
                'total_results': len(execution.results)
            })
            
        return history
        
    def validate_checkpoint(self, checkpoint_data: Dict[str, Any]) -> bool:
        """
        Validar finalización de checkpoint.
        
        Args:
            checkpoint_data: Datos del checkpoint
            
        Returns:
            bool: True si el checkpoint es válido
        """
        required_fields = ['phase', 'validations', 'status']
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in checkpoint_data:
                return False
                
        # Verificar estado completado
        if checkpoint_data['status'] != ComplianceStatus.COMPLETED:
            return False
            
        # Verificar que todas las validaciones estén completadas
        validations = checkpoint_data.get('validations', {})
        if isinstance(validations, dict):
            return all(validations.values())
            
        return False
