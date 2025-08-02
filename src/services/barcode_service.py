"""
Servicio de Códigos de Barras - Modo Teclado
===========================================

Servicio de lógica de negocio para manejo de códigos de barras
en el sistema de inventario usando lectores en modo HID teclado.

CAMBIOS PRINCIPALES v1.1.0:
- Eliminadas dependencias de hardware externo (hidapi, device_manager)
- Enfoque en modo teclado para lectores HID
- Métodos simplificados y más robustos
- Sin dependencias circulares
- Compatibilidad con BarcodeEntry widget

Autor: Sistema de Inventario Copy Point S.A.
Versión: 1.1.0 - Modo Teclado
Fecha: Julio 2025
"""

import logging
import re
from typing import List, Dict, Optional, Any, Union


class BarcodeService:
    """
    Servicio para gestión de códigos de barras en modo teclado.
    
    NUEVA FILOSOFÍA v1.1.0:
    - Sin dependencias de hardware externo
    - Enfocado en validación y lógica de negocio
    - Compatible con lectores HID configurados como teclado
    - Integración con BarcodeEntry widget para captura
    - Métodos simplificados y confiables
    
    MODO DE OPERACIÓN:
    1. Los lectores de códigos de barras se configuran en modo HID teclado
    2. El widget BarcodeEntry captura la entrada automáticamente
    3. Este servicio valida, formatea y busca productos
    4. No hay gestión directa de dispositivos USB
    
    Funcionalidades principales:
    - Validación de códigos de barras
    - Formateo y normalización de códigos
    - Búsqueda de productos por código
    - Estadísticas básicas del sistema
    """
    
    # Patrón para validación de códigos de barras
    # Permite letras, números y algunos caracteres especiales comunes
    VALID_BARCODE_PATTERN = re.compile(r'^[A-Za-z0-9\-_]+$')
    
    # Longitud máxima para códigos de barras
    MAX_BARCODE_LENGTH = 100
    
    def __init__(self, product_service=None):
        """
        Inicializa el servicio de códigos de barras en modo teclado.
        
        Args:
            product_service: Servicio de productos (opcional para evitar dependencias circulares)
        """
        self.logger = logging.getLogger(__name__)
        self.product_service = product_service
        
        # Configuración para modo teclado
        self._keyboard_mode = True
        self._service_version = "1.1.0"
        
        self.logger.info("BarcodeService inicializado en modo teclado (sin hardware externo)")
    
    def set_product_service(self, product_service):
        """
        Establece el servicio de productos después de la inicialización.
        
        Método para evitar dependencias circulares.
        
        Args:
            product_service: Instancia de ProductService
        """
        self.product_service = product_service
        self.logger.debug("ProductService configurado en BarcodeService")
    
    # ===== MÉTODOS PRINCIPALES DE VALIDACIÓN Y BÚSQUEDA =====
    
    def validate_barcode(self, barcode: Union[str, None]) -> bool:
        """
        Valida si un código de barras tiene formato válido.
        
        Args:
            barcode: Código de barras a validar
            
        Returns:
            bool: True si el código es válido
        """
        if not barcode:
            return False
        
        # Convertir a string y limpiar
        barcode_str = str(barcode).strip()
        
        # Verificar que no esté vacío después de limpiar
        if not barcode_str:
            return False
        
        # Verificar longitud máxima
        if len(barcode_str) > self.MAX_BARCODE_LENGTH:
            return False
        
        # Verificar patrón válido (solo letras, números, guiones y guiones bajos)
        if not self.VALID_BARCODE_PATTERN.match(barcode_str):
            return False
        
        return True
    
    def format_barcode(self, barcode: str) -> str:
        """
        Formatea y normaliza un código de barras.
        
        Args:
            barcode: Código de barras a formatear
            
        Returns:
            str: Código formateado
        """
        if not barcode:
            return ""
        
        # Convertir a string, limpiar espacios y convertir a mayúsculas
        formatted = str(barcode).strip().upper()
        
        # Remover caracteres de control (\\n, \\t, etc.)
        formatted = re.sub(r'\\[ntr]', '', formatted)
        
        return formatted
    
    def search_product_by_code(self, code: str):
        """
        Busca un producto por código de barras.
        
        En el sistema, el ID del producto funciona como código de barras.
        
        Args:
            code: Código de barras o ID del producto
            
        Returns:
            Producto encontrado o None si no existe
        """
        if not self.product_service:
            self.logger.warning("ProductService no está configurado")
            return None
        
        try:
            # Formatear el código
            formatted_code = self.format_barcode(code)
            
            if not formatted_code:
                self.logger.debug("Código vacío después del formateo")
                return None
            
            # Intentar convertir a ID numérico
            if formatted_code.isdigit():
                product_id = int(formatted_code)
                product = self.product_service.get_product_by_id(product_id)
                
                if product:
                    self.logger.info(f"Producto encontrado para código {formatted_code}: {product.nombre}")
                else:
                    self.logger.warning(f"No se encontró producto para código: {formatted_code}")
                
                return product
            else:
                self.logger.debug(f"Código no numérico: {formatted_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error buscando producto por código {code}: {e}")
            return None
    
    # ===== MÉTODOS DE COMPATIBILIDAD (SIN HARDWARE) =====
    
    def is_connected(self) -> bool:
        """
        Verifica conexión de dispositivos.
        
        En modo teclado, siempre retorna False ya que no gestionamos hardware directamente.
        
        Returns:
            bool: False (no hay gestión directa de hardware)
        """
        return False
    
    def is_scanner_available(self) -> bool:
        """
        Verifica disponibilidad de escáner.
        
        En modo teclado, no podemos detectar hardware directamente.
        
        Returns:
            bool: False (detección no disponible en modo teclado)
        """
        return False
    
    def scan_barcode_devices(self) -> List[Dict[str, Any]]:
        """
        Escanea dispositivos de códigos de barras.
        
        En modo teclado, retorna lista vacía ya que no gestionamos hardware directamente.
        
        Returns:
            List[Dict]: Lista vacía (no hay detección de hardware)
        """
        self.logger.debug("scan_barcode_devices llamado en modo teclado - retornando lista vacía")
        return []
    
    def connect_barcode_device(self, device_id: str) -> bool:
        """
        Conecta dispositivo de código de barras.
        
        En modo teclado, no hay conexiones directas de hardware.
        
        Args:
            device_id: ID del dispositivo (ignorado)
            
        Returns:
            bool: False (no hay gestión directa de hardware)
        """
        self.logger.debug(f"connect_barcode_device({device_id}) llamado en modo teclado - sin efecto")
        return False
    
    def disconnect_device(self, device_id: str) -> bool:
        """
        Desconecta dispositivo específico.
        
        Args:
            device_id: ID del dispositivo (ignorado)
            
        Returns:
            bool: False (no hay gestión directa de hardware)
        """
        self.logger.debug(f"disconnect_device({device_id}) llamado en modo teclado - sin efecto")
        return False
    
    def disconnect_all_devices(self) -> None:
        """
        Desconecta todos los dispositivos.
        
        En modo teclado, no hay dispositivos que desconectar.
        """
        self.logger.debug("disconnect_all_devices llamado en modo teclado - sin efecto")
    
    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """
        Obtiene dispositivos conectados.
        
        Returns:
            List[Dict]: Lista vacía (no hay gestión directa de hardware)
        """
        return []
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de dispositivo.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            None: No hay información de hardware en modo teclado
        """
        self.logger.debug(f"get_device_info({device_id}) llamado en modo teclado - retornando None")
        return None
    
    def read_code(self, timeout: float = 0.1) -> Optional[str]:
        """
        Intenta leer código desde dispositivo.
        
        En modo teclado, la lectura se maneja por el widget BarcodeEntry.
        
        Args:
            timeout: Tiempo de espera (ignorado)
            
        Returns:
            None: Lectura directa no disponible en modo teclado
        """
        self.logger.debug("read_code llamado en modo teclado - usar BarcodeEntry widget")
        return None
    
    def read_barcode(self, device_id: str, timeout: int = 5000) -> Optional[str]:
        """
        Lee código desde dispositivo específico.
        
        Args:
            device_id: ID del dispositivo (ignorado)
            timeout: Timeout en milisegundos (ignorado)
            
        Returns:
            None: Lectura directa no disponible en modo teclado
        """
        self.logger.debug(f"read_barcode({device_id}) llamado en modo teclado - usar BarcodeEntry widget")
        return None
    
    def is_device_connected(self, device_id: str) -> bool:
        """
        Verifica si dispositivo está conectado.
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            bool: False (no hay gestión directa de hardware)
        """
        return False
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Obtiene dispositivos disponibles.
        
        Returns:
            List[Dict]: Lista vacía (no hay detección de hardware)
        """
        return []
    
    def auto_connect_first_device(self) -> Optional[str]:
        """
        Auto-conecta primer dispositivo disponible.
        
        Returns:
            None: No hay auto-conexión en modo teclado
        """
        self.logger.debug("auto_connect_first_device llamado en modo teclado - sin dispositivos")
        return None
    
    # ===== MÉTODOS DE ESTADÍSTICAS Y UTILIDADES =====
    
    def get_barcode_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio de códigos de barras.
        
        Returns:
            Dict: Estadísticas del servicio en modo teclado
        """
        try:
            service_stats = {
                'service_version': self._service_version,
                'keyboard_mode': self._keyboard_mode,
                'validation_pattern': self.VALID_BARCODE_PATTERN.pattern,
                'max_barcode_length': self.MAX_BARCODE_LENGTH,
                'product_service_configured': self.product_service is not None,
                'hardware_dependencies': False,
                'supported_features': [
                    'validation',
                    'formatting', 
                    'product_search',
                    'keyboard_mode_integration'
                ],
                'deprecated_features': [
                    'direct_usb_access',
                    'device_management',
                    'hardware_detection'
                ]
            }
            
            return service_stats
            
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas: {e}")
            return {}
    
    # ===== MÉTODOS SIMPLIFICADOS PARA INTEGRACIÓN =====
    
    def lookup_product_by_barcode(self, barcode: str):
        """
        Busca producto por código de barras (alias para compatibility).
        
        Args:
            barcode: Código de barras a buscar
            
        Returns:
            Producto: Instancia del producto, None si no se encuentra
        """
        return self.search_product_by_code(barcode)
    
    def read_barcode_with_validation(self, device_id: str, timeout: int = 5000) -> Optional[str]:
        """
        Lee código con validación (método de compatibilidad).
        
        En modo teclado, no hay lectura directa.
        
        Args:
            device_id: ID del dispositivo (ignorado)
            timeout: Timeout (ignorado)
            
        Returns:
            None: Usar BarcodeEntry widget para lectura
        """
        self.logger.debug("read_barcode_with_validation llamado en modo teclado - usar BarcodeEntry")
        return None
    
    def read_and_lookup_product(self, device_id: str, timeout: int = 5000) -> Optional[Dict[str, Any]]:
        """
        Lee código y busca producto (método de compatibilidad).
        
        Args:
            device_id: ID del dispositivo (ignorado)
            timeout: Timeout (ignorado)
            
        Returns:
            None: Usar BarcodeEntry widget con callback para este flujo
        """
        self.logger.debug("read_and_lookup_product llamado en modo teclado - usar BarcodeEntry con callback")
        return None


# ===== EXCEPCIONES =====

class BarcodeServiceError(Exception):
    """Excepción base para errores del servicio de códigos de barras"""
    pass


class BarcodeValidationError(BarcodeServiceError):
    """Excepción para errores de validación de códigos"""
    pass


class BarcodeDeviceError(BarcodeServiceError):
    """Excepción para errores de dispositivos de códigos de barras (deprecated en modo teclado)"""
    pass


class BarcodeReadError(BarcodeServiceError):
    """Excepción para errores de lectura de códigos (deprecated en modo teclado)"""
    pass


# ===== FUNCIÓN DE UTILIDAD PARA CREAR SERVICIO =====

def create_barcode_service(product_service=None) -> BarcodeService:
    """
    Función de conveniencia para crear BarcodeService en modo teclado.
    
    Args:
        product_service: Servicio de productos opcional
        
    Returns:
        BarcodeService: Servicio configurado para modo teclado
    """
    service = BarcodeService(product_service)
    return service
