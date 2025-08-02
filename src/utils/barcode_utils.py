"""
Utilidades para códigos de barras.

Este módulo proporciona funciones auxiliares para el manejo de códigos de barras:
- Validación de formatos específicos
- Cálculo de checksums
- Conversión entre formatos
- Generación de códigos aleatorios
- Extracción de información de códigos

Autor: Sistema de Inventario Copy Point S.A.
Fecha: Junio 2025
"""

import logging
import re
import random
import string
from typing import Dict, Optional, List, Tuple, Any
from decimal import Decimal

# Configurar logging
logger = logging.getLogger(__name__)


class BarcodeUtils:
    """
    Clase utilitaria para operaciones con códigos de barras.
    
    Proporciona métodos estáticos para validación, conversión y manipulación
    de códigos de barras en diferentes formatos.
    """
    
    # Patrones de validación para diferentes formatos
    VALIDATION_PATTERNS = {
        'CODE128': r'^[\x20-\x7F]+$',  # ASCII imprimible
        'CODE39': r'^[A-Z0-9\-\.\$\/\+\%\s]+$',  # Caracteres válidos Code39
        'EAN13': r'^\d{13}$',  # Exactamente 13 dígitos
        'EAN8': r'^\d{8}$',   # Exactamente 8 dígitos
        'UPC': r'^\d{12}$',   # Exactamente 12 dígitos
        'UPCA': r'^\d{12}$',  # Mismo que UPC
        'ISBN': r'^\d{10}(\d{3})?$',  # 10 o 13 dígitos
    }
    
    # Longitudes válidas por formato
    VALID_LENGTHS = {
        'EAN13': [13],
        'EAN8': [8],
        'UPC': [12],
        'UPCA': [12],
        'CODE128': list(range(1, 49)),  # Variable, máximo 48 caracteres
        'CODE39': list(range(1, 44)),   # Variable, máximo 43 caracteres
        'ISBN': [10, 13],
    }
    
    @staticmethod
    def validate_ean13(code: str) -> bool:
        """
        Validar código EAN-13.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Limpiar código
            clean_code = code.strip().replace('-', '').replace(' ', '')
            
            # Verificar longitud y formato
            if not re.match(BarcodeUtils.VALIDATION_PATTERNS['EAN13'], clean_code):
                return False
            
            # Calcular checksum
            calculated_checksum = BarcodeUtils.calculate_ean13_checksum(clean_code[:-1])
            provided_checksum = int(clean_code[-1])
            
            return calculated_checksum == provided_checksum
            
        except Exception as e:
            logger.debug(f"Error validando EAN13 {code}: {e}")
            return False
    
    @staticmethod
    def validate_ean8(code: str) -> bool:
        """
        Validar código EAN-8.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Limpiar código
            clean_code = code.strip().replace('-', '').replace(' ', '')
            
            # Verificar longitud y formato
            if not re.match(BarcodeUtils.VALIDATION_PATTERNS['EAN8'], clean_code):
                return False
            
            # Calcular checksum
            calculated_checksum = BarcodeUtils.calculate_ean8_checksum(clean_code[:-1])
            provided_checksum = int(clean_code[-1])
            
            return calculated_checksum == provided_checksum
            
        except Exception as e:
            logger.debug(f"Error validando EAN8 {code}: {e}")
            return False
    
    @staticmethod
    def validate_upc(code: str) -> bool:
        """
        Validar código UPC-A.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Limpiar código
            clean_code = code.strip().replace('-', '').replace(' ', '')
            
            # Verificar longitud y formato
            if not re.match(BarcodeUtils.VALIDATION_PATTERNS['UPC'], clean_code):
                return False
            
            # Calcular checksum UPC (similar a EAN13)
            calculated_checksum = BarcodeUtils.calculate_upc_checksum(clean_code[:-1])
            provided_checksum = int(clean_code[-1])
            
            return calculated_checksum == provided_checksum
            
        except Exception as e:
            logger.debug(f"Error validando UPC {code}: {e}")
            return False
    
    @staticmethod
    def validate_code128(code: str) -> bool:
        """
        Validar código Code128.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Verificar caracteres válidos (ASCII imprimible)
            if not re.match(BarcodeUtils.VALIDATION_PATTERNS['CODE128'], code):
                return False
            
            # Verificar longitud
            if len(code) < 1 or len(code) > 48:
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error validando Code128 {code}: {e}")
            return False
    
    @staticmethod
    def validate_code39(code: str) -> bool:
        """
        Validar código Code39.
        
        Args:
            code: Código a validar
            
        Returns:
            bool: True si el código es válido
        """
        try:
            if not code or not isinstance(code, str):
                return False
            
            # Convertir a mayúsculas
            upper_code = code.upper()
            
            # Verificar caracteres válidos
            if not re.match(BarcodeUtils.VALIDATION_PATTERNS['CODE39'], upper_code):
                return False
            
            # Verificar longitud
            if len(upper_code) < 1 or len(upper_code) > 43:
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Error validando Code39 {code}: {e}")
            return False
    
    @staticmethod
    def calculate_checksum(code: str, format: str) -> str:
        """
        Calcular checksum para un código según su formato.
        
        Args:
            code: Código sin checksum
            format: Formato del código (EAN13, EAN8, UPC, etc.)
            
        Returns:
            str: Checksum calculado
            
        Raises:
            ValueError: Si el formato no es soportado
        """
        format_upper = format.upper()
        
        if format_upper == 'EAN13':
            return str(BarcodeUtils.calculate_ean13_checksum(code))
        elif format_upper == 'EAN8':
            return str(BarcodeUtils.calculate_ean8_checksum(code))
        elif format_upper in ['UPC', 'UPCA']:
            return str(BarcodeUtils.calculate_upc_checksum(code))
        elif format_upper == 'CODE39':
            # Code39 opcionalmente usa checksum
            return BarcodeUtils.calculate_code39_checksum(code)
        elif format_upper == 'CODE128':
            # Code128 no usa checksum externo (maneja internamente)
            return ''
        else:
            raise ValueError(f"Formato {format} no soportado para cálculo de checksum")
    
    @staticmethod
    def calculate_ean13_checksum(code: str) -> int:
        """
        Calcular checksum EAN-13.
        
        Args:
            code: Código de 12 dígitos
            
        Returns:
            int: Dígito de checksum
        """
        if len(code) != 12:
            raise ValueError("EAN13 requiere exactamente 12 dígitos para calcular checksum")
        
        total = 0
        for i, digit in enumerate(code):
            weight = 3 if i % 2 == 1 else 1
            total += int(digit) * weight
        
        checksum = (10 - (total % 10)) % 10
        return checksum
    
    @staticmethod
    def calculate_ean8_checksum(code: str) -> int:
        """
        Calcular checksum EAN-8.
        
        Args:
            code: Código de 7 dígitos
            
        Returns:
            int: Dígito de checksum
        """
        if len(code) != 7:
            raise ValueError("EAN8 requiere exactamente 7 dígitos para calcular checksum")
        
        total = 0
        for i, digit in enumerate(code):
            weight = 3 if i % 2 == 1 else 1
            total += int(digit) * weight
        
        checksum = (10 - (total % 10)) % 10
        return checksum
    
    @staticmethod
    def calculate_upc_checksum(code: str) -> int:
        """
        Calcular checksum UPC-A.
        
        Args:
            code: Código de 11 dígitos
            
        Returns:
            int: Dígito de checksum
        """
        if len(code) != 11:
            raise ValueError("UPC requiere exactamente 11 dígitos para calcular checksum")
        
        total = 0
        for i, digit in enumerate(code):
            weight = 3 if i % 2 == 0 else 1
            total += int(digit) * weight
        
        checksum = (10 - (total % 10)) % 10
        return checksum
    
    @staticmethod
    def calculate_code39_checksum(code: str) -> str:
        """
        Calcular checksum Code39 (opcional).
        
        Args:
            code: Código Code39
            
        Returns:
            str: Carácter de checksum
        """
        # Tabla de valores Code39
        CODE39_VALUES = {
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'G': 16, 'H': 17, 'I': 18,
            'J': 19, 'K': 20, 'L': 21, 'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27,
            'S': 28, 'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33, 'Y': 34, 'Z': 35,
            '-': 36, '.': 37, ' ': 38, '$': 39, '/': 40, '+': 41, '%': 42
        }
        
        CODE39_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%'
        
        total = sum(CODE39_VALUES.get(char.upper(), 0) for char in code)
        checksum_index = total % 43
        
        return CODE39_CHARS[checksum_index]
    
    @staticmethod
    def convert_format(code: str, from_format: str, to_format: str) -> str:
        """
        Convertir código entre formatos compatibles.
        
        Args:
            code: Código original
            from_format: Formato origen
            to_format: Formato destino
            
        Returns:
            str: Código convertido
            
        Raises:
            ValueError: Si la conversión no es posible
        """
        from_format = from_format.upper()
        to_format = to_format.upper()
        
        # Limpiar código
        clean_code = code.strip().replace('-', '').replace(' ', '')
        
        # Conversiones posibles
        conversions = {
            ('UPC', 'EAN13'): lambda x: '0' + x,  # Agregar 0 al inicio
            ('EAN13', 'UPC'): lambda x: x[1:] if x.startswith('0') else None,  # Quitar 0 inicial
            ('EAN8', 'EAN13'): lambda x: '00000' + x,  # Padding con ceros
        }
        
        conversion_key = (from_format, to_format)
        
        if conversion_key in conversions:
            result = conversions[conversion_key](clean_code)
            if result is None:
                raise ValueError(f"No se puede convertir {code} de {from_format} a {to_format}")
            return result
        else:
            raise ValueError(f"Conversión de {from_format} a {to_format} no soportada")
    
    @staticmethod
    def generate_random_code(length: int = 10, format: str = 'CODE128') -> str:
        """
        Generar código aleatorio válido.
        
        Args:
            length: Longitud del código
            format: Formato del código
            
        Returns:
            str: Código aleatorio generado
        """
        format_upper = format.upper()
        
        if format_upper == 'EAN13':
            # Generar 12 dígitos + checksum
            digits = ''.join(random.choices(string.digits, k=12))
            checksum = BarcodeUtils.calculate_ean13_checksum(digits)
            return digits + str(checksum)
        
        elif format_upper == 'EAN8':
            # Generar 7 dígitos + checksum
            digits = ''.join(random.choices(string.digits, k=7))
            checksum = BarcodeUtils.calculate_ean8_checksum(digits)
            return digits + str(checksum)
        
        elif format_upper in ['UPC', 'UPCA']:
            # Generar 11 dígitos + checksum
            digits = ''.join(random.choices(string.digits, k=11))
            checksum = BarcodeUtils.calculate_upc_checksum(digits)
            return digits + str(checksum)
        
        elif format_upper == 'CODE128':
            # Generar caracteres ASCII imprimibles
            chars = ''.join(chr(i) for i in range(32, 127))  # ASCII 32-126
            return ''.join(random.choices(chars, k=min(length, 48)))
        
        elif format_upper == 'CODE39':
            # Generar caracteres válidos Code39
            valid_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%'
            return ''.join(random.choices(valid_chars, k=min(length, 43)))
        
        else:
            # Por defecto, generar dígitos
            return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def extract_product_info(code: str) -> Dict[str, Any]:
        """
        Extraer información de producto desde código de barras.
        
        Args:
            code: Código de barras
            
        Returns:
            Dict: Información extraída
        """
        info = {
            'code': code,
            'format': None,
            'valid': False,
            'country_code': None,
            'manufacturer_code': None,
            'product_code': None,
            'checksum': None,
            'metadata': {}
        }
        
        # Determinar formato
        clean_code = code.strip().replace('-', '').replace(' ', '')
        
        if BarcodeUtils.validate_ean13(clean_code):
            info['format'] = 'EAN13'
            info['valid'] = True
            info['country_code'] = clean_code[:3]
            info['manufacturer_code'] = clean_code[3:8]
            info['product_code'] = clean_code[8:12]
            info['checksum'] = clean_code[12]
            
            # Información adicional EAN13
            country_codes = {
                '000': 'US/Canada', '001': 'US/Canada', '020': 'In-store use',
                '030': 'US/Canada', '040': 'In-store use', '050': 'Coupons',
                '060': 'US/Canada', '100': 'US/Canada', '139': 'US/Canada',
                '200': 'In-store use', '300': 'France', '380': 'Bulgaria',
                '400': 'Germany', '450': 'Japan', '460': 'Russia',
                '500': 'UK', '520': 'Greece', '540': 'Belgium/Luxembourg',
                '560': 'Portugal', '590': 'Poland', '600': 'South Africa',
                '611': 'Morocco', '613': 'Algeria', '616': 'Kenya',
                '618': 'Ivory Coast', '619': 'Tunisia', '621': 'Syria',
                '622': 'Egypt', '624': 'Libya', '625': 'Jordan',
                '626': 'Iran', '627': 'Kuwait', '628': 'Saudi Arabia',
                '629': 'UAE', '640': 'Finland', '690': 'China',
                '700': 'Norway', '729': 'Israel', '730': 'Sweden',
                '740': 'Guatemala', '741': 'El Salvador', '742': 'Honduras',
                '743': 'Nicaragua', '744': 'Costa Rica', '745': 'Panama',
                '746': 'Dominican Republic', '750': 'Mexico', '754': 'Canada',
                '755': 'Canada', '759': 'Venezuela', '760': 'Switzerland',
                '770': 'Colombia', '773': 'Uruguay', '775': 'Peru',
                '777': 'Bolivia', '779': 'Argentina', '780': 'Chile',
                '784': 'Paraguay', '786': 'Ecuador', '789': 'Brazil',
                '800': 'Italy', '840': 'Spain', '850': 'Cuba',
                '858': 'Slovakia', '859': 'Czech Republic', '860': 'Yugoslavia',
                '867': 'North Korea', '869': 'Turkey', '870': 'Netherlands',
                '880': 'South Korea', '885': 'Thailand', '888': 'Singapore',
                '890': 'India', '893': 'Vietnam', '896': 'Pakistan',
                '899': 'Indonesia', '900': 'Austria', '930': 'Australia',
                '940': 'New Zealand', '955': 'Malaysia', '958': 'Macau'
            }
            
            country_prefix = clean_code[:3]
            info['metadata']['country_name'] = country_codes.get(country_prefix, 'Unknown')
            
        elif BarcodeUtils.validate_ean8(clean_code):
            info['format'] = 'EAN8'
            info['valid'] = True
            info['country_code'] = clean_code[:2]
            info['product_code'] = clean_code[2:7]
            info['checksum'] = clean_code[7]
            
        elif BarcodeUtils.validate_upc(clean_code):
            info['format'] = 'UPC'
            info['valid'] = True
            info['manufacturer_code'] = clean_code[:6]
            info['product_code'] = clean_code[6:11]
            info['checksum'] = clean_code[11]
            
        elif BarcodeUtils.validate_code128(clean_code):
            info['format'] = 'CODE128'
            info['valid'] = True
            
        elif BarcodeUtils.validate_code39(clean_code):
            info['format'] = 'CODE39'
            info['valid'] = True
        
        return info
    
    @staticmethod
    def format_display_code(code: str, format: str = None) -> str:
        """
        Formatear código para visualización.
        
        Args:
            code: Código a formatear
            format: Formato específico (opcional)
            
        Returns:
            str: Código formateado
        """
        clean_code = code.strip().replace('-', '').replace(' ', '')
        
        # Auto-detectar formato si no se especifica
        if not format:
            info = BarcodeUtils.extract_product_info(clean_code)
            format = info.get('format', 'UNKNOWN')
        
        format_upper = format.upper()
        
        if format_upper == 'EAN13' and len(clean_code) == 13:
            # Formato: 123 4567 890123
            return f"{clean_code[:3]} {clean_code[3:7]} {clean_code[7:12]} {clean_code[12]}"
        
        elif format_upper == 'EAN8' and len(clean_code) == 8:
            # Formato: 1234 5678
            return f"{clean_code[:4]} {clean_code[4:]}"
        
        elif format_upper in ['UPC', 'UPCA'] and len(clean_code) == 12:
            # Formato: 1 23456 78901 2
            return f"{clean_code[0]} {clean_code[1:6]} {clean_code[6:11]} {clean_code[11]}"
        
        else:
            # Para otros formatos, insertar espacios cada 4 caracteres
            return ' '.join(clean_code[i:i+4] for i in range(0, len(clean_code), 4))
    
    @staticmethod
    def normalize_code(code: str) -> str:
        """
        Normalizar código eliminando espacios y caracteres no válidos.
        
        Args:
            code: Código a normalizar
            
        Returns:
            str: Código normalizado
        """
        if not code:
            return ''
        
        # Eliminar espacios, guiones y caracteres especiales comunes
        normalized = re.sub(r'[-\s]', '', str(code).strip())
        
        # Convertir a mayúsculas para Code39
        return normalized.upper()
    
    @staticmethod
    def get_format_info(format: str) -> Dict[str, Any]:
        """
        Obtener información sobre un formato de código.
        
        Args:
            format: Formato del código
            
        Returns:
            Dict: Información del formato
        """
        format_upper = format.upper()
        
        format_info = {
            'EAN13': {
                'name': 'European Article Number 13',
                'length': 13,
                'type': 'numeric',
                'checksum': True,
                'description': 'Estándar internacional para identificación de productos',
                'usage': 'Productos retail, supermercados'
            },
            'EAN8': {
                'name': 'European Article Number 8',
                'length': 8,
                'type': 'numeric',
                'checksum': True,
                'description': 'Versión corta de EAN para productos pequeños',
                'usage': 'Productos pequeños donde EAN13 no cabe'
            },
            'UPC': {
                'name': 'Universal Product Code',
                'length': 12,
                'type': 'numeric',
                'checksum': True,
                'description': 'Estándar estadounidense para productos',
                'usage': 'Productos en Estados Unidos y Canadá'
            },
            'CODE128': {
                'name': 'Code 128',
                'length': 'variable',
                'type': 'alphanumeric',
                'checksum': False,
                'description': 'Código de alta densidad para datos alfanuméricos',
                'usage': 'Envíos, inventario, aplicaciones industriales'
            },
            'CODE39': {
                'name': 'Code 39',
                'length': 'variable',
                'type': 'alphanumeric',
                'checksum': 'optional',
                'description': 'Código simple y robusto',
                'usage': 'Inventario, identificación de activos'
            }
        }
        
        return format_info.get(format_upper, {
            'name': 'Unknown Format',
            'length': 'unknown',
            'type': 'unknown',
            'checksum': False,
            'description': 'Formato no reconocido',
            'usage': 'N/A'
        })


# Funciones de conveniencia
def validate_barcode(code: str, format: str = None) -> bool:
    """
    Función de conveniencia para validar cualquier código.
    
    Args:
        code: Código a validar
        format: Formato específico (opcional)
        
    Returns:
        bool: True si el código es válido
    """
    if not format:
        # Auto-detectar formato
        info = BarcodeUtils.extract_product_info(code)
        return info['valid']
    
    format_upper = format.upper()
    
    validators = {
        'EAN13': BarcodeUtils.validate_ean13,
        'EAN8': BarcodeUtils.validate_ean8,
        'UPC': BarcodeUtils.validate_upc,
        'UPCA': BarcodeUtils.validate_upc,
        'CODE128': BarcodeUtils.validate_code128,
        'CODE39': BarcodeUtils.validate_code39,
    }
    
    validator = validators.get(format_upper)
    if validator:
        return validator(code)
    
    return False


def generate_product_code(base_id: int, format: str = 'CODE128') -> str:
    """
    Generar código de producto basado en ID.
    
    Args:
        base_id: ID base del producto
        format: Formato del código
        
    Returns:
        str: Código generado
    """
    format_upper = format.upper()
    
    if format_upper == 'EAN13':
        # Usar ID como base y rellenar
        base_str = str(base_id).zfill(12)
        if len(base_str) > 12:
            base_str = base_str[-12:]  # Truncar si es muy largo
        
        checksum = BarcodeUtils.calculate_ean13_checksum(base_str)
        return base_str + str(checksum)
    
    elif format_upper == 'CODE128':
        # Simplemente usar el ID como string
        return str(base_id)
    
    else:
        # Para otros formatos, usar ID con padding
        return str(base_id).zfill(10)


def is_valid_product_code(code: str) -> Tuple[bool, str]:
    """
    Verificar si un código es válido para productos.
    
    Args:
        code: Código a verificar
        
    Returns:
        Tuple[bool, str]: (es_válido, formato_detectado)
    """
    info = BarcodeUtils.extract_product_info(code)
    return info['valid'], info.get('format', 'UNKNOWN')
