#!/usr/bin/env python3
"""
Script de Validación de Sintaxis para Sistema de Compliance
Desarrollado siguiendo TDD
Validado contra duplicación
Autorizado el: 2025-07-10
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


def validate_python_syntax(file_path: str) -> Tuple[bool, str]:
    """
    Valida la sintaxis de un archivo Python
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        Tuple con (es_valido, mensaje_error)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Compilar el código para verificar sintaxis
        ast.parse(content)
        return True, "Sintaxis válida"
        
    except SyntaxError as e:
        return False, f"Error de sintaxis: {e}"
    except Exception as e:
        return False, f"Error al procesar archivo: {e}"


def validate_naming_conventions(file_path: str) -> Tuple[bool, List[str]]:
    """
    Valida las convenciones de nomenclatura
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        Tuple con (es_valido, lista_warnings)
    """
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Verificar snake_case en funciones
                if not node.name.islower() or '__' in node.name:
                    if not node.name.startswith('_'):  # Permitir métodos privados
                        warnings.append(f"Función '{node.name}' no sigue snake_case")
            
            elif isinstance(node, ast.ClassDef):
                # Verificar PascalCase en clases
                if not node.name[0].isupper():
                    warnings.append(f"Clase '{node.name}' no sigue PascalCase")
        
        return len(warnings) == 0, warnings
        
    except Exception as e:
        return False, [f"Error al validar nomenclatura: {e}"]


def validate_documentation(file_path: str) -> Tuple[bool, List[str]]:
    """
    Valida la documentación del archivo
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        Tuple con (es_valido, lista_warnings)
    """
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Verificar docstring en funciones
                if not ast.get_docstring(node):
                    warnings.append(f"Función '{node.name}' no tiene docstring")
            
            elif isinstance(node, ast.ClassDef):
                # Verificar docstring en clases
                if not ast.get_docstring(node):
                    warnings.append(f"Clase '{node.name}' no tiene docstring")
        
        # Verificar encabezado del archivo
        if not content.startswith('"""') and not content.startswith("'''"):
            warnings.append("Archivo no tiene encabezado de documentación")
        
        return len(warnings) == 0, warnings
        
    except Exception as e:
        return False, [f"Error al validar documentación: {e}"]


def validate_file_comprehensive(file_path: str) -> Dict[str, Any]:
    """
    Validación completa de un archivo Python
    
    Args:
        file_path: Ruta del archivo a validar
        
    Returns:
        Diccionario con resultados de validación
    """
    results = {
        'file_path': file_path,
        'syntax_valid': False,
        'naming_valid': False,
        'documentation_valid': False,
        'overall_valid': False,
        'errors': [],
        'warnings': []
    }
    
    # Validar sintaxis
    syntax_valid, syntax_msg = validate_python_syntax(file_path)
    results['syntax_valid'] = syntax_valid
    if not syntax_valid:
        results['errors'].append(syntax_msg)
    
    # Validar nomenclatura
    naming_valid, naming_warnings = validate_naming_conventions(file_path)
    results['naming_valid'] = naming_valid
    results['warnings'].extend(naming_warnings)
    
    # Validar documentación
    doc_valid, doc_warnings = validate_documentation(file_path)
    results['documentation_valid'] = doc_valid
    results['warnings'].extend(doc_warnings)
    
    # Validación general
    results['overall_valid'] = syntax_valid and naming_valid and doc_valid
    
    return results


def validate_compliance_system() -> Dict[str, Any]:
    """
    Validar todo el sistema de compliance
    
    Returns:
        Diccionario con resultados de validación del sistema
    """
    base_path = Path('D:/inventario_app2/src/compliance')
    config_path = Path('D:/inventario_app2/src/config')
    
    files_to_validate = [
        base_path / 'models' / 'compliance_models.py',
        base_path / 'models' / '__init__.py',
        base_path / '__init__.py',
        base_path / 'utils' / '__init__.py',
        config_path / 'compliance_config.py'
    ]
    
    validation_results = {
        'total_files': len(files_to_validate),
        'valid_files': 0,
        'invalid_files': 0,
        'files_results': [],
        'overall_valid': False,
        'summary': {
            'syntax_errors': 0,
            'naming_warnings': 0,
            'documentation_warnings': 0
        }
    }
    
    for file_path in files_to_validate:
        if file_path.exists():
            result = validate_file_comprehensive(str(file_path))
            validation_results['files_results'].append(result)
            
            if result['overall_valid']:
                validation_results['valid_files'] += 1
            else:
                validation_results['invalid_files'] += 1
            
            # Contar errores y warnings
            validation_results['summary']['syntax_errors'] += len(result['errors'])
            validation_results['summary']['naming_warnings'] += len([w for w in result['warnings'] if 'snake_case' in w or 'PascalCase' in w])
            validation_results['summary']['documentation_warnings'] += len([w for w in result['warnings'] if 'docstring' in w or 'documentación' in w])
    
    validation_results['overall_valid'] = validation_results['invalid_files'] == 0
    
    return validation_results


def print_validation_report(results: Dict[str, Any]) -> None:
    """
    Imprimir reporte de validación
    
    Args:
        results: Resultados de validación
    """
    print("=" * 60)
    print("REPORTE DE VALIDACIÓN DE SINTAXIS - SISTEMA DE COMPLIANCE")
    print("=" * 60)
    print(f"Archivos validados: {results['total_files']}")
    print(f"Archivos válidos: {results['valid_files']}")
    print(f"Archivos inválidos: {results['invalid_files']}")
    print(f"Estado general: {'✓ VÁLIDO' if results['overall_valid'] else '✗ INVÁLIDO'}")
    print()
    
    print("RESUMEN DE PROBLEMAS:")
    print(f"  Errores de sintaxis: {results['summary']['syntax_errors']}")
    print(f"  Warnings de nomenclatura: {results['summary']['naming_warnings']}")
    print(f"  Warnings de documentación: {results['summary']['documentation_warnings']}")
    print()
    
    print("DETALLE POR ARCHIVO:")
    for file_result in results['files_results']:
        status = "✓" if file_result['overall_valid'] else "✗"
        print(f"  {status} {file_result['file_path']}")
        
        if file_result['errors']:
            for error in file_result['errors']:
                print(f"    ERROR: {error}")
        
        if file_result['warnings']:
            for warning in file_result['warnings']:
                print(f"    WARNING: {warning}")
    
    print("=" * 60)


if __name__ == "__main__":
    # Ejecutar validación
    results = validate_compliance_system()
    
    # Imprimir reporte
    print_validation_report(results)
    
    # Guardar reporte en archivo
    report_path = Path('D:/inventario_app2/tests/reports/syntax_validation_report.txt')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("REPORTE DE VALIDACIÓN DE SINTAXIS - SISTEMA DE COMPLIANCE\n")
        f.write("=" * 60 + "\n")
        f.write(f"Fecha: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Archivos validados: {results['total_files']}\n")
        f.write(f"Archivos válidos: {results['valid_files']}\n")
        f.write(f"Archivos inválidos: {results['invalid_files']}\n")
        f.write(f"Estado general: {'VÁLIDO' if results['overall_valid'] else 'INVÁLIDO'}\n\n")
        
        for file_result in results['files_results']:
            f.write(f"Archivo: {file_result['file_path']}\n")
            f.write(f"  Sintaxis: {'OK' if file_result['syntax_valid'] else 'ERROR'}\n")
            f.write(f"  Nomenclatura: {'OK' if file_result['naming_valid'] else 'WARNING'}\n")
            f.write(f"  Documentación: {'OK' if file_result['documentation_valid'] else 'WARNING'}\n")
            f.write(f"  Estado: {'VÁLIDO' if file_result['overall_valid'] else 'INVÁLIDO'}\n\n")
    
    print(f"\nReporte guardado en: {report_path}")
    
    # Salir con código de error si hay problemas
    sys.exit(0 if results['overall_valid'] else 1)
