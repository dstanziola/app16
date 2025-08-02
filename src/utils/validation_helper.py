"""
ValidationHelper - Patrón FASE 3
Helper para validaciones de datos robustas y seguras.

RESPONSABILIDADES:
- Validaciones de seguridad para usuarios
- Validaciones de datos de negocio
- Patrones de validación reutilizables
- Mensajes de error estandarizados
"""

import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging


class ValidationHelper:
    """Helper para validaciones de datos."""
    
    def __init__(self):
        """Inicializar helper de validación."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Patrones de validación comunes
        self.username_pattern = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^[\d\-\+\(\)\s]{8,20}$')
        
    def validate_username(self, username: str) -> bool:
        """
        Validar formato de nombre de usuario.
        
        Args:
            username: Nombre de usuario a validar
            
        Returns:
            True si es válido
        """
        if not username:
            return False
            
        return bool(self.username_pattern.match(username))
        
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validar fortaleza de contraseña con criterios de seguridad.
        
        Args:
            password: Contraseña a validar
            
        Returns:
            Dict con resultado de validación y detalles
        """
        result = {
            'is_valid': False,
            'score': 0,
            'errors': [],
            'recommendations': []
        }
        
        if not password:
            result['errors'].append("La contraseña no puede estar vacía")
            return result
            
        # Criterios de validación
        criteria = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special_chars': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'no_common': not self._is_common_password(password)
        }
        
        # Calcular score
        result['score'] = sum(criteria.values())
        
        # Generar errores y recomendaciones
        if not criteria['length']:
            result['errors'].append("Debe tener al menos 8 caracteres")
            
        if not criteria['uppercase']:
            result['recommendations'].append("Incluir al menos una letra mayúscula")
            
        if not criteria['lowercase']:
            result['recommendations'].append("Incluir al menos una letra minúscula")
            
        if not criteria['numbers']:
            result['recommendations'].append("Incluir al menos un número")
            
        if not criteria['special_chars']:
            result['recommendations'].append("Incluir al menos un carácter especial")
            
        if not criteria['no_common']:
            result['errors'].append("Contraseña demasiado común")
            
        # Password es válido si cumple criterios mínimos
        result['is_valid'] = (
            criteria['length'] and 
            criteria['no_common'] and
            result['score'] >= 4  # Al menos 4 de 6 criterios
        )
        
        return result
        
    def validate_role(self, role: str) -> bool:
        """
        Validar que el rol sea válido.
        
        Args:
            role: Rol a validar
            
        Returns:
            True si es válido
        """
        valid_roles = ['ADMIN', 'VENDEDOR']
        return role in valid_roles
        
    def validate_email(self, email: str) -> bool:
        """
        Validar formato de email.
        
        Args:
            email: Email a validar
            
        Returns:
            True si es válido
        """
        if not email:
            return False
            
        return bool(self.email_pattern.match(email))
        
    def validate_phone(self, phone: str) -> bool:
        """
        Validar formato de teléfono.
        
        Args:
            phone: Teléfono a validar
            
        Returns:
            True si es válido
        """
        if not phone:
            return False
            
        return bool(self.phone_pattern.match(phone))
        
    def validate_decimal_range(self, value: Any, min_value: float = None, 
                              max_value: float = None) -> bool:
        """
        Validar que un valor decimal esté en un rango.
        
        Args:
            value: Valor a validar
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
            
        Returns:
            True si está en el rango válido
        """
        try:
            decimal_value = Decimal(str(value))
            
            if min_value is not None and decimal_value < Decimal(str(min_value)):
                return False
                
            if max_value is not None and decimal_value > Decimal(str(max_value)):
                return False
                
            return True
            
        except (ValueError, TypeError):
            return False
            
    def validate_positive_integer(self, value: Any) -> bool:
        """
        Validar que un valor sea un entero positivo.
        
        Args:
            value: Valor a validar
            
        Returns:
            True si es entero positivo
        """
        try:
            int_value = int(value)
            return int_value >= 0
        except (ValueError, TypeError):
            return False
            
    def validate_non_empty_string(self, value: str, min_length: int = 1) -> bool:
        """
        Validar que una cadena no esté vacía.
        
        Args:
            value: Cadena a validar
            min_length: Longitud mínima requerida
            
        Returns:
            True si cumple los criterios
        """
        if not isinstance(value, str):
            return False
            
        return len(value.strip()) >= min_length
        
    def validate_product_data(self, **kwargs) -> Dict[str, Any]:
        """
        Validar datos completos de producto.
        
        Args:
            **kwargs: Datos del producto
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'is_valid': True,
            'errors': []
        }
        
        # Validar nombre
        nombre = kwargs.get('nombre', '')
        if not self.validate_non_empty_string(nombre, 3):
            result['errors'].append("El nombre debe tener al menos 3 caracteres")
            
        # Validar precios
        precio_venta = kwargs.get('precio_venta', 0)
        if not self.validate_decimal_range(precio_venta, 0.01):
            result['errors'].append("El precio de venta debe ser mayor a 0")
            
        precio_compra = kwargs.get('precio_compra', 0)
        if not self.validate_decimal_range(precio_compra, 0):
            result['errors'].append("El precio de compra no puede ser negativo")
            
        # Validar stock
        stock = kwargs.get('stock', 0)
        if not self.validate_positive_integer(stock):
            result['errors'].append("El stock debe ser un número entero no negativo")
            
        # Validar tasa de impuesto
        tasa_impuesto = kwargs.get('tasa_impuesto', 0)
        if not self.validate_decimal_range(tasa_impuesto, 0, 100):
            result['errors'].append("La tasa de impuesto debe estar entre 0 y 100")
            
        result['is_valid'] = len(result['errors']) == 0
        return result
        
    def validate_category_data(self, **kwargs) -> Dict[str, Any]:
        """
        Validar datos de categoría.
        
        Args:
            **kwargs: Datos de la categoría
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'is_valid': True,
            'errors': []
        }
        
        # Validar nombre
        nombre = kwargs.get('nombre', '')
        if not self.validate_non_empty_string(nombre, 2):
            result['errors'].append("El nombre debe tener al menos 2 caracteres")
            
        # Validar tipo
        tipo = kwargs.get('tipo', '')
        if tipo not in ['MATERIAL', 'SERVICIO']:
            result['errors'].append("El tipo debe ser 'MATERIAL' o 'SERVICIO'")
            
        result['is_valid'] = len(result['errors']) == 0
        return result
        
    def sanitize_string(self, value: str, max_length: int = None) -> str:
        """
        Limpiar y sanitizar una cadena.
        
        Args:
            value: Cadena a sanitizar
            max_length: Longitud máxima permitida
            
        Returns:
            Cadena sanitizada
        """
        if not isinstance(value, str):
            return ""
            
        # Limpiar espacios
        sanitized = value.strip()
        
        # Truncar si es necesario
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized
        
    def validate_barcode_format(self, barcode: str) -> bool:
        """
        Validar formato de código de barras.
        
        Args:
            barcode: Código a validar
            
        Returns:
            bool: True si es válido
        """
        if not barcode or not isinstance(barcode, str):
            return False
        
        # Limpiar el código
        clean_barcode = barcode.strip()
        
        # Debe tener al menos 3 caracteres
        if len(clean_barcode) < 3:
            return False
        
        # Solo debe contener caracteres alfanuméricos y algunos especiales
        pattern = r'^[A-Za-z0-9\-_]+$'
        return bool(re.match(pattern, clean_barcode))
        
    def _is_common_password(self, password: str) -> bool:
        """
        Verificar si la contraseña es muy común.
        
        Args:
            password: Contraseña a verificar
            
        Returns:
            True si es una contraseña común
        """
        common_passwords = {
            '123456', 'password', 'admin', 'qwerty', '123456789',
            'letmein', 'welcome', 'monkey', '1234567890', 'abc123',
            'password123', 'admin123', '12345678', '123', 'test',
            'user', 'guest', 'demo', 'root', 'toor', 'pass'
        }
        
        return password.lower() in common_passwords

    def validate_batch_data(self, data_list: List[Dict], validation_func) -> Dict[str, Any]:
        """
        Validar múltiples elementos usando una función de validación.
        
        Args:
            data_list: Lista de datos a validar
            validation_func: Función que valida un elemento individual
            
        Returns:
            Dict con resultado de validación batch
        """
        result = {
            'is_valid': True,
            'total_items': len(data_list),
            'valid_items': 0,
            'errors': [],
            'item_errors': {}
        }
        
        for index, item_data in enumerate(data_list):
            try:
                item_result = validation_func(**item_data)
                
                if item_result.get('is_valid', False):
                    result['valid_items'] += 1
                else:
                    result['item_errors'][index] = item_result.get('errors', [])
                    
            except Exception as e:
                result['errors'].append(f"Error en item {index}: {str(e)}")
                
        result['is_valid'] = result['valid_items'] == result['total_items']
        return result
    
    def validate_date_range(self, start_date, end_date) -> bool:
        """
        Validar rango de fechas.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            bool: True si el rango es válido
        """
        try:
            from datetime import datetime
            
            # Convertir a datetime si son strings
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            # Verificar que sean datetime objects
            if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
                return False
            
            # Fecha de inicio debe ser menor o igual a fecha de fin
            return start_date <= end_date
            
        except Exception:
            return False
    
    def validate_date(self, date_value) -> bool:
        """
        Validar que un valor sea una fecha válida.
        
        Args:
            date_value: Valor a validar como fecha
            
        Returns:
            bool: True si es una fecha válida
        """
        try:
            from datetime import datetime
            
            if isinstance(date_value, str):
                datetime.fromisoformat(date_value)
                return True
            elif isinstance(date_value, datetime):
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def validate_list_items(self, items: List[str], valid_values: List[str]) -> bool:
        """
        Validar que todos los elementos de una lista estén en valores válidos.
        
        Args:
            items: Lista de elementos a validar
            valid_values: Lista de valores válidos
            
        Returns:
            bool: True si todos los elementos son válidos
        """
        if not isinstance(items, list) or not isinstance(valid_values, list):
            return False
        
        return all(item in valid_values for item in items)
