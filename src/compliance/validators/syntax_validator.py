"""
Validador de sintaxis del sistema de compliance.

Este módulo implementa el sistema de validación de sintaxis en tiempo real
que verifica automáticamente el cumplimiento de estándares de codificación,
convenciones de nomenclatura y documentación según las mejores prácticas.
"""

import ast
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.compliance.models.compliance_models import ValidationResult


@dataclass
class SyntaxValidationResult:
    """Resultado de validación de sintaxis."""
    file_path: str
    is_valid: bool
    validation_details: Dict[str, Any]
    failed_rules: List[str]
    messages: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class SyntaxValidationConfig:
    """Configuración de validación de sintaxis."""
    max_line_length: int = 88
    max_complexity: int = 10
    require_docstrings: bool = True
    enforce_naming_conventions: bool = True
    check_import_organization: bool = True
    enable_all_rules: bool = True


@dataclass
class ValidationRule:
    """Regla de validación específica."""
    name: str
    description: str
    severity: str = 'error'  # 'error', 'warning', 'info'
    enabled: bool = True


class SyntaxValidator:
    """
    Validador de sintaxis del sistema de compliance.
    
    Proporciona validación automática y en tiempo real de código Python
    verificando sintaxis, convenciones de nomenclatura, documentación,
    organización de imports y complejidad de código.
    """
    
    def __init__(self):
        """Inicializar validador de sintaxis."""
        self.validation_config = SyntaxValidationConfig()
        self.validation_rules = []
        self.validation_history = []
        self.load_validation_rules()
        
    def load_validation_rules(self):
        """Cargar reglas de validación predefinidas."""
        self.validation_rules = [
            ValidationRule(
                name='python_syntax',
                description='Validar sintaxis Python correcta',
                severity='error'
            ),
            ValidationRule(
                name='naming_conventions',
                description='Verificar convenciones de nomenclatura snake_case y PascalCase',
                severity='warning'
            ),
            ValidationRule(
                name='documentation_presence',
                description='Verificar presencia de docstrings en funciones y clases',
                severity='warning'
            ),
            ValidationRule(
                name='import_organization',
                description='Verificar organización correcta de imports según PEP 8',
                severity='info'
            ),
            ValidationRule(
                name='code_complexity',
                description='Verificar complejidad ciclomática aceptable',
                severity='warning'
            ),
            ValidationRule(
                name='line_length',
                description='Verificar longitud de líneas dentro del límite',
                severity='info'
            )
        ]
        
    def validate_python_syntax(self, file_path: str) -> ValidationResult:
        """
        Validar sintaxis Python de un archivo.
        
        Args:
            file_path: Ruta del archivo a validar
            
        Returns:
            ValidationResult: Resultado de validación de sintaxis
        """
        validation_details = {}
        is_valid = True
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Intentar parsear el archivo con AST
            ast.parse(content)
            validation_details['syntax_valid'] = True
            messages.append("Sintaxis Python válida")
            
        except SyntaxError as e:
            is_valid = False
            validation_details['syntax_valid'] = False
            validation_details['syntax_errors'] = [
                {
                    'line': e.lineno,
                    'column': e.offset,
                    'message': str(e.msg),
                    'text': e.text.strip() if e.text else ''
                }
            ]
            messages.append(f"Error de sintaxis en línea {e.lineno}: {e.msg}")
            
        except FileNotFoundError:
            is_valid = False
            validation_details['file_error'] = f"Archivo no encontrado: {file_path}"
            messages.append(f"Archivo no encontrado: {file_path}")
            
        except Exception as e:
            is_valid = False
            validation_details['unexpected_error'] = str(e)
            messages.append(f"Error inesperado: {str(e)}")
            
        return ValidationResult(
            instruction_id="PYTHON_SYNTAX",
            is_valid=is_valid,
            validation_details=validation_details,
            message="; ".join(messages)
        )
        
    def validate_naming_conventions(self, code_content: str) -> ValidationResult:
        """
        Validar convenciones de nomenclatura.
        
        Args:
            code_content: Contenido del código a validar
            
        Returns:
            ValidationResult: Resultado de validación de nomenclatura
        """
        validation_details = {}
        is_valid = True
        violations = []
        
        try:
            tree = ast.parse(code_content)
            
            # Patrones de nomenclatura
            snake_case_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')
            pascal_case_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
            
            # Verificar funciones y métodos
            function_violations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not snake_case_pattern.match(node.name):
                        function_violations.append(f"Función '{node.name}' no sigue snake_case")
                        
            # Verificar clases
            class_violations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not pascal_case_pattern.match(node.name):
                        class_violations.append(f"Clase '{node.name}' no sigue PascalCase")
                        
            # Verificar variables (simplificado - solo asignaciones directas)
            variable_violations = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if not snake_case_pattern.match(target.id):
                                variable_violations.append(f"Variable '{target.id}' no sigue snake_case")
                                
            validation_details['function_naming'] = len(function_violations) == 0
            validation_details['class_naming'] = len(class_violations) == 0
            validation_details['variable_naming'] = len(variable_violations) == 0
            
            all_violations = function_violations + class_violations + variable_violations
            
            if all_violations:
                is_valid = False
                validation_details['naming_violations'] = all_violations
                
        except SyntaxError:
            is_valid = False
            validation_details['parse_error'] = "No se pudo parsear el código para validar nomenclatura"
            
        return ValidationResult(
            instruction_id="NAMING_CONVENTIONS",
            is_valid=is_valid,
            validation_details=validation_details,
            message="Convenciones de nomenclatura validadas" if is_valid else f"Violaciones encontradas: {len(all_violations) if 'all_violations' in locals() else 0}"
        )
        
    def validate_documentation_presence(self, code_content: str) -> ValidationResult:
        """
        Validar presencia de documentación.
        
        Args:
            code_content: Contenido del código a validar
            
        Returns:
            ValidationResult: Resultado de validación de documentación
        """
        validation_details = {}
        is_valid = True
        missing_docstrings = []
        
        try:
            tree = ast.parse(code_content)
            
            # Verificar docstring del módulo
            module_docstring = ast.get_docstring(tree)
            validation_details['module_docstring'] = module_docstring is not None
            
            # Verificar docstrings de funciones
            function_docstrings = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring is None:
                        missing_docstrings.append(f"Función '{node.name}' sin docstring")
                        function_docstrings.append(False)
                    else:
                        function_docstrings.append(True)
                        
            # Verificar docstrings de clases
            class_docstrings = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if docstring is None:
                        missing_docstrings.append(f"Clase '{node.name}' sin docstring")
                        class_docstrings.append(False)
                    else:
                        class_docstrings.append(True)
                        
            validation_details['function_docstrings'] = all(function_docstrings) if function_docstrings else True
            validation_details['class_docstrings'] = all(class_docstrings) if class_docstrings else True
            
            if missing_docstrings:
                is_valid = False
                validation_details['missing_docstrings'] = missing_docstrings
                
        except SyntaxError:
            is_valid = False
            validation_details['parse_error'] = "No se pudo parsear el código para validar documentación"
            
        return ValidationResult(
            instruction_id="DOCUMENTATION_PRESENCE",
            is_valid=is_valid,
            validation_details=validation_details,
            message="Documentación completa" if is_valid else f"Faltan {len(missing_docstrings)} docstrings"
        )
        
    def validate_import_organization(self, code_content: str) -> ValidationResult:
        """
        Validar organización de imports según PEP 8.
        
        Args:
            code_content: Contenido del código a validar
            
        Returns:
            ValidationResult: Resultado de validación de imports
        """
        validation_details = {}
        is_valid = True
        violations = []
        
        try:
            tree = ast.parse(code_content)
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append({
                        'type': 'import' if isinstance(node, ast.Import) else 'from_import',
                        'module': getattr(node, 'module', None),
                        'names': [alias.name for alias in node.names],
                        'lineno': node.lineno
                    })
                    
            # Verificar orden de imports (simplificado)
            # Orden esperado: stdlib, third-party, local
            stdlib_modules = {'os', 'sys', 'datetime', 'typing', 'collections', 'itertools', 'functools'}
            
            previous_type = None
            order_violations = []
            
            for imp in imports:
                current_type = 'stdlib'
                if imp['module']:
                    if imp['module'].startswith('src.'):
                        current_type = 'local'
                    elif imp['module'] not in stdlib_modules:
                        current_type = 'third_party'
                        
                if previous_type and self._compare_import_order(previous_type, current_type) > 0:
                    order_violations.append(f"Import mal ordenado en línea {imp['lineno']}")
                    
                previous_type = current_type
                
            validation_details['import_order'] = len(order_violations) == 0
            
            if order_violations:
                is_valid = False
                validation_details['import_order_violations'] = order_violations
                
        except SyntaxError:
            is_valid = False
            validation_details['parse_error'] = "No se pudo parsear el código para validar imports"
            
        return ValidationResult(
            instruction_id="IMPORT_ORGANIZATION",
            is_valid=is_valid,
            validation_details=validation_details,
            message="Imports correctamente organizados" if is_valid else f"Violaciones de orden: {len(violations) if violations else 0}"
        )
        
    def _compare_import_order(self, type1: str, type2: str) -> int:
        """Comparar orden de tipos de import."""
        order = {'stdlib': 0, 'third_party': 1, 'local': 2}
        return order.get(type1, 2) - order.get(type2, 2)
        
    def validate_code_complexity(self, code_content: str) -> ValidationResult:
        """
        Validar complejidad ciclomática del código.
        
        Args:
            code_content: Contenido del código a validar
            
        Returns:
            ValidationResult: Resultado de validación de complejidad
        """
        validation_details = {}
        is_valid = True
        violations = []
        
        try:
            tree = ast.parse(code_content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    validation_details[f'complexity_{node.name}'] = complexity
                    
                    if complexity > self.validation_config.max_complexity:
                        violations.append(f"Función '{node.name}' tiene complejidad {complexity} (máximo {self.validation_config.max_complexity})")
                        
            validation_details['complexity_score'] = max(validation_details.values()) if validation_details else 1
            
            if violations:
                is_valid = False
                validation_details['complexity_violations'] = violations
                
        except SyntaxError:
            is_valid = False
            validation_details['parse_error'] = "No se pudo parsear el código para validar complejidad"
            
        return ValidationResult(
            instruction_id="CODE_COMPLEXITY",
            is_valid=is_valid,
            validation_details=validation_details,
            message="Complejidad aceptable" if is_valid else f"Violaciones de complejidad: {len(violations)}"
        )
        
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcular complejidad ciclomática simplificada."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        return complexity
        
    def validate_line_length(self, code_content: str) -> ValidationResult:
        """
        Validar longitud de líneas.
        
        Args:
            code_content: Contenido del código a validar
            
        Returns:
            ValidationResult: Resultado de validación de longitud
        """
        validation_details = {}
        is_valid = True
        long_lines = []
        
        lines = code_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if len(line) > self.validation_config.max_line_length:
                long_lines.append({
                    'line_number': i,
                    'length': len(line),
                    'content': line.strip()[:50] + '...' if len(line.strip()) > 50 else line.strip()
                })
                
        validation_details['line_length_violations'] = len(long_lines)
        validation_details['max_line_length'] = self.validation_config.max_line_length
        
        if long_lines:
            is_valid = False
            validation_details['long_lines'] = long_lines
            
        return ValidationResult(
            instruction_id="LINE_LENGTH",
            is_valid=is_valid,
            validation_details=validation_details,
            message="Longitud de líneas aceptable" if is_valid else f"Líneas largas encontradas: {len(long_lines)}"
        )
        
    def validate_file(self, file_path: str) -> SyntaxValidationResult:
        """
        Validar archivo completo con todas las reglas.
        
        Args:
            file_path: Ruta del archivo a validar
            
        Returns:
            SyntaxValidationResult: Resultado completo de validación
        """
        validation_details = {}
        failed_rules = []
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Ejecutar todas las validaciones
            syntax_result = self.validate_python_syntax(file_path)
            naming_result = self.validate_naming_conventions(content)
            docs_result = self.validate_documentation_presence(content)
            imports_result = self.validate_import_organization(content)
            complexity_result = self.validate_code_complexity(content)
            length_result = self.validate_line_length(content)
            
            # Consolidar resultados
            results = [
                ('python_syntax', syntax_result),
                ('naming_conventions', naming_result),
                ('documentation_presence', docs_result),
                ('import_organization', imports_result),
                ('code_complexity', complexity_result),
                ('line_length', length_result)
            ]
            
            overall_valid = True
            
            for rule_name, result in results:
                validation_details[rule_name] = result.validation_details
                messages.append(result.message)
                
                if not result.is_valid:
                    overall_valid = False
                    failed_rules.append(rule_name)
                    
        except Exception as e:
            overall_valid = False
            failed_rules.append('file_processing')
            validation_details['file_error'] = str(e)
            messages.append(f"Error procesando archivo: {str(e)}")
            
        result = SyntaxValidationResult(
            file_path=file_path,
            is_valid=overall_valid,
            validation_details=validation_details,
            failed_rules=failed_rules,
            messages=messages
        )
        
        self.validation_history.append(result)
        return result
        
    def validate_multiple_files(self, file_paths: List[str]) -> List[SyntaxValidationResult]:
        """
        Validar múltiples archivos.
        
        Args:
            file_paths: Lista de rutas de archivos
            
        Returns:
            List[SyntaxValidationResult]: Resultados de validación
        """
        results = []
        
        for file_path in file_paths:
            if file_path.endswith('.py'):
                result = self.validate_file(file_path)
                results.append(result)
                
        return results
        
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generar reporte completo de validaciones.
        
        Returns:
            Dict: Reporte de validaciones
        """
        total_validations = len(self.validation_history)
        successful_validations = sum(1 for result in self.validation_history if result.is_valid)
        failed_validations = total_validations - successful_validations
        
        # Consolidar estadísticas por regla
        rule_stats = {}
        for result in self.validation_history:
            for rule in result.failed_rules:
                rule_stats[rule] = rule_stats.get(rule, 0) + 1
                
        report = {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'failed_validations': failed_validations,
            'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0.0,
            'rule_failure_stats': rule_stats,
            'validation_summary': [
                {
                    'file_path': result.file_path,
                    'is_valid': result.is_valid,
                    'failed_rules': result.failed_rules,
                    'timestamp': result.timestamp.isoformat()
                }
                for result in self.validation_history
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        return report
        
    def get_validation_config(self) -> SyntaxValidationConfig:
        """
        Obtener configuración actual de validación.
        
        Returns:
            SyntaxValidationConfig: Configuración de validación
        """
        return self.validation_config
