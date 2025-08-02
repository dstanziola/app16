"""
Modelo de datos para CompanyConfig.
Representa la configuración de empresa para tickets y facturación.

Este archivo implementa el modelo siguiendo TDD:
- Validaciones robustas para datos de empresa
- Métodos para formateo de información corporativa
- Gestión de tasas de impuestos

Autor: Sistema TDD - FASE 3
Fecha: 2025-06-25
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
import re


class CompanyConfig:
    """
    Modelo para representar la configuración de empresa.
    
    Almacena datos corporativos utilizados en tickets, facturas
    y documentos del sistema.
    """
    
    # Valores por defecto de Copy Point S.A.
    DEFAULT_NOMBRE = "Completa los datos para tu empresa"
    DEFAULT_RUC = "888-888-8888"
    DEFAULT_DIRECCION = "Jordanal, Capira, Panamá"
    DEFAULT_TELEFONO = "6666-6666"
    DEFAULT_EMAIL = "tu_correo@gmail.com"
    DEFAULT_ITBMS_RATE = Decimal("7.00")
    DEFAULT_MONEDA = "USD"
    
    def __init__(
        self,
        nombre: str = DEFAULT_NOMBRE,
        ruc: str = DEFAULT_RUC,
        direccion: str = DEFAULT_DIRECCION,
        telefono: str = DEFAULT_TELEFONO,
        email: str = DEFAULT_EMAIL,
        itbms_rate: float = float(DEFAULT_ITBMS_RATE),
        moneda: str = DEFAULT_MONEDA,
        logo_path: Optional[str] = None,
        updated_at: Optional[datetime] = None,
        config_id: int = 1
    ):
        """
        Inicializar configuración de empresa.
        
        Args:
            nombre: Nombre de la empresa
            ruc: RUC de la empresa
            direccion: Dirección física
            telefono: Teléfono de contacto
            email: Email de contacto
            itbms_rate: Tasa de ITBMS (impuesto) en porcentaje
            moneda: Código de moneda (USD, PAB, etc.)
            logo_path: Ruta al archivo de logo
            updated_at: Fecha de última actualización
            config_id: ID de configuración (siempre 1 para Singleton)
        """
        self.config_id = config_id
        self.nombre = nombre
        self.ruc = ruc
        self.direccion = direccion
        self.telefono = telefono
        self.email = email
        self.itbms_rate = Decimal(str(itbms_rate))
        self.moneda = moneda
        self.logo_path = logo_path
        self.updated_at = updated_at or datetime.now()
        
        # Validar datos en la inicialización
        self._validar_datos_iniciales()
    
    def _validar_datos_iniciales(self) -> None:
        """
        Validar datos básicos durante la inicialización.
        
        Raises:
            ValueError: Si los datos no son válidos
        """
        errores = self.validar_datos()
        if errores:
            raise ValueError(f"Configuración de empresa no válida: {', '.join(errores)}")
    
    def validar_datos(self) -> list:
        """
        Validar todos los datos de configuración.
        
        Returns:
            Lista de errores encontrados (vacía si todo está bien)
        """
        errores = []
        
        # Validar nombre de empresa
        if not self.nombre or len(self.nombre.strip()) == 0:
            errores.append("El nombre de la empresa es requerido")
        elif len(self.nombre.strip()) > 100:
            errores.append("El nombre de la empresa no puede exceder 100 caracteres")
        
        # Validar RUC
        if not self.ruc or len(self.ruc.strip()) == 0:
            errores.append("El RUC es requerido")
        elif not self._validar_formato_ruc(self.ruc):
            errores.append("El formato del RUC no es válido (ejemplo: 888-888-8888)")
        
        # Validar dirección
        if not self.direccion or len(self.direccion.strip()) == 0:
            errores.append("La dirección es requerida")
        elif len(self.direccion.strip()) > 255:
            errores.append("La dirección no puede exceder 255 caracteres")
        
        # Validar teléfono
        if not self.telefono or len(self.telefono.strip()) == 0:
            errores.append("El teléfono es requerido")
        elif not self._validar_formato_telefono(self.telefono):
            errores.append("El formato del teléfono no es válido (ejemplo: 6666-6666)")
        
        # Validar email
        if not self.email or len(self.email.strip()) == 0:
            errores.append("El email es requerido")
        elif not self._validar_formato_email(self.email):
            errores.append("El formato del email no es válido")
        
        # Validar tasa de ITBMS
        if self.itbms_rate < 0 or self.itbms_rate > 100:
            errores.append("La tasa de ITBMS debe estar entre 0 y 100")
        
        # Validar moneda
        if not self.moneda or len(self.moneda.strip()) == 0:
            errores.append("La moneda es requerida")
        elif len(self.moneda.strip()) > 10:
            errores.append("El código de moneda no puede exceder 10 caracteres")
        
        # Validar logo_path si está presente
        if self.logo_path and len(self.logo_path.strip()) > 255:
            errores.append("La ruta del logo no puede exceder 255 caracteres")
        
        return errores
    
    def _validar_formato_ruc(self, ruc: str) -> bool:
        """
        Validar formato de RUC panameño.
        
        Args:
            ruc: RUC a validar
            
        Returns:
            True si el formato es válido
        """
        # Patrón básico para RUC panameño: ###-###-####
        patron = r'^\d{1,3}-\d{1,3}-\d{1,4}$'
        return bool(re.match(patron, ruc.strip()))
    
    def _validar_formato_telefono(self, telefono: str) -> bool:
        """
        Validar formato de teléfono.
        
        Args:
            telefono: Teléfono a validar
            
        Returns:
            True si el formato es válido
        """
        # Patrones válidos: ####-####, +### ####-####, etc.
        telefono_limpio = telefono.strip()
        
        # Permitir números con o sin guiones, con o sin prefijo +
        patron = r'^(\+?\d{1,3}\s?)?\d{4}-?\d{4}$'
        return bool(re.match(patron, telefono_limpio))
    
    def _validar_formato_email(self, email: str) -> bool:
        """
        Validar formato de email.
        
        Args:
            email: Email a validar
            
        Returns:
            True si el formato es válido
        """
        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(patron, email.strip()))
    
    def es_valido(self) -> bool:
        """
        Verificar si la configuración tiene datos válidos.
        
        Returns:
            True si todos los datos son válidos
        """
        return len(self.validar_datos()) == 0
    
    def actualizar_timestamp(self) -> None:
        """
        Actualizar el timestamp de última modificación.
        """
        self.updated_at = datetime.now()
    
    def obtener_nombre_formateado(self) -> str:
        """
        Obtener nombre de empresa formateado para documentos.
        
        Returns:
            Nombre de empresa en mayúsculas
        """
        return self.nombre.upper()
    
    def obtener_ruc_formateado(self) -> str:
        """
        Obtener RUC formateado para documentos.
        
        Returns:
            RUC con formato R.U.C.: ###-###-####
        """
        return f"R.U.C.: {self.ruc}"
    
    def obtener_telefono_formateado(self) -> str:
        """
        Obtener teléfono formateado para documentos.
        
        Returns:
            Teléfono con formato Tel.: ####-####
        """
        return f"Tel.: {self.telefono}"
    
    def obtener_email_formateado(self) -> str:
        """
        Obtener email formateado para documentos.
        
        Returns:
            Email con formato E-mail: usuario@dominio.com
        """
        return f"E-mail: {self.email}"
    
    def obtener_itbms_formateado(self) -> str:
        """
        Obtener tasa de ITBMS formateada.
        
        Returns:
            Tasa de ITBMS con formato ##.##%
        """
        return f"{self.itbms_rate}%"
    
    def calcular_itbms(self, subtotal: Decimal) -> Decimal:
        """
        Calcular ITBMS sobre un subtotal.
        
        Args:
            subtotal: Monto base para calcular impuesto
            
        Returns:
            Monto del ITBMS calculado
        """
        if not isinstance(subtotal, Decimal):
            subtotal = Decimal(str(subtotal))
        
        itbms = (subtotal * self.itbms_rate) / Decimal('100')
        return itbms.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calcular_total_con_itbms(self, subtotal: Decimal) -> Decimal:
        """
        Calcular total incluyendo ITBMS.
        
        Args:
            subtotal: Monto base
            
        Returns:
            Total con ITBMS incluido
        """
        if not isinstance(subtotal, Decimal):
            subtotal = Decimal(str(subtotal))
        
        itbms = self.calcular_itbms(subtotal)
        total = subtotal + itbms
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def obtener_simbolo_moneda(self) -> str:
        """
        Obtener símbolo de la moneda.
        
        Returns:
            Símbolo de moneda
        """
        simbolos_moneda = {
            'USD': '$',
            'PAB': 'B/.',
            'EUR': '€',
            'MXN': '$',
            'COP': '$'
        }
        
        return simbolos_moneda.get(self.moneda.upper(), self.moneda)
    
    def formatear_monto(self, monto: Decimal) -> str:
        """
        Formatear un monto con la moneda configurada.
        
        Args:
            monto: Monto a formatear
            
        Returns:
            Monto formateado con símbolo de moneda
        """
        if not isinstance(monto, Decimal):
            monto = Decimal(str(monto))
        
        simbolo = self.obtener_simbolo_moneda()
        monto_formateado = f"{monto:,.2f}"
        
        return f"{simbolo} {monto_formateado}"
    
    def tiene_logo(self) -> bool:
        """
        Verificar si tiene logo configurado.
        
        Returns:
            True si hay ruta de logo configurada
        """
        return bool(self.logo_path and len(self.logo_path.strip()) > 0)
    
    def establecer_logo(self, logo_path: str) -> None:
        """
        Establecer ruta del logo de empresa.
        
        Args:
            logo_path: Ruta completa al archivo de logo
        """
        if logo_path and len(logo_path.strip()) > 0:
            self.logo_path = logo_path.strip()
            self.actualizar_timestamp()
        else:
            self.logo_path = None
            self.actualizar_timestamp()
    
    def obtener_encabezado_completo(self) -> Dict[str, str]:
        """
        Obtener encabezado completo para documentos.
        
        Returns:
            Diccionario con todos los datos de encabezado
        """
        return {
            'nombre': self.obtener_nombre_formateado(),
            'ruc': self.obtener_ruc_formateado(),
            'direccion': self.direccion,
            'telefono': self.obtener_telefono_formateado(),
            'email': self.obtener_email_formateado(),
            'logo_path': self.logo_path
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir configuración a diccionario.
        
        Returns:
            Diccionario con todos los atributos
        """
        return {
            'config_id': self.config_id,
            'nombre': self.nombre,
            'ruc': self.ruc,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'itbms_rate': float(self.itbms_rate),
            'moneda': self.moneda,
            'logo_path': self.logo_path,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyConfig':
        """
        Crear configuración desde un diccionario.
        
        Args:
            data: Diccionario con los datos de configuración
            
        Returns:
            Nueva instancia de CompanyConfig
        """
        updated_at = None
        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                updated_at = datetime.fromisoformat(data['updated_at'])
            elif isinstance(data['updated_at'], datetime):
                updated_at = data['updated_at']
        
        return cls(
            nombre=data.get('nombre', cls.DEFAULT_NOMBRE),
            ruc=data.get('ruc', cls.DEFAULT_RUC),
            direccion=data.get('direccion', cls.DEFAULT_DIRECCION),
            telefono=data.get('telefono', cls.DEFAULT_TELEFONO),
            email=data.get('email', cls.DEFAULT_EMAIL),
            itbms_rate=data.get('itbms_rate', float(cls.DEFAULT_ITBMS_RATE)),
            moneda=data.get('moneda', cls.DEFAULT_MONEDA),
            logo_path=data.get('logo_path'),
            updated_at=updated_at,
            config_id=data.get('config_id', 1)
        )
    
    @classmethod
    def crear_configuracion_defecto(cls) -> 'CompanyConfig':
        """
        Crear configuración con valores por defecto de Copy Point S.A.
        
        Returns:
            Nueva instancia con valores por defecto
        """
        return cls()
    
    def actualizar_datos(
        self,
        nombre: Optional[str] = None,
        ruc: Optional[str] = None,
        direccion: Optional[str] = None,
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        itbms_rate: Optional[float] = None,
        moneda: Optional[str] = None,
        logo_path: Optional[str] = None
    ) -> None:
        """
        Actualizar datos de configuración.
        
        Args:
            nombre: Nuevo nombre (opcional)
            ruc: Nuevo RUC (opcional)
            direccion: Nueva dirección (opcional)
            telefono: Nuevo teléfono (opcional)
            email: Nuevo email (opcional)
            itbms_rate: Nueva tasa de ITBMS (opcional)
            moneda: Nueva moneda (opcional)
            logo_path: Nueva ruta de logo (opcional)
        """
        if nombre is not None:
            self.nombre = nombre
        if ruc is not None:
            self.ruc = ruc
        if direccion is not None:
            self.direccion = direccion
        if telefono is not None:
            self.telefono = telefono
        if email is not None:
            self.email = email
        if itbms_rate is not None:
            self.itbms_rate = Decimal(str(itbms_rate))
        if moneda is not None:
            self.moneda = moneda
        if logo_path is not None:
            self.logo_path = logo_path
        
        self.actualizar_timestamp()
        
        # Re-validar después de actualizar
        errores = self.validar_datos()
        if errores:
            raise ValueError(f"Datos actualizados no válidos: {', '.join(errores)}")
    
    def __str__(self) -> str:
        """
        Representación string de la configuración.
        
        Returns:
            String descriptivo con nombre de empresa
        """
        return f"CompanyConfig(nombre='{self.nombre}', ruc='{self.ruc}')"
    
    def __repr__(self) -> str:
        """
        Representación técnica de la configuración.
        
        Returns:
            String con atributos principales
        """
        return (f"CompanyConfig(config_id={self.config_id}, "
                f"nombre='{self.nombre}', ruc='{self.ruc}', "
                f"itbms_rate={self.itbms_rate})")
    
    def __eq__(self, other) -> bool:
        """
        Comparar dos configuraciones por igualdad.
        
        Args:
            other: Otra instancia de CompanyConfig
            
        Returns:
            True si son la misma configuración
        """
        if not isinstance(other, CompanyConfig):
            return False
        
        return (self.config_id == other.config_id and 
                self.nombre == other.nombre and
                self.ruc == other.ruc)
    
    def __hash__(self) -> int:
        """
        Hash de la configuración.
        
        Returns:
            Hash basado en ID y datos básicos
        """
        return hash(('CompanyConfig', self.config_id, self.nombre, self.ruc))
