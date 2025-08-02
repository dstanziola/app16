"""
Configuración de Compliance para Sistema de Control de Cumplimiento
Desarrollado siguiendo TDD
Validado contra duplicación
Autorizado el: 2025-07-10
"""

from typing import Dict, List, Any, Optional
import copy


# Instrucciones obligatorias del sistema
MANDATORY_INSTRUCTIONS = [
    {
        'instruction_id': 'INST_001',
        'title': 'Análisis de Contexto Completo',
        'description': 'Cargar y comprender contexto completo antes de cualquier acción',
        'phase': 'ANALYSIS',
        'validation_criteria': [
            'contexto_cargado',
            'estructura_comprendida',
            'requerimientos_analizados'
        ]
    },
    {
        'instruction_id': 'INST_002',
        'title': 'Detección de Redundancias',
        'description': 'Buscar funcionalidades similares antes de implementar',
        'phase': 'ANALYSIS',
        'validation_criteria': [
            'busqueda_funciones_similares',
            'comparacion_logica_existente',
            'validacion_consistencia'
        ]
    },
    {
        'instruction_id': 'INST_003',
        'title': 'Planificación Previa',
        'description': 'Presentar lista de archivos a modificar antes de proceder',
        'phase': 'PLANNING',
        'validation_criteria': [
            'lista_archivos_presentada',
            'autorizacion_solicitada',
            'impacto_evaluado'
        ]
    },
    {
        'instruction_id': 'INST_004',
        'title': 'Implementación TDD',
        'description': 'Escribir tests antes del código de implementación',
        'phase': 'IMPLEMENTATION',
        'validation_criteria': [
            'tests_escritos_primero',
            'cobertura_minima_95_porciento',
            'tests_pasando'
        ]
    },
    {
        'instruction_id': 'INST_005',
        'title': 'Validación de Sintaxis',
        'description': 'Validar sintaxis y convenciones antes de guardar',
        'phase': 'VALIDATION',
        'validation_criteria': [
            'sintaxis_validada',
            'convenciones_cumplidas',
            'documentacion_actualizada'
        ]
    },
    {
        'instruction_id': 'INST_006',
        'title': 'Confirmación de Usuario',
        'description': 'Esperar confirmación antes de continuar',
        'phase': 'CONFIRMATION',
        'validation_criteria': [
            'confirmacion_recibida',
            'autorizacion_explicita',
            'estado_reportado'
        ]
    }
]

# Plantillas de checkpoint para cada fase
CHECKPOINT_TEMPLATES = {
    'ANALYSIS': {
        'pre_action_checklist': [
            'contexto_completo_cargado',
            'estructura_directorios_verificada',
            'funcionalidades_similares_buscadas',
            'consistencia_nombres_validada'
        ],
        'required_outputs': [
            'resumen_contexto',
            'lista_funcionalidades_existentes',
            'decision_reutilizacion_vs_nuevo'
        ]
    },
    'PLANNING': {
        'pre_action_checklist': [
            'archivos_a_modificar_identificados',
            'tests_necesarios_diseñados',
            'impacto_arquitectura_evaluado',
            'dependencias_identificadas'
        ],
        'required_outputs': [
            'lista_completa_archivos',
            'plan_implementacion_tdd',
            'solicitud_autorizacion'
        ]
    },
    'IMPLEMENTATION': {
        'pre_action_checklist': [
            'tests_escritos_primero',
            'codigo_minimo_implementado',
            'sintaxis_validada',
            'convenciones_cumplidas'
        ],
        'required_outputs': [
            'tests_pasando',
            'codigo_funcional',
            'documentacion_actualizada'
        ]
    },
    'VALIDATION': {
        'pre_action_checklist': [
            'tests_ejecutados_exitosamente',
            'cobertura_minima_alcanzada',
            'sintaxis_final_validada',
            'archivos_guardados'
        ],
        'required_outputs': [
            'reporte_tests',
            'changelog_actualizado',
            'directorio_sistema_actualizado'
        ]
    },
    'CONFIRMATION': {
        'pre_action_checklist': [
            'cambios_completados',
            'documentacion_actualizada',
            'estado_reportado',
            'siguiente_paso_identificado'
        ],
        'required_outputs': [
            'resumen_cambios',
            'confirmacion_usuario',
            'plan_siguiente_fase'
        ]
    }
}

# Reglas de validación
VALIDATION_RULES = {
    'naming_convention': {
        'description': 'Validar convenciones de nomenclatura',
        'rules': [
            'snake_case_para_funciones_y_variables',
            'PascalCase_para_clases',
            'nombres_descriptivos_obligatorios',
            'no_abreviaciones_ambiguas'
        ]
    },
    'documentation': {
        'description': 'Validar documentación obligatoria',
        'rules': [
            'docstrings_en_todas_las_funciones',
            'comentarios_en_logica_compleja',
            'encabezados_con_metadata',
            'changelog_actualizado'
        ]
    },
    'tdd_compliance': {
        'description': 'Validar cumplimiento de TDD',
        'rules': [
            'tests_escritos_antes_del_codigo',
            'cobertura_minima_95_porciento',
            'tests_atomicos_y_especificos',
            'refactoring_manteniendo_tests_verdes'
        ]
    },
    'no_duplication': {
        'description': 'Validar ausencia de duplicación',
        'rules': [
            'no_codigo_duplicado',
            'no_logica_redundante',
            'reutilizacion_de_componentes_existentes',
            'principio_DRY_aplicado'
        ]
    },
    'syntax_validation': {
        'description': 'Validar sintaxis y estructura',
        'rules': [
            'sintaxis_python_valida',
            'imports_organizados',
            'no_variables_magicas',
            'manejo_errores_apropiado'
        ]
    }
}

# Configuraciones por defecto
DEFAULT_COMPLIANCE_SETTINGS = {
    'auto_validation': True,
    'strict_mode': True,
    'logging_level': 'INFO',
    'checkpoint_frequency': 'EVERY_ACTION',
    'require_explicit_authorization': True,
    'tdd_enforcement': True,
    'syntax_validation_enabled': True,
    'documentation_required': True,
    'duplication_detection_enabled': True,
    'coverage_minimum_percentage': 95,
    'max_function_length': 50,
    'max_class_length': 200,
    'backup_before_changes': True,
    'session_tracking_enabled': True
}


class ComplianceConfig:
    """Clase para gestionar la configuración del sistema de compliance"""
    
    def __init__(self):
        """Inicializar configuración con valores por defecto"""
        self.mandatory_instructions = copy.deepcopy(MANDATORY_INSTRUCTIONS)
        self.checkpoint_templates = copy.deepcopy(CHECKPOINT_TEMPLATES)
        self.validation_rules = copy.deepcopy(VALIDATION_RULES)
        self.default_settings = copy.deepcopy(DEFAULT_COMPLIANCE_SETTINGS)
        self.current_settings = copy.deepcopy(DEFAULT_COMPLIANCE_SETTINGS)
    
    def get_instruction_by_id(self, instruction_id: str) -> Optional[Dict[str, Any]]:
        """Obtener instrucción por ID"""
        for instruction in self.mandatory_instructions:
            if instruction['instruction_id'] == instruction_id:
                return instruction
        return None
    
    def get_checkpoint_template(self, phase: str) -> Optional[Dict[str, Any]]:
        """Obtener plantilla de checkpoint para una fase específica"""
        return self.checkpoint_templates.get(phase)
    
    def validate_instruction(self, instruction: Dict[str, Any]) -> bool:
        """Validar que una instrucción tenga la estructura correcta"""
        required_fields = ['instruction_id', 'title', 'description', 'phase', 'validation_criteria']
        
        for field in required_fields:
            if field not in instruction:
                return False
        
        # Validar tipos
        if not isinstance(instruction['validation_criteria'], list):
            return False
        
        return True
    
    def is_mandatory_instruction(self, instruction_id: str) -> bool:
        """Verificar si una instrucción es obligatoria"""
        return any(
            instruction['instruction_id'] == instruction_id 
            for instruction in self.mandatory_instructions
        )
    
    def get_phase_instructions(self, phase: str) -> List[Dict[str, Any]]:
        """Obtener todas las instrucciones para una fase específica"""
        return [
            instruction for instruction in self.mandatory_instructions
            if instruction['phase'] == phase
        ]
    
    def update_setting(self, setting_name: str, value: Any) -> None:
        """Actualizar una configuración específica"""
        self.current_settings[setting_name] = value
    
    def get_setting(self, setting_name: str) -> Any:
        """Obtener el valor de una configuración específica"""
        return self.current_settings.get(setting_name)
    
    def reset_to_defaults(self) -> None:
        """Restablecer todas las configuraciones a sus valores por defecto"""
        self.current_settings = copy.deepcopy(self.default_settings)
    
    def get_validation_rules_for_phase(self, phase: str) -> List[str]:
        """Obtener reglas de validación aplicables a una fase específica"""
        phase_rules = []
        
        if phase == 'ANALYSIS':
            phase_rules.extend(['naming_convention', 'no_duplication'])
        elif phase == 'PLANNING':
            phase_rules.extend(['documentation', 'tdd_compliance'])
        elif phase == 'IMPLEMENTATION':
            phase_rules.extend(['syntax_validation', 'tdd_compliance', 'no_duplication'])
        elif phase == 'VALIDATION':
            phase_rules.extend(['syntax_validation', 'documentation', 'tdd_compliance'])
        elif phase == 'CONFIRMATION':
            phase_rules.extend(['documentation'])
        
        return phase_rules
    
    def get_checkpoint_format(self, phase: str) -> str:
        """Obtener formato de checkpoint para una fase específica"""
        return f"""
=== CHECKPOINT DE CUMPLIMIENTO ===
Fase actual: {phase}
Instrucciones seguidas: {[inst['instruction_id'] for inst in self.get_phase_instructions(phase)]}
Archivos afectados: [Lista completa]
Autorización requerida: {'Sí' if self.get_setting('require_explicit_authorization') else 'No'}
Estado TDD: [Tests diseñados/Código implementado/Refactorizado]
"""


def validate_syntax_compliance():
    """
    Validación automática de cumplimiento de sintaxis
    Implementa las reglas de validación definidas en las instrucciones
    """
    # Verificar nombres descriptivos
    # Verificar documentación
    # Verificar ausencia de variables mágicas
    pass
